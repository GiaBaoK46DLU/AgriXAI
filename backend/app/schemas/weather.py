"""Schema cho ô thời tiết ở trang chủ app di động."""

from __future__ import annotations

from pydantic import BaseModel


class ForecastDay(BaseModel):
    day: str
    temp: int
    is_now: bool


class WeatherOut(BaseModel):
    location: str
    temp: int
    description: str

    # Câu đã dựng sẵn để hiện thẳng lên UI, ví dụ "Độ ẩm 89% · gió nhẹ · có
    # thể mưa về đêm" — dựng ở backend để không lặp lại ngưỡng phân loại gió/
    # mưa ở cả hai phía (xem CLAUDE.md mục nhận diện ngoại tuyến, nơi việc
    # chép logic sang Dart từng gây khó đồng bộ).
    detail: str

    # `null` khi không có cảnh báo nào đáng nói.
    advisory: str | None = None

    forecast: list[ForecastDay]
