"""Augmentation dữ liệu bệnh không dùng ảnh nền validation/test."""

import csv

import torch
from PIL import Image, ImageDraw
from src.data.domain_dataset import DomainDiseaseDataset


def test_backgrounds_are_train_only_and_validation_never_augmented(tmp_path):
    paths = []
    for split in ("train", "val", "test"):
        path = tmp_path / f"bg-{split}.png"
        Image.new("RGB", (128, 128), (110, 80, 50)).save(path)
        paths.append((path, split))
    manifest = tmp_path / "backgrounds.csv"
    with manifest.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["path", "label", "split"])
        writer.writerows((str(path), "not_tomato_leaf", split) for path, split in paths)
    leaf = Image.new("RGB", (160, 120), (150, 150, 150))
    ImageDraw.Draw(leaf).ellipse((40, 10, 120, 110), fill=(30, 130, 40))
    leaf_path = tmp_path / "leaf.png"
    leaf.save(leaf_path)
    rows = [{"path": str(leaf_path), "label": "early_blight", "source": "plantvillage"}]
    cfg = {
        "data": {"image_size": 64},
        "augment": {
            "outdoor": {
                "enabled": True,
                "background_manifest": str(manifest),
                "background_prob": 1.0,
                "light_prob": 1.0,
            }
        },
    }
    train = DomainDiseaseDataset(rows, ["early_blight"], cfg, True)
    assert train.breaker.background_paths == [paths[0][0]]
    tensor, label = train[0]
    assert tensor.shape == (3, 64, 64) and torch.isfinite(tensor).all() and label == 0
    val = DomainDiseaseDataset(rows, ["early_blight"], cfg, False)
    assert val.breaker is None
    a, _ = val[0]
    b, _ = val[0]
    assert torch.equal(a, b)


def test_native_field_image_does_not_receive_lab_background_compositing(tmp_path, monkeypatch):
    path = tmp_path / "field.png"
    Image.new("RGB", (128, 128), (50, 130, 40)).save(path)
    ds = DomainDiseaseDataset(
        [{"path": str(path), "label": "healthy", "source": "plantdoc"}],
        ["healthy"],
        {"data": {"image_size": 64}},
        True,
    )

    def fail(*args):
        raise AssertionError("Không được ghép nền cho PlantDoc")

    ds.breaker = fail
    tensor, label = ds[0]
    assert tensor.shape == (3, 64, 64) and label == 0
