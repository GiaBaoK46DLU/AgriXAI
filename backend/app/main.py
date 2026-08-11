"""Điểm khởi động ứng dụng FastAPI.

Chạy:
    cd backend
    uvicorn app.main:app --reload
    uvicorn app.main:app --host 0.0.0.0 --port 8000   # để điện thoại trong cùng LAN gọi được

Tài liệu API tự sinh: http://localhost:8000/docs
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.services.inference.loader import get_predictor, is_using_real_model
from app.services.storage.local import ensure_directories

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s  %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Nạp mô hình MỘT LẦN lúc khởi động, không phải mỗi request."""
    ensure_directories()

    predictor = get_predictor()
    if is_using_real_model():
        logger.info("Mô hình thật đã sẵn sàng: %s", predictor.model_version)
    else:
        logger.warning(
            "=" * 70 + "\n"
            "  ĐANG DÙNG MÔ HÌNH GIẢ (DummyPredictor)\n"
            "  Kết quả chẩn đoán KHÔNG có ý nghĩa thực tế.\n"
            "  Trỏ MODEL_CHECKPOINT trong .env tới checkpoint thật để chuyển đổi.\n"
            + "=" * 70
        )

    yield
    logger.info("Đang tắt ứng dụng")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "API chẩn đoán bệnh trên lá cà chua kèm giải thích trực quan (XAI).\n\n"
        "Đồ án tốt nghiệp — Khoa CNTT, Trường Đại học Đà Lạt."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Phục vụ ảnh đã lưu tại /storage/uploads/... và /storage/overlays/...
ensure_directories()
app.mount("/storage", StaticFiles(directory=settings.storage_path), name="storage")


@app.get("/", tags=["Hệ thống"], summary="Thông tin cơ bản")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": app.version,
        "docs": "/docs",
        "api": settings.API_V1_PREFIX,
    }


@app.get("/health", tags=["Hệ thống"], summary="Kiểm tra tình trạng hệ thống")
def health():
    """Frontend gọi endpoint này để biết backend sống chưa và mô hình có thật không."""
    predictor = get_predictor()
    return {
        "status": "ok",
        "using_real_model": is_using_real_model(),
        "model_version": getattr(predictor, "model_version", "unknown"),
    }
