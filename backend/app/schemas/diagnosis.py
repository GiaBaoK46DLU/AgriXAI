"""Schema cho kết quả chẩn đoán và danh mục bệnh."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field

STORAGE_URL_PREFIX = "/storage"


class DiseaseInfo(BaseModel):
    """Thông tin tra cứu về một loại bệnh, lấy từ danh mục dùng chung."""

    key: str
    name_vi: str
    name_en: str
    pathogen: str | None = None
    is_healthy: bool = False
    symptoms: str = ""
    favorable_conditions: str | None = None
    treatments: list[str] = Field(default_factory=list)
    prevention: list[str] = Field(default_factory=list)
    reference_url: str | None = None


class ProbabilityItem(BaseModel):
    disease_key: str
    name_vi: str
    probability: float


class DiagnosisBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plot_id: int | None
    user_id: int
    disease_key: str
    disease_name: str
    confidence: float
    severity: str
    severity_name: str
    affected_ratio: float
    explanation: str | None
    model_version: str
    latency_ms: float
    note: str | None
    created_at: datetime

    image_path: str
    overlay_path: str | None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def image_url(self) -> str:
        return f"{STORAGE_URL_PREFIX}/{self.image_path}"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def overlay_url(self) -> str | None:
        return f"{STORAGE_URL_PREFIX}/{self.overlay_path}" if self.overlay_path else None


class DiagnosisOut(DiagnosisBase):
    """Bản rút gọn cho danh sách lịch sử."""

    plot_puc: str | None = None
    plot_name: str | None = None


class DiagnosisDetail(DiagnosisOut):
    """Bản đầy đủ cho màn hình kết quả — kèm gợi ý xử lý và top xác suất."""

    disease: DiseaseInfo | None = None
    top_predictions: list[ProbabilityItem] = Field(default_factory=list)
    disclaimer: str = ""


class DiagnosisUpdate(BaseModel):
    note: str | None = Field(default=None, max_length=500)
    plot_id: int | None = None


class DiagnosisPage(BaseModel):
    """Kết quả phân trang cho bảng lịch sử của web admin."""

    items: list[DiagnosisOut]
    total: int
    page: int
    page_size: int
