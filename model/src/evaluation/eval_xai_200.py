"""Đánh giá Grad-CAM++ (đối chứng Grad-CAM) trên bộ 200 ảnh mới, checkpoint đang triển khai.

Chạy từ model/:  python -m src.evaluation.eval_xai_200 <lệnh> --help

    sample     chọn 200 ảnh từ test-inventory của checkpoint đã thích nghi miền,
               loại 56 ảnh của #17/#122/#98 và mọi ảnh trùng băm với dữ liệu huấn luyện
    run        đo từng ảnh (đồng thuận, độ trung thực, Average Drop, độ bền); chạy tiếp được
    mprt       sanity check ngẫu nhiên hoá tham số theo tầng (cascading)
    summarize  bootstrap theo ảnh, chênh lệch ghép cặp Grad-CAM++ − Grad-CAM

Không có mặt nạ lá/vết bệnh cho bộ này nên không đo các chỉ số định vị theo vùng tham chiếu.
Định nghĩa chỉ số và cách lấp (trung bình, làm mờ, ROAD) lấy nguyên từ extend_xai_eval.py.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from skimage.segmentation import slic

from src.data.dataset import build_infer_transform
from src.evaluation import extend_xai_eval as E
from src.evaluation.compare_xai import ROOT, Predictor, bootstrap, dump, sha256
from src.labels import class_keys
from src.models.build import load_checkpoint, target_layer_for_gradcam
from src.xai.gradcam_plusplus import create_cam

CHECKPOINT = ROOT / "checkpoints/leaf_disease_domain_adapted.pt"
GATE = ROOT / "checkpoints/organ_gate.pt"
INVENTORY = ROOT / "outputs/domain-50-20261104-b8"
OLD_SAMPLES = (ROOT / "outputs/audit-gradcam-17/mau-pv.csv", ROOT / "outputs/audit-gradcam-17/mau-pd.csv")
DEFAULT_OUT = ROOT / "outputs/xai-eval-200"
METHODS = ("gradcam_plusplus", "gradcam")   # phương pháp được đánh giá đứng trước
REFERENCE = "gradcam_plusplus"
TOTAL = 200
SAMPLE_SEED = 20261128
UNITS = ("slic", "grid")
FILLS = ("mean", "blur", "road")
SUBSETS = ("all", "pv", "pd", "correct", "wrong", "gate_pass")


# --------------------------------------------------------------------------- chọn ảnh

def allocate(total: int, classes: list[str], seed: int) -> dict[str, int]:
    """Chia đều ``total`` cho các lớp; phần dư trao cho các lớp chọn ngẫu nhiên có seed."""
    base, extra = divmod(total, len(classes))
    lucky = set(np.random.default_rng(seed).permutation(sorted(classes))[:extra])
    return {c: base + (c in lucky) for c in sorted(classes)}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_sample(out: Path) -> list[dict]:
    """Bộ 200 ảnh: toàn bộ ảnh PlantDoc test còn lại + ảnh PlantVillage test chia đều 10 lớp."""
    load = lambda name: json.loads((INVENTORY / name).read_text(encoding="utf-8"))
    test = load("test-inventory.json")
    calibration = load("bn-calibration-inventory.json")
    seen = load("training-inventory.json") + load("rehearsal-inventory.json") + [
        r for rows in calibration.values() for r in rows]
    seen_hashes = {r["sha256"] for r in seen}

    old_paths, old_hashes = set(), set()
    for csv_path in OLD_SAMPLES:
        for row in csv.DictReader(csv_path.open(encoding="utf-8-sig")):
            old_paths.add(row["path"])
            old_hashes.add(file_sha256(ROOT / row["path"]))

    candidates, used_hashes, dropped = [], set(), {"old_56": 0, "seen_in_training": 0, "duplicate": 0}
    for row in sorted(test, key=lambda r: r["path"]):
        if row["path"] in old_paths or row["sha256"] in old_hashes:
            dropped["old_56"] += 1
        elif row["sha256"] in seen_hashes:
            dropped["seen_in_training"] += 1
        elif row["sha256"] in used_hashes:
            dropped["duplicate"] += 1
        else:
            used_hashes.add(row["sha256"])
            candidates.append(row)

    pd_rows = [r for r in candidates if r["source"] == "plantdoc"]
    pv_rows = [r for r in candidates if r["source"] == "plantvillage"]
    quota = allocate(TOTAL - len(pd_rows), sorted({r["label"] for r in pv_rows}), SAMPLE_SEED)
    rng = np.random.default_rng(SAMPLE_SEED)
    chosen = list(pd_rows)
    for label, k in quota.items():
        pool = [r for r in pv_rows if r["label"] == label]
        chosen += [pool[i] for i in sorted(rng.choice(len(pool), size=k, replace=False))]

    samples, counters = [], {}
    for row in chosen:
        dataset = "pd" if row["source"] == "plantdoc" else "pv"
        actual = file_sha256(ROOT / row["path"])
        if actual != row["sha256"]:
            raise ValueError(f"Băm file khác inventory: {row['path']}")
        key = (dataset, row["label"])
        counters[key] = counters.get(key, 0) + 1
        samples.append({"sample_id": f"{dataset}-{row['label']}-{counters[key]}", "dataset": dataset,
                        "label": row["label"], "path": row["path"], "sha256": actual})
    if len(samples) != TOTAL or len({s["sha256"] for s in samples}) != TOTAL:
        raise ValueError("Bộ ảnh không đủ 200 ảnh phân biệt")
    if {s["path"] for s in samples} & old_paths or {s["sha256"] for s in samples} & (old_hashes | seen_hashes):
        raise ValueError("Bộ ảnh mới trùng bộ 56 hoặc dữ liệu huấn luyện")

    out.mkdir(parents=True, exist_ok=True)
    with (out / "samples.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(samples[0]))
        writer.writeheader()
        writer.writerows(samples)
    dump(out / "sampling.json", {
        "seed": SAMPLE_SEED, "total": TOTAL, "pool": "test-inventory.json của domain-50-20261104-b8",
        "dropped": dropped, "plantdoc": len(pd_rows), "plantvillage_quota": quota,
        "checks": ["băm file khớp inventory", "không trùng đường dẫn/băm với 56 ảnh #17",
                   "không trùng băm với training, rehearsal, bn-calibration inventory"]})
    print(f"Đã chọn {len(samples)} ảnh: {len(pd_rows)} PlantDoc + {TOTAL - len(pd_rows)} PlantVillage; bỏ {dropped}")
    return samples


# --------------------------------------------------------------------------- dữ liệu & mô hình

class Context:
    """Checkpoint đang triển khai + bộ chặn lá + 200 ảnh 224×224 (resize thẳng như suy luận thật)."""

    def __init__(self, out: Path, device: str, threads: int = 4, limit: int | None = None):
        torch.set_num_threads(threads)
        torch.backends.cudnn.benchmark = False
        torch.backends.cudnn.deterministic = True
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        self.device = torch.device(device)
        self.model, checkpoint = load_checkpoint(CHECKPOINT, self.device)
        if checkpoint["class_keys"] != class_keys():
            raise ValueError("Thứ tự lớp checkpoint không khớp danh mục")
        self.arch, self.size = checkpoint["arch"], checkpoint["image_size"]
        self.model_version = checkpoint.get("model_version", CHECKPOINT.stem)
        self.predictor = Predictor(self.model, self.device, 32)
        self.gate, gate_ckpt = load_checkpoint(GATE, self.device)
        self.gate_keys = gate_ckpt["class_keys"]
        self.gate_transform = build_infer_transform(gate_ckpt.get("image_size", 224))
        rows = list(csv.DictReader((out / "samples.csv").open(encoding="utf-8-sig")))[:limit]
        self.samples = [self._load(row) for row in rows]

    def _load(self, row: dict) -> dict:
        original = Image.open(ROOT / row["path"]).convert("RGB")
        image = np.asarray(original.resize((self.size, self.size), Image.Resampling.BILINEAR))
        probabilities = self.predictor(image[None])[0]
        target = int(probabilities.argmax())
        with torch.inference_mode():
            gate = torch.softmax(self.gate(self.gate_transform(original).unsqueeze(0).to(self.device)), 1)[0]
        leaf_probability = float(gate[self.gate_keys.index("tomato_leaf")])
        return {**row, "image": image, "target": target, "predicted": class_keys()[target],
                "correct": class_keys()[target] == row["label"], "target_probability": float(probabilities[target]),
                "gate_leaf_probability": leaf_probability,
                "gate_pass": self.gate_keys[int(gate.argmax())] == "tomato_leaf",
                "segments": slic(image, n_segments=50, compactness=10, sigma=1, start_label=0),
                "baseline": np.broadcast_to(image.mean((0, 1)).astype(np.uint8), image.shape).copy()}

    def fresh_model(self) -> nn.Module:
        return load_checkpoint(CHECKPOINT, self.device)[0].eval()

    def cam(self, method: str, image: np.ndarray, target: int, model: nn.Module | None = None) -> np.ndarray:
        model = self.model if model is None else model
        with create_cam(model, target_layer_for_gradcam(model, self.arch), method) as cam:
            return cam(self.predictor.tensor(image[None]), class_idx=target)[0]


META = ("sample_id", "dataset", "label", "path", "predicted", "correct", "target_probability",
        "gate_leaf_probability", "gate_pass")


def write_protocol(out: Path, name: str, ctx: Context, params: dict) -> None:
    versions = {}
    for package in ("torch", "torchvision", "numpy", "scipy", "scikit-image", "opencv-python"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    dump(out / name / "protocol.json", {
        "experiment": name, "started_utc": datetime.now(timezone.utc).isoformat(),
        "checkpoint": str(CHECKPOINT.relative_to(ROOT)), "checkpoint_sha256": sha256(CHECKPOINT),
        "gate": str(GATE.relative_to(ROOT)), "gate_sha256": sha256(GATE), "model_version": ctx.model_version,
        "device": str(ctx.device), "gpu": torch.cuda.get_device_name() if torch.cuda.is_available() else None,
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "script_sha256": sha256(Path(__file__)), "metric_library_sha256": sha256(Path(E.__file__)),
        "python": platform.python_version(), "versions": versions,
        "sample_ids": [s["sample_id"] for s in ctx.samples], "params": params})


# --------------------------------------------------------------------------- đo từng ảnh

def measure(ctx: Context, sample: dict, number: int, blur_sigma: float) -> dict:
    image, target = sample["image"], sample["target"]
    maps = {m: ctx.cam(m, image, target) for m in METHODS}
    record = {k: sample[k] for k in META}
    record["determinism_max_abs_diff"] = {
        m: float(np.abs(ctx.cam(m, image, target) - maps[m]).max()) for m in METHODS}
    record["agreement"] = {}
    for unit in UNITS:
        index = E.unit_index(sample["segments"] if unit == "slic" else None, image.shape[:2])
        record["agreement"][unit] = E.agreement(E.unit_scores(maps[METHODS[0]], index),
                                                E.unit_scores(maps[METHODS[1]], index))

    blurred = cv2.GaussianBlur(image, (0, 0), sigmaX=blur_sigma)
    original = float(ctx.predictor(image[None])[0, target])
    perturbed = E.perturbations(image, 104729 + number)
    labels = {}
    for name, changed in perturbed.items():
        p = ctx.predictor(changed[None])[0]
        labels[name] = {"predicted": class_keys()[int(p.argmax())], "label_kept": int(p.argmax()) == target}
    record["perturbation_labels"] = labels

    record["methods"] = {}
    for method in METHODS:
        heatmap = maps[method]
        entry = {"empty": E.normalized(heatmap) is None, "faithfulness": {}, "drop": {}, "robustness": {}}
        for unit in UNITS:
            for how in FILLS:
                # Cùng seed nhiễu ROAD cho cả hai phương pháp trên cùng ảnh.
                entry["faithfulness"][f"{unit}|{how}"] = E.curves(ctx, sample, heatmap, unit, how, blurred,
                                                                  7919 * number)
        inputs = E.masked_inputs(image, heatmap, sample["baseline"])
        if inputs is not None:
            probs = ctx.predictor(np.stack([inputs["multiply"], inputs["keep_top15"]]))[:, target]
            for variant, probability in zip(("multiply", "keep_top15"), probs):
                drop, increase = E.drop_and_increase(original, float(probability))
                entry["drop"][variant] = {"drop": drop, "increase": increase,
                                          "masked_probability": float(probability)}
        for name, changed in perturbed.items():
            entry["robustness"][name] = (E.map_distance(heatmap, ctx.cam(method, changed, target))
                                         if labels[name]["label_kept"] else None)
        record["methods"][method] = entry
    return record


def run_records(ctx: Context, out: Path, blur_sigma: float) -> None:
    records = out / "records"
    records.mkdir(parents=True, exist_ok=True)
    write_protocol(out, "run", ctx, {"blur_sigma": blur_sigma, "units": UNITS, "fills": FILLS,
                                     "overlay_threshold": E.OVERLAY_THRESHOLD, "grid": E.GRID})
    for number, sample in enumerate(ctx.samples):
        path = records / f"{sample['sample_id']}.json"
        if path.exists():
            continue
        dump(path, measure(ctx, sample, number, blur_sigma))
        print(f"run {number + 1}/{len(ctx.samples)} {sample['sample_id']}", flush=True)


def run_mprt(ctx: Context, out: Path) -> None:
    """Cascading MPRT: cùng seed theo bước cho cả hai phương pháp → cùng một mô hình ngẫu nhiên."""
    write_protocol(out, "mprt", ctx, {"mode": "matched", "seed_rule": "1000 + step"})
    rows, order = [], E.layer_order(ctx.model)
    for method in METHODS:
        model = ctx.fresh_model()
        originals = {s["sample_id"]: ctx.cam(method, s["image"], s["target"]) for s in ctx.samples}
        for step, layer in enumerate(order, 1):
            E.randomize_(model.get_submodule(layer), 1000 + step, "matched")
            for sample in ctx.samples:
                original = originals[sample["sample_id"]]
                randomized = ctx.cam(method, sample["image"], sample["target"], model)
                row = {k: sample[k] for k in ("sample_id", "dataset", "correct", "gate_pass")}
                row.update(method=method, step=step, layer=layer, **E.map_similarity(original, randomized),
                           randomized_empty=100.0 if float(randomized.max()) <= 1e-12 else 0.0)
                rows.append(row)
            print(f"MPRT {method} bước {step}/{len(order)} ({layer})", flush=True)
    dump(out / "mprt" / "per-image.json", rows)


# --------------------------------------------------------------------------- tổng hợp

def subset(rows: list[dict], name: str) -> list[dict]:
    if name == "all":
        return rows
    if name in ("pv", "pd"):
        return [r for r in rows if r["dataset"] == name]
    if name == "gate_pass":
        return [r for r in rows if r["gate_pass"]]
    return [r for r in rows if r["correct"] == (name == "correct")]


def flatten(record: dict) -> list[dict]:
    """Một dòng/phương pháp/ảnh với mọi chỉ số; độ bền lấy trung bình và trường hợp xấu nhất."""
    rows = []
    for method, entry in record["methods"].items():
        row = {k: record[k] for k in META}
        row["method"] = method
        for setting, values in entry["faithfulness"].items():
            for metric, value in values.items():
                row[f"{setting}|{metric}"] = value
        for variant, values in entry["drop"].items():
            for metric, value in values.items():
                row[f"{metric}_{variant}"] = value
        kept = {n: v for n, v in entry["robustness"].items() if v is not None}
        for metric in ("contour_iou", "rel_l2", "one_minus_spearman"):
            values = [v[metric] for v in kept.values() if v[metric] is not None]
            row[f"avg_{metric}"] = float(np.mean(values)) if values else None
        ious = [v["contour_iou"] for v in kept.values() if v["contour_iou"] is not None]
        row["worst_contour_iou"] = float(min(ious)) if ious else None
        for name, values in entry["robustness"].items():
            row[f"{name}|contour_iou"] = None if values is None else values["contour_iou"]
        rows.append(row)
    return rows


def add_wins(rows: list[dict]) -> None:
    """Win%: phương pháp có Drop thấp hơn trên cùng ảnh; hoà thì chia đều."""
    by_sample = {}
    for row in rows:
        by_sample.setdefault(row["sample_id"], []).append(row)
    for group in by_sample.values():
        for variant in ("multiply", "keep_top15"):
            drops = {r["method"]: r.get(f"drop_{variant}") for r in group}
            valid = {m: d for m, d in drops.items() if d is not None}
            best = min(valid.values()) if valid else None
            winners = [m for m, d in valid.items() if np.isclose(d, best)]
            for r in group:
                r[f"win_{variant}"] = (100.0 / len(winners) if r["method"] in winners else 0.0) if valid else None


def summarize_rows(rows: list[dict], group: str, metrics: list[str]) -> dict:
    result = {}
    for name in SUBSETS:
        chosen = subset(rows, name)
        result[name] = {}
        for key in dict.fromkeys(r[group] for r in rows):
            selected = [r for r in chosen if r[group] == key]
            result[name][key] = {m: bootstrap(v) for m in metrics
                                 if (v := [r[m] for r in selected if r.get(m) is not None])}
    return result


def paired_rows(rows: list[dict], metrics: list[str], match: tuple[str, ...] = ("sample_id",)) -> dict:
    """Chênh lệch ghép cặp theo ảnh: Grad-CAM++ − Grad-CAM, cho từng tập con."""
    keyed = {(*(r[m] for m in match), r["method"]): r for r in rows}
    result = {}
    for name in SUBSETS:
        result[name] = {}
        for metric in metrics:
            diffs = []
            for r in subset(rows, name):
                if r["method"] != REFERENCE:
                    continue
                other = keyed.get((*(r[m] for m in match), METHODS[1]))
                if other and r.get(metric) is not None and other.get(metric) is not None:
                    diffs.append(r[metric] - other[metric])
            if diffs:
                result[name][metric] = bootstrap(diffs)
    return result


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = list(dict.fromkeys(k for r in rows for k in r))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def run_summarize(out: Path) -> dict:
    records = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((out / "records").glob("*.json"))]
    rows = [row for record in records for row in flatten(record)]
    add_wins(rows)
    write_csv(out / "per-image.csv", rows)
    perturbations = list(records[0]["methods"][METHODS[0]]["robustness"])
    metrics = ([f"{u}|{f}|{m}" for u in UNITS for f in FILLS for m in ("deletion_auc", "insertion_auc", "gap")]
               + [f"{p}_{v}" for v in ("multiply", "keep_top15") for p in ("drop", "increase", "win")]
               + ["avg_contour_iou", "worst_contour_iou", "avg_rel_l2", "avg_one_minus_spearman"]
               + [f"{p}|contour_iou" for p in perturbations])
    agreement_rows = [{**{k: r[k] for k in META}, "unit": unit, **values}
                      for r in records for unit, values in r["agreement"].items()]
    summary = {
        "n_images": len(records),
        "composition": {d: sum(r["dataset"] == d for r in records) for d in ("pv", "pd")},
        "classification": {name: {"n": len(s), "correct": sum(r["correct"] for r in s)}
                           for name in ("all", "pv", "pd")
                           for s in [[r for r in records if name == "all" or r["dataset"] == name]]},
        "gate_pass": {d: sum(r["gate_pass"] for r in records if r["dataset"] == d) for d in ("pv", "pd")},
        "determinism_max_abs_diff": {m: max(r["determinism_max_abs_diff"][m] for r in records) for m in METHODS},
        "empty_maps": {m: sum(r["methods"][m]["empty"] for r in records) for m in METHODS},
        "label_flips": {p: sum(not r["perturbation_labels"][p]["label_kept"] for r in records) for p in perturbations},
        "summary": summarize_rows(rows, "method", metrics),
        "paired_gradcampp_minus_gradcam": paired_rows(rows, metrics),
        "agreement": summarize_rows(agreement_rows, "unit", ["spearman", "top20_agreement"]),
    }
    mprt_path = out / "mprt" / "per-image.json"
    if mprt_path.exists():
        mprt_rows = json.loads(mprt_path.read_text(encoding="utf-8"))
        for r in mprt_rows:
            r["group"] = f"{r['method']}|{r['step']:02d}|{r['layer']}"
        summary["mprt"] = summarize_rows(mprt_rows, "group", ["spearman", "ssim", "hog_pearson", "randomized_empty"])
        write_csv(out / "mprt" / "per-image.csv", mprt_rows)
    dump(out / "summary.json", summary)
    print(f"Tổng hợp {len(records)} ảnh → {out / 'summary.json'}")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("sample", "run", "mprt", "summarize"))
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--limit", type=int, default=None, help="chỉ dùng N ảnh đầu (chạy thử)")
    parser.add_argument("--blur-sigma", type=float, default=10.0)
    args = parser.parse_args()
    if args.command == "sample":
        run_sample(args.out)
    elif args.command == "summarize":
        run_summarize(args.out)
    else:
        ctx = Context(args.out, args.device, args.threads, args.limit)
        (run_records if args.command == "run" else lambda c, o, *_: run_mprt(c, o))(ctx, args.out, args.blur_sigma)


if __name__ == "__main__":
    main()
