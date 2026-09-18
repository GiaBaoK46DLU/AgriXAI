"""Băm mật khẩu và phát hành JWT."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings

# bcrypt chỉ xử lý tối đa 72 byte đầu; cắt trước để không bị ném lỗi
_BCRYPT_MAX_BYTES = 72


def _truncate(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_truncate(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_truncate(password), hashed.encode("utf-8"))
    except ValueError:
        # Hash hỏng hoặc sai định dạng — coi như không khớp
        return False


def create_access_token(subject: str | int, extra: dict[str, Any] | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {"sub": str(subject), "exp": expire, **(extra or {})}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Trả về payload nếu token hợp lệ, None nếu hết hạn hoặc sai chữ ký."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        return None


def new_refresh_token_value() -> str:
    """Chuỗi ngẫu nhiên (không phải JWT) — refresh token phải thu hồi được
    theo từng bản ghi trong CSDL, JWT tự chứng thực (stateless) thì không."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """SHA-256 đủ dùng để tra cứu — token thô đã có entropy cao (48 byte
    ngẫu nhiên), không cần chi phí băm chậm như bcrypt cho mật khẩu."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
