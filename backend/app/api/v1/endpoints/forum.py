"""Diễn đàn nông dân — trao đổi kinh nghiệm quanh một lần chẩn đoán cụ thể.

Toàn bộ endpoint yêu cầu đăng nhập, giống mọi màn có tab khác của app (xem
CLAUDE.md) — không có chế độ đọc công khai riêng.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.diagnosis import Diagnosis
from app.models.forum import ForumComment, ForumPost, ForumPostType
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


def _to_out(post: ForumPost) -> ForumPostOut:
    out = ForumPostOut.model_validate(post)
    out.user_full_name = post.user.full_name if post.user else ""
    out.disease_name = catalog.get_disease(post.disease_key)["name_vi"]
    out.diagnosis_summary = _diagnosis_summary(post.diagnosis)
    return out


def _to_comment_out(comment: ForumComment) -> ForumCommentOut:
    out = ForumCommentOut.model_validate(comment)
    out.user_full_name = comment.user.full_name if comment.user else ""
    return out


def _get_post(db, post_id: int) -> ForumPost:
    post = db.get(
        ForumPost,
        post_id,
        options=[selectinload(ForumPost.user), selectinload(ForumPost.diagnosis)],
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
    del user  # chỉ dùng để bắt buộc đăng nhập, không lọc theo người viết

    stmt = select(ForumPost).options(
        selectinload(ForumPost.user), selectinload(ForumPost.diagnosis)
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
        items=[_to_out(p) for p in posts],
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
    return _to_out(_get_post(db, post.id))


@router.get("/posts/{post_id}", response_model=ForumPostDetail, summary="Chi tiết bài viết")
def get_post(post_id: int, db: DbSession, user: CurrentUser):
    del user
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

    detail = ForumPostDetail(**_to_out(post).model_dump())
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


@router.post("/posts/{post_id}/like", response_model=ForumPostOut, summary="Thích bài viết")
def like_post(post_id: int, db: DbSession, user: CurrentUser):
    del user
    post = _get_post(db, post_id)
    post.likes_count += 1
    db.commit()
    db.refresh(post)
    return _to_out(_get_post(db, post_id))
