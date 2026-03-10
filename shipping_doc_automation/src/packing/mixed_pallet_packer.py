"""혼합 팔레트 적재 (MCCB/MC/Relay/부품)

알고리즘:
1. 전체 품목을 카테고리별 정렬 (MCCB→MC→Relay→부품 순)
2. 무게 기준 내림차순 정렬
3. Greedy Bin Packing: 팔레트당 순중량 400kg 제한
4. 대형 제품 우선 배치 → 남은 공간에 소형 제품 채움
"""
from typing import List, Tuple

from src.models.data_models import CILineItem, PackedCase, PackedItem, ProductCategory
from src.packing.weight_estimator import get_unit_weight, get_case_weight, get_case_dimensions
from config.packing_constraints import PALLET_SPECS, CATEGORY_PACKING_PRIORITY


# 팔레트 최대 순중량
MAX_NET_WEIGHT = PALLET_SPECS['STANDARD']['max_net_weight_kg']


def pack_mixed_pallet(items: List[CILineItem], start_case_no: int = 1) -> List[PackedCase]:
    """MCCB/MC/Relay/부품을 혼합 팔레트로 적재

    Args:
        items: 혼합 팔레트 대상 품목 리스트
        start_case_no: 시작 케이스 번호

    Returns:
        PackedCase 리스트
    """
    if not items:
        return []

    # 각 품목의 단위중량 계산 및 개별 유닛으로 확장
    units = []  # (item, unit_weight, total_weight_for_all)
    for item in items:
        unit_weight = get_unit_weight(item)
        units.append((item, unit_weight, item.quantity))

    # 카테고리 우선순위 → 무게 내림차순 정렬
    units.sort(key=lambda x: (
        CATEGORY_PACKING_PRIORITY.get(x[0].category.value, 99),
        -x[1],
    ))

    # Greedy Bin Packing
    bins = []  # list of {'items': [(item, unit_weight, qty)], 'total_weight': float}

    for item, unit_weight, total_qty in units:
        remaining_qty = total_qty

        while remaining_qty > 0:
            placed = False

            # 기존 팔레트에 추가 시도
            for pallet in bins:
                available_weight = MAX_NET_WEIGHT - pallet['total_weight']
                if available_weight <= 0:
                    continue

                # 넣을 수 있는 최대 수량
                max_qty = int(available_weight / unit_weight) if unit_weight > 0 else remaining_qty
                qty_to_add = min(remaining_qty, max(1, max_qty))

                if qty_to_add > 0 and (unit_weight * qty_to_add) <= available_weight + 0.01:
                    pallet['items'].append((item, unit_weight, qty_to_add))
                    pallet['total_weight'] += unit_weight * qty_to_add
                    remaining_qty -= qty_to_add
                    placed = True
                    break

            if not placed:
                # 새 팔레트 생성
                qty_for_new = remaining_qty
                if unit_weight > 0:
                    max_qty = int(MAX_NET_WEIGHT / unit_weight)
                    qty_for_new = min(remaining_qty, max(1, max_qty))

                bins.append({
                    'items': [(item, unit_weight, qty_for_new)],
                    'total_weight': unit_weight * qty_for_new,
                })
                remaining_qty -= qty_for_new

    # 빈 → PackedCase 변환
    cases = []
    case_no = start_case_no
    dims = get_case_dimensions(ProductCategory.MCCB)
    base_case_weight = get_case_weight(ProductCategory.MCCB)

    for pallet in bins:
        # 같은 모델 그룹핑
        model_items = {}
        for item, unit_weight, qty in pallet['items']:
            key = (item.model_number, item.description)
            if key not in model_items:
                model_items[key] = {
                    'item': item,
                    'qty': 0,
                    'unit_weight': unit_weight,
                }
            model_items[key]['qty'] += qty

        packed_items = []
        for key, info in model_items.items():
            packed_items.append(PackedItem(
                ci_item=info['item'],
                quantity=info['qty'],
                net_weight=round(info['unit_weight'] * info['qty'], 2),
            ))

        # 카테고리별 정렬 (MCCB→MC→RELAY→SPARE)
        packed_items.sort(key=lambda pi: (
            CATEGORY_PACKING_PRIORITY.get(pi.ci_item.category.value, 99),
            -pi.net_weight,
        ))

        # 팔레트 순중량에 따라 규격 결정
        total_net = sum(pi.net_weight for pi in packed_items)
        if total_net > 400:
            dims = tuple(PALLET_SPECS['LARGE']['length':'height'])
            case_w = PALLET_SPECS['LARGE']['pallet_weight_kg'] + PALLET_SPECS['LARGE']['wrapping_weight_kg']
        else:
            case_w = base_case_weight

        # 주요 카테고리 결정 (가장 무거운 품목 기준)
        main_category = packed_items[0].ci_item.category if packed_items else ProductCategory.MCCB
        main_header = packed_items[0].ci_item.category_header if packed_items else "MOLDED CASE CIRCUIT BREAKER"

        n_types = len(model_items)
        n_units = sum(pi.quantity for pi in packed_items)
        reason = (
            f"혼합 팔레트: Greedy Bin Packing "
            f"({n_types}종 {n_units}대, N.W={total_net:.1f}/{MAX_NET_WEIGHT}kg)"
        )

        case = PackedCase(
            case_no=case_no,
            case_type="PALLET",
            items=packed_items,
            dimensions=dims,
            case_weight=round(case_w, 2),
            category=main_category,
            category_header=main_header,
            order_number=packed_items[0].ci_item.order_number if packed_items else '',
            reason=reason,
        )
        cases.append(case)
        case_no += 1

    return cases
