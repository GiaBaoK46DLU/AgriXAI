"""Bất biến của các phép đo mở rộng; không cần checkpoint hoặc dữ liệu thật."""
import numpy as np
import pytest

from src.evaluation.extend_xai_eval import (
    agreement,
    drop_and_increase,
    entropy,
    map_distance,
    map_pairs,
    masked_inputs,
    noisy_linear_impute,
    randomize_,
    removal_schedule,
    unit_index,
    unit_scores,
)


def _baseline(image):
    return np.broadcast_to(image.mean((0, 1)).astype(np.uint8), image.shape).copy()


def test_road_fill_reproduces_linear_ramp_and_keeps_known_pixels():
    ramp = np.tile(np.linspace(0, 200, 32), (32, 1))
    image = np.repeat(ramp[..., None], 3, axis=2).astype(np.uint8)
    removed = np.zeros((32, 32), bool)
    removed[10:20, 8:24] = True
    filled = noisy_linear_impute(image, removed, _baseline(image), noise=0)
    assert np.array_equal(filled[~removed], image[~removed].astype(np.float64))
    # Trung bình đối xứng 8 láng giềng giữ đúng hàm tuyến tính bên trong lỗ.
    assert np.abs(filled[removed] - image[removed]).max() <= 1.0


def test_road_full_removal_falls_back_to_mean_baseline():
    image = np.random.default_rng(0).integers(0, 255, (8, 8, 3)).astype(np.uint8)
    filled = noisy_linear_impute(image, np.ones((8, 8), bool), _baseline(image))
    assert np.array_equal(filled, _baseline(image).astype(np.float64))


def test_grid_units_are_block_means():
    heatmap = np.zeros((28, 28))
    heatmap[:2, :2] = 1
    scores = unit_scores(heatmap, unit_index(None, heatmap.shape))
    assert scores.shape == (196,)
    assert scores[0] == pytest.approx(1)
    assert scores[1:].sum() == 0


def test_agreement_extremes_and_constant_maps():
    a = np.arange(10, dtype=float)
    same = agreement(a, a)
    assert same["spearman"] == pytest.approx(1)
    assert same["top20_agreement"] == pytest.approx(1)
    reverse = agreement(a, a[::-1])
    assert reverse["spearman"] == pytest.approx(-1)
    assert reverse["top20_agreement"] == pytest.approx(0)
    assert agreement(a, np.zeros(10))["spearman"] is None


def test_map_pairs_matches_seeds_and_deterministic_maps():
    det, sampled = {None: 0}, {42: 1, 123: 2, 2026: 3}
    assert map_pairs(det, sampled) == [(0, 1), (0, 2), (0, 3)]
    assert map_pairs(sampled, sampled) == [(1, 1), (2, 2), (3, 3)]


def test_keep_top15_keeps_fifteen_percent_of_original_pixels():
    image = np.full((20, 20, 3), 200, np.uint8)
    heatmap = np.random.default_rng(1).random((20, 20))
    inputs = masked_inputs(image, heatmap, np.zeros_like(image))
    assert inputs["keep_top15"][..., 0].sum() / 200 == pytest.approx(0.15 * 400)
    assert masked_inputs(image, np.zeros((20, 20)), image) is None


def test_drop_and_increase_definition():
    assert drop_and_increase(0.8, 0.6) == (pytest.approx(25.0), 0.0)
    assert drop_and_increase(0.5, 0.7) == (0.0, 100.0)


def test_removal_schedule_area_axis_and_order():
    heatmap = np.zeros((28, 28))
    heatmap[:14, :14] = 1
    tops, x = removal_schedule(heatmap, unit_index(None, heatmap.shape))
    assert x[0] == 0 and x[-1] == pytest.approx(1)
    first = next(t for t, area in zip(tops, x) if area > 0)
    assert heatmap[first].min() == 1  # vùng quan trọng nhất bị xoá trước


def test_matched_randomization_changes_weights_but_keeps_scale_and_batchnorm():
    import torch
    import torch.nn as nn

    torch.manual_seed(0)
    block = nn.Sequential(nn.Conv2d(3, 64, 3), nn.BatchNorm2d(64))
    block[1].running_mean.fill_(0.5)
    before = block[0].weight.detach().clone()
    randomize_(block, 7, "matched")
    after = block[0].weight.detach()
    assert not torch.allclose(before, after)
    assert float(after.std()) == pytest.approx(float(before.std()), rel=0.1)
    assert float(after.mean()) == pytest.approx(float(before.mean()), abs=0.01)
    assert torch.all(block[1].running_mean == 0.5)
    again = nn.Sequential(nn.Conv2d(3, 64, 3), nn.BatchNorm2d(64))
    again[0].weight.data.copy_(before)
    again[0].bias.data.copy_(block[0].bias.data)
    with pytest.raises(ValueError):
        randomize_(again, 7, "khong-co")


def test_map_distance_identical_and_entropy():
    m = np.random.default_rng(2).random((16, 16))
    d = map_distance(m, m)
    assert d["rel_l2"] == pytest.approx(0)
    assert d["one_minus_spearman"] == pytest.approx(0, abs=1e-12)
    assert d["contour_iou"] == pytest.approx(1)
    assert map_distance(m, np.zeros_like(m))["rel_l2"] is None
    assert entropy(np.ones((4, 4))) == pytest.approx(np.log(16))
