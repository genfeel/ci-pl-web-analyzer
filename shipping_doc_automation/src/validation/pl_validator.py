"""PL 자동 검증

생성된 PL의 정합성을 자동 검증:
- 수량 일치 (CI 총수량 = PL 총수량)
- 모델 누락 검사
- 중량 합리성 검사
- CBM 정합성
"""
from typing import Dict, List, Tuple

from src.models.data_models import CIDocument, PLDocument, PackedCase


class ValidationResult:
    def __init__(self):
        self.passed = True
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.metrics: Dict = {}

    def add_warning(self, msg: str):
        self.warnings.append(msg)

    def add_error(self, msg: str):
        self.errors.append(msg)
        self.passed = False

    def summary(self) -> str:
        lines = []
        status = "PASS" if self.passed else "FAIL"
        lines.append(f"=== 검증 결과: {status} ===")

        if self.metrics:
            lines.append("\n[지표]")
            for key, val in self.metrics.items():
                lines.append(f"  {key}: {val}")

        if self.errors:
            lines.append(f"\n[오류] ({len(self.errors)}건)")
            for e in self.errors:
                lines.append(f"  ✗ {e}")

        if self.warnings:
            lines.append(f"\n[경고] ({len(self.warnings)}건)")
            for w in self.warnings:
                lines.append(f"  △ {w}")

        if not self.errors and not self.warnings:
            lines.append("  모든 검증 항목 통과")

        return "\n".join(lines)


def validate_pl(ci_doc: CIDocument, pl_cases: List[PackedCase]) -> ValidationResult:
    """생성된 PL 검증

    Args:
        ci_doc: 원본 CI 문서
        pl_cases: 생성된 PL 케이스 리스트

    Returns:
        ValidationResult
    """
    result = ValidationResult()

    # 1. 수량 일치 검증
    ci_total = ci_doc.total_quantity
    pl_total = sum(c.total_quantity for c in pl_cases)
    result.metrics['CI 총수량'] = ci_total
    result.metrics['PL 총수량'] = pl_total
    result.metrics['케이스 수'] = len(pl_cases)

    if ci_total != pl_total:
        result.add_error(
            f"수량 불일치: CI={ci_total}, PL={pl_total} (차이: {ci_total - pl_total})"
        )

    # 2. 모델번호 매핑 검증
    ci_models = {}
    for item in ci_doc.items:
        key = item.model_number
        ci_models[key] = ci_models.get(key, 0) + item.quantity

    pl_models = {}
    for case in pl_cases:
        for pi in case.items:
            key = pi.ci_item.model_number
            pl_models[key] = pl_models.get(key, 0) + pi.quantity

    # 누락된 모델
    for model, qty in ci_models.items():
        if model not in pl_models:
            result.add_error(f"PL에서 누락된 모델: {model} (CI 수량: {qty})")
        elif pl_models[model] != qty:
            result.add_warning(
                f"모델 수량 불일치: {model} - CI={qty}, PL={pl_models[model]}"
            )

    # 3. 중량 합리성 검증
    total_net = sum(c.net_weight for c in pl_cases)
    total_gross = sum(c.gross_weight for c in pl_cases)

    result.metrics['총 순중량 (kg)'] = round(total_net, 2)
    result.metrics['총 총중량 (kg)'] = round(total_gross, 2)

    if total_net <= 0:
        result.add_error("총 순중량이 0 이하입니다.")

    if total_gross < total_net:
        result.add_error("총중량이 순중량보다 작습니다.")

    gross_ratio = total_gross / total_net if total_net > 0 else 0
    if gross_ratio > 1.5:
        result.add_warning(f"총중량/순중량 비율이 높습니다: {gross_ratio:.2f}")
    elif gross_ratio < 1.01 and total_net > 10:
        result.add_warning(f"총중량/순중량 비율이 너무 낮습니다: {gross_ratio:.2f}")

    # 4. CBM 검증
    total_cbm = sum(c.cbm for c in pl_cases)
    result.metrics['총 CBM'] = round(total_cbm, 3)

    if total_cbm <= 0:
        result.add_warning("총 CBM이 0입니다. 규격 정보를 확인하세요.")

    # 5. 케이스별 검증
    for case in pl_cases:
        if case.net_weight <= 0:
            result.add_warning(f"Case {case.case_no}: 순중량이 0")
        if not case.items:
            result.add_error(f"Case {case.case_no}: 빈 케이스")
        if case.dimensions == (0, 0, 0):
            result.add_warning(f"Case {case.case_no}: 규격 정보 없음")

    return result


def compare_with_actual_pl(
    generated_cases: List[PackedCase],
    actual_filepath: str,
) -> ValidationResult:
    """생성된 PL과 실제 PL 비교

    Args:
        generated_cases: 자동 생성된 케이스 리스트
        actual_filepath: 실제 PL 파일 경로

    Returns:
        비교 결과
    """
    from src.parser.pl_parser import parse_pl

    result = ValidationResult()
    actual_pl = parse_pl(actual_filepath)

    # 케이스 수 비교
    gen_count = len(generated_cases)
    act_count = len(actual_pl.cases)
    result.metrics['생성 케이스 수'] = gen_count
    result.metrics['실제 케이스 수'] = act_count

    if gen_count != act_count:
        result.add_warning(
            f"케이스 수 차이: 생성={gen_count}, 실제={act_count}"
        )

    # 총 수량 비교
    gen_qty = sum(c.total_quantity for c in generated_cases)
    act_qty = sum(c.total_quantity for c in actual_pl.cases)
    result.metrics['생성 총수량'] = gen_qty
    result.metrics['실제 총수량'] = act_qty

    if gen_qty != act_qty:
        result.add_warning(f"총수량 차이: 생성={gen_qty}, 실제={act_qty}")

    # 총 중량 비교
    gen_net = sum(c.net_weight for c in generated_cases)
    act_net = sum(c.net_weight for c in actual_pl.cases)
    if act_net > 0:
        weight_diff_pct = abs(gen_net - act_net) / act_net * 100
        result.metrics['순중량 차이(%)'] = round(weight_diff_pct, 1)
        if weight_diff_pct > 10:
            result.add_warning(f"순중량 차이 {weight_diff_pct:.1f}%: 생성={gen_net:.1f}kg, 실제={act_net:.1f}kg")

    return result
