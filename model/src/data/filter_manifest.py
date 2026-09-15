"""Lọc một manifest xuống còn một tập lớp cho trước — để so sánh CÔNG BẰNG.

Vì sao cần: bộ đo PlantDoc chỉ có 8 trong 10 lớp của đề tài (không có
``target_spot``, và ``spider_mites`` chỉ 2 ảnh). Đem accuracy PlantVillage tính
trên đủ 10 lớp ra so với accuracy PlantDoc tính trên 8 lớp là **so lệch** — hai
bài toán khác độ khó. Muốn con số chênh lệch nói đúng về domain gap thì cả hai
phía phải cùng một tập lớp.

Ví dụ dùng cho issue #49:

    cd model
    # Lấy đúng tập lớp mà PlantDoc thật sự đo được
    python -m src.data.filter_manifest \\
        --manifest data/processed/split.csv \\
        --out data/processed/plantvillage-8lop/split.csv \\
        --keep bacterial_spot,early_blight,late_blight,leaf_mold,septoria_leaf_spot,yellow_leaf_curl_virus,mosaic_virus,healthy

Không copy ảnh, chỉ ghi lại một manifest mới — giống tinh thần của
``src.data.prepare``. Manifest gốc không bị đụng tới.
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from src.labels import class_keys


def main() -> None:
    ap = argparse.ArgumentParser(description="Lọc manifest xuống một tập lớp")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--keep", required=True,
                    help="Danh sách khoá lớp cách nhau bằng dấu phẩy")
    ap.add_argument("--split", default=None,
                    help="Chỉ giữ một split (train|val|test). Mặc định giữ hết.")
    args = ap.parse_args()

    keep = [k.strip() for k in args.keep.split(",") if k.strip()]
    valid = set(class_keys())
    bad = [k for k in keep if k not in valid]
    if bad:
        raise SystemExit(
            f"Khoá lớp không có trong danh mục: {bad}\nHợp lệ: {sorted(valid)}"
        )

    src = Path(args.manifest)
    if not src.exists():
        raise SystemExit(f"Không tìm thấy manifest '{src}'")

    keep_set = set(keep)
    rows: list[tuple[str, str, str]] = []
    dropped = Counter()
    with open(src, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if args.split and row["split"] != args.split:
                continue
            if row["label"] not in keep_set:
                dropped[row["label"]] += 1
                continue
            rows.append((row["path"], row["label"], row["split"]))

    if not rows:
        raise SystemExit("Không còn dòng nào sau khi lọc — kiểm lại --keep / --split")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["path", "label", "split"])
        w.writerows(rows)

    counts: dict[str, Counter] = {}
    for _, label, split in rows:
        counts.setdefault(label, Counter())[split] += 1

    print(f"\nGiữ {len(rows)} dòng trên {len(keep)} lớp, bỏ {sum(dropped.values())} dòng\n")
    print(f"{'Lớp':<26}{'train':>8}{'val':>8}{'test':>8}")
    print("-" * 50)
    for k in class_keys():
        if k not in keep_set:
            continue
        c = counts.get(k, Counter())
        print(f"{k:<26}{c['train']:>8}{c['val']:>8}{c['test']:>8}")
    print("-" * 50)
    tot = Counter()
    for c in counts.values():
        tot.update(c)
    print(f"{'TỔNG':<26}{tot['train']:>8}{tot['val']:>8}{tot['test']:>8}")

    if dropped:
        print("\nĐã bỏ theo lớp: "
              + ", ".join(f"{k}={v}" for k, v in sorted(dropped.items())))
    print(f"\nĐã ghi: {out}")


if __name__ == "__main__":
    main()
