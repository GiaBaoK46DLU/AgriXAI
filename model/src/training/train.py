"""Huấn luyện mô hình phân loại bệnh lá cà chua.

Chạy:
    cd model
    python -m src.training.train --config configs/default.yaml

Chiến lược: transfer learning hai giai đoạn.
  Giai đoạn 1 (vài epoch đầu) — đóng băng backbone, chỉ huấn luyện lớp phân loại.
  Giai đoạn 2 — mở khoá toàn bộ, hạ learning rate xuống 1/10 để tinh chỉnh nhẹ.

Kết thúc, checkpoint tốt nhất được ghi vào ``checkpoints/best.pt``. File này tự
mô tả (chứa arch, danh sách lớp, image_size) nên backend nạp thẳng được mà không
cần biết trước cấu hình huấn luyện.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import torch
import torch.nn as nn
from tqdm import tqdm

from src.data.dataset import build_dataloaders
from src.labels import class_keys
from src.models.build import build_model, count_parameters, set_backbone_trainable
from src.utils.common import AverageMeter, ensure_dir, get_device, load_config, set_seed


def run_epoch(model, loader, criterion, device, optimizer=None, scaler=None,
              desc: str = "") -> tuple[float, float]:
    """Chạy một epoch. Có ``optimizer`` là huấn luyện, không có là đánh giá."""
    is_train = optimizer is not None
    model.train(is_train)

    loss_meter, acc_meter = AverageMeter(), AverageMeter()
    bar = tqdm(loader, desc=desc, leave=False)

    with torch.set_grad_enabled(is_train):
        for images, targets in bar:
            images = images.to(device, non_blocking=True)
            targets = targets.to(device, non_blocking=True)

            if is_train:
                optimizer.zero_grad(set_to_none=True)

            use_amp = scaler is not None and device.type == "cuda"
            with torch.autocast(device_type=device.type, enabled=use_amp):
                logits = model(images)
                loss = criterion(logits, targets)

            if is_train:
                if use_amp:
                    scaler.scale(loss).backward()
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    loss.backward()
                    optimizer.step()

            acc = (logits.argmax(1) == targets).float().mean().item()
            loss_meter.update(loss.item(), images.size(0))
            acc_meter.update(acc, images.size(0))
            bar.set_postfix(loss=f"{loss_meter.avg:.4f}", acc=f"{acc_meter.avg:.4f}")

    return loss_meter.avg, acc_meter.avg


def main() -> None:
    ap = argparse.ArgumentParser(description="Huấn luyện mô hình nhận diện bệnh cà chua")
    ap.add_argument("--config", default="configs/default.yaml")
    ap.add_argument("--device", default=None, help="cuda | cpu (mặc định: tự dò)")
    ap.add_argument("--resume", default=None, help="Đường dẫn checkpoint để học tiếp")
    args = ap.parse_args()

    cfg = load_config(args.config)
    set_seed(cfg["seed"])
    device = get_device(args.device)

    manifest = Path(cfg["data"]["processed_dir"]) / "split.csv"
    if not manifest.exists():
        raise SystemExit(
            f"Chưa có manifest '{manifest}'. Chạy trước:  python -m src.data.prepare"
        )

    loaders = build_dataloaders(cfg, manifest)
    arch = cfg["model"]["arch"]
    model = build_model(arch, cfg["model"]["pretrained"], cfg["model"]["dropout"]).to(device)

    if args.resume:
        model.load_state_dict(torch.load(args.resume, map_location=device)["state_dict"])
        print(f"Đã nạp trọng số từ {args.resume}")

    total_p, _ = count_parameters(model)
    print(f"Thiết bị: {device} | Kiến trúc: {arch} | Tham số: {total_p:,}")
    print(f"Số ảnh — train: {len(loaders['train'].dataset)}, "
          f"val: {len(loaders['val'].dataset)}, test: {len(loaders['test'].dataset)}")

    t = cfg["train"]
    criterion = nn.CrossEntropyLoss(label_smoothing=t["label_smoothing"])
    optimizer = torch.optim.AdamW(model.parameters(), lr=t["lr"], weight_decay=t["weight_decay"])
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=t["epochs"])
    scaler = torch.amp.GradScaler(device.type) if (t["amp"] and device.type == "cuda") else None

    freeze_epochs = t["freeze_backbone_epochs"]
    set_backbone_trainable(model, arch, trainable=freeze_epochs == 0)

    ckpt_dir = ensure_dir(cfg["paths"]["checkpoint_dir"])
    out_dir = ensure_dir(Path(cfg["paths"]["output_dir"]) / "logs")
    model_version = f"{arch}-{datetime.now():%Y%m%d-%H%M}"

    best_acc, patience, history = 0.0, 0, []
    start = time.time()

    for epoch in range(1, t["epochs"] + 1):
        # Hết giai đoạn đóng băng thì mở khoá backbone và hạ learning rate
        if epoch == freeze_epochs + 1 and freeze_epochs > 0:
            set_backbone_trainable(model, arch, trainable=True)
            for g in optimizer.param_groups:
                g["lr"] = t["lr"] * 0.1
            print(f"\n>>> Epoch {epoch}: mở khoá backbone, lr = {t['lr'] * 0.1:g}\n")

        tr_loss, tr_acc = run_epoch(model, loaders["train"], criterion, device,
                                    optimizer, scaler, f"Epoch {epoch}/{t['epochs']} [train]")
        va_loss, va_acc = run_epoch(model, loaders["val"], criterion, device,
                                    desc=f"Epoch {epoch}/{t['epochs']} [val]")
        scheduler.step()

        history.append({"epoch": epoch, "train_loss": tr_loss, "train_acc": tr_acc,
                        "val_loss": va_loss, "val_acc": va_acc,
                        "lr": optimizer.param_groups[0]["lr"]})
        print(f"Epoch {epoch:>3}/{t['epochs']} | "
              f"train loss {tr_loss:.4f} acc {tr_acc:.4f} | "
              f"val loss {va_loss:.4f} acc {va_acc:.4f}")

        if va_acc > best_acc:
            best_acc, patience = va_acc, 0
            torch.save({
                "arch": arch,
                "class_keys": class_keys(),
                "image_size": cfg["data"]["image_size"],
                "dropout": cfg["model"]["dropout"],
                "state_dict": model.state_dict(),
                "model_version": model_version,
                "epoch": epoch,
                "val_acc": va_acc,
            }, ckpt_dir / "best.pt")
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
    print(f"Checkpoint: {ckpt_dir / 'best.pt'}")
    print("Bước tiếp theo:  python -m src.evaluation.evaluate --checkpoint checkpoints/best.pt")


if __name__ == "__main__":
    main()
