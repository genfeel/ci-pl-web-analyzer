"""합적 주문 분리기

합적 주문(복수 주문번호)을 주문별로 분리하고,
각 주문 내 품목을 카테고리별로 그룹핑.
"""
from typing import Dict, List
from src.models.data_models import CIDocument, CILineItem, ProductCategory


def split_by_order(doc: CIDocument) -> Dict[str, List[CILineItem]]:
    """합적 주문을 주문번호별로 분리"""
    if not doc.is_combined_order:
        return {"SINGLE": doc.items}

    orders = {}
    for item in doc.items:
        order = item.order_number or "UNKNOWN"
        if order not in orders:
            orders[order] = []
        orders[order].append(item)

    return orders


def group_by_category(items: List[CILineItem]) -> Dict[ProductCategory, List[CILineItem]]:
    """품목 리스트를 카테고리별로 그룹핑"""
    groups = {}
    for item in items:
        cat = item.category
        if cat not in groups:
            groups[cat] = []
        groups[cat].append(item)
    return groups


def get_packing_groups(doc: CIDocument) -> List[dict]:
    """패킹에 필요한 그룹 정보 생성

    Returns:
        list of {
            'order_number': str,
            'category': ProductCategory,
            'items': list[CILineItem],
            'packing_method': str,
        }
    """
    from config.packing_constraints import PACKING_METHOD

    groups = []
    orders = split_by_order(doc)

    for order_num, items in orders.items():
        cat_groups = group_by_category(items)

        for cat, cat_items in cat_groups.items():
            method = PACKING_METHOD.get(cat.value, 'MIXED_PALLET')
            groups.append({
                'order_number': order_num,
                'category': cat,
                'items': cat_items,
                'packing_method': method,
            })

    # 카테고리 우선순위로 정렬
    from config.packing_constraints import CATEGORY_PACKING_PRIORITY
    groups.sort(key=lambda g: CATEGORY_PACKING_PRIORITY.get(g['category'].value, 99))

    return groups
