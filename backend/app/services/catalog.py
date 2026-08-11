"""Đọc danh mục bệnh từ ``shared/data/tomato_diseases.json``.

Cả backend và phần model đều đọc chung file này để tên bệnh, thứ tự lớp và
gợi ý xử lý không bao giờ lệch nhau giữa hai bên.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from app.core.config import settings


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
    """Thông tin một lớp bệnh. Trả về bản ghi rỗng an toàn nếu khoá lạ."""
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
