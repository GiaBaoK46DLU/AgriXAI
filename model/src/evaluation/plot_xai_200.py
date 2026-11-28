"""Hình minh hoạ cho báo cáo đánh giá Grad-CAM++ trên bộ 200 ảnh.

Chạy từ model/ sau ``eval_xai_200 summarize``:  python -m src.evaluation.plot_xai_200
Ghi vào outputs/xai-eval-200/figures/. Ảnh ví dụ chọn ngẫu nhiên có seed (không chọn tay);
ví dụ độ bền chọn ảnh có IoU gần trung bình toàn bộ nhất.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

from src.evaluation import eval_xai_200 as V  # noqa: E402
from src.evaluation import extend_xai_eval as E  # noqa: E402
from src.evaluation.compare_xai import ROOT  # noqa: E402

C_PP, C_GC = "#2E58A6", "#2C5F2D"
NAMES = {d["key"]: d["name_vi"] for d in json.loads(
    (ROOT.parent / "shared/data/tomato_diseases.json").read_text(encoding="utf-8"))["diseases"]}
PERTS = {"sang_hon_15": "Sáng +15%", "toi_hon_15": "Tối −15%", "jpeg_q70": "JPEG q70",
         "mo_sigma1": "Mờ σ = 1", "nhieu_sd5": "Nhiễu sd 5"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False})


def ci(entry):
    return entry["mean"], entry["mean"] - entry["ci95"][0], entry["ci95"][1] - entry["mean"]


def bars(ax, labels, pp, gc, ylabel, fmt="{:.3f}"):
    x = np.arange(len(labels))
    for offset, data, color, name in ((-0.2, pp, C_PP, "Grad-CAM++"), (0.2, gc, C_GC, "Grad-CAM")):
        means = [d[0] for d in data]
        ax.bar(x + offset, means, 0.38, color=color, label=name,
               yerr=[[d[1] for d in data], [d[2] for d in data]], capsize=3, ecolor="#555555")
        for xi, m, d in zip(x + offset, means, data):
            ax.text(xi, m + d[2] + 0.005 * max(means), fmt.format(m).replace(".", ","), ha="center",
                    va="bottom", fontsize=8.5)
    ax.set_xticks(x, labels)
    ax.set_ylabel(ylabel)
    ax.legend(frameon=False, loc="upper right")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}".replace(".", ",")))


def metric_figures(summary: dict, out: Path) -> None:
    s, p = summary["summary"]["all"], "gradcam_plusplus"
    pick = lambda key: (ci(s[p][key]), ci(s["gradcam"][key]))

    keys = [f"{k}|contour_iou" for k in PERTS] + ["avg_contour_iou"]
    data = [pick(k) for k in keys]
    fig, ax = plt.subplots(figsize=(9, 3.8), dpi=200)
    bars(ax, list(PERTS.values()) + ["Trung bình"], [d[0] for d in data], [d[1] for d in data],
         "IoU vùng khoanh ↑")
    ax.set_ylim(0, 1.08)
    fig.tight_layout()
    fig.savefig(out / "fig3_robustness.png")
    plt.close(fig)

    configs = [("slic", "mean", "SLIC +\ntrung bình"), ("slic", "blur", "SLIC +\nlàm mờ"), ("slic", "road", "SLIC +\nROAD"),
               ("grid", "mean", "Lưới +\ntrung bình"), ("grid", "blur", "Lưới +\nlàm mờ"), ("grid", "road", "Lưới +\nROAD")]
    data = [pick(f"{u}|{f}|gap") for u, f, _ in configs]
    fig, ax = plt.subplots(figsize=(9, 3.8), dpi=200)
    bars(ax, [c[2] for c in configs], [d[0] for d in data], [d[1] for d in data], "Gap = insertion − deletion ↑")
    ax.set_ylim(0, 0.62)
    ax.legend(frameon=False, loc="upper left", ncol=2)
    fig.tight_layout()
    fig.savefig(out / "fig4_faithfulness.png")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), dpi=200)
    data = [pick(k) for k in ("drop_multiply", "drop_keep_top15")]
    bars(axes[0], ["Nhân theo điểm", "Giữ top 15%"], [d[0] for d in data], [d[1] for d in data],
         "Average Drop (%) ↓", "{:.1f}")
    axes[0].set_ylim(0, 115)
    axes[0].legend(frameon=False, loc="upper left", ncol=2)
    data = [pick(k) for k in ("win_multiply", "win_keep_top15")]
    bars(axes[1], ["Nhân theo điểm", "Giữ top 15%"], [d[0] for d in data], [d[1] for d in data],
         "Win% ↑", "{:.0f}")
    axes[1].set_ylim(0, 115)
    axes[1].legend(frameon=False, loc="upper left", ncol=2)
    fig.tight_layout()
    fig.savefig(out / "fig5_drop.png")
    plt.close(fig)

    mprt = summary["mprt"]["all"]
    fig, ax = plt.subplots(figsize=(9, 3.6), dpi=200)
    for method, color, name in ((p, C_PP, "Grad-CAM++"), ("gradcam", C_GC, "Grad-CAM")):
        groups = sorted(g for g in mprt if g.startswith(method + "|"))
        steps = [int(g.split("|")[1]) for g in groups]
        values = [mprt[g]["spearman"]["mean"] if "spearman" in mprt[g] else np.nan for g in groups]
        ax.plot(steps, values, "o-", color=color, label=name, lw=2)
    ax.axhline(0, color="#999999", lw=0.8, ls="--")
    ax.annotate("Grad-CAM: bản đồ rỗng từ bước 3\n(mô hình bị phá → không còn gì để giải thích)",
                xy=(3, -0.45), fontsize=9, color=C_GC)
    layers = ["phân loại", "f.8", "f.7", "f.6", "f.5", "f.4", "f.3", "f.2", "f.1", "f.0"]
    ax.set_xticks(range(1, 11), [f"{i}\n{l}" for i, l in enumerate(layers, 1)])
    ax.set_xlabel("Bước ngẫu nhiên hoá (từ đầu ra về đầu vào)")
    ax.set_ylabel("Spearman với bản đồ gốc\n(thấp = qua phép thử)")
    ax.set_ylim(-0.7, 1.05)
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout()
    fig.savefig(out / "fig6_mprt.png")
    plt.close(fig)


def overlay(ax, image, heatmap, title):
    unit = E.normalized(heatmap)
    ax.imshow(image)
    ax.imshow(unit, cmap="jet", alpha=0.4, vmin=0, vmax=1)
    mask = (unit >= E.OVERLAY_THRESHOLD).astype(np.uint8)
    for c in cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]:
        c = c[:, 0, :]
        ax.plot(np.r_[c[:, 0], c[0, 0]], np.r_[c[:, 1], c[0, 1]], color="white", lw=2)
    ax.set_title(title, fontsize=11)
    ax.axis("off")


def example_figures(out: Path, base: Path) -> None:
    samples = list(csv.DictReader((base / "samples.csv").open(encoding="utf-8-sig")))
    rng = np.random.default_rng(V.SAMPLE_SEED)

    # Hình 1: 12 ảnh trong bộ test, 6 PV + 6 PD, chọn ngẫu nhiên có seed.
    chosen = []
    for dataset in ("pv", "pd"):
        pool = [s for s in samples if s["dataset"] == dataset]
        chosen += [pool[i] for i in sorted(rng.choice(len(pool), 6, replace=False))]
    fig, axes = plt.subplots(2, 6, figsize=(12, 5.0), dpi=170)
    for ax, s in zip(axes.ravel(), chosen):
        ax.imshow(Image.open(ROOT / s["path"]).convert("RGB").resize((224, 224)))
        ax.set_title(f"{'PlantVillage' if s['dataset'] == 'pv' else 'PlantDoc'}\n{NAMES[s['label']]}", fontsize=9)
        ax.axis("off")
    fig.tight_layout(h_pad=1.6)
    fig.savefig(out / "fig1_samples.png")
    plt.close(fig)

    # Hình 2: Grad-CAM và Grad-CAM++ trên 4 ảnh (2 PV, 2 PD), cùng seed.
    ids = [s["sample_id"] for s in samples]
    picks = []
    for dataset in ("pv", "pd"):
        pool = [i for i, s in enumerate(samples) if s["dataset"] == dataset]
        picks += [pool[i] for i in sorted(rng.choice(len(pool), 2, replace=False))]
    ctx = V.Context(base, "cuda" if V.torch.cuda.is_available() else "cpu", limit=None)
    by_id = {s["sample_id"]: s for s in ctx.samples}
    fig, axes = plt.subplots(4, 3, figsize=(8.4, 11.4), dpi=170)
    for row, index in zip(axes, picks):
        s = by_id[ids[index]]
        mark = "đúng" if s["correct"] else "sai"
        row[0].imshow(s["image"])
        row[0].set_title(f"{s['sample_id']}\nNhãn: {NAMES[s['label']]}\nDự đoán: {NAMES[s['predicted']]} ({mark})",
                         fontsize=9.5)
        row[0].axis("off")
        overlay(row[1], s["image"], ctx.cam("gradcam", s["image"], s["target"]), "Grad-CAM")
        overlay(row[2], s["image"], ctx.cam("gradcam_plusplus", s["image"], s["target"]), "Grad-CAM++")
    fig.tight_layout()
    fig.savefig(out / "fig2_examples.png")
    plt.close(fig)

    # Hình 7: độ bền khi nén JPEG — ảnh đoán đúng có IoU gần trung bình nhất của cả hai phương pháp.
    records = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (base / "records").glob("*.json")}
    means = {m: np.mean([r["methods"][m]["robustness"]["jpeg_q70"]["contour_iou"] for r in records.values()
                         if r["methods"][m]["robustness"]["jpeg_q70"]]) for m in V.METHODS}
    best = min((r for r in records.values() if r["correct"] and r["methods"][V.METHODS[0]]["robustness"]["jpeg_q70"]),
               key=lambda r: sum((r["methods"][m]["robustness"]["jpeg_q70"]["contour_iou"] - means[m]) ** 2
                                 for m in V.METHODS))
    s = by_id[best["sample_id"]]
    number = [x["sample_id"] for x in ctx.samples].index(s["sample_id"])
    jpeg = E.perturbations(s["image"], 104729 + number)["jpeg_q70"]
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.9), dpi=170)
    axes[0].imshow(jpeg)
    axes[0].set_title(f"Ảnh sau khi nén JPEG q70\n{s['sample_id']}", fontsize=10)
    axes[0].axis("off")
    for ax, method, name in ((axes[1], "gradcam", "Grad-CAM"), (axes[2], "gradcam_plusplus", "Grad-CAM++")):
        a = E.normalized(ctx.cam(method, s["image"], s["target"])) >= E.OVERLAY_THRESHOLD
        b = E.normalized(ctx.cam(method, jpeg, s["target"])) >= E.OVERLAY_THRESHOLD
        iou = best["methods"][method]["robustness"]["jpeg_q70"]["contour_iou"]
        ax.imshow(s["image"])
        for mask, color in ((a, "#22C55E"), (b, "#F43F5E")):
            for c in cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]:
                c = c[:, 0, :]
                ax.plot(np.r_[c[:, 0], c[0, 0]], np.r_[c[:, 1], c[0, 1]], color=color, lw=2.4)
        ax.set_title(f"{name} · IoU {iou:.2f}".replace(".", ","), fontsize=11, fontweight="bold")
        ax.axis("off")
    fig.legend(handles=[plt.Line2D([], [], color="#22C55E", lw=3, label="Vùng khoanh trên ảnh gốc"),
                        plt.Line2D([], [], color="#F43F5E", lw=3, label="Sau khi nén JPEG")],
               loc="lower center", ncol=2, frameon=False)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.1, wspace=0.04)
    fig.savefig(out / "fig7_robust_example.png")
    plt.close(fig)
    print("Ví dụ hình 2:", [ids[i] for i in picks], "· hình 7:", s["sample_id"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=V.DEFAULT_OUT)
    args = parser.parse_args()
    out = args.base / "figures"
    out.mkdir(parents=True, exist_ok=True)
    metric_figures(json.loads((args.base / "summary.json").read_text(encoding="utf-8")), out)
    example_figures(out, args.base)
    print("Đã ghi hình vào", out)


if __name__ == "__main__":
    main()
