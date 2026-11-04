"""Hiệu chỉnh BatchNorm bằng train, chọn biến thể bằng validation trước khi mở test.

Chỉ thay running_mean/running_var/num_batches_tracked. Không học thêm trọng số,
không bật dropout hoặc stochastic depth trong lượt đo thống kê.
"""

import copy
import json
import random

import torch
from torch.utils.data import DataLoader

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


def update_statistics(model, data, device):
    model.eval()
    layers = [m for m in model.modules() if isinstance(m, torch.nn.modules.batchnorm._BatchNorm)]
    if not layers:
        raise ValueError("Mô hình không có BatchNorm để hiệu chỉnh")
    momenta = [m.momentum for m in layers]
    for layer in layers:
        layer.reset_running_stats()
        layer.momentum = None
        layer.train()
    try:
        with torch.no_grad():
            for images, _ in data:
                model(images.to(device))
    finally:
        for layer, momentum in zip(layers, momenta):
            layer.momentum = momentum
        model.eval()


def recalibrate_candidates(root, selection, validation, device="cuda"):
    if (root / "evaluation").exists():
        raise RuntimeError("Không được chọn BN sau khi mở test")
    inventory = json.loads((root / "training-inventory.json").read_text(encoding="utf-8"))
    test = json.loads((root / "test-inventory.json").read_text(encoding="utf-8"))
    blocked = {r["sha256"] for r in test}
    lookup = {r["path"]: r["sha256"] for r in inventory}
    blocked |= {lookup[r["path"]] for rows in validation.values() for r in rows}
    rng = random.Random(42)
    sources = {}
    for source, count in (("plantvillage", 32), ("plantdoc", 12)):
        rows = [r for r in inventory if r["split"] == "train" and r["source"] == source]
        sampled = []
        for label in sorted({r["label"] for r in rows}):
            group = [r for r in rows if r["label"] == label]
            sampled += rng.sample(group, min(count, len(group)))
        assert not blocked & {r["sha256"] for r in sampled}
        sources[source] = sampled
    cfg = copy.deepcopy(selection["config"])
    cfg["preprocess"]["leaf_crop"]["enabled"] = False
    cfg["data"]["num_workers"] = 2
    variants = {
        "pv": sources["plantvillage"],
        "mixed": sources["plantvillage"] + sources["plantdoc"],
    }
    write_json(root / "bn-calibration-inventory.json", variants)
    results = {}
    for tag, rows in variants.items():
        model, meta = load_checkpoint(str(root / "adaptation.pt"), device)
        parameters = {k: v.detach().cpu().clone() for k, v in model.named_parameters()}
        calibration = DataLoader(
            DomainDiseaseDataset(rows, meta["class_keys"], cfg),
            batch_size=32,
            shuffle=True,
            generator=torch.Generator().manual_seed(42),
            num_workers=2,
            worker_init_fn=initialize_worker,
        )
        update_statistics(model, calibration, torch.device(device))
        del calibration
        assert all(
            torch.equal(parameters[k], v.detach().cpu()) for k, v in model.named_parameters()
        )
        result = {}
        for source, samples in validation.items():
            data = loader(samples, meta["class_keys"], cfg)
            result[source] = evaluate(model, data, torch.device(device))
            del data
            print("bn-validation", tag, source, brief(result[source]), flush=True)
        name = f"adaptation-bn-{tag}"
        path = root / f"{name}.pt"
        meta["state_dict"] = {k: v.detach().cpu() for k, v in model.state_dict().items()}
        meta["val_acc"] = result["pv"]["accuracy"]
        meta["model_version"] += f"-bn-{tag}"
        meta["selection"] = {
            **meta["selection"],
            "pv_val": brief(result["pv"]),
            "pd_val": brief(result["pd"]),
            "bn_calibration": tag,
        }
        meta["bn_calibration"] = {
            "source_checkpoint_sha256": digest(root / "adaptation.pt"),
            "images": len(rows),
            "parameters_unchanged": True,
        }
        torch.save(meta, path)
        result["checkpoint"] = str(path)
        result["checkpoint_sha256"] = digest(path)
        results[name] = result
        selection["candidates"][name] = {"pv": result["pv"], "pd": result["pd"]}
        del model, meta, parameters
    write_json(root / "bn-calibration-validation.json", results)
    eligible = [
        name
        for name, values in selection["candidates"].items()
        if values["pv"]["accuracy"] >= 0.985
    ]
    chosen = max(
        eligible or ["baseline"],
        key=lambda name: selection["candidates"][name]["pd"]["macro_f1_present"],
    )
    paths = {
        "baseline": "checkpoints/leaf_disease_detection_model.pt",
        "augmentation": str(root / "augmentation.pt"),
        "adaptation": str(root / "adaptation.pt"),
        **{name: value["checkpoint"] for name, value in results.items()},
    }
    selection.update(
        selected=chosen,
        checkpoint=paths[chosen],
        eligible=eligible,
        checkpoint_sha256=digest(paths[chosen]),
    )
    if chosen in results:
        selection["config"] = cfg
        selection["crop_enabled"] = False
    return selection
