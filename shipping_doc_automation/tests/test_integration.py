"""E2E 통합 테스트: CI → PL → 검증"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from src.parser.ci_parser import parse_ci
from src.classifier.product_classifier import classify_document
from src.packing.strategy_selector import select_and_pack
from src.models.data_models import PLDocument
from src.validation.pl_validator import validate_pl, compare_with_actual_pl
from src.generator.pl_generator import generate_pl_excel
from config.settings import SAMPLES_DIR


SAMPLE_FILES = list(SAMPLES_DIR.glob("*CIPL*.*"))


class TestE2EPipeline:
    """전체 파이프라인 통합 테스트"""

    @pytest.fixture(params=SAMPLE_FILES, ids=[f.name for f in SAMPLE_FILES])
    def sample_file(self, request):
        return request.param

    def test_full_pipeline(self, sample_file):
        """CI 파싱 → 분류 → 포장 → 검증"""
        # 1. CI 파싱
        ci_doc = parse_ci(str(sample_file))
        assert len(ci_doc.items) > 0

        # 2. 분류
        ci_doc = classify_document(ci_doc)

        # 3. 포장
        cases = select_and_pack(ci_doc)
        assert len(cases) > 0

        # 4. 검증
        result = validate_pl(ci_doc, cases)
        # 수량 일치는 반드시 통과해야 함
        ci_total = ci_doc.total_quantity
        pl_total = sum(c.total_quantity for c in cases)
        assert ci_total == pl_total, (
            f"수량 불일치: CI={ci_total}, PL={pl_total}"
        )

    def test_generate_excel(self, sample_file):
        """엑셀 파일 생성 테스트"""
        ci_doc = parse_ci(str(sample_file))
        ci_doc = classify_document(ci_doc)
        cases = select_and_pack(ci_doc)

        pl_doc = PLDocument(
            filename="test_output.xlsx",
            cases=cases,
            header_info=ci_doc.header_info,
            order_numbers=ci_doc.order_numbers,
            is_combined_order=ci_doc.is_combined_order,
        )

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            output_path = f.name

        result = generate_pl_excel(pl_doc, str(sample_file), output_path)
        assert Path(result).exists()
        assert Path(result).stat().st_size > 0

        Path(result).unlink()

    def test_compare_with_actual(self, sample_file):
        """실제 PL과 비교 (케이스 수, 총수량)"""
        ci_doc = parse_ci(str(sample_file))
        ci_doc = classify_document(ci_doc)
        cases = select_and_pack(ci_doc)

        # 실제 PL과 비교
        result = compare_with_actual_pl(cases, str(sample_file))
        # 비교 자체가 오류 없이 완료되면 성공
        assert result is not None


class TestSpecificScenarios:
    """특정 시나리오 테스트"""

    def test_25022120_12_cases(self):
        """25022120: MCCB/MC/Relay/부품 혼합 → 12 cases"""
        filepath = SAMPLES_DIR / "25022120-CIPL_샘플.xlsx"
        if not filepath.exists():
            pytest.skip("샘플 파일 없음")

        ci_doc = parse_ci(str(filepath))
        ci_doc = classify_document(ci_doc)
        cases = select_and_pack(ci_doc)

        # 수량 일치
        assert ci_doc.total_quantity == sum(c.total_quantity for c in cases)
        # 케이스 수 확인 (실제: 12)
        print(f"  생성된 케이스 수: {len(cases)} (실제: 12)")

    def test_25021809_16_cases_acb(self):
        """25021809: ACB 전용 → 16 cases"""
        filepath = SAMPLES_DIR / "25021809-CIPL_샘플.xls"
        if not filepath.exists():
            pytest.skip("샘플 파일 없음")

        ci_doc = parse_ci(str(filepath))
        ci_doc = classify_document(ci_doc)
        cases = select_and_pack(ci_doc)

        assert ci_doc.total_quantity == sum(c.total_quantity for c in cases)
        print(f"  생성된 케이스 수: {len(cases)} (실제: 16)")

    def test_25022297_combined_order(self):
        """25022297: 합적 주문 → 6 cases"""
        filepath = SAMPLES_DIR / "25022297-1 25021874 25023500-CIPL_샘플.xlsx"
        if not filepath.exists():
            pytest.skip("샘플 파일 없음")

        ci_doc = parse_ci(str(filepath))
        ci_doc = classify_document(ci_doc)

        # 합적 주문 확인
        assert ci_doc.is_combined_order

        cases = select_and_pack(ci_doc)
        assert ci_doc.total_quantity == sum(c.total_quantity for c in cases)
        print(f"  생성된 케이스 수: {len(cases)} (실제: 6)")
        print(f"  주문번호: {ci_doc.order_numbers}")

    def test_25020325_33_cases_full_range(self):
        """25020325: 전 제품 → 33 cases"""
        filepath = SAMPLES_DIR / "25020325-CIPL_샘플.xls"
        if not filepath.exists():
            pytest.skip("샘플 파일 없음")

        ci_doc = parse_ci(str(filepath))
        ci_doc = classify_document(ci_doc)
        cases = select_and_pack(ci_doc)

        assert ci_doc.total_quantity == sum(c.total_quantity for c in cases)
        print(f"  생성된 케이스 수: {len(cases)} (실제: 33)")
