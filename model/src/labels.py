"""Danh mục lớp bệnh — nguồn sự thật duy nhất cho cả model lẫn backend.

Mọi thứ đọc từ ``shared/data/tomato_diseases.json`` để tên lớp, thứ tự lớp và
tên tiếng Việt không bao giờ lệch nhau giữa hai phần của hệ thống.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

CATALOG_PATH = Path(__file__).resolve().parents[2] / "shared" / "data" / "tomato_diseases.json"


@lru_cache(maxsize=1)
def load_catalog(path: str | Path | None = None) -> dict[str, Any]:
    """Đọc file danh mục bệnh."""
    p = Path(path) if path else CATALOG_PATH
    with open(p, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def class_keys() -> list[str]:
    """Danh sách khoá lớp theo đúng thứ tự trong file danh mục.

    Thứ tự này chính là thứ tự output của mô hình — không được thay đổi sau
    khi đã huấn luyện, nếu không nhãn trả về sẽ sai hết.
    """
    return [d["key"] for d in load_catalog()["diseases"]]


@lru_cache(maxsize=1)
def dir_to_key() -> dict[str, str]:
    """Ánh xạ tên thư mục PlantVillage -> khoá lớp nội bộ."""
    return {d["plantvillage_dir"]: d["key"] for d in load_catalog()["diseases"]}


@lru_cache(maxsize=1)
def key_to_name_vi() -> dict[str, str]:
    return {d["key"]: d["name_vi"] for d in load_catalog()["diseases"]}


def disease_info(key: str) -> dict[str, Any]:
    """Toàn bộ thông tin của một lớp bệnh (triệu chứng, gợi ý xử lý...)."""
    for d in load_catalog()["diseases"]:
        if d["key"] == key:
            return d
    raise KeyError(f"Không có lớp bệnh nào tên '{key}' trong danh mục")


def num_classes() -> int:
    return len(class_keys())
