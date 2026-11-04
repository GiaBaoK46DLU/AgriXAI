"""So cắt/bỏ cắt cho checkpoint đã học, chỉ bằng validation trước khi mở test."""

import argparse
import copy
import json
from pathlib import Path

import torch

from src.evaluation.recalibrate_domain_bn import recalibrate_candidates
from src.models.build import load_checkpoint
from src.training.adapt_domain import brief, digest, evaluate, loader, write_json
from src.training.rehearse_domain import rehearse_candidate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    args = ap.parse_args()
    root = Path(args.run)
    if (root / "evaluation").exists():
        raise RuntimeError("Đã mở test, không được chọn lại preprocessing")
    selection = json.loads((root / "selection.json").read_text(encoding="utf-8"))
    validation = json.loads((root / "validation-rows.json").read_text(encoding="utf-8"))
    assert digest(selection["checkpoint"]) == selection["checkpoint_sha256"]
    metadata_audit = []
    # val_acc cũ đi theo metadata checkpoint cha. Đưa nó về số đo thực của
    # checkpoint con trước triển khai; chỉ sửa metadata, không sửa tensor.
    for name in ("augmentation", "adaptation"):
        path = root / f"{name}.pt"
        ckpt = torch.load(path, map_location="cpu", weights_only=False)
        actual = ckpt["selection"]["pv_val"]["accuracy"]
        if ckpt.get("val_acc") != actual:
            before_hash = digest(path)
            ckpt["parent_val_acc"] = ckpt.get("val_acc")
            ckpt["val_acc"] = actual
            torch.save(ckpt, path)
            reloaded = torch.load(path, map_location="cpu", weights_only=False)
            assert all(
                torch.equal(value, reloaded["state_dict"][key])
                for key, value in ckpt["state_dict"].items()
            )
            metadata_audit.append(
                {
                    "checkpoint": str(path),
                    "before_sha256": before_hash,
                    "after_sha256": digest(path),
                    "tensors_unchanged": True,
                    "val_acc": actual,
                }
            )
    write_json(root / "checkpoint-metadata-audit.json", metadata_audit)
    selection["checkpoint_sha256"] = digest(selection["checkpoint"])
    write_json(root / "selection-before-bn-check.json", selection)
    torch.set_num_threads(4)
    selection = recalibrate_candidates(root, selection, validation)
    # Không bỏ lợi ích học PlantDoc chỉ vì quên dữ liệu nguồn: thử nhắc lại
    # với teacher gốc trước khi quyết định chọn bản augmentation đơn thuần.
    write_json(root / "selection-before-rehearsal.json", selection)
    selection = rehearse_candidate(root, selection, validation)
    # Máy backend dùng CPU. Chốt checkpoint bằng validation trên đúng thiết bị
    # triển khai; không dùng các số đo test để đổi người thắng.
    selection["candidates_gpu"] = copy.deepcopy(selection["candidates"])
    cfg = copy.deepcopy(selection["config"])
    cfg["data"]["evaluation_batch_size"] = 1
    cfg["preprocess"]["leaf_crop"]["enabled"] = False
    seed_model, seed_meta = load_checkpoint("checkpoints/leaf_disease_detection_model.pt", "cpu")
    del seed_model
    validation_loaders = {
        source: loader(rows, seed_meta["class_keys"], cfg) for source, rows in validation.items()
    }
    cpu_candidates = {}
    paths = {}
    for name in selection["candidates"]:
        path = (
            Path("checkpoints/leaf_disease_detection_model.pt")
            if name == "baseline"
            else root / f"{name}.pt"
        )
        paths[name] = str(path)
        model, _ = load_checkpoint(str(path), "cpu")
        cpu_candidates[name] = {}
        for source, data in validation_loaders.items():
            cpu_candidates[name][source] = evaluate(model, data, torch.device("cpu"))
        print(
            "selection-cpu",
            name,
            {k: brief(v) for k, v in cpu_candidates[name].items()},
            flush=True,
        )
        del model
    del validation_loaders
    write_json(root / "candidate-validation-cpu.json", cpu_candidates)
    eligible = [
        name for name, values in cpu_candidates.items() if values["pv"]["accuracy"] >= 0.985
    ]
    chosen = max(
        eligible or ["baseline"], key=lambda name: cpu_candidates[name]["pd"]["macro_f1_present"]
    )
    selection.update(
        selected=chosen,
        checkpoint=paths[chosen],
        checkpoint_sha256=digest(paths[chosen]),
        candidates=cpu_candidates,
        eligible=eligible,
        selection_device="cpu",
        config=cfg,
        crop_enabled=False,
    )
    before = copy.deepcopy(selection)
    torch.set_num_threads(4)
    model, meta = load_checkpoint(selection["checkpoint"], "cpu")
    # Đối chứng không cắt đã có trong selection; chỉ chạy phần cắt còn thiếu.
    result = {}
    cfg = copy.deepcopy(selection["config"])
    cfg["preprocess"]["leaf_crop"]["enabled"] = not selection["crop_enabled"]
    for source, rows in validation.items():
        data = loader(rows, meta["class_keys"], cfg)
        result[source] = evaluate(model, data, torch.device("cpu"))
        del data
    original = selection["candidates"][selection["selected"]]
    use_alternative = (
        result["pv"]["accuracy"] >= 0.985
        and result["pd"]["macro_f1_present"] > original["pd"]["macro_f1_present"]
    )
    write_json(
        root / "crop-selection-validation.json",
        {
            "checkpoint_sha256": digest(selection["checkpoint"]),
            "before_selection_sha256": digest(root / "selection.json"),
            "alternative_crop_enabled": cfg["preprocess"]["leaf_crop"]["enabled"],
            "alternative": result,
            "accepted": use_alternative,
            "rule": "Only validation: PV accuracy >= 0.985, PD macro-F1 strictly improves",
        },
    )
    if use_alternative:
        selection["config"] = cfg
        selection["crop_enabled"] = cfg["preprocess"]["leaf_crop"]["enabled"]
    selection["selected_validation"] = result if use_alternative else original
    write_json(root / "selection-before-crop-check.json", before)
    write_json(root / "selection.json", selection)
    print("CROP_SELECTION", selection["crop_enabled"], {k: brief(v) for k, v in result.items()})


if __name__ == "__main__":
    main()
