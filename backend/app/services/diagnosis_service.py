"""Điều phối một lần chẩn đoán — nơi mô hình, XAI, lưu trữ và CSDL gặp nhau.

Đây là luồng trung tâm của cả hệ thống. Người dùng tải lên 3–5 ảnh (xem
``app/api/v1/endpoints/diagnoses.py``); mỗi ảnh chạy hết luồng dưới đây một
cách độc lập:

    bytes ảnh
      -> mở & chuẩn hoá (xoay đúng chiều, thu nhỏ)
      -> predictor.predict()          [mô hình + Grad-CAM]
      -> explain.interpret()          [mức độ, vị trí, câu giải thích]
      -> overlay.draw_regions()       [vẽ vùng khoanh]
      -> lưu 2 ảnh + 1 bản ghi CSDL (``DiagnosisImage``)

Kết quả cuối cùng của cả lô ảnh tổng hợp bằng cách gộp toàn bộ danh sách xác
suất theo từng bệnh mà mỗi ảnh trả về, lấy **trung bình cộng theo từng bệnh**
qua tất cả các ảnh (kể cả ảnh không tự chọn bệnh đó là top-1), rồi **xếp hạng
từ cao xuống thấp** — bệnh có tỉ lệ trung bình cao nhất thắng. Cách này phản
ánh đúng "% tỉ lệ tổng hợp" thay vì chỉ đếm phiếu top-1 của từng ảnh, nên một
bệnh được nhiều ảnh đồng thuận với xác suất cao vẫn có thể thắng dù không có
ảnh nào tự chọn nó làm top-1 riêng lẻ.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.diagnosis import Diagnosis, DiagnosisImage
from app.services import catalog
from app.services.inference.base import Prediction
from app.services.inference.loader import get_predictor
from app.services.storage import local as storage
from app.services.xai import explain, overlay
from app.services.xai.explain import Explanation

logger = logging.getLogger(__name__)


@dataclass
class _ImageResult:
    prediction: Prediction
    interpretation: Explanation
    image_path: str
    overlay_path: str | None


def _run_single_image(image_bytes: bytes) -> _ImageResult:
    """Chạy toàn bộ luồng mô hình + XAI cho một ảnh, và lưu ảnh xuống đĩa.

    Raises:
        storage.InvalidImageError: ảnh hỏng hoặc sai định dạng.
    """
    image = storage.open_and_normalize(image_bytes)

    predictor = get_predictor()
    prediction = predictor.predict(image)

    interpretation = explain.interpret(
        prediction.disease_key, prediction.confidence, prediction.heatmap
    )

    image_path = storage.save_upload(image)

    # Chỉ sinh ảnh overlay khi thực sự có vùng đáng khoanh. Vẽ một vòng elip
    # bừa lên ảnh khi mô hình không chắc chắn còn tệ hơn là không vẽ gì.
    overlay_path: str | None = None
    if prediction.heatmap is not None and overlay.has_visible_region(prediction.heatmap):
        try:
            overlay_path = storage.save_overlay(
                overlay.draw_regions(image, prediction.heatmap)
            )
        except Exception:  # noqa: BLE001
            # Vẽ hỏng thì vẫn phải trả về được kết quả chẩn đoán
            logger.exception("Không vẽ được ảnh overlay, bỏ qua phần khoanh vùng")

    return _ImageResult(
        prediction=prediction,
        interpretation=interpretation,
        image_path=image_path,
        overlay_path=overlay_path,
    )


def _average_probabilities(results: list[_ImageResult]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for result in results:
        for key, prob in (result.prediction.probabilities or {}).items():
            totals[key] = totals.get(key, 0.0) + prob
    n = len(results)
    return {key: total / n for key, total in totals.items()}


@dataclass
class _Aggregate:
    results: list[_ImageResult]
    top_key: str
    avg_probabilities: dict[str, float]
    avg_confidence: float
    representative: _ImageResult


def _run_and_aggregate(images: list[bytes]) -> _Aggregate:
    if not images:
        raise ValueError("images không được rỗng")

    results = [_run_single_image(raw) for raw in images]

    avg_probabilities = _average_probabilities(results)
    # Xếp hạng từ cao xuống thấp theo % trung bình rồi chọn bệnh đứng đầu —
    # không phải bệnh được nhiều ảnh tự chọn làm top-1 nhất.
    ranked = sorted(avg_probabilities.items(), key=lambda kv: kv[1], reverse=True)
    top_key, avg_confidence = ranked[0]

    # Ảnh đại diện cho phần XAI (giải thích/mức độ/ảnh overlay chính): ảnh có
    # xác suất riêng cho đúng bệnh thắng cuộc cao nhất — luôn tồn tại vì
    # `top_key` chỉ đứng đầu bảng xếp hạng nhờ có mặt trong xác suất của
    # ít nhất một ảnh.
    representative = max(
        results, key=lambda r: r.prediction.probabilities.get(top_key, 0.0)
    )

    return _Aggregate(results, top_key, avg_probabilities, avg_confidence, representative)


def run_diagnosis(db: Session, *, user_id: int, plot_id: int | None,
                  images: list[bytes], note: str | None = None) -> Diagnosis:
    """Chạy toàn bộ luồng chẩn đoán cho một lô ảnh và ghi kết quả vào CSDL.

    Raises:
        storage.InvalidImageError: một trong các ảnh hỏng hoặc sai định dạng.
    """
    agg = _run_and_aggregate(images)
    disease = catalog.get_disease(agg.top_key)
    rep_interp = agg.representative.interpretation

    record = Diagnosis(
        user_id=user_id,
        plot_id=plot_id,
        image_path=agg.representative.image_path,
        overlay_path=agg.representative.overlay_path,
        disease_key=agg.top_key,
        disease_name=disease.get("name_vi", agg.top_key),
        confidence=agg.avg_confidence,
        probabilities=agg.avg_probabilities,
        severity=rep_interp.severity,
        severity_name=rep_interp.severity_name,
        affected_ratio=rep_interp.affected_ratio,
        explanation=rep_interp.text,
        model_version=agg.representative.prediction.model_version,
        latency_ms=sum(r.prediction.latency_ms for r in agg.results),
        note=note,
    )
    db.add(record)
    db.flush()  # cần record.id để gán khoá ngoại cho từng ảnh

    for result in agg.results:
        image_disease = catalog.get_disease(result.prediction.disease_key)
        db.add(DiagnosisImage(
            diagnosis_id=record.id,
            image_path=result.image_path,
            overlay_path=result.overlay_path,
            disease_key=result.prediction.disease_key,
            disease_name=image_disease.get("name_vi", result.prediction.disease_key),
            confidence=result.prediction.confidence,
        ))

    db.commit()
    db.refresh(record)
    return record


def run_diagnosis_preview(user_id: int, images: list[bytes]) -> Diagnosis:
    """Chẩn đoán nhanh từ nút chụp ảnh chung (không qua một lô đất cụ thể) —
    không ghi gì vào CSDL nên không xuất hiện ở Lịch sử, theo đúng quy tắc "chỉ
    lưu kết quả khi có gắn lô đất" (xem CLAUDE.md mục quản lý lô đất).

    Ảnh gốc/overlay vẫn được lưu xuống đĩa như luồng có lưu (`_run_single_image`
    không đổi) vì màn kết quả cần URL ảnh để hiển thị khoanh vùng — chấp nhận
    đây là ảnh mồ côi không có bản ghi CSDL trỏ tới, phạm vi đồ án nhỏ nên
    không đáng xây thêm cơ chế dọn rác cho việc này.

    Trả về một `Diagnosis` KHÔNG được `db.add()` — chỉ dùng để tái sử dụng
    `_to_detail()` ở endpoint, không bao giờ được commit.
    """
    agg = _run_and_aggregate(images)
    disease = catalog.get_disease(agg.top_key)
    rep_interp = agg.representative.interpretation

    record = Diagnosis(
        user_id=user_id,
        plot_id=None,
        image_path=agg.representative.image_path,
        overlay_path=agg.representative.overlay_path,
        disease_key=agg.top_key,
        disease_name=disease.get("name_vi", agg.top_key),
        confidence=agg.avg_confidence,
        probabilities=agg.avg_probabilities,
        severity=rep_interp.severity,
        severity_name=rep_interp.severity_name,
        affected_ratio=rep_interp.affected_ratio,
        explanation=rep_interp.text,
        model_version=agg.representative.prediction.model_version,
        latency_ms=sum(r.prediction.latency_ms for r in agg.results),
        note=None,
    )
    record.id = 0
    record.created_at = datetime.now(timezone.utc)
    record.images = [
        DiagnosisImage(
            id=idx + 1,
            diagnosis_id=0,
            image_path=result.image_path,
            overlay_path=result.overlay_path,
            disease_key=result.prediction.disease_key,
            disease_name=catalog.get_disease(result.prediction.disease_key)
            .get("name_vi", result.prediction.disease_key),
            confidence=result.prediction.confidence,
        )
        for idx, result in enumerate(agg.results)
    ]
    return record


def top_predictions(record: Diagnosis, limit: int = 3) -> list[dict]:
    """Ba lớp có xác suất trung bình cao nhất — hiển thị ở màn hình kết quả.

    Giúp người dùng thấy mô hình còn phân vân giữa những bệnh nào, thay vì chỉ
    đưa một đáp án duy nhất. Bản thân việc này cũng là một dạng minh bạch hoá.
    """
    if not record.probabilities:
        return []

    ordered = sorted(record.probabilities.items(), key=lambda kv: kv[1], reverse=True)
    return [
        {
            "disease_key": key,
            "name_vi": catalog.get_disease(key).get("name_vi", key),
            "probability": float(prob),
        }
        for key, prob in ordered[:limit]
    ]
