"""Đánh giá bộ chặn 2 lớp lá / không phải lá (issue #92).

Trả lời đúng ba câu hỏi đo được bằng máy trong mục "Cách kiểm tra" của #92
(hai ca còn lại là thao tác tay qua app, không script được):

A. **Tập test riêng của bộ chặn** — recall lớp ``tomato_leaf`` phải >= 0,98.
   Ticket đặt ngưỡng cứng cho lớp này mà **không** đặt cho lớp âm, vì chặn oan
   lá thật làm người dùng không dùng được app, còn để lọt ảnh rác chỉ khó chịu.

B. **Toàn bộ 2.719 ảnh test PlantVillage** — đếm bao nhiêu ảnh bị chặn oan.
   Hợp lệ vì ảnh dương của bộ chặn chỉ lấy từ split ``train`` của
   ``split.csv``: không một ảnh test nào lọt vào lúc huấn luyện
   (xem ``src/data/prepare_gate.py``).

C. **Toàn bộ 342 ảnh âm của #91** — đếm bao nhiêu ảnh lọt, tách theo nhóm.
   ⚠️ Con số theo nhóm ở đây có **hai cách đọc**, script in cả hai: tính trên
   *toàn nhóm* thì lạc quan (phần lớn ảnh nhóm đó đã nằm trong tập huấn luyện),
   tính trên *riêng phần test* mới trung thực nhưng n rất nhỏ (~9 ảnh/nhóm).
   Nhóm ``other_plant_leaves`` là ca khó nhất và cũng là ca hội đồng dễ hỏi nhất.

D. **PlantDoc — phép thử lối tắt, KHÔNG có trong ticket nhưng là phép đo quan
   trọng nhất ở đây.** A/B/C đều đo lớp dương bằng ảnh PlantVillage (chụp trong
   phòng, nền đồng nhất) còn lớp âm toàn ảnh Internet, nên hai lớp **tách được
   bằng phong cách ảnh** chứ không cần hiểu gì về lá. Nếu bộ chặn học lối tắt đó
   thì A/B/C vẫn đẹp gần tuyệt đối mà bộ chặn **vô dụng lúc chạy thật**, vì ảnh
   nông dân chụp ngoài đồng trông giống PlantDoc chứ không giống PlantVillage.
   742 ảnh PlantDoc **đều là lá cà chua thật**, nên mọi ảnh bị chặn đều là chặn
   oan — đây là con số nói đúng điều gì sẽ xảy ra khi bật ra thật.

Chạy:
    cd model
    .venv/Scripts/python -m src.evaluation.evaluate_gate

Ghi ``outputs/gate/report.json``.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset

from src.data.dataset import build_infer_transform
from src.models.build import load_checkpoint
from src.utils.common import ensure_dir, get_device

POSITIVE_LABEL = "tomato_leaf"
NEGATIVE_LABEL = "not_tomato_leaf"


class _PathListDataset(Dataset):
    """Chạy suy luận trên một danh sách đường dẫn bất kỳ, không cần nhãn."""

    def __init__(self, paths: list[Path], transform) -> None:
        self.paths = paths
        self.transform = transform

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, idx: int):
        image = Image.open(self.paths[idx]).convert("RGB")
        return self.transform(image), idx


@torch.no_grad()
def predict_paths(model, paths: list[Path], transform, device, batch_size: int = 64) -> list[int]:
    """Trả về chỉ số lớp dự đoán, theo đúng thứ tự ``paths``."""
    loader = DataLoader(_PathListDataset(paths, transform), batch_size=batch_size,
                        shuffle=False, num_workers=4, pin_memory=device.type == "cuda")
    preds = [0] * len(paths)
    for images, idxs in loader:
        out = model(images.to(device)).argmax(1).cpu().tolist()
        for i, p in zip(idxs.tolist(), out):
            preds[i] = p
    return preds


def read_manifest(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def binary_metrics(y_true: list[int], y_pred: list[int]) -> dict:
    """Index 0 = tomato_leaf (dương), index 1 = not_tomato_leaf (âm)."""
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)

    def safe(num, den):
        return num / den if den else float("nan")

    return {
        "n": len(y_true),
        "accuracy": safe(tp + tn, len(y_true)),
        "tomato_leaf": {
            "n": tp + fn,
            "recall": safe(tp, tp + fn),
            "precision": safe(tp, tp + fp),
            "bi_chan_oan": fn,
        },
        "not_tomato_leaf": {
            "n": tn + fp,
            "recall": safe(tn, tn + fp),
            "precision": safe(tn, tn + fn),
            "lot_luoi": fp,
        },
        "confusion": {"tp": tp, "fn": fn, "tn": tn, "fp": fp},
    }


def run(checkpoint: Path, gate_manifest: Path, split_csv: Path,
        negative_manifest: Path, plantdoc_manifest: Path, out_dir: Path) -> None:
    device = get_device()
    model, ckpt = load_checkpoint(str(checkpoint), device)
    keys: list[str] = ckpt["class_keys"]
    if keys != [POSITIVE_LABEL, NEGATIVE_LABEL]:
        raise SystemExit(f"Checkpoint có class_keys lạ: {keys}")
    transform = build_infer_transform(ckpt.get("image_size", 224))
    report: dict = {"checkpoint": str(checkpoint), "model_version": ckpt.get("model_version")}

    # ---- A. Tập test riêng của bộ chặn -------------------------------------
    gate_rows = [r for r in read_manifest(gate_manifest) if r["split"] == "test"]
    paths = [Path(r["path"]) for r in gate_rows]
    y_true = [0 if r["label"] == POSITIVE_LABEL else 1 for r in gate_rows]
    y_pred = predict_paths(model, paths, transform, device)
    report["A_gate_test"] = binary_metrics(y_true, y_pred)

    # ---- B. Toàn bộ tập test PlantVillage ----------------------------------
    pv_rows = [r for r in read_manifest(split_csv) if r["split"] == "test"]
    pv_paths = [Path(r["path"]) for r in pv_rows]
    pv_pred = predict_paths(model, pv_paths, transform, device)
    blocked = [r for r, p in zip(pv_rows, pv_pred) if p == 1]
    by_disease: dict[str, int] = defaultdict(int)
    for r in blocked:
        by_disease[r["label"]] += 1
    report["B_plantvillage_test"] = {
        "n": len(pv_rows),
        "bi_chan_oan": len(blocked),
        "ty_le_chan_oan": len(blocked) / len(pv_rows),
        "recall_tomato_leaf": 1 - len(blocked) / len(pv_rows),
        "theo_lop_benh": dict(sorted(by_disease.items(), key=lambda kv: -kv[1])),
        "vi_du_bi_chan": [r["path"] for r in blocked[:10]],
    }

    # ---- C. Toàn bộ bộ ảnh âm #91 ------------------------------------------
    neg_rows = read_manifest(negative_manifest)
    neg_split = {r["path"]: r["split"]
                 for r in read_manifest(gate_manifest) if r["label"] == NEGATIVE_LABEL}
    neg_paths = [Path(r["path"]) for r in neg_rows]
    neg_pred = predict_paths(model, neg_paths, transform, device)

    per_group: dict[str, dict] = defaultdict(lambda: {"n": 0, "lot": 0, "n_test": 0, "lot_test": 0})
    leaked_examples: list[str] = []
    for r, p in zip(neg_rows, neg_pred):
        g = per_group[r["group"]]
        g["n"] += 1
        is_test = neg_split.get(r["path"].replace("\\", "/")) == "test"
        if is_test:
            g["n_test"] += 1
        if p == 0:  # bị coi là lá cà chua -> lọt lưới
            g["lot"] += 1
            if is_test:
                g["lot_test"] += 1
            if len(leaked_examples) < 15:
                leaked_examples.append(r["path"])

    for g in per_group.values():
        g["ty_le_lot"] = g["lot"] / g["n"] if g["n"] else float("nan")
        g["ty_le_lot_test"] = g["lot_test"] / g["n_test"] if g["n_test"] else float("nan")

    total_leak = sum(g["lot"] for g in per_group.values())
    report["C_bo_am"] = {
        "n": len(neg_rows),
        "lot_luoi": total_leak,
        "recall_not_tomato_leaf_toan_bo": 1 - total_leak / len(neg_rows),
        "theo_nhom": {k: dict(v) for k, v in sorted(per_group.items())},
        "vi_du_lot_luoi": leaked_examples,
    }

    # ---- D. PlantDoc: phép thử trên lá thật ngoài đồng ----------------------
    if plantdoc_manifest.exists():
        pd_rows = read_manifest(plantdoc_manifest)
        pd_pred = predict_paths(model, [Path(r["path"]) for r in pd_rows], transform, device)

        def summarize(rows_pred: list[tuple[dict, int]]) -> dict:
            if not rows_pred:
                return {}
            blocked = [r for r, p in rows_pred if p == 1]
            per_disease: dict[str, dict] = defaultdict(lambda: {"n": 0, "bi_chan": 0})
            for r, p in rows_pred:
                per_disease[r["label"]]["n"] += 1
                if p == 1:
                    per_disease[r["label"]]["bi_chan"] += 1
            return {
                "n": len(rows_pred),
                "bi_chan_oan": len(blocked),
                "ty_le_chan_oan": len(blocked) / len(rows_pred),
                "recall_tomato_leaf": 1 - len(blocked) / len(rows_pred),
                "theo_lop_benh": {k: dict(v) for k, v in sorted(per_disease.items())},
            }

        paired = list(zip(pd_rows, pd_pred))
        report["D1_plantdoc_test_sach"] = summarize(
            [(r, p) for r, p in paired if "/test/" in r["path"]])
        report["D1_plantdoc_test_sach"]["ghi_chu"] = (
            "Thước đo SẠCH: thư mục test gốc của PlantDoc, chưa từng vào huấn "
            "luyện bộ chặn dưới bất kỳ hình thức nào. Đây là con số phải trích "
            "khi báo cáo."
        )
        report["D2_plantdoc_toan_bo_NHIEM"] = summarize(paired)
        report["D2_plantdoc_toan_bo_NHIEM"]["ghi_chu"] = (
            "⚠️ NHIỄM — 674/742 ảnh này nằm trong tập huấn luyện của bộ chặn "
            "(thư mục train gốc). Giữ lại chỉ để so với hai bản trước khi dùng "
            "PlantDoc (0,0795 và 0,3477), TUYỆT ĐỐI không trích như số đo."
        )
    else:
        report["D1_plantdoc_test_sach"] = {"bỏ_qua": f"không thấy {plantdoc_manifest}"}

    ensure_dir(out_dir)
    (out_dir / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---- In ra cho người đọc ------------------------------------------------
    a = report["A_gate_test"]
    print(f"\n=== A. Tập test riêng của bộ chặn (n={a['n']}) ===")
    print(f"  accuracy              {a['accuracy']:.4f}")
    print(f"  recall tomato_leaf    {a['tomato_leaf']['recall']:.4f}  "
          f"(ngưỡng #92: >= 0,98 -> {'ĐẠT' if a['tomato_leaf']['recall'] >= 0.98 else 'KHÔNG ĐẠT'})"
          f"  [chặn oan {a['tomato_leaf']['bi_chan_oan']}/{a['tomato_leaf']['n']}]")
    print(f"  recall not_tomato_leaf {a['not_tomato_leaf']['recall']:.4f}  "
          f"(không có ngưỡng cứng)  [lọt {a['not_tomato_leaf']['lot_luoi']}/{a['not_tomato_leaf']['n']}]")

    b = report["B_plantvillage_test"]
    print(f"\n=== B. Toàn bộ test PlantVillage (n={b['n']}) ===")
    print(f"  bị chặn oan: {b['bi_chan_oan']} ảnh ({b['ty_le_chan_oan'] * 100:.2f}%)"
          f"  -> recall lá = {b['recall_tomato_leaf']:.4f}")
    if b["theo_lop_benh"]:
        print("  theo lớp bệnh:", dict(list(b["theo_lop_benh"].items())[:5]))

    c = report["C_bo_am"]
    print(f"\n=== C. Toàn bộ bộ ảnh âm #91 (n={c['n']}) ===")
    print(f"  lọt lưới: {c['lot_luoi']} ảnh  -> recall lớp âm = {c['recall_not_tomato_leaf_toan_bo']:.4f}")
    print(f"  {'nhóm':22s} {'lọt/tổng':>10s} {'lọt/test':>10s}   (cột test trung thực hơn, n nhỏ)")
    for name, g in c["theo_nhom"].items():
        print(f"  {name:22s} {g['lot']:4d}/{g['n']:<5d} {g['lot_test']:4d}/{g['n_test']:<5d}")
    d1 = report["D1_plantdoc_test_sach"]
    if "bỏ_qua" not in d1:
        print(f"\n=== D1. PlantDoc test — {d1['n']} ảnh lá THẬT, THƯỚC ĐO SẠCH ===")
        print(f"  bị chặn oan: {d1['bi_chan_oan']} ảnh ({d1['ty_le_chan_oan'] * 100:.1f}%)"
              f"  -> recall lá = {d1['recall_tomato_leaf']:.4f}")
        d2 = report["D2_plantdoc_toan_bo_NHIEM"]
        print(f"\n=== D2. PlantDoc toàn bộ {d2['n']} ảnh — ⚠️ NHIỄM, chỉ để so mốc cũ ===")
        print(f"  recall lá = {d2['recall_tomato_leaf']:.4f}  "
              f"(674/742 ảnh nằm trong tập huấn luyện — đừng trích số này)")

    print(f"\nGhi {out_dir / 'report.json'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--checkpoint", type=Path, default=Path("checkpoints/organ_gate.pt"))
    ap.add_argument("--gate-manifest", type=Path, default=Path("data/processed/gate-split.csv"))
    ap.add_argument("--split-csv", type=Path, default=Path("data/processed/split.csv"))
    ap.add_argument("--negative-manifest", type=Path, default=Path("data/negative/manifest.csv"))
    ap.add_argument("--plantdoc-manifest", type=Path,
                    default=Path("data/processed/plantdoc-all/split.csv"))
    ap.add_argument("--out-dir", type=Path, default=Path("outputs/gate"))
    args = ap.parse_args()
    run(args.checkpoint, args.gate_manifest, args.split_csv,
        args.negative_manifest, args.plantdoc_manifest, args.out_dir)
