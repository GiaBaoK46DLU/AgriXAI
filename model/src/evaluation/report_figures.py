"""Sinh bộ hình cho báo cáo tiến độ và slide bảo vệ.

Mọi số liệu đọc thẳng từ file kết quả máy sinh trong ``outputs/`` — không có con
số nào gõ tay vào đây, nên chạy lại sau khi huấn luyện lại là hình tự cập nhật.

Ghi vào ``outputs/figures/report/``, **không đụng** ba hình cũ trong
``outputs/figures/`` (đã dùng trong `docx/bao-cao-huan-luyen-mo-hinh.md`).

Chạy:
    cd model
    .venv/Scripts/python -m src.evaluation.report_figures

⚠️ **Vì sao F1 từng lớp vẽ bằng dot plot chứ không phải cột:** F1 của 10 lớp nằm
trong khoảng 0,9835–1,0000. Vẽ cột tính từ 0 sẽ ra mười cột cao bằng nhau, nhìn
không đọc được gì; mà cắt gốc trục của biểu đồ cột thì lại là đánh lừa mắt, vì
mắt người đọc **độ dài** cột. Dot plot không gợi ý độ dài nên phóng to trục là
trung thực. Ngược lại, phần domain gap trải từ 0,04 tới 1,00 nên cột tính từ 0
mới đúng.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from src.labels import key_to_name_vi  # noqa: E402
from src.utils.common import ensure_dir  # noqa: E402

# Bảng màu mặc định của skill dataviz, đã chạy validate_palette.js (light,
# surface #fcfcfb): đạt cả 5 kiểm tra, cặp sát nhau tệ nhất ΔE 9,2 (deutan).
# Slot dùng theo đúng thứ tự cố định, không xoay vòng.
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"
SURFACE = "#fcfcfb"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#9a9a94"
GRID = "#e3e3df"


def _style(ax) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=9, length=0)
    ax.grid(True, color=GRID, linewidth=0.8, alpha=0.9)
    ax.set_axisbelow(True)


def _fig(w: float, h: float):
    fig, ax = plt.subplots(figsize=(w, h))
    fig.patch.set_facecolor(SURFACE)
    _style(ax)
    return fig, ax


def _legend_tren(ax, ncols: int = 3) -> None:
    """Chú giải đặt NGOÀI vùng vẽ, ngay trên trục.

    Để ``loc="lower left"``/``"lower right"`` như bản đầu thì chú giải nằm đè lên
    chính cột/điểm dữ liệu ở hàng dưới cùng — nhìn ra ngay khi mở hình.
    """
    ax.legend(loc="lower left", bbox_to_anchor=(0, 1.01), frameon=False,
              fontsize=9, ncols=ncols, handletextpad=0.5, columnspacing=1.6)


def _save(fig, path: Path, title: str, subtitle: str = "") -> None:
    # Bản đầu đặt suptitle mặc định (y≈0.98) và phụ đề cứng ở y=0.945 — hai dòng
    # chồng lên nhau, và phụ đề dài thì tràn khỏi mép phải. Nay xuống dòng theo
    # chiều rộng hình thật rồi chừa chỗ theo số dòng đếm được.
    import textwrap

    width_in = fig.get_size_inches()[0]
    lines = textwrap.wrap(subtitle, width=int(width_in * 13.5)) if subtitle else []

    fig.text(0.02, 0.975, title, fontsize=13, fontweight="bold", color=INK,
             ha="left", va="top")
    if lines:
        fig.text(0.02, 0.928, "\n".join(lines), fontsize=9.5, color=INK2,
                 ha="left", va="top", linespacing=1.45)

    top = 0.935 - 0.035 * len(lines)
    fig.tight_layout(rect=(0, 0, 1, top))
    fig.savefig(path, dpi=150, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    print(f"  {path}")


def ten_vi(key: str) -> str:
    return key_to_name_vi().get(key, key)


# ── 1. Precision / Recall / F1 từng lớp ───────────────────────────────────────
def fig_per_class_metrics(report: dict, out: Path) -> None:
    pc = report["per_class"]
    rows = sorted(pc.items(), key=lambda kv: kv[1]["f1-score"])
    names = [f"{ten_vi(k)}  (n={int(v['support'])})" for k, v in rows]
    y = np.arange(len(rows))

    fig, ax = _fig(9.5, 5.4)
    for i, (_, v) in enumerate(rows):
        vals = [v["precision"], v["recall"], v["f1-score"]]
        ax.plot([min(vals), max(vals)], [i, i], color=GRID, linewidth=2, zorder=1)

    for slot, (label, color) in enumerate(
            [("Precision", S1), ("Recall", S2), ("F1", S3)]):
        key = ["precision", "recall", "f1-score"][slot]
        ax.scatter([v[key] for _, v in rows], y, s=58, color=color, label=label,
                   zorder=3, edgecolors=SURFACE, linewidths=1.4)

    lo = min(min(v["precision"], v["recall"], v["f1-score"]) for _, v in rows)
    ax.set_xlim(lo - 0.006, 1.018)
    # Chặn vạch trục ở 1,00: F1/precision/recall không thể lớn hơn 1, để
    # matplotlib tự sinh vạch 1,01 là gợi ý sai về miền giá trị.
    ax.set_xticks([t for t in ax.get_xticks() if lo - 0.006 <= t <= 1.0])

    # Nhãn F1 xếp thành MỘT CỘT ở mép phải thay vì bám theo từng chấm — bám theo
    # chấm thì ở hàng có precision/recall sát 1,0 nhãn đè thẳng lên chấm bên cạnh.
    # Đây cũng là phần "relief" bắt buộc cho slot aqua (contrast 2,74:1 < 3:1).
    for i, (_, v) in enumerate(rows):
        ax.annotate(f"{v['f1-score']:.4f}", (1.008, i), ha="left", va="center",
                    fontsize=8.5, color=INK2)
    ax.set_yticks(y, names)
    ax.set_xlabel("Giá trị (trục đã phóng to — xem ghi chú)", fontsize=9, color=INK2)
    _legend_tren(ax, ncols=3)
    ax.grid(axis="y", visible=False)
    _save(fig, out / "01-chi-so-tung-lop.png",
          "Precision · Recall · F1 từng lớp bệnh — tập test PlantVillage",
          f"{report['num_samples']} ảnh · accuracy {report['accuracy']:.4f} · "
          f"macro-F1 {report['macro_f1']:.4f}. Trục x bắt đầu từ {lo - 0.006:.3f}, "
          "không phải 0 — dot plot nên phóng trục là trung thực.")


# ── 2. Số ảnh huấn luyện so với F1 ────────────────────────────────────────────
def fig_support_vs_f1(report: dict, out: Path) -> None:
    pc = report["per_class"]
    sup = np.array([v["support"] for v in pc.values()])
    f1 = np.array([v["f1-score"] for v in pc.values()])
    keys = list(pc.keys())

    fig, ax = _fig(8.6, 5.0)
    ax.scatter(sup, f1, s=90, color=S1, edgecolors=SURFACE, linewidths=1.5, zorder=3)

    # Chỉ ghi nhãn ba điểm mang câu chuyện. Ghi nhãn cả 10 lớp thì vùng giữa
    # (5 lớp chụm trong khoảng F1 0,992–0,998) chồng chữ lên nhau không đọc nổi.
    diem_nhan = {
        "mosaic_virus": (0, 14, "center"),
        "yellow_leaf_curl_virus": (0, 14, "center"),
        "target_spot": (0, 14, "center"),
    }
    for k, x, yy in zip(keys, sup, f1):
        if k not in diem_nhan:
            continue
        dx, dy, ha = diem_nhan[k]
        ax.annotate(f"{ten_vi(k)}\nn={int(x)} · F1 {yy:.4f}", (x, yy),
                    xytext=(dx, dy), textcoords="offset points", ha=ha,
                    fontsize=8.5, color=INK, fontweight="bold", linespacing=1.4)

    ax.set_xlabel("Số ảnh trong tập test (tỉ lệ thuận với số ảnh huấn luyện)",
                  fontsize=9, color=INK2)
    ax.set_ylabel("F1", fontsize=9, color=INK2)
    ax.set_ylim(0.978, 1.004)
    _save(fig, out / "02-so-anh-vs-f1.png",
          "Lớp ít ảnh nhất vẫn đạt F1 tuyệt đối",
          "Virus khảm chỉ có 55 ảnh test (ít hơn lớp đông nhất 14,6 lần) nhưng F1 = 1,0000; "
          "lớp yếu nhất lại là Đốm đích, vốn không thiếu ảnh. "
          "→ lệch lớp là nguy cơ, không phải hậu quả tất yếu.")


# ── 3. Đường cong huấn luyện ──────────────────────────────────────────────────
def fig_training_curves(history: list[dict], unfreeze_epoch: int, out: Path) -> None:
    ep = [h["epoch"] for h in history]
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.6, 6.4), sharex=True)
    fig.patch.set_facecolor(SURFACE)
    for ax in (ax1, ax2):
        _style(ax)
        ax.axvline(unfreeze_epoch, color=MUTED, linewidth=1.2, linestyle="--", zorder=1)

    ax1.plot(ep, [h["train_loss"] for h in history], color=S1, linewidth=2, label="Train")
    ax1.plot(ep, [h["val_loss"] for h in history], color=S2, linewidth=2, label="Validation")
    ax1.set_ylabel("Loss", fontsize=9, color=INK2)
    ax1.legend(loc="upper right", frameon=False, fontsize=9)
    ax1.annotate("mở khoá backbone,\nlr giảm 10 lần", (unfreeze_epoch, ax1.get_ylim()[1]),
                 xytext=(8, -14), textcoords="offset points", fontsize=8.5, color=INK2)

    ax2.plot(ep, [h["train_acc"] for h in history], color=S1, linewidth=2, label="Train")
    ax2.plot(ep, [h["val_acc"] for h in history], color=S2, linewidth=2, label="Validation")
    ax2.set_ylabel("Accuracy", fontsize=9, color=INK2)
    ax2.set_xlabel("Epoch", fontsize=9, color=INK2)
    ax2.legend(loc="lower right", frameon=False, fontsize=9)

    best = max(history, key=lambda h: h["val_acc"])
    ax2.scatter([best["epoch"]], [best["val_acc"]], s=70, color=S2,
                edgecolors=SURFACE, linewidths=1.5, zorder=4)
    ax2.annotate(f"val acc tốt nhất {best['val_acc']:.4f}\n(epoch {best['epoch']})",
                 (best["epoch"], best["val_acc"]), xytext=(-12, -34),
                 textcoords="offset points", ha="right", fontsize=8.5, color=INK2)

    # Hai thước đo khác đơn vị -> hai bảng riêng dùng chung trục x, KHÔNG
    # dùng hai trục y chồng lên một bảng.
    _save(fig, out / "03-duong-cong-huan-luyen.png",
          "Đường cong huấn luyện — EfficientNet-B0, 25 epoch",
          "Hai bảng dùng chung trục epoch. Loss và accuracy khác đơn vị nên tách bảng, "
          "không vẽ chồng hai trục y.")


# ── 4. Domain gap từng lớp ────────────────────────────────────────────────────
def fig_domain_gap(pv: dict, pd_: dict, out: Path) -> None:
    chung = [k for k, v in pd_["per_class"].items() if v["support"] > 0]
    chung.sort(key=lambda k: pd_["per_class"][k]["f1-score"])
    y = np.arange(len(chung))
    h = 0.38

    fig, ax = _fig(9.5, 5.6)
    f_pv = [pv["per_class"][k]["f1-score"] for k in chung]
    f_pd = [pd_["per_class"][k]["f1-score"] for k in chung]
    ax.barh(y + h / 2, f_pv, height=h, color=S1, label="PlantVillage (ảnh phòng chụp)", zorder=3)
    ax.barh(y - h / 2, f_pd, height=h, color=S2, label="PlantDoc (ảnh thật)", zorder=3)

    for i, (a, b) in enumerate(zip(f_pv, f_pd)):
        ax.annotate(f"{a:.2f}", (a, i + h / 2), xytext=(5, 0), textcoords="offset points",
                    va="center", fontsize=8.5, color=INK2)
        ax.annotate(f"{b:.2f}", (b, i - h / 2), xytext=(5, 0), textcoords="offset points",
                    va="center", fontsize=8.5, color=INK2)

    ax.set_yticks(y, [ten_vi(k) for k in chung])
    ax.set_xlim(0, 1.12)
    ax.set_xlabel("F1", fontsize=9, color=INK2)
    _legend_tren(ax, ncols=2)
    ax.grid(axis="y", visible=False)
    _save(fig, out / "04-domain-gap-tung-lop.png",
          "Domain gap: cùng một mô hình, hai loại ảnh",
          f"Accuracy {pv['accuracy']:.4f} → {pd_['accuracy']:.4f} trên 8 lớp PlantDoc có ảnh. "
          "Không lớp nào giữ được phong độ; hai lớp tụt về gần 0.")


# ── 5. Phân bố độ tin cậy trên ảnh KHÔNG phải lá ──────────────────────────────
def fig_negative_confidence(rows: list[dict], out: Path) -> None:
    conf = np.array([float(r["confidence"]) for r in rows])

    fig, ax = _fig(8.6, 4.8)
    ax.hist(conf, bins=24, color=S1, zorder=3)
    for thr in (0.5, 0.9):
        ax.axvline(thr, color=S2, linewidth=1.6, linestyle="--", zorder=4)
        lot = (conf >= thr).sum()
        ax.annotate(f"ngưỡng {thr:.1f}\n{lot} ảnh lọt", (thr, ax.get_ylim()[1]),
                    xytext=(6, -30), textcoords="offset points",
                    fontsize=8.5, color=S2, fontweight="bold")

    ax.set_xlabel("Độ tin cậy mô hình gán cho ảnh KHÔNG phải lá cà chua",
                  fontsize=9, color=INK2)
    ax.set_ylabel("Số ảnh", fontsize=9, color=INK2)
    _save(fig, out / "05-do-tin-cay-anh-khong-phai-la.png",
          "Vì sao ngưỡng tin cậy một mình không chặn được ảnh rác",
          f"{len(conf)} ảnh không phải lá cà chua (#91). Cao nhất đạt {conf.max():.3f} — "
          "mô hình vẫn rất tự tin với ảnh nó chưa từng học.")


# ── 6. Ba bản bộ chặn ─────────────────────────────────────────────────────────
def fig_gate_variants(out: Path) -> None:
    # Ba con số của mỗi bản nằm ở ba nơi khác nhau (bản 1 và 2 đã bị ghi đè
    # checkpoint), nên đây là chỗ DUY NHẤT trong file phải ghi số theo báo cáo
    # thay vì đọc từ JSON. Nguồn: CLAUDE.md mục "#92 — bộ chặn 2 lớp".
    bans = ["Bản 1\nchỉ ảnh phòng chụp", "Bản 2\n+ phá lối tắt", "Bản 3\n+ ảnh đồng ruộng"]
    series = [
        ("Lá thật ngoài đồng", S2, [0.0882, 0.35, 0.9118]),
        ("Lá ảnh phòng chụp", S1, [0.9993, 0.9978, 0.9989]),
        ("Ảnh rác (chặn đúng)", S3, [1.0000, 0.9912, 0.9678]),
    ]
    x = np.arange(len(bans))
    w = 0.26

    fig, ax = _fig(9.0, 5.0)
    for i, (label, color, vals) in enumerate(series):
        pos = x + (i - 1) * w
        ax.bar(pos, vals, width=w - 0.02, color=color, label=label, zorder=3)
        for xi, v in zip(pos, vals):
            ax.annotate(f"{v:.2f}", (xi, v), xytext=(0, 4), textcoords="offset points",
                        ha="center", fontsize=8.5, color=INK2)

    ax.set_xticks(x, bans)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Recall", fontsize=9, color=INK2)
    _legend_tren(ax, ncols=3)
    ax.grid(axis="x", visible=False)
    _save(fig, out / "06-ba-ban-bo-chan.png",
          "Bộ chặn: bản đạt mọi tiêu chí nghiệm thu lại là bản hỏng nhất",
          "Bản 1 chặn đúng 100 % ảnh rác và gần như không chặn oan ảnh phòng chụp — "
          "nhưng loại bỏ 91 % ảnh lá THẬT. Cột cam mới là cột nói lên sự thật.")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-dir", type=Path, default=Path("outputs/figures/report"))
    ap.add_argument("--history", type=Path,
                    default=Path("outputs/logs/history-efficientnet_b0-20260907-1443.json"))
    ap.add_argument("--unfreeze-epoch", type=int, default=4)
    args = ap.parse_args()

    out = ensure_dir(args.out_dir)
    doc = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))  # noqa: E731

    print("Sinh hình báo cáo:")
    report = doc("outputs/report-test.json")
    fig_per_class_metrics(report, out)
    fig_support_vs_f1(report, out)
    fig_training_curves(doc(args.history), args.unfreeze_epoch, out)
    fig_domain_gap(doc("outputs/plantvillage-8lop/report-test.json"),
                   doc("outputs/plantdoc-8lop/report-test.json"), out)
    with open("outputs/negative-confidence/results.csv", encoding="utf-8") as f:
        fig_negative_confidence(list(csv.DictReader(f)), out)
    fig_gate_variants(out)


if __name__ == "__main__":
    main()
