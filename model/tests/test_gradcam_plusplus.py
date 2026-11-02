"""Kiểm tra công thức, vòng đời hook và hợp đồng predictor của #98."""

import numpy as np
import pytest
import torch
from torch import nn

from src.xai.gradcam import GradCAM
from src.xai.gradcam_plusplus import GradCAMPlusPlus, create_cam


@pytest.fixture
def model():
    torch.manual_seed(98)
    return nn.Sequential(nn.Conv2d(3, 4, 1), nn.ReLU(), nn.AdaptiveAvgPool2d(1),
                         nn.Flatten(), nn.Linear(4, 2)).eval()


def test_weights_match_independent_reference(model):
    reference = pytest.importorskip("pytorch_grad_cam").GradCAMPlusPlus
    generator = torch.Generator().manual_seed(98)
    acts = torch.rand((2, 4, 3, 3), generator=generator)
    grads = torch.randn((2, 4, 3, 3), generator=generator)
    grads[0, 0] = 0
    with reference(model, [model[1]]) as ref:
        expected = ref.get_cam_weights(None, None, None, acts.numpy(), grads.numpy())
    actual = GradCAMPlusPlus.channel_weights(acts, grads).squeeze(-1).squeeze(-1)
    np.testing.assert_allclose(actual.numpy(), expected, rtol=2e-6, atol=1e-6)


def test_batch_targets_match_individual_calls_without_changing_parameters(model):
    images = torch.randn(2, 3, 8, 10)
    before = {name: p.detach().clone() for name, p in model.named_parameters()}
    for p in model.parameters():
        p.grad = torch.ones_like(p)
    with GradCAMPlusPlus(model, model[1]) as cam:
        with torch.no_grad():
            batch = cam(images, torch.tensor([0, 1]))
        single = np.concatenate([cam(images[i:i+1], i) for i in range(2)])
        np.testing.assert_allclose(batch, single, atol=2e-6)
        assert batch.shape == (2, 8, 10)
        assert np.isfinite(batch).all() and batch.min() >= 0 and batch.max() <= 1
        assert cam.activations is None and cam.gradients is None
    for name, p in model.named_parameters():
        torch.testing.assert_close(p, before[name])
        torch.testing.assert_close(p.grad, torch.ones_like(p))


def test_zero_gradient_produces_empty_finite_map(model):
    with torch.no_grad():
        model[-1].weight.zero_()
    with GradCAMPlusPlus(model, model[1]) as cam:
        for normalize in (True, False):
            result = cam(torch.zeros(1, 3, 8, 10), 0, normalize=normalize)
            assert np.isfinite(result).all()
            assert not result.any()


def test_bad_target_and_closed_cam_fail_without_leaking_hooks(model):
    original = len(model[1]._forward_hooks)
    cam = GradCAMPlusPlus(model, model[1])
    image = torch.randn(1, 3, 8, 8)
    for target in (-1, 2, torch.tensor([0, 1]), torch.tensor([0.5])):
        with pytest.raises(ValueError):
            cam(image, target)
        assert cam.activations is None and cam.gradients is None
    cam.close()
    cam.close()
    assert len(model[1]._forward_hooks) == original
    with pytest.raises(RuntimeError, match="đã đóng"):
        cam(image)


def test_missing_target_layer_does_not_reuse_previous_activations(model):
    with GradCAMPlusPlus(model, nn.Identity()) as cam:
        with pytest.raises(RuntimeError, match="Target layer"):
            cam(torch.randn(1, 3, 8, 8))


def test_selector_preserves_baseline_and_rejects_typo(model):
    for method, cls in (("gradcam", GradCAM), ("gradcam_plusplus", GradCAMPlusPlus)):
        with create_cam(model, model[1], method) as cam:
            assert type(cam) is cls
    with pytest.raises(ValueError, match="không hợp lệ"):
        create_cam(model, model[1], "gradcam++")


def test_predictor_reads_xai_config_without_changing_contract(model, monkeypatch, tmp_path):
    from dataclasses import fields
    from PIL import Image
    import src.predictor as module

    checkpoint = tmp_path / "fake.pt"
    checkpoint.touch()
    metadata = {"class_keys": ["a", "b"], "image_size": 8,
                "model_version": "test", "arch": "test"}
    monkeypatch.setattr(module, "load_checkpoint", lambda *args: (model, metadata))
    monkeypatch.setattr(module, "target_layer_for_gradcam", lambda *args: model[1])
    config = tmp_path / "xai.yaml"
    config.write_text("xai:\n  method: gradcam_plusplus\n", encoding="utf-8")
    upgraded = module.DiseasePredictor(checkpoint, device="cpu", xai_config_path=config)
    baseline = module.DiseasePredictor(checkpoint, device="cpu", xai_method="gradcam")
    try:
        image = Image.new("RGB", (40, 30), (100, 150, 30))
        a, b = upgraded.predict(image), baseline.predict(image)
        assert upgraded.xai_method == "gradcam_plusplus"
        assert a.disease_key == b.disease_key and a.probabilities == b.probabilities
        assert a.heatmap.shape == (30, 40) and a.heatmap.dtype == np.float32
        assert upgraded.predict(image, with_heatmap=False).heatmap is None
        assert [f.name for f in fields(a)] == ["disease_key", "confidence", "probabilities",
                                               "heatmap", "model_version", "latency_ms"]
    finally:
        upgraded.close()
        baseline.close()
