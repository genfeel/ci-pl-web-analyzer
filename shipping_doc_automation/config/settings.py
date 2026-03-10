"""전역 설정"""
from pathlib import Path

# 프로젝트 경로
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SAMPLES_DIR = DATA_DIR / "samples"
PRODUCT_DB_PATH = DATA_DIR / "product_db.json"

# CI 파싱 설정
CI_SHEET_PATTERNS = ["CI", "ci", "C.I", "C.I."]
PL_SHEET_PATTERNS = ["PL", "pl", "P.L", "P.L.", "P/L"]

# CI 컬럼 매핑 (0-indexed)
CI_COLUMNS = {
    "no": 0,           # A: No.
    "description": 1,  # B: Description (merged B~E)
    "quantity": 5,      # F: Quantity
    "unit": 6,          # G: Unit
    "unit_price": 7,    # H: Unit Price
    "amount": 8,        # I: Amount
}

# PL 컬럼 매핑 (0-indexed)
PL_COLUMNS = {
    "case_no": 0,       # A: CASE NO.
    "description": 1,   # B: Description (merged B~E)
    "quantity": 5,      # F: Quantity
    "unit": 6,          # G: Unit
    "net_weight": 7,    # H: Net Weight (KGS)
    "gross_weight": 8,  # I: Gross Weight (KGS)
    "measurement": 9,   # J: Measurement (CBM)
}

# 엑셀 출력 설정
OUTPUT_DIR = PROJECT_ROOT / "output"
