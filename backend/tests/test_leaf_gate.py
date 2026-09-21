"""Kiểm thử #47 — nối bộ chặn lá cà chua / không phải lá (#92) vào backend.

Không cần torch hay checkpoint thật: giả một predictor trả về
``disease_key="not_tomato_leaf"`` giống hệt hình dạng mà ``DiseasePredictor``
thật trả về khi gate của #92 từ chối ảnh — cùng kiểu với cách ``DummyPredictor``
cho phép kiểm cả luồng mà không cần mô hình thật.
"""

from __future__ import annotations

import io

import numpy as np
from PIL import Image

from app.core.config import settings
from app.services import diagnosis_service
from app.services.catalog import NOT_TOMATO_LEAF_MESSAGE, get_disease
from app.services.inference.base import NOT_TOMATO_LEAF_KEY, Prediction

API = settings.API_V1_PREFIX


class _GateRejectAllPredictor:
    """Giả bộ chặn luôn từ chối — mọi ảnh đều 'not_tomato_leaf'."""

    model_version = "fake-gate-reject-all"

    def predict(self, image: Image.Image, with_heatmap: bool = True) -> Prediction:
        return Prediction(
            disease_key=NOT_TOMATO_LEAF_KEY,
            confidence=0.97,
            probabilities={},
            heatmap=None,
            model_version=self.model_version,
            latency_ms=1.0,
        )


class _GateMixedPredictor:
    """Giả bộ chặn phân biệt theo màu chủ đạo của ảnh: xanh lá (giống fixture
    ``leaf_image``) coi là lá thật, còn lại bị chặn — đủ để kiểm một lô ảnh
    hỗn hợp mà không cần đoán mò kết quả của mô hình thật."""

    model_version = "fake-gate-mixed"

    def predict(self, image: Image.Image, with_heatmap: bool = True) -> Prediction:
        rgb = np.array(image.convert("RGB")).astype(np.float32)
        mean = rgb.reshape(-1, 3).mean(axis=0)
        is_leaf = mean[1] > mean[0] and mean[1] > mean[2]

        if not is_leaf:
            return Prediction(
                disease_key=NOT_TOMATO_LEAF_KEY,
                confidence=0.9,
                probabilities={},
                heatmap=None,
                model_version=self.model_version,
                latency_ms=1.0,
            )

        width, height = image.size
        heatmap = np.zeros((height, width), dtype=np.float32)
        heatmap[height // 3: 2 * height // 3, width // 3: 2 * width // 3] = 1.0
        return Prediction(
            disease_key="early_blight",
            confidence=0.88,
            probabilities={"early_blight": 0.88, "healthy": 0.12},
            heatmap=heatmap,
            model_version=self.model_version,
            latency_ms=1.0,
        )


def _jpeg_bytes(color: tuple[int, int, int]) -> bytes:
    image = Image.new("RGB", (400, 400), color)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def _non_leaf_image() -> bytes:
    return _jpeg_bytes((200, 60, 40))  # đỏ gạch — không giống lá


def _files(image: bytes, count: int = 3) -> list[tuple[str, tuple[str, bytes, str]]]:
    return [("files", (f"vat{i}.jpg", image, "image/jpeg")) for i in range(count)]


# ── catalog: không được lộ khoá thô ra tên hiển thị ──

def test_catalog_hides_raw_key_for_not_tomato_leaf():
    info = get_disease(NOT_TOMATO_LEAF_KEY)
    assert info["name_vi"] == NOT_TOMATO_LEAF_MESSAGE
    assert "not_tomato_leaf" not in info["name_vi"]


# ── cả lô đều bị chặn: báo lỗi rõ ràng, không lưu gì ──

def test_diagnose_rejects_when_gate_blocks_everything(
    client, farmer_headers, seeded, leaf_image, monkeypatch,
):
    monkeypatch.setattr(diagnosis_service, "get_predictor", lambda: _GateRejectAllPredictor())

    response = client.post(
        f"{API}/diagnoses",
        headers=farmer_headers,
        files=_files(leaf_image),
        data={"plot_id": str(seeded["plot_id"])},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == NOT_TOMATO_LEAF_MESSAGE
    assert "not_tomato_leaf" not in response.text


def test_diagnose_does_not_persist_when_gate_blocks_everything(
    client, farmer_headers, seeded, leaf_image, monkeypatch,
):
    monkeypatch.setattr(diagnosis_service, "get_predictor", lambda: _GateRejectAllPredictor())
    before = client.get(f"{API}/diagnoses", headers=farmer_headers).json()["total"]

    client.post(
        f"{API}/diagnoses",
        headers=farmer_headers,
        files=_files(leaf_image),
        data={"plot_id": str(seeded["plot_id"])},
    )

    after = client.get(f"{API}/diagnoses", headers=farmer_headers).json()["total"]
    assert after == before, "Lô ảnh bị chặn toàn bộ thì không được tạo bản ghi Diagnosis nào"


# ── lô hỗn hợp: ảnh bị chặn không được pha loãng kết quả của ảnh lá thật ──

def test_diagnose_mixed_batch_ignores_blocked_images(
    client, farmer_headers, seeded, leaf_image, monkeypatch,
):
    monkeypatch.setattr(diagnosis_service, "get_predictor", lambda: _GateMixedPredictor())

    response = client.post(
        f"{API}/diagnoses",
        headers=farmer_headers,
        files=[
            ("files", ("la1.jpg", leaf_image, "image/jpeg")),
            ("files", ("la2.jpg", leaf_image, "image/jpeg")),
            ("files", ("vat.jpg", _non_leaf_image(), "image/jpeg")),
        ],
        data={"plot_id": str(seeded["plot_id"])},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["disease_key"] == "early_blight"

    per_image_keys = {img["disease_key"] for img in body["images"]}
    assert per_image_keys == {"early_blight", NOT_TOMATO_LEAF_KEY}

    blocked = next(img for img in body["images"] if img["disease_key"] == NOT_TOMATO_LEAF_KEY)
    assert blocked["disease_name"] == NOT_TOMATO_LEAF_MESSAGE
