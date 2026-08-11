"""Quản lý tài khoản và phân quyền — chỉ dành cho quản trị.

Tương ứng trang *Tài khoản & phân quyền* trong wireframe web admin.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import AdminUser, DbSession
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.schemas.auth import UserCreate, UserOut, UserUpdate

router = APIRouter()


@router.get("", response_model=list[UserOut], summary="Danh sách tài khoản")
def list_users(
    db: DbSession,
    _: AdminUser,
    q: str | None = Query(default=None, description="Tìm theo tên đăng nhập hoặc họ tên"),
    role: str | None = None,
    is_active: bool | None = None,
    limit: int = Query(default=100, le=500),
    offset: int = 0,
):
    stmt = select(User)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(User.username.ilike(pattern) | User.full_name.ilike(pattern))
    if role:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)

    return db.scalars(
        stmt.order_by(User.created_at.desc()).limit(limit).offset(offset)
    ).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED,
             summary="Tạo tài khoản mới")
def create_user(payload: UserCreate, db: DbSession, _: AdminUser):
    if payload.role not in UserRole.ALL:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Vai trò phải là một trong: {', '.join(UserRole.ALL)}",
        )
    if db.scalar(select(User.id).where(User.username == payload.username)) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Tên đăng nhập '{payload.username}' đã tồn tại",
        )

    user = User(
        username=payload.username,
        full_name=payload.full_name,
        phone=payload.phone,
        role=payload.role,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserOut, summary="Chi tiết tài khoản")
def get_user(user_id: int, db: DbSession, _: AdminUser):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài khoản")
    return user


@router.patch("/{user_id}", response_model=UserOut,
              summary="Cập nhật / khoá tài khoản")
def update_user(user_id: int, payload: UserUpdate, db: DbSession, admin: AdminUser):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy tài khoản")

    # Chặn quản trị tự khoá hoặc tự hạ quyền chính mình rồi mất đường vào hệ thống
    if user.id == admin.id:
        if payload.is_active is False:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không thể tự khoá tài khoản của mình")
        if payload.role and payload.role != UserRole.ADMIN:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Không thể tự hạ quyền của mình")

    if payload.role is not None:
        if payload.role not in UserRole.ALL:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"Vai trò phải là một trong: {', '.join(UserRole.ALL)}",
            )
        user.role = payload.role

    for field in ("full_name", "phone", "is_active"):
        value = getattr(payload, field)
        if value is not None:
            setattr(user, field, value)

    if payload.password:
        user.hashed_password = hash_password(payload.password)

    db.commit()
    db.refresh(user)
    return user
