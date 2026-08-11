"""Vẽ vùng khoanh XAI lên ảnh — thứ nông dân thực sự nhìn thấy.

Cố ý KHÔNG phủ bản đồ nhiệt màu cầu vồng lên ảnh. Heatmap kiểu đó hợp cho báo
cáo kỹ thuật (xem ``model/src/xai/visualize.py``) nhưng với người dùng cuối thì
rối và che mất chính vết bệnh họ cần nhìn. Thay vào đó vẽ đường viền elip quanh
vùng nghi ngờ — đủ để chỉ chỗ, vẫn thấy rõ lá bên dưới.
"""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image

from app.core.config import settings
from app.services.xai.explain import MIN_REGION_RATIO

# Màu đường viền (RGB) — cam đỏ, nổi bật trên nền lá xanh và vết bệnh nâu
OUTLINE_COLOR = (255, 64, 32)
# Chỉ vẽ tối đa ngần này vùng, tránh ảnh rối như tổ ong
MAX_REGIONS = 3


def draw_regions(image: Image.Image, heatmap: np.ndarray,
                 threshold: float | None = None) -> Image.Image:
    """Khoanh các vùng có ảnh hưởng lớn nhất tới quyết định của mô hình.

    Args:
        image: ảnh gốc.
        heatmap: mảng (H, W) trong khoảng 0..1, cùng kích thước ảnh gốc.
        threshold: ngưỡng cắt, mặc định lấy từ cấu hình.

    Returns:
        Ảnh mới đã vẽ; ảnh gốc không bị thay đổi.
    """
    thr = settings.HEATMAP_THRESHOLD if threshold is None else threshold

    rgb = np.array(image.convert("RGB"))
    height, width = rgb.shape[:2]

    # Heatmap có thể lệch kích thước nếu ảnh bị thu nhỏ sau khi suy luận
    if heatmap.shape != (height, width):
        heatmap = cv2.resize(heatmap.astype(np.float32), (width, height),
                             interpolation=cv2.INTER_LINEAR)

    mask = (heatmap >= thr).astype(np.uint8) * 255

    # Làm mượt biên: bỏ đốm nhiễu li ti rồi hàn các mảnh gần nhau thành một vùng
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area = MIN_REGION_RATIO * width * height
    contours = sorted(
        (c for c in contours if cv2.contourArea(c) >= min_area),
        key=cv2.contourArea, reverse=True,
    )[:MAX_REGIONS]

    thickness = max(2, round(min(width, height) / 220))

    for contour in contours:
        if len(contour) >= 5:
            # fitEllipse cần ít nhất 5 điểm; elip trông tự nhiên hơn hình chữ nhật
            cv2.ellipse(rgb, cv2.fitEllipse(contour), OUTLINE_COLOR, thickness)
        else:
            (cx, cy), radius = cv2.minEnclosingCircle(contour)
            cv2.circle(rgb, (int(cx), int(cy)), int(radius), OUTLINE_COLOR, thickness)

    return Image.fromarray(rgb)


def has_visible_region(heatmap: np.ndarray, threshold: float | None = None) -> bool:
    """Kiểm tra có vùng nào đủ lớn để vẽ không — dùng để quyết định có lưu ảnh overlay."""
    thr = settings.HEATMAP_THRESHOLD if threshold is None else threshold
    return float((heatmap >= thr).mean()) >= MIN_REGION_RATIO
