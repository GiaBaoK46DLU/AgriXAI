"""Người dùng hệ thống."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.diagnosis import Diagnosis
    from app.models.plot import Plot


class UserRole:
    """Vai trò. Dùng chuỗi thay vì ENUM của PostgreSQL cho đỡ rắc rối khi
    migrate — thêm vai trò mới chỉ cần sửa hằng số, không phải đổi kiểu cột."""

    ADMIN = "admin"      # quản trị: xem toàn hệ thống, quản lý tài khoản
    FARMER = "farmer"    # nông dân: chỉ thấy lô đất và lịch sử của chính mình

    ALL = (ADMIN, FARMER)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(20), default=None)
    role: Mapped[str] = mapped_column(String(20), default=UserRole.FARMER, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    plots: Mapped[list["Plot"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )
    diagnoses: Mapped[list["Diagnosis"]] = relationship(back_populates="user")

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"
