"""Schema cho thuốc gợi ý, gán thuốc theo bệnh, và video hướng dẫn.

Quản trị viên (web admin) là bên duy nhất ghi vào ba bảng này — xem
``models/medicine.py`` và mục "Tích hợp mô hình thật" trong CLAUDE.md để biết
vì sao ba bảng này nằm trong CSDL thay vì ``shared/data/tomato_diseases.json``.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class MedicineBase(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    group: str | None = Field(default=None, max_length=80)
    purchase_url: str | None = Field(default=None, max_length=500)


class MedicineCreate(MedicineBase):
    pass


class MedicineUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    group: str | None = Field(default=None, max_length=80)
    purchase_url: str | None = Field(default=None, max_length=500)


class MedicineOut(MedicineBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class DiseaseMedicineCreate(BaseModel):
    disease_key: str = Field(min_length=1, max_length=50)
    medicine_id: int
    note: str | None = Field(default=None, max_length=500)


class DiseaseMedicineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    disease_key: str
    medicine_id: int
    note: str | None = None
    # Ghép sẵn để web admin không phải tự tra tên thuốc theo medicine_id.
    medicine_name: str = ""


class DiseaseGuideUpsert(BaseModel):
    video_url: str = Field(min_length=1, max_length=500)


class DiseaseGuideOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    disease_key: str
    video_url: str
