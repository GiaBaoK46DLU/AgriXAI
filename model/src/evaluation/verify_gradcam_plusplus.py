"""Kiểm chứng độc lập các tệp đầu ra #98 mà không chạy lại lan truyền ngược."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from src.evaluation.compare_gradcam_plusplus import METHODS, ROOT, normalize, region_metrics, summarize, text_sha256
from src.evaluation.compare_xai import dump, read_samples, sha256
from src.predictor import DiseasePredictor


def verify(out: Path, checkpoint: Path) -> dict:
    sys.path.insert(0, str(ROOT.parent / "backend"))
    from app.services.xai.overlay import draw_regions

    protocol = json.loads((out / "protocol.json").read_text(encoding="utf-8"))
    records = json.loads((out / "per-image.json").read_text(encoding="utf-8"))
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    if sha256(checkpoint) != protocol["checkpoint_sha256"]:
        raise ValueError("Checkpoint đã thay đổi")
    for name, expected in protocol["sources_sha256"].items():
        if text_sha256(ROOT.parent / name) != expected:
            raise ValueError(f"Mã nguồn đã thay đổi: {name}")
    for dataset, expected in protocol["annotation_sha256"].items():
        if text_sha256(ROOT / f"outputs/audit-gradcam-17/{dataset}/khoanh-tay.json") != expected:
            raise ValueError(f"Mặt nạ tham chiếu đã thay đổi: {dataset}")
    samples = read_samples()
    saved = protocol["samples"]
    if [{k: v for k, v in row.items() if k != "annotation"} for row in samples] != saved:
        raise ValueError("Tập ảnh/nhãn/hash đầu vào không khớp")
    expected_keys = {(row["sample_id"], method) for row in samples for method in METHODS}
    actual_keys = [(row["sample_id"], row["method"]) for row in records]
    if len(actual_keys) != len(expected_keys) or set(actual_keys) != expected_keys:
        raise ValueError("Thiếu/trùng bản ghi phương pháp hoặc ảnh")
    by_key = {(row["sample_id"], row["method"]): row for row in records}
    for row in samples:
        original = Image.open(ROOT / row["path"]).convert("RGB")
        with np.load(out / "maps" / f"{row['sample_id']}.npz") as maps:
            for method in METHODS:
                record = by_key[row["sample_id"], method]
                heatmap, raw = maps[method], maps[method + "_raw"]
                if heatmap.shape != (224, 224) or not np.isfinite(raw).all() or (raw < 0).any():
                    raise ValueError("Kích thước hoặc giá trị bản đồ không hợp lệ")
                np.testing.assert_array_equal(heatmap, normalize(raw))
                full = DiseasePredictor._resize_heatmap(heatmap, *original.size)
                rendered = draw_regions(Image.new("RGB", original.size), full,
                                        protocol["overlay_threshold"])
                actual = region_metrics(heatmap, row["annotation"], np.asarray(rendered).any(2))
                for metric, value in actual.items():
                    if value is None or isinstance(value, bool):
                        if record[metric] != value:
                            raise ValueError(f"Sai {metric}: {row['sample_id']}")
                    else:
                        np.testing.assert_allclose(record[metric], value, rtol=0, atol=1e-12)
                if len(record["timings_ms"]) != protocol["repeats"] or min(record["timings_ms"]) <= 0:
                    raise ValueError("Thiếu số đo thời gian")
                np.testing.assert_allclose(record["explain_ms"], np.mean(record["timings_ms"]))
                if method == "gradcam_plusplus" and (record["reference_max_error"] > 2e-4
                                                       or record["reference_overlay_iou"] < .99):
                    raise ValueError("Không đạt đối chứng thư viện")
        a, b = (by_key[row["sample_id"], method] for method in METHODS)
        if (a["predicted"], a["confidence"], a["correct"]) != (b["predicted"], b["confidence"], b["correct"]):
            raise ValueError("Hai phương pháp không dùng cùng dự đoán/lớp mục tiêu")
        with Image.open(out / "figures" / f"{row['sample_id']}.png") as figure:
            figure.verify()
    for key, value in summarize(records).items():
        if summary[key] != value:
            raise ValueError(f"Bảng tổng hợp không khớp kết quả từng ảnh: {key}")
    if summary["image_count"] != len(samples) or summary["record_count"] != len(records):
        raise ValueError("Sai số lượng ảnh/bản ghi tổng hợp")
    result = {"passed": True, "images": len(samples), "records": len(records),
              "figures": len(samples), "maps": 2 * len(samples),
              "verifier_source_sha256": text_sha256(Path(__file__))}
    dump(out / "verification.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("outputs/gradcam-plus-plus-98"))
    parser.add_argument("--checkpoint", type=Path, default=Path("checkpoints/leaf_disease_detection_model.pt"))
    args = parser.parse_args()
    print(json.dumps(verify(args.out, args.checkpoint), ensure_ascii=False))
