"""포장 전략 테스트"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.models.data_models import CILineItem, ProductCategory
from src.packing.vcb_packer import pack_vcb
from src.packing.acb_packer import pack_acb_standard, pack_acb_large
from src.packing.mixed_pallet_packer import pack_mixed_pallet


def make_item(model, qty, category=ProductCategory.UNKNOWN, cat_header=""):
    return CILineItem(
        line_no=1, description=f"{model}-TEST",
        model_number=model, quantity=qty, unit="SET",
        unit_price=1.0, amount=float(qty),
        category=category, category_header=cat_header,
    )


class TestVCBPacker:
    """VCB 개별 포장 테스트"""

    def test_single_item(self):
        items = [make_item("HGV3141", 1, ProductCategory.VCB)]
        cases = pack_vcb(items)
        assert len(cases) == 1
        assert cases[0].total_quantity == 1
        assert cases[0].reason != ""
        assert "VCB 개별포장" in cases[0].reason

    def test_multiple_quantity(self):
        items = [make_item("HGV3141", 3, ProductCategory.VCB)]
        cases = pack_vcb(items)
        assert len(cases) == 3  # 3대 → 3케이스
        for case in cases:
            assert case.reason != ""
            assert "HGV3141" in case.reason

    def test_mixed_models(self):
        items = [
            make_item("HGV3141", 2, ProductCategory.VCB),
            make_item("HGV2141", 1, ProductCategory.VCB),
        ]
        cases = pack_vcb(items)
        assert len(cases) == 3  # 2 + 1 = 3케이스
        for case in cases:
            assert case.reason != ""

    def test_case_numbering(self):
        items = [make_item("HGV3141", 2, ProductCategory.VCB)]
        cases = pack_vcb(items, start_case_no=5)
        assert cases[0].case_no == 5
        assert cases[1].case_no == 6


class TestACBPacker:
    """ACB 포장 테스트"""

    def test_acb_standard_grouping(self):
        items = [
            make_item("HGS1033B", 6, ProductCategory.ACB_HGS, "AIR CIRCUIT BREAKER"),
        ]
        cases = pack_acb_standard(items)
        assert len(cases) >= 1
        total_qty = sum(c.total_quantity for c in cases)
        assert total_qty == 6
        for case in cases:
            assert case.reason != ""
            assert "ACB 그룹포장" in case.reason
            assert "FFD 적재" in case.reason

    def test_acb_standard_max_per_case(self):
        """케이스당 최대 수량 제한 테스트"""
        items = [
            make_item("HGS1033B", 12, ProductCategory.ACB_HGS, "AIR CIRCUIT BREAKER"),
        ]
        cases = pack_acb_standard(items)
        for case in cases:
            assert case.total_quantity <= 6  # A-frame 최대 6대
            assert case.reason != ""

    def test_acb_large_individual(self):
        items = [make_item("HGN2063", 2, ProductCategory.ACB_LARGE)]
        cases = pack_acb_large(items)
        assert len(cases) == 2
        for case in cases:
            assert case.reason != ""
            assert "ACB 대형 개별포장" in case.reason
            assert "HGN2063" in case.reason


class TestMixedPalletPacker:
    """혼합 팔레트 적재 테스트"""

    def test_single_category(self):
        items = [make_item("HGM100E", 100, ProductCategory.MCCB)]
        cases = pack_mixed_pallet(items)
        assert len(cases) >= 1
        total_qty = sum(c.total_quantity for c in cases)
        assert total_qty == 100
        for case in cases:
            assert case.reason != ""
            assert "혼합 팔레트" in case.reason

    def test_weight_limit(self):
        """팔레트당 400kg 제한 테스트"""
        # 100kg 짜리 10개 → 4000kg → 최소 10개 팔레트
        items = [make_item("HGM800E", 10, ProductCategory.MCCB)]
        cases = pack_mixed_pallet(items)
        for case in cases:
            assert case.net_weight <= 400 + 1  # 약간의 여유
            assert case.reason != ""

    def test_mixed_categories(self):
        items = [
            make_item("HGM100E", 50, ProductCategory.MCCB, "MOLDED CASE CIRCUIT BREAKER"),
            make_item("HGC9", 100, ProductCategory.MC, "MAGNETIC CONTACTOR"),
            make_item("HGT40", 50, ProductCategory.RELAY, "RELAY"),
        ]
        cases = pack_mixed_pallet(items)
        total_qty = sum(c.total_quantity for c in cases)
        assert total_qty == 200
        for case in cases:
            assert case.reason != ""
            assert "Greedy Bin Packing" in case.reason

    def test_empty_input(self):
        cases = pack_mixed_pallet([])
        assert len(cases) == 0
