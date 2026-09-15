"""Sinh manifest cho bộ đo PlantDoc (H2) — dùng cho issue #49, đo domain gap.

Vì sao script riêng, không gộp vào ``prepare.py``:

``prepare.py`` làm một việc khác hẳn — nó **chia ngẫu nhiên** một bộ ảnh
class-per-folder thành train/val/test theo tỉ lệ, và bảng chia tập đó đã được
dùng để huấn luyện checkpoint hiện tại (issue #14, #15). Đụng vào nó là rủi ro
cho tính tái lập của những số liệu đã báo cáo.

PlantDoc thì ngược lại: **không chia gì cả** — bộ này tự mang sẵn thư mục
``train``/``test``, và toàn bộ nó là *tập đo*, không một ảnh nào được vào tập
huấn luyện. Ngoài ra nó có ba vấn đề toàn vẹn mà PlantVillage không có (xem
phần "Ba vấn đề toàn vẹn" bên dưới), cần xử lý và **ghi lại** chứ không im lặng
bỏ qua.

Hai chế độ:

``--mode all`` (mặc định)
    Toàn bộ ảnh PlantDoc cà chua, gộp cả ``train`` lẫn ``test``, ghi thành
    ``split=test`` để ``evaluate.py`` đo hết. **Đây là con số domain gap chính
    của đề tài** — hợp lệ vì checkpoint hiện tại chưa từng thấy một ảnh PlantDoc
    nào, nên con số này đúng vĩnh viễn, kể cả sau khi #50 fine-tune.

``--mode official``
    Chỉ phần ``test`` gốc của PlantDoc. Dùng làm mốc "trước" cho phép so
    trước/sau ở #50 — khi đó ``train`` sẽ được dùng để fine-tune, nên phải đo
    trên đúng những ảnh sẽ làm "sau".

Ba vấn đề toàn vẹn của PlantDoc, đo được ngày 15/09/2026:

1. **Ba cặp ảnh trùng byte tuyệt đối giữa ``train`` và ``test``** (so bằng
   sha256). Bản chia của chính bộ dữ liệu bị rò rỉ. Ở ``--mode all`` thì bỏ bản
   sao, giữ một; ở ``--mode official`` thì bỏ khỏi ``test`` vì chúng sẽ nằm
   trong tập fine-tune.
2. **Một ảnh mang hai nhãn mâu thuẫn**: ``tomato_V8.jpg`` trùng byte, nằm ở
   ``test/Tomato leaf bacterial spot`` và ``train/Tomato Septoria leaf spot``.
   Không có cách biết nhãn nào đúng nên **loại hẳn** — giữ lại thì dù mô hình
   trả lời gì cũng có một nhãn gọi nó là sai.
3. **``spider_mites`` chỉ có 2 ảnh**, ``target_spot`` không có thư mục nào.
   Manifest vẫn giữ 2 ảnh đó (không giấu dữ liệu), nhưng ``evaluate.py`` báo
   riêng macro-F1 trên các lớp có mặt, và báo cáo phải nói rõ n=2 là vô nghĩa
   về thống kê.

Chạy:
    cd model
    python -m src.data.prepare_plantdoc --mode all      --out-dir data/processed/plantdoc-all
    python -m src.data.prepare_plantdoc --mode official --out-dir data/processed/plantdoc-official
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from src.labels import class_keys

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".JPG", ".JPEG", ".PNG"}
MANIFEST_NAME = "split.csv"
AUDIT_NAME = "audit.json"

# Ánh xạ tên thư mục PlantDoc -> khoá lớp của đề tài.
#
# Cố ý viết thẳng ở đây thay vì thêm trường vào
# ``shared/data/tomato_diseases.json``: PlantDoc là bộ ĐO, chỉ liên quan tới
# ``model/``, trong khi file JSON kia là hợp đồng dùng chung với backend và còn
# bị mobile chép tay một bản. Thêm một trường mà cả hai bên đó không cần chỉ tạo
# thêm nghĩa vụ đồng bộ — đúng kiểu "thêm cho sau này dễ" mà CLAUDE.md dặn không
# nên làm.
#
# Tên thư mục lấy từ chính bộ dữ liệu (liệt kê thư mục, không phải đoán). Hai
# lớp của đề tài không có mặt trong PlantDoc thì không xuất hiện ở đây:
#   - target_spot  : PlantDoc không có thư mục nào
#   - (spider_mites có thư mục nhưng chỉ 2 ảnh — vẫn nhận, xử lý ở bước báo cáo)
PLANTDOC_DIR_TO_KEY: dict[str, str] = {
    "Tomato leaf bacterial spot": "bacterial_spot",
    "Tomato Early blight leaf": "early_blight",
    "Tomato leaf late blight": "late_blight",
    "Tomato mold leaf": "leaf_mold",
    "Tomato Septoria leaf spot": "septoria_leaf_spot",
    "Tomato two spotted spider mites leaf": "spider_mites",
    "Tomato leaf yellow virus": "yellow_leaf_curl_virus",
    "Tomato leaf mosaic virus": "mosaic_virus",
    "Tomato leaf": "healthy",
}


def _check_mapping() -> None:
    """Sai khoá lớp thì phải sập ngay, đừng để ra manifest sai rồi mới biết."""
    valid = set(class_keys())
    bad = {d: k for d, k in PLANTDOC_DIR_TO_KEY.items() if k not in valid}
    if bad:
        raise SystemExit(
            f"PLANTDOC_DIR_TO_KEY trỏ tới khoá lớp không có trong danh mục: {bad}\n"
            f"Khoá hợp lệ: {sorted(valid)}"
        )


def scan(raw_dir: Path) -> tuple[list[dict], list[str]]:
    """Quét ``raw_dir/{train,test}/<thư mục lớp>/*.jpg``.

    Trả về danh sách bản ghi kèm sha256 (để tìm ảnh trùng) và danh sách thư mục
    không ánh xạ được.
    """
    records: list[dict] = []
    unknown: list[str] = []

    for split_dir in sorted(p for p in raw_dir.iterdir() if p.is_dir()):
        if split_dir.name not in {"train", "test"}:
            unknown.append(f"{split_dir.name}/ (không phải train|test)")
            continue
        for cls_dir in sorted(p for p in split_dir.iterdir() if p.is_dir()):
            key = PLANTDOC_DIR_TO_KEY.get(cls_dir.name)
            if key is None:
                unknown.append(f"{split_dir.name}/{cls_dir.name}")
                continue
            for img in sorted(cls_dir.rglob("*")):
                if not (img.is_file() and img.suffix in IMAGE_SUFFIXES):
                    continue
                records.append({
                    "path": img.as_posix(),
                    "label": key,
                    "origin": split_dir.name,
                    "dir": cls_dir.name,
                    "sha": hashlib.sha256(img.read_bytes()).hexdigest(),
                })
    return records, unknown


def find_problems(records: list[dict]) -> tuple[dict[str, list[dict]], set[str]]:
    """Tìm ảnh trùng byte và ảnh mang nhãn mâu thuẫn.

    Trả về (nhóm ảnh trùng theo sha, tập sha có nhãn mâu thuẫn).
    """
    by_sha: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_sha[r["sha"]].append(r)

    dups = {s: rs for s, rs in by_sha.items() if len(rs) > 1}
    conflicting = {s for s, rs in dups.items() if len({r["label"] for r in rs}) > 1}
    return dups, conflicting


def main() -> None:
    ap = argparse.ArgumentParser(description="Sinh manifest cho bộ đo PlantDoc (#49)")
    ap.add_argument("--raw-dir", default="data/field/plantdoc")
    ap.add_argument("--out-dir", default="data/processed/plantdoc-all")
    ap.add_argument("--mode", choices=["all", "official"], default="all",
                    help="all = gộp train+test làm tập đo (số chính); "
                         "official = chỉ phần test gốc (mốc cho #50)")
    args = ap.parse_args()

    _check_mapping()

    raw_dir = Path(args.raw_dir)
    if not raw_dir.exists():
        raise SystemExit(
            f"Không tìm thấy '{raw_dir}'.\n"
            "Tải PlantDoc từ https://github.com/pratikkayal/PlantDoc-Dataset và đặt\n"
            "phần cà chua vào đó theo cấu trúc raw-dir/{train,test}/<thư mục lớp>/.\n"
            "Thư mục này nằm NGOÀI Git (xem CLAUDE.md)."
        )

    records, unknown = scan(raw_dir)
    if not records:
        raise SystemExit(f"Không tìm thấy ảnh nào trong '{raw_dir}'")
    if unknown:
        print(f"[!] Bỏ qua {len(unknown)} thư mục không ánh xạ được: "
              f"{', '.join(unknown[:6])}{' ...' if len(unknown) > 6 else ''}")

    dups, conflicting = find_problems(records)

    # --- Lọc theo chế độ, ghi lại từng ảnh bị bỏ và VÌ SAO bị bỏ ---
    dropped: list[dict] = []
    kept: list[dict] = []
    seen_sha: set[str] = set()

    for r in records:
        if args.mode == "official" and r["origin"] != "test":
            continue

        if r["sha"] in conflicting:
            dropped.append({**r, "reason": "nhãn mâu thuẫn — cùng ảnh, hai lớp khác nhau"})
            continue

        if r["sha"] in dups:
            if args.mode == "official":
                # Ảnh này cũng nằm trong train -> sẽ là dữ liệu fine-tune ở #50
                dropped.append({**r, "reason": "trùng byte với ảnh trong train (rò rỉ)"})
                continue
            if r["sha"] in seen_sha:
                dropped.append({**r, "reason": "bản sao trùng byte, đã giữ một bản"})
                continue

        seen_sha.add(r["sha"])
        kept.append(r)

    # Toàn bộ manifest là tập ĐO -> split="test" cho mọi dòng.
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = out_dir / MANIFEST_NAME
    with open(manifest, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["path", "label", "split"])
        w.writerows((r["path"], r["label"], "test") for r in kept)

    counts = Counter(r["label"] for r in kept)
    origin = Counter(r["origin"] for r in kept)
    audit = {
        "mode": args.mode,
        "raw_dir": str(raw_dir),
        "num_files_scanned": len(records),
        "num_kept": len(kept),
        "num_dropped": len(dropped),
        "kept_by_origin": dict(origin),
        "kept_per_class": {k: counts.get(k, 0) for k in class_keys()},
        "classes_absent": [k for k in class_keys() if not counts.get(k)],
        "duplicate_groups": [
            {"sha": s, "files": [r["path"] for r in rs],
             "labels": sorted({r["label"] for r in rs}),
             "conflicting": s in conflicting}
            for s, rs in sorted(dups.items())
        ],
        "dropped": dropped,
        "unknown_dirs": unknown,
        "dir_to_key": PLANTDOC_DIR_TO_KEY,
    }
    with open(out_dir / AUDIT_NAME, "w", encoding="utf-8") as f:
        json.dump(audit, f, ensure_ascii=False, indent=2)

    # --- Báo cáo ra màn hình ---
    print(f"\nChế độ '{args.mode}' — quét {len(records)} file, giữ {len(kept)}, bỏ {len(dropped)}")
    if origin:
        print("Nguồn ảnh giữ lại: " + ", ".join(f"{k}={v}" for k, v in sorted(origin.items())))

    print(f"\n{'Lớp':<26}{'số ảnh':>10}")
    print("-" * 36)
    for key in class_keys():
        n = counts.get(key, 0)
        note = "  <- KHÔNG CÓ trong PlantDoc" if n == 0 else ("  <- quá ít, vô nghĩa thống kê" if n < 5 else "")
        print(f"{key:<26}{n:>10}{note}")
    print("-" * 36)
    print(f"{'TỔNG':<26}{len(kept):>10}")

    if dropped:
        print(f"\nĐã bỏ {len(dropped)} ảnh:")
        for reason, n in Counter(d["reason"] for d in dropped).most_common():
            print(f"  {n:>3}  {reason}")

    print(f"\nĐã ghi:\n  {manifest}\n  {out_dir / AUDIT_NAME}")


if __name__ == "__main__":
    main()
