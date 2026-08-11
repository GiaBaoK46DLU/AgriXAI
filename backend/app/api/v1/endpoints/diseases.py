"""Tra cứu danh mục bệnh và gợi ý xử lý.

Không cần đăng nhập: đây là kiến thức tra cứu công khai, và app di động cần
hiển thị được ngay cả khi người dùng chưa đăng nhập.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas.diagnosis import DiseaseInfo
from app.services import catalog

router = APIRouter()


def _to_schema(info: dict) -> DiseaseInfo:
    return DiseaseInfo(**{k: v for k, v in info.items() if k in DiseaseInfo.model_fields})


@router.get("", response_model=list[DiseaseInfo], summary="Toàn bộ danh mục bệnh")
def list_diseases():
    return [_to_schema(d) for d in catalog.load_catalog()["diseases"]]


@router.get("/{disease_key}", response_model=DiseaseInfo,
            summary="Chi tiết một loại bệnh")
def get_disease(disease_key: str):
    """Màn hình *Xem gợi ý xử lý* của app gọi endpoint này."""
    info = catalog.diseases_by_key().get(disease_key)
    if info is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"Không có bệnh nào mang khoá '{disease_key}' trong danh mục",
        )
    return _to_schema(info)
