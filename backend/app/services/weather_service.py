"""Ô thời tiết ở trang chủ app di động.

Gọi hai endpoint miễn phí của OpenWeather (Current Weather + 5 Day / 3 Hour
Forecast) — không dùng One Call vì gói đó cần đăng ký riêng. Toạ độ cố định ở
Đà Lạt (``settings.WEATHER_LAT/LON``), không lấy theo từng lô đất — xem
CLAUDE.md mục phạm vi đề tài.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
from fastapi import HTTPException, status

from app.core.config import settings
from app.schemas.weather import ForecastDay, WeatherOut

_BASE_URL = "https://api.openweathermap.org/data/2.5"

# `datetime.weekday()`: 0 = Thứ Hai ... 6 = Chủ Nhật.
_WEEKDAY_VI = ("T2", "T3", "T4", "T5", "T6", "T7", "CN")


def _weekday_label(dt: datetime) -> str:
    return _WEEKDAY_VI[dt.weekday()]


def _wind_label(speed_ms: float) -> str:
    if speed_ms < 2:
        return "gió nhẹ"
    if speed_ms < 5.5:
        return "gió vừa"
    return "gió mạnh"


def _rain_note(today_slots: list[dict]) -> str:
    """Mô tả khả năng mưa trong các mốc còn lại của hôm nay (giờ địa phương)."""
    night = [s for s in today_slots if s["local"].hour >= 18]
    if any(s["pop"] >= 0.4 for s in night):
        return "mưa về đêm"
    if any(s["pop"] >= 0.4 for s in today_slots):
        return "có thể mưa trong ngày"
    return "trời quang"


def _advisory(temp: float, humidity: int) -> str | None:
    """Cảnh báo điều kiện thuận lợi cho mốc sương muộn — bệnh phổ biến nhất ở
    Đà Lạt (xem ``favorable_conditions`` của ``late_blight`` trong
    ``shared/data/tomato_diseases.json``: 15–22°C kèm ẩm cao kéo dài). Chỉ một
    ngưỡng đơn giản để nhắc kiểm tra vườn, không phải mô hình dự báo bệnh.
    """
    if humidity >= 80 and 14 <= temp <= 23:
        return (
            "Ẩm cao kéo dài — điều kiện thuận lợi cho mốc sương muộn. "
            "Nên kiểm tra vườn hôm nay."
        )
    if humidity >= 88:
        return "Độ ẩm rất cao — nguy cơ nấm bệnh tăng, nên kiểm tra vườn thường xuyên hơn."
    return None


def fetch_weather() -> WeatherOut:
    if not settings.OPENWEATHER_API_KEY:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Chưa cấu hình OPENWEATHER_API_KEY trong .env",
        )

    params = {
        "lat": settings.WEATHER_LAT,
        "lon": settings.WEATHER_LON,
        "appid": settings.OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": "vi",
    }
    try:
        with httpx.Client(timeout=8.0) as client:
            current = client.get(f"{_BASE_URL}/weather", params=params).json()
            forecast = client.get(f"{_BASE_URL}/forecast", params=params).json()
    except httpx.HTTPError as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Không gọi được dịch vụ thời tiết, thử lại sau.",
        ) from exc

    if str(current.get("cod")) != "200" or str(forecast.get("cod")) != "200":
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "Dịch vụ thời tiết trả về lỗi, thử lại sau.",
        )

    tz_offset = forecast.get("city", {}).get("timezone", 0)
    now_local = datetime.now(timezone.utc) + timedelta(seconds=tz_offset)
    today = now_local.date()

    slots = [
        {
            "local": datetime.fromtimestamp(item["dt"], tz=timezone.utc)
            + timedelta(seconds=tz_offset),
            "temp": item["main"]["temp"],
            "pop": item.get("pop", 0.0),
        }
        for item in forecast["list"]
    ]

    today_slots = [s for s in slots if s["local"].date() == today]
    detail = (
        f"Độ ẩm {current['main']['humidity']}% · "
        f"{_wind_label(current['wind']['speed'])} · "
        f"{_rain_note(today_slots)}"
    )

    # Một mốc đại diện mỗi ngày (giờ gần 12:00 trưa nhất) cho 4 ngày kế tiếp.
    by_date: dict = {}
    for s in slots:
        d = s["local"].date()
        if d == today:
            continue
        best = by_date.get(d)
        if best is None or abs(s["local"].hour - 12) < abs(best["local"].hour - 12):
            by_date[d] = s

    forecast_days = [
        ForecastDay(
            day=_weekday_label(now_local),
            temp=round(current["main"]["temp"]),
            is_now=True,
        )
    ]
    for d in sorted(by_date)[:4]:
        s = by_date[d]
        forecast_days.append(
            ForecastDay(day=_weekday_label(s["local"]), temp=round(s["temp"]), is_now=False)
        )

    return WeatherOut(
        location=settings.WEATHER_LOCATION_NAME,
        temp=round(current["main"]["temp"]),
        description=current["weather"][0]["description"],
        detail=detail,
        advisory=_advisory(current["main"]["temp"], current["main"]["humidity"]),
        forecast=forecast_days,
    )
