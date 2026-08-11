"""Predictor giả — cho phép toàn hệ thống chạy khi chưa có mô hình thật.

Đây không phải code tạm bợ mà là một quyết định thiết kế: nhờ nó, backend, app
di động và web admin được xây và kiểm thử đầy đủ ngay từ tháng 8, song song với
việc huấn luyện mô hình. Đến khi có ``best.pt``, chỉ cần trỏ ``MODEL_CHECKPOINT``
trong ``.env`` là hệ thống chuyển sang mô hình thật, không sửa một dòng code nào.

Kết quả sinh ra là ngẫu nhiên nhưng **tất định theo nội dung ảnh**: cùng một ảnh
luôn cho cùng một kết quả. Điều này quan trọng để viết được kiểm thử tự động.
"""

from __future__ import annotations

import hashlib
import time

import numpy as np
from PIL import Image

from app.services.catalog import class_keys
from app.services.inference.base import Prediction


class DummyPredictor:
    """Sinh kết quả giả có hình dạng giống hệt kết quả thật."""

    model_version = "dummy-v1"

    def __init__(self) -> None:
        self.class_keys = class_keys()

    def predict(self, image: Image.Image, with_heatmap: bool = True) -> Prediction:
        started = time.perf_counter()

        image = image.convert("RGB")
        width, height = image.size

        # Seed lấy từ nội dung ảnh -> cùng ảnh cho cùng kết quả
        digest = hashlib.sha256(image.tobytes()).digest()
        rng = np.random.default_rng(int.from_bytes(digest[:8], "big"))

        # Phân phối xác suất có một lớp trội hẳn, giống mô hình thật
        logits = rng.normal(0, 1, len(self.class_keys))
        logits[rng.integers(len(self.class_keys))] += 4.0
        exp = np.exp(logits - logits.max())
        probs = exp / exp.sum()
        idx = int(probs.argmax())

        heatmap = None
        if with_heatmap:
            heatmap = self._blob_heatmap(width, height, rng)

        return Prediction(
            disease_key=self.class_keys[idx],
            confidence=float(probs[idx]),
            probabilities={k: float(p) for k, p in zip(self.class_keys, probs)},
            heatmap=heatmap,
            model_version=self.model_version,
            latency_ms=(time.perf_counter() - started) * 1000,
        )

    @staticmethod
    def _blob_heatmap(width: int, height: int, rng: np.random.Generator) -> np.ndarray:
        """Vài đốm Gauss đặt ngẫu nhiên — đủ để kiểm thử phần vẽ vùng khoanh."""
        yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
        heatmap = np.zeros((height, width), dtype=np.float32)

        for _ in range(int(rng.integers(1, 4))):
            cx = rng.uniform(0.25, 0.75) * width
            cy = rng.uniform(0.25, 0.75) * height
            sigma = rng.uniform(0.08, 0.16) * min(width, height)
            heatmap += np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * sigma ** 2))

        peak = heatmap.max()
        return heatmap / peak if peak > 0 else heatmap
