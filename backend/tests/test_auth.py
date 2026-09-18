"""Kiểm thử luồng đăng nhập, làm mới token và đăng xuất.

Chạy:
    cd backend
    pytest tests/test_auth.py -v
"""

from __future__ import annotations

from app.core.config import settings

API = settings.API_V1_PREFIX


def _register(client, username: str) -> dict:
    response = client.post(f"{API}/auth/register", json={
        "username": username,
        "password": "matkhau123",
        "full_name": "Người dùng test refresh",
        "email": f"{username}@agrixai.vn",
    })
    assert response.status_code == 201, response.text
    return response.json()


def test_login_returns_refresh_token(client):
    # Đăng ký một tài khoản riêng thay vì dùng `nongdan` (fixture `seeded`,
    # dùng chung toàn bộ file test) — `test_api.py` có test đổi mật khẩu của
    # `nongdan`, nên mật khẩu seed ban đầu không còn đáng tin cậy ở đây.
    register_body = _register(client, "login_returns_refresh_user")
    response = client.post(f"{API}/auth/login", json={
        "username": "login_returns_refresh_user", "password": "matkhau123",
    })
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["refresh_token"] != register_body["refresh_token"]


def test_refresh_issues_new_access_token_and_rotates(client):
    body = _register(client, "refresh_rotate_user")
    old_refresh = body["refresh_token"]

    refreshed = client.post(f"{API}/auth/refresh", json={"refresh_token": old_refresh})
    assert refreshed.status_code == 200, refreshed.text
    new_body = refreshed.json()
    assert new_body["access_token"]
    assert new_body["refresh_token"]
    # Không so access token mới/cũ: JWT chỉ đổi nội dung khi `exp` (độ phân
    # giải giây) đổi, nên hai token phát trong cùng một giây giống hệt nhau
    # — không phải lỗi, refresh token (so được ở dưới) mới là thứ xoay vòng.
    assert new_body["refresh_token"] != old_refresh

    # Access token mới dùng được ngay
    me = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {new_body['access_token']}"})
    assert me.status_code == 200, me.text

    # Refresh token cũ đã bị thu hồi — dùng lại lần hai phải bị từ chối
    reused = client.post(f"{API}/auth/refresh", json={"refresh_token": old_refresh})
    assert reused.status_code == 401


def test_refresh_rejects_unknown_token(client):
    response = client.post(f"{API}/auth/refresh", json={"refresh_token": "khong-ton-tai"})
    assert response.status_code == 401


def test_logout_revokes_refresh_token(client):
    body = _register(client, "logout_user")
    refresh_token = body["refresh_token"]

    logout = client.post(f"{API}/auth/logout", json={"refresh_token": refresh_token})
    assert logout.status_code == 204

    # Token đã đăng xuất không dùng lại được để làm mới access token
    response = client.post(f"{API}/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 401

    # Gọi logout lần hai (token đã thu hồi/không tồn tại) vẫn không báo lỗi
    again = client.post(f"{API}/auth/logout", json={"refresh_token": refresh_token})
    assert again.status_code == 204
