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
    baseline = DiseasePredictor(checkpoint, device="cpu", xai_method="gradcam")
    # Constructor mà backend đang dùng phải tự đọc mặc định ++, không cần
    # truyền tham số thử nghiệm hoặc sửa loader phía backend.
    upgraded = DiseasePredictor(checkpoint, device="cpu")
    gated = DiseasePredictor(checkpoint, device="cpu", xai_config_path=config,
                             gate_checkpoint=gate)
    try:
        assert baseline.xai_method == "gradcam"
        assert upgraded.xai_method == "gradcam_plusplus"
        yield baseline, upgraded, gated
    finally:
        for predictor in (baseline, upgraded, gated):
            predictor.close()
        torch.set_num_threads(original_threads)


@pytest.mark.parametrize("sample_id", ["pv-bacterial_spot-3", "pv-septoria_leaf_spot-2",
                                      "pd-septoria_leaf_spot-2"])
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
        row = next(r for r in csv.DictReader(stream)
                   if r["label"] == "not_tomato_leaf" and r["split"] == "test")
    path = ROOT / row["path"]
    if not path.is_file():
        pytest.skip("Chưa có ảnh âm để kiểm tra bộ chặn")
    result = predictors[2].predict(Image.open(path))
    assert result.disease_key == "not_tomato_leaf"
    assert result.heatmap is None and result.probabilities == {}
