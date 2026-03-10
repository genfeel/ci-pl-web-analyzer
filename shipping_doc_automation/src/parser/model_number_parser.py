"""제품코드(모델번호) 패턴 분석 및 파싱"""
import re
from typing import Optional


# 제품코드 접두사 → 카테고리 매핑
MODEL_PREFIX_PATTERNS = {
    # VCB (Vacuum Circuit Breaker)
    r'^HGV\d{4}': 'VCB',

    # ACB - HGS (Air Circuit Breaker - Standard)
    r'^HGS\d{2,4}': 'ACB_HGS',

    # ACB - Large (HGN, UAN, UCB)
    r'^HGN\d{2,4}': 'ACB_LARGE',
    r'^UAN\d{2,4}': 'ACB_LARGE',
    r'^UCB\d{2,4}': 'ACB_LARGE',

    # MCCB (Molded Case Circuit Breaker)
    r'^HGM\d{2,4}': 'MCCB',
    r'^HGP\d{2,4}': 'MCCB',

    # MC (Magnetic Contactor)
    r'^HGC\d{1,4}': 'MC',

    # Relay (Thermal Overload Relay)
    r'^HGT\d{1,4}': 'RELAY',
    r'^HGR\d{1,4}': 'RELAY',
}

# 모델번호 전체 파싱 정규식
MODEL_NUMBER_REGEX = re.compile(
    r'(?P<prefix>[A-Z]{2,4})'
    r'(?P<frame_or_current>\d{1,4})'
    r'(?P<variant>[A-Z]*)'
    r'(?P<suffix>[\d\-/A-Z]*)',
    re.IGNORECASE
)

# ACB 프레임 타입 판별
ACB_FRAME_PATTERNS = {
    'A-FRAME': re.compile(r'HGS\d{2}[0-3]\d', re.IGNORECASE),  # 800A 이하
    'B-FRAME': re.compile(r'HGS\d{2}[4-6]\d', re.IGNORECASE),  # 1600A 이하
    'C-FRAME': re.compile(r'HGS\d{2}[7-9]\d', re.IGNORECASE),  # 2000A 이상
}

# MCCB 프레임 크기 판별 (전류값 기반)
MCCB_FRAME_MAP = {
    (0, 125): '100AF',
    (126, 250): '250AF',
    (251, 400): '400AF',
    (401, 630): '630AF',
    (631, 1000): '800AF',
}


def parse_model_number(model_str: str) -> dict:
    """모델번호 문자열에서 구조화된 정보 추출"""
    model_str = model_str.strip()
    result = {
        'original': model_str,
        'prefix': '',
        'category': 'UNKNOWN',
        'frame_or_current': '',
        'variant': '',
        'frame_type': '',
        'frame_size': '',
    }

    match = MODEL_NUMBER_REGEX.match(model_str)
    if not match:
        return result

    result['prefix'] = match.group('prefix').upper()
    result['frame_or_current'] = match.group('frame_or_current')
    result['variant'] = match.group('variant')

    # 카테고리 결정
    for pattern, category in MODEL_PREFIX_PATTERNS.items():
        if re.match(pattern, model_str, re.IGNORECASE):
            result['category'] = category
            break

    # ACB 프레임 타입 결정
    if result['category'] == 'ACB_HGS':
        for frame_type, pattern in ACB_FRAME_PATTERNS.items():
            if pattern.match(model_str):
                result['frame_type'] = frame_type
                break
        if not result['frame_type']:
            result['frame_type'] = 'A-FRAME'

    # MCCB 프레임 크기 결정
    if result['category'] == 'MCCB':
        try:
            current_val = int(result['frame_or_current'])
            for (lo, hi), frame_size in MCCB_FRAME_MAP.items():
                if lo <= current_val <= hi:
                    result['frame_size'] = frame_size
                    break
        except ValueError:
            result['frame_size'] = '100AF'

    return result


def extract_model_from_description(description: str) -> Optional[str]:
    """Description 텍스트에서 모델번호 추출

    패턴 예시:
    - "HGV3141-S1A0200TBN" → "HGV3141"
    - "HGS1033B-H4MXXX" → "HGS1033B"
    - "HGM100E-F3PTXXX" → "HGM100E"
    - "HGC9 AC110V" → "HGC9"
    """
    if not description:
        return None

    # 주요 제품 모델번호 패턴
    patterns = [
        r'(HGV\d{4}[A-Z]?)',
        r'(HGS\d{2,4}[A-Z]?)',
        r'(HGN\d{2,4}[A-Z]?)',
        r'(UAN\d{2,4}[A-Z]?)',
        r'(UCB\d{2,4}[A-Z]?)',
        r'(HGM\d{2,4}[A-Z]?)',
        r'(HGP\d{2,4}[A-Z]?)',
        r'(HGC\d{1,4})',
        r'(HGT\d{1,4})',
        r'(HGR\d{1,4})',
    ]

    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return match.group(1).upper()

    return None


def extract_current_rating(description: str) -> Optional[int]:
    """Description에서 전류 정격 추출 (예: 100A, 630AF)"""
    patterns = [
        r'(\d+)\s*AF\b',
        r'(\d+)\s*A\b',
        r'/(\d+)[A-Z]',
    ]
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                continue
    return None


def extract_poles(description: str) -> Optional[int]:
    """Description에서 극수 추출 (예: 3P, 4P)"""
    match = re.search(r'(\d)\s*[Pp](?:\b|[/\-])', description)
    if match:
        return int(match.group(1))
    return None


def get_weight_lookup_key(model_number: str) -> str:
    """제품DB 조회용 키 생성

    모델번호에서 중량 조회에 필요한 핵심 부분만 추출
    예: "HGM100E-F3PTXXX" → "HGM100"
        "HGC9 AC110V" → "HGC9"
        "HGV3141-S1A0200TBN" → "HGV3141"
    """
    parsed = parse_model_number(model_number)
    prefix = parsed['prefix']
    frame_or_current = parsed['frame_or_current']

    if prefix in ('HGV',):
        return f"{prefix}{frame_or_current}"
    elif prefix in ('HGS', 'HGN', 'UAN', 'UCB'):
        return f"{prefix}{frame_or_current}"
    elif prefix in ('HGM', 'HGP'):
        return f"{prefix}{frame_or_current}"
    elif prefix in ('HGC', 'HGT', 'HGR'):
        return f"{prefix}{frame_or_current}"

    return model_number.split('-')[0].split(' ')[0].upper()


def is_category_header(text: str) -> bool:
    """텍스트가 카테고리 헤더인지 판별

    카테고리 헤더 예시:
    - "VACUUM CIRCUIT BREAKER"
    - "AIR CIRCUIT BREAKER(ACB)"
    - "MOLDED CASE CIRCUIT BREAKER"
    - "MAGNETIC CONTACTOR"
    - "THERMAL OVERLOAD RELAY"
    - "SPARE PART FOR VCB"
    """
    header_patterns = [
        r'VACUUM\s+CIRCUIT\s+BREAKER',
        r'AIR\s+CIRCUIT\s+BREAKER',
        r'MOLDED\s+CASE\s+CIRCUIT\s+BREAKER',
        r'MOULDED\s+CASE\s+CIRCUIT\s+BREAKER',
        r'MAGNETIC\s+CONTACTOR',
        r'THERMAL\s+OVERLOAD\s+RELAY',
        r'EARTH\s+LEAKAGE',
        r'SPARE\s+PART',
        r'ACCESSORIES',
    ]
    text_upper = text.upper().strip()
    return any(re.search(p, text_upper) for p in header_patterns)


def detect_category_from_header(header_text: str) -> str:
    """카테고리 헤더 텍스트에서 카테고리 추출"""
    text = header_text.upper().strip()

    if 'VACUUM CIRCUIT BREAKER' in text or 'VCB' in text:
        return 'VCB'
    if 'AIR CIRCUIT BREAKER' in text or 'ACB' in text:
        return 'ACB'  # 추후 HGS/HGN 구분 필요
    if 'MOLDED CASE CIRCUIT BREAKER' in text or 'MOULDED CASE' in text or 'MCCB' in text:
        return 'MCCB'
    if 'MAGNETIC CONTACTOR' in text or 'MC' in text.split():
        return 'MC'
    if 'THERMAL OVERLOAD RELAY' in text or 'RELAY' in text:
        return 'RELAY'
    if 'SPARE' in text or 'ACCESSORIES' in text:
        return 'SPARE'

    return 'UNKNOWN'
