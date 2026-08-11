"""Biến bản đồ nhiệt Grad-CAM thành thứ nông dân hiểu được.

Đây là đóng góp chính của đề tài. Heatmap thô là một mảng số — đưa thẳng cho
nông dân xem thì vô nghĩa. Ở đây ta rút từ nó ra ba thứ cụ thể:

  1. **Mức độ nặng**  — dựa trên tỉ lệ diện tích lá bị mô hình đánh dấu.
  2. **Vị trí**       — vết bệnh nằm ở đâu trên lá, mô tả bằng lời.
  3. **Câu giải thích** — một câu tiếng Việt thường ngày, không có thuật ngữ.

Cần nói rõ giới hạn khi viết báo cáo: Grad-CAM chỉ ra vùng ảnh **ảnh hưởng
nhiều nhất tới quyết định của mô hình**, không phải vùng bệnh được bác sĩ cây
trồng khoanh. Hai thứ này thường trùng nhau nhưng không đồng nhất về mặt khái
niệm, và tỉ lệ diện tích ở đây là ước lượng gián tiếp cho mức độ nặng.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.core.config import settings
from app.services.catalog import get_disease, severity_levels

# Vùng nhỏ hơn ngưỡng này coi như nhiễu, không đáng nhắc tới
MIN_REGION_RATIO = 0.005


@dataclass
class Explanation:
    severity: str
    severity_name: str
    affected_ratio: float
    region: str
    text: str


def mask_from_heatmap(heatmap: np.ndarray, threshold: float | None = None) -> np.ndarray:
    """Cắt heatmap thành mặt nạ nhị phân theo ngưỡng."""
    thr = settings.HEATMAP_THRESHOLD if threshold is None else threshold
    return heatmap >= thr


def affected_ratio(mask: np.ndarray) -> float:
    """Tỉ lệ diện tích ảnh bị đánh dấu, 0..1."""
    return float(mask.mean()) if mask.size else 0.0


def severity_for(ratio: float, is_healthy: bool) -> tuple[str, str]:
    """Quy tỉ lệ diện tích thành mức độ nặng theo bảng trong danh mục bệnh."""
    levels = severity_levels()

    if is_healthy:
        none_level = next((s for s in levels if s["key"] == "none"), levels[0])
        return none_level["key"], none_level["name_vi"]

    for level in levels:
        if level["key"] == "none":
            continue
        if ratio <= level["max_area_ratio"]:
            return level["key"], level["name_vi"]

    last = levels[-1]
    return last["key"], last["name_vi"]


def describe_region(mask: np.ndarray) -> str:
    """Mô tả vị trí trọng tâm vùng nghi ngờ bằng lời."""
    ys, xs = np.nonzero(mask)
    if ys.size == 0:
        return "toàn bộ phiến lá"

    height, width = mask.shape
    cy = ys.mean() / height
    cx = xs.mean() / width

    if cy < 0.34:
        vertical = "phía trên"
    elif cy > 0.66:
        vertical = "phía dưới"
    else:
        vertical = "phần giữa"

    if cx < 0.34:
        horizontal = "bên trái"
    elif cx > 0.66:
        horizontal = "bên phải"
    else:
        horizontal = ""

    # Vùng trải rộng gần hết ảnh thì mô tả theo vị trí sẽ gây hiểu nhầm
    if affected_ratio(mask) > 0.45:
        return "phần lớn diện tích lá"

    return f"{vertical} {horizontal}".strip() + " của lá"


def interpret(disease_key: str, confidence: float,
              heatmap: np.ndarray | None) -> Explanation:
    """Gộp tất cả lại thành phần giải thích hiển thị cho người dùng."""
    disease = get_disease(disease_key)
    is_healthy = bool(disease.get("is_healthy"))
    name_vi = disease.get("name_vi", disease_key)

    if heatmap is None:
        ratio, region = 0.0, "toàn bộ phiến lá"
    else:
        mask = mask_from_heatmap(heatmap)
        ratio = affected_ratio(mask)
        region = describe_region(mask)

    severity, severity_name = severity_for(ratio, is_healthy)

    if is_healthy:
        text = (
            f"Hệ thống không tìm thấy dấu hiệu bệnh nào rõ rệt trên lá "
            f"(độ tin cậy {confidence:.0%}). Lá có màu đều, không có đốm hay biến dạng."
        )
    elif ratio < MIN_REGION_RATIO:
        text = (
            f"Hệ thống nghiêng về {name_vi} với độ tin cậy {confidence:.0%}, "
            f"nhưng không khoanh được vùng nào đủ rõ trên ảnh. "
            f"Nên chụp lại gần hơn, đủ sáng và lấy nét vào phần lá nghi ngờ."
        )
    else:
        cue = disease.get("visual_cue") or "dấu hiệu bất thường"
        text = (
            f"Hệ thống tập trung vào {region} — nơi xuất hiện {cue}. "
            f"Đây là dấu hiệu đặc trưng của {name_vi} "
            f"(độ tin cậy {confidence:.0%}, vùng nghi ngờ chiếm khoảng "
            f"{ratio:.0%} diện tích ảnh)."
        )

    return Explanation(
        severity=severity,
        severity_name=severity_name,
        affected_ratio=ratio,
        region=region,
        text=text,
    )
