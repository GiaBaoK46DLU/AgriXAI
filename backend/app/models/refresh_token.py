"""Refresh token — cho phép làm mới access token mà không bắt đăng nhập lại.

Lưu dạng băm (``token_hash``), không lưu token thô — mất DB không lộ token
dùng được ngay. Xoay vòng (rotation): mỗi lần `/auth/refresh` gọi thành công,
bản ghi cũ bị thu hồi (`revoked_at`) và một bản ghi mới được tạo, nên một
refresh token chỉ dùng được đúng một lần.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.user import User


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    user: Mapped["User"] = relationship()
