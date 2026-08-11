"""Schema cho các số liệu thống kê của dashboard quản trị."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class OverviewStats(BaseModel):
    """Bốn ô số liệu ở đầu trang tổng quan."""

    total_plots: int
    total_farmers: int
    total_diagnoses: int
    recent_alerts: int  # ca bệnh mức nặng trong 7 ngày gần nhất


class TimeseriesPoint(BaseModel):
    day: date
    count: int


class DiseaseCount(BaseModel):
    disease_key: str
    name_vi: str
    count: int


class SeverityCount(BaseModel):
    severity: str
    name_vi: str
    count: int


class DashboardStats(BaseModel):
    overview: OverviewStats
    timeseries: list[TimeseriesPoint]
    by_disease: list[DiseaseCount]
    by_severity: list[SeverityCount]
    using_real_model: bool
    model_version: str
