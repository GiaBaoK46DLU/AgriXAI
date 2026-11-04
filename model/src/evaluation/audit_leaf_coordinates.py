"""Ảnh QA #93: khung cắt, đầu vào mô hình và CAM đặt lại trên ảnh gốc."""

import argparse
import json
from pathlib import Path

import cv2
import torch
import yaml
from PIL import Image

from src.data.leaf_crop import locate_leaf
from src.predictor import DiseasePredictor
from src.training.adapt_domain import write_json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    root = Path(args.run)
    rows = json.loads((root / "validation-rows.json").read_text(encoding="utf-8"))
    out = root / "coordinate-audit"
    out.mkdir(exist_ok=False)
    config = {"preprocess": {"leaf_crop": {"enabled": True}}, "xai": {"method": "gradcam_plusplus"}}
    config_path = out / "config.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    torch.set_num_threads(4)
    predictor = DiseasePredictor(
        "checkpoints/leaf_disease_detection_model.pt", device="cpu", xai_config_path=config_path
    )
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    records = []
    for source in ("pv", "pd"):
        n = 0
        for row in rows[source]:
            with Image.open(row["path"]) as opened:
                image = opened.convert("RGB")
            region = locate_leaf(image)
            x0, y0, x1, y1 = region.box
            if region.mask is None or (x1 - x0) * (y1 - y0) / (image.width * image.height) > 0.90:
                continue
            result = predictor.predict(image)
            heat = result.heatmap
            assert heat.shape == (image.height, image.width)
            outside = heat.copy()
            outside[y0:y1, x0:x1] = 0
            assert not outside.any()
            n += 1
            figure, axes = plt.subplots(1, 3, figsize=(11, 4))
            display = image.copy()
            display.thumbnail((640, 640))
            sx, sy = display.width / image.width, display.height / image.height
            axes[0].imshow(display)
            axes[0].add_patch(
                Rectangle(
                    (x0 * sx, y0 * sy),
                    (x1 - x0) * sx,
                    (y1 - y0) * sy,
                    edgecolor="red",
                    fill=False,
                    linewidth=2,
                )
            )
            axes[0].set_title("Ảnh gốc và khung cắt")
            axes[1].imshow(image.crop(region.box))
            axes[1].set_title("Vùng lá đưa vào phân loại")
            axes[2].imshow(display)
            axes[2].imshow(cv2.resize(heat, display.size), cmap="jet", alpha=0.45, vmin=0, vmax=1)
            axes[2].set_title("CAM ánh xạ về đúng khung gốc")
            for ax in axes:
                ax.axis("off")
            figure.tight_layout()
            filename = f"{source}-{n:02}.png"
            figure.savefig(out / filename, dpi=110, bbox_inches="tight")
            plt.close(figure)
            records.append(
                {
                    **row,
                    "box": region.box,
                    "image_size": image.size,
                    "heatmap_shape": heat.shape,
                    "outside_crop_mass": float(outside.sum()),
                    "figure": filename,
                }
            )
            if n == 6:
                break
        assert n == 6, (source, n)
    predictor.close()
    write_json(out / "records.json", records)
    print("Đã tạo 12 ảnh QA có cắt thật, CAM không tràn ngoài khung cắt")


if __name__ == "__main__":
    main()
