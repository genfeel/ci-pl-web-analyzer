"""CLI 진입점 - 선적서류 자동 변환 시스템

사용법:
    python -m cli.main generate <CI파일> [-o 출력경로]
    python -m cli.main validate <CI파일> <PL파일>
    python -m cli.main train <PL파일들...>
    python -m cli.main compare <CI파일> <실제PL파일>
"""
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import click

from src.parser.ci_parser import parse_ci
from src.classifier.product_classifier import classify_document
from src.packing.strategy_selector import select_and_pack
from src.generator.pl_generator import generate_pl_excel, generate_pl_from_template
from src.models.data_models import PLDocument
from src.validation.pl_validator import validate_pl, compare_with_actual_pl
from config.settings import OUTPUT_DIR


@click.group()
@click.version_option(version='0.1.0')
def cli():
    """선적서류(CI→PL) 자동 변환 시스템

    HD현대일렉트릭 배전전략영업과 선적서류 자동화 프로토타입
    """
    pass


@cli.command()
@click.argument('ci_file', type=click.Path(exists=True))
@click.option('-o', '--output', 'output_path', type=click.Path(), default=None,
              help='출력 파일 경로 (기본: output/<원본명>_PL.xlsx)')
@click.option('--template/--no-template', default=False,
              help='CI 파일의 PL 시트를 템플릿으로 사용')
@click.option('-v', '--verbose', is_flag=True, help='상세 출력')
def generate(ci_file, output_path, template, verbose):
    """CI 엑셀 파일에서 PL을 자동 생성합니다."""
    ci_path = Path(ci_file)
    click.echo(f"\n📄 CI 파일 파싱: {ci_path.name}")

    # 1. CI 파싱
    ci_doc = parse_ci(str(ci_path))
    click.echo(f"   품목 수: {len(ci_doc.items)}")
    click.echo(f"   총 수량: {ci_doc.total_quantity}")
    click.echo(f"   합적 주문: {'예' if ci_doc.is_combined_order else '아니오'}")

    if ci_doc.is_combined_order:
        click.echo(f"   주문번호: {', '.join(ci_doc.order_numbers)}")

    # 2. 제품 분류
    ci_doc = classify_document(ci_doc)

    if verbose:
        cat_counts = {}
        for item in ci_doc.items:
            cat = item.category.value
            cat_counts[cat] = cat_counts.get(cat, 0) + item.quantity
        click.echo(f"\n   카테고리별 수량:")
        for cat, cnt in sorted(cat_counts.items()):
            click.echo(f"     {cat}: {cnt}")

    # 3. 포장 전략 실행
    click.echo(f"\n📦 포장 전략 실행 중...")
    cases = select_and_pack(ci_doc)

    # PLDocument 생성
    pl_doc = PLDocument(
        filename=ci_path.stem + '_PL.xlsx',
        cases=cases,
        header_info=ci_doc.header_info.copy(),
        order_numbers=ci_doc.order_numbers,
        is_combined_order=ci_doc.is_combined_order,
    )

    click.echo(f"   케이스 수: {pl_doc.total_cases}")
    click.echo(f"   총 순중량: {pl_doc.total_net_weight:.2f} kg")
    click.echo(f"   총 총중량: {pl_doc.total_gross_weight:.2f} kg")
    click.echo(f"   총 CBM: {pl_doc.total_cbm:.3f}")

    if verbose:
        click.echo(f"\n   케이스별 상세:")
        for case in cases:
            items_desc = ', '.join(f"{pi.ci_item.model_number}x{pi.quantity}" for pi in case.items[:3])
            if len(case.items) > 3:
                items_desc += f" 외 {len(case.items)-3}건"
            click.echo(f"     Case {case.case_no}: {case.category.value} | "
                       f"수량={case.total_quantity} | "
                       f"N.W={case.net_weight:.1f}kg | "
                       f"G.W={case.gross_weight:.1f}kg | "
                       f"{items_desc}")
            if case.reason:
                click.echo(f"       └ 사유: {case.reason}")

    # 4. 검증
    click.echo(f"\n✅ 검증 중...")
    validation = validate_pl(ci_doc, cases)
    click.echo(validation.summary())

    # 5. PL 엑셀 생성
    if output_path is None:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = str(OUTPUT_DIR / pl_doc.filename)

    click.echo(f"\n📝 PL 엑셀 생성: {output_path}")

    if template and ci_path.suffix.lower() == '.xlsx':
        result_path = generate_pl_from_template(pl_doc, str(ci_path), output_path)
    else:
        result_path = generate_pl_excel(pl_doc, str(ci_path), output_path)

    click.echo(f"   ✓ 생성 완료: {result_path}")


@cli.command()
@click.argument('ci_file', type=click.Path(exists=True))
@click.argument('pl_file', type=click.Path(exists=True))
def validate(ci_file, pl_file):
    """CI와 PL 간 정합성을 검증합니다."""
    click.echo(f"\n🔍 검증 시작")
    click.echo(f"   CI: {Path(ci_file).name}")
    click.echo(f"   PL: {Path(pl_file).name}")

    # CI 파싱
    ci_doc = parse_ci(str(ci_file))
    ci_doc = classify_document(ci_doc)

    # 포장 실행
    cases = select_and_pack(ci_doc)

    # 내부 검증
    result = validate_pl(ci_doc, cases)
    click.echo(f"\n{result.summary()}")

    # 실제 PL과 비교
    click.echo(f"\n📊 실제 PL과 비교:")
    comparison = compare_with_actual_pl(cases, str(pl_file))
    click.echo(comparison.summary())


@cli.command()
@click.argument('pl_files', nargs=-1, type=click.Path(exists=True))
def train(pl_files):
    """PL 파일들에서 중량 데이터를 학습합니다."""
    if not pl_files:
        click.echo("PL 파일을 지정해주세요.")
        return

    click.echo(f"\n🎓 학습 시작 ({len(pl_files)}개 파일)")

    from src.ml.training_pipeline import train_full_pipeline

    results = train_full_pipeline(list(pl_files))

    click.echo(f"\n학습 결과:")
    click.echo(f"  추출된 중량 데이터: {results['extracted_weights']}건")
    click.echo(f"  DB 업데이트: {results['db_updated']}건")
    click.echo(f"  ML 모델 성능:")
    for key, val in results['model_metrics'].items():
        click.echo(f"    {key}: {val}")


@cli.command()
@click.argument('ci_file', type=click.Path(exists=True))
@click.argument('actual_pl_file', type=click.Path(exists=True))
@click.option('-v', '--verbose', is_flag=True, help='상세 출력')
def compare(ci_file, actual_pl_file, verbose):
    """CI에서 생성한 PL과 실제 PL을 비교합니다."""
    click.echo(f"\n📊 비교 분석")

    # CI → PL 생성
    ci_doc = parse_ci(str(ci_file))
    ci_doc = classify_document(ci_doc)
    cases = select_and_pack(ci_doc)

    # 비교
    result = compare_with_actual_pl(cases, str(actual_pl_file))
    click.echo(result.summary())


@cli.command()
@click.argument('corrected_pl', type=click.Path(exists=True))
def feedback(corrected_pl):
    """수정된 PL에서 학습하여 DB를 업데이트합니다."""
    click.echo(f"\n🔄 피드백 학습: {Path(corrected_pl).name}")

    from src.validation.feedback_loop import learn_from_corrected_pl

    result = learn_from_corrected_pl(str(corrected_pl))
    click.echo(f"  새 중량 데이터: {result['new_weights']}건")
    click.echo(f"  DB 업데이트: {result['db_updated']}건")


if __name__ == '__main__':
    cli()
