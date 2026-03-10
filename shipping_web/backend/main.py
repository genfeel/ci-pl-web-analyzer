"""FastAPI 앱 진입점 — 선적서류 웹 서비스"""
import sys
from pathlib import Path

# shipping_doc_automation 모듈 경로 추가
AUTOMATION_ROOT = Path(__file__).parent.parent.parent / "shipping_doc_automation"
sys.path.insert(0, str(AUTOMATION_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
