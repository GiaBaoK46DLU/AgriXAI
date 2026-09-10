"""Đăng nhập và thông tin tài khoản."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    Token,
    UserOut,
    UserUpdate,
)

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


@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED,
             summary="Tự đăng ký tài khoản nông dân")
def register(payload: RegisterRequest, db: DbSession):
    """Công khai, không cần đăng nhập trước — luôn tạo với vai trò `farmer`.

    Muốn tạo tài khoản `admin` phải dùng `POST /users` (yêu cầu quyền admin),
    xem `app/api/v1/endpoints/users.py`.
    """
    if db.scalar(select(User.id).where(User.username == payload.username)) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Tên đăng nhập '{payload.username}' đã tồn tại",
        )
    if db.scalar(select(User.id).where(User.email == payload.email)) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Email này đã được đăng ký",
        )

    user = User(
        username=payload.username,
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        role=UserRole.FARMER,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {**_issue(user), "user": user}


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
    # Người dùng thường không được tự nâng quyền, tự mở khoá tài khoản, hay
    # đổi mật khẩu qua đường này — đổi mật khẩu phải qua
    # `POST /auth/change-password` vì cần xác nhận mật khẩu hiện tại.
    for field in ("full_name", "phone"):
        value = getattr(payload, field)
        if value is not None:
            setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.post("/change-password", response_model=UserOut, summary="Đổi mật khẩu")
def change_password(payload: ChangePasswordRequest, user: CurrentUser, db: DbSession):
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Mật khẩu hiện tại không đúng"
        )
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    db.refresh(user)
    return user
