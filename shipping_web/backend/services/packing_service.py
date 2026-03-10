"""CI→PL 파이프라인 래핑 서비스

기존 shipping_doc_automation의 파이프라인을 웹 서비스용으로 래핑.
"""
import uuid
from pathlib import Path
from typing import Dict, Any

from src.parser.ci_parser import parse_ci
from src.classifier.product_classifier import classify_document
from src.packing.strategy_selector import select_and_pack
from src.generator.pl_generator import generate_pl_excel
from src.models.data_models import PLDocument, PackedCase
from src.validation.pl_validator import validate_pl

# 메모리 캐시: result_id → {ci_doc, cases, pl_doc, validation, ci_filepath}
_result_cache: Dict[str, Dict[str, Any]] = {}

STORAGE_DIR = Path(__file__).parent.parent / "storage"
UPLOADS_DIR = STORAGE_DIR / "uploads"
RESULTS_DIR = STORAGE_DIR / "results"


def process_ci_file(filepath: str, original_filename: str) -> dict:
    """CI 파일을 파싱하고 포장 파이프라인을 실행하여 결과를 반환"""
    # 1. CI 파싱
    ci_doc = parse_ci(filepath)

    # 2. 제품 분류
    ci_doc = classify_document(ci_doc)

    # 3. 포장 전략 실행
    cases = select_and_pack(ci_doc)

    # 4. PLDocument 생성
    pl_doc = PLDocument(
        filename=Path(original_filename).stem + "_PL.xlsx",
        cases=cases,
        header_info=ci_doc.header_info.copy(),
        order_numbers=ci_doc.order_numbers,
        is_combined_order=ci_doc.is_combined_order,
    )

    # 5. 검증
    validation = validate_pl(ci_doc, cases)

    # 6. 결과 캐시
    result_id = uuid.uuid4().hex[:12]
    _result_cache[result_id] = {
        "ci_doc": ci_doc,
        "cases": cases,
        "pl_doc": pl_doc,
        "validation": validation,
        "ci_filepath": filepath,
        "original_filename": original_filename,
    }

    return _build_response(result_id, ci_doc, cases, pl_doc, validation)


def get_cached_result(result_id: str) -> dict | None:
    """캐시된 결과 조회"""
    cached = _result_cache.get(result_id)
    if not cached:
        return None
    return _build_response(
        result_id,
        cached["ci_doc"],
        cached["cases"],
        cached["pl_doc"],
        cached["validation"],
    )


def generate_pl_file(result_id: str) -> str | None:
    """캐시된 결과로 PL 엑셀 파일 생성 후 경로 반환"""
    cached = _result_cache.get(result_id)
    if not cached:
        return None

    pl_doc = cached["pl_doc"]
    ci_filepath = cached["ci_filepath"]

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = str(RESULTS_DIR / pl_doc.filename)

    generate_pl_excel(pl_doc, ci_filepath, output_path)
    return output_path


def get_cases_for_loading(result_id: str) -> list[PackedCase] | None:
    """컨테이너 적재용 케이스 데이터 반환"""
    cached = _result_cache.get(result_id)
    if not cached:
        return None
    return cached["cases"]


def _build_response(result_id, ci_doc, cases, pl_doc, validation) -> dict:
    """API 응답 딕셔너리 구성"""
    cases_data = []
    for case in cases:
        items_data = []
        for pi in case.items:
            items_data.append({
                "description": pi.ci_item.description,
                "model_number": pi.ci_item.model_number,
                "quantity": pi.quantity,
                "net_weight": round(pi.net_weight, 2),
            })

        cases_data.append({
            "case_no": case.case_no,
            "case_type": case.case_type,
            "category": case.category.value,
            "reason": case.reason or "",
            "total_quantity": case.total_quantity,
            "net_weight": round(case.net_weight, 2),
            "gross_weight": round(case.gross_weight, 2),
            "dimensions": list(case.dimensions),
            "cbm": round(case.cbm, 3),
            "items": items_data,
        })

    # 카테고리별 요약
    cat_summary = {}
    for case in cases:
        cat = case.category.value
        if cat not in cat_summary:
            cat_summary[cat] = {
                "category": cat,
                "case_count": 0,
                "total_quantity": 0,
                "total_net_weight": 0.0,
                "total_gross_weight": 0.0,
            }
        cat_summary[cat]["case_count"] += 1
        cat_summary[cat]["total_quantity"] += case.total_quantity
        cat_summary[cat]["total_net_weight"] += case.net_weight
        cat_summary[cat]["total_gross_weight"] += case.gross_weight

    for v in cat_summary.values():
        v["total_net_weight"] = round(v["total_net_weight"], 2)
        v["total_gross_weight"] = round(v["total_gross_weight"], 2)

    return {
        "result_id": result_id,
        "filename": ci_doc.filename,
        "total_cases": pl_doc.total_cases,
        "total_quantity": pl_doc.total_quantity,
        "total_net_weight": pl_doc.total_net_weight,
        "total_gross_weight": pl_doc.total_gross_weight,
        "total_cbm": pl_doc.total_cbm,
        "is_combined_order": ci_doc.is_combined_order,
        "order_numbers": ci_doc.order_numbers,
        "cases": cases_data,
        "category_summary": list(cat_summary.values()),
        "validation": {
            "passed": validation.passed,
            "errors": validation.errors,
            "warnings": validation.warnings,
            "metrics": validation.metrics,
        },
    }
