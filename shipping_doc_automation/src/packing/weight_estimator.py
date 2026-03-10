"""단위중량 조회 및 추정

제품 DB에서 중량을 조회하고, 미등록 제품은 규칙 기반으로 추정.
"""
import json
from pathlib import Path
from typing import Optional

from src.models.data_models import CILineItem, ProductCategory
from src.parser.model_number_parser import get_weight_lookup_key, parse_model_number
from config.settings import PRODUCT_DB_PATH


_product_db = None


def _load_db() -> dict:
    global _product_db
    if _product_db is None:
        with open(PRODUCT_DB_PATH, 'r') as f:
            _product_db = json.load(f)
    return _product_db


def get_unit_weight(item: CILineItem) -> float:
    """품목의 단위중량(kg) 조회/추정"""
    db = _load_db()
    cat = item.category.value

    # 카테고리 DB에서 조회
    cat_db = db.get(cat, {})
    lookup_key = get_weight_lookup_key(item.model_number)

    # 정확한 키 매칭
    if lookup_key in cat_db:
        return cat_db[lookup_key]['unit_weight_kg']

    # 부분 매칭 (접두사 기반)
    for key, spec in cat_db.items():
        if key.startswith('_') or key.endswith('DEFAULT'):
            continue
        if isinstance(spec, dict) and 'unit_weight_kg' in spec:
            if lookup_key.startswith(key[:4]):
                return spec['unit_weight_kg']

    # 기본값 사용
    defaults = {
        ProductCategory.VCB: 100.0,
        ProductCategory.ACB_HGS: 45.0,
        ProductCategory.ACB_LARGE: 160.0,
        ProductCategory.MCCB: 3.0,
        ProductCategory.MC: 1.0,
        ProductCategory.RELAY: 0.2,
        ProductCategory.SPARE: 0.5,
        ProductCategory.UNKNOWN: 1.0,
    }

    # MCCB/MC는 전류값 기반 추정
    if cat in ('MCCB', 'MC', 'RELAY'):
        weight = _estimate_by_current(item)
        if weight:
            return weight

    return defaults.get(item.category, 1.0)


def _estimate_by_current(item: CILineItem) -> Optional[float]:
    """전류 정격 기반 중량 추정"""
    parsed = parse_model_number(item.model_number)
    try:
        current = int(parsed['frame_or_current'])
    except (ValueError, TypeError):
        return None

    if item.category == ProductCategory.MCCB:
        if current <= 125:
            return 1.8
        elif current <= 250:
            return 3.0
        elif current <= 400:
            return 5.0
        elif current <= 630:
            return 7.5
        else:
            return 8.8

    if item.category == ProductCategory.MC:
        if current <= 25:
            return 0.38
        elif current <= 50:
            return 0.55
        elif current <= 85:
            return 0.85
        elif current <= 150:
            return 2.0
        elif current <= 265:
            return 8.0
        else:
            return 18.0

    if item.category == ProductCategory.RELAY:
        if current <= 40:
            return 0.2
        elif current <= 85:
            return 0.3
        else:
            return 0.6

    return None


def get_case_weight(category: ProductCategory, case_type: str = '') -> float:
    """케이스 자체 중량 반환"""
    db = _load_db()

    if category == ProductCategory.VCB:
        return 30.0  # 기본 우든 케이스
    if category == ProductCategory.ACB_HGS:
        specs = db.get('case_specs', {}).get('ACB_STANDARD', {})
        return specs.get('case_weight_kg', 55.0)
    if category == ProductCategory.ACB_LARGE:
        return 60.0

    # 혼합 팔레트
    specs = db.get('case_specs', {}).get('PALLET_STANDARD', {})
    return specs.get('pallet_weight_kg', 25.0) + specs.get('wrapping_weight_kg', 5.0)


def get_case_dimensions(category: ProductCategory, model_number: str = '') -> tuple:
    """케이스 규격 (L, W, H) mm 반환"""
    db = _load_db()

    if category == ProductCategory.VCB:
        vcb_db = db.get('VCB', {})
        key = get_weight_lookup_key(model_number)
        if key in vcb_db:
            spec = vcb_db[key].get('case_spec', [900, 900, 1000])
            return tuple(spec)
        return (900, 900, 1000)

    if category == ProductCategory.ACB_HGS:
        specs = db.get('case_specs', {}).get('ACB_STANDARD', {})
        dims = specs.get('dimensions', [1760, 1200, 840])
        return tuple(dims)

    if category == ProductCategory.ACB_LARGE:
        large_db = db.get('ACB_LARGE', {})
        prefix = model_number[:3].upper() if model_number else ''
        if prefix in large_db:
            spec = large_db[prefix].get('case_spec', [1500, 1100, 1200])
            return tuple(spec)
        return (1500, 1100, 1200)

    # 혼합 팔레트
    specs = db.get('case_specs', {}).get('PALLET_STANDARD', {})
    dims = specs.get('dimensions', [1100, 1100, 1120])
    return tuple(dims)
