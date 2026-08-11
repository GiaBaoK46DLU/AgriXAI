"""Một lần chẩn đoán bệnh — bản ghi trung tâm của hệ thống."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.plot import Plot
    from app.models.user import User


class Diagnosis(Base):
    """Kết quả một lần chẩn đoán, kèm ảnh gốc và ảnh đã khoanh vùng XAI.

    Lưu ``model_version`` cho mỗi bản ghi để sau này truy vết được kết quả nào
    do mô hình nào sinh ra — cần thiết khi so sánh chất lượng giữa các lần
    huấn luyện, và khi giải thích với người dùng vì sao cùng một ảnh mà kết quả
    hôm nay khác hôm qua.
    """

    __tablename__ = "diagnoses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    plot_id: Mapped[int | None] = mapped_column(
        ForeignKey("plots.id", ondelete="SET NULL"), default=None, index=True
    )

    # ── Ảnh ──
    image_path: Mapped[str] = mapped_column(String(255))        # ảnh gốc
    overlay_path: Mapped[str | None] = mapped_column(String(255), default=None)  # ảnh khoanh vùng

    # ── Kết quả mô hình ──
    disease_key: Mapped[str] = mapped_column(String(50), index=True)
    disease_name: Mapped[str] = mapped_column(String(120))
    confidence: Mapped[float] = mapped_column(Float)
    # Xác suất toàn bộ các lớp — giữ lại để phân tích lỗi và hiển thị top-3
    probabilities: Mapped[dict | None] = mapped_column(JSON, default=None)

    # ── Phần XAI ──
    severity: Mapped[str] = mapped_column(String(20), default="none", index=True)
    severity_name: Mapped[str] = mapped_column(String(50), default="Không có dấu hiệu")
    affected_ratio: Mapped[float] = mapped_column(Float, default=0.0)  # tỉ lệ diện tích nghi ngờ
    explanation: Mapped[str | None] = mapped_column(Text, default=None)

    # ── Siêu dữ liệu ──
    model_version: Mapped[str] = mapped_column(String(80), default="unknown")
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    note: Mapped[str | None] = mapped_column(String(500), default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    user: Mapped["User"] = relationship(back_populates="diagnoses")
    plot: Mapped["Plot | None"] = relationship(back_populates="diagnoses")

    def __repr__(self) -> str:
        return f"<Diagnosis #{self.id} {self.disease_key} {self.confidence:.2f}>"
