"""Đo phân bố độ tin cậy + energy của mô hình lá trên bộ ảnh "không phải lá cà
chua" (issue #91) — số liệu #47 đang chờ để hiệu chỉnh ngưỡng go/no-go.

Bối cảnh: `docx/Plan_model.md` mục 1.3–1.4 đã đề xuất dùng energy score
(``-logsumexp(logits)``) thay vì chỉ ngưỡng tin cậy, nhưng số liệu lúc đó
(bảng 1.3/1.4) chỉ dựa trên **11–16 ảnh tổng hợp** (nền trơn, nhiễu, ô bàn cờ) —
tự ticket #91 gọi đó là "định hướng, chưa phải hiệu chỉnh". Script này chạy lại
đúng phép đo đó trên 342 ảnh thật của #91 (6 nhóm, xem `data/negative/manifest.csv`).

Không đo lại phía "chặn oan % ảnh test PlantVillage" ở đây — đó là tập dữ liệu
khác (ảnh lá thật), việc của #47 khi ghép hai bảng lại để chọn ngưỡng cuối cùng.
Script này chỉ trả lời: "ảnh không phải lá cà chua thì mô hình lá cho ra
confidence/energy thế nào".

Chạy:
    cd model
    .venv/Scripts/python -m src.evaluation.audit_negative_confidence

Sinh ra trong ``outputs/negative-confidence/``:
  - ``results.csv``   một dòng/ảnh: path, group, lớp dự đoán, confidence, energy
  - ``summary.json``  thống kê tổng + theo nhóm, và bảng quét ngưỡng kiểu
                       Plan_model.md bảng 1.3/1.4 (đọc thẳng vào #47)
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch
from PIL import Image

from src.data.dataset import build_infer_transform
from src.models.build import load_checkpoint
from src.utils.common import ensure_dir, get_device

IMAGE_EXTS = (".jpg", ".jpeg", ".png")
# Giữ đúng hai mức đã đề xuất ở Plan_model.md bảng 1.4 (tính trên 11-16 ảnh cũ)
# để so sánh trực tiếp: ngưỡng đó có còn đứng vững trên 342 ảnh thật không.
CONFIDENCE_THRESHOLDS = [0.50, 0.60, 0.70, 0.80, 0.90, 0.95]
ENERGY_THRESHOLDS = [-3.34, -2.67, -2.0, -1.0, 0.0]


def collect_images(negative_dir: Path) -> list[tuple[str, Path]]:
    items = []
    for group_dir in sorted(negative_dir.iterdir()):
        if not group_dir.is_dir():
            continue
        for p in sorted(group_dir.iterdir()):
            if p.suffix.lower() in IMAGE_EXTS:
                items.append((group_dir.name, p))
    return items


def percentile(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    s = sorted(values)
    idx = min(len(s) - 1, max(0, round(q / 100 * (len(s) - 1))))
    return s[idx]


def summarize(values: list[float]) -> dict:
    if not values:
        return {}
    return {
        "n": len(values),
        "mean": sum(values) / len(values),
        "min": min(values),
        "p10": percentile(values, 10),
        "median": percentile(values, 50),
        "p90": percentile(values, 90),
        "max": max(values),
    }


def run(checkpoint: Path, negative_dir: Path, out_dir: Path) -> None:
    device = get_device()
    model, ckpt = load_checkpoint(str(checkpoint), device)
    class_keys: list[str] = ckpt["class_keys"]
    transform = build_infer_transform(ckpt.get("image_size", 224))

    items = collect_images(negative_dir)
    if not items:
        raise SystemExit(f"Không thấy ảnh nào trong '{negative_dir}'. Chạy fetch_negative_images.py trước.")

    rows: list[dict] = []
    started = time.perf_counter()

    with torch.no_grad():
        for group, path in items:
            image = Image.open(path).convert("RGB")
            tensor = transform(image).unsqueeze(0).to(device)
            logits = model(tensor)[0]
            probs = torch.softmax(logits, dim=0)
            idx = int(probs.argmax().item())
            energy = -torch.logsumexp(logits, dim=0).item()

            rows.append({
                "path": str(path.relative_to(negative_dir.parent.parent)),
                "group": group,
                "predicted_disease_key": class_keys[idx],
                "confidence": float(probs[idx].item()),
                "energy": energy,
            })

    elapsed = time.perf_counter() - started
    print(f"Đã suy luận {len(rows)} ảnh trong {elapsed:.1f}s ({elapsed / len(rows) * 1000:.0f} ms/ảnh, device={device})")

    ensure_dir(out_dir)
    results_path = out_dir / "results.csv"
    with results_path.open("w", encoding="utf-8", newline="") as f:
        import csv
        writer = csv.DictWriter(f, fieldnames=["path", "group", "predicted_disease_key", "confidence", "energy"])
        writer.writeheader()
        writer.writerows(rows)

    all_conf = [r["confidence"] for r in rows]
    all_energy = [r["energy"] for r in rows]

    by_group: dict[str, list[dict]] = {}
    for r in rows:
        by_group.setdefault(r["group"], []).append(r)

    summary = {
        "n_images": len(rows),
        "checkpoint": str(checkpoint),
        "confidence": summarize(all_conf),
        "energy": summarize(all_energy),
        "confidence_threshold_sweep": [
            {
                "threshold": t,
                "pct_blocked": sum(1 for c in all_conf if c < t) / len(all_conf) * 100,
            }
            for t in CONFIDENCE_THRESHOLDS
        ],
        "energy_threshold_sweep": [
            {
                "threshold": t,
                "pct_blocked": sum(1 for e in all_energy if e > t) / len(all_energy) * 100,
            }
            for t in ENERGY_THRESHOLDS
        ],
        "by_group": {
            group: {
                "n": len(g_rows),
                "confidence": summarize([r["confidence"] for r in g_rows]),
                "energy": summarize([r["energy"] for r in g_rows]),
            }
            for group, g_rows in sorted(by_group.items())
        },
    }

    summary_path = out_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nGhi {results_path} và {summary_path}")
    print("\n--- Quét ngưỡng tin cậy (đọc thẳng vào #47) ---")
    print("ngưỡng | % ảnh không phải lá bị chặn (confidence < ngưỡng)")
    for row in summary["confidence_threshold_sweep"]:
        print(f"  {row['threshold']:.2f} | {row['pct_blocked']:.1f}%")
    print("\n--- Quét ngưỡng energy ---")
    print("ngưỡng | % ảnh không phải lá bị chặn (energy > ngưỡng)")
    for row in summary["energy_threshold_sweep"]:
        print(f"  {row['threshold']:.2f} | {row['pct_blocked']:.1f}%")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=Path("checkpoints/leaf_disease_detection_model.pt"))
    parser.add_argument("--negative-dir", type=Path, default=Path("data/negative"))
    parser.add_argument("--out-dir", type=Path, default=Path("outputs/negative-confidence"))
    args = parser.parse_args()
    run(args.checkpoint, args.negative_dir, args.out_dir)
