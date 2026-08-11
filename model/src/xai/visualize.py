"""Sinh hình minh hoạ Grad-CAM cho báo cáo và slide bảo vệ.

Khác với phần overlay dành cho nông dân (nằm ở ``backend/app/services/xai/``,
vẽ vùng khoanh đơn giản), file này vẽ bản đồ nhiệt kiểu kỹ thuật — cái mà giảng
viên và hội đồng cần nhìn để đánh giá mô hình có "nhìn" đúng chỗ hay không.

Chạy:
    cd model
    python -m src.xai.visualize --checkpoint checkpoints/best.pt --num 12
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path

import matplotlib
import numpy as np
from PIL import Image

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src.labels import key_to_name_vi  # noqa: E402
from src.predictor import DiseasePredictor  # noqa: E402
from src.utils.common import ensure_dir  # noqa: E402


def overlay_heatmap(image: Image.Image, heatmap: np.ndarray, alpha: float = 0.45) -> np.ndarray:
    """Trộn bản đồ nhiệt (colormap jet) lên ảnh gốc."""
    base = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0
    colored = plt.get_cmap("jet")(np.clip(heatmap, 0, 1))[..., :3]
    return np.clip(base * (1 - alpha) + colored * alpha, 0, 1)


def main() -> None:
    ap = argparse.ArgumentParser(description="Vẽ hình minh hoạ Grad-CAM")
    ap.add_argument("--checkpoint", default="checkpoints/best.pt")
    ap.add_argument("--manifest", default="data/processed/split.csv")
    ap.add_argument("--split", default="test")
    ap.add_argument("--num", type=int, default=12, help="Số ảnh đưa vào hình")
    ap.add_argument("--out", default="outputs/figures/gradcam-samples.png")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    import csv
    with open(args.manifest, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["split"] == args.split]
    if not rows:
        raise SystemExit(f"Manifest không có mẫu nào cho split='{args.split}'")

    random.Random(args.seed).shuffle(rows)
    rows = rows[:args.num]

    predictor = DiseasePredictor(args.checkpoint)
    names_vi = key_to_name_vi()

    cols = 4
    n_rows = (len(rows) + cols - 1) // cols
    fig, axes = plt.subplots(n_rows, cols, figsize=(cols * 3.2, n_rows * 3.6))
    axes = np.atleast_1d(axes).ravel()

    for ax, row in zip(axes, rows):
        image = Image.open(row["path"]).convert("RGB")
        result = predictor.predict(image)

        ax.imshow(overlay_heatmap(image, result.heatmap))
        ax.axis("off")

        correct = result.disease_key == row["label"]
        ax.set_title(
            f"Thật: {names_vi.get(row['label'], row['label'])}\n"
            f"Đoán: {names_vi.get(result.disease_key, result.disease_key)} "
            f"({result.confidence:.0%})",
            fontsize=8, color="green" if correct else "red",
        )

    for ax in axes[len(rows):]:
        ax.axis("off")

    fig.suptitle("Grad-CAM — vùng ảnh ảnh hưởng tới quyết định của mô hình", fontsize=12)
    fig.tight_layout()

    out = Path(args.out)
    ensure_dir(out.parent)
    fig.savefig(out, dpi=150)
    plt.close(fig)
    predictor.close()
    print(f"Đã ghi {out}")


if __name__ == "__main__":
    main()
