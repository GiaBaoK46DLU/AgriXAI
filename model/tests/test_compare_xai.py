"""Kiểm tra bất biến của phép đo, không cần checkpoint hoặc dữ liệu thật."""
import numpy as np
import pytest
import torch

from src.evaluation.compare_xai import Predictor, positive_density, spatial_metrics, stability, top_fraction_weights


def test_region_contribution_is_conserved_with_unequal_areas():
    segments = np.array([[0, 0, 0], [0, 1, 2]])
    density = positive_density(np.array([2.0, 3.0, -1.0]), segments)
    assert density[segments == 0].sum() == pytest.approx(2)
    assert density[segments == 1].sum() == pytest.approx(3)
    assert density[segments == 2].sum() == 0


def test_tied_top_fraction_does_not_prefer_first_pixels():
    support = top_fraction_weights(np.ones((10, 10)), 0.2)
    assert support.sum() == pytest.approx(20)
    assert np.allclose(support, 0.2)


def test_leaf_lift_is_zero_for_uniform_map():
    annotation = {"luoi": ["VL", "NN"], "kieu_trieu_chung": "cuc_bo"}
    result = spatial_metrics(np.ones((4, 4)), annotation)
    assert result["leaf_mass"] == pytest.approx(0.5)
    assert result["leaf_lift"] == pytest.approx(0)
    assert result["lesion_lift"] == pytest.approx(0)


def test_empty_map_is_not_reported_as_valid_explanation():
    result = spatial_metrics(np.zeros((2, 2)), {"luoi": ["VL", "NN"]})
    assert not result["valid_map"]
    assert result["leaf_mass"] is None


def test_healthy_has_no_lesion_metric_and_disputed_masks_are_excluded():
    annotation = {"luoi": ["LL", "NN"], "kieu_trieu_chung": "khong_co_vet"}
    assert spatial_metrics(np.ones((2, 2)), annotation)["lesion_mass"] is None
    annotation["co_van_de_du_lieu"] = True
    assert spatial_metrics(np.ones((2, 2)), annotation)["leaf_mass"] is None


def test_stability_measures_seed_variation_without_tie_artifacts():
    first = np.zeros((10, 10))
    second = first.copy()
    first[:2] = 1
    second[-2:] = 1
    assert stability([first, first.copy(), first.copy()]) == pytest.approx(1)
    assert stability([first, second]) == pytest.approx(0)
    assert stability([first, np.zeros_like(first)]) is None


def test_mask_predictor_preserves_original_and_background_endpoints():
    class Toy(torch.nn.Module):
        def forward(self, x):
            score = x.mean((1, 2, 3))
            return torch.stack((score, -score), 1)
    predictor = Predictor(Toy(), torch.device("cpu"), batch_size=2)
    image = np.full((2, 2, 3), 200, dtype=np.uint8)
    baseline = np.full_like(image, 50)
    segments = np.array([[0, 0], [1, 1]])
    result = predictor.masks(np.array([[0, 0], [1, 1]]), image, baseline, segments, 0)
    assert result[0] == pytest.approx(predictor(baseline[None])[0, 0])
    assert result[1] == pytest.approx(predictor(image[None])[0, 0])
    predictor.handle.remove()
