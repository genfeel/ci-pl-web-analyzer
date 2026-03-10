"""API 엔드포인트"""
import shutil
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

from api.schemas import (
    UploadResponse,
    ContainerLoadRequest,
    ContainerLoadResponse,
)
from services.packing_service import (
    process_ci_file,
    get_cached_result,
    generate_pl_file,
    get_cases_for_loading,
    UPLOADS_DIR,
)
from services.container_loading_service import simulate_container_loading

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_ci(file: UploadFile = File(...)):
    """CI Excel 파일 업로드 → 파이프라인 실행 → JSON 결과 반환"""
    if not file.filename:
        raise HTTPException(400, "파일명이 없습니다.")

    ext = Path(file.filename).suffix.lower()
    if ext not in (".xls", ".xlsx"):
        raise HTTPException(400, "xls 또는 xlsx 파일만 업로드 가능합니다.")

    # 파일 저장
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    save_path = UPLOADS_DIR / file.filename
    with open(save_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        result = process_ci_file(str(save_path), file.filename)
        return result
    except Exception as e:
        raise HTTPException(500, f"파이프라인 실행 오류: {str(e)}")


@router.get("/result/{result_id}", response_model=UploadResponse)
async def get_result(result_id: str):
    """캐시된 결과 조회"""
    result = get_cached_result(result_id)
    if not result:
        raise HTTPException(404, "결과를 찾을 수 없습니다.")
    return result


@router.get("/download-pl/{result_id}")
async def download_pl(result_id: str):
    """PL Excel 파일 다운로드"""
    output_path = generate_pl_file(result_id)
    if not output_path or not Path(output_path).exists():
        raise HTTPException(404, "PL 파일을 생성할 수 없습니다.")

    return FileResponse(
        path=output_path,
        filename=Path(output_path).name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.post("/container-load/{result_id}", response_model=ContainerLoadResponse)
async def container_load(result_id: str, req: ContainerLoadRequest):
    """컨테이너 적재 시뮬레이션 실행"""
    cases = get_cases_for_loading(result_id)
    if cases is None:
        raise HTTPException(404, "결과를 찾을 수 없습니다.")

    try:
        result = simulate_container_loading(cases, req.container_type)
        return result
    except ValueError as e:
        raise HTTPException(400, str(e))
