"""Sinh hình minh hoạ kết quả bộ chặn #92 — dùng cho báo cáo và slide bảo vệ.

Hai hình:

``demo-anh-khong-phai-la.png``
    Ảnh không phải lá cà chua, đặt cạnh nhau hai cột: mô hình bệnh trả lời gì khi
    **chưa có** bộ chặn, và khi **có** bộ chặn. Cột trái chính là lỗi mà #92 sinh
    ra để chữa — hệ thống tự tin dán nhãn bệnh cho một vật thể bất kỳ.

``demo-anh-la-benh.png``
    Lá bệnh thật kèm vùng khoanh Grad-CAM, gồm cả ảnh PlantVillage lẫn ảnh đồng
    ruộng PlantDoc — để thấy bộ chặn **không** cản trở ca dùng bình thường, kể cả
    với lá bệnh nặng (ca #92 nói dễ hỏng nhất).

Chạy:
    cd model
    .venv/Scripts/python -m src.xai.demo_gate_figures
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

from src.labels import key_to_name_vi  # noqa: E402
from src.predictor import DiseasePredictor  # noqa: E402
from src.utils.common import ensure_dir  # noqa: E402
from src.xai.visualize import overlay_heatmap  # noqa: E402

NOT_LEAF_KEY = "not_tomato_leaf"


def ten_benh(key: str) -> str:
    if key == NOT_LEAF_KEY:
        return "Không phải lá cà chua"
    return key_to_name_vi().get(key, key)


def hinh_anh_am(pred_off: DiseasePredictor, pred_on: DiseasePredictor,
                paths: list[tuple[str, Path]], out: Path) -> None:
    fig, axes = plt.subplots(len(paths), 2, figsize=(8.5, 4.1 * len(paths)))
    for row, (mo_ta, path) in enumerate(paths):
        image = Image.open(path).convert("RGB")
        r_off = pred_off.predict(image, with_heatmap=False)
        r_on = pred_on.predict(image, with_heatmap=False)

        for col, (tieu_de, r) in enumerate(
                [("CHƯA có bộ chặn", r_off), ("CÓ bộ chặn (#92)", r_on)]):
            ax = axes[row, col]
            ax.imshow(image)
            ax.axis("off")
            chan = r.disease_key == NOT_LEAF_KEY
            ax.set_title(
                f"{tieu_de}\n{ten_benh(r.disease_key)} — {r.confidence * 100:.1f}%",
                fontsize=10, color="#1b7a3d" if chan else "#c0392b",
                fontweight="bold", pad=8)
        axes[row, 0].text(-0.06, 0.5, mo_ta, transform=axes[row, 0].transAxes,
                          rotation=90, va="center", ha="center", fontsize=9, color="#444")

    fig.suptitle("Ảnh KHÔNG phải lá cà chua: đỏ = kết luận sai, xanh = chặn đúng",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0.02, 0, 1, 0.97))
    fig.savefig(out, dpi=110)
    plt.close(fig)
    print(f"Ghi {out}")


def hinh_la_benh(pred_on: DiseasePredictor, paths: list[tuple[str, Path]], out: Path) -> None:
    fig, axes = plt.subplots(len(paths), 2, figsize=(8.5, 4.1 * len(paths)))
    for row, (mo_ta, path) in enumerate(paths):
        image = Image.open(path).convert("RGB")
        r = pred_on.predict(image)

        axes[row, 0].imshow(image)
        axes[row, 0].set_title("Ảnh vào", fontsize=10, pad=8)
        axes[row, 0].axis("off")
        axes[row, 0].text(-0.06, 0.5, mo_ta, transform=axes[row, 0].transAxes,
                          rotation=90, va="center", ha="center", fontsize=9, color="#444")

        if r.heatmap is not None:
            axes[row, 1].imshow(overlay_heatmap(image, r.heatmap))
        else:
            axes[row, 1].imshow(image)
        axes[row, 1].set_title(
            f"{ten_benh(r.disease_key)} — {r.confidence * 100:.1f}%",
            fontsize=10, color="#1b7a3d", fontweight="bold", pad=8)
        axes[row, 1].axis("off")

    fig.suptitle("Lá bệnh thật: bộ chặn cho qua, vùng khoanh Grad-CAM vẫn hoạt động",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0.02, 0, 1, 0.97))
    fig.savefig(out, dpi=110)
    plt.close(fig)
    print(f"Ghi {out}")


def doc_manifest(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--checkpoint", default="checkpoints/leaf_disease_detection_model.pt")
    ap.add_argument("--gate", default="checkpoints/organ_gate.pt")
    ap.add_argument("--out-dir", type=Path, default=Path("outputs/gate/demo"))
    args = ap.parse_args()

    out_dir = ensure_dir(args.out_dir)
    pred_off = DiseasePredictor(args.checkpoint)
    pred_on = DiseasePredictor(args.checkpoint, gate_checkpoint=args.gate)

    negatives = doc_manifest(Path("data/negative/manifest.csv"))

    def anh_am(nhom: str, chua: str | None = None) -> Path:
        for r in negatives:
            if r["group"] == nhom and (chua is None or chua in r["path"]):
                return Path(r["path"])
        raise SystemExit(f"Không thấy ảnh nhóm '{nhom}'")

    # Ảnh sân vườn này là ca tệ nhất đo được ở #91: mô hình bệnh kết luận
    # "xoăn vàng lá" với 96,7 % tin cậy dù trong ảnh không có cọng lá cà chua nào.
    hinh_anh_am(pred_off, pred_on, [
        ("sân vườn, hoa vàng", anh_am("soil_ground", "0049_")),
        ("đồ vật trong nhà", anh_am("indoor_objects")),
        ("lá cây KHÁC (họ Cà)", anh_am("other_plant_leaves")),
    ], out_dir / "demo-anh-khong-phai-la.png")

    pv = [r for r in doc_manifest(Path("data/processed/split.csv")) if r["split"] == "test"]
    pd_rows = [r for r in doc_manifest(Path("data/processed/plantdoc-all/split.csv"))
               if "/test/" in r["path"]]

    def anh_benh(rows: list[dict], benh: str) -> Path:
        return Path(next(r["path"] for r in rows if r["label"] == benh))

    hinh_la_benh(pred_on, [
        ("PlantVillage\nmốc sương muộn", anh_benh(pv, "late_blight")),
        ("PlantVillage\nđốm lá vi khuẩn", anh_benh(pv, "bacterial_spot")),
        ("PlantDoc\n(ảnh đồng ruộng thật)", anh_benh(pd_rows, "late_blight")),
    ], out_dir / "demo-anh-la-benh.png")


if __name__ == "__main__":
    main()
