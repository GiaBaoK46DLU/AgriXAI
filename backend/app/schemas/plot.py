"""Schema cho lô đất."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.plot import PlotStatus


class PlotBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    region: str | None = Field(default=None, max_length=120)
    area_m2: float | None = Field(default=None, ge=0)
    crop: str = Field(default="tomato", max_length=50)
    status: str = PlotStatus.ACTIVE
    note: str | None = Field(default=None, max_length=500)


class PlotCreate(PlotBase):
    # Mã vùng trồng. Bỏ trống thì hệ thống tự sinh.
    puc: str | None = Field(default=None, max_length=32)
    # Chỉ quản trị mới được gán lô đất cho nông dân khác; nông dân bỏ trống.
    owner_id: int | None = None


class PlotUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    region: str | None = Field(default=None, max_length=120)
    area_m2: float | None = Field(default=None, ge=0)
    crop: str | None = Field(default=None, max_length=50)
    status: str | None = None
    note: str | None = Field(default=None, max_length=500)


class PlotOut(PlotBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    puc: str
    owner_id: int
    created_at: datetime


class PlotWithStats(PlotOut):
    """Dùng cho màn hình trang chủ của app: mỗi lô kèm tình trạng gần nhất."""

    owner_name: str | None = None
    diagnosis_count: int = 0
    last_diagnosis_at: datetime | None = None
    last_disease_name: str | None = None
    last_severity: str | None = None
