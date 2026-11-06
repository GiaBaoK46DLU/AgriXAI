"""Nhắc lại dữ liệu nguồn và chưng cất để hạn chế quên sau fine-tune #50.

Chỉ gọi trước khi mở test. Teacher là checkpoint cha, loss chưng cất chỉ áp
trên ảnh PV train. PlantDoc train vẫn học bằng nhãn thật, không nhãn giả.
"""

import copy
import json
import random
import time

import torch
from torch.nn import functional as F
from torch.utils.data import DataLoader, Dataset

from src.data.domain_dataset import DomainDiseaseDataset
from src.models.build import load_checkpoint
from src.training.adapt_domain import (
    brief,
    digest,
    evaluate,
    initialize_worker,
    loader,
    write_json,
)
from src.utils.common import set_seed


def distillation_loss(student_logits, teacher_logits, temperature=2.0):
    return (
        F.kl_div(
            F.log_softmax(student_logits / temperature, dim=1),
            F.softmax(teacher_logits.detach() / temperature, dim=1),
            reduction="batchmean",
        )
        * temperature**2
    )


class RehearsalDataset(Dataset):
    def __init__(self, rows, keys, config):
        self.inner = DomainDiseaseDataset(rows, keys, config, training=True)

    def __len__(self):
        return len(self.inner)

    def __getitem__(self, index):
        image, label = self.inner[index]
        return image, label, self.inner.rows[index]["source"] == "plantvillage"


def rehearse_candidate(root, selection, validation, device="cuda", epochs=3):
    if (root / "evaluation").exists():
        raise RuntimeError("Không được học tiếp sau khi đã mở test")
    set_seed(2026)
    device = torch.device(device)
    inventory = json.loads((root / "training-inventory.json").read_text(encoding="utf-8"))
    test = json.loads((root / "test-inventory.json").read_text(encoding="utf-8"))
    lookup = {r["path"]: r["sha256"] for r in inventory}
    excluded = {r["sha256"] for r in test} | {
        lookup[r["path"]] for rows in validation.values() for r in rows
    }
    student, meta = load_checkpoint(str(root / "adaptation.pt"), device)
    teacher, _ = load_checkpoint("checkpoints/leaf_disease_detection_model.pt", device)
    teacher.requires_grad_(False).eval()
    cfg = copy.deepcopy(selection["config"])
    cfg["preprocess"]["leaf_crop"]["enabled"] = False
    cfg["augment"]["outdoor"]["enabled"] = False
    cfg["data"].update(batch_size=8, num_workers=2)
    rows = []
    rng = random.Random(2026)
    for key in meta["class_keys"]:
        group = [
            r
            for r in inventory
            if r["split"] == "train" and r["source"] == "plantvillage" and r["label"] == key
        ]
        rows += rng.sample(group, min(200, len(group)))
    rows += [r for r in inventory if r["split"] == "train" and r["source"] == "plantdoc"]
    assert not excluded & {r["sha256"] for r in rows}
    write_json(root / "rehearsal-inventory.json", rows)
    write_json(
        root / "rehearsal-protocol.json",
        {
            "seed": 2026,
            "epochs": epochs,
            "temperature": 2.0,
            "distillation_weight": 0.5,
            "student_parent_sha256": digest(root / "adaptation.pt"),
            "teacher_sha256": digest("checkpoints/leaf_disease_detection_model.pt"),
            "config": cfg,
            "test_overlap": [],
            "selection_rule": "eligible PV val >= .985; highest PD val macro-F1",
        },
    )
    train = DataLoader(
        RehearsalDataset(rows, meta["class_keys"], cfg),
        batch_size=8,
        shuffle=True,
        num_workers=2,
        persistent_workers=True,
        worker_init_fn=initialize_worker,
        pin_memory=device.type == "cuda",
    )
    validation_loaders = {
        source: loader(samples, meta["class_keys"], cfg) for source, samples in validation.items()
    }
    optimizer = torch.optim.AdamW(student.parameters(), lr=1e-5, weight_decay=1e-4)
    scaler = torch.amp.GradScaler(device.type, enabled=device.type == "cuda")
    best = (-1, -float("inf"))
    history = []
    checkpoint = root / "rehearsal.pt"
    for epoch in range(1, epochs + 1):
        started = time.perf_counter()
        student.train()
        optimizer.zero_grad(set_to_none=True)
        total_loss = 0.0
        n = 0
        for step, (images, labels, source) in enumerate(train):
            images, labels, source = images.to(device), labels.to(device), source.to(device)
            with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                logits = student(images)
                loss = F.cross_entropy(logits, labels, label_smoothing=0.05)
                if source.any():
                    with torch.no_grad():
                        reference = teacher(images[source])
                    loss = loss + 0.5 * distillation_loss(logits[source].float(), reference.float())
            group_start = (step // 4) * 4
            scaler.scale(loss / min(4, len(train) - group_start)).backward()
            if (step + 1) % 4 == 0 or step + 1 == len(train):
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)
            total_loss += float(loss.detach()) * len(labels)
            n += len(labels)
        values = {
            source: evaluate(student, data, device) for source, data in validation_loaders.items()
        }
        record = {
            "epoch": epoch,
            "train_loss": total_loss / n,
            "pv_val": brief(values["pv"]),
            "pd_val": brief(values["pd"]),
            "seconds": time.perf_counter() - started,
        }
        history.append(record)
        print("rehearsal", json.dumps(record), flush=True)
        eligible = values["pv"]["accuracy"] >= 0.985
        score = (
            int(eligible),
            values["pd"]["macro_f1_present"] if eligible else values["pv"]["accuracy"],
        )
        if score > best:
            best = score
            torch.save(
                {
                    **meta,
                    "state_dict": {k: v.detach().cpu() for k, v in student.state_dict().items()},
                    "selection": record,
                    "epoch": epoch,
                    "val_acc": values["pv"]["accuracy"],
                    "model_version": meta["model_version"] + "-rehearsal",
                    "rehearsal_teacher_sha256": digest(
                        "checkpoints/leaf_disease_detection_model.pt"
                    ),
                },
                checkpoint,
            )
            write_json(root / "rehearsal-validation.json", values)
        write_json(root / "rehearsal-history.json", history)
    del train, validation_loaders, student, teacher
    result = json.loads((root / "rehearsal-validation.json").read_text(encoding="utf-8"))
    selection["candidates"]["rehearsal"] = result
    eligible = [
        name
        for name, values in selection["candidates"].items()
        if values["pv"]["accuracy"] >= 0.985
    ]
    chosen = max(
        eligible or ["baseline"],
        key=lambda name: selection["candidates"][name]["pd"]["macro_f1_present"],
    )
    if chosen == "rehearsal":
        selection.update(
            selected=chosen,
            checkpoint=str(checkpoint),
            checkpoint_sha256=digest(checkpoint),
            config=cfg,
            crop_enabled=False,
        )
    selection["eligible"] = eligible
    return selection
