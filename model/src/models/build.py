"""Dựng mô hình phân loại bằng transfer learning.

Không huấn luyện từ đầu: bộ dữ liệu cà chua của nhóm (~18k ảnh) quá nhỏ so với
ImageNet (1.2 triệu ảnh) mà các backbone này đã học qua. Ta giữ phần trích đặc
trưng và chỉ thay lớp phân loại cuối bằng lớp 10 lớp bệnh của mình.
"""

from __future__ import annotations

import torch
import torch.nn as nn
from torchvision import models

from src.labels import num_classes

# arch -> (hàm dựng của torchvision, bộ trọng số pretrained tương ứng)
SUPPORTED = {
    "efficientnet_b0": (models.efficientnet_b0, models.EfficientNet_B0_Weights.IMAGENET1K_V1),
    "efficientnet_b3": (models.efficientnet_b3, models.EfficientNet_B3_Weights.IMAGENET1K_V1),
    "resnet18": (models.resnet18, models.ResNet18_Weights.IMAGENET1K_V1),
    "resnet50": (models.resnet50, models.ResNet50_Weights.IMAGENET1K_V2),
}


def build_model(arch: str = "efficientnet_b0", pretrained: bool = True,
                dropout: float = 0.3, n_classes: int | None = None) -> nn.Module:
    if arch not in SUPPORTED:
        raise ValueError(f"arch='{arch}' chưa hỗ trợ. Chọn một trong: {list(SUPPORTED)}")

    ctor, weights = SUPPORTED[arch]
    model = ctor(weights=weights if pretrained else None)
    n_classes = n_classes or num_classes()

    if arch.startswith("efficientnet"):
        in_features = model.classifier[-1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(dropout, inplace=True),
            nn.Linear(in_features, n_classes),
        )
    else:  # resnet
        in_features = model.fc.in_features
        model.fc = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(in_features, n_classes),
        )
    return model


def target_layer_for_gradcam(model: nn.Module, arch: str) -> nn.Module:
    """Lớp tích chập cuối cùng — nơi Grad-CAM lấy feature map.

    Chọn lớp cuối vì đó là nơi đặc trưng đã đủ trừu tượng để mang ngữ nghĩa
    ("vết đốm nâu"), nhưng vẫn còn giữ thông tin vị trí không gian (7x7 với
    ảnh vào 224x224) để biết vết bệnh nằm ở đâu trên lá.
    """
    if arch.startswith("efficientnet"):
        return model.features[-1]
    if arch.startswith("resnet"):
        return model.layer4[-1]
    raise ValueError(f"Chưa biết chọn target layer cho arch='{arch}'")


def set_backbone_trainable(model: nn.Module, arch: str, trainable: bool) -> None:
    """Đóng băng / mở khoá backbone.

    Vài epoch đầu ta đóng băng backbone để lớp phân loại mới (khởi tạo ngẫu
    nhiên) không tạo ra gradient lớn phá hỏng trọng số pretrained.
    """
    head_name = "classifier" if arch.startswith("efficientnet") else "fc"
    for name, param in model.named_parameters():
        if not name.startswith(head_name):
            param.requires_grad = trainable


def count_parameters(model: nn.Module) -> tuple[int, int]:
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return total, trainable


def load_checkpoint(path: str, device: torch.device | str = "cpu") -> tuple[nn.Module, dict]:
    """Nạp checkpoint và dựng lại đúng kiến trúc đã lưu trong đó.

    Checkpoint tự mô tả (chứa arch, class_keys, image_size) nên backend không
    cần biết trước mô hình được huấn luyện bằng kiến trúc nào.
    """
    ckpt = torch.load(path, map_location=device, weights_only=False)
    model = build_model(
        arch=ckpt["arch"],
        pretrained=False,
        dropout=ckpt.get("dropout", 0.0),
        n_classes=len(ckpt["class_keys"]),
    )
    model.load_state_dict(ckpt["state_dict"])
    model.to(device).eval()
    return model, ckpt
