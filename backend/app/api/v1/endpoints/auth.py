"""Đăng nhập và thông tin tài khoản."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, Token, UserOut, UserUpdate

router = APIRouter()


def _authenticate(db, username: str, password: str) -> User:
    user = db.scalar(select(User).where(User.username == username))
    # Kiểm tra cả hai điều kiện rồi mới báo lỗi chung, để không tiết lộ
    # tài khoản nào tồn tại
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai tên đăng nhập hoặc mật khẩu",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản đã bị khoá",
        )
    return user


def _issue(user: User) -> dict:
    return {
        "access_token": create_access_token(user.id, {"role": user.role}),
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


@router.post("/login", response_model=LoginResponse, summary="Đăng nhập (JSON)")
def login(payload: LoginRequest, db: DbSession):
    """Dùng cho app di động và web admin."""
    user = _authenticate(db, payload.username, payload.password)
    return {**_issue(user), "user": user}


@router.post("/token", response_model=Token, summary="Đăng nhập (form, cho Swagger)")
def login_form(
    db: DbSession,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """Endpoint dạng form để nút *Authorize* trong `/docs` hoạt động."""
    user = _authenticate(db, form.username, form.password)
    return _issue(user)


@router.get("/me", response_model=UserOut, summary="Thông tin tài khoản đang đăng nhập")
def me(user: CurrentUser):
    return user


@router.patch("/me", response_model=UserOut, summary="Cập nhật thông tin cá nhân")
def update_me(payload: UserUpdate, user: CurrentUser, db: DbSession):
    # Người dùng thường không được tự nâng quyền hay tự mở khoá tài khoản
    for field in ("full_name", "phone"):
        value = getattr(payload, field)
        if value is not None:
            setattr(user, field, value)

    if payload.password:
        user.hashed_password = hash_password(payload.password)

    db.commit()
    db.refresh(user)
    return user
