"""Grad-CAM — trả lời câu hỏi "mô hình đã nhìn vào đâu để kết luận như vậy?".

Ý tưởng (Selvaraju et al., 2017): lấy feature map của lớp tích chập cuối cùng,
tính gradient của điểm số lớp được dự đoán theo từng kênh feature map đó. Kênh
nào có gradient lớn nghĩa là kênh đó ảnh hưởng mạnh tới quyết định. Lấy trung
bình gradient trên toàn không gian làm trọng số, cộng có trọng số các kênh lại,
bỏ phần âm (ReLU) rồi phóng to về kích thước ảnh gốc — ta được bản đồ nhiệt chỉ
ra vùng ảnh có ảnh hưởng lớn nhất.

Cài đặt trực tiếp bằng hook thay vì gọi thư viện ngoài: chỉ khoảng 60 dòng,
không phụ thuộc phiên bản, và quan trọng hơn là nhóm nắm được từng bước để giải
thích trước hội đồng. Interface giữ giống ``pytorch-grad-cam`` nên muốn đổi
sang thư viện đó sau này cũng không phải sửa chỗ gọi.
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class GradCAM:
    """Sinh bản đồ nhiệt Grad-CAM cho một mô hình phân loại ảnh.

    Ví dụ::

        cam = GradCAM(model, target_layer_for_gradcam(model, arch))
        heatmap = cam(input_tensor)      # (B, H, W) trong khoảng 0..1
        cam.close()
    """

    def __init__(self, model: nn.Module, target_layer: nn.Module) -> None:
        self.model = model
        self.target_layer = target_layer
        self.activations: torch.Tensor | None = None
        self.gradients: torch.Tensor | None = None
        self._handles = [target_layer.register_forward_hook(self._forward_hook)]

    def _forward_hook(self, module, inputs, output) -> None:
        self.activations = output
        if output.requires_grad:
            # Bắt gradient chảy ngược qua đúng feature map này
            output.register_hook(self._save_gradient)

    def _save_gradient(self, grad: torch.Tensor) -> None:
        self.gradients = grad

    def __call__(self, input_tensor: torch.Tensor,
                 class_idx: int | torch.Tensor | None = None) -> np.ndarray:
        """Tính heatmap cho một batch ảnh đã chuẩn hoá.

        Args:
            input_tensor: (B, 3, H, W) — đã qua ``build_eval_transform``.
            class_idx: lớp cần giải thích. None = lớp mô hình dự đoán.

        Returns:
            Mảng (B, H, W) float32, mỗi ảnh đã chuẩn hoá về 0..1.
        """
        self.model.zero_grad(set_to_none=True)

        # Grad-CAM cần gradient nên không được chạy trong no_grad
        with torch.enable_grad():
            x = input_tensor.clone().requires_grad_(True)
            logits = self.model(x)

            if class_idx is None:
                targets = logits.argmax(dim=1)
            elif isinstance(class_idx, int):
                targets = torch.full((logits.size(0),), class_idx,
                                     dtype=torch.long, device=logits.device)
            else:
                targets = class_idx.to(logits.device)

            score = logits.gather(1, targets.unsqueeze(1)).sum()
            score.backward()

        if self.activations is None or self.gradients is None:
            raise RuntimeError(
                "Không bắt được activation/gradient. Kiểm tra lại target_layer "
                "có thực sự nằm trong đường đi forward của mô hình không."
            )

        acts = self.activations.detach()      # (B, C, h, w)
        grads = self.gradients.detach()       # (B, C, h, w)

        # Trọng số mỗi kênh = trung bình gradient trên toàn không gian
        weights = grads.mean(dim=(2, 3), keepdim=True)          # (B, C, 1, 1)
        cam = F.relu((weights * acts).sum(dim=1, keepdim=True))  # (B, 1, h, w)

        cam = F.interpolate(cam, size=input_tensor.shape[-2:],
                            mode="bilinear", align_corners=False).squeeze(1)  # (B, H, W)

        # Chuẩn hoá từng ảnh về 0..1 để ngưỡng cắt có ý nghĩa nhất quán
        flat = cam.flatten(1)
        cam_min = flat.min(dim=1)[0].view(-1, 1, 1)
        cam_max = flat.max(dim=1)[0].view(-1, 1, 1)
        cam = (cam - cam_min) / (cam_max - cam_min + 1e-8)

        return cam.cpu().numpy().astype(np.float32)

    def close(self) -> None:
        for h in self._handles:
            h.remove()
        self._handles.clear()

    def __enter__(self) -> "GradCAM":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
