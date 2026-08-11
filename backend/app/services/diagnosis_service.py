"""Điều phối một lần chẩn đoán — nơi mô hình, XAI, lưu trữ và CSDL gặp nhau.

Đây là luồng trung tâm của cả hệ thống:

    bytes ảnh
      -> mở & chuẩn hoá (xoay đúng chiều, thu nhỏ)
      -> predictor.predict()          [mô hình + Grad-CAM]
      -> explain.interpret()          [mức độ, vị trí, câu giải thích]
      -> overlay.draw_regions()       [vẽ vùng khoanh]
      -> lưu 2 ảnh + 1 bản ghi CSDL
"""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.models.diagnosis import Diagnosis
from app.services import catalog
from app.services.inference.loader import get_predictor
from app.services.storage import local as storage
from app.services.xai import explain, overlay

logger = logging.getLogger(__name__)


def run_diagnosis(db: Session, *, user_id: int, plot_id: int | None,
                  image_bytes: bytes, note: str | None = None) -> Diagnosis:
    """Chạy toàn bộ luồng chẩn đoán và ghi kết quả vào CSDL.

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

    disease = catalog.get_disease(prediction.disease_key)

    record = Diagnosis(
        user_id=user_id,
        plot_id=plot_id,
        image_path=image_path,
        overlay_path=overlay_path,
        disease_key=prediction.disease_key,
        disease_name=disease.get("name_vi", prediction.disease_key),
        confidence=prediction.confidence,
        probabilities=prediction.probabilities,
        severity=interpretation.severity,
        severity_name=interpretation.severity_name,
        affected_ratio=interpretation.affected_ratio,
        explanation=interpretation.text,
        model_version=prediction.model_version,
        latency_ms=prediction.latency_ms,
        note=note,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def top_predictions(record: Diagnosis, limit: int = 3) -> list[dict]:
    """Ba lớp có xác suất cao nhất — hiển thị ở màn hình kết quả.

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
