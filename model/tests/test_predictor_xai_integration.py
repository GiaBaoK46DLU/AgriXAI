"""Kiểm tra tích hợp bằng checkpoint thật; tự bỏ qua nếu máy chưa tải dữ liệu."""

import csv
from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image
from src.predictor import DiseasePredictor

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def predictors(tmp_path_factory):
    checkpoint = ROOT / "checkpoints/leaf_disease_detection_model.pt"
    gate = ROOT / "checkpoints/organ_gate.pt"
    if not checkpoint.is_file() or not gate.is_file():
        pytest.skip("Cần checkpoint bệnh và bộ chặn thật để kiểm tra tích hợp")
    original_threads = torch.get_num_threads()
    torch.set_num_threads(4)
    config = tmp_path_factory.mktemp("xai") / "config.yaml"
    config.write_text("xai:\n  method: gradcam_plusplus\n", encoding="utf-8")
    # Tách phép so thuật toán XAI khỏi chốt hiển thị/cắt ảnh của #90/#93.
    baseline = DiseasePredictor(
        checkpoint, device="cpu", xai_method="gradcam", xai_config_path=config
    )
    upgraded = DiseasePredictor(checkpoint, device="cpu", xai_config_path=config)
    gated = DiseasePredictor(checkpoint, device="cpu", xai_config_path=config, gate_checkpoint=gate)
    try:
        assert baseline.xai_method == "gradcam"
        assert upgraded.xai_method == "gradcam_plusplus"
        yield baseline, upgraded, gated
    finally:
        for predictor in (baseline, upgraded, gated):
            predictor.close()
        torch.set_num_threads(original_threads)


def test_reliability_switch_preserves_classification_with_real_checkpoint(tmp_path):
    from src.data.leaf_crop import locate_leaf
    from src.xai.reliability import assess_heatmap

    checkpoint = ROOT / "checkpoints/leaf_disease_detection_model.pt"
    if not checkpoint.exists():
        pytest.skip("Cần checkpoint thật")
    config = tmp_path / "guard.yaml"
    config.write_text(
        "xai:\n  method: gradcam_plusplus\n  reliability:\n"
        "    enabled: true\n    min_leaf_mass: 0.65\n    min_lift: 0.05\n",
        encoding="utf-8",
    )
    threads = torch.get_num_threads()
    torch.set_num_threads(4)
    predictor = DiseasePredictor(checkpoint, device="cpu", xai_config_path=config)
    try:
        for sample in ("pv-bacterial_spot-3", "pv-septoria_leaf_spot-2", "pd-septoria_leaf_spot-2"):
            image = Image.open(
                ROOT / f"outputs/xai-comparison-122/quality/images/{sample}.png"
            ).convert("RGB")
            guarded = predictor.predict(image)
            predictor.reliability_enabled = False
            original = predictor.predict(image)
            predictor.reliability_enabled = True
            assert guarded.probabilities == original.probabilities
            assert guarded.disease_key == original.disease_key
            expected = assess_heatmap(original.heatmap, locate_leaf(image).mask)["accepted"]
            assert (guarded.heatmap is not None) == expected
    finally:
        predictor.close()
        torch.set_num_threads(threads)


def test_backend_constructor_reads_current_default_config():
    import yaml

    checkpoint = ROOT / "checkpoints/leaf_disease_detection_model.pt"
    if not checkpoint.exists():
        pytest.skip("Cần checkpoint thật")
    cfg = yaml.safe_load((ROOT / "configs/default.yaml").read_text(encoding="utf-8"))
    predictor = DiseasePredictor(checkpoint, device="cpu")
    try:
        assert predictor.xai_method == cfg["xai"]["method"] == "gradcam_plusplus"
        assert predictor.crop_enabled == cfg.get("preprocess", {}).get("leaf_crop", {}).get(
            "enabled", False
        )
        assert predictor.reliability_enabled == cfg["xai"].get("reliability", {}).get(
            "enabled", False
        )
    finally:
        predictor.close()


@pytest.mark.parametrize(
    "sample_id", ["pv-bacterial_spot-3", "pv-septoria_leaf_spot-2", "pd-septoria_leaf_spot-2"]
)
def test_real_checkpoint_preserves_predictions_and_original_coordinates(predictors, sample_id):
    path = ROOT / f"outputs/xai-comparison-122/quality/images/{sample_id}.png"
    if not path.is_file():
        pytest.skip("Chưa có ảnh audit #122")
    image = Image.open(path).convert("RGB").resize((350, 270))
    baseline, upgraded, _ = predictors
    a, b = baseline.predict(image), upgraded.predict(image)
    assert a.disease_key == b.disease_key
    assert a.probabilities == b.probabilities
    assert b.heatmap.shape == (270, 350)
    assert b.heatmap.dtype == np.float32 and np.isfinite(b.heatmap).all()
    assert upgraded.predict(image, with_heatmap=False).heatmap is None


def test_real_gate_still_rejects_negative_image_before_cam(predictors):
    manifest = ROOT / "data/processed/gate-split.csv"
    if not manifest.is_file():
        pytest.skip("Chưa có bộ ảnh âm #91")
    with manifest.open(encoding="utf-8") as stream:
        row = next(
            r
            for r in csv.DictReader(stream)
            if r["label"] == "not_tomato_leaf" and r["split"] == "test"
        )
    path = ROOT / row["path"]
    if not path.is_file():
        pytest.skip("Chưa có ảnh âm để kiểm tra bộ chặn")
    result = predictors[2].predict(Image.open(path))
    assert result.disease_key == "not_tomato_leaf"
    assert result.heatmap is None and result.probabilities == {}
