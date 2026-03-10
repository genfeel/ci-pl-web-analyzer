"""FastAPI 앱 진입점 — 선적서류 웹 서비스"""
import sys
from pathlib import Path

# shipping_doc_automation 모듈 경로 추가
AUTOMATION_ROOT = Path(__file__).parent.parent.parent / "shipping_doc_automation"
sys.path.insert(0, str(AUTOMATION_ROOT))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from api.routes import router

app = FastAPI(title="선적서류 웹 서비스", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}


# 프로덕션: 프론트엔드 빌드 결과물(dist/) 서빙
DIST_DIR = Path(__file__).parent.parent / "frontend" / "dist"
if DIST_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """SPA fallback — 모든 비-API 경로를 index.html로 라우팅"""
        file_path = DIST_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(DIST_DIR / "index.html"))
