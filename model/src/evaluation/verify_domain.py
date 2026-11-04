"""Kiểm chứng số liệu #50 bằng file dự đoán và kiểm tra cách ly dữ liệu."""

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import yaml
from sklearn.metrics import f1_score

from src.labels import class_keys
from src.training.adapt_domain import digest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    root = Path(args.run)

    def read(name):
        return json.loads((root / name).read_text(encoding="utf-8"))

    protocol = read("protocol.json")
    selection = read("selection.json")
    inventory = read("training-inventory.json")
    backgrounds = read("background-inventory.json")
    test = read("test-inventory.json")
    current_files = {r["path"]: r["sha256"] for r in inventory + backgrounds + test}
    for index, (path, expected) in enumerate(current_files.items(), 1):
        assert digest(path) == expected, f"Ảnh nguồn đã thay đổi: {path}"
        if index % 5000 == 0:
            print(f"Đã kiểm hash hiện tại của {index}/{len(current_files)} ảnh", flush=True)
    test_hashes = {r["sha256"] for r in test}
    assert not test_hashes & {r["sha256"] for r in inventory + backgrounds}
    assert not protocol["remaining_test_overlap"]
    assert not any(Path(r["path"]).name == "tomato_V8.jpg" for r in inventory)
    validation = read("validation-rows.json")
    train_hashes = {r["sha256"] for r in inventory if r["split"] == "train"}
    hashes_by_path = {r["path"]: r["sha256"] for r in inventory}
    assert not train_hashes & {
        hashes_by_path[r["path"]] for rows in validation.values() for r in rows
    }
    assert digest(selection["checkpoint"]) == selection["checkpoint_sha256"]
    cpu_candidates = read("candidate-validation-cpu.json")
    eligible = [
        name for name, values in cpu_candidates.items() if values["pv"]["accuracy"] >= 0.985
    ]
    assert selection["selection_device"] == "cpu"
    assert selection["selected"] == max(
        eligible, key=lambda name: cpu_candidates[name]["pd"]["macro_f1_present"]
    )
    for values in cpu_candidates.values():
        for source, rows in validation.items():
            result = values[source]
            truth = np.array([class_keys().index(row["label"]) for row in rows])
            pred = np.array(result["pred"])
            assert np.array_equal(truth, result["truth"])
            assert np.isclose((truth == pred).mean(), result["accuracy"])
            assert np.isclose(
                f1_score(truth, pred, labels=sorted(set(truth)), average="macro", zero_division=0),
                result["macro_f1_present"],
            )
    for name in ("augmentation", "adaptation"):
        checkpoint = torch.load(root / f"{name}.pt", map_location="cpu", weights_only=False)
        assert checkpoint["class_keys"] == class_keys()
        assert checkpoint["val_acc"] == checkpoint["selection"]["pv_val"]["accuracy"]
    parent = torch.load(root / "adaptation.pt", map_location="cpu", weights_only=False)
    bn_inventory = read("bn-calibration-inventory.json")
    validation_hashes = {hashes_by_path[r["path"]] for rows in validation.values() for r in rows}
    for tag, rows in bn_inventory.items():
        assert not (test_hashes | validation_hashes) & {r["sha256"] for r in rows}
        child = torch.load(root / f"adaptation-bn-{tag}.pt", map_location="cpu", weights_only=False)
        assert child["class_keys"] == class_keys()
        for name, value in parent["state_dict"].items():
            if not name.endswith(("running_mean", "running_var", "num_batches_tracked")):
                assert torch.equal(value, child["state_dict"][name]), name
    if (root / "rehearsal.pt").exists():
        rows = read("rehearsal-inventory.json")
        assert not (test_hashes | validation_hashes) & {r["sha256"] for r in rows}
        child = torch.load(root / "rehearsal.pt", map_location="cpu", weights_only=False)
        assert child["class_keys"] == class_keys()
    evaluation = root / "evaluation"
    manifest = read("evaluation/manifest.json")
    assert digest(root / "selection.json") == manifest["selection_sha256"]
    for name, expected in manifest["files"].items():
        assert digest(evaluation / name) == expected, name
    reports = read("evaluation/classification.json")
    for variant, groups in reports.items():
        for group in ("pv10", "pd8"):
            predictions = read(f"evaluation/predictions-{variant}-{group}.json")
            assert len(predictions) == (2719 if group == "pv10" else 66)
            assert all(row["truth"] == class_keys().index(row["label"]) for row in predictions)
            truth = np.array([r["truth"] for r in predictions])
            pred = np.array([r["prediction"] for r in predictions])
            probs = np.array([r["probabilities"] for r in predictions])
            assert np.array_equal(probs.argmax(1), pred)
            assert np.allclose(probs.sum(1), 1, atol=1e-5)
            assert np.isclose((truth == pred).mean(), groups[group]["accuracy"])
            assert np.isclose(
                f1_score(truth, pred, labels=sorted(set(truth)), average="macro", zero_division=0),
                groups[group]["macro_f1_present"],
            )
    cpu_reports = read("evaluation/classification-cpu.json")
    for variant, groups in cpu_reports.items():
        for group in ("pv10", "pd8"):
            predictions = read(f"evaluation/predictions-cpu-{variant}-{group}.json")
            assert len(predictions) == (2719 if group == "pv10" else 66)
            truth = np.array([class_keys().index(row["label"]) for row in predictions])
            pred = np.array([row["prediction"] for row in predictions])
            probs = np.array([row["probabilities"] for row in predictions])
            assert np.array_equal(probs.argmax(1), pred)
            assert np.isclose((truth == pred).mean(), groups[group]["accuracy"])
            assert np.isclose(
                f1_score(truth, pred, labels=sorted(set(truth)), average="macro", zero_division=0),
                groups[group]["macro_f1_present"],
            )
    summary = read("evaluation/guard-summary.json")
    assert summary["pv-test"]["n"] >= 300 and summary["negative-test"]["n"] >= 10
    for tag, values in summary.items():
        records = read(f"evaluation/guard-{tag}.json")
        assert len(records) == values["n"]
        assert sum(not r["accepted"] for r in records) == values["hidden"]
        assert sum(r["returned_heatmap_none"] for r in records) == values["hidden"]
        for row in records:
            if row["accepted"]:
                assert (
                    row["leaf_mass"] >= selection["config"]["xai"]["reliability"]["min_leaf_mass"]
                )
                assert row["leaf_lift"] >= selection["config"]["xai"]["reliability"]["min_lift"]
    system = read("evaluation/system-summary.json")
    for tag, values in system.items():
        records = read(f"evaluation/system-{tag}-predictions.json")
        assert len(records) == values["n"] == 66
        assert sum(r["rejected"] for r in records) == values["rejected"]
        assert np.isclose(sum(r["correct"] for r in records) / 66, values["overall_accuracy"])
    if (root / "api-http.json").exists():
        native = read("api-http.json")
        model_root = Path(__file__).resolve().parents[2]
        config_path = model_root / "configs/default.yaml"
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        assert (
            native["uses_real_auth"] and native["uses_real_loader"] and native["isolated_database"]
        )
        assert native["health"]["using_real_model"]
        assert native["checkpoint_sha256"] == selection["checkpoint_sha256"]
        assert native["default_config_sha256"] == digest(config_path)
        assert (
            digest(model_root / "checkpoints/leaf_disease_domain_adapted.pt")
            == selection["checkpoint_sha256"]
        )
        assert (
            config["xai"]["method"] == "gradcam_plusplus"
            and config["xai"]["reliability"]["enabled"]
        )
        assert config["preprocess"]["leaf_crop"]["enabled"] == selection["crop_enabled"]
        assert {key: value["status"] for key, value in native["cases"].items()} == {
            "visible": 201,
            "hidden": 201,
            "rejected": 422,
        }
    print("Đã kiểm chứng: cách ly hash, checkpoint, dự đoán từng ảnh, accuracy/F1 và chốt XAI")


if __name__ == "__main__":
    main()
