"""Sinh hinh tong hop cho bao cao #17 — vai ca tieu bieu tren MOT tam anh.

Ba anh ``doi-chieu/`` sinh ra tung tam mot (56 tam, ~70 MB) la de *soat lai*, va
khong theo Git. Hinh nay moi la thu dua vao bao cao va slide: chon tay vai ca
noi len duoc cau chuyen, xep thanh luoi.

Moi o hien ba thu chong len nhau:

- anh goc 224x224,
- ban do nhiet Grad-CAM (jet),
- **vien trang lien** = vung app that su khoanh cho nong dan (CAM >= 0,5),
- **vien xanh la dut** = vet benh do nguoi khoanh tay.

Doc hinh: hai vien trung nhau = heatmap chi dung vet benh. Hai vien roi nhau =
mo hinh dang nhin cho khac voi cho co trieu chung.

Chay::

    cd model
    python -m src.xai.audit_figure \
        --bo pv=outputs/audit-gradcam-17/pv --bo pd=outputs/audit-gradcam-17/pd \
        --ca "pv:pv-septoria_leaf_spot-3=Trung cum dom — ca tot nhat cua PlantVillage" \
        --out outputs/audit-gradcam-17/figures/gradcam-vet-benh-17.png
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import numpy as np
from PIL import Image

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from src.data.dataset import build_infer_transform  # noqa: E402
from src.labels import key_to_name_vi  # noqa: E402
from src.models.build import load_checkpoint, target_layer_for_gradcam  # noqa: E402
from src.utils.common import ensure_dir, get_device  # noqa: E402
from src.xai.audit_sheets import HEATMAP_THRESHOLD  # noqa: E402
from src.xai.gradcam import GradCAM  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Hinh tong hop cac ca tieu bieu cho #17")
    ap.add_argument("--bo", action="append", required=True, help="ten=thu_muc")
    ap.add_argument("--ca", action="append", required=True,
                    help="'ten_bo:sample_id=chu thich', lap lai duoc")
    ap.add_argument("--checkpoint", default="checkpoints/leaf_disease_detection_model.pt")
    ap.add_argument("--cot", type=int, default=3)
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default=None)
    args = ap.parse_args()

    thu_muc = dict(s.split("=", 1) for s in args.bo)
    du_lieu = {
        ten: (json.loads((Path(d) / "cam-cells.json").read_text(encoding="utf-8")),
              json.loads((Path(d) / "khoanh-tay.json").read_text(encoding="utf-8")))
        for ten, d in thu_muc.items()
    }

    device = get_device(args.device)
    model, ckpt = load_checkpoint(args.checkpoint, device)
    keys: list[str] = ckpt["class_keys"]
    image_size: int = ckpt.get("image_size", 224)
    tf = build_infer_transform(image_size)
    names_vi = key_to_name_vi()
    cam_fn = GradCAM(model, target_layer_for_gradcam(model, ckpt["arch"]))

    ca = []
    for spec in args.ca:
        khoa, chu_thich = spec.split("=", 1)
        ten_bo, sid = khoa.split(":", 1)
        ca.append((ten_bo, sid, chu_thich))

    cols = args.cot
    rows = (len(ca) + cols - 1) // cols
    # Moi o co tieu de 3 dong nen phai chua chieu cao cho chu, khong thi
    # tieu de hang duoi de len anh hang tren.
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 4.3, rows * 5.5))
    axes = np.atleast_1d(axes).ravel()

    for ax, (ten_bo, sid, chu_thich) in zip(axes, ca):
        cam_data, ann_data = du_lieu[ten_bo]
        mau = cam_data["samples"][sid]
        ann = ann_data["annotations"][sid]

        image = Image.open(mau["path"]).convert("RGB")
        img224 = np.asarray(image.resize((image_size, image_size), Image.BILINEAR))
        tensor = tf(image).unsqueeze(0).to(device)
        heat = cam_fn(tensor, class_idx=keys.index(mau["pred"]))[0]

        # Mat na vet benh: tu luoi 14x14 phong len dung kich thuoc anh
        luoi = np.array([list(h) for h in ann["luoi"]])
        k = image_size // luoi.shape[0]
        mat_na_vet = np.kron((luoi == "V").astype(float), np.ones((k, k)))

        ax.imshow(img224, interpolation="nearest")
        ax.imshow(heat, cmap="jet", alpha=0.45, vmin=0, vmax=1)
        ax.contour(heat, levels=[HEATMAP_THRESHOLD], colors="white", linewidths=2.0)
        if mat_na_vet.any():
            ax.contour(mat_na_vet, levels=[0.5], colors="#69db7c", linewidths=1.6,
                       linestyles="dashed")
        ax.set_xticks([])
        ax.set_yticks([])

        dung = mau["pred"] == mau["label"]
        ax.set_title(
            f"{sid}\nthật: {names_vi.get(mau['label'], mau['label'])}  ·  "
            f"đoán: {names_vi.get(mau['pred'], mau['pred'])} {mau['confidence']:.0%}\n"
            f"{chu_thich}",
            fontsize=8, color="#2b8a3e" if dung else "#c92a2a")

    for ax in axes[len(ca):]:
        ax.axis("off")

    fig.suptitle(
        "Grad-CAM có rơi đúng vết bệnh không? (#17)\n"
        "viền trắng liền = vùng app khoanh cho nông dân (CAM ≥ 0,5)  ·  "
        "viền xanh đứt = vết bệnh do người khoanh tay",
        fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.93), h_pad=4.0)
    out = Path(args.out)
    ensure_dir(out.parent)
    fig.savefig(out, dpi=130)
    plt.close(fig)
    cam_fn.close()
    print(f"Da ghi {out} ({len(ca)} ca)")


if __name__ == "__main__":
    main()
