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

Kết quả cuối cùng của cả lô ảnh tổng hợp bằng cách **bỏ phiếu theo đa số**
trên nhãn top-1 của từng ảnh — bệnh nào được nhiều ảnh dự đoán nhất thắng.
Độ tin cậy hiển thị là **trung bình cộng** xác suất của lớp thắng cuộc qua
tất cả các ảnh (kể cả những ảnh không tự chọn lớp đó là top-1), không phải
độ tin cậy riêng của một ảnh nào.
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass

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


def _majority_key(results: list[_ImageResult]) -> str:
    """Bệnh được nhiều ảnh tự chọn làm top-1 nhất thắng.

    Hoà phiếu (nhiều bệnh cùng số phiếu cao nhất) thì chọn bệnh có tổng xác
    suất qua các ảnh cao hơn — vẫn nhất quán với tinh thần "trung bình cộng".
    """
    counts = Counter(r.prediction.disease_key for r in results)
    top_count = max(counts.values())
    tied = [key for key, count in counts.items() if count == top_count]
    if len(tied) == 1:
        return tied[0]
    return max(
        tied,
        key=lambda key: sum(r.prediction.probabilities.get(key, 0.0) for r in results),
    )


def _average_probabilities(results: list[_ImageResult]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for result in results:
        for key, prob in (result.prediction.probabilities or {}).items():
            totals[key] = totals.get(key, 0.0) + prob
    n = len(results)
    return {key: total / n for key, total in totals.items()}


def run_diagnosis(db: Session, *, user_id: int, plot_id: int | None,
                  images: list[bytes], note: str | None = None) -> Diagnosis:
    """Chạy toàn bộ luồng chẩn đoán cho một lô ảnh và ghi kết quả vào CSDL.

    Raises:
        storage.InvalidImageError: một trong các ảnh hỏng hoặc sai định dạng.
    """
    if not images:
        raise ValueError("images không được rỗng")

    results = [_run_single_image(raw) for raw in images]

    majority_key = _majority_key(results)
    avg_probabilities = _average_probabilities(results)
    avg_confidence = avg_probabilities.get(majority_key, 0.0)

    # Ảnh đại diện cho phần XAI (giải thích/mức độ/ảnh overlay chính): trong
    # số các ảnh mà mô hình tự chọn đúng bệnh thắng cuộc, lấy ảnh có độ tin
    # cậy riêng cao nhất — luôn tồn tại ít nhất một ảnh như vậy vì đó chính là
    # cách `majority_key` được tính.
    representative = max(
        (r for r in results if r.prediction.disease_key == majority_key),
        key=lambda r: r.prediction.confidence,
    )

    disease = catalog.get_disease(majority_key)
    rep_interp = representative.interpretation

    record = Diagnosis(
        user_id=user_id,
        plot_id=plot_id,
        image_path=representative.image_path,
        overlay_path=representative.overlay_path,
        disease_key=majority_key,
        disease_name=disease.get("name_vi", majority_key),
        confidence=avg_confidence,
        probabilities=avg_probabilities,
        severity=rep_interp.severity,
        severity_name=rep_interp.severity_name,
        affected_ratio=rep_interp.affected_ratio,
        explanation=rep_interp.text,
        model_version=representative.prediction.model_version,
        latency_ms=sum(r.prediction.latency_ms for r in results),
        note=note,
    )
    db.add(record)
    db.flush()  # cần record.id để gán khoá ngoại cho từng ảnh

    for result in results:
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
