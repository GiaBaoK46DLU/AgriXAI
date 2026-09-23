"""Đo chi phí của 4 kiến trúc trong ``models/build.py`` — số liệu cho phần
"vì sao chọn EfficientNet-B0" của báo cáo (#19 rút gọn).

⚠️ **Đây KHÔNG phải #19.** #19 là huấn luyện thật từng kiến trúc trên bộ dữ
liệu của nhóm rồi so độ chính xác (4 lượt × ~25 phút). Script này chỉ đo phần
**không cần huấn luyện**: số tham số, độ phân giải bản đồ đặc trưng (quyết
định độ mịn của Grad-CAM) và thời gian một lượt truyền xuôi trên CPU.

Dùng ``pretrained=False`` có chủ đích: ba đại lượng trên không phụ thuộc giá
trị trọng số, nên không cần tải ~100 MB trọng số ImageNet về chỉ để đếm.

    python -m src.evaluation.arch_stats
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import torch

from src.models.build import SUPPORTED, build_model, count_parameters

# Mỗi kiến trúc đo ở đúng độ phân giải nó được thiết kế cho. Chạy B3 ở 224 như
# `configs/default.yaml` đang đặt là dưới độ phân giải thiết kế của nó — xem
# cảnh báo "bốn cái bẫy đã biết trước" trong CLAUDE.md.
INPUT_SIZE = {
    "efficientnet_b0": 224,
    "efficientnet_b3": 300,
    "resnet18": 224,
    "resnet50": 224,
}

N_THREADS = 4      # khớp cách đã đo 215 ms ở #18 (để torch tự lấy 16 luồng thì chậm hơn)
N_WARMUP = 3
N_REPEAT = 20
OUT = Path("outputs/arch-stats.json")


def _feature_extractor(model: torch.nn.Module, arch: str) -> torch.nn.Module:
    """Phần trích đặc trưng, tới ngay trước lớp gộp trung bình toàn cục."""
    if arch.startswith("efficientnet"):
        return model.features
    return torch.nn.Sequential(model.conv1, model.bn1, model.relu, model.maxpool,
                               model.layer1, model.layer2, model.layer3, model.layer4)


def measure(arch: str, n_classes: int = 10) -> dict:
    model = build_model(arch, pretrained=False, n_classes=n_classes).eval()
    size = INPUT_SIZE[arch]
    x = torch.randn(1, 3, size, size)

    total, _ = count_parameters(model)

    with torch.no_grad():
        feat = _feature_extractor(model, arch)(x)
        for _ in range(N_WARMUP):
            model(x)
        started = time.perf_counter()
        for _ in range(N_REPEAT):
            model(x)
        cpu_ms = (time.perf_counter() - started) / N_REPEAT * 1000

    return {
        "params": total,
        "params_trieu": round(total / 1e6, 2),
        "input_size": size,
        "feature_map": f"{feat.shape[-2]}x{feat.shape[-1]}",
        "cpu_ms": round(cpu_ms, 1),
        # float32 -> 4 byte/tham số. Đối chiếu: B0 ra 16,1 MB, đúng bằng kích
        # thước thật của mobile/assets/model/tomato_leaf_v1.onnx.
        "kich_thuoc_mb": round(total * 4 / 1e6, 1),
    }


def main() -> None:
    torch.set_num_threads(N_THREADS)
    results = {"n_threads": N_THREADS, "n_repeat": N_REPEAT, "archs": {}}
    for arch in SUPPORTED:
        results["archs"][arch] = measure(arch)
        print(f"{arch:18s} {results['archs'][arch]}", flush=True)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nĐã ghi {OUT}")


if __name__ == "__main__":
    main()
