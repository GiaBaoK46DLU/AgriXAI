"""Quản lý thuốc gợi ý, gán thuốc theo bệnh, và video hướng dẫn xử lý.

Toàn bộ endpoint trong file này chỉ dành cho quản trị (``AdminUser``) — đây là
dữ liệu web admin ghi vào, người dùng cuối chỉ đọc qua ``GET /diseases/{key}``
(xem ``endpoints/diseases.py`` và ``services/catalog.py``).

``disease_key`` nhận vào không được validate chặt bằng khoá ngoại (xem
``models/medicine.py``), nhưng vẫn kiểm tra tồn tại trong danh mục JSON để
tránh gán nhầm thuốc/video cho một khoá đánh máy sai.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import AdminUser, DbSession
from app.models.medicine import DiseaseGuide, DiseaseMedicine, Medicine
from app.schemas.medicine import (
    DiseaseGuideOut,
    DiseaseGuideUpsert,
    DiseaseMedicineCreate,
    DiseaseMedicineOut,
    MedicineCreate,
    MedicineOut,
    MedicineUpdate,
)
from app.services import catalog

router = APIRouter()


def _check_disease_key(disease_key: str) -> None:
    if disease_key not in catalog.diseases_by_key():
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"Không có bệnh nào mang khoá '{disease_key}' trong danh mục",
        )


def _get_medicine(db, medicine_id: int) -> Medicine:
    medicine = db.get(Medicine, medicine_id)
    if medicine is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thuốc")
    return medicine


# ── Thuốc ──

@router.get("", response_model=list[MedicineOut], summary="Danh sách thuốc")
def list_medicines(db: DbSession, _: AdminUser):
    return db.scalars(select(Medicine).order_by(Medicine.name)).all()


@router.post("", response_model=MedicineOut, status_code=status.HTTP_201_CREATED,
             summary="Thêm thuốc mới")
def create_medicine(payload: MedicineCreate, db: DbSession, _: AdminUser):
    medicine = Medicine(**payload.model_dump())
    db.add(medicine)
    db.commit()
    db.refresh(medicine)
    return medicine


@router.patch("/{medicine_id}", response_model=MedicineOut, summary="Sửa thông tin thuốc")
def update_medicine(medicine_id: int, payload: MedicineUpdate, db: DbSession, _: AdminUser):
    medicine = _get_medicine(db, medicine_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(medicine, field, value)
    db.commit()
    db.refresh(medicine)
    return medicine


@router.delete("/{medicine_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Xoá thuốc")
def delete_medicine(medicine_id: int, db: DbSession, _: AdminUser):
    """Xoá kéo theo mọi lượt gán thuốc này cho bệnh (``ondelete="CASCADE"``)."""
    medicine = _get_medicine(db, medicine_id)
    db.delete(medicine)
    db.commit()


# ── Gán thuốc theo bệnh ──

@router.get("/assignments", response_model=list[DiseaseMedicineOut],
            summary="Danh sách thuốc đã gán cho một bệnh")
def list_assignments(
    db: DbSession,
    _: AdminUser,
    disease_key: str = Query(..., description="Khoá bệnh cần xem"),
):
    rows = db.execute(
        select(DiseaseMedicine, Medicine.name)
        .join(Medicine, Medicine.id == DiseaseMedicine.medicine_id)
        .where(DiseaseMedicine.disease_key == disease_key)
    ).all()
    return [
        DiseaseMedicineOut(
            id=dm.id,
            disease_key=dm.disease_key,
            medicine_id=dm.medicine_id,
            note=dm.note,
            medicine_name=name,
        )
        for dm, name in rows
    ]


@router.post("/assignments", response_model=DiseaseMedicineOut,
             status_code=status.HTTP_201_CREATED, summary="Gán một thuốc cho một bệnh")
def create_assignment(payload: DiseaseMedicineCreate, db: DbSession, _: AdminUser):
    _check_disease_key(payload.disease_key)
    medicine = _get_medicine(db, payload.medicine_id)

    assignment = DiseaseMedicine(**payload.model_dump())
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return DiseaseMedicineOut(
        id=assignment.id,
        disease_key=assignment.disease_key,
        medicine_id=assignment.medicine_id,
        note=assignment.note,
        medicine_name=medicine.name,
    )


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Gỡ một lượt gán thuốc")
def delete_assignment(assignment_id: int, db: DbSession, _: AdminUser):
    assignment = db.get(DiseaseMedicine, assignment_id)
    if assignment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy lượt gán thuốc")
    db.delete(assignment)
    db.commit()


# ── Video hướng dẫn ──

@router.get("/guides/{disease_key}", response_model=DiseaseGuideOut | None,
            summary="Video hướng dẫn hiện tại của một bệnh")
def get_guide(disease_key: str, db: DbSession, _: AdminUser):
    _check_disease_key(disease_key)
    return db.get(DiseaseGuide, disease_key)


@router.put("/guides/{disease_key}", response_model=DiseaseGuideOut,
            summary="Đặt / đổi video hướng dẫn cho một bệnh")
def upsert_guide(disease_key: str, payload: DiseaseGuideUpsert, db: DbSession, _: AdminUser):
    """Tối đa một video mỗi bệnh (``disease_key`` là khoá chính) — đặt lại là ghi đè."""
    _check_disease_key(disease_key)
    guide = db.get(DiseaseGuide, disease_key)
    if guide is None:
        guide = DiseaseGuide(disease_key=disease_key, video_url=payload.video_url)
        db.add(guide)
    else:
        guide.video_url = payload.video_url
    db.commit()
    db.refresh(guide)
    return guide


@router.delete("/guides/{disease_key}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Gỡ video hướng dẫn của một bệnh")
def delete_guide(disease_key: str, db: DbSession, _: AdminUser):
    guide = db.get(DiseaseGuide, disease_key)
    if guide is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Bệnh này chưa có video hướng dẫn")
    db.delete(guide)
    db.commit()
