"""학습 파이프라인

기존 PL에서 단위중량을 역산하고, ML 모델을 학습시키는 파이프라인.
scipy.optimize.nnls를 사용하여 연립방정식 기반 중량 역산 수행.
"""
import json
from typing import Dict, List, Tuple

import numpy as np

from src.parser.pl_parser import parse_pl
from src.parser.model_number_parser import extract_model_from_description, get_weight_lookup_key
from src.ml.weight_predictor import WeightPredictor
from config.settings import PRODUCT_DB_PATH


def extract_weights_from_pl(pl_filepath: str) -> List[Tuple[str, float]]:
    """PL에서 모델별 중량 추출

    케이스별 총 순중량과 품목별 수량을 이용해 단위중량을 역산.
    scipy.optimize.nnls로 비음수 최소제곱법 적용.

    Returns:
        list of (model_number, unit_weight_kg)
    """
    from scipy.optimize import nnls

    pl_doc = parse_pl(pl_filepath)

    # 케이스별 데이터 수집
    models = set()
    cases_data = []

    for case in pl_doc.cases:
        net_weight = getattr(case, '_header_net_weight', None)
        if net_weight is None:
            net_weight = case.net_weight

        if net_weight <= 0:
            continue

        case_models = {}
        for pi in case.items:
            model = pi.ci_item.model_number
            if model:
                key = get_weight_lookup_key(model)
                case_models[key] = case_models.get(key, 0) + pi.quantity
                models.add(key)

        if case_models:
            cases_data.append((case_models, net_weight))

    if not cases_data or not models:
        return []

    # 연립방정식 구성: A * x = b
    model_list = sorted(models)
    model_idx = {m: i for i, m in enumerate(model_list)}

    A = np.zeros((len(cases_data), len(model_list)))
    b = np.zeros(len(cases_data))

    for i, (case_models, net_weight) in enumerate(cases_data):
        for model, qty in case_models.items():
            j = model_idx[model]
            A[i, j] = qty
        b[i] = net_weight

    # NNLS (Non-Negative Least Squares) 풀기
    try:
        x, residual = nnls(A, b)
    except Exception:
        return []

    # 결과 추출
    results = []
    for i, model in enumerate(model_list):
        if x[i] > 0.001:  # 의미 있는 중량만
            results.append((model, round(x[i], 3)))

    return results


def update_product_db(new_weights: List[Tuple[str, float]], source: str = "pl_extraction"):
    """product_db.json에 새 중량 데이터 추가/업데이트"""
    with open(PRODUCT_DB_PATH, 'r') as f:
        db = json.load(f)

    updated = 0
    for model_key, weight in new_weights:
        # 카테고리 결정
        prefix = model_key[:3].upper()
        cat_map = {
            'HGV': 'VCB', 'HGS': 'ACB_HGS', 'HGN': 'ACB_LARGE',
            'UAN': 'ACB_LARGE', 'UCB': 'ACB_LARGE',
            'HGM': 'MCCB', 'HGP': 'MCCB',
            'HGC': 'MC', 'HGT': 'RELAY', 'HGR': 'RELAY',
        }
        category = cat_map.get(prefix, 'SPARE')

        if category not in db:
            db[category] = {}

        if model_key not in db[category]:
            db[category][model_key] = {
                'unit_weight_kg': weight,
                'source': source,
            }
            updated += 1
        else:
            existing = db[category][model_key].get('unit_weight_kg', 0)
            if abs(existing - weight) > 0.1:
                # 평균 적용
                db[category][model_key]['unit_weight_kg'] = round(
                    (existing + weight) / 2, 3
                )
                db[category][model_key]['source'] = f"avg({source})"
                updated += 1

    if updated > 0:
        with open(PRODUCT_DB_PATH, 'w') as f:
            json.dump(db, f, indent=2, ensure_ascii=False)

    return updated


def train_full_pipeline(pl_filepaths: List[str]) -> dict:
    """전체 학습 파이프라인 실행

    1. PL 파일들에서 중량 역산
    2. product_db 업데이트
    3. ML 모델 학습

    Returns:
        {'extracted_weights': int, 'db_updated': int, 'model_metrics': dict}
    """
    all_weights = []

    for filepath in pl_filepaths:
        try:
            weights = extract_weights_from_pl(filepath)
            all_weights.extend(weights)
        except Exception as e:
            print(f"경고: {filepath} 처리 실패 - {e}")

    # DB 업데이트
    db_updated = 0
    if all_weights:
        db_updated = update_product_db(all_weights)

    # ML 모델 학습
    predictor = WeightPredictor()
    training_data = predictor.build_training_data_from_db()
    training_data.extend(all_weights)

    # 중복 제거
    seen = set()
    unique_data = []
    for model, weight in training_data:
        if model not in seen:
            seen.add(model)
            unique_data.append((model, weight))

    metrics = predictor.train(unique_data)
    predictor.save()

    return {
        'extracted_weights': len(all_weights),
        'db_updated': db_updated,
        'model_metrics': metrics,
    }
