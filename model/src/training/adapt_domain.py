"""Thí nghiệm #93/#50: chốt cấu hình bằng validation, chưa đụng test.

Chạy từ model: python -u -m src.training.adapt_domain --out outputs/domain-50
Test chỉ được mở ở script đánh giá sau khi selection.json đã được ghi.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import time
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader

from src.data.domain_dataset import DomainDiseaseDataset
from src.data.gate_augment import background_pool
from src.data.prepare_plantdoc import IMAGE_SUFFIXES, PLANTDOC_DIR_TO_KEY
from src.models.build import load_checkpoint
from src.utils.common import load_config, set_seed


def digest(path):
    # Git có thể đổi CRLF/LF khi checkout trên máy khác. Chuẩn hoá chỉ file
    # văn bản; checkpoint và ảnh luôn so byte nghiêm ngặt.
    path = Path(str(path).replace("\\", "/"))
    if path.suffix.lower() in {".json", ".csv", ".yaml", ".yml", ".md", ".txt", ".log", ".py"}:
        return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_rows(path, source):
    with open(path, encoding="utf-8") as stream:
        return [dict(r, source=source) for r in csv.DictReader(stream)]


def initialize_worker(_):
    import cv2

    cv2.setNumThreads(0)


def loader(rows, keys, cfg, training=False):
    workers = cfg["data"].get("num_workers", 2)
    return DataLoader(
        DomainDiseaseDataset(rows, keys, cfg, training),
        batch_size=(
            cfg["data"].get("batch_size", 8)
            if training
            else cfg["data"].get("evaluation_batch_size", 32)
        ),
        shuffle=training,
        num_workers=workers,
        pin_memory=True,
        persistent_workers=workers > 0,
        worker_init_fn=initialize_worker,
    )


def evaluate(model, data, device):
    model.eval()
    truth, pred, prob = [], [], []
    with torch.no_grad():
        for images, labels in data:
            p = model(images.to(device)).softmax(1).cpu().numpy()
            truth.extend(labels.tolist())
            pred.extend(p.argmax(1).tolist())
            prob.extend(p.tolist())
    present = sorted(set(truth))
    return {
        "accuracy": float(np.mean(np.array(truth) == pred)),
        "macro_f1_present": float(
            f1_score(truth, pred, labels=present, average="macro", zero_division=0)
        ),
        "n": len(truth),
        "truth": truth,
        "pred": pred,
        "probabilities": prob,
    }


def brief(result):
    return {k: v for k, v in result.items() if k not in ("truth", "pred", "probabilities")}


def train_candidate(name, rows, pv_val, pd_val, cfg, original, device, out, epochs):
    model, meta = load_checkpoint(original, device)
    keys = meta["class_keys"]
    train_loader = loader(rows, keys, cfg, True)
    pv_loader, pd_loader = loader(pv_val, keys, cfg), loader(pd_val, keys, cfg)
    optimizer = torch.optim.AdamW(model.parameters(), lr=3e-5, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, epochs, eta_min=3e-6)
    criterion = torch.nn.CrossEntropyLoss(label_smoothing=0.05)
    scaler = torch.amp.GradScaler("cuda", enabled=device.type == "cuda")
    best_score, history = -float("inf"), []
    checkpoint = out / f"{name}.pt"
    for epoch in range(1, epochs + 1):
        started = time.perf_counter()
        model.train()
        loss_sum, hits, n = 0.0, 0, 0
        accumulation = cfg["train"].get("accumulation_steps", 4)
        optimizer.zero_grad(set_to_none=True)
        for batch_index, (images, labels) in enumerate(train_loader):
            images, labels = images.to(device), labels.to(device)
            with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                logits = model(images)
                loss = criterion(logits, labels)
            scaler.scale(loss / accumulation).backward()
            if (batch_index + 1) % accumulation == 0 or batch_index + 1 == len(train_loader):
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)
            n += len(labels)
            loss_sum += float(loss.detach()) * len(labels)
            hits += int((logits.argmax(1) == labels).sum())
            if (batch_index + 1) % 200 == 0:
                print(
                    name,
                    "epoch",
                    epoch,
                    "images",
                    n,
                    "seconds",
                    round(time.perf_counter() - started),
                    flush=True,
                )
        pv, pd = evaluate(model, pv_loader, device), evaluate(model, pd_loader, device)
        # Chọn augmentation bằng PV val, adaptation bằng PD val.
        # Phạt mạnh khi accuracy trên nguồn cũ giảm xuống dưới 98,5 %.
        score = pv["accuracy"] if name == "augmentation" else pd["macro_f1_present"]
        score -= max(0.0, 0.985 - pv["accuracy"]) * 10
        record = {
            "epoch": epoch,
            "train_loss": loss_sum / n,
            "train_accuracy": hits / n,
            "pv_val": brief(pv),
            "pd_val": brief(pd),
            "selection_score": score,
            "seconds": time.perf_counter() - started,
        }
        history.append(record)
        print(name, json.dumps(record), flush=True)
        if score > best_score:
            best_score = score
            state = {k: v.cpu() for k, v in model.state_dict().items()}
            torch.save(
                {
                    **{k: v for k, v in meta.items() if k != "state_dict"},
                    "state_dict": state,
                    "epoch": epoch,
                    "model_version": f"efficientnet_b0-domain50-{name}-{out.name}",
                    "domain_config": cfg,
                    "parent_sha256": digest(original),
                    "selection": record,
                },
                checkpoint,
            )
        write_json(out / f"{name}-history.json", history)
        scheduler.step()
    del train_loader, pv_loader, pd_loader, model
    torch.cuda.empty_cache()
    return checkpoint


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--augmentation-epochs", type=int, default=6)
    ap.add_argument("--adaptation-epochs", type=int, default=15)
    ap.add_argument("--train-batch-size", type=int, default=8)
    ap.add_argument("--num-workers", type=int, default=2)
    ap.add_argument("--reuse-crop-validation", default=None)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if (out / "protocol.json").exists():
        raise SystemExit("Thư mục đã có protocol, dùng --out mới để giữ chứng cứ")
    set_seed(42)
    torch.set_num_threads(4)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    pv = read_rows("data/processed/split.csv", "plantvillage")
    pd = read_rows("data/processed/plantdoc-official/split.csv", "plantdoc")
    pd_pool = []
    for folder, label in PLANTDOC_DIR_TO_KEY.items():
        if label == "spider_mites":
            continue
        for path in sorted((Path("data/field/plantdoc/train") / folder).rglob("*")):
            if path.is_file() and path.suffix in IMAGE_SUFFIXES and path.name != "tomato_V8.jpg":
                pd_pool.append(
                    {
                        "path": path.as_posix(),
                        "label": label,
                        "split": "train",
                        "source": "plantdoc",
                    }
                )
    assert len(pd_pool) == 674, len(pd_pool)
    pd_train, pd_val = train_test_split(
        pd_pool, test_size=0.2, random_state=42, stratify=[r["label"] for r in pd_pool]
    )
    for split, rows in (("train", pd_train), ("val", pd_val)):
        for row in rows:
            row["split"] = split
    pv_train = [r for r in pv if r["split"] == "train"]
    pv_val = [r for r in pv if r["split"] == "val"]
    test = [r for r in pv + pd if r["split"] == "test"]
    backgrounds = background_pool(Path("data/processed/gate-split.csv"))
    # Nhãn test chỉ phục vụ kiểm tra trùng, tuyệt đối không chọn epoch/ngưỡng.
    print("Đang kiểm tra hash ảnh train/val/test và nền", flush=True)
    test_inventory = [dict(r, sha256=digest(r["path"])) for r in test]
    test_hashes = {r["sha256"] for r in test_inventory}
    sources = pv_train + pv_val + pd_train + pd_val
    inventory = [dict(r, sha256=digest(r["path"])) for r in sources]
    bg_inventory = [{"path": str(p), "sha256": digest(p)} for p in backgrounds]
    overlap = test_hashes & {r["sha256"] for r in inventory + bg_inventory}
    dropped = [r for r in inventory + bg_inventory if r["sha256"] in overlap]
    write_json(out / "excluded-test-duplicates.json", dropped)
    write_json(out / "test-inventory.json", test_inventory)
    if overlap:
        # Không thay test lịch sử: loại bản sao khỏi dữ liệu học mới, ghi rõ
        # checkpoint cũ đã từng thấy bản sao nào để báo thêm PV test sạch.
        write_json(
            out / "baseline-test-exposure.json",
            [
                r
                for r in test_inventory
                if r["sha256"] in {v["sha256"] for v in inventory if v["split"] == "train"}
            ],
        )
        blocked_paths = {r["path"] for r in dropped}
        pv_train = [r for r in pv_train if r["path"] not in blocked_paths]
        pv_val = [r for r in pv_val if r["path"] not in blocked_paths]
        pd_train = [r for r in pd_train if r["path"] not in blocked_paths]
        pd_val = [r for r in pd_val if r["path"] not in blocked_paths]
        if any(r["path"] in blocked_paths for r in bg_inventory):
            raise RuntimeError("Ảnh nền train trùng test; phải làm sạch manifest nền trước")
        inventory = [r for r in inventory if r["path"] not in blocked_paths]
        print("Đã loại", len(dropped), "bản sao train/val trùng test", flush=True)
    # Một ảnh trùng giữa train và val cũng phải bị loại khỏi val.
    train_hashes = {r["sha256"] for r in inventory if r["split"] == "train"}
    pv_val = [r for r in pv_val if digest(r["path"]) not in train_hashes]
    pd_val = [r for r in pd_val if digest(r["path"]) not in train_hashes]
    original = "checkpoints/leaf_disease_detection_model.pt"
    cfg = load_config("configs/default.yaml")
    cfg["data"]["batch_size"] = args.train_batch_size
    cfg["data"]["num_workers"] = args.num_workers
    cfg["train"]["accumulation_steps"] = max(1, 32 // args.train_batch_size)
    cfg["preprocess"]["leaf_crop"]["enabled"] = False
    cfg["xai"]["reliability"]["enabled"] = False
    cfg["augment"]["outdoor"] = {
        "enabled": True,
        "background_manifest": "data/processed/gate-split.csv",
        "background_prob": 0.7,
        "light_prob": 0.5,
    }
    write_json(
        out / "protocol.json",
        {
            "seed": 42,
            "device": str(device),
            "torch": torch.__version__,
            "checkpoint_sha256": digest(original),
            "config": cfg,
            "test_overlap_hashes_removed": sorted(overlap),
            "remaining_test_overlap": [],
            "selection_rule": "PD validation macro-F1; PV validation accuracy >= 0.985 preferred; no test tuning",
            "augmentation_epochs": args.augmentation_epochs,
            "adaptation_epochs": args.adaptation_epochs,
        },
    )
    write_json(out / "training-inventory.json", inventory)
    write_json(out / "background-inventory.json", bg_inventory)
    write_json(out / "validation-rows.json", {"pv": pv_val, "pd": pd_val})
    model, meta = load_checkpoint(original, device)
    # Chốt cắt lá bằng validation trước các lần huấn luyện.
    ablation = {}
    if args.reuse_crop_validation:
        previous = Path(args.reuse_crop_validation)
        previous_protocol = json.loads((previous / "protocol.json").read_text(encoding="utf-8"))
        assert previous_protocol["checkpoint_sha256"] == digest(original)
        previous_rows = json.loads((previous / "validation-rows.json").read_text(encoding="utf-8"))
        assert previous_rows == {"pv": pv_val, "pd": pd_val}
        previous_hashes = {
            r["path"]: r["sha256"]
            for r in json.loads((previous / "training-inventory.json").read_text(encoding="utf-8"))
        }
        assert all(previous_hashes[r["path"]] == r["sha256"] for r in inventory)
        ablation = json.loads((previous / "crop-validation.json").read_text(encoding="utf-8"))
        print("Tái sử dụng đo cắt lá: hash checkpoint, ảnh và validation đều khớp", flush=True)
    for crop in () if ablation else (False, True):
        cfg["preprocess"]["leaf_crop"]["enabled"] = crop
        ablation[str(crop)] = {}
        for source, rows in (("pv", pv_val), ("pd", pd_val)):
            data = loader(rows, meta["class_keys"], cfg)
            ablation[str(crop)][source] = evaluate(model, data, device)
            del data
        print(
            "crop_validation",
            crop,
            {k: brief(v) for k, v in ablation[str(crop)].items()},
            flush=True,
        )
    use_crop = (
        ablation["True"]["pd"]["accuracy"] > ablation["False"]["pd"]["accuracy"]
        and ablation["True"]["pv"]["accuracy"] >= ablation["False"]["pv"]["accuracy"] - 0.01
    )
    cfg["preprocess"]["leaf_crop"]["enabled"] = use_crop
    write_json(out / "crop-validation.json", ablation)
    del model
    aug = train_candidate(
        "augmentation",
        pv_train,
        pv_val,
        pd_val,
        cfg,
        original,
        device,
        out,
        args.augmentation_epochs,
    )
    # Học lại ảnh nguồn đủ 10 lớp, giữ cả hai lớp không có trong PlantDoc.
    rng = random.Random(42)
    replay = []
    for label in meta["class_keys"]:
        subset = [r for r in pv_train if r["label"] == label]
        replay += rng.sample(subset, min(250, len(subset)))
    # Hai thử nghiệm đều bắt đầu từ checkpoint gốc để so công bằng.
    adapted = train_candidate(
        "adaptation",
        replay + pd_train * 5,
        pv_val,
        pd_val,
        cfg,
        original,
        device,
        out,
        args.adaptation_epochs,
    )
    candidates = {}
    for name, path in (("baseline", original), ("augmentation", aug), ("adaptation", adapted)):
        model, _ = load_checkpoint(str(path), device)
        candidates[name] = {}
        for source, rows in (("pv", pv_val), ("pd", pd_val)):
            data = loader(rows, meta["class_keys"], cfg)
            candidates[name][source] = evaluate(model, data, device)
            del data
        del model
    eligible = [name for name, values in candidates.items() if values["pv"]["accuracy"] >= 0.985]
    selected = max(
        eligible or ["baseline"], key=lambda name: candidates[name]["pd"]["macro_f1_present"]
    )
    paths = {"baseline": original, "augmentation": str(aug), "adaptation": str(adapted)}
    write_json(
        out / "selection.json",
        {
            "selected": selected,
            "checkpoint": paths[selected],
            "checkpoint_sha256": digest(paths[selected]),
            "crop_enabled": use_crop,
            "candidates": candidates,
            "eligible": eligible,
            "config": cfg,
        },
    )
    print("SELECTION", selected, "crop", use_crop, flush=True)


if __name__ == "__main__":
    main()
