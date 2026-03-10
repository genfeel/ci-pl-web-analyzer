"""제품코드 → 특성 추출 (ML 입력 피처)

모델번호에서 중량 예측에 필요한 수치 특성을 추출.
"""
import re
import numpy as np
from typing import Dict

from src.parser.model_number_parser import parse_model_number


# 제품 계열별 기본 특성값
PRODUCT_FAMILY_FEATURES = {
    'HGV': {'family_id': 1, 'base_weight': 100},
    'HGS': {'family_id': 2, 'base_weight': 45},
    'HGN': {'family_id': 3, 'base_weight': 160},
    'UAN': {'family_id': 4, 'base_weight': 200},
    'UCB': {'family_id': 5, 'base_weight': 180},
    'HGM': {'family_id': 6, 'base_weight': 3},
    'HGP': {'family_id': 7, 'base_weight': 3},
    'HGC': {'family_id': 8, 'base_weight': 1},
    'HGT': {'family_id': 9, 'base_weight': 0.2},
    'HGR': {'family_id': 10, 'base_weight': 0.15},
}

# 프레임 타입 인코딩
FRAME_TYPE_ENCODING = {
    '': 0,
    'A-FRAME': 1,
    'B-FRAME': 2,
    'C-FRAME': 3,
    'LARGE': 4,
}

# 프레임 크기 인코딩
FRAME_SIZE_ENCODING = {
    '': 0,
    '100AF': 1,
    '250AF': 2,
    '400AF': 3,
    '630AF': 4,
    '800AF': 5,
}


def extract_features(model_number: str) -> Dict[str, float]:
    """모델번호에서 ML 특성 추출

    Returns:
        {
            'family_id': float,       # 제품 계열 ID
            'log_current': float,     # log(전류정격+1) - 스케일 정규화
            'frame_type': float,      # 프레임 타입 (인코딩)
            'frame_size': float,      # 프레임 크기 (인코딩)
            'log_base_weight': float, # log(계열 기본 중량) - 스케일 정규화
        }
    """
    parsed = parse_model_number(model_number)
    prefix = parsed['prefix']

    family = PRODUCT_FAMILY_FEATURES.get(prefix, {'family_id': 0, 'base_weight': 1})

    # 전류 정격 추출
    current_rating = 0
    try:
        current_rating = float(parsed['frame_or_current'])
    except (ValueError, TypeError):
        pass

    features = {
        'family_id': float(family['family_id']),
        'log_current': float(np.log1p(current_rating)),
        'frame_type': float(FRAME_TYPE_ENCODING.get(parsed.get('frame_type', ''), 0)),
        'frame_size': float(FRAME_SIZE_ENCODING.get(parsed.get('frame_size', ''), 0)),
        'log_base_weight': float(np.log1p(family['base_weight'])),
    }

    return features


def extract_features_vector(model_number: str) -> list:
    """특성을 벡터(리스트)로 반환 (ML 모델 입력용)"""
    features = extract_features(model_number)
    return [
        features['family_id'],
        features['log_current'],
        features['frame_type'],
        features['frame_size'],
        features['log_base_weight'],
    ]


FEATURE_NAMES = [
    'family_id',
    'log_current',
    'frame_type',
    'frame_size',
    'log_base_weight',
]
