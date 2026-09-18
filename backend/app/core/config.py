"""Cấu hình ứng dụng — đọc từ biến môi trường / file .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# backend/app/core/config.py -> backend/
BACKEND_DIR = Path(__file__).resolve().parents[2]
# -> gốc dự án
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    PROJECT_NAME: str = "Chẩn đoán bệnh cây trồng"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+psycopg2://plantdx:plantdx@localhost:5432/plantdx"

    SECRET_KEY: str = "doi-khoa-nay-truoc-khi-trien-khai-that"
    ALGORITHM: str = "HS256"
    # Ngắn hạn có chủ đích (trước đây 7 ngày, không có refresh token nào cả)
    # — từ khi có `/auth/refresh` (07/09/2026... cập nhật 18/09/2026), access
    # token chỉ cần sống đủ ngắn để giảm thiệt hại nếu bị lộ; phiên đăng nhập
    # thật sự kéo dài nhờ REFRESH_TOKEN_EXPIRE_DAYS bên dưới, mobile tự làm
    # mới token nền khi gặp 401 (xem `mobile/lib/services/api_client.dart`).
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Để trống -> dùng DummyPredictor
    MODEL_CHECKPOINT: str = ""
    MODEL_PACKAGE_DIR: str = "../model"
    MODEL_DEVICE: str = ""

    # Bộ chặn 2 lớp lá/không phải lá (#92). Để trống -> không bật, hành vi
    # giống hệt trước khi có #47: mọi ảnh đều đi thẳng vào mô hình bệnh.
    MODEL_GATE_CHECKPOINT: str = ""

    STORAGE_DIR: str = "storage"
    MAX_UPLOAD_MB: int = 10
    MAX_IMAGE_DIMENSION: int = 1280

    HEATMAP_THRESHOLD: float = 0.5

    # Để trống -> endpoint /weather trả lỗi rõ ràng thay vì gọi OpenWeather
    # bằng key rỗng. Toạ độ cố định Đà Lạt vì mọi lô đất trong phạm vi đề tài
    # đều ở khu vực này (xem CLAUDE.md) — không cần lấy theo từng lô đất.
    OPENWEATHER_API_KEY: str = ""
    WEATHER_LOCATION_NAME: str = "Đà Lạt"
    WEATHER_LAT: float = 11.9404
    WEATHER_LON: float = 108.4583

    # NoDecode là bắt buộc, không phải trang trí: với field kiểu list,
    # pydantic-settings mặc định chạy json.loads() trên giá trị đọc từ .env
    # TRƯỚC khi validator dưới đây được gọi, nên chuỗi ngăn cách bằng dấu phẩy
    # sẽ làm hỏng ngay lúc khởi động. NoDecode tắt bước đó đi.
    #
    # Mặc định rỗng từ 16/09/2026: web-admin (Next.js) gọi backend qua kiến
    # trúc BFF (phía server của Next.js, không phải trình duyệt) nên không
    # cần khai origin nào ở đây nữa — xem web-admin/README.md.
    CORS_ORIGINS: Annotated[list[str], NoDecode] = []

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _split_origins(cls, v):
        """Cho phép khai báo dạng chuỗi ngăn cách bằng dấu phẩy trong .env."""
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    # ── Đường dẫn tuyệt đối, suy ra từ cấu hình trên ──

    @property
    def storage_path(self) -> Path:
        p = Path(self.STORAGE_DIR)
        return p if p.is_absolute() else (BACKEND_DIR / p).resolve()

    @property
    def uploads_path(self) -> Path:
        return self.storage_path / "uploads"

    @property
    def overlays_path(self) -> Path:
        return self.storage_path / "overlays"

    @property
    def model_package_path(self) -> Path:
        p = Path(self.MODEL_PACKAGE_DIR)
        return p if p.is_absolute() else (BACKEND_DIR / p).resolve()

    @property
    def checkpoint_path(self) -> Path | None:
        if not self.MODEL_CHECKPOINT.strip():
            return None
        p = Path(self.MODEL_CHECKPOINT)
        return p if p.is_absolute() else (BACKEND_DIR / p).resolve()

    @property
    def gate_checkpoint_path(self) -> Path | None:
        if not self.MODEL_GATE_CHECKPOINT.strip():
            return None
        p = Path(self.MODEL_GATE_CHECKPOINT)
        return p if p.is_absolute() else (BACKEND_DIR / p).resolve()

    @property
    def disease_catalog_path(self) -> Path:
        return PROJECT_ROOT / "shared" / "data" / "tomato_diseases.json"

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
