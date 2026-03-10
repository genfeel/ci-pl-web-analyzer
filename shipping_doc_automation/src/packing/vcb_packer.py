"""VCB(Vacuum Circuit Breaker) 개별 포장

규칙: 1대 1케이스, 모델별 규격 룩업
"""
from typing import List

from src.models.data_models import CILineItem, PackedCase, PackedItem, ProductCategory
from src.packing.weight_estimator import get_unit_weight, get_case_weight, get_case_dimensions


def pack_vcb(items: List[CILineItem], start_case_no: int = 1) -> List[PackedCase]:
    """VCB 품목을 개별 케이스로 포장

    Args:
        items: VCB 카테고리 품목 리스트
        start_case_no: 시작 케이스 번호

    Returns:
        PackedCase 리스트 (각 케이스에 1대)
    """
    cases = []
    case_no = start_case_no

    for item in items:
        unit_weight = get_unit_weight(item)
        dims = get_case_dimensions(ProductCategory.VCB, item.model_number)
        case_weight = get_case_weight(ProductCategory.VCB)

        # 수량만큼 개별 케이스 생성
        for _ in range(item.quantity):
            packed_item = PackedItem(
                ci_item=item,
                quantity=1,
                net_weight=round(unit_weight, 2),
            )

            reason = (
                f"VCB 개별포장: 1대/케이스 규칙 "
                f"({item.model_number}, 단중 {unit_weight:.1f}kg)"
            )

            case = PackedCase(
                case_no=case_no,
                case_type="WOODEN CASE",
                items=[packed_item],
                dimensions=dims,
                case_weight=round(case_weight, 2),
                category=ProductCategory.VCB,
                category_header=item.category_header or "VACUUM CIRCUIT BREAKER",
                order_number=item.order_number,
                reason=reason,
            )
            cases.append(case)
            case_no += 1

    return cases
