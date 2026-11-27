"""Kiểm thử phần tổng hợp kết quả của một lô ảnh.

Bệnh chung được chọn theo trung bình xác suất, nên ảnh đại diện có thể tự chọn
một bệnh khác. Câu giải thích, mức độ nặng và vùng khoanh chính của lô ảnh phải
luôn nói về đúng bệnh chung.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from app.core.config import settings
from app.services import diagnosis_service
from app.services.catalog import get_disease
from app.services.inference.base import Prediction

API = settings.API_V1_PREFIX


class _QueuedPredictor:
    """Trả lần lượt các kết quả định sẵn, theo đúng thứ tự ảnh được tải lên."""

    model_version = "fake-queued"

    def __init__(self, outputs: list[dict[str, float]]) -> None:
        self._outputs = list(outputs)

    def predict(self, image: Image.Image, with_heatmap: bool = True) -> Prediction:
        probabilities = self._outputs.pop(0)
        key = max(probabilities, key=probabilities.get)
        width, height = image.size
        heatmap = np.zeros((height, width), dtype=np.float32)
        heatmap[height // 3: 2 * height // 3, width // 3: 2 * width // 3] = 1.0
        return Prediction(
            disease_key=key,
            confidence=probabilities[key],
            probabilities=probabilities,
            heatmap=heatmap,
            model_version=self.model_version,
            latency_ms=1.0,
        )


def _post(client, headers, plot_id, leaf_image, *, save: bool):
    return client.post(
        f"{API}/diagnoses",
        headers=headers,
        files=[("files", (f"la{i}.jpg", leaf_image, "image/jpeg")) for i in range(3)],
        data={"plot_id": str(plot_id), "save": "true" if save else "false"},
    )


def _name(key: str) -> str:
    return get_disease(key)["name_vi"]


def test_representative_prefers_image_that_picked_the_winner(
    client, farmer_headers, seeded, leaf_image, monkeypatch,
):
    # Ảnh 2 có xác suất đốm vòng cao nhất (0,45) nhưng tự chọn mốc sương muộn.
    outputs = [
        {"early_blight": 0.40, "septoria_leaf_spot": 0.30, "healthy": 0.30},
        {"early_blight": 0.45, "late_blight": 0.55},
        {"early_blight": 0.42, "late_blight": 0.30, "healthy": 0.28},
    ]
    predictor = _QueuedPredictor(outputs)
    monkeypatch.setattr(diagnosis_service, "get_predictor", lambda: predictor)

    response = _post(client, farmer_headers, seeded["plot_id"], leaf_image, save=True)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["disease_key"] == "early_blight"
    assert _name("early_blight") in body["explanation"]
    assert _name("late_blight") not in body["explanation"]
    # Câu giải thích phải dùng độ tin cậy chung (trung bình), không phải của một ảnh
    assert f"{body['confidence']:.0%}" in body["explanation"]
    # Ảnh đại diện là ảnh 3: cùng chọn đốm vòng với xác suất cao nhất (0,42)
    representative = body["images"][2]
    assert body["image_url"] == representative["image_url"]
    assert body["overlay_url"] == representative["overlay_url"]
    assert body["overlay_url"] is not None


def test_no_overlay_or_region_when_no_image_picked_the_winner(
    client, farmer_headers, seeded, leaf_image, monkeypatch,
):
    # Đốm vòng đứng đầu theo trung bình nhưng không ảnh nào chọn nó làm top-1.
    outputs = [
        {"early_blight": 0.45, "late_blight": 0.55},
        {"early_blight": 0.40, "septoria_leaf_spot": 0.60},
        {"early_blight": 0.44, "healthy": 0.56},
    ]
    for save in (True, False):  # cả luồng có lưu lẫn luồng xem tạm
        predictor = _QueuedPredictor(outputs)
        monkeypatch.setattr(diagnosis_service, "get_predictor", lambda: predictor)

        response = _post(client, farmer_headers, seeded["plot_id"], leaf_image, save=save)

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["disease_key"] == "early_blight"
        assert _name("early_blight") in body["explanation"]
        for other in ("late_blight", "septoria_leaf_spot"):
            assert _name(other) not in body["explanation"]
        assert f"{body['confidence']:.0%}" in body["explanation"]
        # Mô hình chỉ trả bản đồ nhiệt cho bệnh mà ảnh tự chọn nên không có
        # vùng nào để khoanh cho bệnh chung
        assert body["overlay_url"] is None
        assert body["affected_ratio"] == 0
