"""Đọc danh mục bệnh từ ``shared/data/tomato_diseases.json``.

Cả backend và phần model đều đọc chung file này để tên bệnh, thứ tự lớp và
gợi ý xử lý không bao giờ lệch nhau giữa hai bên.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.medicine import DiseaseGuide, DiseaseMedicine, Medicine
from app.services.inference.base import NOT_TOMATO_LEAF_KEY

# Câu tiếng Việt hiển thị cho người dùng khi bộ chặn #92 từ chối ảnh — nguồn
# duy nhất cho câu này, dùng cả ở đây (tên hiển thị) lẫn ở
# `diagnosis_service` (thông báo lỗi 422 khi cả lô ảnh đều bị chặn).
NOT_TOMATO_LEAF_MESSAGE = "Ảnh chưa rõ lá cà chua, bạn chụp lại giúp mình nhé"


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, Any]:
    with open(settings.disease_catalog_path, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def diseases_by_key() -> dict[str, dict[str, Any]]:
    return {d["key"]: d for d in load_catalog()["diseases"]}


@lru_cache(maxsize=1)
def class_keys() -> list[str]:
    """Thứ tự lớp — phải khớp với thứ tự output của mô hình."""
    return [d["key"] for d in load_catalog()["diseases"]]


def get_disease(key: str) -> dict[str, Any]:
    """Thông tin một lớp bệnh. Trả về bản ghi rỗng an toàn nếu khoá lạ.

    ``key == NOT_TOMATO_LEAF_KEY`` (#92) là trường hợp đặc biệt phải xử lý
    trước khi rơi vào nhánh "khoá lạ" bên dưới: khoá đó không có trong danh
    mục JSON một cách CÓ CHỦ ĐÍCH (không phải lỗi thiếu dữ liệu), nên phải trả
    về câu tiếng Việt dễ hiểu — không được để lọt chuỗi ``"not_tomato_leaf"``
    ra giao diện (#47 tiêu chí hoàn thành).
    """
    if key == NOT_TOMATO_LEAF_KEY:
        return {
            "key": key,
            "name_vi": NOT_TOMATO_LEAF_MESSAGE,
            "name_en": "Not a tomato leaf",
            "is_healthy": False,
            "visual_cue": "",
            "symptoms": "",
            "treatments": [],
            "prevention": [],
        }

    found = diseases_by_key().get(key)
    if found:
        return found
    return {
        "key": key,
        "name_vi": key,
        "name_en": key,
        "is_healthy": False,
        "visual_cue": "dấu hiệu bất thường",
        "symptoms": "",
        "treatments": [],
        "prevention": [],
    }


@lru_cache(maxsize=1)
def severity_levels() -> list[dict[str, Any]]:
    """Các mức độ nặng, đã sắp xếp theo ngưỡng tăng dần."""
    return sorted(load_catalog()["severity_levels"], key=lambda s: s["max_area_ratio"])


def disclaimer() -> str:
    return load_catalog().get("disclaimer", "")


# ── Thuốc gợi ý + video hướng dẫn (CSDL, không phải JSON — xem CLAUDE.md) ──

def get_medicines(db: Session, disease_key: str) -> list[dict[str, Any]]:
    """Thuốc gợi ý cho một bệnh. Rỗng nếu chưa có thuốc nào được gán."""
    rows = db.execute(
        select(Medicine, DiseaseMedicine.note)
        .join(DiseaseMedicine, DiseaseMedicine.medicine_id == Medicine.id)
        .where(DiseaseMedicine.disease_key == disease_key)
    ).all()
    return [
        {"name": m.name, "group": m.group, "purchase_url": m.purchase_url, "note": note}
        for m, note in rows
    ]


def get_video_url(db: Session, disease_key: str) -> str | None:
    """Link video YouTube hướng dẫn xử lý, hoặc None nếu chưa có."""
    guide = db.get(DiseaseGuide, disease_key)
    return guide.video_url if guide else None


def get_disease_with_extras(db: Session, key: str) -> dict[str, Any]:
    """``get_disease()`` kèm thêm ``products`` và ``video_url`` từ CSDL.

    Dùng ở các endpoint trả về cho người dùng cuối (``DiseaseInfo``). Không
    dùng ở ``xai/explain.py`` vì phần đó chỉ cần is_healthy/name_vi/visual_cue,
    không cần đụng CSDL.
    """
    info = dict(get_disease(key))
    info["products"] = get_medicines(db, key)
    info["video_url"] = get_video_url(db, key)
    return info
