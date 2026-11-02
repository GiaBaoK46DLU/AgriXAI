"""Kiểm chứng tính đầy đủ và nhất quán của kết quả #122, không sửa kết quả."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from src.evaluation.compare_xai import METHODS, ROOT, sha256


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def text_hash_matches(path: Path, expected: str) -> bool:
    """Chấp nhận LF/CRLF do Git chuyển đổi, vẫn chặn mọi khác biệt nội dung."""
    content = path.read_bytes()
    lf = content.replace(b"\r\n", b"\n")
    return expected in {hashlib.sha256(candidate).hexdigest()
                        for candidate in (content, lf, lf.replace(b"\n", b"\r\n"))}


def verify_run(directory: Path, expected_count: int) -> dict:
    protocol = load(directory / "protocol.json")
    config = protocol["config"]
    assert text_hash_matches(ROOT / "src/evaluation/compare_xai.py", config["script_sha256"]), "Mã chạy khác hash đã lưu"
    assert config["checkpoint_sha256"] == sha256(ROOT / "checkpoints/leaf_disease_detection_model.pt"), "Checkpoint đã đổi"
    assert text_hash_matches(ROOT.parent / "shared/data/tomato_diseases.json", config["catalog_sha256"]), "Danh mục đã đổi"
    assert text_hash_matches(ROOT / "src/xai/gradcam.py", config["gradcam_source_sha256"]), "Grad-CAM sản phẩm đã đổi"
    assert len(config["sample_ids"]) == expected_count
    assert len(set(config["sample_ids"])) == expected_count
    expected_records = expected_count * len(METHODS) * len(config["seeds"])
    files = list((directory / "records").glob("*.json"))
    assert len(files) == expected_records, (len(files), expected_records)
    records, empty = {}, []
    for sample in protocol["samples"]:
        sample_id = sample["sample_id"]
        assert sample["image_sha256"] == sha256(ROOT / sample["path"])
        assert (directory / "images" / f"{sample_id}.png").is_file()
        for method in METHODS:
            for seed in config["seeds"]:
                name = f"{sample_id}--{method}--{seed}"
                record = load(directory / "records" / f"{name}.json")
                records[(sample_id, method, seed)] = record
                assert (record["sample_id"], record["method"], record["seed"]) == (sample_id, method, seed)
                reference = records.get((sample_id, "gradcam", config["seeds"][0]))
                if reference:
                    assert record["predicted"] == reference["predicted"]
                    assert abs(record["confidence"] - reference["confidence"]) < 1e-6
                assert record["total_ms"] > 0 and record["forward_images"] > 0
                heatmap = np.load(directory / "maps" / f"{name}.npz")["heatmap"]
                assert heatmap.shape == (config["image_size"], config["image_size"])
                assert np.isfinite(heatmap).all() and (heatmap >= 0).all()
                if not record["valid_map"]:
                    empty.append(name)
                if method == "gradcam":
                    assert record["forward_images"] == record["forward_calls"] == record["backward_passes"] == 1
                else:
                    assert record["backward_passes"] == 0
                    coefficients = np.asarray(record["signed_region_weights"])
                    assert np.isclose(heatmap.sum(), np.maximum(coefficients, 0).sum(), rtol=1e-5, atol=1e-6)
                    if method == "lime":
                        assert record["forward_images"] == config["perturbations"]
                    else:
                        assert abs(record["expected_value"] + coefficients.sum() - record["confidence"]) < 1e-5
                if not config["timing_only"]:
                    assert 0 <= record["deletion_auc"] <= 1
                    assert 0 <= record["insertion_auc"] <= 1
                    assert record["curve_area"][0] == 0 and record["curve_area"][-1] == 1
    # Kiểm tra bảng tổng hợp lấy trung bình theo ảnh, không coi seed là ảnh độc lập.
    summary = load(directory / "summary.json")
    per_image = load(directory / "per-image.json")
    assert summary["record_count"] == expected_records
    assert len(per_image) == expected_count * len(METHODS)
    for method in METHODS:
        for metric, aggregate in summary["by_dataset"]["all"][method].items():
            values = [row[metric] for row in per_image if row["method"] == method and row[metric] is not None]
            assert aggregate["n_images"] == len(values)
            assert abs(aggregate["mean"] - np.mean(values)) < 1e-9
    return {"directory": str(directory), "images": expected_count, "records": expected_records,
            "empty_positive_maps": len(empty), "checks": "passed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=ROOT / "outputs/xai-comparison-122")
    args = parser.parse_args()
    results = [verify_run(args.base / "quality", 56), verify_run(args.base / "cpu", 19)]
    assert len(list((args.base / "gallery").glob("*.png"))) == 56
    print(json.dumps({"runs": results, "gallery_images": 56}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
