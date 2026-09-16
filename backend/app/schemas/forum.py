"""Schema cho diễn đàn nông dân."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.forum import ForumPostType


class ForumPostCreate(BaseModel):
    # Tuỳ chọn: nếu bỏ trống nhưng có gửi `diagnosis_id`, backend tự lấy
    # `disease_key` từ bản chẩn đoán đó (xem endpoint `create_post`).
    disease_key: str | None = Field(default=None, max_length=50)
    diagnosis_id: int | None = None
    type: str = Field(pattern="^(agree|disagree|medicine_issue|tip)$")
    content: str = Field(min_length=1, max_length=5000)


class ForumCommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class ForumCommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    user_id: int
    content: str
    created_at: datetime
    user_full_name: str = ""
    # Để mobile/web tô nổi bật tên quản trị khi họ tham gia bình luận — không
    # phải khoá ngoại gì thêm, chỉ đọc từ `user.role` đã join sẵn.
    user_role: str = ""


class ForumPostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    disease_key: str
    diagnosis_id: int | None
    type: str
    content: str
    likes_count: int
    created_at: datetime

    user_full_name: str = ""
    user_role: str = ""
    # Ghép sẵn tên bệnh + thời gian của lần chẩn đoán đính kèm (nếu có), để
    # mobile không phải gọi thêm API — xem `forum.py._diagnosis_summary`.
    diagnosis_summary: str | None = None
    disease_name: str = ""
    # True nếu user hiện tại đã thích bài này — tính ngoài ORM bởi endpoint,
    # mặc định False để tương thích ngược khi không truyền vào.
    is_liked_by_me: bool = False
    # Số bình luận — tính sẵn ở server để list không cần load toàn bộ objects.
    comments_count: int = 0


class ForumPostDetail(ForumPostOut):
    comments: list[ForumCommentOut] = Field(default_factory=list)


class ForumPostPage(BaseModel):
    items: list[ForumPostOut]
    total: int
    page: int
    page_size: int


__all__ = [
    "ForumCommentCreate",
    "ForumCommentOut",
    "ForumPostCreate",
    "ForumPostDetail",
    "ForumPostOut",
    "ForumPostPage",
    "ForumPostType",
]
