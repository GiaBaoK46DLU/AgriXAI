"""Sinh phiếu khoanh tay + dữ liệu CAM cho phép kiểm Grad-CAM (#17 — MD-08).

Đây là phần "đo" của #17. Việc *nhận xét* thì mắt người làm, nhưng muốn có **số**
thì phải ghép hai thứ: bản đồ nhiệt (máy tính được) và mặt nạ vùng lá / vết bệnh
(người khoanh). Script này lo phần máy, và sinh ra tờ phiếu để người khoanh.

Bốn quyết định thiết kế, đều cần giải thích được trước hội đồng
=================================================================

**1. Khoanh trên ảnh đã resize về 224x224, không khoanh trên ảnh gốc.**
``build_infer_transform`` resize thẳng về vuông (xem ``dataset.py`` — cố ý không
center-crop để heatmap phủ đúng toàn ảnh). Mô hình *chỉ* nhìn thấy bản 224x224
đó, Grad-CAM cũng sinh ra trên đúng lưới đó. Khoanh trên ảnh gốc rồi ánh xạ
ngược sẽ thêm một bước nội suy nữa, tự đưa sai số vào phép đo mà không được gì.
Ảnh PlantVillage vốn vuông (256x256) nên không méo; ảnh PlantDoc có thể méo tỉ
lệ — nhưng đó đúng là thứ mô hình nhìn thấy.

**2. Lưới 14x14, không phải khoanh đa giác tự do.**
Lớp tích chập cuối của EfficientNet-B0 với ảnh 224 cho feature map **7x7**. Toàn
bộ phần "mịn" của heatmap sau đó chỉ là nội suy song tuyến — **không mang thêm
thông tin nào**. Một mặt nạ khoanh tay mịn hơn 7x7 vì vậy là *độ chính xác giả*.
Lưới 14x14 = đúng 2x độ phân giải gốc của CAM: đủ mịn để không mất thông tin, đủ
thô để người khoanh tay nhất quán và để người khác kiểm lại được từng ô. Trên
phiếu, đường kẻ đậm vẽ mỗi 2 ô — tức đúng biên của một ô CAM gốc.

**3. Phiếu KHÔNG in bản đồ nhiệt (khoanh mù).**
Nếu vừa nhìn heatmap vừa khoanh vết bệnh thì mặt nạ sẽ bị chính heatmap dẫn dắt,
và con số "heatmap rơi trúng vết bệnh" thành ra tự chứng minh chính nó. Vì vậy
phiếu chỉ có ảnh. Bản chồng heatmap sinh bằng ``--overlay`` và **chỉ chạy sau khi
đã khoanh xong** (xem mục "Cách chạy" cuối file).

**4. Tính CAM cho CẢ lớp dự đoán lẫn lớp thật.**
Lớp dự đoán là thứ app hiển thị cho nông dân — đó là con số chính. Lớp thật trả
lời một câu hỏi khác, đáng giá cho phần phân tích lỗi: *khi đoán sai, mô hình có
nhìn thấy vết bệnh thật không, hay nó không thấy gì cả?*

Và ghi CẢ hai bản CAM: bản đã chuẩn hoá min-max (đúng thứ app dùng) lẫn bản thô.
Xem docstring ``GradCAM.__call__`` về lý do — tóm tắt: CAM phẳng lét cũng bị kéo
giãn thành 0..1 nên nhìn bản đã chuẩn hoá thì không biết mô hình có thật sự tập
trung hay không.

Cách chạy
=========
::

    cd model
    # Bước 1 — phiếu khoanh mù
    python -m src.xai.audit_sheets --samples outputs/audit-gradcam-17/mau-pv.csv \
        --out-dir outputs/audit-gradcam-17/pv

    # Bước 2 — người khoanh, ghi vào outputs/audit-gradcam-17/pv/khoanh-tay.json

    # Bước 3 — bản chồng heatmap để đối chiếu, CHỈ chạy sau bước 2
    python -m src.xai.audit_sheets --samples outputs/audit-gradcam-17/mau-pv.csv \
        --out-dir outputs/audit-gradcam-17/pv --overlay
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib
import numpy as np
import torch
from PIL import Image

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from src.data.dataset import build_infer_transform  # noqa: E402
from src.labels import key_to_name_vi  # noqa: E402
from src.models.build import load_checkpoint, target_layer_for_gradcam  # noqa: E402
from src.utils.common import ensure_dir, get_device  # noqa: E402
from src.xai.gradcam import GradCAM  # noqa: E402

# Ngưỡng app dùng để quyết định vẽ vùng khoanh cho nông dân.
# Khớp backend/app/core/config.py::HEATMAP_THRESHOLD và bản Dart chạy ngoại tuyến.
# Ghi cứng ở đây (không import backend) vì model/ không được phụ thuộc backend/.
HEATMAP_THRESHOLD = 0.5

# Màu hiển thị ba nhãn ô khi vẽ lại mặt nạ đã khoanh
MAU_NHAN = {"V": "#e03131", "L": "#2f9e44", "N": "#868e96"}
TEN_NHAN = {"V": "vết bệnh", "L": "phiến lá lành", "N": "nền"}


def cell_means(cam: np.ndarray, grid: int) -> np.ndarray:
    """Gộp bản đồ nhiệt (S, S) về lưới (grid, grid) bằng trung bình từng ô."""
    s = cam.shape[0]
    if s % grid:
        raise ValueError(f"Cạnh ảnh {s} không chia hết cho lưới {grid}")
    k = s // grid
    return cam.reshape(grid, k, grid, k).mean(axis=(1, 3))


def nguong_otsu(x: np.ndarray, bins: int = 256) -> float:
    """Ngưỡng Otsu — tự cài để khỏi thêm phụ thuộc (OpenCV / scikit-image).

    Otsu quét mọi ngưỡng và chọn ngưỡng làm **phương sai giữa hai nhóm** lớn
    nhất, tức tách hai cụm giá trị rõ nhất. Công thức dùng ở đây là dạng tích
    luỹ, tính một lượt trên histogram nên không cần vòng lặp Python.
    """
    hist, canh = np.histogram(x.ravel(), bins=bins, range=(0.0, 1.0))
    p = hist.astype(np.float64) / max(hist.sum(), 1)
    giua = (canh[:-1] + canh[1:]) / 2
    w0 = np.cumsum(p)
    w1 = 1.0 - w0
    m0 = np.cumsum(p * giua) / np.maximum(w0, 1e-12)
    m1 = (np.sum(p * giua) - np.cumsum(p * giua)) / np.maximum(w1, 1e-12)
    giua_nhom = w0 * w1 * (m0 - m1) ** 2
    return float(giua[int(np.argmax(giua_nhom))])


def mat_na_tu_dong(img224: Image.Image, grid: int) -> np.ndarray:
    """Mặt nạ lá XẤP XỈ bằng ngưỡng Otsu trên kênh bão hoà màu.

    Đây là **cài lại** đúng cách làm của #49, để #17 so được mặt nạ tay với mặt
    nạ tự động **trên cùng một tập ảnh**. Script gốc của #49 chạy trong thư mục
    tạm và chưa commit (`docx/Plan_model.md` mục 6, việc chờ chốt số 7), nên chỉ
    dựng lại được từ mô tả trong `docx/bao-cao-domain-gap.md` mục 5: *"mặt nạ lá
    xấp xỉ bằng ngưỡng Otsu trên kênh bão hoà màu"*.

    ⚠️ Vì là dựng lại từ mô tả chứ không phải chạy lại đúng mã nguồn cũ, con số
    ra đây có thể lệch chút so với bảng của #49. Nó vẫn dùng được cho mục đích
    duy nhất mà #17 cần: **so mặt nạ tay với mặt nạ tự động trên cùng 56 ảnh**,
    vì cả hai nhánh đều chạy trên cùng một hàm này.

    Trả về lưới (grid, grid) chứa **tỉ lệ điểm ảnh được coi là lá** trong từng ô.
    """
    hsv = np.asarray(img224.convert("HSV"), dtype=np.float32) / 255.0
    bao_hoa = hsv[..., 1]
    mask = (bao_hoa > nguong_otsu(bao_hoa)).astype(np.float32)
    return cell_means(mask, grid)


def _ve_luoi(ax, grid: int, size: int) -> None:
    """Kẻ lưới + đánh số hàng/cột lên một panel đã imshow ảnh size x size."""
    step = size / grid
    for i in range(grid + 1):
        # Đường đậm mỗi 2 ô = đúng biên một ô CAM gốc 7x7
        dam = (i % 2 == 0)
        kw = {
            "color": "#ffd43b" if dam else "#ffffff",
            "linewidth": 1.4 if dam else 0.5,
            "alpha": 0.95 if dam else 0.45,
        }
        ax.axhline(i * step - 0.5, **kw)
        ax.axvline(i * step - 0.5, **kw)

    for i in range(grid):
        c = (i + 0.5) * step - 0.5
        ax.text(c, -step * 0.45, str(i + 1), ha="center", va="center",
                fontsize=7, color="black")
        ax.text(-step * 0.45, c, str(i + 1), ha="center", va="center",
                fontsize=7, color="black")
    ax.set_xlim(-step * 0.9, size - 0.5)
    ax.set_ylim(size - 0.5, -step * 0.9)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


def ve_phieu_mu(image: Image.Image, img224: Image.Image, grid: int,
                sample_id: str, out: Path, zoom: int = 3) -> None:
    """Phiếu khoanh mù: chỉ ảnh + lưới, KHÔNG có heatmap.

    Hai panel, **cùng một hình học** nên lưới ô trùng khít nhau:

    - trái: đúng 224x224 mà mô hình nhìn thấy, vẽ ``interpolation="nearest"``
      để không nhoè thêm — đây là panel quyết định ô nào là gì;
    - phải: cùng khung hình đó nhưng lấy lại từ ảnh gốc ở độ phân giải cao hơn,
      chỉ để **nhận dạng** vết bệnh nhỏ. Cần panel này vì đốm vi khuẩn hay chấm
      nhện đường kính vài pixel: ở bản 224 chúng nhoè thành vệt xám, nhìn bản
      gốc mới phân biệt được vết bệnh thật với bóng đổ hay bụi đất.

    Panel phải **không** làm thay đổi phép đo — nó chỉ giúp người khoanh đọc
    đúng nội dung ô. Ô nào mô hình không thể thấy được vết bệnh (vì đã mất khi
    resize) thì đó là hạn chế của mô hình, phải ghi vào báo cáo chứ không phải
    sửa bằng cách khoanh khác đi.
    """
    arr = np.asarray(img224)
    size = arr.shape[0]
    hi = np.asarray(image.resize((size * zoom, size * zoom), Image.LANCZOS))

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 7.0))
    axes[0].imshow(arr, interpolation="nearest")
    axes[0].set_title("224x224 — đúng thứ mô hình nhìn thấy", fontsize=9)
    _ve_luoi(axes[0], grid, size)

    axes[1].imshow(hi)
    axes[1].set_title(f"cùng khung hình, độ phân giải x{zoom} — để nhận dạng vết bệnh",
                      fontsize=9)
    _ve_luoi(axes[1], grid, hi.shape[0])

    fig.suptitle(f"{sample_id}  —  khoanh V (vet benh) / L (la lanh) / N (nen)",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(out, dpi=105)
    plt.close(fig)


def ve_phieu_doi_chieu(img224: Image.Image, cam_norm: np.ndarray, grid: int,
                       nhan: list[str] | None, tieu_de: str, out: Path) -> None:
    """Bản đối chiếu sau khi khoanh: ảnh | heatmap | mặt nạ đã khoanh."""
    arr = np.asarray(img224)
    size = arr.shape[0]
    n_panel = 3 if nhan else 2
    fig, axes = plt.subplots(1, n_panel, figsize=(4.6 * n_panel, 5.0))

    axes[0].imshow(arr, interpolation="nearest")
    axes[0].set_title("Ảnh mô hình nhìn thấy (224x224)", fontsize=9)

    axes[1].imshow(arr, interpolation="nearest")
    axes[1].imshow(cam_norm, cmap="jet", alpha=0.45, vmin=0, vmax=1)
    # Viền trắng quanh vùng app thật sự khoanh cho nông dân
    axes[1].contour(cam_norm, levels=[HEATMAP_THRESHOLD], colors="white", linewidths=1.6)
    axes[1].set_title(f"Grad-CAM (viền trắng = vùng >= {HEATMAP_THRESHOLD})", fontsize=9)

    if nhan:
        axes[2].imshow(arr, alpha=0.35)
        step = size / grid
        for r in range(grid):
            for c in range(grid):
                ch = nhan[r][c]
                axes[2].add_patch(Rectangle(
                    (c * step - 0.5, r * step - 0.5), step, step,
                    facecolor=MAU_NHAN.get(ch, "#000000"), alpha=0.5,
                    edgecolor="none"))
        axes[2].contour(cam_norm, levels=[HEATMAP_THRESHOLD], colors="white",
                        linewidths=1.6)
        axes[2].set_title("Mặt nạ khoanh tay — đỏ: vết bệnh, xanh: lá lành, xám: nền",
                          fontsize=9)

    for ax in axes:
        _ve_luoi(ax, grid, size)
    fig.suptitle(tieu_de, fontsize=10)
    fig.tight_layout()
    fig.savefig(out, dpi=105)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description="Sinh phiếu khoanh tay + dữ liệu CAM cho #17")
    ap.add_argument("--samples", required=True, help="CSV do audit_sample.py sinh ra")
    ap.add_argument("--checkpoint", default="checkpoints/leaf_disease_detection_model.pt")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--grid", type=int, default=14)
    ap.add_argument("--device", default=None)
    ap.add_argument("--overlay", action="store_true",
                    help="Sinh bản đối chiếu có heatmap. CHỈ chạy sau khi đã khoanh xong.")
    ap.add_argument("--annotations", default=None,
                    help="File khoanh tay JSON; mặc định <out-dir>/khoanh-tay.json")
    args = ap.parse_args()

    out_dir = ensure_dir(args.out_dir)
    device = get_device(args.device)
    model, ckpt = load_checkpoint(args.checkpoint, device)
    keys: list[str] = ckpt["class_keys"]
    image_size: int = ckpt.get("image_size", 224)
    names_vi = key_to_name_vi()
    tf = build_infer_transform(image_size)

    with open(args.samples, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    nhan_tay: dict[str, dict] = {}
    if args.overlay:
        ann_path = Path(args.annotations or (out_dir / "khoanh-tay.json"))
        if ann_path.exists():
            nhan_tay = json.loads(ann_path.read_text(encoding="utf-8")).get("annotations", {})
            print(f"Doc mat na khoanh tay: {ann_path} ({len(nhan_tay)} anh)")
        else:
            print(f"[!] Chua co {ann_path} — ban doi chieu se thieu panel mat na")

    sheet_dir = ensure_dir(out_dir / ("doi-chieu" if args.overlay else "phieu"))
    cam = GradCAM(model, target_layer_for_gradcam(model, ckpt["arch"]))
    payload: dict[str, dict] = {}

    for row in rows:
        sid = row["sample_id"]
        image = Image.open(row["path"]).convert("RGB")
        img224 = image.resize((image_size, image_size), Image.BILINEAR)
        tensor = tf(image).unsqueeze(0).to(device)

        with torch.no_grad():
            probs = torch.softmax(model(tensor), dim=1)[0].cpu().numpy()
        pred_idx = int(probs.argmax())
        true_idx = keys.index(row["label"])

        cam_norm = cam(tensor, class_idx=pred_idx, normalize=True)[0]
        cam_raw = cam(tensor, class_idx=pred_idx, normalize=False)[0]
        cam_norm_true = cam(tensor, class_idx=true_idx, normalize=True)[0]

        o_norm = cell_means(cam_norm, args.grid)
        o_raw = cell_means(cam_raw, args.grid)
        o_true = cell_means(cam_norm_true, args.grid)

        top3 = np.argsort(probs)[::-1][:3]
        payload[sid] = {
            "path": row["path"],
            "label": row["label"],
            "label_vi": names_vi.get(row["label"], row["label"]),
            "pred": keys[pred_idx],
            "pred_vi": names_vi.get(keys[pred_idx], keys[pred_idx]),
            "confidence": float(probs[pred_idx]),
            "dung": pred_idx == true_idx,
            "top3": [[keys[i], float(probs[i])] for i in top3],
            "o_cam_chuan_hoa": o_norm.round(6).tolist(),
            "o_cam_tho": o_raw.round(8).tolist(),
            "o_cam_lop_that": o_true.round(6).tolist(),
            # Mat na Otsu cua #49, cai lai — de #17 so duoc TREN CUNG TAP ANH
            "o_mat_na_tu_dong": mat_na_tu_dong(img224, args.grid).round(4).tolist(),
            # Đo độ "phẳng" của CAM THÔ — phần mà bản chuẩn hoá giấu đi.
            # ti_le_trung_binh_tren_dinh gần 1 nghĩa là CAM gần như phẳng.
            "cam_tho": {
                "dinh": float(cam_raw.max()),
                "trung_binh": float(cam_raw.mean()),
                "ti_le_trung_binh_tren_dinh": (
                    float(cam_raw.mean() / cam_raw.max()) if cam_raw.max() > 0 else 0.0),
                "ti_le_diem_bang_khong": float((cam_raw <= 0).mean()),
            },
            "ti_le_dien_tich_nong": float((cam_norm >= HEATMAP_THRESHOLD).mean()),
        }

        out_png = sheet_dir / f"{sid}.png"
        if args.overlay:
            ok = "DUNG" if pred_idx == true_idx else "SAI"
            tieu_de = (f"{sid}  |  that: {payload[sid]['label_vi']}  |  "
                       f"doan: {payload[sid]['pred_vi']} {probs[pred_idx]:.0%}  [{ok}]")
            ve_phieu_doi_chieu(img224, cam_norm, args.grid,
                               nhan_tay.get(sid, {}).get("luoi"), tieu_de, out_png)
        else:
            ve_phieu_mu(image, img224, args.grid, sid, out_png)

    cam.close()

    meta = {
        "checkpoint": args.checkpoint,
        "model_version": ckpt.get("model_version"),
        "image_size": image_size,
        "grid": args.grid,
        "nguong_khoanh_vung": HEATMAP_THRESHOLD,
        "nhan_o": TEN_NHAN,
        "samples": payload,
    }
    cam_path = out_dir / "cam-cells.json"
    cam_path.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{len(rows)} anh -> {sheet_dir}")
    print(f"Du lieu CAM -> {cam_path}")
    if not args.overlay:
        dung = sum(1 for v in payload.values() if v["dung"])
        print(f"Trong mau nay mo hinh doan dung {dung}/{len(payload)} anh")


if __name__ == "__main__":
    main()
