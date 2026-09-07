"""Thuốc gợi ý theo bệnh, và video hướng dẫn xử lý — bổ sung 07/09/2026 (IN-02).

Cố tình KHÔNG đụng ``shared/data/tomato_diseases.json``: bệnh vẫn chỉ có trong
JSON (khoá + thứ tự gắn với output mô hình), còn thuốc/video là dữ liệu web
admin cần sửa được qua CRUD sau này nên phải nằm trong CSDL. Xem CLAUDE.md mục
"Tích hợp mô hình thật" để biết vì sao lệch hướng so với issue #84.

``disease_key`` ở đây là chuỗi thường, KHÔNG phải khoá ngoại — không có bảng
``diseases`` trong CSDL để tham chiếu tới, cố tình để vậy.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Medicine(Base):
    """Một loại thuốc/hoạt chất có thể gợi ý cho nhiều bệnh khác nhau."""

    __tablename__ = "medicines"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150))
    group: Mapped[str | None] = mapped_column(String(80), default=None)
    purchase_url: Mapped[str | None] = mapped_column(String(500), default=None)

    def __repr__(self) -> str:
        return f"<Medicine {self.name}>"


class DiseaseMedicine(Base):
    """Gắn một thuốc vào một bệnh, kèm ghi chú riêng cho cặp đó.

    ``note`` dùng cho các ca như virus xoăn vàng lá: thuốc trị bọ phấn trắng
    (môi giới truyền bệnh) chứ không trị trực tiếp virus — người dùng cần biết
    điều đó để khỏi hiểu lầm là "thuốc chữa virus".
    """

    __tablename__ = "disease_medicines"

    id: Mapped[int] = mapped_column(primary_key=True)
    disease_key: Mapped[str] = mapped_column(String(50), index=True)
    medicine_id: Mapped[int] = mapped_column(ForeignKey("medicines.id", ondelete="CASCADE"))
    note: Mapped[str | None] = mapped_column(String(500), default=None)


class DiseaseGuide(Base):
    """Video hướng dẫn xử lý cho một bệnh — tối đa một video mỗi bệnh."""

    __tablename__ = "disease_guides"

    disease_key: Mapped[str] = mapped_column(String(50), primary_key=True)
    video_url: Mapped[str] = mapped_column(String(500))
