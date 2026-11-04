"""Tách lá bằng màu, độc lập với mô hình bệnh và bản đồ nhiệt (#93).

Đây là heuristic cho một phiến lá nổi bật, không phải phân vùng vết bệnh.
Khi không có vùng đủ rõ thì giữ toàn ảnh; không ép cắt ảnh nhiều lá/nền màu.
"""

from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image


@dataclass
class LeafRegion:
    box: tuple[int, int, int, int]
    mask: np.ndarray | None
    reason: str

    def restore(self, cam: np.ndarray, size: tuple[int, int]) -> np.ndarray:
        """Đặt CAM của ảnh cắt vào đúng khung ảnh gốc, nền ngoài khung bằng 0."""
        w, h = size
        x0, y0, x1, y1 = self.box
        resized = cv2.resize(
            cam.astype(np.float32), (x1 - x0, y1 - y0), interpolation=cv2.INTER_LINEAR
        )
        restored = np.zeros((h, w), dtype=np.float32)
        restored[y0:y1, x0:x1] = np.clip(resized, 0, 1)
        return restored


def locate_leaf(
    image: Image.Image,
    padding: float = 0.08,
    min_area: float = 0.05,
    max_area: float = 0.90,
    min_dominance: float = 0.65,
) -> LeafRegion:
    """HSV/Otsu + thành phần lớn nhất; giữ phần nâu, lấp lỗ trong phiến lá.

    Thu nhỏ tối đa 512 px để chi phí không tăng theo ảnh camera nhiều MP.
    Mask trả về ở kích thước ảnh gốc. Ngưỡng/margin cố định trước phép đo test.
    """
    w, h = image.size
    full = (0, 0, w, h)
    small = image.convert("RGB").copy()
    small.thumbnail((512, 512))
    rgb = np.asarray(small)
    sat = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)[..., 1]
    threshold, _ = cv2.threshold(sat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    mask = (sat > max(35, min(100, threshold))).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    n, labels, stats, _ = cv2.connectedComponentsWithStats(mask, 8)
    if n <= 1:
        return LeafRegion(full, None, "no_component")
    best = 1 + int(stats[1:, cv2.CC_STAT_AREA].argmax())
    component = (labels == best).astype(np.uint8)
    # Lấp lỗ tối/nâu trong lá để không vô tình loại chính triệu chứng.
    contours, _ = cv2.findContours(component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(component, contours, -1, 1, cv2.FILLED)
    area = float(component.mean())
    dominance = stats[best, cv2.CC_STAT_AREA] / max(1, int(mask.sum()))
    if not min_area <= area <= max_area or dominance < min_dominance:
        return LeafRegion(full, None, "ambiguous_mask")
    x, y, bw, bh = cv2.boundingRect(component)
    sh, sw = component.shape
    dx, dy = padding * bw, padding * bh
    box = (
        max(0, int((x - dx) * w / sw)),
        max(0, int((y - dy) * h / sh)),
        min(w, int(np.ceil((x + bw + dx) * w / sw))),
        min(h, int(np.ceil((y + bh + dy) * h / sh))),
    )
    original_mask = cv2.resize(component, (w, h), interpolation=cv2.INTER_NEAREST).astype(bool)
    return LeafRegion(box, original_mask, "localized")


class CropLeaf:
    """Transform xác định, dùng cùng thuật toán cho huấn luyện và suy luận."""

    def __init__(self, **options):
        self.options = options

    def __call__(self, image):
        return image.crop(locate_leaf(image, **self.options).box)
