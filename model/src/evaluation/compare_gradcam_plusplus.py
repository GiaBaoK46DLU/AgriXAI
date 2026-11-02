"""Đối chiếu Grad-CAM / Grad-CAM++ trên toàn bộ mẫu cố định của #17.

Chạy từ model/: python -m src.evaluation.compare_gradcam_plusplus
Mặt nạ tham chiếu do AI khoanh mù, chưa được chuyên gia xác nhận. Không
diễn giải các chỉ số vùng này thành độ chính xác chẩn đoán ngoài đồng.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import inspect
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import matplotlib
import numpy as np
import torch
from PIL import Image

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.data.dataset import build_infer_transform
from src.evaluation.compare_xai import bootstrap, dump, read_samples, sha256, spatial_metrics
from src.labels import class_keys
from src.models.build import load_checkpoint, target_layer_for_gradcam
from src.predictor import DiseasePredictor
from src.xai.gradcam import GradCAM
from src.xai.gradcam_plusplus import GradCAMPlusPlus

ROOT = Path(__file__).resolve().parents[2]
METHODS = {"gradcam": GradCAM, "gradcam_plusplus": GradCAMPlusPlus}


def text_sha256(path: Path) -> str:
    """Hash văn bản theo LF để Git trên Windows/Linux không làm sai bằng chứng."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def normalize(raw: np.ndarray) -> np.ndarray:
    return (raw - raw.min()) / (raw.max() - raw.min() + 1e-8)


def region_metrics(heatmap: np.ndarray, annotation: dict, rendered_mask: np.ndarray) -> dict:
    """Đo trên lưới tham chiếu; contour đo ở đúng kích thước ảnh gốc."""
    result = spatial_metrics(heatmap, annotation)
    if not result["valid_map"] or annotation.get("co_van_de_du_lieu", False):
        return {**result, **{k: None for k in ("leaf_concentration", "peak_in_leaf",
                                             "peak_on_lesion", "overlay_outside_leaf", "overlay_lesion_iou")}}
    grid = np.array([list(r) for r in annotation["luoi"]])
    leaf = grid != "N"
    lesion = grid == "V"
    # Giống #17: điểm nóng lấy từ trung bình mỗi ô trên lưới 14x14.
    cells = heatmap.reshape(grid.shape[0], heatmap.shape[0] // grid.shape[0],
                            grid.shape[1], heatmap.shape[1] // grid.shape[1]).mean((1, 3))
    peak = np.unravel_index(cells.argmax(), cells.shape)
    full_leaf = cv2.resize(leaf.astype(np.uint8), rendered_mask.shape[::-1], interpolation=cv2.INTER_NEAREST).astype(bool)
    full_lesion = cv2.resize(lesion.astype(np.uint8), rendered_mask.shape[::-1], interpolation=cv2.INTER_NEAREST).astype(bool)
    localized = annotation.get("kieu_trieu_chung") == "cuc_bo" and lesion.any()
    union = (rendered_mask | full_lesion).sum()
    result.update(leaf_concentration=result["leaf_mass"] / float(leaf.mean()),
                  peak_in_leaf=float(leaf[peak]),
                  peak_on_lesion=float(lesion[peak]) if localized else None,
                  overlay_outside_leaf=float((rendered_mask & ~full_leaf).sum() / rendered_mask.sum()) if rendered_mask.any() else None,
                  overlay_lesion_iou=float((rendered_mask & full_lesion).sum() / union) if localized and union else None)
    return result


def summarize(records: list[dict]) -> dict:
    metrics = ("leaf_mass", "leaf_lift", "leaf_concentration", "peak_in_leaf",
               "lesion_mass", "lesion_lift", "peak_on_lesion", "overlay_outside_leaf",
               "overlay_lesion_iou", "explain_ms", "reference_max_error", "reference_overlay_iou")
    result = {"by_dataset": {}, "paired_plusplus_minus_gradcam": {}}
    by_id = {(r["sample_id"], r["method"]): r for r in records}
    lesion_metrics = {"lesion_mass", "lesion_lift", "peak_on_lesion", "overlay_lesion_iou"}
    for dataset in ("all", "pv", "pd"):
        subset = [r for r in records if dataset == "all" or r["dataset"] == dataset]
        result["by_dataset"][dataset] = {}
        for method in METHODS:
            rows = [r for r in subset if r["method"] == method]
            stats = {"n_images": len(rows), "empty_maps": sum(not r["valid_map"] for r in rows)}
            for metric in metrics:
                # La/vet benh là hai câu hỏi khác nhau: chỉ đánh giá vết bệnh
                # lớp dự đoán trên ảnh phân loại đúng và triệu chứng khu trú.
                values = [r[metric] for r in rows if r.get(metric) is not None
                          and (metric not in lesion_metrics or r["correct"])]
                if values:
                    stats[metric] = bootstrap(values)
            result["by_dataset"][dataset][method] = stats
        differences = {}
        for metric in metrics:
            pairs = [(r, by_id[(r["sample_id"], "gradcam_plusplus")])
                     for r in subset if r["method"] == "gradcam"]
            values = [b[metric] - a[metric] for a, b in pairs
                      if a.get(metric) is not None and b.get(metric) is not None
                      and (metric not in lesion_metrics or a["correct"])]
            if values:
                differences[metric] = bootstrap(values)
        result["paired_plusplus_minus_gradcam"][dataset] = differences
    return result


def figure(image, annotation, maps, overlays, row, target, confidence, path):
    fig, axes = plt.subplots(1, 6, figsize=(15, 3.2))
    panels = [np.array(image.resize((224, 224))), None, None, None,
              np.array(overlays["gradcam"].resize((224, 224))),
              np.array(overlays["gradcam_plusplus"].resize((224, 224)))]
    grid = np.array([list(r) for r in annotation["luoi"]])
    colors = {"N": (45, 45, 45), "L": (70, 170, 90), "V": (230, 160, 35)}
    panels[1] = np.array([[colors[c] for c in line] for line in grid], dtype=np.uint8)
    for i, method in enumerate(METHODS, 2):
        base = np.asarray(image.resize((224, 224)), dtype=np.float32) / 255
        panels[i] = np.clip(.55 * base + .45 * plt.get_cmap("jet")(maps[method])[..., :3], 0, 1)
    titles = ["Ảnh gốc", "Tham chiếu AI\nVàng: vết; xanh: lá", "Grad-CAM", "Grad-CAM++",
              "Contour Grad-CAM", "Contour Grad-CAM++"]
    for ax, panel, title in zip(axes, panels, titles):
        ax.imshow(panel)
        ax.set_title(title, fontsize=9)
        ax.axis("off")
    fig.suptitle(f"{row['sample_id']} · nhãn: {row['label']} · dự đoán: {target} ({confidence:.1%})",
                 color="green" if target == row["label"] else "firebrick", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def run(args):
    from pytorch_grad_cam import GradCAMPlusPlus as Reference
    from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

    # Gọi đúng code tạo contour của sản phẩm, không tự vẽ phiên bản gần giống.
    sys.path.insert(0, str(ROOT.parent / "backend"))
    from app.services.xai.overlay import draw_regions

    torch.set_num_threads(args.threads)
    torch.set_num_interop_threads(1)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    device = torch.device(args.device)
    out = Path(args.out)
    if (out / "protocol.json").exists():
        raise FileExistsError("Thư mục đã có thực nghiệm; chọn --out mới để không ghi đè bằng chứng.")
    for directory in (out, out / "maps", out / "figures"):
        directory.mkdir(parents=True, exist_ok=True)
    samples = read_samples()
    model, checkpoint = load_checkpoint(args.checkpoint, device)
    assert checkpoint["class_keys"] == class_keys(), "Sai thứ tự lớp checkpoint"
    before = {key: value.detach().clone() for key, value in model.state_dict().items()}
    transform = build_infer_transform(checkpoint["image_size"])
    source_paths = [Path(__file__), ROOT / "src/xai/gradcam.py", ROOT / "src/xai/gradcam_plusplus.py",
                    ROOT / "src/predictor.py", ROOT / "src/evaluation/compare_xai.py",
                    ROOT / "src/data/dataset.py", ROOT / "src/models/build.py",
                    ROOT.parent / "backend/app/services/xai/overlay.py",
                    ROOT.parent / "backend/app/services/xai/explain.py"]
    protocol = {"checkpoint_sha256": sha256(Path(args.checkpoint)), "model_version": checkpoint["model_version"],
                "device": str(device), "threads": args.threads, "repeats": args.repeats,
                "overlay_threshold": args.threshold, "reference_version": importlib.metadata.version("grad-cam"),
                "reference_source_sha256": sha256(Path(inspect.getfile(Reference))),
                "started_utc": datetime.now(timezone.utc).isoformat(),
                "text_hash_mode": "sha256, CRLF normalized to LF",
                "sources_sha256": {p.relative_to(ROOT.parent).as_posix(): text_sha256(p) for p in source_paths},
                "torch": torch.__version__, "numpy": np.__version__, "opencv": cv2.__version__,
                "platform": platform.platform(), "python": sys.version,
                "samples": [{k: v for k, v in r.items() if k != "annotation"} for r in samples],
                "annotation_sha256": {ds: text_sha256(ROOT / f"outputs/audit-gradcam-17/{ds}/khoanh-tay.json") for ds in ("pv", "pd")}}
    dump(out / "protocol.json", protocol)
    cams = {name: cls(model, target_layer_for_gradcam(model, checkpoint["arch"])) for name, cls in METHODS.items()}
    reference = Reference(model, [target_layer_for_gradcam(model, checkpoint["arch"])])
    records = []
    def synchronize():
        if device.type == "cuda":
            torch.cuda.synchronize()
    try:
        warm = transform(Image.open(ROOT / samples[0]["path"]).convert("RGB"))[None].to(device)
        for cam in cams.values():
            for _ in range(3):
                cam(warm)
        for i, row in enumerate(samples):
            image = Image.open(ROOT / row["path"]).convert("RGB")
            x = transform(image)[None].to(device)
            with torch.no_grad():
                probabilities = torch.softmax(model(x), 1)
            target = int(probabilities.argmax())
            target_key = checkpoint["class_keys"][target]
            confidence = float(probabilities[0, target])
            maps, overlays, saved = {}, {}, {}
            # Luân phiên thứ tự để giảm thiên lệch do đo một phương pháp luôn trước.
            ordered = list(cams.items())
            if i % 2:
                ordered.reverse()
            for method, cam in ordered:
                times = []
                for _ in range(args.repeats):
                    synchronize()
                    started = time.perf_counter()
                    raw = cam(x, target, normalize=False)[0]
                    synchronize()
                    times.append((time.perf_counter() - started) * 1000)
                heatmap = normalize(raw)
                maps[method] = heatmap
                full = DiseasePredictor._resize_heatmap(heatmap, *image.size)
                overlays[method] = draw_regions(image, full, args.threshold)
                # Đo cả nét viền và vùng tô mà nông dân thật sự nhìn thấy.
                black_overlay = draw_regions(Image.new("RGB", image.size), full, args.threshold)
                rendered_mask = np.asarray(black_overlay).any(2)
                record = {"sample_id": row["sample_id"], "dataset": row["dataset"], "label": row["label"],
                          "predicted": target_key, "correct": target_key == row["label"], "confidence": confidence,
                          "method": method, "explain_ms": float(np.mean(times)), "timings_ms": times,
                          **region_metrics(heatmap, row["annotation"], rendered_mask)}
                if method == "gradcam_plusplus":
                    expected = reference(x, [ClassifierOutputTarget(target)])[0]
                    record["reference_max_error"] = float(abs(expected - heatmap).max())
                    union = ( (expected >= args.threshold) | (heatmap >= args.threshold)).sum()
                    record["reference_overlay_iou"] = float(((expected >= args.threshold) & (heatmap >= args.threshold)).sum() / union) if union else 1.0
                    if record["reference_max_error"] > 2e-4:
                        raise AssertionError(f"Không khớp thư viện đối chứng: {row['sample_id']}")
                records.append(record)
                saved[method], saved[method + "_raw"] = heatmap, raw
            with torch.no_grad():
                after = torch.softmax(model(x), 1)
            torch.testing.assert_close(after, probabilities, rtol=0, atol=0)
            np.savez_compressed(out / "maps" / f"{row['sample_id']}.npz", **saved)
            figure(image, row["annotation"], maps, overlays, row, target_key, confidence,
                   out / "figures" / f"{row['sample_id']}.png")
            print(f"{i+1}/{len(samples)} {row['sample_id']}", flush=True)
        for key, value in model.state_dict().items():
            torch.testing.assert_close(value, before[key], rtol=0, atol=0)
    finally:
        for cam in cams.values():
            cam.close()
        reference.activations_and_grads.release()
    dump(out / "per-image.json", records)
    result = summarize(records)
    result.update(classification_unchanged=True, model_parameters_unchanged=True,
                  image_count=len(samples), record_count=len(records),
                  completed_utc=datetime.now(timezone.utc).isoformat())
    dump(out / "summary.json", result)
    print(f"Đã ghi {out / 'summary.json'}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", default="checkpoints/leaf_disease_detection_model.pt")
    parser.add_argument("--out", default="outputs/gradcam-plus-plus-98")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--threshold", type=float, default=.62)
    args = parser.parse_args()
    if args.repeats < 1 or not 0 < args.threshold < 1:
        parser.error("repeats phải >= 1 và threshold phải nằm trong (0, 1)")
    run(args)


if __name__ == "__main__":
    main()
