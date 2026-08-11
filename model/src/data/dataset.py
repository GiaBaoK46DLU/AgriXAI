"""Dataset và các phép biến đổi ảnh."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

from src.labels import class_keys

# Giá trị chuẩn hoá của ImageNet — bắt buộc phải khớp với lúc pretrain,
# và backend cũng phải dùng đúng bộ số này khi suy luận.
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


class TomatoLeafDataset(Dataset):
    """Đọc ảnh theo manifest do ``src.data.prepare`` sinh ra."""

    def __init__(self, manifest: str | Path, split: str, transform=None) -> None:
        self.transform = transform
        self.keys = class_keys()
        self.key_to_idx = {k: i for i, k in enumerate(self.keys)}

        self.samples: list[tuple[Path, int]] = []
        with open(manifest, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row["split"] != split:
                    continue
                self.samples.append((Path(row["path"]), self.key_to_idx[row["label"]]))

        if not self.samples:
            raise ValueError(f"Manifest '{manifest}' không có mẫu nào cho split='{split}'")

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, int]:
        path, label = self.samples[idx]
        image = Image.open(path).convert("RGB")
        if self.transform:
            image = self.transform(image)
        return image, label

    @property
    def class_counts(self) -> list[int]:
        counts = [0] * len(self.keys)
        for _, label in self.samples:
            counts[label] += 1
        return counts


def build_train_transform(cfg: dict[str, Any]) -> transforms.Compose:
    size = cfg["data"]["image_size"]
    aug = cfg.get("augment", {})
    jitter = aug.get("color_jitter", {})

    ops: list[Any] = [
        transforms.RandomResizedCrop(
            size, scale=tuple(aug.get("random_resized_crop_scale", [0.7, 1.0]))
        ),
        transforms.RandomHorizontalFlip(aug.get("horizontal_flip", 0.5)),
        transforms.RandomVerticalFlip(aug.get("vertical_flip", 0.2)),
        transforms.RandomRotation(aug.get("rotation_degrees", 30)),
        transforms.ColorJitter(
            brightness=jitter.get("brightness", 0.3),
            contrast=jitter.get("contrast", 0.3),
            saturation=jitter.get("saturation", 0.3),
            hue=jitter.get("hue", 0.05),
        ),
    ]
    blur_p = aug.get("gaussian_blur_prob", 0.0)
    if blur_p > 0:
        ops.append(transforms.RandomApply(
            [transforms.GaussianBlur(kernel_size=5, sigma=(0.1, 1.5))], p=blur_p
        ))
    ops += [transforms.ToTensor(), transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)]
    return transforms.Compose(ops)


def build_infer_transform(image_size: int) -> transforms.Compose:
    """Biến đổi KHÔNG ngẫu nhiên — dùng cho val, test và cả suy luận thật.

    Cố tình resize thẳng về vuông thay vì Resize + CenterCrop như thói quen
    thường thấy. Lý do: center crop cắt mất phần rìa ảnh, mà heatmap Grad-CAM
    lại sinh ra trên phần đã cắt — khi vẽ đè lên ảnh gốc sẽ lệch vị trí, mà
    khoanh vùng sai chỗ dù chỉ một chút là mất hết ý nghĩa với người dùng.
    Resize thẳng làm ảnh hơi méo tỉ lệ, đổi lại heatmap phủ đúng toàn bộ ảnh.

    Dùng chung một hàm cho cả đánh giá lẫn suy luận để con số accuracy trong
    báo cáo đúng bằng chất lượng người dùng thực sự nhận được.
    """
    return transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


def build_dataloaders(cfg: dict[str, Any], manifest: str | Path) -> dict[str, DataLoader]:
    d = cfg["data"]
    train_ds = TomatoLeafDataset(manifest, "train", build_train_transform(cfg))
    eval_tf = build_infer_transform(d["image_size"])
    val_ds = TomatoLeafDataset(manifest, "val", eval_tf)
    test_ds = TomatoLeafDataset(manifest, "test", eval_tf)

    common = {"batch_size": d["batch_size"], "num_workers": d["num_workers"],
              "pin_memory": torch.cuda.is_available()}
    return {
        "train": DataLoader(train_ds, shuffle=True, drop_last=True, **common),
        "val": DataLoader(val_ds, shuffle=False, **common),
        "test": DataLoader(test_ds, shuffle=False, **common),
    }
