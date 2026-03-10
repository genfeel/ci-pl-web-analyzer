"""포장 전략 라우터

품목 분류 결과에 따라 적절한 Packer를 조합하여 전체 케이스 리스트 생성.
"""
from typing import List

from src.models.data_models import CIDocument, PackedCase, ProductCategory
from src.classifier.product_classifier import classify_document
from src.classifier.order_splitter import split_by_order, group_by_category
from src.packing.vcb_packer import pack_vcb
from src.packing.acb_packer import pack_acb_standard, pack_acb_large
from src.packing.mixed_pallet_packer import pack_mixed_pallet
from config.packing_constraints import CATEGORY_PACKING_PRIORITY


# 혼합 팔레트 대상 카테고리
MIXED_PALLET_CATEGORIES = {
    ProductCategory.MCCB,
    ProductCategory.MC,
    ProductCategory.RELAY,
    ProductCategory.SPARE,
    ProductCategory.UNKNOWN,
}


def select_and_pack(doc: CIDocument) -> List[PackedCase]:
    """CI 문서를 분석하여 최적 포장 전략으로 전체 케이스 생성

    전략:
    1. 주문별 분리 (합적 주문 대응)
    2. 카테고리별 그룹핑
    3. 카테고리에 맞는 Packer 호출
    4. 순차 케이스 번호 부여
    """
    # 제품 분류
    doc = classify_document(doc)

    all_cases = []
    case_no = 1

    if doc.is_combined_order:
        # 합적 주문: 주문별로 독립 패킹
        orders = split_by_order(doc)
        for order_num, items in orders.items():
            order_cases = _pack_items_by_category(items, case_no)
            # 주문번호 설정
            for c in order_cases:
                c.order_number = order_num
            all_cases.extend(order_cases)
            case_no += len(order_cases)
    else:
        # 단일 주문: 전체 품목 패킹
        all_cases = _pack_items_by_category(doc.items, case_no)

    # 케이스 번호 재정렬
    for i, case in enumerate(all_cases, 1):
        case.case_no = i

    return all_cases


def _pack_items_by_category(items: list, start_case_no: int) -> List[PackedCase]:
    """품목을 카테고리별로 분리하여 적절한 Packer로 포장"""
    cat_groups = group_by_category(items)
    all_cases = []
    case_no = start_case_no

    # 카테고리 우선순위 순으로 처리
    sorted_cats = sorted(
        cat_groups.keys(),
        key=lambda c: CATEGORY_PACKING_PRIORITY.get(c.value, 99)
    )

    # 혼합 팔레트 대상 품목 수집
    mixed_items = []

    for cat in sorted_cats:
        cat_items = cat_groups[cat]

        if cat == ProductCategory.VCB:
            cases = pack_vcb(cat_items, case_no)
            all_cases.extend(cases)
            case_no += len(cases)

        elif cat == ProductCategory.ACB_HGS:
            cases = pack_acb_standard(cat_items, case_no)
            all_cases.extend(cases)
            case_no += len(cases)

        elif cat == ProductCategory.ACB_LARGE:
            cases = pack_acb_large(cat_items, case_no)
            all_cases.extend(cases)
            case_no += len(cases)

        elif cat in MIXED_PALLET_CATEGORIES:
            mixed_items.extend(cat_items)

        else:
            # 기타: 혼합 팔레트로 처리
            mixed_items.extend(cat_items)

    # 혼합 팔레트 처리
    if mixed_items:
        cases = pack_mixed_pallet(mixed_items, case_no)
        all_cases.extend(cases)

    return all_cases
