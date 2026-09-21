"""Kiểm thử vùng khoanh XAI bám đúng hình dạng thật, không phải elip khớp.

Trước 18/09/2026 ``draw_regions`` dùng ``cv2.fitEllipse`` — với một vùng nghi
ngờ không lồi (ví dụ hình chữ L), elip khớp quanh nó sẽ tô cả phần "hốc" nằm
ngoài vùng thật. Bộ test này khoá lại hành vi mới: điểm nằm trong hốc của một
vùng hình chữ L phải KHÔNG bị tô, còn điểm nằm giữa vùng thật phải được tô.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

from app.services.xai import overlay

_BG = (40, 120, 50)


def _l_shaped_heatmap(size: int = 300) -> np.ndarray:
    """Bản đồ nhiệt nhị phân hình chữ L — không lồi, không giống elip/tròn."""
    heatmap = np.zeros((size, size), dtype=np.float32)
    heatmap[50:150, 50:100] = 1.0   # nhánh dọc
    heatmap[120:150, 50:220] = 1.0  # nhánh ngang
    return heatmap


def test_draw_regions_follows_contour_not_ellipse():
    image = Image.new("RGB", (300, 300), _BG)
    heatmap = _l_shaped_heatmap()

    out = np.array(overlay.draw_regions(image, heatmap, threshold=0.5))
    bg = np.array(_BG)

    # Hốc của chữ L (trong bounding box/elip khớp, nhưng ngoài vùng thật)
    assert np.array_equal(out[60, 200], bg), (
        "Hốc ngoài vùng chữ L bị tô — vẫn đang khoanh theo bounding box/elip "
        "thay vì đúng hình contour"
    )
    # Giữa vùng thật phải được tô (viền hoặc lớp tô nhẹ)
    assert not np.array_equal(out[135, 150], bg), "Vùng nghi ngờ thật không được vẽ gì"


def test_draw_regions_returns_original_when_nothing_above_threshold():
    image = Image.new("RGB", (120, 120), _BG)
    heatmap = np.zeros((120, 120), dtype=np.float32)

    out = np.array(overlay.draw_regions(image, heatmap, threshold=0.5))
    assert np.array_equal(out, np.array(image)), "Không có vùng nào vượt ngưỡng thì ảnh phải giữ nguyên"


def test_draw_regions_preserves_size_when_heatmap_is_smaller():
    image = Image.new("RGB", (200, 160), _BG)
    small_heatmap = np.ones((40, 32), dtype=np.float32)  # kích thước khác ảnh gốc

    out = overlay.draw_regions(image, small_heatmap, threshold=0.5)
    assert out.size == image.size
