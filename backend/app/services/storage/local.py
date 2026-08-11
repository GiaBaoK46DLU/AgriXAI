"""Lưu ảnh xuống ổ đĩa.

Giai đoạn demo dùng thẳng hệ thống file cho đơn giản. Nếu sau này triển khai
thật thì thay phần thân các hàm ở đây bằng lời gọi S3/MinIO — chỗ gọi bên
ngoài không phải sửa, vì tất cả đều đi qua ba hàm dưới đây.

Ảnh được xếp theo thư mục ``YYYY/MM`` để một thư mục không phình lên hàng chục
nghìn file sau vài tháng chạy.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps

from app.core.config import settings

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "BMP"}


class InvalidImageError(ValueError):
    """Ảnh tải lên không hợp lệ hoặc không đọc được."""


def open_and_normalize(data: bytes) -> Image.Image:
    """Mở ảnh từ bytes, xoay đúng chiều và thu nhỏ nếu quá lớn.

    Ảnh chụp từ điện thoại hay bị xoay ngang do thẻ EXIF Orientation —
    ``exif_transpose`` đưa về đúng chiều người chụp nhìn thấy. Không xử lý bước
    này thì mô hình nhận ảnh nằm ngang và kết quả sẽ kém đi rõ rệt.
    """
    from io import BytesIO

    try:
        image = Image.open(BytesIO(data))
        image.verify()               # kiểm tra file có hỏng không
        image = Image.open(BytesIO(data))   # verify() làm đóng file, phải mở lại
    except Exception as exc:  # noqa: BLE001
        raise InvalidImageError("Không đọc được ảnh — file hỏng hoặc sai định dạng") from exc

    if image.format and image.format.upper() not in ALLOWED_FORMATS:
        raise InvalidImageError(
            f"Định dạng '{image.format}' không được hỗ trợ. "
            f"Chấp nhận: {', '.join(sorted(ALLOWED_FORMATS))}"
        )

    image = ImageOps.exif_transpose(image).convert("RGB")

    limit = settings.MAX_IMAGE_DIMENSION
    if max(image.size) > limit:
        image.thumbnail((limit, limit), Image.LANCZOS)

    return image


def save_upload(image: Image.Image) -> str:
    """Lưu ảnh gốc. Trả về đường dẫn tương đối để ghi vào CSDL."""
    return _save(image, settings.uploads_path, "uploads")


def save_overlay(image: Image.Image) -> str:
    """Lưu ảnh đã khoanh vùng XAI."""
    return _save(image, settings.overlays_path, "overlays")


def _save(image: Image.Image, base_dir: Path, prefix: str) -> str:
    now = datetime.now()
    sub = f"{now:%Y/%m}"
    target_dir = base_dir / sub
    target_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{now:%d%H%M%S}-{uuid.uuid4().hex[:8]}.jpg"
    image.save(target_dir / filename, format="JPEG", quality=88, optimize=True)

    # Đường dẫn tương đối, dùng luôn làm URL: /storage/uploads/2026/09/...
    return f"{prefix}/{sub}/{filename}"


def absolute_path(relative: str) -> Path:
    return settings.storage_path / relative


def delete(relative: str) -> bool:
    """Xoá một file đã lưu. Trả về True nếu thực sự xoá được."""
    path = absolute_path(relative)
    try:
        path.unlink()
        return True
    except (FileNotFoundError, OSError):
        return False


def ensure_directories() -> None:
    """Tạo sẵn thư mục lưu trữ lúc khởi động."""
    settings.uploads_path.mkdir(parents=True, exist_ok=True)
    settings.overlays_path.mkdir(parents=True, exist_ok=True)
