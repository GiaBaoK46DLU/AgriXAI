"""Cham diem phep kiem Grad-CAM: ghep mat na khoanh tay voi ban do nhiet (#17 — MD-08).

Doc hai file do hai buoc truoc sinh ra va tra loi CAU HOI CHINH cua #17:

    Trong tong "khoi luong" cua ban do nhiet, bao nhieu phan tram roi vao
    VET BENH, bao nhieu vao PHIEN LA LANH, bao nhieu ra NEN?

Ba con so do cong lai bang 1. Con so 46,3 % "trong la" ma #49 bao cao gop hai
loai dau lai, nen no khong tra loi duoc cau hoi "mo hinh co that su nhin vao
trieu chung khong" — do la ly do #17 ton tai.

Cac dai luong va cach doc
=========================

**Ti le khoi luong (``kl_*``)** — tong gia tri CAM trong nhom o do, chia cho tong
toan anh. Day la "mo hinh danh bao nhieu phan chu y cho vung nay".

**Ti le dien tich (``dt_*``)** — so o cua nhom chia 196. Day la "vung do to bao
nhieu".

**Muc tap trung (``tt_*``) = ti le khoi luong / ti le dien tich.** Dai luong quan
trong nhat, va la dai luong duy nhat so sanh duoc giua hai bo anh:

- ``= 1,00`` : CAM rai deu, khong uu tien gi. Bang dung voi rai ngau nhien.
- ``> 1,00`` : CAM uu tien vung do.
- ``< 1,00`` : CAM ne vung do.

Phai chia cho dien tich moi so duoc, vi ti le dien tich la o hai bo rat khac
nhau (PlantVillage mot phien la tren nen tron; PlantDoc co anh phu kin tan la).
So thang ti le khoi luong giua hai bo la so sai.

**Vung app thuc su khoanh (``app_*``)** — chi tinh tren cac o co CAM >= 0,5, dung
nguong ma backend va ban Dart ngoai tuyen dung de ve elip cho nong dan. Day la
con so *san pham*: trong cai vong ma nong dan nhin thay, bao nhieu phan tram
that su nam tren vet benh.

**CAM tho (``tho_*``)** — cung cac ti le tren nhung tinh tren CAM CHUA chuan hoa
min-max. Dung de kiem tra ket luan co phu thuoc vao phep keo gian o
``gradcam.py`` hay khong (xem canh bao ve #90 trong docstring ``GradCAM``).

Ba nhom lop, phai doc rieng — day la phat hien cua chinh #17
============================================================
Truong ``kieu_trieu_chung`` trong file khoanh tay chia cac anh lam ba:

- ``cuc_bo``     — vet benh khu tru duoc (dom, mang hoai tu). CHI nhom nay moi
                   doc duoc ti le V/L, vi moi o day "vet benh" va "la lanh" la
                   hai vung khac nhau that.
- ``khuech_tan`` — trieu chung trai deu ca phien la (kham virus, vang xoan la,
                   cham nhen do). O day V ~ ca phien la nen ti le V/L la HE QUA
                   CUA BENH HOC chu khong phai cua mo hinh. Chi doc la-vs-nen.
- ``khong_co_vet`` — lop ``healthy``, khong co o V nao theo dinh nghia.

Gop ba nhom lai roi bao mot con so "% trung vet benh" la sai ve phuong phap.
Script vi vay bao ca ba nhom rieng, va con so chinh cua bao cao lay tu nhom
``cuc_bo``.

Khoang tin cay
==============
n rat nho (3 anh/lop). Khoang tin cay 95 % tinh bang bootstrap percentile 10.000
lan tren tung anh — khong gia dinh phan phoi chuan, phu hop voi ti le bi chan
trong [0, 1] va co mau be. Con so tung lop (n=3) chi de tham khao dinh tinh; chi
con so gop ca bo moi du de trich vao bao cao.

Cach chay
=========
::

    cd model
    python -m src.xai.audit_score \
        --bo pv=outputs/audit-gradcam-17/pv \
        --bo pd=outputs/audit-gradcam-17/pd \
        --out-dir outputs/audit-gradcam-17
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from src.labels import key_to_name_vi
from src.utils.common import ensure_dir

NHAN = ("V", "L", "N")
TEN_NHOM = {
    "cuc_bo": "vết bệnh khu trú được",
    "khuech_tan": "triệu chứng khuếch tán cả phiến lá",
    "khong_co_vet": "không khoanh được vết bệnh nào",
}


def nang_chuan_hoa(kl: float, dt: float) -> float | None:
    """Mức nâng so với rải ngẫu nhiên, chuẩn hoá theo trần lý thuyết.

    Vì sao cần: "mức tập trung" = khối lượng ÷ diện tích có **trần khác nhau**
    tuỳ ảnh. Nếu vùng lá đã chiếm 70 % ảnh thì dù CAM dồn 100 % khối lượng vào
    lá, mức tập trung cũng chỉ đạt 1 ÷ 0,70 = 1,43×. Còn với ảnh mà lá chỉ
    chiếm 35 % thì trần là 2,86×. So thẳng 1,65× với 1,10× giữa hai bộ ảnh có
    tỉ lệ diện tích lá khác hẳn nhau là **so sai** — đây chính là chỗ bảng của
    #49 dễ bị đọc quá tay.

    Đại lượng này chuẩn hoá lại: ``(khối lượng − diện tích) / (1 − diện tích)``

    - ``0,00`` = đúng bằng rải ngẫu nhiên (không biết gì);
    - ``1,00`` = dồn toàn bộ khối lượng vào vùng đó (hoàn hảo);
    - âm = né vùng đó.

    Đọc được như "đi được bao nhiêu phần đoạn đường từ đoán mò tới hoàn hảo".
    """
    if dt is None or dt >= 1.0:
        return None
    return (kl - dt) / (1.0 - dt)


def _mat_na(luoi: list[str]) -> dict[str, np.ndarray]:
    arr = np.array([list(hang) for hang in luoi])
    return {ch: (arr == ch) for ch in NHAN}


def _ti_le(o_cam: np.ndarray, mask: dict[str, np.ndarray]) -> dict[str, float]:
    """Ti le khoi luong CAM roi vao tung nhan."""
    tong = float(o_cam.sum())
    if tong <= 0:
        return {ch: 0.0 for ch in NHAN}
    return {ch: float(o_cam[mask[ch]].sum() / tong) for ch in NHAN}


def do_mot_anh(cam: dict, ann: dict) -> dict:
    """Tinh toan bo chi so cho mot anh."""
    mask = _mat_na(ann["luoi"])
    n_o = mask["V"].size

    o_norm = np.array(cam["o_cam_chuan_hoa"], dtype=np.float64)
    o_tho = np.array(cam["o_cam_tho"], dtype=np.float64)
    o_that = np.array(cam["o_cam_lop_that"], dtype=np.float64)

    dt = {ch: float(mask[ch].sum() / n_o) for ch in NHAN}
    kl = _ti_le(o_norm, mask)
    kl_tho = _ti_le(o_tho, mask)
    kl_that = _ti_le(o_that, mask)

    # Vung app thuc su khoanh: cac o co CAM >= nguong (mac dinh 0,5)
    nong = o_norm >= 0.5
    n_nong = int(nong.sum())
    app = {ch: (float((nong & mask[ch]).sum() / n_nong) if n_nong else 0.0)
           for ch in NHAN}

    # O nong nhat — diem ma app dat tam vong khoanh
    r, c = np.unravel_index(int(o_norm.argmax()), o_norm.shape)
    dinh = ann["luoi"][r][c]

    def tap_trung(d: dict[str, float]) -> dict[str, float | None]:
        return {ch: (d[ch] / dt[ch] if dt[ch] > 0 else None) for ch in NHAN}

    dt_la = dt["V"] + dt["L"]
    kl_la = kl["V"] + kl["L"]
    tu_dong = _mat_na_tu_dong(cam, o_norm)

    return {
        "label": cam["label"],
        "pred": cam["pred"],
        "confidence": cam["confidence"],
        "dung": cam["dung"],
        "kieu_trieu_chung": ann.get("kieu_trieu_chung", "cuc_bo"),
        "co_van_de_du_lieu": bool(ann.get("co_van_de_du_lieu", False)),
        "dt": dt,
        "kl": kl,
        "tt": tap_trung(kl),
        "kl_tho": kl_tho,
        "tt_tho": tap_trung(kl_tho),
        "kl_lop_that": kl_that,
        "app": app,
        "app_ti_le_dien_tich": n_nong / n_o,
        "o_nong_nhat": dinh,
        # Hai dai luong nay so 1:1 duoc voi bang cua #49
        "dt_la": dt_la,
        "kl_la": kl_la,
        "tt_la": (kl_la / dt_la) if dt_la > 0 else None,
        # Chuan hoa theo tran ly thuyet — dai luong DUY NHAT so duoc giua hai bo
        "nang_la": nang_chuan_hoa(kl_la, dt_la),
        "nang_vet": nang_chuan_hoa(kl["V"], dt["V"]) if dt["V"] > 0 else None,
        "cam_tho": cam["cam_tho"],
        **tu_dong,
    }


def _mat_na_tu_dong(cam: dict, o_norm: np.ndarray) -> dict:
    """Cung ba chi so do, nhung dung MAT NA OTSU thay vi mat na khoanh tay.

    Muc dich duy nhat: tach "khac do doi mat na" khoi "khac do doi tap anh" khi
    dat canh bang cua #49. Hai nhanh chay tren DUNG cung 56 anh, cung mot CAM —
    khac nhau doc nhat o chO mat na tu dau ra.
    """
    o = cam.get("o_mat_na_tu_dong")
    if o is None:
        return {}
    la = np.array(o, dtype=np.float64) >= 0.5
    dt = float(la.mean())
    tong = float(o_norm.sum())
    kl = float(o_norm[la].sum() / tong) if tong > 0 else 0.0
    r, c = np.unravel_index(int(o_norm.argmax()), o_norm.shape)
    return {
        "td_dt_la": dt,
        "td_kl_la": kl,
        "td_tt_la": (kl / dt) if dt > 0 else None,
        "td_nang_la": nang_chuan_hoa(kl, dt),
        "td_dinh_trong_la": bool(la[r, c]),
    }


def bootstrap_ci(xs: list[float], n_lan: int = 10000, seed: int = 42
                 ) -> tuple[float | None, float | None, float | None]:
    """Trung binh + khoang tin cay 95 % bang bootstrap percentile.

    Tra ve None khi khong co gia tri nao — KHONG tra ve 0. Phan biet nay quan
    trong: lop ``healthy`` khong co o vet benh nao nen "muc tap trung vao vet
    benh" la **khong xac dinh**, in ra 0,00x se bi doc nham thanh "CAM ne hoan
    toan vet benh".
    """
    a = np.asarray([x for x in xs if x is not None], dtype=np.float64)
    if a.size == 0:
        return None, None, None
    if a.size == 1:
        return float(a[0]), float(a[0]), float(a[0])
    rng = np.random.default_rng(seed)
    mau = rng.choice(a, size=(n_lan, a.size), replace=True).mean(axis=1)
    return float(a.mean()), float(np.percentile(mau, 2.5)), float(np.percentile(mau, 97.5))


def gop(ket_qua: list[dict], keys: list[str]) -> dict:
    """Gop nhieu anh lai: moi anh mot phieu (macro), khong phai gop theo pixel."""
    out: dict = {"n": len(ket_qua)}
    if not ket_qua:
        return out
    for nhom in ("dt", "kl", "tt", "app", "kl_tho", "tt_tho", "kl_lop_that"):
        out[nhom] = {}
        for ch in NHAN:
            tb, lo, hi = bootstrap_ci([r[nhom][ch] for r in ket_qua])
            out[nhom][ch] = {"tb": tb, "kt95": [lo, hi]}
    for ten in ("dt_la", "kl_la", "tt_la", "nang_la", "nang_vet",
                "app_ti_le_dien_tich", "td_dt_la", "td_kl_la", "td_tt_la",
                "td_nang_la"):
        gt = [r.get(ten) for r in ket_qua]
        tb, lo, hi = bootstrap_ci(gt)
        out[ten] = {"tb": tb, "kt95": [lo, hi], "n": sum(x is not None for x in gt)}
    if any("td_dinh_trong_la" in r for r in ket_qua):
        out["td_dinh_trong_la"] = (
            sum(r.get("td_dinh_trong_la", False) for r in ket_qua) / len(ket_qua))
    out["dinh_trong_la"] = sum(r["o_nong_nhat"] in ("V", "L") for r in ket_qua) / len(ket_qua)
    out["dinh_tren_vet"] = sum(r["o_nong_nhat"] == "V" for r in ket_qua) / len(ket_qua)
    out["so_dung"] = sum(r["dung"] for r in ket_qua)
    tb, lo, hi = bootstrap_ci([r["cam_tho"]["ti_le_trung_binh_tren_dinh"] for r in ket_qua])
    out["cam_tho_do_phang"] = {"tb": tb, "kt95": [lo, hi]}
    out["class_keys"] = keys
    return out


def _pc(x: float | None) -> str:
    return "—" if x is None else f"{100 * x:.1f} %".replace(".", ",")


def _so(x: float | None) -> str:
    return "—" if x is None else f"{x:.2f}".replace(".", ",")


def _lan(x: float | None) -> str:
    """Số kèm dấu × — bỏ luôn dấu × khi giá trị không xác định."""
    return "—" if x is None else _so(x) + "×"


def viet_bang(f, tieu_de: str, rows: list[tuple[str, dict]]) -> None:
    """Bảng ba trường hợp — câu trả lời chính của #17."""
    f.write(f"\n### {tieu_de}\n\n")
    f.write("| Nhóm | n | KL vết bệnh | KL lá lành | KL nền | DT vết bệnh | "
            "Tập trung vết bệnh | DT lá | KL lá | Tập trung lá | Nâng chuẩn hoá (lá) | "
            "Đỉnh trong lá | Đỉnh trên vết |\n")
    f.write("|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|\n")
    for ten, g in rows:
        if not g.get("n"):
            continue
        f.write(f"| {ten} | {g['n']} | {_pc(g['kl']['V']['tb'])} | "
                f"{_pc(g['kl']['L']['tb'])} | {_pc(g['kl']['N']['tb'])} | "
                f"{_pc(g['dt']['V']['tb'])} | {_lan(g['tt']['V']['tb'])} | "
                f"{_pc(g['dt_la']['tb'])} | {_pc(g['kl_la']['tb'])} | "
                f"{_lan(g['tt_la']['tb'])} | {_so(g['nang_la']['tb'])} | "
                f"{_pc(g['dinh_trong_la'])} | {_pc(g['dinh_tren_vet'])} |\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="Cham diem phep kiem Grad-CAM #17")
    ap.add_argument("--bo", action="append", required=True,
                    help="Dang 'ten=thu_muc', lap lai duoc. VD: --bo pv=outputs/audit-gradcam-17/pv")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    names_vi = key_to_name_vi()
    out_dir = ensure_dir(args.out_dir)
    tong_hop: dict = {}
    chi_tiet: dict = {}

    for spec in args.bo:
        ten, thu_muc = spec.split("=", 1)
        d = Path(thu_muc)
        cam_data = json.loads((d / "cam-cells.json").read_text(encoding="utf-8"))
        ann_data = json.loads((d / "khoanh-tay.json").read_text(encoding="utf-8"))
        anns = ann_data["annotations"]
        keys = sorted({v["label"] for v in cam_data["samples"].values()})

        thieu = sorted(set(cam_data["samples"]) - set(anns))
        if thieu:
            raise SystemExit(f"[{ten}] chua khoanh tay {len(thieu)} anh: {thieu[:5]}")

        ket_qua = {sid: do_mot_anh(cam, anns[sid])
                   for sid, cam in cam_data["samples"].items()}
        chi_tiet[ten] = ket_qua
        tat_ca = list(ket_qua.values())

        muc: dict = {
            "bo_du_lieu": ann_data["bo_du_lieu"],
            "tat_ca": gop(tat_ca, keys),
            "theo_kieu_trieu_chung": {
                k: gop([r for r in tat_ca if r["kieu_trieu_chung"] == k], keys)
                for k in TEN_NHOM
            },
            "theo_lop": {
                k: gop([r for r in tat_ca if r["label"] == k], keys) for k in keys
            },
            "doan_dung": gop([r for r in tat_ca if r["dung"]], keys),
            "doan_sai": gop([r for r in tat_ca if not r["dung"]], keys),
            "bo_anh_co_van_de": gop([r for r in tat_ca if not r["co_van_de_du_lieu"]], keys),
        }
        tong_hop[ten] = muc

    (out_dir / "ket-qua.json").write_text(
        json.dumps({"tong_hop": tong_hop, "chi_tiet": chi_tiet},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    # Bang tung anh — de soat lai bang mat, va de Bao doi chieu khi review
    def _f(x: float | None, n: int = 4) -> str:
        return "" if x is None else f"{x:.{n}f}"

    with open(out_dir / "tung-anh.csv", "w", encoding="utf-8", newline="") as f:
        cot = ["sample_id", "bo", "lop_that", "lop_doan", "tin_cay", "dung",
               "kieu_trieu_chung", "co_van_de_du_lieu", "dt_vet", "dt_la", "kl_vet",
               "kl_la", "kl_nen", "tt_vet", "tt_la", "nang_la", "nang_vet",
               "o_nong_nhat", "app_dt", "app_vet", "app_la", "app_nen"]
        f.write(",".join(cot) + "\n")
        for ten, ket_qua in chi_tiet.items():
            for sid, r in sorted(ket_qua.items()):
                f.write(",".join([
                    sid, ten, r["label"], r["pred"], _f(r["confidence"]),
                    str(int(r["dung"])), r["kieu_trieu_chung"],
                    str(int(r["co_van_de_du_lieu"])),
                    _f(r["dt"]["V"]), _f(r["dt_la"]), _f(r["kl"]["V"]),
                    _f(r["kl_la"]), _f(r["kl"]["N"]),
                    _f(r["tt"]["V"], 3), _f(r["tt_la"], 3),
                    _f(r["nang_la"], 3), _f(r["nang_vet"], 3),
                    r["o_nong_nhat"], _f(r["app_ti_le_dien_tich"]),
                    _f(r["app"]["V"]), _f(r["app"]["L"]), _f(r["app"]["N"]),
                ]) + "\n")

    md = out_dir / "ket-qua.md"
    with open(md, "w", encoding="utf-8") as f:
        f.write("# Kết quả đo Grad-CAM với mặt nạ khoanh tay (#17)\n\n")
        f.write("Sinh tự động bởi `src/xai/audit_score.py` — đừng sửa tay.\n\n")
        f.write("**KL** = tỉ lệ khối lượng bản đồ nhiệt · **DT** = tỉ lệ diện tích ô · "
                "**Tập trung** = KL ÷ DT (1,00× = rải đều, không ưu tiên gì) · "
                "**Nâng chuẩn hoá** = (KL − DT) ÷ (1 − DT), tức đi được bao nhiêu phần "
                "đoạn đường từ đoán mò (0,00) tới hoàn hảo (1,00). Chỉ đại lượng cuối "
                "so được giữa hai bộ ảnh có tỉ lệ diện tích lá khác nhau.\n\n")
        f.write("Mọi con số là **trung bình theo từng ảnh** (mỗi ảnh một phiếu), "
                "không phải gộp theo pixel.\n")

        if len(tong_hop) > 1:
            f.write("\n## So hai bộ cạnh nhau — bảng chính\n\n")
            f.write("| | " + " | ".join(f"`{t}`" for t in tong_hop) + " |\n")
            f.write("|---|" + "--:|" * len(tong_hop) + "\n")
            hang = [
                ("Số ảnh", lambda g: str(g["n"])),
                ("Đoán đúng", lambda g: f"{g['so_dung']}/{g['n']}"),
                ("Diện tích lá (khoanh tay)", lambda g: _pc(g["dt_la"]["tb"])),
                ("Khối lượng heatmap trong lá", lambda g: _pc(g["kl_la"]["tb"])),
                ("**Mức tập trung vào lá**", lambda g: _lan(g["tt_la"]["tb"])),
                ("Trần lý thuyết của mức tập trung",
                 lambda g: _lan(1 / g["dt_la"]["tb"]) if g["dt_la"]["tb"] else "—"),
                ("**Nâng chuẩn hoá vào lá**", lambda g: _so(g["nang_la"]["tb"])),
                ("Đỉnh heatmap nằm trong lá", lambda g: _pc(g["dinh_trong_la"])),
                ("Đỉnh heatmap nằm trên vết bệnh", lambda g: _pc(g["dinh_tren_vet"])),
            ]
            for ten_h, fn in hang:
                f.write(f"| {ten_h} | " + " | ".join(fn(m["tat_ca"]) for m in tong_hop.values()) + " |\n")
            f.write("\nChỉ tính riêng nhóm **vết bệnh khu trú được** — nhóm duy nhất mà "
                    "tỉ lệ vết-bệnh / lá-lành có nghĩa:\n\n")
            f.write("| | " + " | ".join(f"`{t}`" for t in tong_hop) + " |\n")
            f.write("|---|" + "--:|" * len(tong_hop) + "\n")
            hang_cb = [
                ("Số ảnh", lambda g: str(g["n"])),
                ("Diện tích vết bệnh", lambda g: _pc(g["dt"]["V"]["tb"])),
                ("Khối lượng heatmap trên vết bệnh", lambda g: _pc(g["kl"]["V"]["tb"])),
                ("**Mức tập trung vào vết bệnh**", lambda g: _lan(g["tt"]["V"]["tb"])),
                ("**Nâng chuẩn hoá vào vết bệnh**", lambda g: _so(g["nang_vet"]["tb"])),
                ("Đỉnh heatmap nằm trên vết bệnh", lambda g: _pc(g["dinh_tren_vet"])),
                ("Vùng app khoanh — phần trên vết bệnh",
                 lambda g: _pc(g["app"]["V"]["tb"])),
                ("Vùng app khoanh — phần trên nền", lambda g: _pc(g["app"]["N"]["tb"])),
            ]
            for ten_h, fn in hang_cb:
                f.write(f"| {ten_h} | " + " | ".join(
                    fn(m["theo_kieu_trieu_chung"]["cuc_bo"]) for m in tong_hop.values()) + " |\n")

            if all(m["tat_ca"].get("td_dt_la", {}).get("tb") is not None
                   for m in tong_hop.values()):
                f.write("\n## Mặt nạ khoanh tay so với mặt nạ Otsu tự động — "
                        "**trên đúng cùng một tập ảnh**\n\n")
                f.write("Đây là phép so mà #49 không làm được, và là lý do #17 tồn tại. "
                        "Hai cột của mỗi bộ chạy trên cùng ảnh, cùng bản đồ nhiệt — "
                        "khác nhau **duy nhất** ở chỗ mặt nạ lá lấy từ đâu.\n\n")
                cot = []
                for t in tong_hop:
                    cot += [f"`{t}` tay", f"`{t}` Otsu"]
                f.write("| | " + " | ".join(cot) + " |\n")
                f.write("|---|" + "--:|" * len(cot) + "\n")
                hang_mn = [
                    ("Diện tích lá", "dt_la", "td_dt_la", _pc),
                    ("Khối lượng heatmap trong lá", "kl_la", "td_kl_la", _pc),
                    ("**Mức tập trung**", "tt_la", "td_tt_la", _lan),
                    ("**Nâng chuẩn hoá**", "nang_la", "td_nang_la", _so),
                ]
                for ten_h, k_tay, k_td, fmt in hang_mn:
                    o = [fmt(m["tat_ca"][k]["tb"]) for m in tong_hop.values()
                         for k in (k_tay, k_td)]
                    f.write(f"| {ten_h} | " + " | ".join(o) + " |\n")
                o = [_pc(m["tat_ca"][k]) for m in tong_hop.values()
                     for k in ("dinh_trong_la", "td_dinh_trong_la")]
                f.write("| Đỉnh heatmap nằm trong lá | " + " | ".join(o) + " |\n")
        for ten, muc in tong_hop.items():
            f.write(f"\n## Bộ `{ten}` — {muc['bo_du_lieu']}\n")
            g = muc["tat_ca"]
            f.write(f"\n{g['n']} ảnh, mô hình đoán đúng {g['so_dung']}/{g['n']}.\n")
            viet_bang(f, "Gộp, và tách theo kiểu triệu chứng", [
                ("**Toàn bộ**", g),
                *[(f"{TEN_NHOM[k]}", muc["theo_kieu_trieu_chung"][k]) for k in TEN_NHOM],
                ("*chỉ ảnh đoán đúng*", muc["doan_dung"]),
                ("*chỉ ảnh đoán sai*", muc["doan_sai"]),
                ("*bỏ ảnh có vấn đề dữ liệu*", muc["bo_anh_co_van_de"]),
            ])
            viet_bang(f, "Theo từng lớp (n=3 — chỉ đọc định tính)",
                      [(names_vi.get(k, k), muc["theo_lop"][k]) for k in g["class_keys"]])

            f.write("\n### Vùng app thật sự khoanh cho nông dân (ô có CAM ≥ 0,5)\n\n")
            f.write("| Nhóm | n | % diện tích ảnh | trên vết bệnh | trên lá lành | trên nền |\n")
            f.write("|---|--:|--:|--:|--:|--:|\n")
            for ten_n, gg in [("**Toàn bộ**", g)] + [
                    (TEN_NHOM[k], muc["theo_kieu_trieu_chung"][k]) for k in TEN_NHOM]:
                if not gg.get("n"):
                    continue
                f.write(f"| {ten_n} | {gg['n']} | {_pc(gg['app_ti_le_dien_tich']['tb'])} | "
                        f"{_pc(gg['app']['V']['tb'])} | {_pc(gg['app']['L']['tb'])} | "
                        f"{_pc(gg['app']['N']['tb'])} |\n")

            f.write("\n### Kiểm chứng: dùng CAM THÔ (chưa chuẩn hoá min-max)\n\n")
            f.write("| Nhóm | n | KL vết bệnh | KL lá lành | KL nền | Tập trung lá |\n")
            f.write("|---|--:|--:|--:|--:|--:|\n")
            for ten_n, gg in [("**Toàn bộ**", g)] + [
                    (TEN_NHOM[k], muc["theo_kieu_trieu_chung"][k]) for k in TEN_NHOM]:
                if not gg.get("n"):
                    continue
                tt_la_tho = ((gg["kl_tho"]["V"]["tb"] + gg["kl_tho"]["L"]["tb"])
                             / gg["dt_la"]["tb"]) if gg["dt_la"]["tb"] else None
                f.write(f"| {ten_n} | {gg['n']} | {_pc(gg['kl_tho']['V']['tb'])} | "
                        f"{_pc(gg['kl_tho']['L']['tb'])} | {_pc(gg['kl_tho']['N']['tb'])} | "
                        f"{_lan(tt_la_tho)} |\n")
            f.write(f"\nĐộ phẳng CAM thô (trung bình ÷ đỉnh; càng gần 1 càng phẳng): "
                    f"**{_so(g['cam_tho_do_phang']['tb'])}**"
                    f" (KTC 95 %: {_so(g['cam_tho_do_phang']['kt95'][0])}–"
                    f"{_so(g['cam_tho_do_phang']['kt95'][1])})\n")

    print(f"Da ghi:\n  {out_dir / 'ket-qua.json'}\n  {md}")
    for ten, muc in tong_hop.items():
        g = muc["tat_ca"]
        cb = muc["theo_kieu_trieu_chung"]["cuc_bo"]
        print(f"\n[{ten}] n={g['n']}  dung={g['so_dung']}")
        print(f"  KL: vet benh {_pc(g['kl']['V']['tb'])} | la lanh "
              f"{_pc(g['kl']['L']['tb'])} | nen {_pc(g['kl']['N']['tb'])}")
        print(f"  Trong la {_pc(g['kl_la']['tb'])} / dien tich la "
              f"{_pc(g['dt_la']['tb'])} -> tap trung {_so(g['tt_la']['tb'])}x")
        print(f"  Nang chuan hoa vao la: {_so(g['nang_la']['tb'])} "
              f"(tran tap trung {_so(1 / g['dt_la']['tb'])}x)")
        if cb.get("n"):
            print(f"  Nhom cuc_bo (n={cb['n']}): KL vet benh {_pc(cb['kl']['V']['tb'])} "
                  f"tren DT vet benh {_pc(cb['dt']['V']['tb'])} "
                  f"-> tap trung {_so(cb['tt']['V']['tb'])}x, "
                  f"nang chuan hoa {_so(cb['nang_vet']['tb'])}")


if __name__ == "__main__":
    main()
