"""Chọn và nạp predictor — thật nếu có checkpoint, giả nếu không.

Mô hình được nạp MỘT LẦN lúc ứng dụng khởi động rồi giữ trong bộ nhớ. Nạp lại
cho mỗi request sẽ khiến mỗi lần chẩn đoán mất thêm vài giây.
"""

from __future__ import annotations

import logging
import sys
from functools import lru_cache

from app.core.config import settings
from app.services.inference.base import Predictor
from app.services.inference.dummy import DummyPredictor

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_predictor() -> Predictor:
    """Trả về predictor dùng chung cho toàn ứng dụng.

    Thứ tự ưu tiên:
      1. Có ``MODEL_CHECKPOINT`` trỏ tới file tồn tại và import được PyTorch
         -> ``DiseasePredictor`` thật.
      2. Ngược lại -> ``DummyPredictor``, kèm cảnh báo trong log.

    Mọi lỗi khi nạp mô hình thật đều được nuốt và rơi về dummy: thà hệ thống
    chạy với kết quả giả còn hơn sập hoàn toàn giữa lúc đang demo.
    """
    checkpoint = settings.checkpoint_path

    if checkpoint is None:
        logger.warning(
            "MODEL_CHECKPOINT chưa được cấu hình — dùng DummyPredictor. "
            "Kết quả chẩn đoán là GIẢ, chỉ dùng để phát triển giao diện."
        )
        return DummyPredictor()

    if not checkpoint.exists():
        logger.error(
            "Không tìm thấy checkpoint '%s' — rơi về DummyPredictor.", checkpoint
        )
        return DummyPredictor()

    try:
        # Thư mục model/ không phải package cài đặt, thêm vào sys.path để import
        model_dir = str(settings.model_package_path)
        if model_dir not in sys.path:
            sys.path.insert(0, model_dir)

        from src.predictor import DiseasePredictor  # type: ignore[import-not-found]

        # Bộ chặn (#92) là phụ, mô hình bệnh mới là chính — thiếu/lỗi checkpoint
        # bộ chặn không được kéo cả predictor thật rơi về DummyPredictor. Nên
        # kiểm tồn tại ở đây, trước khi vào constructor (nơi lỗi này sẽ bị
        # `except Exception` bên dưới nuốt chung với lỗi của mô hình bệnh).
        gate_checkpoint = settings.gate_checkpoint_path
        if gate_checkpoint is not None and not gate_checkpoint.exists():
            logger.error(
                "Không tìm thấy checkpoint bộ chặn '%s' — bỏ qua #92, "
                "vẫn dùng mô hình bệnh thật bình thường.", gate_checkpoint,
            )
            gate_checkpoint = None

        predictor = DiseasePredictor(
            checkpoint_path=str(checkpoint),
            device=settings.MODEL_DEVICE or None,
            gate_checkpoint=str(gate_checkpoint) if gate_checkpoint else None,
        )
        if gate_checkpoint is not None:
            logger.info(
                "Đã nạp bộ chặn lá/không-phải-lá: %s (phiên bản %s)",
                gate_checkpoint, predictor.gate_version,
            )
        logger.info(
            "Đã nạp mô hình thật: %s (phiên bản %s)", checkpoint, predictor.model_version
        )
        return predictor

    except ImportError as exc:
        logger.error(
            "Không import được mô hình (%s). Nhiều khả năng chưa cài torch/torchvision. "
            "Rơi về DummyPredictor.", exc
        )
    except Exception as exc:  # noqa: BLE001 — cố tình bắt rộng, xem docstring
        logger.exception("Lỗi khi nạp mô hình: %s. Rơi về DummyPredictor.", exc)

    return DummyPredictor()


def is_using_real_model() -> bool:
    """Để endpoint /health báo cho frontend biết kết quả có thật hay không."""
    return not isinstance(get_predictor(), DummyPredictor)
