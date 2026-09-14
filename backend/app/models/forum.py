"""Diễn đàn nông dân — trao đổi kinh nghiệm quanh một lần chẩn đoán cụ thể.

``disease_key`` là chuỗi thường, KHÔNG phải khoá ngoại — cùng lý do đã ghi
trong ``models/medicine.py``: ``Disease`` chỉ tồn tại trong
``shared/data/tomato_diseases.json``, không có bảng ``diseases`` trong CSDL
để tham chiếu tới.

``diagnosis_id`` NULLABLE vì bài viết không bắt buộc phải đính kèm một lần
chẩn đoán cụ thể — người dùng có thể chỉ muốn hỏi/chia sẻ kinh nghiệm chung
về một loại bệnh. ``ondelete="SET NULL"`` vì xoá bản chẩn đoán không có
nghĩa là bài viết bàn về nó cũng mất giá trị (giống lý do ``Diagnosis.plot_id``
dùng SET NULL khi xoá lô đất — xem ``plots.py``).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

if TYPE_CHECKING:
    from app.models.diagnosis import Diagnosis
    from app.models.user import User


class ForumPostType:
    """Loại phản hồi của một bài viết."""

    AGREE = "agree"                    # đồng ý với kết quả
    DISAGREE = "disagree"              # nghĩ là bệnh khác
    MEDICINE_ISSUE = "medicine_issue"  # thuốc gợi ý không phù hợp
    TIP = "tip"                        # kinh nghiệm xử lý khác

    ALL = (AGREE, DISAGREE, MEDICINE_ISSUE, TIP)


class ForumPost(Base):
    __tablename__ = "forum_posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    disease_key: Mapped[str] = mapped_column(String(50), index=True)
    diagnosis_id: Mapped[int | None] = mapped_column(
        ForeignKey("diagnoses.id", ondelete="SET NULL"), default=None, index=True
    )
    type: Mapped[str] = mapped_column(String(20), index=True)
    content: Mapped[str] = mapped_column(Text)
    likes_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    user: Mapped["User"] = relationship()
    diagnosis: Mapped["Diagnosis | None"] = relationship()
    comments: Mapped[list["ForumComment"]] = relationship(
        back_populates="post", cascade="all, delete-orphan", order_by="ForumComment.id"
    )

    def __repr__(self) -> str:
        return f"<ForumPost #{self.id} {self.disease_key} {self.type}>"


class ForumComment(Base):
    __tablename__ = "forum_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(
        ForeignKey("forum_posts.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    post: Mapped["ForumPost"] = relationship(back_populates="comments")
    user: Mapped["User"] = relationship()
