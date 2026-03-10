"""PL 출력 서식 규칙

샘플 분석 결과 기반 레이아웃 규칙 정의.
"""
import re
from src.models.data_models import ProductCategory
from config.packing_constraints import CATEGORY_DISPLAY_NAMES, PLURAL_NAMES


def get_category_display_name(category: ProductCategory, plural: bool = True) -> str:
    """카테고리 표시명 반환 (단수/복수)"""
    name = CATEGORY_DISPLAY_NAMES.get(category.value, "PARTS")
    if plural:
        return PLURAL_NAMES.get(name, name)
    return name


def format_dimensions(dims: tuple) -> str:
    """규격을 문자열로 변환: (1100, 1100, 1120) → '1100X1100X1120.MM'"""
    if not dims or dims == (0, 0, 0):
        return ""
    l, w, h = dims
    return f"{l}X{w}X{h}.MM"


def format_cbm(cbm: float) -> str:
    """CBM 포맷: 1.3552 → '1.355'"""
    if cbm <= 0:
        return ""
    return f"{cbm:.3f}"


def format_weight(weight: float) -> str:
    """중량 포맷: 정수면 정수로, 소수면 소수점 2자리"""
    if weight == 0:
        return ""
    if weight == int(weight):
        return str(int(weight))
    return f"{weight:.2f}"


def format_case_header(case_no: int, total_cases: int) -> str:
    """케이스 헤더 문자열: 'CASE NO : 1 of 12'"""
    return f"CASE NO : {case_no} of {total_cases}"


def format_total_header(total_cases: int) -> str:
    """TOTAL 헤더 문자열: 'TOTAL(12 CASES)'"""
    return f"TOTAL({total_cases} CASES)"


def should_pluralize(count: int, category_name: str) -> str:
    """수량에 따른 복수형 처리"""
    if count <= 1:
        return category_name
    return PLURAL_NAMES.get(category_name, category_name)


# PL 헤더 영역 행 구조 (Row 1~약 28)
PL_HEADER_TEMPLATE = {
    'title_row': 1,
    'sheet_info_row': 2,
    'shipper_start': 3,
    'consignee_row': 8,
    'notify_row': 14,
    'port_row': 24,
    'carrier_row': 26,
    'column_header_row': 28,  # 실제 파일에 따라 동적 조정
}

# PL 컬럼 레이아웃
PL_COLUMN_WIDTHS = {
    'A': 18,   # Marks and No.
    'B': 3,    # (A 연속)
    'C': 30,   # Description
    'D': 12,   # (C 연속)
    'E': 10,   # Quantity
    'F': 12,   # Net-weight
    'G': 12,   # Gross-weight
    'H': 20,   # Measurement
}

# 서명 영역
SIGNATURE_ROWS = [
    "",
    "HD HYUNDAI ELECTRIC CO., LTD.",
    "",
    "",
    "___________________________",
    "Authorized Signature",
]
