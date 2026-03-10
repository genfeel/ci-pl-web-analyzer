"""제품 분류기 테스트"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.models.data_models import CILineItem, ProductCategory
from src.classifier.product_classifier import classify_item, get_acb_frame_type
from src.parser.model_number_parser import parse_model_number, extract_model_from_description


class TestModelNumberParser:
    """모델번호 파서 테스트"""

    @pytest.mark.parametrize("model,expected_cat", [
        ("HGV3141", "VCB"),
        ("HGS1033B", "ACB_HGS"),
        ("HGN2063", "ACB_LARGE"),
        ("HGM100E", "MCCB"),
        ("HGP250E", "MCCB"),
        ("HGC9", "MC"),
        ("HGT40", "RELAY"),
    ])
    def test_category_detection(self, model, expected_cat):
        parsed = parse_model_number(model)
        assert parsed['category'] == expected_cat

    @pytest.mark.parametrize("desc,expected_model", [
        ("HGV3141-S1A0200TBN", "HGV3141"),
        ("HGS1033B-H4MXXX", "HGS1033B"),
        ("HGM100E-F3PTXXX", "HGM100E"),
        ("HGC9 AC110V", "HGC9"),
    ])
    def test_model_extraction(self, desc, expected_model):
        model = extract_model_from_description(desc)
        assert model == expected_model


class TestProductClassifier:
    """제품 분류기 테스트"""

    def _make_item(self, model="", desc="", cat_header=""):
        return CILineItem(
            line_no=1, description=desc or model,
            model_number=model, quantity=1, unit="SET",
            unit_price=1.0, amount=1.0,
            category_header=cat_header,
        )

    def test_vcb_classification(self):
        item = self._make_item("HGV3141", cat_header="VACUUM CIRCUIT BREAKER")
        assert classify_item(item) == ProductCategory.VCB

    def test_acb_hgs_classification(self):
        item = self._make_item("HGS1033B", cat_header="AIR CIRCUIT BREAKER")
        assert classify_item(item) == ProductCategory.ACB_HGS

    def test_acb_large_classification(self):
        item = self._make_item("HGN2063", cat_header="AIR CIRCUIT BREAKER")
        assert classify_item(item) == ProductCategory.ACB_LARGE

    def test_mccb_classification(self):
        item = self._make_item("HGM100E", cat_header="MOLDED CASE CIRCUIT BREAKER")
        assert classify_item(item) == ProductCategory.MCCB

    def test_mc_classification(self):
        item = self._make_item("HGC9", cat_header="MAGNETIC CONTACTOR")
        assert classify_item(item) == ProductCategory.MC

    def test_relay_classification(self):
        item = self._make_item("HGT40", cat_header="THERMAL OVERLOAD RELAY")
        assert classify_item(item) == ProductCategory.RELAY

    def test_spare_classification(self):
        item = self._make_item("HGC9", cat_header="SPARE PART FOR MAGNETIC CONTACTOR")
        assert classify_item(item) == ProductCategory.SPARE

    def test_acb_frame_type(self):
        item = self._make_item("HGS1033B")
        item.category = ProductCategory.ACB_HGS
        frame = get_acb_frame_type(item)
        assert frame in ('A-FRAME', 'B-FRAME', 'C-FRAME')
