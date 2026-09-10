"""Thời tiết cho ô ở trang chủ.

Không cần đăng nhập — cùng lý do với ``diseases.py``: không phải dữ liệu cá
nhân, và toạ độ đang cố định ở Đà Lạt cho mọi người dùng (xem CLAUDE.md).
"""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.weather import WeatherOut
from app.services import weather_service

router = APIRouter()


@router.get("", response_model=WeatherOut, summary="Thời tiết Đà Lạt hiện tại + 4 ngày tới")
def get_weather() -> WeatherOut:
    return weather_service.fetch_weather()
