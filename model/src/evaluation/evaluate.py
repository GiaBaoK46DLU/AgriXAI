"""Đánh giá mô hình trên tập test và xuất số liệu cho báo cáo.

Chạy:
    cd model
    python -m src.evaluation.evaluate --checkpoint checkpoints/best.pt
    python -m src.evaluation.evaluate --checkpoint checkpoints/best.pt --split val

Sinh ra trong ``outputs/``:
  - ``confusion-matrix-<split>.png``  ma trận nhầm lẫn
  - ``report-<split>.json``           accuracy tổng thể + precision/recall/f1 từng lớp

Lưu ý khi viết báo cáo: accuracy trên tập test PlantVillage thường rất cao
(>99%) vì ảnh chụp trong phòng, nền đồng nhất. Con số đó KHÔNG phản ánh chất
lượng thực tế. Hãy xếp ảnh tự chụp ngoài đồng vào ``data/field/`` theo đúng cấu
trúc thư mục PlantVillage, sinh manifest riêng bằng
``python -m src.data.prepare --raw-dir data/field --out-dir data/processed/field --test-ratio 1.0 --val-ratio 0.0``
rồi đánh giá trên đó và báo cáo CẢ HAI con số — hội đồng gần như chắc chắn sẽ
hỏi về điểm này.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np
import torch

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    classification_report,
    confusion_matrix,
    top_k_accuracy_score,
)
from torch.utils.data import DataLoader  # noqa: E402
from tqdm import tqdm  # noqa: E402

from src.data.dataset import TomatoLeafDataset, build_infer_transform  # noqa: E402
from src.labels import key_to_name_vi  # noqa: E402
from src.models.build import load_checkpoint  # noqa: E402
from src.utils.common import ensure_dir, get_device  # noqa: E402


def collect_predictions(model, loader, device) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    y_true, y_pred, y_prob = [], [], []
    model.eval()
    with torch.no_grad():
        for images, targets in tqdm(loader, desc="Đánh giá", leave=False):
            probs = torch.softmax(model(images.to(device)), dim=1).cpu().numpy()
            y_prob.append(probs)
            y_pred.append(probs.argmax(1))
            y_true.append(targets.numpy())
    return np.concatenate(y_true), np.concatenate(y_pred), np.concatenate(y_prob)


def plot_confusion_matrix(cm: np.ndarray, labels: list[str], out_path: Path,
                          title: str) -> None:
    # Chuẩn hoá theo hàng để đọc được tỉ lệ nhầm lẫn dù các lớp lệch số lượng
    cm_norm = cm.astype(float) / np.maximum(cm.sum(axis=1, keepdims=True), 1)

    fig, ax = plt.subplots(figsize=(11, 9))
    im = ax.imshow(cm_norm, cmap="Blues", vmin=0, vmax=1)
    fig.colorbar(im, ax=ax, fraction=0.046, label="Tỉ lệ trong lớp thật")

    ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(labels)), labels, fontsize=8)
    ax.set_xlabel("Dự đoán")
    ax.set_ylabel("Thực tế")
    ax.set_title(title)

    for i in range(len(labels)):
        for j in range(len(labels)):
            if cm[i, j]:
                ax.text(j, i, str(cm[i, j]), ha="center", va="center", fontsize=7,
                        color="white" if cm_norm[i, j] > 0.5 else "black")

    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description="Đánh giá mô hình nhận diện bệnh cà chua")
    ap.add_argument("--checkpoint", default="checkpoints/best.pt")
    ap.add_argument("--manifest", default="data/processed/split.csv")
    ap.add_argument("--split", default="test", choices=["train", "val", "test"])
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--num-workers", type=int, default=4)
    ap.add_argument("--out-dir", default="outputs")
    ap.add_argument("--device", default=None)
    args = ap.parse_args()

    device = get_device(args.device)
    model, ckpt = load_checkpoint(args.checkpoint, device)
    keys: list[str] = ckpt["class_keys"]
    names_vi = key_to_name_vi()
    labels_vi = [names_vi.get(k, k) for k in keys]

    ds = TomatoLeafDataset(args.manifest, args.split,
                           build_infer_transform(ckpt.get("image_size", 224)))
    loader = DataLoader(ds, batch_size=args.batch_size, shuffle=False,
                        num_workers=args.num_workers)

    print(f"Checkpoint: {args.checkpoint} (phiên bản {ckpt.get('model_version', '?')})")
    print(f"Tập '{args.split}': {len(ds)} ảnh trên {device}\n")

    y_true, y_pred, y_prob = collect_predictions(model, loader, device)

    accuracy = float((y_true == y_pred).mean())
    top3 = float(top_k_accuracy_score(y_true, y_prob, k=3, labels=list(range(len(keys)))))
    report = classification_report(y_true, y_pred, target_names=keys,
                                   output_dict=True, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(keys))))

    print(classification_report(y_true, y_pred, target_names=keys, zero_division=0))
    print(f"Accuracy      : {accuracy:.4f}")
    print(f"Top-3 accuracy: {top3:.4f}")

    out_dir = ensure_dir(args.out_dir)
    fig_dir = ensure_dir(out_dir / "figures")
    plot_confusion_matrix(cm, labels_vi, fig_dir / f"confusion-matrix-{args.split}.png",
                          f"Ma trận nhầm lẫn — tập {args.split}")

    payload = {
        "checkpoint": str(args.checkpoint),
        "model_version": ckpt.get("model_version"),
        "split": args.split,
        "num_samples": len(ds),
        "accuracy": accuracy,
        "top3_accuracy": top3,
        "macro_f1": report["macro avg"]["f1-score"],
        "per_class": {k: report[k] for k in keys if k in report},
        "confusion_matrix": cm.tolist(),
        "class_keys": keys,
    }
    with open(out_dir / f"report-{args.split}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"\nĐã ghi:\n  {fig_dir / f'confusion-matrix-{args.split}.png'}"
          f"\n  {out_dir / f'report-{args.split}.json'}")

    # Chỉ ra cặp lớp bị nhầm nhiều nhất — rất đáng đưa vào phần phân tích lỗi
    off_diag = cm.copy()
    np.fill_diagonal(off_diag, 0)
    if off_diag.max() > 0:
        i, j = np.unravel_index(off_diag.argmax(), off_diag.shape)
        print(f"\nNhầm nhiều nhất: '{labels_vi[i]}' bị đoán thành "
              f"'{labels_vi[j]}' ({off_diag[i, j]} ảnh)")


if __name__ == "__main__":
    main()
