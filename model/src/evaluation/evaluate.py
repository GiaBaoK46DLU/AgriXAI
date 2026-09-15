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
lượng thực tế, nên phải báo cáo CẢ HAI con số — hội đồng gần như chắc chắn sẽ
hỏi về điểm này.

Con số thứ hai đó đến từ bộ **PlantDoc** (issue #49). Sinh manifest bằng
``python -m src.data.prepare_plantdoc`` — **không** dùng ``src.data.prepare``,
vì script đó chỉ nhận tên thư mục ``Tomato___*`` của PlantVillage và sẽ cho ra
manifest RỖNG với tên thư mục PlantDoc mà không báo lỗi gì.

``--out-dir`` **phải** trỏ ra thư mục riêng khi đo bộ khác. Mặc định ``outputs/``
đang chứa ``report-test.json`` và ``confusion-matrix-test.png`` của PlantVillage
và đã commit vào Git (số liệu của #15) — ghi đè là mất, không báo lỗi.

Khi tập đo thiếu lớp (PlantDoc không có ``target_spot``, và ``spider_mites`` chỉ
có 2 ảnh) thì đọc ``macro_f1_present`` chứ đừng đọc ``macro_f1``: lớp vắng mặt
đóng góp F1 = 0 và kéo macro-F1 xuống một cách máy móc, con số đó không nói gì
về mô hình.
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


def wilson_interval(hits: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Khoảng tin cậy 95% cho accuracy theo phương pháp Wilson.

    Dùng Wilson chứ không dùng công thức xấp xỉ chuẩn ``p ± z·√(p(1−p)/n)`` vì tập
    đo có thể rất nhỏ (phần ``test`` gốc của PlantDoc chỉ 66 ảnh) và accuracy có
    thể sát 0 hoặc sát 1 — đúng hai trường hợp mà xấp xỉ chuẩn cho khoảng vượt ra
    ngoài [0, 1] hoặc hẹp đến mức sai lệch.
    """
    if n == 0:
        return 0.0, 0.0
    p = hits / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


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
    ap.add_argument("--min-support", type=int, default=5,
                    help="Lớp có ít hơn số ảnh này bị loại khỏi macro_f1_min_support — "
                         "chỉ số của một lớp n=2 không có ý nghĩa thống kê")
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

    all_labels = list(range(len(keys)))
    accuracy = float((y_true == y_pred).mean())
    lo, hi = wilson_interval(int((y_true == y_pred).sum()), len(y_true))
    top3 = float(top_k_accuracy_score(y_true, y_prob, k=3, labels=all_labels))
    # labels= là BẮT BUỘC: không truyền thì sklearn tự suy nhãn từ y_true ∪ y_pred,
    # và với tập đo thiếu lớp (PlantDoc) số nhãn suy ra sẽ ít hơn len(target_names)
    # -> ValueError. Hai dòng confusion_matrix/top_k dưới đây vốn đã truyền labels.
    report = classification_report(y_true, y_pred, target_names=keys, labels=all_labels,
                                   output_dict=True, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=all_labels)

    print(classification_report(y_true, y_pred, target_names=keys, labels=all_labels,
                                zero_division=0))

    # Lớp nào thật sự có mặt trong tập đo này
    support = {k: int(report[k]["support"]) for k in keys if k in report}
    present = [k for k in keys if support.get(k, 0) > 0]
    absent = [k for k in keys if support.get(k, 0) == 0]
    macro_f1_present = (
        float(np.mean([report[k]["f1-score"] for k in present])) if present else 0.0
    )

    print(f"Accuracy      : {accuracy:.4f}  (khoảng tin cậy 95%: {lo:.4f}–{hi:.4f}, n={len(y_true)})")
    print(f"Top-3 accuracy: {top3:.4f}")
    print(f"Macro-F1      : {report['macro avg']['f1-score']:.4f}  (tính trên đủ {len(keys)} lớp)")
    if absent:
        print(f"Macro-F1 (lớp có mặt): {macro_f1_present:.4f}  "
              f"(chỉ {len(present)} lớp — ĐỌC CON SỐ NÀY)")
        print(f"[!] Tập đo KHÔNG có ảnh của {len(absent)} lớp: {', '.join(absent)}")
        print("    -> macro_f1 phía trên bị kéo xuống một cách máy móc vì các lớp đó "
              "đóng góp F1 = 0.")
    solid = [k for k in present if support[k] >= args.min_support]
    macro_f1_solid = (
        float(np.mean([report[k]["f1-score"] for k in solid])) if solid else 0.0
    )
    thin = [k for k in present if support[k] < args.min_support]
    if thin:
        print(f"[!] Lớp quá ít ảnh, chỉ số không có ý nghĩa thống kê: "
              f"{', '.join(f'{k} (n={support[k]})' for k in thin)}")
        print(f"Macro-F1 (≥{args.min_support} ảnh): {macro_f1_solid:.4f}  "
              f"(chỉ {len(solid)} lớp — ĐỌC CON SỐ NÀY cho báo cáo)")

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
        "accuracy_ci95": [lo, hi],
        "top3_accuracy": top3,
        "macro_f1": report["macro avg"]["f1-score"],
        "macro_f1_present": macro_f1_present,
        "macro_f1_min_support": macro_f1_solid,
        "min_support": args.min_support,
        "classes_solid": solid,
        "classes_present": present,
        "classes_absent": absent,
        "support_per_class": support,
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
