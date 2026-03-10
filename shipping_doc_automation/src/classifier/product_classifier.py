"""제품 카테고리 분류기

2단계 분류:
1. 제품코드 접두사 기반 분류
2. 카테고리 헤더 교차 검증
"""
from src.models.data_models import CILineItem, CIDocument, ProductCategory
from src.parser.model_number_parser import parse_model_number, extract_model_from_description


# 제품코드 접두사 → 카테고리 매핑
PREFIX_TO_CATEGORY = {
    'HGV': ProductCategory.VCB,
    'HGS': ProductCategory.ACB_HGS,
    'HGN': ProductCategory.ACB_LARGE,
    'UAN': ProductCategory.ACB_LARGE,
    'UCB': ProductCategory.ACB_LARGE,
    'HGM': ProductCategory.MCCB,
    'HGP': ProductCategory.MCCB,
    'HGC': ProductCategory.MC,
    'HGT': ProductCategory.RELAY,
    'HGR': ProductCategory.RELAY,
}

# 카테고리 헤더 텍스트 → 카테고리 매핑
HEADER_TO_CATEGORY = {
    'VACUUM CIRCUIT BREAKER': ProductCategory.VCB,
    'AIR CIRCUIT BREAKER': ProductCategory.ACB_HGS,  # 기본값
    'MOLDED CASE CIRCUIT BREAKER': ProductCategory.MCCB,
    'MOULDED CASE CIRCUIT BREAKER': ProductCategory.MCCB,
    'MAGNETIC CONTACTOR': ProductCategory.MC,
    'THERMAL OVERLOAD RELAY': ProductCategory.RELAY,
    'RELAY': ProductCategory.RELAY,
}


def classify_item(item: CILineItem) -> ProductCategory:
    """개별 품목 카테고리 분류"""
    # 0단계: SPARE PART 헤더는 모델번호보다 우선
    if item.category_header and 'SPARE' in item.category_header.upper():
        return ProductCategory.SPARE

    # 1단계: 카테고리 헤더 기반 분류 (CI 문서 구조에서 가장 신뢰도 높음)
    model = item.model_number or extract_model_from_description(item.description) or ''
    model_upper = model.upper()

    if item.category_header:
        header_upper = item.category_header.upper()

        for header_text, category in HEADER_TO_CATEGORY.items():
            if header_text in header_upper:
                # ACB 헤더인 경우만 모델번호로 세분화 (HGN/UAN → ACB_LARGE)
                if category == ProductCategory.ACB_HGS:
                    if any(model_upper.startswith(p) for p in ('HGN', 'UAN')):
                        return ProductCategory.ACB_LARGE
                return category

    # 2단계: 모델번호 접두사 기반 분류 (헤더 없는 경우)
    for prefix, category in PREFIX_TO_CATEGORY.items():
        if model_upper.startswith(prefix):
            if prefix == 'HGS':
                return ProductCategory.ACB_HGS
            return category

    # 3단계: description 텍스트 분석
    desc_upper = item.description.upper()
    if 'VACUUM' in desc_upper or 'VCB' in desc_upper:
        return ProductCategory.VCB
    if 'AIR CIRCUIT' in desc_upper or 'ACB' in desc_upper:
        return ProductCategory.ACB_HGS
    if 'MOLDED CASE' in desc_upper or 'MCCB' in desc_upper:
        return ProductCategory.MCCB
    if 'CONTACTOR' in desc_upper:
        return ProductCategory.MC
    if 'RELAY' in desc_upper:
        return ProductCategory.RELAY
    if 'SPARE' in desc_upper:
        return ProductCategory.SPARE

    return item.category if item.category != ProductCategory.UNKNOWN else ProductCategory.SPARE


def classify_document(doc: CIDocument) -> CIDocument:
    """문서 내 모든 품목 분류"""
    for item in doc.items:
        if item.category == ProductCategory.UNKNOWN:
            item.category = classify_item(item)
        else:
            # 기존 분류 검증
            verified = classify_item(item)
            if verified != ProductCategory.UNKNOWN:
                item.category = verified
    return doc


def get_acb_frame_type(item: CILineItem) -> str:
    """ACB 프레임 타입 결정 (A-FRAME, B-FRAME, C-FRAME)"""
    if item.category != ProductCategory.ACB_HGS:
        return ''

    parsed = parse_model_number(item.model_number)
    if parsed['frame_type']:
        return parsed['frame_type']

    # description에서 프레임 추정
    desc = item.description.upper()
    if 'A-FRAME' in desc or 'A FRAME' in desc:
        return 'A-FRAME'
    if 'B-FRAME' in desc or 'B FRAME' in desc:
        return 'B-FRAME'
    if 'C-FRAME' in desc or 'C FRAME' in desc:
        return 'C-FRAME'

    # 모델번호의 숫자 부분으로 추정
    model = item.model_number.upper()
    if model.startswith('HGS'):
        try:
            num_part = model[3:7]
            frame_digit = int(num_part[2]) if len(num_part) > 2 else 0
            if frame_digit <= 3:
                return 'A-FRAME'
            elif frame_digit <= 6:
                return 'B-FRAME'
            else:
                return 'C-FRAME'
        except (ValueError, IndexError):
            pass

    return 'A-FRAME'  # 기본값
