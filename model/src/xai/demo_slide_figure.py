"""Hình demo nhận diện + bản đồ nhiệt, bố cục dành cho slide.

Khác ``visualize.py`` (lưới 4 cột, chỉ vẽ bản đồ nhiệt) và khác bản
``figures/demo-nhan-dien.png`` cũ ở một điểm quan trọng: **nhãn kết luận đặt
phía trên ảnh chứ không in đè lên ảnh**. Bản cũ in chữ xanh lên mép dưới phiến
lá, chiếu lên màn hình thì gần như không đọc được.

Mỗi cột là một lớp bệnh: hàng trên ảnh gốc, hàng dưới cùng ảnh đó phủ bản đồ
nhiệt Grad-CAM. Ảnh lấy từ tập test nên mô hình chưa từng thấy.

    cd model
    python -m src.xai.demo_slide_figure
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib
import numpy as np
from PIL import Image

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src.labels import key_to_name_vi  # noqa: E402
from src.predictor import DiseasePredictor  # noqa: E402
from src.utils.common import ensure_dir  # noqa: E402

# Sáu lớp chọn tay cho slide: hai virus, hai bệnh đốm, một bệnh mốc, một lá
# khoẻ — đủ trải các kiểu triệu chứng khác nhau để hội đồng thấy được sự đa dạng.
CLASSES = [
    "spider_mites",
    "yellow_leaf_curl_virus",
    "healthy",
    "target_spot",
    "leaf_mold",
    "bacterial_spot",
]
OK, BAD = "#1B7A3D", "#B03A2E"


def overlay(image: Image.Image, heatmap: np.ndarray, alpha: float = 0.45) -> np.ndarray:
    base = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
    colored = plt.get_cmap("jet")(np.clip(heatmap, 0, 1))[..., :3]
    return np.clip(base * (1 - alpha) + colored * alpha, 0, 1)


def main() -> None:
    ap = argparse.ArgumentParser(description="Hình demo nhận diện cho slide")
    ap.add_argument("--checkpoint", default="checkpoints/leaf_disease_detection_model.pt")
    ap.add_argument("--manifest", default="data/processed/split.csv")
    ap.add_argument("--out", default="outputs/figures/demo-nhan-dien-slide.png")
    args = ap.parse_args()

    with open(args.manifest, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["split"] == "test"]

    # Lấy ảnh đầu tiên của mỗi lớp — cố định, không ngẫu nhiên, để chạy lại là
    # ra đúng hình cũ (slide đã in ra rồi thì hình không được đổi).
    chosen = []
    for key in CLASSES:
        match = next((r for r in rows if r["label"] == key), None)
        if match is None:
            raise SystemExit(f"Tập test không có lớp '{key}'")
        chosen.append(match)

    predictor = DiseasePredictor(args.checkpoint)
    names_vi = key_to_name_vi()

    n = len(chosen)
    fig, axes = plt.subplots(2, n, figsize=(n * 2.5, 6.0))
    for col, row in enumerate(chosen):
        image = Image.open(row["path"]).convert("RGB")
        result = predictor.predict(image)
        correct = result.disease_key == row["label"]

        top, bottom = axes[0][col], axes[1][col]
        top.imshow(image)
        top.set_title(names_vi.get(row["label"], row["label"]),
                      fontsize=10, color="#222222", pad=6)
        bottom.imshow(overlay(image, result.heatmap))
        bottom.set_title(
            f"{names_vi.get(result.disease_key, result.disease_key)}\n"
            f"{result.confidence:.1%}".replace(".", ","),
            fontsize=10, color=OK if correct else BAD, fontweight="bold", pad=6)
        for ax in (top, bottom):
            ax.axis("off")

    # Nhãn hai hàng đặt ngoài lề trái, không đè lên ảnh.
    fig.text(0.008, 0.74, "Ảnh vào", rotation=90, va="center", fontsize=10, color="#555555")
    fig.text(0.008, 0.26, "Grad-CAM", rotation=90, va="center", fontsize=10, color="#555555")

    fig.tight_layout(rect=(0.02, 0, 1, 1))
    out = Path(args.out)
    ensure_dir(out.parent)
    fig.savefig(out, dpi=150, facecolor="white")
    plt.close(fig)
    predictor.close()
    print(f"Đã ghi {out}")


if __name__ == "__main__":
    main()
