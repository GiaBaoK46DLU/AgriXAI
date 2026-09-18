"""Schema cho xác thực và người dùng."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # giây


class TokenPair(Token):
    """`Token` + refresh token — trả về từ `/auth/login`, `/auth/register`,
    `/auth/refresh`. Tách khỏi `Token` vì `POST /auth/token` (dạng form,
    riêng cho nút Authorize của Swagger) không cần refresh token."""

    refresh_token: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    role: str = UserRole.FARMER


class UserCreate(UserBase):
    """Admin tạo tài khoản — được chọn vai trò, xem `POST /users`."""

    password: str = Field(min_length=6, max_length=128)


class RegisterRequest(BaseModel):
    """Tự đăng ký — luôn tạo với vai trò `farmer`, không được chọn vai trò
    như `UserCreate` (chỉ admin mới cấp quyền quản trị)."""

    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    role: str | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)


class UserOut(UserBase):
    """Trả về cho client — KHÔNG dùng lại kiểu `EmailStr` của `UserBase` cho
    trường `email`.

    `EmailStr` chạy lại toàn bộ kiểm tra cú pháp (kể cả chặn TLD dành riêng
    như `.local`/`.test`) mỗi lần serialize, tức là validate lại dữ liệu ĐÃ
    nằm trong CSDL. Một bản ghi cũ/nhập tay lỡ có email không hợp lệ sẽ làm
    sập `ResponseValidationError` ở MỌI endpoint trả `UserOut` (`/auth/login`,
    `/auth/me`...), không riêng gì chỗ tạo ra nó. Input (`RegisterRequest`,
    `UserCreate`, `UserUpdate`) vẫn giữ `EmailStr` để chặn email sai cú pháp
    ngay lúc nhận — chỉ output nới thành `str` vì lúc này dữ liệu coi như đã
    tin cậy, chỉ cần trả nguyên văn."""

    model_config = ConfigDict(from_attributes=True)

    email: str | None = None
    id: int
    is_active: bool
    created_at: datetime


class LoginResponse(TokenPair):
    user: UserOut


class ChangePasswordRequest(BaseModel):
    """Đổi mật khẩu tự phục vụ — khác `UserUpdate.password` (admin đặt mật
    khẩu hộ người khác, không cần biết mật khẩu cũ). Bắt buộc gửi kèm mật
    khẩu hiện tại để tránh việc một token bị đánh cắp có thể khoá tài khoản
    thật ngoài bằng cách đổi mật khẩu mà chủ tài khoản không biết."""

    current_password: str = Field(min_length=6, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)
