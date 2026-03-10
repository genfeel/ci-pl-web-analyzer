"""합적 주문 처리

여러 주문을 하나의 선적으로 합칠 때, 주문별 독립 패킹 후 순차 케이스 번호 부여.
"""
from typing import Dict, List

from src.models.data_models import CIDocument, CILineItem, PackedCase, PLDocument
from src.packing.strategy_selector import select_and_pack


def pack_combined_orders(doc: CIDocument) -> PLDocument:
    """합적 주문 CI를 PL로 변환

    각 주문별로 독립 패킹 후, 순차 케이스 번호를 부여.
    """
    cases = select_and_pack(doc)

    pl_doc = PLDocument(
        filename=doc.filename.replace('CI', 'PL'),
        cases=cases,
        header_info=doc.header_info.copy(),
        order_numbers=doc.order_numbers,
        is_combined_order=doc.is_combined_order,
    )

    return pl_doc


def get_order_case_ranges(cases: List[PackedCase]) -> Dict[str, tuple]:
    """주문별 케이스 번호 범위 반환

    Returns:
        {'25022297-1': (1, 3), '25021874': (4, 5), ...}
    """
    ranges = {}
    for case in cases:
        order = case.order_number or "SINGLE"
        if order not in ranges:
            ranges[order] = (case.case_no, case.case_no)
        else:
            lo, hi = ranges[order]
            ranges[order] = (min(lo, case.case_no), max(hi, case.case_no))
    return ranges
