"""포장 규칙 및 제약조건 상수"""

# === VCB 포장 규격 (mm) ===
VCB_CASE_SPECS = {
    # model_prefix: (length, width, height, case_weight_kg)
    "HGV3141": (800, 800, 900, 25),
    "HGV2141": (1000, 1000, 1100, 35),
    "HGV2142": (1000, 1000, 1100, 35),
    "HGV_DEFAULT": (900, 900, 1000, 30),
}

# === ACB 포장 규격 (mm) ===
ACB_STANDARD_CASE = {
    # HGS 표준 케이스 (프레임 4~6대)
    "length": 1760,
    "width": 1200,
    "height": 840,
    "case_weight_kg": 55,
    "max_units": 6,
}

ACB_FRAME_SPECS = {
    # frame_type: (unit_weight_kg, max_per_case)
    "A-FRAME": (34, 6),    # 소형: 800A 이하
    "B-FRAME": (58, 4),    # 중형: 1600A 이하
    "B-FRAME-L": (70, 4),  # 중대형
    "C-FRAME": (95, 2),    # 대형: 2000A 이상
}

ACB_LARGE_CASE_SPECS = {
    # HGN/UAN 개별 케이스
    "HGN": {
        1: (1500, 1100, 1200, 60),
        2: (1500, 1100, 1200, 60),
    },
    "UAN": {
        1: (1700, 1300, 1400, 80),
    },
    "DEFAULT": (1500, 1100, 1200, 60),
}

# === 혼합 팔레트 규격 ===
PALLET_SPECS = {
    "STANDARD": {
        "length": 1100,
        "width": 1100,
        "height": 1120,
        "max_net_weight_kg": 400,
        "pallet_weight_kg": 25,
        "wrapping_weight_kg": 5,
    },
    "LARGE": {
        "length": 1400,
        "width": 1100,
        "height": 1120,
        "max_net_weight_kg": 500,
        "pallet_weight_kg": 30,
        "wrapping_weight_kg": 5,
    },
}

# === 카테고리 우선순위 (팔레트 적재 순서) ===
CATEGORY_PACKING_PRIORITY = {
    "VCB": 1,
    "ACB_HGS": 2,
    "ACB_LARGE": 3,
    "MCCB": 4,
    "MC": 5,
    "RELAY": 6,
    "SPARE": 7,
}

# === 카테고리별 포장 방식 ===
PACKING_METHOD = {
    "VCB": "INDIVIDUAL_WOODEN",      # 개별 우든 케이스
    "ACB_HGS": "GROUP_WOODEN",       # 그룹 우든 케이스
    "ACB_LARGE": "INDIVIDUAL_WOODEN", # 개별 대형 케이스
    "MCCB": "MIXED_PALLET",          # 혼합 팔레트
    "MC": "MIXED_PALLET",
    "RELAY": "MIXED_PALLET",
    "SPARE": "MIXED_PALLET",
}

# === 카테고리 표시명 ===
CATEGORY_DISPLAY_NAMES = {
    "VCB": "VACUUM CIRCUIT BREAKER",
    "ACB_HGS": "AIR CIRCUIT BREAKER",
    "ACB_LARGE": "AIR CIRCUIT BREAKER",
    "MCCB": "MOLDED CASE CIRCUIT BREAKER",
    "MC": "MAGNETIC CONTACTOR",
    "RELAY": "THERMAL OVERLOAD RELAY",
    "SPARE": "SPARE PARTS",
}

# 복수형 변환 매핑
PLURAL_NAMES = {
    "VACUUM CIRCUIT BREAKER": "VACUUM CIRCUIT BREAKERS",
    "AIR CIRCUIT BREAKER": "AIR CIRCUIT BREAKERS",
    "MOLDED CASE CIRCUIT BREAKER": "MOLDED CASE CIRCUIT BREAKERS",
    "MAGNETIC CONTACTOR": "MAGNETIC CONTACTORS",
    "THERMAL OVERLOAD RELAY": "THERMAL OVERLOAD RELAYS",
    "SPARE PARTS": "SPARE PARTS",
}

# === Gross Weight 계산 비율 (케이스 타입별) ===
GROSS_WEIGHT_FACTORS = {
    "WOODEN_CASE": 1.15,   # 순중량 대비 15% 추가
    "PALLET": 1.08,        # 순중량 대비 8% 추가 (팔레트+랩)
}
