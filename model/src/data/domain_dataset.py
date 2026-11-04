"""Dữ liệu bệnh có augmentation điều kiện ngoài trời, chỉ dùng split train."""

from pathlib import Path

from PIL import Image
from torch.utils.data import Dataset

from src.data.dataset import build_infer_transform, build_train_transform
from src.data.gate_augment import DomainShortcutBreaker, background_pool, load_rgb_fast
from src.data.leaf_crop import locate_leaf


class DomainDiseaseDataset(Dataset):
    def __init__(self, rows, keys, cfg, training=False):
        self.rows, self.keys, self.cfg, self.training = rows, keys, cfg, training
        self.transform = (
            build_train_transform(cfg)
            if training
            else build_infer_transform(cfg["data"]["image_size"])
        )
        outdoor = cfg.get("augment", {}).get("outdoor", {})
        self.breaker = None
        if training and outdoor.get("enabled", False):
            # API chỉ cho dùng train; không có tham số split lấy val/test.
            backgrounds = background_pool(Path(outdoor["background_manifest"]), "train")
            if not backgrounds:
                raise ValueError("Augmentation nền cần ảnh âm thuộc tập train")
            self.breaker = DomainShortcutBreaker(
                backgrounds, outdoor.get("background_prob", 0.7), outdoor.get("light_prob", 0.5)
            )

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        row = self.rows[index]
        if self.training:
            image = load_rgb_fast(Path(row["path"]), max_side=512)
        else:
            with Image.open(row["path"]) as opened:
                image = opened.convert("RGB")
        crop = dict(self.cfg.get("preprocess", {}).get("leaf_crop", {}))
        enabled = crop.pop("enabled", False)
        # Chỉ ghép nền cho PlantVillage; PlantDoc đã có nền phức tạp thật.
        if self.breaker is not None:
            if row.get("source") == "plantvillage" or "raw" in Path(row["path"]).parts:
                image = self.breaker(image)
            else:
                import random

                import numpy as np

                from src.data.gate_augment import harsh_outdoor_light

                if random.random() < 0.5:
                    image = Image.fromarray(harsh_outdoor_light(np.asarray(image), random))
        if enabled:
            image = image.crop(locate_leaf(image, **crop).box)
        return self.transform(image), self.keys.index(row["label"])
