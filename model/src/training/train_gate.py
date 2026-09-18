"""Huấn luyện bộ chặn 2 lớp lá cà chua / không phải lá cà chua (issue #92).

Đây là cách chữa gốc cho lỗi "chụp vật thể bất kỳ vẫn báo bệnh lá": mô hình 10
lớp dùng softmax nên 10 xác suất luôn cộng bằng 1, **không có chỗ nào biểu đạt
"không thuộc lớp nào cả"**. Một bộ phân loại nhị phân đứng trước nó mới trả lời
được câu đó.

Vì sao script riêng chứ không thêm cờ vào ``train.py``: ``train.py`` lấy số lớp
từ ``src/labels.py`` (đọc ``shared/data/tomato_diseases.json``), mà ticket #92
cấm đụng vào đó — thứ tự lớp trong file ấy là thứ tự output của mô hình bệnh.
Script này đi đường riêng, truyền thẳng ``GATE_CLASS_KEYS`` xuống dataset.

Cấu hình dùng lại ``configs/default.yaml`` (cùng augment, cùng image_size để
suy luận khớp mô hình chính), chỉ ghi đè số epoch — bài toán này dễ hơn hẳn phân
loại bệnh nên không cần 25 epoch.

Chạy (cần ``data/processed/gate-split.csv``, sinh bằng ``src.data.prepare_gate``):
    cd model
    .venv/Scripts/python -m src.training.train_gate

Ghi ``checkpoints/organ_gate.pt`` — checkpoint tự mô tả như mô hình chính, nên
``load_checkpoint`` nạp được mà không cần biết trước nó là bộ 2 lớp.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from src.data.dataset import build_dataloaders, build_train_transform
from src.data.gate_augment import DomainShortcutBreaker, GateTrainDataset, background_pool
from src.models.build import build_model, count_parameters, set_backbone_trainable
from src.training.train import run_epoch
from src.utils.common import ensure_dir, get_device, load_config, set_seed

# Thứ tự này là thứ tự output của bộ chặn: index 0 = lá, index 1 = không phải lá.
# Giữ nguyên thứ tự sau khi đã huấn luyện, cùng lý do như mảng `diseases` của mô
# hình bệnh — đổi chỗ là đảo nhãn mà không có gì báo lỗi.
GATE_CLASS_KEYS = ["tomato_leaf", "not_tomato_leaf"]


def main() -> None:
    ap = argparse.ArgumentParser(description="Huấn luyện bộ chặn 2 lớp lá / không phải lá")
    ap.add_argument("--config", default="configs/default.yaml")
    ap.add_argument("--manifest", type=Path, default=Path("data/processed/gate-split.csv"))
    ap.add_argument("--out", type=Path, default=Path("checkpoints/organ_gate.pt"))
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--freeze-epochs", type=int, default=2)
    ap.add_argument("--no-domain-augment", action="store_true",
                    help="Tắt phần phá lối tắt phong cách ảnh — để tái lập bản đầu "
                         "(recall PlantDoc 0,0795) khi cần so sánh trong báo cáo")
    ap.add_argument("--device", default=None)
    args = ap.parse_args()

    cfg = load_config(args.config)
    set_seed(cfg["seed"])
    device = get_device(args.device)

    if not args.manifest.exists():
        raise SystemExit(
            f"Chưa có manifest '{args.manifest}'. Chạy trước:  "
            "python -m src.data.prepare_gate"
        )

    loaders = build_dataloaders(cfg, args.manifest, keys=GATE_CLASS_KEYS)

    if not args.no_domain_augment:
        # Thay tập train bằng bản có phá lối tắt phong cách ảnh. Val/test giữ
        # nguyên ảnh gốc — augment tập đánh giá là tự bịa số liệu.
        breaker = DomainShortcutBreaker(background_pool(args.manifest, "train"))
        train_ds = GateTrainDataset(args.manifest, "train",
                                    build_train_transform(cfg), GATE_CLASS_KEYS, breaker)
        d = cfg["data"]
        loaders["train"] = DataLoader(
            train_ds, batch_size=d["batch_size"], shuffle=True, drop_last=True,
            num_workers=d["num_workers"], pin_memory=torch.cuda.is_available())
        print(f"Phá lối tắt phong cách ảnh: BẬT ({len(breaker.background_paths)} ảnh nền)")
    else:
        print("Phá lối tắt phong cách ảnh: TẮT")

    arch = cfg["model"]["arch"]
    model = build_model(arch, cfg["model"]["pretrained"], cfg["model"]["dropout"],
                        n_classes=len(GATE_CLASS_KEYS)).to(device)

    total_p, _ = count_parameters(model)
    print(f"Thiết bị: {device} | Kiến trúc: {arch} | Tham số: {total_p:,}")
    for split in ("train", "val", "test"):
        ds = loaders[split].dataset
        counts = dict(zip(ds.keys, ds.class_counts))
        print(f"  {split:5s}: {len(ds):5d} ảnh  {counts}")

    t = cfg["train"]
    criterion = nn.CrossEntropyLoss(label_smoothing=t["label_smoothing"])
    optimizer = torch.optim.AdamW(model.parameters(), lr=t["lr"],
                                  weight_decay=t["weight_decay"])
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)
    scaler = torch.amp.GradScaler(device.type) if (t["amp"] and device.type == "cuda") else None

    set_backbone_trainable(model, arch, trainable=args.freeze_epochs == 0)

    ckpt_dir = ensure_dir(args.out.parent)
    out_dir = ensure_dir(Path(cfg["paths"]["output_dir"]) / "logs")
    model_version = f"gate-{arch}-{datetime.now():%Y%m%d-%H%M}"

    best_acc, patience, history = 0.0, 0, []
    start = time.time()

    for epoch in range(1, args.epochs + 1):
        if epoch == args.freeze_epochs + 1 and args.freeze_epochs > 0:
            set_backbone_trainable(model, arch, trainable=True)
            for g in optimizer.param_groups:
                g["lr"] = t["lr"] * 0.1
            print(f"\n>>> Epoch {epoch}: mở khoá backbone, lr = {t['lr'] * 0.1:g}\n")

        tr_loss, tr_acc = run_epoch(model, loaders["train"], criterion, device,
                                    optimizer, scaler, f"Epoch {epoch}/{args.epochs} [train]")
        va_loss, va_acc = run_epoch(model, loaders["val"], criterion, device,
                                    desc=f"Epoch {epoch}/{args.epochs} [val]")
        scheduler.step()

        history.append({"epoch": epoch, "train_loss": tr_loss, "train_acc": tr_acc,
                        "val_loss": va_loss, "val_acc": va_acc,
                        "lr": optimizer.param_groups[0]["lr"]})
        print(f"Epoch {epoch:>3}/{args.epochs} | train loss {tr_loss:.4f} acc {tr_acc:.4f} | "
              f"val loss {va_loss:.4f} acc {va_acc:.4f}")

        if va_acc > best_acc:
            best_acc, patience = va_acc, 0
            torch.save({
                "arch": arch,
                "class_keys": GATE_CLASS_KEYS,
                "image_size": cfg["data"]["image_size"],
                "dropout": cfg["model"]["dropout"],
                "state_dict": model.state_dict(),
                "model_version": model_version,
                "epoch": epoch,
                "val_acc": va_acc,
            }, args.out)
            print(f"  -> Lưu checkpoint mới (val acc {va_acc:.4f})")
        else:
            patience += 1
            if patience >= t["early_stopping_patience"]:
                print(f"\nDừng sớm: {patience} epoch liên tiếp không cải thiện.")
                break

    with open(out_dir / f"history-{model_version}.json", "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    mins = (time.time() - start) / 60
    print(f"\nXong sau {mins:.1f} phút. Val accuracy tốt nhất: {best_acc:.4f}")
    print(f"Checkpoint: {args.out}")
    print("Bước tiếp theo:  python -m src.evaluation.evaluate_gate")


if __name__ == "__main__":
    main()
