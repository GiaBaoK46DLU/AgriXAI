"""Kiểm tra cách tổng hợp bằng chứng, tránh kết luận từ mẫu sai hoặc CAM rỗng."""

import numpy as np
import pytest

from src.evaluation.compare_gradcam_plusplus import region_metrics, summarize


def test_rendered_contour_is_measured_in_original_coordinates():
    annotation = {"luoi": ["VL", "NN"], "kieu_trieu_chung": "cuc_bo"}
    heatmap = np.ones((4, 4), dtype=np.float32)
    rendered = np.zeros((8, 12), dtype=bool)
    rendered[:4, :6] = True
    metrics = region_metrics(heatmap, annotation, rendered)
    assert metrics["leaf_concentration"] == pytest.approx(1)
    assert metrics["leaf_lift"] == pytest.approx(0)
    assert metrics["overlay_outside_leaf"] == pytest.approx(0)
    assert metrics["overlay_lesion_iou"] == pytest.approx(1)


def test_disputed_and_empty_maps_do_not_become_successful_localizations():
    annotation = {"luoi": ["VL", "NN"], "co_van_de_du_lieu": True}
    for heatmap in (np.zeros((4, 4)), np.ones((4, 4))):
        result = region_metrics(heatmap, annotation, np.ones((8, 12), dtype=bool))
        for metric in ("leaf_concentration", "peak_in_leaf", "overlay_lesion_iou"):
            assert result[metric] is None


def test_summary_excludes_wrong_predictions_from_lesion_but_not_leaf_metrics():
    records = []
    for sample_id, correct in (("a", True), ("b", False)):
        for method in ("gradcam", "gradcam_plusplus"):
            records.append({"sample_id": sample_id, "dataset": "pv", "correct": correct,
                            "method": method, "valid_map": True, "leaf_lift": .2,
                            "lesion_lift": .1 if correct else .9})
    result = summarize(records)
    for method in ("gradcam", "gradcam_plusplus"):
        stats = result["by_dataset"]["pv"][method]
        assert stats["leaf_lift"]["n_images"] == 2
        assert stats["lesion_lift"]["n_images"] == 1
        assert stats["lesion_lift"]["mean"] == pytest.approx(.1)
    assert result["paired_plusplus_minus_gradcam"]["pv"]["lesion_lift"]["n_images"] == 1
