"""Chẩn đoán bệnh — endpoint trung tâm của hệ thống."""

from __future__ import annotations

from datetime import date, datetime, time

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.models.diagnosis import Diagnosis
from app.models.plot import Plot
from app.models.user import User
from app.schemas.diagnosis import (
    DiagnosisDetail,
    DiagnosisOut,
    DiagnosisPage,
    DiagnosisUpdate,
    DiseaseInfo,
    ProbabilityItem,
)
from app.services import catalog, diagnosis_service
from app.services.storage.local import InvalidImageError

router = APIRouter()


# ── Chuyển bản ghi CSDL thành schema trả về ──

def _attach_plot(schema: DiagnosisOut, record: Diagnosis) -> None:
    schema.plot_puc = record.plot.puc if record.plot else None
    schema.plot_name = record.plot.name if record.plot else None


def _to_out(record: Diagnosis) -> DiagnosisOut:
    out = DiagnosisOut.model_validate(record)
    _attach_plot(out, record)
    return out


def _to_detail(record: Diagnosis) -> DiagnosisDetail:
    detail = DiagnosisDetail.model_validate(record)
    _attach_plot(detail, record)

    info = catalog.get_disease(record.disease_key)
    detail.disease = DiseaseInfo(
        **{k: v for k, v in info.items() if k in DiseaseInfo.model_fields}
    )
    detail.top_predictions = [
        ProbabilityItem(**p) for p in diagnosis_service.top_predictions(record)
    ]
    detail.disclaimer = catalog.disclaimer()
    return detail


def _get_owned(db, diagnosis_id: int, user: User) -> Diagnosis:
    record = db.get(Diagnosis, diagnosis_id)
    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy bản chẩn đoán")
    if not user.is_admin and record.user_id != user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Bản ghi này không thuộc về bạn")
    return record


# ── Endpoint ──

@router.post("", response_model=DiagnosisDetail, status_code=status.HTTP_201_CREATED,
             summary="Chẩn đoán bệnh từ ảnh")
async def create_diagnosis(
    db: DbSession,
    user: CurrentUser,
    file: UploadFile = File(..., description="Ảnh lá cà chua (JPEG/PNG/WEBP)"),
    plot_id: int | None = Form(default=None, description="Lô đất áp dụng"),
    note: str | None = Form(default=None, description="Ghi chú của người dùng"),
):
    """Nhận ảnh, chạy mô hình + Grad-CAM, lưu kết quả và trả về đầy đủ phần giải thích.

    Đây là endpoint mà app di động gọi ở màn hình *Chụp / tải ảnh*.
    """
    if plot_id is not None:
        plot = db.get(Plot, plot_id)
        if plot is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy lô đất")
        if not user.is_admin and plot.owner_id != user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Lô đất này không thuộc về bạn")

    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "File ảnh rỗng")
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            f"Ảnh vượt quá {settings.MAX_UPLOAD_MB} MB. Hãy chụp ở độ phân giải thấp hơn.",
        )

    try:
        record = diagnosis_service.run_diagnosis(
            db, user_id=user.id, plot_id=plot_id, image_bytes=data, note=note
        )
    except InvalidImageError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    return _to_detail(record)


@router.get("", response_model=DiagnosisPage, summary="Lịch sử chẩn đoán")
def list_diagnoses(
    db: DbSession,
    user: CurrentUser,
    plot_id: int | None = None,
    user_id: int | None = Query(default=None, description="Chỉ quản trị mới lọc được"),
    disease_key: str | None = None,
    severity: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """Dùng cho cả màn *Lịch sử* của app lẫn bảng lịch sử toàn hệ thống của web admin.

    Nông dân luôn chỉ thấy bản ghi của chính mình, bất kể truyền tham số gì.
    """
    stmt = select(Diagnosis).options(selectinload(Diagnosis.plot))
    count_stmt = select(func.count(Diagnosis.id))

    filters = []
    if user.is_admin:
        if user_id is not None:
            filters.append(Diagnosis.user_id == user_id)
    else:
        filters.append(Diagnosis.user_id == user.id)

    if plot_id is not None:
        filters.append(Diagnosis.plot_id == plot_id)
    if disease_key:
        filters.append(Diagnosis.disease_key == disease_key)
    if severity:
        filters.append(Diagnosis.severity == severity)
    if date_from:
        filters.append(Diagnosis.created_at >= datetime.combine(date_from, time.min))
    if date_to:
        filters.append(Diagnosis.created_at <= datetime.combine(date_to, time.max))

    if filters:
        stmt = stmt.where(*filters)
        count_stmt = count_stmt.where(*filters)

    total = db.scalar(count_stmt) or 0
    records = db.scalars(
        stmt.order_by(Diagnosis.created_at.desc())
        .limit(page_size)
        .offset((page - 1) * page_size)
    ).all()

    return DiagnosisPage(
        items=[_to_out(r) for r in records],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{diagnosis_id}", response_model=DiagnosisDetail, summary="Chi tiết chẩn đoán")
def get_diagnosis(diagnosis_id: int, db: DbSession, user: CurrentUser):
    return _to_detail(_get_owned(db, diagnosis_id, user))


@router.patch("/{diagnosis_id}", response_model=DiagnosisDetail,
              summary="Sửa ghi chú hoặc gán lại lô đất")
def update_diagnosis(diagnosis_id: int, payload: DiagnosisUpdate,
                     db: DbSession, user: CurrentUser):
    record = _get_owned(db, diagnosis_id, user)

    if payload.note is not None:
        record.note = payload.note
    if payload.plot_id is not None:
        plot = db.get(Plot, payload.plot_id)
        if plot is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy lô đất")
        if not user.is_admin and plot.owner_id != user.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Lô đất này không thuộc về bạn")
        record.plot_id = payload.plot_id

    db.commit()
    db.refresh(record)
    return _to_detail(record)


@router.delete("/{diagnosis_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Xoá bản chẩn đoán")
def delete_diagnosis(diagnosis_id: int, db: DbSession, user: CurrentUser):
    record = _get_owned(db, diagnosis_id, user)
    db.delete(record)
    db.commit()
