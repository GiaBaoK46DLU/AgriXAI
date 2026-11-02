"""So sánh XAI trên cùng checkpoint, ảnh và lớp dự đoán (#122).

Chạy từ model/: python -m src.evaluation.compare_xai --help.
Không thay predictor sản phẩm, không huấn luyện lại, không chọn mẫu theo kết quả.
SHAP ở đây là Kernel SHAP trên cùng các superpixel SLIC dùng cho LIME.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import itertools
import json
import os
import platform
import subprocess
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from skimage.segmentation import slic

from src.data.dataset import IMAGENET_MEAN, IMAGENET_STD
from src.labels import class_keys
from src.models.build import load_checkpoint, target_layer_for_gradcam
from src.xai.gradcam import GradCAM

ROOT = Path(__file__).resolve().parents[2]
METHODS = ("gradcam", "lime", "kernel_shap")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def read_samples() -> list[dict]:
    samples = []
    audit = ROOT / "outputs/audit-gradcam-17"
    for dataset in ("pv", "pd"):
        annotations = json.loads((audit / dataset / "khoanh-tay.json").read_text(encoding="utf-8"))["annotations"]
        with (audit / f"mau-{dataset}.csv").open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                path = ROOT / row["path"]
                if not path.is_file():
                    raise FileNotFoundError(path)
                row["image_sha256"] = sha256(path)
                row["annotation"] = annotations[row["sample_id"]]
                samples.append(row)
    return samples


def positive_density(weights: np.ndarray, segments: np.ndarray) -> np.ndarray:
    """Chia đóng góp mỗi vùng cho diện tích; bảo toàn tổng đóng góp dương."""
    positive = np.maximum(np.asarray(weights, dtype=np.float64), 0)
    counts = np.bincount(segments.ravel(), minlength=len(positive))
    return (positive / np.maximum(counts, 1))[segments].astype(np.float32)


def top_fraction_weights(heatmap: np.ndarray, fraction: float = 0.2) -> np.ndarray:
    """Vùng top 20%; chia đều trọng số ở điểm bằng nhau, không ưu tiên góc ảnh."""
    flat = np.asarray(heatmap).ravel()
    budget = fraction * flat.size
    threshold = np.partition(flat, flat.size - int(np.ceil(budget)))[flat.size - int(np.ceil(budget))]
    above = flat > threshold
    ties = flat == threshold
    result = above.astype(np.float64)
    result[ties] = (budget - int(above.sum())) / int(ties.sum())
    return result.reshape(heatmap.shape)


def spatial_metrics(heatmap: np.ndarray, annotation: dict) -> dict:
    if not np.isfinite(heatmap).all():
        raise ValueError("Bản đồ chứa NaN/Inf")
    total = float(heatmap.sum())
    if total <= 1e-12:
        return {"valid_map": False, "leaf_mass": None, "leaf_lift": None,
                "lesion_mass": None, "lesion_lift": None, "leaf_top20": None}
    grid = np.array([list(row) for row in annotation["luoi"]])
    if heatmap.shape[0] % grid.shape[0] or heatmap.shape[1] % grid.shape[1]:
        raise ValueError("Kích thước bản đồ không chia hết cho lưới gán vùng")
    grid = grid.repeat(heatmap.shape[0] // grid.shape[0], 0).repeat(heatmap.shape[1] // grid.shape[1], 1)
    leaf, lesion = grid != "N", grid == "V"
    leaf_mass = float(heatmap[leaf].sum() / total)
    area = float(leaf.mean())
    top = top_fraction_weights(heatmap)
    lesion_valid = annotation.get("kieu_trieu_chung") == "cuc_bo" and lesion.any()
    lesion_mass = float(heatmap[lesion].sum() / total) if lesion_valid else None
    lesion_area = float(lesion.mean())
    if annotation.get("co_van_de_du_lieu", False):
        # Vẫn chạy và lưu ảnh này, nhưng không dùng nhãn vùng đáng ngờ để kết luận.
        return {"valid_map": True, "leaf_mass": None, "leaf_lift": None,
                "lesion_mass": None, "lesion_lift": None, "leaf_top20": None}
    return {"valid_map": True, "leaf_mass": leaf_mass,
            "leaf_lift": (leaf_mass - area) / (1 - area) if area < 1 else None,
            "lesion_mass": lesion_mass,
            "lesion_lift": (lesion_mass - lesion_area) / (1 - lesion_area) if lesion_valid and lesion_area < 1 else None,
            "leaf_top20": float((top * leaf).sum() / top.sum())}


def stability(maps: list[np.ndarray]) -> float | None:
    valid = [m for m in maps if float(m.sum()) > 1e-12]
    if len(valid) != len(maps) or len(valid) < 2:
        return None
    top = [top_fraction_weights(m) for m in valid]
    return float(np.mean([np.minimum(a, b).sum() / np.maximum(a, b).sum()
                          for a, b in itertools.combinations(top, 2)]))


class Predictor:
    """Dự đoán có batch và bộ đếm chung cho cả ba phương pháp."""
    def __init__(self, model, device, batch_size: int):
        self.model, self.device, self.batch_size = model, device, batch_size
        self.mean = torch.tensor(IMAGENET_MEAN, device=device)[None, :, None, None]
        self.std = torch.tensor(IMAGENET_STD, device=device)[None, :, None, None]
        self.calls = self.images = 0
        self.handle = model.register_forward_pre_hook(self._count)

    def _count(self, module, args):
        self.calls += 1
        self.images += int(args[0].shape[0])

    def reset(self):
        self.calls = self.images = 0

    def tensor(self, images: np.ndarray) -> torch.Tensor:
        # PIL có thể trả mảng chỉ đọc; không để torch tham chiếu bộ nhớ không ghi được.
        x = torch.from_numpy(np.array(images, copy=True, order="C")).to(self.device, dtype=torch.float32)
        return (x.permute(0, 3, 1, 2) / 255 - self.mean) / self.std

    def __call__(self, images: np.ndarray) -> np.ndarray:
        output = []
        with torch.inference_mode():
            for start in range(0, len(images), self.batch_size):
                x = self.tensor(images[start:start + self.batch_size])
                output.append(self.model(x).softmax(1).cpu().numpy())
        return np.concatenate(output)

    def masks(self, masks: np.ndarray, image: np.ndarray, baseline: np.ndarray,
              segments: np.ndarray, target: int) -> np.ndarray:
        output = []
        for start in range(0, len(masks), self.batch_size):
            chunk = np.asarray(masks[start:start + self.batch_size])
            visible = chunk[:, segments] > 0.5
            images = np.where(visible[..., None], image[None], baseline[None])
            output.append(self(images)[:, target])
        return np.concatenate(output)

    def synchronize(self):
        if self.device.type == "cuda":
            torch.cuda.synchronize()


def explain(method: str, predictor: Predictor, image: np.ndarray, segments: np.ndarray,
            baseline: np.ndarray, target: int, seed: int, budget: int, arch: str):
    np.random.seed(seed)
    torch.manual_seed(seed)
    count = int(segments.max()) + 1
    if method == "gradcam":
        with GradCAM(predictor.model, target_layer_for_gradcam(predictor.model, arch)) as cam:
            heatmap = cam(predictor.tensor(image[None]), class_idx=target)[0]
        return heatmap, {"backward_passes": 1, "explained_score": "target_logit"}
    if method == "lime":
        from lime.lime_image import LimeImageExplainer
        explanation = LimeImageExplainer(random_state=seed, feature_selection="none").explain_instance(
            image, predictor, labels=(target,), top_labels=None,
            hide_color=baseline[0, 0], num_features=count, num_samples=budget,
            batch_size=predictor.batch_size, segmentation_fn=lambda _: segments,
            distance_metric="cosine", random_seed=seed)
        coefficients = np.zeros(count)
        for index, weight in explanation.local_exp[target]:
            coefficients[index] = weight
        return positive_density(coefficients, segments), {
            "backward_passes": 0, "explained_score": "target_probability",
            "signed_region_weights": coefficients.tolist(), "local_r2": float(explanation.score)}
    if method != "kernel_shap":
        raise ValueError(method)
    import shap
    predict_masks = lambda masks: predictor.masks(masks, image, baseline, segments, target)
    explainer = shap.KernelExplainer(predict_masks, np.zeros((1, count)), link="identity")
    coefficients = np.asarray(explainer.shap_values(
        np.ones((1, count)), nsamples=budget, l1_reg=0, silent=True)).reshape(-1)
    return positive_density(coefficients, segments), {
        "backward_passes": 0, "explained_score": "target_probability",
        "signed_region_weights": coefficients.tolist(),
        "expected_value": float(np.asarray(explainer.expected_value).item())}


def faithfulness(predictor: Predictor, heatmap: np.ndarray, image: np.ndarray,
                 baseline: np.ndarray, segments: np.ndarray, target: int) -> dict:
    """Xóa/chèn cùng các vùng SLIC; tích phân theo diện tích pixel thật sự."""
    count = int(segments.max()) + 1
    sizes = np.bincount(segments.ravel(), minlength=count)
    region_density = np.bincount(segments.ravel(), weights=heatmap.ravel(), minlength=count) / sizes
    order = np.argsort(-region_density, kind="stable")
    steps = np.unique(np.rint(np.linspace(0, count, 11)).astype(int))
    insert = np.zeros((len(steps), count), dtype=np.float64)
    for i, step in enumerate(steps):
        insert[i, order[:step]] = 1
    x = (insert @ sizes / segments.size).tolist()
    ins = predictor.masks(insert, image, baseline, segments, target)
    deletion = predictor.masks(1 - insert, image, baseline, segments, target)
    return {"insertion_auc": float(np.trapezoid(ins, x)),
            "deletion_auc": float(np.trapezoid(deletion, x)),
            "curve_area": x, "insertion_probability": ins.tolist(),
            "deletion_probability": deletion.tolist()}


def bootstrap(values: list[float], seed: int = 20261102) -> dict:
    arr = np.asarray(values, dtype=np.float64)
    rng = np.random.default_rng(seed)
    means = rng.choice(arr, size=(10000, len(arr)), replace=True).mean(1)
    return {"n_images": len(arr), "mean": float(arr.mean()), "median": float(np.median(arr)),
            "ci95": np.quantile(means, [0.025, 0.975]).tolist()}


def summarize(out: Path) -> dict:
    records = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((out / "records").glob("*.json"))]
    if not records:
        raise ValueError("Chưa có kết quả")
    metrics = ("explain_ms", "total_ms", "forward_images", "forward_calls", "leaf_mass", "leaf_lift",
               "lesion_mass", "lesion_lift", "leaf_top20", "insertion_auc", "deletion_auc", "seed_iou")
    grouped = defaultdict(list)
    for record in records:
        grouped[(record["sample_id"], record["dataset"], record["method"])].append(record)
    per_image = []
    for (sample_id, dataset, method), rows in grouped.items():
        entry = {"sample_id": sample_id, "dataset": dataset, "method": method,
                 "label": rows[0]["label"], "predicted": rows[0]["predicted"],
                 "correct": rows[0]["correct"], "n_seeds": len(rows)}
        for metric in metrics:
            values = [r[metric] for r in rows if r.get(metric) is not None]
            entry[metric] = float(np.mean(values)) if values else None
        maps = [np.load(out / "maps" / f'{sample_id}--{method}--{r["seed"]}.npz')["heatmap"] for r in rows]
        entry["seed_iou"] = stability(maps)
        per_image.append(entry)
    result = {"record_count": len(records), "image_count": len({r["sample_id"] for r in records}),
              "classification": {dataset: {"n_images": len(rows := [r for r in per_image if r["method"] == "gradcam" and r["dataset"] == dataset]),
                                            "correct": sum(r["correct"] for r in rows)} for dataset in ("pv", "pd")},
              "by_dataset": {}, "paired_differences_gradcam_minus_other": {}}
    for dataset in ("all", "pv", "pd"):
        result["by_dataset"][dataset] = {}
        for method in METHODS:
            rows = [r for r in per_image if r["method"] == method and (dataset == "all" or r["dataset"] == dataset)]
            result["by_dataset"][dataset][method] = {
                metric: bootstrap([r[metric] for r in rows if r[metric] is not None])
                for metric in metrics if any(r[metric] is not None for r in rows)}
    by_key = {(r["sample_id"], r["method"]): r for r in per_image}
    for other in METHODS[1:]:
        differences = {}
        for metric in metrics:
            pairs = [(r, by_key.get((r["sample_id"], other))) for r in per_image if r["method"] == "gradcam"]
            values = [a[metric] - b[metric] for a, b in pairs if b and a[metric] is not None and b[metric] is not None]
            if values:
                differences[metric] = bootstrap(values)
        result["paired_differences_gradcam_minus_other"][other] = differences
    dump(out / "per-image.json", per_image)
    dump(out / "summary.json", result)
    with (out / "per-image.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(per_image[0]))
        writer.writeheader()
        writer.writerows(per_image)
    return result


def run(args):
    torch.set_num_threads(args.threads)
    torch.set_num_interop_threads(1)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    device = torch.device(args.device)
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    if args.summarize_only:
        print(json.dumps(summarize(out), ensure_ascii=False))
        return
    samples = read_samples()
    if args.one_per_class:
        seen, chosen = set(), []
        for row in samples:
            key = row["dataset"], row["label"]
            if key not in seen:
                seen.add(key)
                chosen.append(row)
        samples = chosen
    if args.limit:
        samples = samples[:args.limit]
    model, checkpoint = load_checkpoint(args.checkpoint, device)
    if checkpoint["class_keys"] != class_keys():
        raise ValueError("Thứ tự lớp checkpoint không khớp danh mục")
    size = checkpoint["image_size"]
    predictor = Predictor(model, device, args.batch_size)
    source = Path(__file__).resolve()
    config = {"checkpoint_sha256": sha256(Path(args.checkpoint)), "script_sha256": sha256(source),
              "gradcam_source_sha256": sha256(ROOT / "src/xai/gradcam.py"),
              "catalog_sha256": sha256(ROOT.parent / "shared/data/tomato_diseases.json"),
              "model_version": checkpoint["model_version"], "image_size": size,
              "device": str(device), "batch_size": args.batch_size, "threads": args.threads,
              "seeds": args.seeds, "perturbations": args.budget, "slic_segments_requested": 50,
              "slic_compactness": 10, "baseline": "global image mean RGB rounded down to uint8",
              "methods": list(METHODS), "timing_only": args.timing_only,
              "sample_ids": [r["sample_id"] for r in samples]}
    protocol_path = out / "protocol.json"
    if protocol_path.exists():
        saved = json.loads(protocol_path.read_text(encoding="utf-8"))
        if saved["config"] != config:
            raise ValueError("Cấu hình/code khác lần chạy trước; dùng thư mục output mới")
    else:
        packages = ("torch", "torchvision", "numpy", "scipy", "scikit-learn", "scikit-image", "lime", "shap")
        dump(protocol_path, {"started_utc": datetime.now(timezone.utc).isoformat(), "config": config,
                             "python": platform.python_version(), "platform": platform.platform(),
                             "processor": platform.processor(), "cpu_count": os.cpu_count(),
                             "gpu": torch.cuda.get_device_name() if torch.cuda.is_available() else None,
                             "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                             "versions": {p: importlib.metadata.version(p) for p in packages},
                             "samples": samples})
    for sub in ("records", "maps", "images"):
        (out / sub).mkdir(exist_ok=True)
    # Nạp thư viện và làm nóng kernel trước đo; không tính thời gian import/load model.
    from lime.lime_image import LimeImageExplainer  # noqa: F401
    import shap  # noqa: F401
    warm = np.asarray(Image.open(ROOT / samples[0]["path"]).convert("RGB").resize((size, size), Image.Resampling.BILINEAR))
    for _ in range(5):
        predictor(warm[None])
    warm_segments = slic(warm, n_segments=50, compactness=10, sigma=1, start_label=0)
    warm_baseline = np.broadcast_to(warm.mean((0, 1)).astype(np.uint8), warm.shape).copy()
    for method in METHODS:
        explain(method, predictor, warm, warm_segments, warm_baseline, 0, 0, 128, checkpoint["arch"])
    predictor.synchronize()
    for number, sample in enumerate(samples, 1):
        image = np.asarray(Image.open(ROOT / sample["path"]).convert("RGB").resize((size, size), Image.Resampling.BILINEAR))
        Image.fromarray(image).save(out / "images" / f'{sample["sample_id"]}.png')
        probabilities = predictor(image[None])[0]
        target = int(probabilities.argmax())
        start = time.perf_counter()
        segments = slic(image, n_segments=50, compactness=10, sigma=1, start_label=0)
        segmentation_ms = (time.perf_counter() - start) * 1000
        baseline = np.broadcast_to(image.mean((0, 1)).astype(np.uint8), image.shape).copy()
        np.savez_compressed(out / "maps" / f'{sample["sample_id"]}--segments.npz', segments=segments)
        # Luân phiên thứ tự để tránh một phương pháp luôn được đo đầu/cuối.
        offset = (number - 1) % len(METHODS)
        for seed in args.seeds:
            for method in METHODS[offset:] + METHODS[:offset]:
                record_path = out / "records" / f'{sample["sample_id"]}--{method}--{seed}.json'
                if record_path.exists():
                    continue
                predictor.reset()
                predictor.synchronize()
                start = time.perf_counter()
                heatmap, extra = explain(method, predictor, image, segments, baseline, target,
                                         seed, args.budget, checkpoint["arch"])
                predictor.synchronize()
                elapsed = (time.perf_counter() - start) * 1000
                record = {k: sample[k] for k in ("sample_id", "dataset", "label", "image_sha256")}
                record.update({"method": method, "seed": seed, "predicted": class_keys()[target],
                               "correct": class_keys()[target] == sample["label"],
                               "confidence": float(probabilities[target]), "explain_ms": elapsed,
                               "segmentation_ms": segmentation_ms if method != "gradcam" else 0,
                               "total_ms": elapsed + (segmentation_ms if method != "gradcam" else 0),
                               "forward_calls": predictor.calls, "forward_images": predictor.images,
                               "n_segments": int(segments.max()) + 1, **extra})
                record.update(spatial_metrics(heatmap, sample["annotation"]))
                record["lesion_lift_all_predictions"] = record["lesion_lift"]
                if not record["correct"]:
                    # Không đánh giá định vị bệnh thật khi đang giải thích một lớp sai.
                    record["lesion_mass"] = record["lesion_lift"] = None
                if not args.timing_only:
                    record.update(faithfulness(predictor, heatmap, image, baseline, segments, target))
                np.savez_compressed(out / "maps" / f'{sample["sample_id"]}--{method}--{seed}.npz', heatmap=heatmap)
                dump(record_path, record)
                print(f'{number}/{len(samples)} {sample["sample_id"]} {method} seed={seed} {elapsed:.1f} ms', flush=True)
    predictor.handle.remove()
    summary = summarize(out)
    print(f'Hoàn tất: {summary["image_count"]} ảnh, {summary["record_count"]} bản giải thích', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", default="checkpoints/leaf_disease_detection_model.pt")
    parser.add_argument("--out", default="outputs/xai-comparison-122/quality")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--budget", type=int, default=1000)
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 123, 2026])
    parser.add_argument("--limit", type=int)
    parser.add_argument("--one-per-class", action="store_true")
    parser.add_argument("--timing-only", action="store_true")
    parser.add_argument("--summarize-only", action="store_true")
    run(parser.parse_args())


if __name__ == "__main__":
    main()
