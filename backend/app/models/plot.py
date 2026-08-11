"""Lô đất canh tác."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.diagnosis import Diagnosis
    from app.models.user import User


class PlotStatus:
    ACTIVE = "active"          # đang canh tác
    FALLOW = "fallow"          # đang nghỉ
    ARCHIVED = "archived"      # ngừng theo dõi

    ALL = (ACTIVE, FALLOW, ARCHIVED)


class Plot(Base):
    """Một lô đất của nông dân.

    Trường ``puc`` (mã vùng trồng) là mã định danh chính thức của lô đất. Giai
    đoạn hiện tại hệ thống chạy độc lập nên PUC chỉ là một mã nội bộ; nếu sau
    này ghép với nhóm nhật ký canh tác và nhóm bản đồ GIS thì đây là khoá dùng
    để đối chiếu dữ liệu giữa ba hệ thống.
    """

    __tablename__ = "plots"

    id: Mapped[int] = mapped_column(primary_key=True)
    puc: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    region: Mapped[str | None] = mapped_column(String(120), default=None, index=True)
    area_m2: Mapped[float | None] = mapped_column(Float, default=None)
    crop: Mapped[str] = mapped_column(String(50), default="tomato")
    status: Mapped[str] = mapped_column(String(20), default=PlotStatus.ACTIVE, index=True)
    note: Mapped[str | None] = mapped_column(String(500), default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    owner: Mapped["User"] = relationship(back_populates="plots")
    diagnoses: Mapped[list["Diagnosis"]] = relationship(back_populates="plot")

    def __repr__(self) -> str:
        return f"<Plot {self.puc} — {self.name}>"
