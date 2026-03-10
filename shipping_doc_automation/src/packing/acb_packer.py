"""ACB(Air Circuit Breaker) 포장

HGS: 그룹 우든포장 (First-Fit Decreasing, 최대 4~6대/case, 프레임별)
HGN/UAN/UCB: 개별 대형 케이스
"""
from typing import List

from src.models.data_models import CILineItem, PackedCase, PackedItem, ProductCategory
from src.packing.weight_estimator import get_unit_weight, get_case_weight, get_case_dimensions
from src.classifier.product_classifier import get_acb_frame_type
from config.packing_constraints import ACB_STANDARD_CASE, ACB_FRAME_SPECS


def pack_acb_standard(items: List[CILineItem], start_case_no: int = 1) -> List[PackedCase]:
    """HGS ACB를 프레임별 그룹 케이스로 포장 (First-Fit Decreasing)

    Args:
        items: ACB_HGS 카테고리 품목 리스트
        start_case_no: 시작 케이스 번호

    Returns:
        PackedCase 리스트
    """
    # 프레임 타입별 그룹핑
    frame_groups = {}
    for item in items:
        frame = get_acb_frame_type(item)
        if frame not in frame_groups:
            frame_groups[frame] = []
        frame_groups[frame].append(item)

    cases = []
    case_no = start_case_no

    for frame_type, frame_items in frame_groups.items():
        # 프레임별 최대 적재 수
        frame_spec = ACB_FRAME_SPECS.get(frame_type, ACB_FRAME_SPECS.get('A-FRAME'))
        max_per_case = frame_spec[1]

        # 개별 유닛으로 확장 (수량 > 1인 경우)
        units = []
        for item in frame_items:
            unit_weight = get_unit_weight(item)
            for _ in range(item.quantity):
                units.append((item, unit_weight))

        # 무게 기준 내림차순 정렬 (FFD)
        units.sort(key=lambda x: x[1], reverse=True)

        # First-Fit Decreasing Bin Packing
        bins = []  # list of list of (item, weight)

        for item, weight in units:
            placed = False
            for bin_items in bins:
                if len(bin_items) < max_per_case:
                    bin_items.append((item, weight))
                    placed = True
                    break
            if not placed:
                bins.append([(item, weight)])

        # 빈 → 케이스 변환
        dims = get_case_dimensions(ProductCategory.ACB_HGS)
        case_weight = get_case_weight(ProductCategory.ACB_HGS)

        for bin_items in bins:
            # 같은 모델 그룹핑
            model_qty = {}
            for item, weight in bin_items:
                key = item.model_number
                if key not in model_qty:
                    model_qty[key] = {'item': item, 'qty': 0, 'unit_weight': weight}
                model_qty[key]['qty'] += 1

            packed_items = []
            for key, info in model_qty.items():
                packed_items.append(PackedItem(
                    ci_item=info['item'],
                    quantity=info['qty'],
                    net_weight=round(info['unit_weight'] * info['qty'], 2),
                ))

            total_nw = sum(pi.net_weight for pi in packed_items)
            total_qty = sum(pi.quantity for pi in packed_items)
            reason = (
                f"ACB 그룹포장: {frame_type} FFD 적재 "
                f"({total_qty}/{max_per_case}대, N.W={total_nw:.1f}kg)"
            )

            case = PackedCase(
                case_no=case_no,
                case_type="WOODEN CASE",
                items=packed_items,
                dimensions=dims,
                case_weight=round(case_weight, 2),
                category=ProductCategory.ACB_HGS,
                category_header=frame_items[0].category_header or "AIR CIRCUIT BREAKER",
                order_number=frame_items[0].order_number,
                reason=reason,
            )
            cases.append(case)
            case_no += 1

    return cases


def pack_acb_large(items: List[CILineItem], start_case_no: int = 1) -> List[PackedCase]:
    """HGN/UAN/UCB 개별 대형 케이스 포장

    Args:
        items: ACB_LARGE 카테고리 품목 리스트
        start_case_no: 시작 케이스 번호

    Returns:
        PackedCase 리스트
    """
    cases = []
    case_no = start_case_no

    for item in items:
        unit_weight = get_unit_weight(item)
        dims = get_case_dimensions(ProductCategory.ACB_LARGE, item.model_number)
        case_weight = get_case_weight(ProductCategory.ACB_LARGE)

        for _ in range(item.quantity):
            packed_item = PackedItem(
                ci_item=item,
                quantity=1,
                net_weight=round(unit_weight, 2),
            )

            reason = (
                f"ACB 대형 개별포장: 1대/케이스 "
                f"({item.model_number}, 단중 {unit_weight:.1f}kg)"
            )

            case = PackedCase(
                case_no=case_no,
                case_type="WOODEN CASE",
                items=[packed_item],
                dimensions=dims,
                case_weight=round(case_weight, 2),
                category=ProductCategory.ACB_LARGE,
                category_header=item.category_header or "AIR CIRCUIT BREAKER",
                order_number=item.order_number,
                reason=reason,
            )
            cases.append(case)
            case_no += 1

    return cases
