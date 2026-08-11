"""Gom toàn bộ endpoint của API v1."""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, diagnoses, diseases, plots, stats, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Xác thực"])
api_router.include_router(plots.router, prefix="/plots", tags=["Lô đất"])
api_router.include_router(diagnoses.router, prefix="/diagnoses", tags=["Chẩn đoán"])
api_router.include_router(diseases.router, prefix="/diseases", tags=["Danh mục bệnh"])
api_router.include_router(stats.router, prefix="/stats", tags=["Thống kê"])
api_router.include_router(users.router, prefix="/users", tags=["Tài khoản"])
