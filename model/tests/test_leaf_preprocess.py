"""Hợp đồng toạ độ #93 và quyền từ chối vẽ XAI #90."""

import cv2
import numpy as np
import pytest
from PIL import Image
from src.data.leaf_crop import LeafRegion, locate_leaf
from src.xai.reliability import assess_heatmap


def test_crop_tracks_offcentre_leaf_and_restores_only_its_coordinates():
    rgb = np.full((180, 340, 3), 140, np.uint8)
    cv2.ellipse(rgb, (245, 80), (45, 65), 0, 0, 360, (42, 130, 35), -1)
    # Vết nâu trong lá vẫn được giữ trong mask, không bị xem thành nền.
    cv2.circle(rgb, (245, 80), 12, (80, 45, 25), -1)
    region = locate_leaf(Image.fromarray(rgb))
    assert region.reason == "localized" and region.mask[80, 245]
    x0, y0, x1, y1 = region.box
    assert x0 > 170 and x1 < 330 and y0 < 20 and y1 > 140
    restored = region.restore(np.ones((7, 7), np.float32), (340, 180))
    assert restored.shape == (180, 340) and restored.dtype == np.float32
    assert restored[80, 245] == 1 and restored[80, 80] == 0
    assert restored.sum() == (x1 - x0) * (y1 - y0)


def test_unresolved_or_many_similar_components_fall_back_to_original():
    image = Image.new("RGB", (260, 150), (130, 130, 130))
    region = locate_leaf(image)
    assert region.box == (0, 0, 260, 150) and region.mask is None
    rgb = np.asarray(image).copy()
    for x in (50, 130, 210):
        cv2.circle(rgb, (x, 75), 25, (35, 140, 40), -1)
    assert locate_leaf(Image.fromarray(rgb)).reason == "ambiguous_mask"


def test_padding_and_heatmap_peak_survive_non_square_mapping():
    region = LeafRegion((80, 30, 240, 150), None, "test")
    cam = np.zeros((12, 16), np.float32)
    cam[6, 8] = 1
    restored = region.restore(cam, (400, 220))
    y, x = np.unravel_index(restored.argmax(), restored.shape)
    assert abs(x - 165) <= 5 and abs(y - 95) <= 5
    assert restored[:30].sum() == restored[:, 240:].sum() == 0


def test_reliability_rejects_background_and_flat_maps_without_changing_label():
    mask = np.zeros((100, 160), bool)
    mask[20:80, 60:120] = True
    focused = mask.astype(np.float32)
    assert assess_heatmap(focused, mask)["accepted"]
    assert not assess_heatmap(1 - focused, mask)["accepted"]
    assert not assess_heatmap(np.ones_like(focused), mask)["accepted"]
    assert not assess_heatmap(focused, None)["accepted"]
    assert not assess_heatmap(np.zeros_like(focused), mask)["accepted"]
    with pytest.raises(ValueError):
        assess_heatmap(focused, mask[:20])


def test_no_heatmap_evidence_is_not_made_from_nan_or_whole_frame_mask():
    mask = np.ones((20, 20), bool)
    assert not assess_heatmap(np.ones((20, 20)), mask)["accepted"]
    mask[:5] = False
    assert not assess_heatmap(np.full((20, 20), np.nan), mask)["accepted"]
