"""CI 파서 테스트"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from src.parser.ci_parser import parse_ci
from src.models.data_models import ProductCategory
from config.settings import SAMPLES_DIR


SAMPLE_FILES = list(SAMPLES_DIR.glob("*CIPL*.*"))


class TestCIParser:
    """CI 파서 기본 테스트"""

    @pytest.fixture(params=SAMPLE_FILES, ids=[f.name for f in SAMPLE_FILES])
    def ci_doc(self, request):
        return parse_ci(str(request.param))

    def test_parse_not_empty(self, ci_doc):
        """파싱 결과가 비어있지 않은지 확인"""
        assert len(ci_doc.items) > 0, "파싱된 품목이 없습니다"

    def test_all_items_have_quantity(self, ci_doc):
        """모든 품목에 수량이 있는지 확인"""
        for item in ci_doc.items:
            assert item.quantity > 0, f"수량 0 품목: {item.description}"

    def test_all_items_have_description(self, ci_doc):
        """모든 품목에 설명이 있는지 확인"""
        for item in ci_doc.items:
            assert item.description, f"설명 없음: line {item.line_no}"

    def test_total_quantity_positive(self, ci_doc):
        """총 수량이 양수인지 확인"""
        assert ci_doc.total_quantity > 0


class TestSpecificSamples:
    """특정 샘플 파일별 테스트"""

    def test_25022120_mixed_items(self):
        """25022120: MC/Relay/MCCB/SPARE 혼합"""
        filepath = SAMPLES_DIR / "25022120-CIPL_샘플.xlsx"
        if not filepath.exists():
            pytest.skip("샘플 파일 없음")
        doc = parse_ci(str(filepath))
        categories = set(item.category for item in doc.items)
        assert len(categories) >= 2, f"최소 2개 카테고리 필요, 발견: {categories}"

    def test_25021809_acb_only(self):
        """25021809: 순수 ACB 주문"""
        filepath = SAMPLES_DIR / "25021809-CIPL_샘플.xls"
        if not filepath.exists():
            pytest.skip("샘플 파일 없음")
        doc = parse_ci(str(filepath))
        assert doc.total_quantity > 0
        # 대부분 ACB
        acb_count = sum(1 for item in doc.items
                       if item.category in (ProductCategory.ACB_HGS, ProductCategory.ACB_LARGE))
        assert acb_count > 0, "ACB 품목이 없습니다"

    def test_25022297_combined_order(self):
        """25022297: 합적 주문 (3주문)"""
        filepath = SAMPLES_DIR / "25022297-1 25021874 25023500-CIPL_샘플.xlsx"
        if not filepath.exists():
            pytest.skip("샘플 파일 없음")
        doc = parse_ci(str(filepath))
        assert doc.is_combined_order, "합적 주문으로 감지되어야 합니다"
        assert len(doc.order_numbers) >= 2, f"최소 2개 주문번호 필요: {doc.order_numbers}"

    def test_25020325_full_product_range(self):
        """25020325: 전 제품 포함 (VCB+ACB+MCCB+MC+Relay)"""
        filepath = SAMPLES_DIR / "25020325-CIPL_샘플.xls"
        if not filepath.exists():
            pytest.skip("샘플 파일 없음")
        doc = parse_ci(str(filepath))
        categories = set(item.category.value for item in doc.items)
        # VCB, ACB, MCCB, MC, RELAY 중 최소 3개
        assert len(categories) >= 3, f"최소 3개 카테고리 필요: {categories}"

    def test_25021818_custom_sheet_name(self):
        """25021818: 시트명에 주문번호 포함"""
        filepath = SAMPLES_DIR / "25021818-1-CIPL_샘플.xlsx"
        if not filepath.exists():
            pytest.skip("샘플 파일 없음")
        doc = parse_ci(str(filepath))
        assert len(doc.items) > 0
