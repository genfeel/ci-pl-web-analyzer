"""사용자 보정 학습 (피드백 루프)

사용자가 수정한 PL을 재파싱하여 중량/포장 규칙을 자동 업데이트.
"""
import json
from pathlib import Path
from typing import List

from src.parser.pl_parser import parse_pl
from src.parser.model_number_parser import get_weight_lookup_key
from src.ml.training_pipeline import extract_weights_from_pl, update_product_db
from config.settings import PRODUCT_DB_PATH, DATA_DIR

FEEDBACK_LOG_PATH = DATA_DIR / "feedback_log.json"


def learn_from_corrected_pl(corrected_pl_path: str) -> dict:
    """수정된 PL에서 학습

    1. PL 재파싱
    2. 단위중량 역산
    3. product_db 업데이트
    4. 피드백 로그 기록

    Returns:
        {'new_weights': int, 'db_updated': int}
    """
    # 중량 역산
    new_weights = extract_weights_from_pl(corrected_pl_path)

    # DB 업데이트
    db_updated = 0
    if new_weights:
        db_updated = update_product_db(new_weights, source="user_feedback")

    # 피드백 로그 기록
    _log_feedback(corrected_pl_path, new_weights)

    return {
        'new_weights': len(new_weights),
        'db_updated': db_updated,
    }


def learn_from_case_correction(
    model_number: str,
    actual_unit_weight: float,
    case_type: str = '',
    notes: str = '',
) -> bool:
    """개별 제품 중량 수동 보정

    Args:
        model_number: 제품 모델번호
        actual_unit_weight: 실제 단위중량 (kg)
        case_type: 케이스 타입
        notes: 메모

    Returns:
        성공 여부
    """
    key = get_weight_lookup_key(model_number)
    updated = update_product_db(
        [(key, actual_unit_weight)],
        source="manual_correction"
    )

    _log_feedback("manual", [(key, actual_unit_weight)], notes)

    return updated > 0


def _log_feedback(source: str, weights: list, notes: str = ''):
    """피드백 로그 기록"""
    log = []
    if FEEDBACK_LOG_PATH.exists():
        with open(FEEDBACK_LOG_PATH, 'r') as f:
            try:
                log = json.load(f)
            except json.JSONDecodeError:
                log = []

    entry = {
        'source': source,
        'weights': [{'model': m, 'weight': w} for m, w in weights],
        'notes': notes,
    }
    log.append(entry)

    FEEDBACK_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FEEDBACK_LOG_PATH, 'w') as f:
        json.dump(log, f, indent=2, ensure_ascii=False)
