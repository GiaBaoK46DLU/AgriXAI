"""Xuất checkpoint sang ONNX để chạy ngay trên điện thoại (suy luận offline).

Không dùng lại nguyên `DiseasePredictor` vì đó là suy luận trên server bằng
Grad-CAM thật (cần backprop, ONNX Runtime di động không hỗ trợ). Với kiến trúc
hiện tại — GAP rồi một lớp Linear — CAM cổ điển (Zhou et al., 2016) cho kết quả
gần như tương đương Grad-CAM mà chỉ cần một lượt forward: nhân feature map
trước GAP với đúng hàng trọng số của lớp Linear ứng với lớp dự đoán. Vì đó chỉ
là một phép tổ hợp tuyến tính theo kênh, cài luôn thành một `Conv2d` 1x1 rồi
xuất chung vào một đồ thị ONNX duy nhất — máy điện thoại không cần biết gì về
kiến trúc gốc, chỉ chạy forward.

Output của mô hình ONNX:
    probs: (1, n_classes) — xác suất đã qua softmax.
    cams:  (1, n_classes, h, w) — CAM thô (CHƯA ReLU/chuẩn hoá) của TỪNG lớp;
        phía Dart tự chọn đúng lớp theo argmax(probs), ReLU rồi min-max chuẩn
        hoá — xem `mobile/lib/services/offline_inference_service.dart`.

Chạy trong container backend (đã có sẵn torch CPU, xem CLAUDE.md mục IN-01):

    docker exec plantdx-backend python -m src.export_onnx \\
        --checkpoint /model/checkpoints/leaf_disease_detection_model.pt \\
        --out /app/model_export_tmp
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch
import torch.nn as nn

from src.data.dataset import IMAGENET_MEAN, IMAGENET_STD
from src.models.build import load_checkpoint


class _ExportWrapper(nn.Module):
    """Bọc mô hình gốc để một lượt forward ra cả xác suất lẫn CAM mọi lớp."""

    def __init__(self, model: nn.Module, arch: str) -> None:
        super().__init__()
        if not arch.startswith("efficientnet"):
            raise NotImplementedError(
                f"Xuất ONNX kèm CAM mới hỗ trợ efficientnet_*, chưa hỗ trợ arch='{arch}'. "
                "Lý do: cam_conv ở dưới giả định backbone kết thúc bằng "
                "GAP + 1 lớp Linear duy nhất (đúng với EfficientNet trong build.py)."
            )
        self.features = model.features
        self.avgpool = model.avgpool
        self.classifier = model.classifier

        linear = next(m for m in reversed(list(self.classifier)) if isinstance(m, nn.Linear))
        self.cam_conv = nn.Conv2d(linear.in_features, linear.out_features, kernel_size=1, bias=True)
        with torch.no_grad():
            self.cam_conv.weight.copy_(linear.weight.view(linear.out_features, linear.in_features, 1, 1))
            self.cam_conv.bias.copy_(linear.bias)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        feat = self.features(x)                     # (B, C, h, w)
        pooled = torch.flatten(self.avgpool(feat), 1)  # (B, C)
        logits = self.classifier(pooled)               # (B, n_classes)
        probs = torch.softmax(logits, dim=1)
        cams = self.cam_conv(feat)                      # (B, n_classes, h, w) — thô, chưa ReLU/chuẩn hoá
        return probs, cams


def export(checkpoint_path: str, out_dir: str) -> None:
    model, ckpt = load_checkpoint(checkpoint_path, device="cpu")
    model.eval()

    wrapper = _ExportWrapper(model, ckpt["arch"]).eval()
    image_size = ckpt.get("image_size", 224)
    dummy = torch.zeros(1, 3, image_size, image_size)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    onnx_path = out / "tomato_leaf_v1.onnx"

    torch.onnx.export(
        wrapper,
        (dummy,),
        str(onnx_path),
        input_names=["image"],
        output_names=["probs", "cams"],
        dynamic_axes=None,  # batch=1 cố định — đủ dùng cho suy luận từng ảnh trên điện thoại
        opset_version=17,
        dynamo=False,  # bản dynamo (mặc định ở torch mới) cần thêm onnxscript, không cần cho đồ thị đơn giản này
    )

    # Kiểm tra nhanh: đồ thị xuất ra phải cho kết quả khớp mô hình gốc, sai một
    # ly là cả pipeline offline sai theo mà không có gì báo lỗi.
    import onnxruntime as ort

    with torch.no_grad():
        probs_ref, cams_ref = wrapper(dummy)
    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])
    probs_onnx, cams_onnx = sess.run(None, {"image": dummy.numpy()})
    torch.testing.assert_close(probs_ref, torch.from_numpy(probs_onnx), atol=1e-4, rtol=1e-3)
    # CAM là tổ hợp tuyến tính của rất nhiều kênh (conv 1x1 trên toàn bộ
    # feature map) nên sai số dấu phẩy động cộng dồn nhiều hơn phần softmax —
    # ONNX Runtime dùng thuật toán conv/gemm khác PyTorch nên lệch vài phần
    # nghìn là bình thường. Đánh giá bằng SAI SỐ TƯƠNG ĐỐI SO VỚI BIÊN ĐỘ CAM
    # (chứ không so trực tiếp từng phần tử) vì đây chỉ là ảnh trực quan, không
    # phải số liệu cần chính xác tuyệt đối.
    cam_range = (cams_ref.amax() - cams_ref.amin()).item()
    max_abs_diff = (cams_ref - torch.from_numpy(cams_onnx)).abs().max().item()
    relative_to_range = max_abs_diff / cam_range if cam_range > 0 else max_abs_diff
    assert relative_to_range < 0.02, (
        f"CAM lệch {relative_to_range:.1%} biên độ giữa PyTorch và ONNX Runtime — "
        "quá lớn để tin cậy vùng khoanh offline, kiểm tra lại _ExportWrapper."
    )

    meta = {
        "model_version": ckpt.get("model_version", Path(checkpoint_path).stem),
        "image_size": image_size,
        "mean": IMAGENET_MEAN,
        "std": IMAGENET_STD,
        "class_keys": ckpt["class_keys"],
        "cam_grid": list(cams_ref.shape[-2:]),  # (h, w) của CAM, vd [7, 7]
    }
    meta_path = out / "tomato_leaf_v1_meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    size_mb = onnx_path.stat().st_size / 1_048_576
    print(f"Đã xuất {onnx_path} ({size_mb:.1f} MB) + {meta_path}")
    print(f"class_keys ({len(meta['class_keys'])}): {meta['class_keys']}")
    print(f"cam_grid: {meta['cam_grid']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    export(args.checkpoint, args.out)
