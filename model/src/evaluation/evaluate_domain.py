"""Mở test sạch sau selection; lưu dự đoán từng ảnh, CI ghép cặp, kiểm XAI."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image
from scipy.stats import binomtest
from sklearn.metrics import classification_report, confusion_matrix

from src.data.leaf_crop import locate_leaf
from src.evaluation.evaluate import wilson_interval
from src.predictor import DiseasePredictor
from src.training.adapt_domain import (
    brief,
    digest,
    evaluate,
    loader,
    read_rows,
    write_json,
)
from src.xai.reliability import assess_heatmap


def statistics(result, keys):
    truth, pred = np.array(result["truth"]), np.array(result["pred"])
    report = classification_report(
        truth,
        pred,
        labels=list(range(len(keys))),
        target_names=keys,
        output_dict=True,
        zero_division=0,
    )
    present = [k for i, k in enumerate(keys) if (truth == i).any()]
    return {
        **brief(result),
        "macro_f1_present": float(np.mean([report[k]["f1-score"] for k in present])),
        "accuracy_ci95": wilson_interval(int((truth == pred).sum()), len(truth)),
        "class_keys": keys,
        "per_class": {k: report[k] for k in keys},
        "classes_present": present,
        "confusion_matrix": confusion_matrix(truth, pred, labels=range(len(keys))).tolist(),
    }


def paired(before, after):
    a = np.array(before["truth"]) == before["pred"]
    b = np.array(after["truth"]) == after["pred"]
    assert before["truth"] == after["truth"]
    delta = b.astype(float) - a.astype(float)
    rng = np.random.default_rng(42)
    boot = np.array([rng.choice(delta, len(delta), replace=True).mean() for _ in range(10000)])
    gained = int((~a & b).sum())
    lost = int((a & ~b).sum())
    return {
        "accuracy_delta": float(delta.mean()),
        "paired_bootstrap_ci95": np.quantile(boot, [0.025, 0.975]).tolist(),
        "wrong_to_correct": gained,
        "correct_to_wrong": lost,
        "mcnemar_exact_p": float(binomtest(gained, gained + lost, 0.5).pvalue)
        if gained + lost
        else 1.0,
    }


def stratified_sample(rows, per_class=30):
    selected = []
    for label in sorted({r["label"] for r in rows}):
        group = [r for r in rows if r["label"] == label]
        rng = np.random.default_rng(42)
        selected += [
            group[i] for i in rng.choice(len(group), min(per_class, len(group)), replace=False)
        ]
    return selected


def guard_probe(checkpoint, rows, cfg, out, tag):
    import yaml

    raw_cfg = copy.deepcopy(cfg)
    raw_cfg["xai"]["reliability"]["enabled"] = False
    path = out / f"probe-{tag}.yaml"
    path.write_text(yaml.safe_dump(raw_cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
    predictor = DiseasePredictor(checkpoint, device="cuda", xai_config_path=path)
    options = dict(cfg["preprocess"]["leaf_crop"])
    options.pop("enabled")
    thresholds = dict(cfg["xai"]["reliability"])
    thresholds.pop("enabled")
    records = []
    for index, row in enumerate(rows):
        with Image.open(row["path"]) as opened:
            image = opened.convert("RGB")
        result = predictor.predict(image)
        region = locate_leaf(image, **options)
        decision = assess_heatmap(result.heatmap, region.mask, **thresholds)
        # Đếm kết quả thật của predict(), không chỉ suy ra từ công thức chốt.
        predictor.reliability_enabled = True
        guarded = predictor.predict(image)
        predictor.reliability_enabled = False
        assert guarded.probabilities == result.probabilities
        assert guarded.disease_key == result.disease_key
        assert (guarded.heatmap is not None) == decision["accepted"]
        records.append(
            {
                **row,
                "prediction": result.disease_key,
                "confidence": result.confidence,
                "correct": result.disease_key == row["label"],
                "region": region.reason,
                "box": region.box,
                "raw_latency_ms": result.latency_ms,
                "latency_ms": guarded.latency_ms,
                "returned_heatmap_none": guarded.heatmap is None,
                **decision,
            }
        )
        if index < 6 and tag in ("pv-test", "pd-test"):
            make_gallery(image, result.heatmap, region, decision, out / f"{tag}-{index + 1}.png")
        if (index + 1) % 50 == 0:
            print("guard", tag, index + 1, flush=True)
    predictor.close()
    write_json(out / f"guard-{tag}.json", records)
    accepted = [r for r in records if r["accepted"]]
    return {
        "n": len(records),
        "hidden": sum(not r["accepted"] for r in records),
        "reasons": {
            reason: sum(r["reason"] == reason for r in records)
            for reason in sorted({r["reason"] for r in records})
        },
        "accepted_accuracy": sum(r["correct"] for r in accepted) / len(accepted)
        if accepted
        else None,
        "all_accuracy": sum(r["correct"] for r in records) / len(records),
    }


def system_probe(checkpoint, rows, config_path, out, tag, device="cuda"):
    """Tính cả ảnh lá bị gate từ chối vào mẫu số, không chỉ báo accuracy có điều kiện."""
    predictor = DiseasePredictor(
        checkpoint,
        device=device,
        gate_checkpoint="checkpoints/organ_gate.pt",
        xai_config_path=config_path,
    )
    backend_dir = str(Path(__file__).resolve().parents[3] / "backend")
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from app.services.storage.local import open_and_normalize

    records = []
    for row in rows:
        image = open_and_normalize(Path(row["path"]).read_bytes())
        result = predictor.predict(image, with_heatmap=False)
        records.append(
            {
                **row,
                "prediction": result.disease_key,
                "correct": result.disease_key == row["label"],
                "rejected": result.disease_key == "not_tomato_leaf",
                "model_version": result.model_version,
            }
        )
    predictor.close()
    accepted = [r for r in records if not r["rejected"]]
    write_json(out / f"system-{tag}-predictions.json", records)
    return {
        "n": len(records),
        "rejected": sum(r["rejected"] for r in records),
        "overall_accuracy": sum(r["correct"] for r in records) / len(records),
        "accepted_accuracy": sum(r["correct"] for r in accepted) / len(accepted)
        if accepted
        else None,
        "gate_checkpoint_sha256": digest("checkpoints/organ_gate.pt"),
        "disease_checkpoint_sha256": digest(checkpoint),
        "includes_backend_image_normalization": True,
    }


def make_gallery(image, heatmap, region, decision, path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    axes[0].imshow(image)
    x0, y0, x1, y1 = region.box
    axes[0].add_patch(
        Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, edgecolor="red", linewidth=2)
    )
    axes[0].set_title("Ảnh gốc, khung lá ước lượng")
    axes[1].imshow(image)
    axes[1].imshow(heatmap, cmap="jet", alpha=0.45, vmin=0, vmax=1)
    axes[1].set_title("Heatmap về toạ độ ảnh gốc")
    axes[2].imshow(image)
    backend_dir = str(Path(__file__).resolve().parents[3] / "backend")
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    from app.services.xai.overlay import draw_regions, has_visible_region

    if decision["accepted"]:
        axes[2].imshow(draw_regions(image, heatmap))
    axes[2].set_title(
        (
            "Vùng khoanh thực từ backend"
            if has_visible_region(heatmap)
            else "Qua chốt, vùng quá nhỏ để vẽ"
        )
        if decision["accepted"]
        else "Ẩn vùng khoanh: " + decision["reason"]
    )
    for ax in axes:
        ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    args = ap.parse_args()
    root = Path(args.run)
    selection = json.loads((root / "selection.json").read_text(encoding="utf-8"))
    assert digest(selection["checkpoint"]) == selection["checkpoint_sha256"]
    out = root / "evaluation"
    out.mkdir(exist_ok=False)
    cfg = selection["config"]
    cfg["xai"]["reliability"]["enabled"] = True
    torch.set_num_threads(4)
    device = torch.device("cuda")
    pv = [r for r in read_rows("data/processed/split.csv", "plantvillage") if r["split"] == "test"]
    pd = read_rows("data/processed/plantdoc-official/split.csv", "plantdoc")
    assert len(pv) == 2719 and len(pd) == 66
    baseline = "checkpoints/leaf_disease_detection_model.pt"
    runs = {
        "baseline-full": (baseline, False),
        "baseline-crop": (baseline, True),
        "augmentation": (str(root / "augmentation.pt"), False),
        "adaptation": (str(root / "adaptation.pt"), False),
    }
    for name in ("adaptation-bn-pv", "adaptation-bn-mixed", "rehearsal"):
        if (root / f"{name}.pt").exists():
            runs[name] = (str(root / f"{name}.pt"), False)
    if selection["crop_enabled"] and selection["selected"] != "baseline":
        runs["selected-crop"] = (selection["checkpoint"], True)
    results = {}
    full_predictions = {}
    for name, (checkpoint, crop) in runs.items():
        from src.models.build import load_checkpoint

        model, meta = load_checkpoint(checkpoint, device)
        run_cfg = copy.deepcopy(cfg)
        run_cfg["preprocess"]["leaf_crop"]["enabled"] = crop
        results[name] = {}
        full_predictions[name] = {}
        for source, rows in (("pv10", pv), ("pd8", pd)):
            data = loader(rows, meta["class_keys"], run_cfg)
            result = evaluate(model, data, device)
            del data
            full_predictions[name][source] = result
            results[name][source] = statistics(result, meta["class_keys"])
            write_json(
                out / f"predictions-{name}-{source}.json",
                [
                    {**r, "truth": y, "prediction": p, "probabilities": probs}
                    for r, y, p, probs in zip(
                        rows, result["truth"], result["pred"], result["probabilities"]
                    )
                ],
            )
            if source == "pv10":
                present_pd = {r["label"] for r in pd}
                keep = [i for i, r in enumerate(rows) if r["label"] in present_pd]
                sub = {
                    key: [result[key][i] for i in keep]
                    for key in ("truth", "pred", "probabilities")
                }
                sub["n"] = len(keep)
                sub["accuracy"] = float(np.mean(np.array(sub["truth"]) == sub["pred"]))
                sub["macro_f1_present"] = float(
                    np.mean([results[name][source]["per_class"][k]["f1-score"] for k in present_pd])
                )
                results[name]["pv8"] = statistics(sub, meta["class_keys"])
                exposed = (
                    json.loads((root / "baseline-test-exposure.json").read_text(encoding="utf-8"))
                    if (root / "baseline-test-exposure.json").exists()
                    else []
                )
                excluded_paths = {r["path"] for r in exposed}
                clean = [i for i, r in enumerate(rows) if r["path"] not in excluded_paths]
                sub = {
                    key: [result[key][i] for i in clean]
                    for key in ("truth", "pred", "probabilities")
                }
                sub.update(
                    n=len(clean), accuracy=float(np.mean(np.array(sub["truth"]) == sub["pred"]))
                )
                results[name]["pv10-clean"] = statistics(sub, meta["class_keys"])
            print(name, source, brief(result), flush=True)
        del model
        write_json(out / "classification.json", results)
    selected_name = (
        ("selected-crop" if selection["crop_enabled"] else selection["selected"])
        if selection["selected"] != "baseline"
        else "baseline-" + ("crop" if selection["crop_enabled"] else "full")
    )
    comparison = {
        source: paired(
            full_predictions["baseline-full"][source], full_predictions[selected_name][source]
        )
        for source in ("pv10", "pd8")
    }
    write_json(out / "paired-comparison.json", comparison)
    # Backend demo dùng CPU: kiểm cả độ chính xác CPU, không chỉ latency.
    # Không chọn lại model theo các số đo test này.
    cpu_reports = {}
    cpu_predictions = {}
    cpu_disagreement = {}
    for name, path, crop in (
        ("baseline", baseline, False),
        ("selected", selection["checkpoint"], selection["crop_enabled"]),
    ):
        model, meta = load_checkpoint(path, "cpu")
        cpu_cfg = copy.deepcopy(cfg)
        cpu_cfg["preprocess"]["leaf_crop"]["enabled"] = crop
        cpu_reports[name] = {}
        cpu_predictions[name] = {}
        cpu_disagreement[name] = {}
        for source, rows in (("pv10", pv), ("pd8", pd)):
            data = loader(rows, meta["class_keys"], cpu_cfg)
            result = evaluate(model, data, torch.device("cpu"))
            del data
            cpu_predictions[name][source] = result
            cpu_reports[name][source] = statistics(result, meta["class_keys"])
            write_json(
                out / f"predictions-cpu-{name}-{source}.json",
                [
                    {**r, "truth": y, "prediction": p, "probabilities": probs}
                    for r, y, p, probs in zip(
                        rows, result["truth"], result["pred"], result["probabilities"]
                    )
                ],
            )
            reference = full_predictions["baseline-full" if name == "baseline" else selected_name][
                source
            ]
            cpu_disagreement[name][source] = int(
                np.sum(np.array(reference["pred"]) != result["pred"])
            )
            print("cpu", name, source, brief(result), flush=True)
        del model
        write_json(out / "classification-cpu.json", cpu_reports)
    write_json(out / "cpu-gpu-disagreement.json", cpu_disagreement)
    write_json(
        out / "paired-comparison-cpu.json",
        {
            source: paired(cpu_predictions["baseline"][source], cpu_predictions["selected"][source])
            for source in ("pv10", "pd8")
        },
    )
    validation = json.loads((root / "validation-rows.json").read_text(encoding="utf-8"))
    guard = {}
    for tag, rows in (
        ("pv-validation", stratified_sample(validation["pv"])),
        ("pd-validation", validation["pd"]),
        ("pv-test", stratified_sample(pv)),
        ("pd-test", pd),
    ):
        guard[tag] = guard_probe(selection["checkpoint"], rows, cfg, out, tag)
        write_json(out / "guard-summary.json", guard)
    with open("data/processed/gate-split.csv", encoding="utf-8") as stream:
        negatives = [
            r
            for r in csv.DictReader(stream)
            if r["label"] == "not_tomato_leaf" and r["split"] == "test"
        ]
    guard["negative-test"] = guard_probe(
        selection["checkpoint"], negatives, cfg, out, "negative-test"
    )
    write_json(out / "guard-summary.json", guard)
    import yaml

    (out / "deployment.yaml").write_text(
        yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    system = {}
    baseline_cfg = copy.deepcopy(cfg)
    baseline_cfg["preprocess"]["leaf_crop"]["enabled"] = False
    (out / "baseline-system.yaml").write_text(
        yaml.safe_dump(baseline_cfg, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    for tag, checkpoint, config_path in (
        ("baseline", baseline, out / "baseline-system.yaml"),
        ("selected", selection["checkpoint"], out / "deployment.yaml"),
    ):
        system[tag] = system_probe(checkpoint, pd, config_path, out, tag)
        write_json(out / "system-summary.json", system)
        print("system", tag, system[tag], flush=True)
    for tag, checkpoint, config_path in (
        ("baseline-cpu", baseline, out / "baseline-system.yaml"),
        ("selected-cpu", selection["checkpoint"], out / "deployment.yaml"),
    ):
        system[tag] = system_probe(checkpoint, pd, config_path, out, tag, device="cpu")
        write_json(out / "system-summary.json", system)
    predictor = DiseasePredictor(
        selection["checkpoint"], device="cpu", xai_config_path=out / "deployment.yaml"
    )
    latencies = {}
    for crop, reliability in ((False, False), (True, False), (False, True), (True, True)):
        predictor.crop_enabled = crop
        predictor.reliability_enabled = reliability
        values = []
        for row in pv[:33]:
            with Image.open(row["path"]) as opened:
                image = opened.convert("RGB")
            values.append(predictor.predict(image).latency_ms)
        latencies[f"crop_{crop}_guard_{reliability}"] = {
            "n": 32,
            "median_ms": float(np.median(values[1:])),
            "p95_ms": float(np.quantile(values[1:], 0.95)),
        }
    predictor.close()
    write_json(out / "cpu-latency.json", latencies)
    # Đối chiếu mask màu với phiếu khoanh mù có sẵn, không dùng để chọn ngưỡng.
    # Phiếu do AI khoanh, chưa phải ground truth của chuyên gia.
    masks = []
    for source in ("pv", "pd"):
        annotations = json.loads(
            Path(f"outputs/audit-gradcam-17/{source}/khoanh-tay.json").read_text(encoding="utf-8")
        )["annotations"]
        for sample, annotation in annotations.items():
            image_path = Path(f"outputs/xai-comparison-122/quality/images/{sample}.png")
            if not image_path.exists():
                continue
            with Image.open(image_path) as opened:
                image = opened.convert("RGB")
            region = locate_leaf(image)
            cells = np.array([list(row) for row in annotation["luoi"]])
            reference = cv2.resize(
                (cells != "N").astype(np.uint8), image.size, interpolation=cv2.INTER_NEAREST
            ).astype(bool)
            found = region.mask
            iou = (
                float((found & reference).sum() / (found | reference).sum())
                if found is not None
                else None
            )
            masks.append({"sample": sample, "reason": region.reason, "mask_iou_ai_reference": iou})
    write_json(out / "mask-audit.json", masks)
    write_json(
        out / "manifest.json",
        {
            "hash_mode": "binary SHA-256; text files CRLF normalized to LF",
            "selection_sha256": digest(root / "selection.json"),
            "files": {p.name: digest(p) for p in out.iterdir() if p.is_file()},
            "test_count": {"plantvillage": 2719, "plantdoc": 66},
            "selected_before_test": True,
            "selected_run": selected_name,
        },
    )
    print("EVALUATION_COMPLETE", json.dumps(comparison), flush=True)


if __name__ == "__main__":
    main()
