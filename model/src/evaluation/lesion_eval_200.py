"""Chỉ số vùng lá/vết bệnh cho Grad-CAM++ và Grad-CAM trên bộ 200 ảnh (xai-eval-200).

Chạy từ model/:  python -m src.evaluation.lesion_eval_200 <lệnh>

    sheets     phiếu khoanh mù 2×2 ảnh/trang: ảnh + lưới 14×14, KHÔNG có bản đồ nhiệt
    run        đo chỉ số vùng bằng đúng ``region_metrics`` của #98 (cần khoanh-tay.json)
    summarize  bootstrap theo ảnh, chênh lệch ghép cặp Grad-CAM++ − Grad-CAM
    figures    hình cho báo cáo vào lesion/figures/ (ảnh ví dụ chọn ngẫu nhiên có seed)

Quy trình và định nghĩa giống hệt #17/#98: mặt nạ lưới 14×14 (N nền, L lá lành, V vết
bệnh), khoanh trên ảnh 224×224 mô hình nhìn thấy, chỉ số vết bệnh chỉ tính trên ảnh
đoán đúng có triệu chứng khu trú, vùng khoanh vẽ bằng ``draw_regions`` của backend.
Khác #98 duy nhất ở checkpoint (bản đang triển khai) và bộ ảnh.

Cần đặt ``DATABASE_URL=sqlite:///:memory:`` khi chạy ``run``: import ``draw_regions``
kéo theo cấu hình CSDL của backend, nhưng phép đo không đụng tới CSDL nào.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import cv2
import matplotlib
import matplotlib.patches  # noqa: F401  (dùng trong chú giải hình)
import matplotlib.patheffects  # noqa: F401
import matplotlib.ticker  # noqa: F401
import numpy as np
import torch
from PIL import Image

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src.data.dataset import build_infer_transform  # noqa: E402
from src.evaluation import compare_gradcam_plusplus as P  # noqa: E402
from src.evaluation.compare_xai import ROOT, dump, sha256  # noqa: E402
from src.evaluation.eval_xai_200 import CHECKPOINT, DEFAULT_OUT  # noqa: E402
from src.labels import class_keys  # noqa: E402
from src.models.build import load_checkpoint, target_layer_for_gradcam  # noqa: E402
from src.predictor import DiseasePredictor  # noqa: E402
from src.xai.audit_sheets import _ve_luoi  # noqa: E402

GRID = 14
THRESHOLD = 0.62
ANNOTATIONS = "khoanh-tay.json"
# Năm ảnh đã lộ bản đồ nhiệt cho người khoanh trước khi khoanh (hình báo cáo ngày
# 28/11/2026) — vẫn khoanh, nhưng báo thêm kết quả khi loại chúng ra.
SEEN_HEATMAP = ("pv-healthy-6", "pv-late_blight-10", "pd-late_blight-2",
                "pd-yellow_leaf_curl_virus-1", "pv-mosaic_virus-10")


def read_samples(base: Path) -> list[dict]:
    return list(csv.DictReader((base / "samples.csv").open(encoding="utf-8-sig")))


def run_sheets(base: Path, per_sheet: int = 4, zoom: int = 2) -> None:
    """Phiếu khoanh mù: mỗi ô ảnh là bản 224 phóng ×zoom, kẻ lưới 14×14 có đánh số."""
    out = base / "annotation" / "phieu"
    out.mkdir(parents=True, exist_ok=True)
    samples = read_samples(base)
    for start in range(0, len(samples), per_sheet):
        chunk = samples[start:start + per_sheet]
        fig, axes = plt.subplots(2, 2, figsize=(11, 11.6), dpi=100)
        for ax in axes.ravel():
            ax.axis("off")
        for ax, s in zip(axes.ravel(), chunk):
            ax.axis("on")
            img224 = Image.open(ROOT / s["path"]).convert("RGB").resize((224, 224), Image.BILINEAR)
            hi = np.asarray(img224.resize((224 * zoom, 224 * zoom), Image.LANCZOS))
            ax.imshow(hi)
            _ve_luoi(ax, GRID, hi.shape[0])
            ax.set_title(s["sample_id"], fontsize=12, fontweight="bold")
        fig.tight_layout()
        fig.savefig(out / f"phieu-{start // per_sheet + 1:03d}.png")
        plt.close(fig)
    print(f"Đã sinh {(len(samples) + per_sheet - 1) // per_sheet} phiếu vào {out}")


def load_annotations(base: Path) -> dict:
    data = json.loads((base / "annotation" / ANNOTATIONS).read_text(encoding="utf-8"))["annotations"]
    for sid, a in data.items():
        rows = a["luoi"]
        if len(rows) != GRID or any(len(r) != GRID or set(r) - set("NLV") for r in rows):
            raise ValueError(f"Lưới sai định dạng: {sid}")
        if a["kieu_trieu_chung"] not in ("cuc_bo", "khuech_tan", "khong_co_vet"):
            raise ValueError(f"Kiểu triệu chứng lạ: {sid}")
    return data


def run_regions(base: Path, device: str) -> None:
    sys.path.insert(0, str(ROOT.parent / "backend"))
    from app.services.xai.overlay import draw_regions

    annotations = load_annotations(base)
    samples = read_samples(base)
    missing = [s["sample_id"] for s in samples if s["sample_id"] not in annotations]
    if missing:
        raise ValueError(f"Chưa khoanh {len(missing)} ảnh, ví dụ {missing[:3]}")
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    dev = torch.device(device)
    model, checkpoint = load_checkpoint(CHECKPOINT, dev)
    if checkpoint["class_keys"] != class_keys():
        raise ValueError("Thứ tự lớp checkpoint không khớp danh mục")
    transform = build_infer_transform(checkpoint["image_size"])
    cams = {name: cls(model, target_layer_for_gradcam(model, checkpoint["arch"])) for name, cls in P.METHODS.items()}
    out = base / "lesion"
    (out / "maps").mkdir(parents=True, exist_ok=True)
    dump(out / "protocol.json", {
        "started_utc": datetime.now(timezone.utc).isoformat(), "checkpoint": str(CHECKPOINT.relative_to(ROOT)),
        "checkpoint_sha256": sha256(CHECKPOINT), "model_version": checkpoint.get("model_version"),
        "device": str(dev), "overlay_threshold": THRESHOLD, "grid": GRID,
        "annotation_sha256": P.text_sha256(base / "annotation" / ANNOTATIONS),
        "sources_sha256": {p.relative_to(ROOT.parent).as_posix(): P.text_sha256(p) for p in (
            Path(__file__), Path(P.__file__), ROOT / "src/xai/gradcam.py", ROOT / "src/xai/gradcam_plusplus.py",
            ROOT.parent / "backend/app/services/xai/overlay.py")},
        "seen_heatmap_before_annotation": list(SEEN_HEATMAP)})
    records = []
    try:
        for number, s in enumerate(samples, 1):
            image = Image.open(ROOT / s["path"]).convert("RGB")
            x = transform(image)[None].to(dev)
            with torch.no_grad():
                probabilities = torch.softmax(model(x), 1)
            target = int(probabilities.argmax())
            predicted = checkpoint["class_keys"][target]
            saved = {}
            for method, cam in cams.items():
                heatmap = P.normalize(cam(x, target, normalize=False)[0])
                full = DiseasePredictor._resize_heatmap(heatmap, *image.size)
                rendered = np.asarray(draw_regions(Image.new("RGB", image.size), full, THRESHOLD)).any(2)
                records.append({"sample_id": s["sample_id"], "dataset": s["dataset"], "label": s["label"],
                                "predicted": predicted, "correct": predicted == s["label"],
                                "confidence": float(probabilities[0, target]), "method": method,
                                "seen_heatmap": s["sample_id"] in SEEN_HEATMAP,
                                "symptom": annotations[s["sample_id"]]["kieu_trieu_chung"],
                                **P.region_metrics(heatmap, annotations[s["sample_id"]], rendered)})
                saved[method] = heatmap
            np.savez_compressed(out / "maps" / f"{s['sample_id']}.npz", **saved)
            print(f"{number}/{len(samples)} {s['sample_id']}", flush=True)
    finally:
        for cam in cams.values():
            cam.close()
    dump(out / "per-image.json", records)


def run_summarize(base: Path) -> dict:
    out = base / "lesion"
    records = json.loads((out / "per-image.json").read_text(encoding="utf-8"))
    annotations = load_annotations(base)
    blind = [r for r in records if not r["seen_heatmap"]]
    summary = {
        "n_images": len(records) // len(P.METHODS),
        "symptom_types": {d: {k: sum(1 for sid, a in annotations.items() if sid.startswith(d + "-")
                                     and a["kieu_trieu_chung"] == k)
                              for k in ("cuc_bo", "khuech_tan", "khong_co_vet")} for d in ("pv", "pd")},
        "data_problem_flags": sorted(sid for sid, a in annotations.items() if a.get("co_van_de_du_lieu")),
        # Đủ điều kiện = đoán đúng + có ô V khu trú + không gắn cờ dữ liệu, đúng điều kiện
        # mà region_metrics/summarize dùng; ảnh cuc_bo không thấy đốm nào ở 224 px bị loại.
        "lesion_eligible": {d: sum(1 for r in records if r["method"] == "gradcam" and r["correct"]
                                   and r["lesion_mass"] is not None and (d == "all" or r["dataset"] == d))
                            for d in ("all", "pv", "pd")},
        "localized_without_visible_lesion": sorted(
            sid for sid, a in annotations.items()
            if a["kieu_trieu_chung"] == "cuc_bo" and not any("V" in row for row in a["luoi"])),
        "all_images": P.summarize(records),
        "blind_only": P.summarize(blind),
    }
    dump(out / "summary.json", summary)
    print(f"Tổng hợp {summary['n_images']} ảnh → {out / 'summary.json'}")
    return summary


C_PP, C_GC = "#2E58A6", "#2C5F2D"
FIG_SEED = 2026
LABELS = {"all": "Tất cả", "pv": "PlantVillage", "pd": "PlantDoc"}


def _mask_rgba(rows: list[str], size: int = 224) -> np.ndarray:
    """Lớp phủ màu cho mặt nạ: lá lành xanh, vết bệnh đỏ, nền để trong suốt."""
    grid = np.array([list(r) for r in rows]).repeat(size // GRID, 0).repeat(size // GRID, 1)
    rgba = np.zeros((size, size, 4))
    rgba[grid == "L"] = (0.13, 0.77, 0.37, 0.35)
    rgba[grid == "V"] = (0.94, 0.25, 0.25, 0.55)
    return rgba


def _contours(ax, mask: np.ndarray, color: str, lw: float = 2.0, ls: str = "-") -> None:
    for c in cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]:
        c = c[:, 0, :]
        ax.plot(np.r_[c[:, 0], c[0, 0]], np.r_[c[:, 1], c[0, 1]], color=color, lw=lw, ls=ls)


def _bars(ax, metric: str, summary: dict, ylabel: str, fmt: str = "{:.3f}") -> None:
    x = np.arange(3)
    for offset, method, color, name in ((-0.2, "gradcam_plusplus", C_PP, "Grad-CAM++"), (0.2, "gradcam", C_GC, "Grad-CAM")):
        entries = [summary["by_dataset"][d][method][metric] for d in LABELS]
        means = np.array([e["mean"] for e in entries])
        err = [[e["mean"] - e["ci95"][0] for e in entries], [e["ci95"][1] - e["mean"] for e in entries]]
        ax.bar(x + offset, means, 0.38, color=color, label=name, yerr=err, capsize=3, ecolor="#555555")
        pad = 0.012 * max(m + hi for m, hi in zip(means, err[1]))
        for xi, m, hi in zip(x + offset, means, err[1]):
            ax.text(xi, m + hi + pad, fmt.format(m).replace(".", ","), ha="center", va="bottom", fontsize=8.5)
    n = [summary["by_dataset"][d]["gradcam"][metric]["n_images"] for d in LABELS]
    ax.set_xticks(x, [f"{LABELS[d]}\n(n = {k})" for d, k in zip(LABELS, n)])
    ax.set_ylabel(ylabel)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))


def run_figures(base: Path) -> None:
    """Hình cho báo cáo; ảnh ví dụ chọn ngẫu nhiên có seed, không chọn tay."""
    out = base / "lesion" / "figures"
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False})
    annotations = load_annotations(base)
    samples = {s["sample_id"]: s for s in read_samples(base)}
    summary = json.loads((base / "lesion" / "summary.json").read_text(encoding="utf-8"))["all_images"]
    records = json.loads((base / "lesion" / "per-image.json").read_text(encoding="utf-8"))
    rec = {(r["sample_id"], r["method"]): r for r in records}
    names = {d["key"]: d["name_vi"] for d in json.loads(
        (ROOT.parent / "shared/data/tomato_diseases.json").read_text(encoding="utf-8"))["diseases"]}
    rng = np.random.default_rng(FIG_SEED)
    img224 = lambda sid: np.asarray(Image.open(ROOT / samples[sid]["path"]).convert("RGB").resize((224, 224), Image.BILINEAR))

    # Hình 1: mặt nạ tham chiếu — 2 ảnh mỗi kiểu (PV/PD × khu trú) + 1 khuếch tán + 1 lá khoẻ.
    groups = [("pv", "cuc_bo", 2), ("pd", "cuc_bo", 2), (None, "khuech_tan", 1), (None, "khong_co_vet", 1)]
    chosen = []
    for dataset, kind, k in groups:
        pool = sorted(sid for sid, a in annotations.items() if a["kieu_trieu_chung"] == kind
                      and not a.get("co_van_de_du_lieu") and (dataset is None or sid.startswith(dataset + "-"))
                      and (kind != "cuc_bo" or any("V" in r for r in a["luoi"])))
        chosen += [pool[i] for i in sorted(rng.choice(len(pool), k, replace=False))]
    kinds = {"cuc_bo": "vết khu trú", "khuech_tan": "khuếch tán", "khong_co_vet": "lá khoẻ"}
    fig, axes = plt.subplots(2, 6, figsize=(13, 5.0), dpi=170)
    for col, sid in enumerate(chosen):
        a = annotations[sid]
        axes[0, col].imshow(img224(sid))
        axes[0, col].set_title(f"{'PlantVillage' if sid.startswith('pv') else 'PlantDoc'}\n{names[samples[sid]['label']]}",
                               fontsize=9)
        axes[1, col].imshow(img224(sid))
        axes[1, col].imshow(_mask_rgba(a["luoi"]))
        axes[1, col].set_title(f"Mặt nạ ({kinds[a['kieu_trieu_chung']]})", fontsize=9)
        for ax in axes[:, col]:
            ax.axis("off")
    fig.legend(handles=[matplotlib.patches.Patch(color=(0.13, 0.77, 0.37, 0.6), label="L — lá lành"),
                        matplotlib.patches.Patch(color=(0.94, 0.25, 0.25, 0.8), label="V — vết bệnh"),
                        matplotlib.patches.Patch(facecolor="white", edgecolor="#999999", label="N — nền (không tô)")],
               loc="lower center", ncol=3, frameon=False)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.9, bottom=0.08, hspace=0.25, wspace=0.05)
    fig.savefig(out / "figL1_masks.png")
    plt.close(fig)

    # Hình 2: chỉ số theo lá.
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.9), dpi=200)
    _bars(axes[0], "leaf_lift", summary, "Mức nâng vào lá ↑")
    axes[0].set_ylim(0, 0.95)
    _bars(axes[1], "overlay_outside_leaf", summary, "Vùng khoanh nằm ngoài lá\n(thấp hơn là tốt hơn)")
    axes[1].set_ylim(0, 0.1)
    axes[0].legend(frameon=False, loc="upper left", ncol=2)
    fig.tight_layout()
    fig.savefig(out / "figL2_leaf.png")
    plt.close(fig)

    # Hình 3: chỉ số theo vết bệnh (ảnh đoán đúng, vết khu trú).
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.9), dpi=200)
    _bars(axes[0], "lesion_lift", summary, "Mức nâng vào vết bệnh ↑")
    axes[0].set_ylim(0, 0.45)
    _bars(axes[1], "peak_on_lesion", summary, "Điểm nóng nhất trúng vết bệnh ↑", "{:.2f}")
    axes[1].set_ylim(0, 1.1)
    _bars(axes[2], "overlay_lesion_iou", summary, "IoU vùng khoanh ~ vết bệnh ↑")
    axes[2].set_ylim(0, 0.36)
    axes[0].legend(frameon=False, loc="upper left", ncol=2)
    fig.tight_layout()
    fig.savefig(out / "figL3_lesion.png")
    plt.close(fig)

    # Hình 4: chênh lệch ghép cặp (Grad-CAM++ − Grad-CAM) với KTC 95%.
    metrics = [("leaf_lift", "Mức nâng vào lá"), ("overlay_outside_leaf", "Vùng khoanh ngoài lá"),
               ("lesion_lift", "Mức nâng vào vết bệnh"), ("peak_on_lesion", "Điểm nóng trúng vết bệnh"),
               ("overlay_lesion_iou", "IoU khoanh ~ vết bệnh")]
    fig, ax = plt.subplots(figsize=(9.5, 4.4), dpi=200)
    colors = {"all": "#111111", "pv": "#2E58A6", "pd": "#D97706"}
    for i, (metric, _) in enumerate(metrics):
        for j, d in enumerate(LABELS):
            e = summary["paired_plusplus_minus_gradcam"][d][metric]
            y = i + (j - 1) * 0.22
            ax.errorbar(e["mean"], y, xerr=[[e["mean"] - e["ci95"][0]], [e["ci95"][1] - e["mean"]]], fmt="o",
                        color=colors[d], capsize=3, label=LABELS[d] if i == 0 else None)
    ax.axvline(0, color="#999999", ls="--", lw=0.9)
    ax.set_yticks(range(len(metrics)), [m[1] for m in metrics])
    ax.invert_yaxis()
    ax.set_xlabel("Chênh lệch Grad-CAM++ − Grad-CAM (KTC 95%)")
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(out / "figL4_paired.png")
    plt.close(fig)

    # Hình 5: ví dụ bản đồ nhiệt + vùng khoanh so với vết bệnh — 2 PV, 2 PD đủ điều kiện tính vết bệnh.
    picks = []
    for dataset in ("pv", "pd"):
        pool = sorted(r["sample_id"] for r in records if r["method"] == "gradcam" and r["dataset"] == dataset
                      and r["correct"] and r["lesion_mass"] is not None)
        picks += [pool[i] for i in sorted(rng.choice(len(pool), 2, replace=False))]
    fig, axes = plt.subplots(4, 3, figsize=(9, 12.4), dpi=170)
    for row, sid in zip(axes, picks):
        image = img224(sid)
        grid = np.array([list(r) for r in annotations[sid]["luoi"]]).repeat(16, 0).repeat(16, 1)
        maps = np.load(base / "lesion" / "maps" / f"{sid}.npz")
        row[0].imshow(image)
        row[0].imshow(_mask_rgba(annotations[sid]["luoi"]))
        row[0].set_title(f"{sid}\n{names[samples[sid]['label']]} · mặt nạ tham chiếu", fontsize=9.5)
        for ax, method, name in ((row[1], "gradcam", "Grad-CAM"), (row[2], "gradcam_plusplus", "Grad-CAM++")):
            heat = maps[method]
            ax.imshow(image)
            ax.imshow(heat, cmap="jet", alpha=0.4, vmin=0, vmax=1)
            _contours(ax, heat >= THRESHOLD, "white", 2.2)
            _contours(ax, grid == "V", "#FACC15", 1.6, "--")
            r = rec[(sid, method)]
            ax.set_title(f"{name}\nnâng vào vết {r['lesion_lift']:.2f} · IoU {r['overlay_lesion_iou']:.2f}".replace(".", ","),
                         fontsize=9.5)
        for ax in row:
            ax.axis("off")
    fig.legend(handles=[plt.Line2D([], [], color="white", lw=3, label="Vùng khoanh (≥ 0,62)",
                                   path_effects=[matplotlib.patheffects.withStroke(linewidth=5, foreground="#333333")]),
                        plt.Line2D([], [], color="#FACC15", lw=2.5, ls="--", label="Vết bệnh trong mặt nạ")],
               loc="lower center", ncol=2, frameon=False)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.04, hspace=0.3, wspace=0.04)
    fig.savefig(out / "figL5_examples.png")
    plt.close(fig)
    print("Hình 1:", chosen, "· hình 5:", picks, "→", out)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("sheets", "run", "summarize", "figures"))
    parser.add_argument("--base", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()
    {"sheets": lambda: run_sheets(args.base), "run": lambda: run_regions(args.base, args.device),
     "summarize": lambda: run_summarize(args.base), "figures": lambda: run_figures(args.base)}[args.command]()


if __name__ == "__main__":
    main()
