"""Số liệu thống kê cho trang tổng quan của web admin."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.deps import AdminUser, DbSession
from app.models.diagnosis import Diagnosis
from app.models.plot import Plot
from app.models.user import User, UserRole
from app.schemas.stats import (
    DashboardStats,
    DiseaseCount,
    OverviewStats,
    SeverityCount,
    TimeseriesPoint,
)
from app.services import catalog
from app.services.inference.loader import get_predictor, is_using_real_model

router = APIRouter()

# Mức độ được coi là đáng cảnh báo trên dashboard
ALERT_SEVERITIES = ("severe",)


@router.get("/dashboard", response_model=DashboardStats,
            summary="Toàn bộ số liệu trang tổng quan")
def dashboard(
    db: DbSession,
    _: AdminUser,
    days: int = Query(default=30, ge=7, le=365, description="Khoảng thời gian của biểu đồ"),
):
    """Gộp tất cả số liệu vào MỘT request.

    Trang tổng quan cần 4 ô số + 1 biểu đồ đường + 2 biểu đồ phân bố. Tách
    thành 7 endpoint sẽ khiến trang phải chờ 7 lượt mạng mới vẽ xong.
    """
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)

    overview = OverviewStats(
        total_plots=db.scalar(select(func.count(Plot.id))) or 0,
        total_farmers=db.scalar(
            select(func.count(User.id)).where(User.role == UserRole.FARMER)
        ) or 0,
        total_diagnoses=db.scalar(select(func.count(Diagnosis.id))) or 0,
        recent_alerts=db.scalar(
            select(func.count(Diagnosis.id)).where(
                Diagnosis.severity.in_(ALERT_SEVERITIES),
                Diagnosis.created_at >= now - timedelta(days=7),
            )
        ) or 0,
    )

    # Số ca theo ngày.
    # Gom nhóm ở phía Python thay vì CAST(... AS DATE) trong câu SQL: SQLite không
    # có kiểu ngày thật nên CAST trả về số nguyên và làm hỏng kết quả, trong khi
    # PostgreSQL trả về đối tượng date — hai kiểu khác nhau tuỳ CSDL. Số bản ghi
    # trong tối đa 365 ngày ở quy mô đề tài này không đáng kể.
    per_day: Counter[date] = Counter(
        created.date()
        for (created,) in db.execute(
            select(Diagnosis.created_at).where(Diagnosis.created_at >= since)
        ).all()
    )
    timeseries = [
        TimeseriesPoint(day=day, count=per_day[day]) for day in sorted(per_day)
    ]

    # Phân bố theo loại bệnh
    by_disease = [
        DiseaseCount(
            disease_key=key,
            name_vi=catalog.get_disease(key).get("name_vi", key),
            count=count,
        )
        for key, count in db.execute(
            select(Diagnosis.disease_key, func.count(Diagnosis.id).label("c"))
            .where(Diagnosis.created_at >= since)
            .group_by(Diagnosis.disease_key)
            .order_by(func.count(Diagnosis.id).desc())
        ).all()
    ]

    severity_names = {s["key"]: s["name_vi"] for s in catalog.severity_levels()}
    by_severity = [
        SeverityCount(severity=key, name_vi=severity_names.get(key, key), count=count)
        for key, count in db.execute(
            select(Diagnosis.severity, func.count(Diagnosis.id))
            .where(Diagnosis.created_at >= since)
            .group_by(Diagnosis.severity)
        ).all()
    ]

    return DashboardStats(
        overview=overview,
        timeseries=timeseries,
        by_disease=by_disease,
        by_severity=by_severity,
        # Hiển thị rõ trên dashboard khi hệ thống đang chạy mô hình giả, tránh
        # trường hợp ai đó tưởng số liệu demo là số liệu thật
        using_real_model=is_using_real_model(),
        model_version=getattr(get_predictor(), "model_version", "unknown"),
    )
