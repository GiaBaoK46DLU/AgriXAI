"""Chọn mẫu ảnh cho phép kiểm Grad-CAM bằng mắt (issue #17 — MD-08).

Vì sao cần một script riêng chỉ để *chọn ảnh*: toàn bộ kết luận của #17 dựa trên
vài chục ảnh được khoanh tay. Nếu ai đó hỏi "sao lại chọn đúng mấy tấm này" mà
câu trả lời là "chọn đại" thì con số mất giá trị ngay. Script này làm việc chọn
trở nên **tái lập được**: cùng manifest + cùng seed thì ra cùng danh sách ảnh,
trên máy nào cũng vậy.

Hai chi tiết bảo đảm tính tái lập, đừng sửa nếu không hiểu rõ:

1. Sắp xếp đường dẫn trước khi bốc mẫu. ``csv.DictReader`` giữ thứ tự file, mà
   thứ tự file lại phụ thuộc lần sinh manifest — sắp xếp làm thứ tự đầu vào cố
   định trước khi seed có tác dụng.
2. Bốc mẫu **theo từng lớp** chứ không bốc ngẫu nhiên trên cả tập. Bốc trên cả
   tập thì lớp đông (``yellow_leaf_curl_virus`` có 803 ảnh test) sẽ chiếm hết,
   còn ``mosaic_virus`` (55 ảnh) có thể không có tấm nào — mà #17 yêu cầu nhận
   xét cho **từng lớp**.

Chạy:
    cd model
    python -m src.xai.audit_sample --manifest data/processed/split.csv \
        --dataset pv --per-class 3 --out outputs/audit-gradcam-17/mau-pv.csv
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

from src.utils.common import ensure_dir


def pick_samples(manifest: str | Path, split: str, dataset: str,
                 per_class: int, seed: int) -> list[dict[str, str]]:
    """Bốc ``per_class`` ảnh mỗi lớp từ manifest, cố định theo seed."""
    by_label: dict[str, list[str]] = {}
    with open(manifest, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["split"] != split:
                continue
            by_label.setdefault(row["label"], []).append(row["path"])

    if not by_label:
        raise SystemExit(f"Manifest '{manifest}' không có ảnh nào cho split='{split}'")

    rng = random.Random(seed)
    picked: list[dict[str, str]] = []
    for label in sorted(by_label):
        paths = sorted(by_label[label])
        # Lớp ít ảnh hơn per_class thì lấy hết và ghi rõ n thật trong báo cáo —
        # PlantDoc chỉ có 2 ảnh spider_mites, đó là dữ kiện chứ không phải lỗi.
        n = min(per_class, len(paths))
        for i, path in enumerate(sorted(rng.sample(paths, n)), start=1):
            picked.append({
                "sample_id": f"{dataset}-{label}-{i}",
                "dataset": dataset,
                "label": label,
                "path": path,
            })
    return picked


def main() -> None:
    ap = argparse.ArgumentParser(description="Chọn mẫu ảnh cho phép kiểm Grad-CAM #17")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--split", default="test")
    ap.add_argument("--dataset", required=True,
                    help="Tiền tố ngắn cho mã mẫu: 'pv' (PlantVillage) hoặc 'pd' (PlantDoc)")
    ap.add_argument("--per-class", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    rows = pick_samples(args.manifest, args.split, args.dataset,
                        args.per_class, args.seed)

    out = Path(args.out)
    ensure_dir(out.parent)
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["sample_id", "dataset", "label", "path"])
        w.writeheader()
        w.writerows(rows)

    counts: dict[str, int] = {}
    for r in rows:
        counts[r["label"]] = counts.get(r["label"], 0) + 1
    print(f"Đã chọn {len(rows)} ảnh từ '{args.manifest}' (seed={args.seed}) -> {out}")
    for label in sorted(counts):
        flag = "" if counts[label] >= args.per_class else "   <-- ít hơn yêu cầu"
        print(f"  {label:<26} {counts[label]}{flag}")


if __name__ == "__main__":
    main()
