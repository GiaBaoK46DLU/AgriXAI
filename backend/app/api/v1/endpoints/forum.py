"""Diễn đàn nông dân — trao đổi kinh nghiệm quanh một lần chẩn đoán cụ thể.

Toàn bộ endpoint yêu cầu đăng nhập, giống mọi màn có tab khác của app (xem
CLAUDE.md) — không có chế độ đọc công khai riêng.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.models.diagnosis import Diagnosis
from app.models.forum import ForumComment, ForumPost, ForumPostLike, ForumPostType
from app.schemas.forum import (
    ForumCommentCreate,
    ForumCommentOut,
    ForumPostCreate,
    ForumPostDetail,
    ForumPostOut,
    ForumPostPage,
)
from app.services import catalog

router = APIRouter()


def _diagnosis_summary(diagnosis: Diagnosis | None) -> str | None:
    if diagnosis is None:
        return None
    return f"{diagnosis.disease_name} · {diagnosis.created_at:%d/%m/%Y %H:%M}"


def _to_out(post: ForumPost, current_user_id: int | None = None, db=None) -> ForumPostOut:
    out = ForumPostOut.model_validate(post)
    out.user_full_name = post.user.full_name if post.user else ""
    out.user_role = post.user.role if post.user else ""
    out.disease_name = catalog.get_disease(post.disease_key)["name_vi"]
    out.diagnosis_summary = _diagnosis_summary(post.diagnosis)
    # Dùng relationship đã load sẵn nếu có; không thì query COUNT riêng.
    if "comments" in post.__dict__:
        out.comments_count = len(post.__dict__["comments"])
    elif db is not None:
        out.comments_count = db.scalar(
            select(func.count(ForumComment.id)).where(ForumComment.post_id == post.id)
        ) or 0
    if current_user_id is not None and db is not None:
        like = db.scalar(
            select(ForumPostLike).where(
                ForumPostLike.post_id == post.id,
                ForumPostLike.user_id == current_user_id,
            )
        )
        out.is_liked_by_me = like is not None
    return out


def _to_comment_out(comment: ForumComment) -> ForumCommentOut:
    out = ForumCommentOut.model_validate(comment)
    out.user_full_name = comment.user.full_name if comment.user else ""
    out.user_role = comment.user.role if comment.user else ""
    return out


def _get_post(db, post_id: int) -> ForumPost:
    post = db.get(
        ForumPost,
        post_id,
        options=[
            selectinload(ForumPost.user),
            selectinload(ForumPost.diagnosis),
            selectinload(ForumPost.comments),
        ],
    )
    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy bài viết")
    return post


@router.get("/posts", response_model=ForumPostPage, summary="Danh sách bài viết")
def list_posts(
    db: DbSession,
    user: CurrentUser,
    disease_key: str | None = None,
    type: str | None = Query(default=None, pattern="^(agree|disagree|medicine_issue|tip)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    stmt = select(ForumPost).options(
        selectinload(ForumPost.user),
        selectinload(ForumPost.diagnosis),
        selectinload(ForumPost.comments),  # để đếm comments_count không cần thêm query
    )
    count_stmt = select(func.count(ForumPost.id))

    filters = []
    if disease_key:
        filters.append(ForumPost.disease_key == disease_key)
    if type:
        filters.append(ForumPost.type == type)

    if filters:
        stmt = stmt.where(*filters)
        count_stmt = count_stmt.where(*filters)

    total = db.scalar(count_stmt) or 0
    posts = db.scalars(
        stmt.order_by(ForumPost.created_at.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    ).all()

    return ForumPostPage(
        items=[_to_out(p, current_user_id=user.id, db=db) for p in posts],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/posts", response_model=ForumPostOut, status_code=status.HTTP_201_CREATED,
             summary="Tạo bài viết")
def create_post(payload: ForumPostCreate, db: DbSession, user: CurrentUser):
    diagnosis: Diagnosis | None = None
    if payload.diagnosis_id is not None:
        diagnosis = db.get(Diagnosis, payload.diagnosis_id)
        if diagnosis is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy bản chẩn đoán")
        if diagnosis.user_id != user.id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Chỉ đính kèm được lần chẩn đoán của chính bạn",
            )

    disease_key = payload.disease_key or (diagnosis.disease_key if diagnosis else None)
    if not disease_key:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Cần chọn bệnh liên quan hoặc đính kèm một lần chẩn đoán",
        )

    post = ForumPost(
        user_id=user.id,
        disease_key=disease_key,
        diagnosis_id=payload.diagnosis_id,
        type=payload.type,
        content=payload.content,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return _to_out(_get_post(db, post.id), current_user_id=user.id, db=db)


@router.get("/posts/{post_id}", response_model=ForumPostDetail, summary="Chi tiết bài viết")
def get_post(post_id: int, db: DbSession, user: CurrentUser):
    post = db.get(
        ForumPost,
        post_id,
        options=[
            selectinload(ForumPost.user),
            selectinload(ForumPost.diagnosis),
            selectinload(ForumPost.comments).selectinload(ForumComment.user),
        ],
    )
    if post is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy bài viết")

    detail = ForumPostDetail(**_to_out(post, current_user_id=user.id, db=db).model_dump())
    detail.comments = [_to_comment_out(c) for c in post.comments]
    return detail


@router.post("/posts/{post_id}/comments", response_model=ForumCommentOut,
             status_code=status.HTTP_201_CREATED, summary="Thêm bình luận")
def create_comment(post_id: int, payload: ForumCommentCreate, db: DbSession, user: CurrentUser):
    _get_post(db, post_id)  # 404 nếu bài viết không tồn tại

    comment = ForumComment(post_id=post_id, user_id=user.id, content=payload.content)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    comment.user = user
    return _to_comment_out(comment)


@router.post("/posts/{post_id}/like", response_model=ForumPostOut, summary="Thích / bỏ thích bài viết")
def like_post(post_id: int, db: DbSession, user: CurrentUser):
    """Toggle like: lần đầu nhấn → like (+1); nhấn lần nữa → unlike (-1).

    Dùng bảng ``forum_post_likes`` để đảm bảo mỗi user chỉ đếm một lần.
    """
    post = _get_post(db, post_id)

    existing = db.scalar(
        select(ForumPostLike).where(
            ForumPostLike.post_id == post_id,
            ForumPostLike.user_id == user.id,
        )
    )

    if existing is None:
        # Chưa like → thêm bản ghi + tăng đếm
        db.add(ForumPostLike(post_id=post_id, user_id=user.id))
        post.likes_count = max(0, post.likes_count + 1)
    else:
        # Đã like → xoá bản ghi + giảm đếm
        db.delete(existing)
        post.likes_count = max(0, post.likes_count - 1)

    db.commit()
    db.refresh(post)
    return _to_out(_get_post(db, post_id), current_user_id=user.id, db=db)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Kiểm duyệt: xoá bài viết")
def delete_post(post_id: int, db: DbSession, _: AdminUser):
    """Chỉ quản trị mới xoá được — chưa có nút xoá cho tác giả tự gỡ bài của
    mình (ngoài phạm vi hiện tại, xem `prompt-cli-forum-feature.md` mục 3).

    Xoá theo tầng (``cascade="all, delete-orphan"`` trên ``ForumPost.comments``)
    nên bình luận của bài cũng mất theo, không cần xoá tay riêng.
    """
    post = _get_post(db, post_id)
    db.delete(post)
    db.commit()


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Kiểm duyệt: xoá một bình luận")
def delete_comment(comment_id: int, db: DbSession, _: AdminUser):
    comment = db.get(ForumComment, comment_id)
    if comment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy bình luận")
    db.delete(comment)
    db.commit()
