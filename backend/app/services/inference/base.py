"""Hợp đồng giữa backend và phần mô hình.

Backend KHÔNG import trực tiếp PyTorch hay bất cứ thứ gì trong ``model/`` ngoài
lớp predictor. Nhờ vậy backend chạy được ngay cả khi máy chưa cài torch — dùng
``DummyPredictor`` để phát triển giao diện song song với việc huấn luyện.

``Prediction`` ở đây khai báo đúng những trường mà ``model/src/predictor.py``
trả về. Hai bên khớp nhau theo tên thuộc tính (duck typing), không bên nào phải
import bên kia — đúng ranh giới đã thống nhất giữa hai người.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

import numpy as np
from PIL import Image


@dataclass
class Prediction:
    """Kết quả thô từ mô hình, trước khi backend diễn giải thành ngôn ngữ người dùng."""

    disease_key: str
    confidence: float
    probabilities: dict[str, float] = field(default_factory=dict)
    heatmap: np.ndarray | None = None      # (H, W) float 0..1, đúng kích thước ảnh gốc
    model_version: str = "unknown"
    latency_ms: float = 0.0


@runtime_checkable
class Predictor(Protocol):
    """Mọi predictor — thật hay giả — đều phải thoả interface này."""

    model_version: str

    def predict(self, image: Image.Image, with_heatmap: bool = True) -> Prediction:
        ...
