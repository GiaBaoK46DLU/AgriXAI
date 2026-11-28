"""Kiểm thử các hàm thuần của src/evaluation/eval_xai_200.py (không cần ảnh hay checkpoint)."""
import pytest

from src.evaluation import eval_xai_200 as V

META = {"dataset": "pv", "label": "x", "path": "p", "predicted": "x", "correct": True,
        "target_probability": 0.9, "gate_leaf_probability": 0.99, "gate_pass": True}


def test_allocate_spreads_remainder_and_keeps_total():
    quota = V.allocate(139, [f"c{i}" for i in range(10)], seed=1)
    assert sum(quota.values()) == 139
    assert sorted(set(quota.values())) == [13, 14]
    assert quota == V.allocate(139, [f"c{i}" for i in reversed(range(10))], seed=1)  # không phụ thuộc thứ tự vào


def _row(sample, method, drop_multiply, drop_top):
    return {"sample_id": sample, "method": method, "drop_multiply": drop_multiply, "drop_keep_top15": drop_top}


def test_add_wins_splits_ties_and_skips_missing():
    rows = [_row("a", "gradcam_plusplus", 10.0, 5.0), _row("a", "gradcam", 20.0, 5.0),
            _row("b", "gradcam_plusplus", None, None), _row("b", "gradcam", None, None)]
    V.add_wins(rows)
    assert [r["win_multiply"] for r in rows[:2]] == [100.0, 0.0]
    assert [r["win_keep_top15"] for r in rows[:2]] == [50.0, 50.0]
    assert rows[2]["win_multiply"] is None and rows[3]["win_keep_top15"] is None


def _record(iou_pp, iou_gc):
    robustness = lambda iou: {"sang_hon_15": {"contour_iou": iou, "rel_l2": 0.1, "one_minus_spearman": 0.05},
                              "jpeg_q70": None}
    method = lambda iou: {"faithfulness": {"grid|road": {"deletion_auc": 0.2, "insertion_auc": 0.5, "gap": 0.3}},
                          "drop": {"multiply": {"drop": 10.0, "increase": 0.0, "masked_probability": 0.8}},
                          "robustness": robustness(iou)}
    return {"sample_id": "s1", **META, "methods": {"gradcam_plusplus": method(iou_pp), "gradcam": method(iou_gc)}}


def test_flatten_ignores_flipped_perturbations():
    rows = V.flatten(_record(0.8, 0.6))
    pp = next(r for r in rows if r["method"] == "gradcam_plusplus")
    assert pp["avg_contour_iou"] == pytest.approx(0.8)
    assert pp["worst_contour_iou"] == pytest.approx(0.8)
    assert pp["jpeg_q70|contour_iou"] is None
    assert pp["grid|road|gap"] == pytest.approx(0.3)
    assert pp["drop_multiply"] == pytest.approx(10.0)


def test_paired_rows_is_gradcampp_minus_gradcam():
    rows = V.flatten(_record(0.8, 0.6))
    paired = V.paired_rows(rows, ["avg_contour_iou"])
    assert paired["all"]["avg_contour_iou"]["mean"] == pytest.approx(0.2)
    assert paired["pd"] == {}  # không có ảnh PlantDoc nào trong tập con


def test_subset_names():
    rows = [{"dataset": "pd", "correct": False, "gate_pass": False}, {"dataset": "pv", "correct": True, "gate_pass": True}]
    assert len(V.subset(rows, "all")) == 2
    assert V.subset(rows, "pd") == [rows[0]]
    assert V.subset(rows, "wrong") == [rows[0]]
    assert V.subset(rows, "gate_pass") == [rows[1]]
