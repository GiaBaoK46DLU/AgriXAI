"""Quản lý lô đất.

Nguyên tắc phân quyền áp dụng cho toàn bộ file: nông dân chỉ thấy và sửa được
lô đất của chính mình; quản trị thấy tất cả.
"""

from __future__ import annotations

import random
import string
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.diagnosis import Diagnosis
from app.models.plot import Plot
from app.models.user import User
from app.schemas.plot import PlotCreate, PlotOut, PlotUpdate, PlotWithStats

router = APIRouter()


def generate_puc(db) -> str:
    """Sinh mã vùng trồng chưa trùng, dạng ``PUC-2609-AB12``."""
    for _ in range(20):
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        candidate = f"PUC-{datetime.now():%y%m}-{suffix}"
        if db.scalar(select(Plot.id).where(Plot.puc == candidate)) is None:
            return candidate
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Không sinh được mã vùng trồng, thử lại",
    )


def get_owned_plot(db, plot_id: int, user: User) -> Plot:
    plot = db.get(Plot, plot_id)
    if plot is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy lô đất")
    if not user.is_admin and plot.owner_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Lô đất này không thuộc về bạn")
    return plot


@router.get("", response_model=list[PlotWithStats], summary="Danh sách lô đất")
def list_plots(
    db: DbSession,
    user: CurrentUser,
    q: str | None = Query(default=None, description="Tìm theo tên hoặc mã PUC"),
    region: str | None = None,
    owner_id: int | None = Query(default=None, description="Chỉ quản trị mới dùng được"),
    limit: int = Query(default=100, le=500),
    offset: int = 0,
):
    """Trang chủ app di động và bảng quản lý lô đất của web admin đều dùng endpoint này.

    Mỗi lô kèm sẵn thông tin lần chẩn đoán gần nhất để màn hình trang chủ không
    phải gọi thêm N request nữa.
    """
    stmt = select(Plot).options(selectinload(Plot.owner))

    if user.is_admin:
        if owner_id is not None:
            stmt = stmt.where(Plot.owner_id == owner_id)
    else:
        stmt = stmt.where(Plot.owner_id == user.id)

    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(Plot.name.ilike(pattern) | Plot.puc.ilike(pattern))
    if region:
        stmt = stmt.where(Plot.region == region)

    plots = db.scalars(
        stmt.order_by(Plot.created_at.desc()).limit(limit).offset(offset)
    ).all()

    if not plots:
        return []

    plot_ids = [p.id for p in plots]

    counts = dict(
        db.execute(
            select(Diagnosis.plot_id, func.count(Diagnosis.id))
            .where(Diagnosis.plot_id.in_(plot_ids))
            .group_by(Diagnosis.plot_id)
        ).all()
    )

    # Lần chẩn đoán gần nhất của mỗi lô: lấy id lớn nhất theo từng plot_id
    latest_ids = db.scalars(
        select(func.max(Diagnosis.id))
        .where(Diagnosis.plot_id.in_(plot_ids))
        .group_by(Diagnosis.plot_id)
    ).all()
    latest = {
        d.plot_id: d
        for d in db.scalars(select(Diagnosis).where(Diagnosis.id.in_(latest_ids))).all()
    }

    result = []
    for plot in plots:
        last = latest.get(plot.id)
        result.append(
            PlotWithStats(
                **PlotOut.model_validate(plot).model_dump(),
                owner_name=plot.owner.full_name if plot.owner else None,
                diagnosis_count=counts.get(plot.id, 0),
                last_diagnosis_at=last.created_at if last else None,
                last_disease_name=last.disease_name if last else None,
                last_severity=last.severity if last else None,
            )
        )
    return result


@router.post("", response_model=PlotOut, status_code=status.HTTP_201_CREATED,
             summary="Tạo lô đất mới")
def create_plot(payload: PlotCreate, db: DbSession, user: CurrentUser):
    owner_id = user.id
    if payload.owner_id is not None:
        if not user.is_admin:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Chỉ quản trị mới được tạo lô đất cho người khác",
            )
        if db.get(User, payload.owner_id) is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy chủ lô đất")
        owner_id = payload.owner_id

    puc = payload.puc or generate_puc(db)
    if db.scalar(select(Plot.id).where(Plot.puc == puc)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Mã vùng trồng '{puc}' đã tồn tại")

    data = payload.model_dump(exclude={"puc", "owner_id"})
    plot = Plot(puc=puc, owner_id=owner_id, **data)
    db.add(plot)
    db.commit()
    db.refresh(plot)
    return plot


@router.get("/{plot_id}", response_model=PlotOut, summary="Chi tiết lô đất")
def get_plot(plot_id: int, db: DbSession, user: CurrentUser):
    return get_owned_plot(db, plot_id, user)


@router.patch("/{plot_id}", response_model=PlotOut, summary="Cập nhật lô đất")
def update_plot(plot_id: int, payload: PlotUpdate, db: DbSession, user: CurrentUser):
    plot = get_owned_plot(db, plot_id, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(plot, field, value)
    db.commit()
    db.refresh(plot)
    return plot


@router.delete("/{plot_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Xoá lô đất")
def delete_plot(plot_id: int, db: DbSession, user: CurrentUser):
    """Lịch sử chẩn đoán của lô KHÔNG bị xoá theo — ``plot_id`` chỉ được gỡ về NULL.

    Dữ liệu chẩn đoán là bằng chứng đã ghi nhận tại thời điểm đó, xoá lô đất
    không có nghĩa là chuyện đã xảy ra bị xoá.
    """
    plot = get_owned_plot(db, plot_id, user)
    db.delete(plot)
    db.commit()
