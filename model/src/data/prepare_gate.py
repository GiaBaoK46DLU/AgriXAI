"""Sinh manifest chia tập cho bộ chặn 2 lớp lá / không phải lá (issue #92).

Hai nguồn ảnh ghép lại thành một manifest ``path,label,split`` duy nhất:

``tomato_leaf`` (lớp dương)
    Lấy từ PlantVillage qua ``data/processed/split.csv``, **lấy mẫu đều 10 lớp
    bệnh** chứ không chỉ lá khoẻ — nếu chỉ học lá khoẻ thì bộ chặn sẽ coi lá bệnh
    nặng là "không phải lá", đúng cái ca tệ nhất mà #92 muốn tránh.

    **Cộng thêm 674 ảnh PlantDoc thuộc thư mục ``train`` gốc** (chốt 18/09/2026).
    Không phải tuỳ chọn cho vui — không có chúng thì bộ chặn không dùng được:
    lớp dương toàn ảnh phòng thí nghiệm còn lớp âm toàn ảnh Internet nên mạng
    tách hai lớp bằng *phong cách ảnh*, đo được là **chặn oan 92,0 % ảnh lá
    thật**. Phá lối tắt bằng augmentation (ghép nền, nắng gắt — xem
    ``gate_augment.py``) kéo được xuống 65,2 %, vẫn chưa dùng nổi. Chỉ khi cho
    bộ chặn nhìn lá thật ngoài đồng mới xong.

    ⚠️ **Ranh giới bắt buộc giữ:** chỉ đụng phần ``train`` của PlantDoc, đúng
    ranh giới ``CLAUDE.md`` đã đặt sẵn cho #50 hướng 2. **68 ảnh thư mục ``test``
    không được dùng vào huấn luyện dưới bất kỳ hình thức nào** — đó là thước đo
    sạch duy nhất còn lại cho bộ chặn. Con số domain gap gốc của #49 (99,60 % →
    30,81 % trên cả 742 ảnh) vẫn đúng vì nó đo checkpoint *mô hình bệnh*, chưa
    từng thấy PlantDoc. Nhưng từ nay **mọi phép đo cả pipeline (chặn + mô hình
    bệnh) trên toàn bộ 742 ảnh đều nhiễm** — phải báo trên 68 ảnh test.

``not_tomato_leaf`` (lớp âm)
    Toàn bộ 342 ảnh của #91 trong ``data/negative/``, chia 70/15/15 **phân tầng
    theo nhóm** để mỗi nhóm (đồ trong nhà, tay/mặt, lá cây khác...) đều có mặt ở
    cả ba tập — cần thế mới đo riêng được từng nhóm như tiêu chí #92 yêu cầu.

⚠️ **Vì sao ảnh dương GIỮ NGUYÊN split gốc của ``split.csv`` thay vì chia lại:**
tiêu chí #92 bắt "chạy lại toàn bộ 2.719 ảnh test PlantVillage qua bộ chặn, đếm
bao nhiêu ảnh bị chặn oan". Nếu chia ngẫu nhiên lại thì ảnh vốn thuộc tập test
của mô hình chính sẽ rơi vào tập *huấn luyện* của bộ chặn, và con số "chặn oan"
đo trên chính ảnh nó đã học — **đẹp giả, không báo lỗi gì**. Giữ nguyên split thì
ranh giới train/test của cả hai mô hình trùng nhau, con số đó mới có nghĩa.

Tỉ lệ dương:âm cố ý lệch về phía lá (mặc định 100 ảnh/lớp bệnh = 1.000 dương so
với 342 âm, ~3:1). Ticket #92 đặt recall lá >= 0,98 mà không đặt mục tiêu cứng cho
lớp âm, vì chặn oan lá thật làm người dùng không dùng được app — prior nghiêng về
"lá" là đúng chiều chi phí đó.

Chạy:
    cd model
    .venv/Scripts/python -m src.data.prepare_gate

Ghi ``data/processed/gate-split.csv`` + ``gate-split-stats.json``.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path

POSITIVE_LABEL = "tomato_leaf"
NEGATIVE_LABEL = "not_tomato_leaf"
SPLIT_RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}


def load_positives(split_csv: Path, per_class_per_split: dict[str, int], seed: int) -> list[dict]:
    """Lấy mẫu đều theo lớp bệnh, giữ nguyên split gốc của từng ảnh."""
    by_class_split: dict[tuple[str, str], list[str]] = defaultdict(list)
    with split_csv.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            by_class_split[(row["label"], row["split"])].append(row["path"])

    rng = random.Random(seed)
    rows: list[dict] = []
    for (disease, split), paths in sorted(by_class_split.items()):
        quota = per_class_per_split[split]
        chosen = sorted(paths)
        rng.shuffle(chosen)
        for p in chosen[:quota]:
            rows.append({
                "path": p,
                "label": POSITIVE_LABEL,
                "split": split,
                "source_group": disease,
            })
    return rows


def load_plantdoc_positives(plantdoc_manifest: Path, seed: int) -> list[dict]:
    """Ảnh lá thật ngoài đồng, CHỈ lấy từ thư mục ``train`` gốc của PlantDoc.

    Chia tiếp 70/15/15 vào train/val/test của bộ chặn thay vì dồn hết vào train:
    val/test của bộ chặn cũng cần có lá kiểu đồng ruộng, không thì việc chọn
    checkpoint tốt nhất lại mù đúng cái nó đang phải sửa.
    """
    if not plantdoc_manifest.exists():
        return []

    with plantdoc_manifest.open(encoding="utf-8") as f:
        paths = sorted(r["path"] for r in csv.DictReader(f) if "/train/" in r["path"])

    rng = random.Random(seed)
    rng.shuffle(paths)
    n = len(paths)
    n_train = round(n * SPLIT_RATIOS["train"])
    n_val = round(n * SPLIT_RATIOS["val"])
    assignment = ["train"] * n_train + ["val"] * n_val + ["test"] * (n - n_train - n_val)
    return [{"path": p, "label": POSITIVE_LABEL, "split": s, "source_group": "plantdoc_train"}
            for p, s in zip(paths, assignment)]


def load_negatives(negative_manifest: Path, seed: int) -> list[dict]:
    """Chia 70/15/15 phân tầng theo nhóm ảnh âm."""
    by_group: dict[str, list[str]] = defaultdict(list)
    with negative_manifest.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            by_group[row["group"]].append(row["path"].replace("\\", "/"))

    rng = random.Random(seed)
    rows: list[dict] = []
    for group, paths in sorted(by_group.items()):
        paths = sorted(paths)
        rng.shuffle(paths)
        n = len(paths)
        n_train = round(n * SPLIT_RATIOS["train"])
        n_val = round(n * SPLIT_RATIOS["val"])
        assignment = (["train"] * n_train + ["val"] * n_val
                      + ["test"] * (n - n_train - n_val))
        for path, split in zip(paths, assignment):
            rows.append({
                "path": path,
                "label": NEGATIVE_LABEL,
                "split": split,
                "source_group": group,
            })
    return rows


def run(split_csv: Path, negative_manifest: Path, plantdoc_manifest: Path,
        out_csv: Path, per_class: int, seed: int) -> None:
    # Chia hạn ngạch theo đúng tỉ lệ 70/15/15 để tập val/test lớp dương không
    # phình to hơn tập train một cách vô lý khi per_class nhỏ.
    per_class_per_split = {
        "train": per_class,
        "val": max(1, round(per_class * SPLIT_RATIOS["val"] / SPLIT_RATIOS["train"])),
        "test": max(1, round(per_class * SPLIT_RATIOS["test"] / SPLIT_RATIOS["train"])),
    }

    positives = load_positives(split_csv, per_class_per_split, seed)
    plantdoc = load_plantdoc_positives(plantdoc_manifest, seed)
    negatives = load_negatives(negative_manifest, seed)
    rows = positives + plantdoc + negatives

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "label", "split", "source_group"])
        writer.writeheader()
        writer.writerows(rows)

    stats: dict = {"per_class_quota": per_class_per_split, "seed": seed, "counts": {}}
    for split in ("train", "val", "test"):
        stats["counts"][split] = {
            POSITIVE_LABEL: sum(1 for r in rows if r["split"] == split and r["label"] == POSITIVE_LABEL),
            NEGATIVE_LABEL: sum(1 for r in rows if r["split"] == split and r["label"] == NEGATIVE_LABEL),
        }
    stats["positive_nguon"] = {
        "plantvillage": len(positives),
        "plantdoc_train": len(plantdoc),
    }
    stats["negative_by_group"] = {
        group: {
            split: sum(1 for r in negatives if r["source_group"] == group and r["split"] == split)
            for split in ("train", "val", "test")
        }
        for group in sorted({r["source_group"] for r in negatives})
    }

    stats_path = out_csv.with_name(out_csv.stem + "-stats.json")
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Ghi {out_csv} ({len(rows)} dòng) và {stats_path}\n")
    print(f"{'split':6s} {POSITIVE_LABEL:>16s} {NEGATIVE_LABEL:>18s}")
    for split, c in stats["counts"].items():
        print(f"{split:6s} {c[POSITIVE_LABEL]:16d} {c[NEGATIVE_LABEL]:18d}")
    print("\nẢnh âm theo nhóm (train/val/test):")
    for group, c in stats["negative_by_group"].items():
        print(f"  {group:22s} {c['train']:3d} / {c['val']:2d} / {c['test']:2d}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--split-csv", type=Path, default=Path("data/processed/split.csv"))
    ap.add_argument("--negative-manifest", type=Path, default=Path("data/negative/manifest.csv"))
    ap.add_argument("--plantdoc-manifest", type=Path,
                    default=Path("data/processed/plantdoc-all/split.csv"),
                    help="Chỉ phần '/train/' được dùng; '/test/' luôn bị loại")
    ap.add_argument("--out", type=Path, default=Path("data/processed/gate-split.csv"))
    ap.add_argument("--per-class", type=int, default=100,
                    help="Số ảnh dương mỗi lớp bệnh trong tập TRAIN (val/test theo tỉ lệ)")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    run(args.split_csv, args.negative_manifest, args.plantdoc_manifest,
        args.out, args.per_class, args.seed)
