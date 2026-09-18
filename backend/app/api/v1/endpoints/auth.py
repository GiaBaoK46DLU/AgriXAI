"""Đăng nhập và thông tin tài khoản."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.core.security import (
    create_access_token,
    hash_password,
    hash_refresh_token,
    new_refresh_token_value,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RegisterRequest,
    Token,
    TokenPair,
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


def _issue(user: User, db: Session) -> dict:
    """Phát access token (JWT, không lưu CSDL) kèm refresh token (chuỗi ngẫu
    nhiên, lưu bản băm trong bảng `refresh_tokens` để thu hồi được)."""
    raw_refresh = new_refresh_token_value()
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_refresh_token(raw_refresh),
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    ))
    db.commit()
    return {
        "access_token": create_access_token(user.id, {"role": user.role}),
        "refresh_token": raw_refresh,
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
    return {**_issue(user, db), "user": user}


@router.post("/login", response_model=LoginResponse, summary="Đăng nhập (JSON)")
def login(payload: LoginRequest, db: DbSession):
    """Dùng cho app di động và web admin."""
    user = _authenticate(db, payload.username, payload.password)
    return {**_issue(user, db), "user": user}


@router.post("/token", response_model=Token, summary="Đăng nhập (form, cho Swagger)")
def login_form(
    db: DbSession,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """Endpoint dạng form để nút *Authorize* trong `/docs` hoạt động."""
    user = _authenticate(db, form.username, form.password)
    return _issue(user, db)


@router.post("/refresh", response_model=TokenPair, summary="Làm mới access token")
def refresh(payload: RefreshRequest, db: DbSession):
    """Đổi một refresh token còn hiệu lực lấy access token mới — xoay vòng:
    refresh token cũ bị thu hồi ngay, chỉ dùng được đúng một lần. Mobile gọi
    endpoint này ở nền khi một API khác trả 401 (xem `api_client.dart`)."""
    token_hash = hash_refresh_token(payload.refresh_token)
    now = datetime.now(timezone.utc)
    # So sánh hạn dùng ở phía SQL (không đọc `expires_at` ra rồi so bằng
    # Python) — SQLite trả `DateTime(timezone=True)` dạng naive sau khi đọc,
    # so trực tiếp với `now` (aware) trong Python sẽ ném lỗi. Cùng lý do với
    # cách `stats.py` so `created_at` trong `.where()` thay vì sau khi fetch.
    record = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at >= now,
        )
    )
    invalid = HTTPException(
        status.HTTP_401_UNAUTHORIZED,
        "Refresh token không hợp lệ hoặc đã hết hạn",
    )
    if record is None:
        raise invalid

    user = db.get(User, record.user_id)
    if user is None or not user.is_active:
        raise invalid

    record.revoked_at = now
    db.commit()
    return _issue(user, db)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Thu hồi refresh token",
)
def logout(payload: RefreshRequest, db: DbSession) -> None:
    """Vô hiệu hoá refresh token phía server lúc đăng xuất — xoá token khỏi
    máy (mobile) không đủ, vì token thô vẫn còn dùng được nếu ai đó có nó.
    Không cần đăng nhập lại: biết đúng token thô là đủ bằng chứng, và endpoint
    tự thành công kể cả khi token không tồn tại/đã thu hồi (dọn dẹp idempotent)."""
    token_hash = hash_refresh_token(payload.refresh_token)
    record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if record is not None and record.revoked_at is None:
        record.revoked_at = datetime.now(timezone.utc)
        db.commit()


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
