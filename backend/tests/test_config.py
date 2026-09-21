"""Kiểm thử #39 — bịt điểm mù đã biết của bộ test: app từng KHÔNG khởi động
nổi khi có file `.env` thật, vì pydantic-settings chạy `json.loads()` lên
field kiểu `list` (`CORS_ORIGINS`) trước khi validator `_split_origins` được
gọi. Ai làm đúng theo hướng dẫn `copy .env.example .env` sẽ gặp crash ngay.

Bộ test cũ (17/17 lúc đó) vẫn pass chỉ vì trong repo không có `.env` — không
test nào từng thật sự NẠP một file `.env`. `NoDecode` đã sửa lỗi, nhưng nếu ai
đó "dọn dẹp" xoá `NoDecode` đi (trông như thừa) thì không có gì báo động.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from app.core.config import Settings


@pytest.fixture
def temp_env_file():
    """File `.env` tạm — tự dọn dù test pass hay fail.

    Đóng file descriptor ngay sau khi tạo (không giữ mở qua `yield`): Windows
    không cho xoá file đang có handle mở, nên thiếu bước này thì `unlink` ở
    dưới ném `PermissionError` mỗi lần chạy trên máy Windows.
    """
    fd, path = tempfile.mkstemp(suffix=".env")
    os.close(fd)
    yield Path(path)
    Path(path).unlink(missing_ok=True)


def test_settings_loads_comma_separated_cors_origins_from_env_file(temp_env_file):
    temp_env_file.write_text(
        "CORS_ORIGINS=http://localhost:3000,http://192.168.1.10:3000\n",
        encoding="utf-8",
    )

    settings = Settings(_env_file=temp_env_file)  # type: ignore[call-arg]

    # Phải là list đã TÁCH đúng, không phải chuỗi thô "a,b" hay lỗi json.loads
    assert settings.CORS_ORIGINS == [
        "http://localhost:3000",
        "http://192.168.1.10:3000",
    ]


def test_settings_loads_without_env_file_uses_defaults(temp_env_file):
    # File tồn tại nhưng RỖNG — mô phỏng máy chưa cấu hình gì, không phải máy
    # thiếu hẳn file .env (case đó không tự nhiên xảy ra vì BaseSettings không
    # lỗi khi thiếu file, chỉ dùng default; cái đáng lo là file CÓ MẶT).
    settings = Settings(_env_file=temp_env_file)  # type: ignore[call-arg]

    assert settings.CORS_ORIGINS == []
    assert settings.HEATMAP_THRESHOLD == 0.5


def test_settings_single_cors_origin_still_a_list(temp_env_file):
    """Một địa chỉ duy nhất (không có dấu phẩy) vẫn phải ra `list[str]`, không
    phải bị tách thành list ký tự hay giữ nguyên chuỗi."""
    temp_env_file.write_text("CORS_ORIGINS=http://localhost:3000\n", encoding="utf-8")

    settings = Settings(_env_file=temp_env_file)  # type: ignore[call-arg]

    assert settings.CORS_ORIGINS == ["http://localhost:3000"]
