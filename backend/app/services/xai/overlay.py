"""Vẽ vùng khoanh XAI lên ảnh — thứ nông dân thực sự nhìn thấy.

Cố ý KHÔNG phủ bản đồ nhiệt màu cầu vồng lên ảnh. Heatmap kiểu đó hợp cho báo
cáo kỹ thuật (xem ``model/src/xai/visualize.py``) nhưng với người dùng cuối thì
rối và che mất chính vết bệnh họ cần nhìn. Thay vào đó khoanh theo ĐÚNG hình
dạng vùng nghi ngờ (đường viền bám sát contour, có tô nhẹ bên trong) — đủ để
chỉ chỗ chính xác, vẫn thấy rõ lá bên dưới.

⚠️ Trước 18/09/2026 bản cũ vẽ elip khớp (``cv2.fitEllipse``) quanh contour thay
vì contour thật. Elip trông "sạch" hơn nhưng luôn sai lệch với hình vết bệnh
thật — vết bệnh hiếm khi tròn/oval đều, elip khớp quanh một vết bệnh hình chữ
L hay dải dài sẽ bao trùm cả những vùng lá lành nằm giữa các "cánh tay" của vết
bệnh đó. Đổi sang vẽ contour thật (làm mượt biên trước để không bị lởm chởm
theo lưới pixel của CAM gốc 7×7 phóng to) là lựa chọn đúng tinh thần XAI của đề
tài hơn: khoanh cái mô hình THẬT SỰ nhìn vào, không phải một hình học gần đúng.
"""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image

from app.core.config import settings
from app.services.xai.explain import MIN_REGION_RATIO

# Màu đường viền (RGB) — cam đỏ, nổi bật trên nền lá xanh và vết bệnh nâu
OUTLINE_COLOR = (255, 64, 32)
# Tô nhẹ bên trong vùng khoanh cùng màu viền, để mắt bắt vùng nghi ngờ nhanh
# hơn mà vẫn nhìn xuyên qua được vết bệnh/gân lá bên dưới (không phải overlay
# đặc như heatmap cầu vồng — chỉ một lớp màu phẳng, mờ)
FILL_ALPHA = 0.22
# Chỉ vẽ tối đa ngần này vùng, tránh ảnh rối như tổ ong
MAX_REGIONS = 3
# Tỉ lệ đơn giản hoá contour theo chu vi (cv2.approxPolyDP) — đủ để bỏ răng cưa
# li ti mà không làm tròn mất hình dạng thật của vết bệnh
_APPROX_EPSILON_RATIO = 0.006


def _smoothed_regions(mask: np.ndarray, width: int, height: int) -> list[np.ndarray]:
    """Tìm và làm mượt contour các vùng đủ lớn trong mặt nạ nhị phân."""
    # Heatmap gốc chỉ 7×7 (kiến trúc CAM cổ điển — xem CLAUDE.md mục nhận diện
    # ngoại tuyến) rồi phóng to nội suy tuyến tính, nên biên mặt nạ trước khi
    # làm mượt là các bậc thang vuông góc theo lưới pixel, không theo hình vết
    # bệnh thật. Gaussian blur + ngưỡng lại một lần nữa cho ra biên cong tự
    # nhiên trước khi trích contour.
    blur_ksize = max(3, round(min(width, height) / 60))
    if blur_ksize % 2 == 0:
        blur_ksize += 1
    blurred = cv2.GaussianBlur(mask, (blur_ksize, blur_ksize), 0)
    _, blurred = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(blurred, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area = MIN_REGION_RATIO * width * height
    contours = sorted(
        (c for c in contours if cv2.contourArea(c) >= min_area),
        key=cv2.contourArea, reverse=True,
    )[:MAX_REGIONS]

    regions = []
    for contour in contours:
        epsilon = _APPROX_EPSILON_RATIO * cv2.arcLength(contour, True)
        smoothed = cv2.approxPolyDP(contour, epsilon, True)
        # approxPolyDP quá mạnh tay có thể suy biến về dưới 3 điểm (không còn
        # là một vùng khép kín) — thà giữ contour gốc còn hơn mất cả vùng
        regions.append(smoothed if len(smoothed) >= 3 else contour)
    return regions


def draw_regions(image: Image.Image, heatmap: np.ndarray,
                 threshold: float | None = None) -> Image.Image:
    """Khoanh các vùng có ảnh hưởng lớn nhất tới quyết định của mô hình, bám
    sát đúng hình dạng vùng đó thay vì gần đúng bằng elip.

    Args:
        image: ảnh gốc.
        heatmap: mảng (H, W) trong khoảng 0..1, cùng kích thước ảnh gốc.
        threshold: ngưỡng cắt, mặc định lấy từ cấu hình.

    Returns:
        Ảnh mới đã vẽ; ảnh gốc không bị thay đổi.
    """
    thr = settings.OVERLAY_DRAW_THRESHOLD if threshold is None else threshold

    rgb = np.array(image.convert("RGB"))
    height, width = rgb.shape[:2]

    # Heatmap có thể lệch kích thước nếu ảnh bị thu nhỏ sau khi suy luận
    if heatmap.shape != (height, width):
        heatmap = cv2.resize(heatmap.astype(np.float32), (width, height),
                             interpolation=cv2.INTER_LINEAR)

    mask = (heatmap >= thr).astype(np.uint8) * 255

    # Bỏ đốm nhiễu li ti rồi hàn các mảnh gần nhau thành một vùng, trước khi
    # làm mượt biên ở `_smoothed_regions`. Kernel PHẢI tỉ lệ theo kích thước
    # ảnh — 5×5 cố định trên ảnh tới 1280px (MAX_IMAGE_DIMENSION) gần như
    # không làm gì (chưa tới 0.4% chiều rộng ảnh).
    k = max(5, round(min(width, height) / 100))
    if k % 2 == 0:
        k += 1
    kernel = np.ones((k, k), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    regions = _smoothed_regions(mask, width, height)
    if not regions:
        return Image.fromarray(rgb)

    thickness = max(2, round(min(width, height) / 220))

    # Tô nhẹ trước (trên một lớp riêng rồi trộn alpha) để không đè cả một lớp
    # đặc màu lên biên — biên vẫn phải vẽ SAU, nét và đúng màu gốc
    fill = rgb.copy()
    cv2.drawContours(fill, regions, -1, OUTLINE_COLOR, thickness=cv2.FILLED,
                     lineType=cv2.LINE_AA)
    rgb = cv2.addWeighted(fill, FILL_ALPHA, rgb, 1 - FILL_ALPHA, 0)

    cv2.drawContours(rgb, regions, -1, OUTLINE_COLOR, thickness, lineType=cv2.LINE_AA)

    return Image.fromarray(rgb)


def has_visible_region(heatmap: np.ndarray, threshold: float | None = None) -> bool:
    """Kiểm tra có vùng nào đủ lớn để vẽ không — dùng để quyết định có lưu ảnh overlay."""
    thr = settings.OVERLAY_DRAW_THRESHOLD if threshold is None else threshold
    return float((heatmap >= thr).mean()) >= MIN_REGION_RATIO
