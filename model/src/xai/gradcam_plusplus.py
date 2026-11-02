"""Grad-CAM++ cạnh Grad-CAM gốc, không sửa thuật toán đối chứng.

Công thức (7), (19) của Chattopadhyay et al., arXiv:1710.11063v3.
Theo quy ước pytorch-grad-cam: dùng gradient logit, bỏ hệ số exp(score)
chung vì hệ số đó triệt tiêu sau chuẩn hoá. Không tính exp trực tiếp để
tránh tràn số. Với tầng cuối GAP + Linear của mô hình hiện tại, logit là
tuyến tính theo activation nên áp dụng được công thức đóng này.
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn.functional as F

from src.xai.gradcam import GradCAM


class GradCAMPlusPlus(GradCAM):
    """Cùng giao diện/target layer với GradCAM; chỉ thay cách tính trọng số."""

    @staticmethod
    def channel_weights(activations: torch.Tensor, gradients: torch.Tensor) -> torch.Tensor:
        """Trọng số theo công thức (19), epsilon như pytorch-grad-cam 1.5.5."""
        squared = gradients.square()
        cubed = squared * gradients
        denominator = 2 * squared + activations.sum((2, 3), keepdim=True) * cubed + 1e-6
        alpha = torch.where(gradients != 0, squared / denominator, 0.0)
        return (alpha * gradients.clamp_min(0)).sum((2, 3), keepdim=True)

    def __call__(self, input_tensor: torch.Tensor,
                 class_idx: int | torch.Tensor | None = None,
                 normalize: bool = True) -> np.ndarray:
        if not self._handles:
            raise RuntimeError("GradCAMPlusPlus đã đóng; cần tạo đối tượng mới.")
        self.activations = self.gradients = None
        try:
            with torch.enable_grad():
                x = input_tensor.detach().clone().requires_grad_(True)
                logits = self.model(x)
                if self.activations is None:
                    raise RuntimeError("Target layer không nằm trong đường forward của mô hình.")
                if class_idx is None:
                    targets = logits.argmax(1)
                elif isinstance(class_idx, int):
                    targets = torch.full((len(x),), class_idx, device=logits.device, dtype=torch.long)
                else:
                    targets = class_idx.to(device=logits.device)
                if targets.shape != (len(x),) or targets.dtype != torch.long:
                    raise ValueError("class_idx phải là số nguyên hoặc tensor int64 có một lớp cho mỗi ảnh.")
                if (targets < 0).any() or (targets >= logits.shape[1]).any():
                    raise ValueError("class_idx nằm ngoài danh mục lớp của mô hình.")
                score = logits.gather(1, targets[:, None]).sum()
                # Chỉ lấy gradient cần thiết; không ghi gradient vào tham số mô hình.
                gradients = torch.autograd.grad(score, self.activations)[0].detach().float()
                activations = self.activations.detach().float()

            weights = self.channel_weights(activations, gradients)
            cam = F.relu((weights * activations).sum(1, keepdim=True))
            cam = F.interpolate(cam, size=input_tensor.shape[-2:], mode="bilinear",
                                align_corners=False).squeeze(1)
            if not torch.isfinite(cam).all():
                raise RuntimeError("Grad-CAM++ sinh NaN/Inf; không thể tạo vùng khoanh hợp lệ.")
            if normalize:
                minimum = cam.flatten(1).amin(1)[:, None, None]
                maximum = cam.flatten(1).amax(1)[:, None, None]
                cam = (cam - minimum) / (maximum - minimum + 1e-8)
            return cam.cpu().numpy().astype(np.float32)
        finally:
            # Không giữ đồ thị autograd/VRAM giữa các request, kể cả khi có lỗi.
            self.activations = self.gradients = None

    def close(self) -> None:
        super().close()
        self.activations = self.gradients = None


def create_cam(model, target_layer, method: str = "gradcam") -> GradCAM:
    """Chọn thuật toán rõ ràng; cấu hình sai phải báo lỗi thay vì âm thầm đổi."""
    classes = {"gradcam": GradCAM, "gradcam_plusplus": GradCAMPlusPlus}
    if method not in classes:
        raise ValueError(f"Phương pháp XAI '{method}' không hợp lệ; chọn {tuple(classes)}.")
    return classes[method](model, target_layer)
