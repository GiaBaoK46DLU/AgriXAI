"""Đánh giá XAI mở rộng cho #122: năm phép đo bổ sung trên cùng 56 ảnh.

Chạy từ model/:  python -m src.evaluation.extend_xai_eval <lệnh> --help

    agreement    mức đồng thuận giữa các phương pháp (Krishna et al., TMLR 2024)
    mprt         sanity check ngẫu nhiên hoá tham số (Adebayo 2018; Smooth/eMPRT 2024)
    drop         Average Drop / Increase in Confidence (Chattopadhay 2018)
    faithfulness deletion/insertion với ba cách lấp: trung bình, làm mờ, ROAD (Rong 2022)
    sensitivity  độ bền trước nhiễu kiểu ảnh điện thoại (Avg/Max-Sensitivity, Yeh 2019)

Giữ nguyên thiết kế #122: cùng checkpoint, cùng ảnh 224×224 đã lưu, cùng lớp mục tiêu
(lớp dự đoán trên ảnh gốc), cùng SLIC và nền trung bình. Bản đồ LIME/Kernel SHAP 3 seed
đọc lại từ #122, không tính lại; Grad-CAM/Grad-CAM++ tính lại và đối chiếu với bản đã lưu.
Tổng hợp: trung bình theo seed trên từng ảnh rồi bootstrap theo ảnh, như #122.
"""
from __future__ import annotations

import argparse
import csv
import importlib.metadata
import io
import itertools
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
from scipy import sparse
from scipy.sparse.linalg import splu
from scipy.stats import spearmanr
from skimage.feature import hog
from skimage.metrics import structural_similarity
from skimage.segmentation import slic

from src.evaluation.compare_xai import (
    ROOT,
    Predictor,
    bootstrap,
    dump,
    explain,
    read_samples,
    sha256,
    top_fraction_weights,
)
from src.labels import class_keys
from src.models.build import load_checkpoint, target_layer_for_gradcam
from src.xai.gradcam_plusplus import create_cam

BASE = ROOT / "outputs/xai-comparison-122/quality"
PLUSPLUS_MAPS = ROOT / "outputs/gradcam-plus-plus-98/maps"
CHECKPOINT = ROOT / "checkpoints/leaf_disease_detection_model.pt"
DEFAULT_OUT = ROOT / "outputs/xai-evaluation-ext"
CAM_METHODS = ("gradcam", "gradcam_plusplus")
SAMPLED_METHODS = ("lime", "kernel_shap")
METHODS = CAM_METHODS + SAMPLED_METHODS
SEEDS = (42, 123, 2026)
GRID = 14                      # cùng độ phân giải lưới khoanh tay của #17
BUDGET = 1000                  # ngân sách LIME/Kernel SHAP như #122
OVERLAY_THRESHOLD = 0.62       # OVERLAY_DRAW_THRESHOLD của backend
SUBSETS = ("all", "pv", "pd", "correct", "wrong")


# --------------------------------------------------------------------------- tiện ích chung

def normalized(heatmap: np.ndarray) -> np.ndarray | None:
    """Chia cho giá trị lớn nhất; bản đồ rỗng trả None thay vì chia cho 0."""
    peak = float(np.max(heatmap))
    return None if peak <= 1e-12 else (np.asarray(heatmap, np.float64) / peak)


def unit_index(segments: np.ndarray | None, shape: tuple[int, int]) -> np.ndarray:
    """Chỉ số đơn vị so sánh cho từng pixel: vùng SLIC hoặc ô lưới 14×14."""
    if segments is not None:
        return segments
    h, w = shape
    if h % GRID or w % GRID:
        raise ValueError("Kích thước ảnh không chia hết cho lưới")
    return (np.arange(h)[:, None] // (h // GRID)) * GRID + np.arange(w)[None, :] // (w // GRID)


def unit_scores(heatmap: np.ndarray, index: np.ndarray) -> np.ndarray:
    """Mật độ trung bình trên mỗi đơn vị (không ưu tiên vùng SLIC to)."""
    count = int(index.max()) + 1
    sizes = np.bincount(index.ravel(), minlength=count)
    return np.bincount(index.ravel(), weights=np.asarray(heatmap, np.float64).ravel(),
                       minlength=count) / np.maximum(sizes, 1)


def subset_rows(rows: list[dict], subset: str) -> list[dict]:
    if subset == "all":
        return rows
    if subset in ("pv", "pd"):
        return [r for r in rows if r["dataset"] == subset]
    return [r for r in rows if r["correct"] == (subset == "correct")]


def summarize(rows: list[dict], group: str, metrics: tuple[str, ...]) -> dict:
    """Bootstrap theo ảnh cho từng nhóm (phương pháp/cặp) × tập con."""
    result = {}
    for subset in SUBSETS:
        chosen = subset_rows(rows, subset)
        result[subset] = {}
        for key in dict.fromkeys(r[group] for r in rows):
            selected = [r for r in chosen if r[group] == key]
            entry = {}
            for metric in metrics:
                values = [r[metric] for r in selected if r.get(metric) is not None]
                if values:
                    entry[metric] = bootstrap(values)
            result[subset][key] = entry
    return result


def paired(rows: list[dict], metrics: tuple[str, ...], reference: str = "gradcam",
           group: str = "method", match: tuple[str, ...] = ("sample_id",)) -> dict:
    """Chênh lệch ghép cặp theo ảnh: reference − phương pháp khác."""
    keyed = {(*(r[m] for m in match), r[group]): r for r in rows}
    result = {}
    for other in dict.fromkeys(r[group] for r in rows):
        if other == reference:
            continue
        result[other] = {}
        for metric in metrics:
            values = []
            for r in rows:
                if r[group] != reference:
                    continue
                o = keyed.get((*(r[m] for m in match), other))
                if o and r.get(metric) is not None and o.get(metric) is not None:
                    values.append(r[metric] - o[metric])
            if values:
                result[other][metric] = bootstrap(values)
    return result


def write_rows(path: Path, rows: list[dict]) -> None:
    dump(path.with_suffix(".json"), rows)
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with path.with_suffix(".csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


# --------------------------------------------------------------------------- dữ liệu & mô hình

class Context:
    """Nạp checkpoint, 56 ảnh và bản đồ của #122/#98; kiểm khớp trước khi đo."""

    def __init__(self, device: str, threads: int = 4, batch_size: int = 32, limit: int | None = None):
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
        self.model_version = checkpoint["model_version"]
        self.predictor = Predictor(self.model, self.device, batch_size)
        self._cache: dict = {}
        self.samples = []
        for row in read_samples()[:limit]:
            sid = row["sample_id"]
            image = np.asarray(Image.open(BASE / "images" / f"{sid}.png").convert("RGB"))
            raw = np.asarray(Image.open(ROOT / row["path"]).convert("RGB").resize(
                (self.size, self.size), Image.Resampling.BILINEAR))
            if not np.array_equal(image, raw):
                raise ValueError(f"Ảnh lưu của #122 không khớp ảnh gốc: {sid}")
            record = json.loads((BASE / "records" / f"{sid}--gradcam--42.json").read_text(encoding="utf-8"))
            row.update(image=image, target=class_keys().index(record["predicted"]),
                       predicted=record["predicted"], correct=bool(record["correct"]),
                       segments=np.load(BASE / "maps" / f"{sid}--segments.npz")["segments"],
                       baseline=np.broadcast_to(image.mean((0, 1)).astype(np.uint8), image.shape).copy())
            self.samples.append(row)

    def fresh_model(self) -> nn.Module:
        """Bản mô hình riêng để ngẫu nhiên hoá; nạp lại thay vì deepcopy (tránh chép hook đếm)."""
        return load_checkpoint(CHECKPOINT, self.device)[0].eval()

    def cam(self, method: str, image: np.ndarray, target: int, model: nn.Module | None = None) -> np.ndarray:
        model = self.model if model is None else model
        with create_cam(model, target_layer_for_gradcam(model, self.arch), method) as cam:
            return cam(self.predictor.tensor(image[None]), class_idx=target)[0]

    def maps(self, sample: dict, method: str) -> dict:
        """{seed: bản đồ}; phương pháp xác định trả {None: bản đồ}."""
        sid = sample["sample_id"]
        if method in CAM_METHODS:
            key = sid, method
            if key not in self._cache:
                self._cache[key] = self.cam(method, sample["image"], sample["target"])
            return {None: self._cache[key]}
        return {seed: np.load(BASE / "maps" / f"{sid}--{method}--{seed}.npz")["heatmap"] for seed in SEEDS}

    def validate_cams(self) -> dict:
        """Grad-CAM tính lại phải khớp #122 (GPU), Grad-CAM++ khớp #98 (CPU)."""
        diffs = {"gradcam_vs_122": [], "gradcam_plusplus_vs_98": []}
        for sample in self.samples:
            sid = sample["sample_id"]
            diffs["gradcam_vs_122"].append(float(np.abs(self.maps(sample, "gradcam")[None] - np.load(
                BASE / "maps" / f"{sid}--gradcam--42.npz")["heatmap"]).max()))
            diffs["gradcam_plusplus_vs_98"].append(float(np.abs(self.maps(sample, "gradcam_plusplus")[None] - np.load(
                PLUSPLUS_MAPS / f"{sid}.npz")["gradcam_plusplus"]).max()))
        return {k: max(v) for k, v in diffs.items()}


def write_protocol(out: Path, name: str, ctx: Context, params: dict) -> None:
    packages = ("torch", "torchvision", "numpy", "scipy", "scikit-image", "opencv-python", "lime", "shap")
    versions = {}
    for package in packages:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    dump(out / "protocol.json", {
        "experiment": name, "started_utc": datetime.now(timezone.utc).isoformat(),
        "checkpoint": str(CHECKPOINT.relative_to(ROOT)), "checkpoint_sha256": sha256(CHECKPOINT),
        "model_version": ctx.model_version, "device": str(ctx.device),
        "gpu": torch.cuda.get_device_name() if torch.cuda.is_available() else None,
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "script_sha256": sha256(Path(__file__)), "python": platform.python_version(),
        "versions": versions, "sample_ids": [s["sample_id"] for s in ctx.samples],
        "source_maps": {"lime_kernel_shap_gradcam": str(BASE.relative_to(ROOT)),
                        "gradcam_plusplus_reference": str(PLUSPLUS_MAPS.relative_to(ROOT))},
        "params": params})


# --------------------------------------------------------------------------- 2. đồng thuận

PAIRS = (("gradcam", "gradcam_plusplus"), ("gradcam", "lime"), ("gradcam", "kernel_shap"),
         ("gradcam_plusplus", "lime"), ("gradcam_plusplus", "kernel_shap"), ("lime", "kernel_shap"))


def agreement(a: np.ndarray, b: np.ndarray, fraction: float = 0.2) -> dict:
    """Spearman giữa thứ hạng đơn vị và tỉ lệ trùng top 20% (feature agreement)."""
    constant = np.ptp(a) == 0 or np.ptp(b) == 0
    top_a, top_b = top_fraction_weights(a, fraction), top_fraction_weights(b, fraction)
    return {"spearman": None if constant else float(spearmanr(a, b).statistic),
            "top20_agreement": None if constant else float(np.minimum(top_a, top_b).sum() / top_a.sum())}


def map_pairs(first: dict, second: dict) -> list[tuple[np.ndarray, np.ndarray]]:
    """Ghép bản đồ: cùng seed nếu cả hai lấy mẫu; mỗi seed với bản đồ xác định nếu không."""
    if None in first and None in second:
        return [(first[None], second[None])]
    if None in first:
        return [(first[None], m) for m in second.values()]
    if None in second:
        return [(m, second[None]) for m in first.values()]
    return [(first[s], second[s]) for s in SEEDS]


def run_agreement(ctx: Context, out: Path) -> dict:
    rows = []
    for sample in ctx.samples:
        maps = {m: ctx.maps(sample, m) for m in METHODS}
        for unit in ("slic", "grid"):
            index = unit_index(sample["segments"] if unit == "slic" else None, sample["image"].shape[:2])
            comparisons = [(f"{a}~{b}", map_pairs(maps[a], maps[b])) for a, b in PAIRS]
            # Trần tham chiếu: hai seed khác nhau của cùng phương pháp lấy mẫu.
            comparisons += [(f"{m}~{m}(seed)", [(maps[m][s], maps[m][t]) for s, t in itertools.combinations(SEEDS, 2)])
                            for m in SAMPLED_METHODS]
            for pair, couples in comparisons:
                values = [agreement(unit_scores(a, index), unit_scores(b, index)) for a, b in couples]
                row = {k: sample[k] for k in ("sample_id", "dataset", "correct")}
                row.update(unit=unit, pair=pair, group=f"{unit}|{pair}",
                           n_degenerate=sum(v["spearman"] is None for v in values))
                for metric in ("spearman", "top20_agreement"):
                    valid = [v[metric] for v in values if v[metric] is not None]
                    row[metric] = float(np.mean(valid)) if valid else None
                rows.append(row)
    write_rows(out / "per-image", rows)
    summary = {"summary": summarize(rows, "group", ("spearman", "top20_agreement")),
               "degenerate_pairs": sum(r["n_degenerate"] for r in rows)}
    dump(out / "summary.json", summary)
    return summary


# --------------------------------------------------------------------------- 3. MPRT

def layer_order(model: nn.Module) -> list[str]:
    """Từ đầu ra ngược về đầu vào: classifier → features[8] → … → features[0]."""
    return ["classifier"] + [f"features.{i}" for i in reversed(range(len(model.features)))]


INIT_MODES = ("matched", "reset_keep_bn")


def randomize_(module: nn.Module, seed: int, mode: str = "matched") -> None:
    """Ngẫu nhiên hoá Conv/Linear của một khối; BatchNorm giữ nguyên ở cả hai chế độ.

    ``matched`` (mặc định): lấy mẫu N(mean, std) của chính tensor đã huấn luyện —
    phá cấu trúc đã học nhưng giữ thang giá trị, nên tín hiệu ảnh còn lan được qua
    mạng. ``reset_keep_bn``: ``reset_parameters()`` mặc định của PyTorch. Chẩn đoán
    cho thấy chế độ này làm đầu ra ngừng thay đổi từ bước 4 (BN đã huấn luyện đặt trên
    trọng số thang khác xoá tín hiệu tầng dưới), nên chỉ chạy để đối chứng.
    """
    generator = torch.Generator().manual_seed(seed)
    torch.manual_seed(seed)
    for layer in module.modules():
        if not isinstance(layer, (nn.Conv2d, nn.Linear)):
            continue
        if mode == "reset_keep_bn":
            layer.reset_parameters()
            continue
        if mode != "matched":
            raise ValueError(mode)
        for parameter in (layer.weight, layer.bias):
            if parameter is None:
                continue
            data = parameter.data
            std = float(data.std()) if data.numel() > 1 else 0.0
            sample = torch.randn(data.shape, generator=generator) * std + float(data.mean())
            data.copy_(sample.to(data.device, data.dtype))


def propagation(ctx: Context, mode: str) -> list[dict]:
    """Chẩn đoán: activation tầng Grad-CAM còn phụ thuộc ảnh và còn đổi theo từng bước không."""
    model, captured = ctx.fresh_model(), {}
    handle = model.features[-1].register_forward_hook(lambda m, i, o: captured.__setitem__("a", o.detach()))
    first, other = (ctx.predictor.tensor(ctx.samples[i]["image"][None]) for i in (0, len(ctx.samples) - 1))
    corr = lambda u, v: float(torch.corrcoef(torch.stack([u.flatten(), v.flatten()]))[0, 1])
    rows, previous = [], None
    with torch.inference_mode():
        for step, layer in enumerate(layer_order(model), 1):
            randomize_(model.get_submodule(layer), 1000 + step, mode)
            model(first)
            a = captured["a"][0].clone()
            model(other)
            b = captured["a"][0].clone()
            rows.append({"step": step, "layer": layer, "spatial_std": float(a.std(dim=(1, 2)).mean()),
                         "corr_two_images": corr(a, b),
                         "corr_previous_step": None if previous is None else corr(a, previous)})
            previous = a
    handle.remove()
    return rows


def map_similarity(a: np.ndarray, b: np.ndarray) -> dict:
    """Ba độ đo của Adebayo et al.: Spearman, SSIM, tương quan HOG."""
    a, b = np.asarray(a, np.float64), np.asarray(b, np.float64)
    result = {"ssim": float(structural_similarity(a, b, data_range=1.0))}
    result["spearman"] = None if np.ptp(a) == 0 or np.ptp(b) == 0 else float(spearmanr(a.ravel(), b.ravel()).statistic)
    ha, hb = (hog(m, pixels_per_cell=(16, 16), cells_per_block=(2, 2)) for m in (a, b))
    result["hog_pearson"] = None if np.ptp(ha) == 0 or np.ptp(hb) == 0 else float(np.corrcoef(ha, hb)[0, 1])
    return result


def entropy(heatmap: np.ndarray) -> float | None:
    """Độ phức tạp (Shannon) của bản đồ coi như phân phối; dùng cho eMPRT."""
    total = float(np.sum(heatmap))
    if total <= 1e-12:
        return None
    p = np.asarray(heatmap, np.float64).ravel() / total
    p = p[p > 0]
    return float(-(p * np.log(p)).sum())


def smooth_cam(ctx: Context, method: str, image: np.ndarray, target: int, model: nn.Module,
               n: int, sigma: float, seed: int) -> np.ndarray:
    """Smooth MPRT: trung bình bản đồ trên n bản ảnh thêm nhiễu Gaussian rồi chuẩn hoá lại."""
    x = ctx.predictor.tensor(image[None])
    generator = torch.Generator(device=x.device).manual_seed(seed)
    noisy = x.repeat(n, 1, 1, 1)
    noisy = noisy + torch.randn(noisy.shape, generator=generator, device=x.device) * sigma * float(x.max() - x.min())
    with create_cam(model, target_layer_for_gradcam(model, ctx.arch), method) as cam:
        mean = cam(noisy, class_idx=target).mean(0)
    low, high = float(mean.min()), float(mean.max())
    return (mean - low) / (high - low + 1e-8)


def saturation_check(ctx: Context, mode: str) -> dict:
    """Vì sao bỏ MPRT cho LIME/SHAP: xác suất của mô hình ngẫu nhiên hoàn toàn có bão hoà không."""
    model = ctx.fresh_model()
    for step, layer in enumerate(layer_order(model), 1):
        randomize_(model.get_submodule(layer), 1000 + step, mode)
    with torch.inference_mode():
        logits = model(ctx.predictor.tensor(np.stack([s["image"] for s in ctx.samples])))
    probabilities = logits.softmax(1)
    return {"reason": "softmax bão hoà trên mô hình ngẫu nhiên hoàn toàn; LIME/SHAP giải thích xác suất",
            "logit_min": float(logits.min()), "logit_max": float(logits.max()),
            "max_probability_min": float(probabilities.max(1).values.min()),
            "distinct_argmax": sorted({int(i) for i in logits.argmax(1)})}


def run_mprt(ctx: Context, out: Path, smooth_n: int, smooth_sigma: float, mode: str = "matched") -> dict:
    rows, order = [], layer_order(ctx.model)
    for method in CAM_METHODS:
        model = ctx.fresh_model()
        originals = {s["sample_id"]: (ctx.maps(s, method)[None],
                                      smooth_cam(ctx, method, s["image"], s["target"], model, smooth_n,
                                                 smooth_sigma, number))
                     for number, s in enumerate(ctx.samples)}
        for step, layer in enumerate(order, 1):
            # Cùng seed theo bước cho mọi phương pháp → cùng một mô hình ngẫu nhiên.
            randomize_(model.get_submodule(layer), 1000 + step, mode)
            for number, sample in enumerate(ctx.samples):
                original, original_smooth = originals[sample["sample_id"]]
                randomized = ctx.cam(method, sample["image"], sample["target"], model)
                smooth = smooth_cam(ctx, method, sample["image"], sample["target"], model,
                                    smooth_n, smooth_sigma, number)
                row = {k: sample[k] for k in ("sample_id", "dataset", "correct")}
                row.update(method=method, step=step, layer=layer, group=f"{method}|{step:02d}|{layer}",
                           **map_similarity(original, randomized),
                           smooth_spearman=map_similarity(original_smooth, smooth)["spearman"],
                           # Bản đồ rỗng (ReLU cắt hết) làm Spearman không xác định; đếm riêng,
                           # không âm thầm bỏ khỏi trung bình.
                           randomized_empty=100.0 if float(randomized.max()) <= 1e-12 else 0.0,
                           entropy_ratio=None)
                if (base := entropy(original)) and (now := entropy(randomized)) is not None:
                    row["entropy_ratio"] = now / base
                rows.append(row)
            print(f"MPRT {method} bước {step}/{len(order)} ({layer})", flush=True)
    # Không chạy MPRT cho LIME/Kernel SHAP: trên mô hình ngẫu nhiên hoàn toàn, logit cỡ
    # −3,7e6 làm softmax bão hoà thành one-hot cố định, nên hai phương pháp giải thích
    # xác suất luôn ra bản đồ rỗng — phép thử suy biến, không mang thông tin; forward
    # cũng chậm ~10 phút/ảnh. Grad-CAM/Grad-CAM++ dùng gradient logit và chuẩn hoá bản đồ
    # nên không bị ảnh hưởng. Bằng chứng ghi trong summary["sampled_methods_note"].
    write_rows(out / "per-image", rows)
    summary = {"layer_order": order, "init_mode": mode,
               "propagation_diagnostics": {m: propagation(ctx, m) for m in INIT_MODES},
               "sampled_methods_note": saturation_check(ctx, mode),
               "summary": summarize(rows, "group", ("spearman", "ssim", "hog_pearson", "smooth_spearman",
                                                     "randomized_empty", "entropy_ratio"))}
    dump(out / "summary.json", summary)
    return summary


# --------------------------------------------------------------------------- 4. Average Drop

def masked_inputs(image: np.ndarray, heatmap: np.ndarray, baseline: np.ndarray) -> dict | None:
    """Hai biến thể: nhân theo điểm (Grad-CAM++) và chỉ giữ top 15% pixel (Score-CAM)."""
    unit = normalized(heatmap)
    if unit is None:
        return None
    keep = top_fraction_weights(heatmap, 0.15)[..., None]
    image = image.astype(np.float64)
    return {"multiply": image * unit[..., None],
            "keep_top15": keep * image + (1 - keep) * baseline.astype(np.float64)}


def drop_and_increase(original: float, masked: float) -> tuple[float, float]:
    """Average Drop (% giảm tương đối, chỉ phần giảm) và Increase (1 nếu tăng)."""
    return max(0.0, original - masked) / original * 100, 100.0 if masked > original else 0.0


def run_drop(ctx: Context, out: Path) -> dict:
    rows = []
    for sample in ctx.samples:
        target = sample["target"]
        original = float(ctx.predictor(sample["image"][None])[0, target])
        per_method = {}
        for method in METHODS:
            scores = {"multiply": [], "keep_top15": []}
            for heatmap in ctx.maps(sample, method).values():
                inputs = masked_inputs(sample["image"], heatmap, sample["baseline"])
                if inputs is None:
                    continue
                probabilities = ctx.predictor(np.stack([inputs["multiply"], inputs["keep_top15"]]))[:, target]
                for variant, probability in zip(("multiply", "keep_top15"), probabilities):
                    scores[variant].append(drop_and_increase(original, float(probability)) + (float(probability),))
            row = {k: sample[k] for k in ("sample_id", "dataset", "correct")}
            row.update(method=method, original_probability=original)
            for variant, values in scores.items():
                row[f"drop_{variant}"] = float(np.mean([v[0] for v in values])) if values else None
                row[f"increase_{variant}"] = float(np.mean([v[1] for v in values])) if values else None
                row[f"masked_probability_{variant}"] = float(np.mean([v[2] for v in values])) if values else None
            per_method[method] = row
        for variant in ("multiply", "keep_top15"):
            # Win%: phương pháp có Drop thấp nhất trên ảnh này; hoà thì chia đều.
            drops = {m: r[f"drop_{variant}"] for m, r in per_method.items() if r[f"drop_{variant}"] is not None}
            best = min(drops.values())
            winners = [m for m, d in drops.items() if np.isclose(d, best)]
            for method, row in per_method.items():
                row[f"win_{variant}"] = 100.0 / len(winners) if method in winners else 0.0
        rows.extend(per_method.values())
    write_rows(out / "per-image", rows)
    metrics = tuple(f"{p}_{v}" for v in ("multiply", "keep_top15") for p in ("drop", "increase", "win"))
    summary = {"summary": summarize(rows, "method", metrics),
               "paired_gradcam_minus_other": paired(rows, metrics)}
    dump(out / "summary.json", summary)
    return summary


# --------------------------------------------------------------------------- 5. deletion/insertion

NEIGHBOURS = ((-1, 0, 1 / 6), (1, 0, 1 / 6), (0, -1, 1 / 6), (0, 1, 1 / 6),
              (-1, -1, 1 / 12), (-1, 1, 1 / 12), (1, -1, 1 / 12), (1, 1, 1 / 12))


def noisy_linear_impute(image: np.ndarray, removed: np.ndarray, baseline: np.ndarray,
                        noise: float = 0.01, rng: np.random.Generator | None = None) -> np.ndarray:
    """Lấp pixel bị xoá kiểu ROAD: mỗi pixel = trung bình có trọng số 8 láng giềng.

    Trọng số 1/6 cho láng giềng cạnh, 1/12 cho láng giềng chéo (Rong et al., 2022),
    chuẩn hoá lại ở mép ảnh. Giải một hệ tuyến tính thưa cho cả mặt nạ, cộng nhiễu
    Gaussian độ lệch ``noise`` (thang 0..1). Xoá toàn bộ ảnh thì hệ suy biến: dùng nền
    trung bình như #122. Trả mảng float thang 0..255, pixel giữ nguyên không đổi.
    """
    removed = np.asarray(removed, bool)
    h, w = removed.shape
    flat = image.reshape(-1, 3).astype(np.float64) / 255
    rows = np.flatnonzero(removed.ravel())
    n = rows.size
    if n == 0:
        return image.astype(np.float64)
    if n == removed.size:
        return baseline.astype(np.float64)
    lookup = np.full(h * w, -1)
    lookup[rows] = np.arange(n)
    ys, xs = np.divmod(rows, w)
    total = np.zeros(n)
    candidates = []
    for dy, dx, weight in NEIGHBOURS:
        ny, nx = ys + dy, xs + dx
        inside = (ny >= 0) & (ny < h) & (nx >= 0) & (nx < w)
        total[inside] += weight
        candidates.append((np.flatnonzero(inside), (ny * w + nx)[inside], weight))
    a_rows, a_cols, a_vals = [np.arange(n)], [np.arange(n)], [np.ones(n)]
    rhs = np.zeros((n, 3))
    for source, neighbour, weight in candidates:
        coefficient = weight / total[source]
        unknown = lookup[neighbour] >= 0
        a_rows.append(source[unknown])
        a_cols.append(lookup[neighbour[unknown]])
        a_vals.append(-coefficient[unknown])
        # Mỗi pixel xuất hiện tối đa một lần cho mỗi hướng nên cộng trực tiếp được.
        rhs[source[~unknown]] += coefficient[~unknown, None] * flat[neighbour[~unknown]]
    matrix = sparse.csc_matrix((np.concatenate(a_vals), (np.concatenate(a_rows), np.concatenate(a_cols))),
                               shape=(n, n))
    solved = splu(matrix).solve(rhs)
    if noise:
        solved = solved + (rng or np.random.default_rng(0)).normal(0, noise, solved.shape)
    result = flat.copy()
    result[rows] = np.clip(solved, 0, 1)
    return result.reshape(image.shape) * 255


def removal_schedule(heatmap: np.ndarray, index: np.ndarray) -> tuple[list[np.ndarray], list[float]]:
    """Xếp đơn vị theo mật độ giảm dần; 11 mức như #122; trục x = diện tích pixel thật."""
    count = int(index.max()) + 1
    sizes = np.bincount(index.ravel(), minlength=count)
    order = np.argsort(-unit_scores(heatmap, index), kind="stable")
    steps = np.unique(np.rint(np.linspace(0, count, 11)).astype(int))
    tops = [np.isin(index, order[:k]) for k in steps]
    return tops, [float(sizes[order[:k]].sum() / index.size) for k in steps]


def fill(image: np.ndarray, removed: np.ndarray, how: str, baseline: np.ndarray, blurred: np.ndarray,
         rng: np.random.Generator) -> np.ndarray:
    if how == "mean":
        return np.where(removed[..., None], baseline, image).astype(np.float64)
    if how == "blur":
        return np.where(removed[..., None], blurred, image).astype(np.float64)
    if how == "road":
        return noisy_linear_impute(image, removed, baseline, rng=rng)
    raise ValueError(how)


def curves(ctx: Context, sample: dict, heatmap: np.ndarray, unit: str, how: str, blurred: np.ndarray,
           seed: int) -> dict:
    """Deletion = xoá vùng quan trọng nhất trước (MoRF); insertion = chỉ giữ vùng quan trọng nhất.

    Insertion trên trục diện tích được giữ lại trùng diện tích với đường LeRF của ROAD,
    nên gap = insertion − deletion tương ứng điểm LeRF − MoRF ROAD khuyến nghị.
    """
    index = unit_index(sample["segments"] if unit == "slic" else None, sample["image"].shape[:2])
    tops, x = removal_schedule(heatmap, index)
    rng = np.random.default_rng(seed)
    images = [fill(sample["image"], top, how, sample["baseline"], blurred, rng) for top in tops]
    images += [fill(sample["image"], ~top, how, sample["baseline"], blurred, rng) for top in tops]
    probabilities = ctx.predictor(np.stack(images))[:, sample["target"]]
    deletion, insertion = probabilities[:len(tops)], probabilities[len(tops):]
    return {"deletion_auc": float(np.trapezoid(deletion, x)),
            "insertion_auc": float(np.trapezoid(insertion, x)),
            "gap": float(np.trapezoid(insertion, x) - np.trapezoid(deletion, x))}


def run_faithfulness(ctx: Context, out: Path, blur_sigma: float) -> dict:
    rows, reproduction = [], []
    for number, sample in enumerate(ctx.samples):
        blurred = cv2.GaussianBlur(sample["image"], (0, 0), sigmaX=blur_sigma)
        for method in METHODS:
            maps = ctx.maps(sample, method)
            for unit in ("slic", "grid"):
                for how in ("mean", "blur", "road"):
                    values = []
                    for seed, heatmap in maps.items():
                        result = curves(ctx, sample, heatmap, unit, how, blurred, 7919 * number + (seed or 0))
                        values.append(result)
                        if unit == "slic" and how == "mean":
                            # Cấu hình trùng #122: phải tái tạo đúng số đã lưu.
                            record = json.loads((BASE / "records" /
                                                 f'{sample["sample_id"]}--{method}--{seed or 42}.json').read_text(
                                encoding="utf-8")) if method != "gradcam_plusplus" else None
                            if record:
                                reproduction.append(max(abs(record["deletion_auc"] - result["deletion_auc"]),
                                                        abs(record["insertion_auc"] - result["insertion_auc"])))
                    row = {k: sample[k] for k in ("sample_id", "dataset", "correct")}
                    row.update(method=method, unit=unit, fill=how, setting=f"{unit}|{how}",
                               group=f"{unit}|{how}|{method}",
                               **{k: float(np.mean([v[k] for v in values])) for k in values[0]})
                    rows.append(row)
        print(f"faithfulness {number + 1}/{len(ctx.samples)} {sample['sample_id']}", flush=True)
    write_rows(out / "per-image", rows)
    metrics = ("deletion_auc", "insertion_auc", "gap")
    by_setting = {}
    for setting in dict.fromkeys(r["setting"] for r in rows):
        chosen = [r for r in rows if r["setting"] == setting]
        by_setting[setting] = paired(chosen, metrics)
    # Thứ hạng từng cấu hình: phương pháp tốt nhất theo trung bình mỗi chỉ số.
    ranking = {}
    for setting in by_setting:
        means = {m: {k: float(np.mean([r[k] for r in rows if r["setting"] == setting and r["method"] == m]))
                     for k in metrics} for m in METHODS}
        ranking[setting] = {"best_deletion": min(means, key=lambda m: means[m]["deletion_auc"]),
                            "best_insertion": max(means, key=lambda m: means[m]["insertion_auc"]),
                            "best_gap": max(means, key=lambda m: means[m]["gap"]), "means": means}
    summary = {"reproduction_max_abs_diff_vs_122": max(reproduction) if reproduction else None,
               "summary": summarize(rows, "group", metrics),
               "paired_gradcam_minus_other": by_setting, "ranking": ranking}
    dump(out / "summary.json", summary)
    return summary


# --------------------------------------------------------------------------- 6. độ bền

def jpeg(image: np.ndarray, quality: int) -> np.ndarray:
    buffer = io.BytesIO()
    Image.fromarray(image).save(buffer, format="JPEG", quality=quality)
    return np.asarray(Image.open(io.BytesIO(buffer.getvalue())).convert("RGB"))


def perturbations(image: np.ndarray, seed: int) -> dict[str, np.ndarray]:
    """Năm biến đổi kiểu chụp lại bằng điện thoại; không xoay/dịch để giữ toạ độ bản đồ."""
    rng = np.random.default_rng(seed)
    as_float = image.astype(np.float64)
    return {"sang_hon_15": np.clip(as_float * 1.15, 0, 255).astype(np.uint8),
            "toi_hon_15": np.clip(as_float * 0.85, 0, 255).astype(np.uint8),
            "jpeg_q70": jpeg(image, 70),
            "mo_sigma1": cv2.GaussianBlur(image, (0, 0), sigmaX=1.0),
            "nhieu_sd5": np.clip(as_float + rng.normal(0, 5, image.shape), 0, 255).astype(np.uint8)}


def map_distance(original: np.ndarray, changed: np.ndarray) -> dict:
    """Khoảng cách sau khi chia max: L2 tương đối, 1 − Spearman, IoU vùng app khoanh (0,62)."""
    a, b = normalized(original), normalized(changed)
    if a is None or b is None:
        return {"rel_l2": None, "one_minus_spearman": None, "contour_iou": None}
    mask_a, mask_b = a >= OVERLAY_THRESHOLD, b >= OVERLAY_THRESHOLD
    union = int((mask_a | mask_b).sum())
    rho = None if np.ptp(a) == 0 or np.ptp(b) == 0 else float(spearmanr(a.ravel(), b.ravel()).statistic)
    return {"rel_l2": float(np.linalg.norm(a - b) / np.linalg.norm(a)),
            "one_minus_spearman": None if rho is None else 1 - rho,
            "contour_iou": float((mask_a & mask_b).sum() / union) if union else None}


def run_sensitivity(ctx: Context, out: Path, validate: int) -> dict:
    records = out / "records"
    records.mkdir(parents=True, exist_ok=True)
    for number, sample in enumerate(ctx.samples):
        path = records / f'{sample["sample_id"]}.json'
        if path.exists():
            continue
        target = sample["target"]
        originals = {m: ctx.maps(sample, m) for m in METHODS}
        result = {k: sample[k] for k in ("sample_id", "dataset", "correct", "predicted")}
        result["perturbations"], result["noise_floor"], result["reproduction"] = {}, {}, {}
        for method in SAMPLED_METHODS:
            # Sàn nhiễu: cùng ảnh, chỉ đổi seed lấy mẫu (seed 42 so với 123 và 2026).
            floors = [map_distance(originals[method][42], originals[method][s]) for s in (123, 2026)]
            result["noise_floor"][method] = {k: (float(np.mean(v)) if (v := [f[k] for f in floors if f[k] is not None])
                                                 else None) for k in floors[0]}
            if number < validate:
                again, _ = explain(method, ctx.predictor, sample["image"], sample["segments"], sample["baseline"],
                                   target, 42, BUDGET, ctx.arch)
                result["reproduction"][method] = float(np.abs(again - originals[method][42]).max())
        for name, image in perturbations(sample["image"], 104729 + number).items():
            probabilities = ctx.predictor(image[None])[0]
            entry = {"predicted": class_keys()[int(probabilities.argmax())],
                     "label_kept": int(probabilities.argmax()) == target,
                     "target_probability": float(probabilities[target]), "methods": {}}
            if entry["label_kept"]:
                # Nhãn đổi thì giải thích đổi là đúng; chỉ đo độ bền khi nhãn giữ nguyên.
                segments = slic(image, n_segments=50, compactness=10, sigma=1, start_label=0)
                baseline = np.broadcast_to(image.mean((0, 1)).astype(np.uint8), image.shape).copy()
                for method in METHODS:
                    if method in CAM_METHODS:
                        changed, reference = ctx.cam(method, image, target), originals[method][None]
                    else:
                        changed, _ = explain(method, ctx.predictor, image, segments, baseline, target, 42,
                                             BUDGET, ctx.arch)
                        reference = originals[method][42]
                    entry["methods"][method] = map_distance(reference, changed)
            result["perturbations"][name] = entry
        dump(path, result)
        print(f"sensitivity {number + 1}/{len(ctx.samples)} {sample['sample_id']}", flush=True)
    return summarize_sensitivity(out)


def summarize_sensitivity(out: Path) -> dict:
    results = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((out / "records").glob("*.json"))]
    rows, per_perturbation = [], []
    for result in results:
        kept = {n: e for n, e in result["perturbations"].items() if e["label_kept"]}
        for method in METHODS:
            row = {k: result[k] for k in ("sample_id", "dataset", "correct")}
            row.update(method=method, perturbations_kept=len(kept))
            for metric in ("rel_l2", "one_minus_spearman", "contour_iou"):
                values = [e["methods"][method][metric] for e in kept.values()
                          if e["methods"][method][metric] is not None]
                row[f"avg_{metric}"] = float(np.mean(values)) if values else None
                # "Max" = trường hợp xấu nhất: khoảng cách lớn nhất, IoU nhỏ nhất.
                worst = (min if metric == "contour_iou" else max)(values) if values else None
                row[f"worst_{metric}"] = worst
                floor = result["noise_floor"].get(method, {}).get(metric)
                row[f"floor_{metric}"] = floor
            rows.append(row)
            for name, entry in kept.items():
                per_perturbation.append({"sample_id": result["sample_id"], "dataset": result["dataset"],
                                         "correct": result["correct"], "method": method, "perturbation": name,
                                         "group": f"{name}|{method}", **entry["methods"][method]})
    write_rows(out / "per-image", rows)
    write_rows(out / "per-perturbation", per_perturbation)
    metrics = tuple(f"{p}_{m}" for m in ("rel_l2", "one_minus_spearman", "contour_iou")
                    for p in ("avg", "worst", "floor"))
    flips = {}
    for name in dict.fromkeys(n for r in results for n in r["perturbations"]):
        entries = [r["perturbations"][name] for r in results]
        flips[name] = {"n_images": len(entries), "label_changed": sum(not e["label_kept"] for e in entries)}
    reproduction = {m: max(r["reproduction"][m] for r in results if m in r["reproduction"])
                    for m in SAMPLED_METHODS if any(m in r["reproduction"] for r in results)}
    summary = {"image_count": len(results), "label_flips": flips,
               "lime_shap_reproduction_max_abs_diff": reproduction,
               "summary": summarize(rows, "method", metrics),
               "paired_gradcam_minus_other": paired(rows, metrics),
               "by_perturbation": summarize(per_perturbation, "group",
                                            ("rel_l2", "one_minus_spearman", "contour_iou"))["all"]}
    dump(out / "summary.json", summary)
    return summary


# --------------------------------------------------------------------------- CLI

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("agreement", "mprt", "drop", "faithfulness", "sensitivity"))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--limit", type=int, help="Chỉ chạy N ảnh đầu (thử nhanh); không dùng cho số liệu báo cáo")
    parser.add_argument("--smooth-n", type=int, default=10)
    parser.add_argument("--smooth-sigma", type=float, default=0.1)
    parser.add_argument("--init", choices=INIT_MODES, default="matched", help="Cách ngẫu nhiên hoá trong MPRT")
    parser.add_argument("--blur-sigma", type=float, default=10.0)
    parser.add_argument("--validate", type=int, default=6, help="Số ảnh tính lại LIME/SHAP seed 42 để kiểm tái lập")
    parser.add_argument("--summarize-only", action="store_true", help="sensitivity: chỉ tổng hợp records sẵn có")
    args = parser.parse_args()
    name = args.command if args.command != "mprt" or args.init == "matched" else f"mprt-{args.init}"
    out = Path(args.out).resolve() / name
    out.mkdir(parents=True, exist_ok=True)
    if args.command == "sensitivity" and args.summarize_only:
        print(json.dumps(summarize_sensitivity(out)["label_flips"], ensure_ascii=False))
        return
    ctx = Context(args.device, args.threads, limit=args.limit)
    params = {k: v for k, v in vars(args).items() if k not in ("out", "summarize_only")}
    params.update(cam_validation_max_abs_diff=ctx.validate_cams(), budget=BUDGET, seeds=SEEDS, grid=GRID,
                  overlay_threshold=OVERLAY_THRESHOLD,
                  mprt_randomization=f"cascading top-down, Conv2d/Linear, init={args.init}, giữ BatchNorm")
    if not (out / "protocol.json").exists() or args.command != "sensitivity":
        write_protocol(out, args.command, ctx, params)
    print("Kiểm Grad-CAM/Grad-CAM++ tính lại:", params["cam_validation_max_abs_diff"], flush=True)
    if args.command == "agreement":
        run_agreement(ctx, out)
    elif args.command == "mprt":
        run_mprt(ctx, out, args.smooth_n, args.smooth_sigma, args.init)
    elif args.command == "drop":
        run_drop(ctx, out)
    elif args.command == "faithfulness":
        run_faithfulness(ctx, out, args.blur_sigma)
    else:
        run_sensitivity(ctx, out, args.validate)
    print(f"Xong: {out}", flush=True)


if __name__ == "__main__":
    main()
