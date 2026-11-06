"""Chốt hiển thị XAI theo mức tập trung trong lá (#90), không đo độ đúng bệnh."""

import numpy as np


def assess_heatmap(
    heatmap: np.ndarray,
    leaf_mask: np.ndarray | None,
    min_leaf_mass: float = 0.65,
    min_lift: float = 0.05,
) -> dict:
    """Không dùng softmax hay cường độ CAM thô làm bằng chứng định vị.

    Lift = (mass trong lá - tỉ lệ diện tích lá)/(1 - tỉ lệ diện tích lá).
    Mask không rõ hoặc CAM trống thì không đủ bằng chứng để vẽ vùng khoanh.
    Qua chốt chỉ chứng minh CAM tập trung vào *vật thể ước lượng*, không xác
    nhận vết bệnh, độ nặng, hay tính đúng đắn của dự đoán phân loại.
    """
    if leaf_mask is None:
        return {"accepted": False, "reason": "unknown_leaf_mask"}
    if heatmap.shape != leaf_mask.shape:
        raise ValueError("Heatmap và mặt nạ lá phải cùng hệ toạ độ")
    if not np.isfinite(heatmap).all() or heatmap.min() < 0:
        return {"accepted": False, "reason": "invalid_heatmap"}
    total = float(heatmap.sum(dtype=np.float64))
    area = float(leaf_mask.mean())
    if total <= 1e-8 or not 0 < area < 1:
        return {"accepted": False, "reason": "empty_or_uninformative"}
    mass = float(heatmap[leaf_mask].sum(dtype=np.float64) / total)
    lift = (mass - area) / (1 - area)
    accepted = mass >= min_leaf_mass and lift >= min_lift
    return {
        "accepted": bool(accepted),
        "reason": "accepted" if accepted else "outside_leaf",
        "leaf_mass": mass,
        "leaf_area": area,
        "leaf_lift": lift,
    }
