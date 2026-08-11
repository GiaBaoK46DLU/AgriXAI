"""Quét dữ liệu PlantVillage và chia tập train/val/test.

Cách làm: KHÔNG copy ảnh sang thư mục mới (tốn vài trăm MB và mất thời gian),
mà chỉ ghi ra một file manifest CSV chứa đường dẫn + nhãn + tập. Dataset đọc
manifest này. Muốn chia lại chỉ cần chạy lại script, dữ liệu gốc không đụng tới.

Chạy:
    cd model
    python -m src.data.prepare
    python -m src.data.prepare --raw-dir data/raw --seed 42
"""

from __future__ import annotations

import argparse
import csv
import random
from collections import Counter, defaultdict
from pathlib import Path

from src.labels import class_keys, dir_to_key

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".JPG", ".JPEG", ".PNG"}
MANIFEST_NAME = "split.csv"


def scan_images(raw_dir: Path) -> dict[str, list[Path]]:
    """Tìm ảnh trong các thư mục con Tomato___* và gom theo khoá lớp."""
    mapping = dir_to_key()
    found: dict[str, list[Path]] = defaultdict(list)
    unknown_dirs: list[str] = []

    for sub in sorted(p for p in raw_dir.iterdir() if p.is_dir()):
        key = mapping.get(sub.name)
        if key is None:
            unknown_dirs.append(sub.name)
            continue
        for img in sorted(sub.rglob("*")):
            if img.is_file() and img.suffix in IMAGE_SUFFIXES:
                found[key].append(img)

    if unknown_dirs:
        print(f"[!] Bỏ qua {len(unknown_dirs)} thư mục không nằm trong danh mục: "
              f"{', '.join(unknown_dirs[:5])}{' ...' if len(unknown_dirs) > 5 else ''}")
    return found


def split_class(files: list[Path], val_ratio: float, test_ratio: float,
                rng: random.Random) -> dict[str, list[Path]]:
    """Chia ngẫu nhiên ảnh của MỘT lớp — chia theo từng lớp để giữ tỉ lệ cân bằng."""
    shuffled = files[:]
    rng.shuffle(shuffled)
    n = len(shuffled)
    n_test = int(n * test_ratio)
    n_val = int(n * val_ratio)
    return {
        "test": shuffled[:n_test],
        "val": shuffled[n_test:n_test + n_val],
        "train": shuffled[n_test + n_val:],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Chia tập dữ liệu PlantVillage tomato")
    ap.add_argument("--raw-dir", default="data/raw")
    ap.add_argument("--out-dir", default="data/processed")
    ap.add_argument("--val-ratio", type=float, default=0.15)
    ap.add_argument("--test-ratio", type=float, default=0.15)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    raw_dir = Path(args.raw_dir)
    if not raw_dir.exists():
        raise SystemExit(
            f"Không tìm thấy '{raw_dir}'.\n"
            "Hãy tải bộ PlantVillage và đặt các thư mục Tomato___* vào đó — "
            "xem hướng dẫn ở model/README.md"
        )

    rng = random.Random(args.seed)
    by_class = scan_images(raw_dir)

    missing = [k for k in class_keys() if not by_class.get(k)]
    if missing:
        print(f"[!] Thiếu ảnh cho các lớp: {', '.join(missing)}")

    rows: list[tuple[str, str, str]] = []
    for key in class_keys():
        files = by_class.get(key, [])
        if not files:
            continue
        for split, items in split_class(files, args.val_ratio, args.test_ratio, rng).items():
            rows.extend((str(p.as_posix()), key, split) for p in items)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = out_dir / MANIFEST_NAME
    with open(manifest, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["path", "label", "split"])
        writer.writerows(rows)

    # Bảng thống kê để đưa vào báo cáo
    counts: dict[str, Counter] = defaultdict(Counter)
    for _, label, split in rows:
        counts[label][split] += 1

    print(f"\nĐã ghi {len(rows)} dòng vào {manifest}\n")
    print(f"{'Lớp':<26}{'train':>8}{'val':>8}{'test':>8}{'tổng':>8}")
    print("-" * 58)
    for key in class_keys():
        c = counts.get(key, Counter())
        print(f"{key:<26}{c['train']:>8}{c['val']:>8}{c['test']:>8}"
              f"{c['train'] + c['val'] + c['test']:>8}")
    total = Counter()
    for c in counts.values():
        total.update(c)
    print("-" * 58)
    print(f"{'TỔNG':<26}{total['train']:>8}{total['val']:>8}{total['test']:>8}{len(rows):>8}")


if __name__ == "__main__":
    main()
