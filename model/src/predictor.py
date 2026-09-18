"""HỢP ĐỒNG GIỮA HAI PHẦN CỦA HỆ THỐNG.

Đây là ranh giới duy nhất giữa phần mô hình (Bảo) và phần backend (Học).
Backend chỉ được phép biết tới ``DiseasePredictor.predict()`` và các thuộc tính
của ``Prediction``. Mọi thứ khác bên trong ``model/`` — kiến trúc mạng, cách
huấn luyện, kỹ thuật XAI — có thể thay đổi tự do mà backend không phải sửa gì.

Nhờ vậy hai người làm song song được: backend dùng ``DummyPredictor`` (cùng
interface, không cần PyTorch) để dựng xong toàn bộ luồng từ tháng 8, tới khi có
checkpoint thật thì chỉ đổi cấu hình là chạy.

    from src.predictor import DiseasePredictor

    predictor = DiseasePredictor("checkpoints/best.pt")
    result = predictor.predict(Image.open("la.jpg"))
    print(result.disease_key, result.confidence)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from src.data.dataset import build_infer_transform
from src.models.build import load_checkpoint, target_layer_for_gradcam
from src.xai.gradcam import GradCAM


NOT_LEAF_KEY = "not_tomato_leaf"


@dataclass
class Prediction:
    """Kết quả chẩn đoán một ảnh.

    Attributes:
        disease_key: khoá lớp bệnh, ví dụ ``"early_blight"``. Luôn nằm trong
            danh mục ``shared/data/tomato_diseases.json`` — **trừ** giá trị
            đặc biệt ``"not_tomato_leaf"`` khi bộ chặn của #92 kết luận ảnh
            không phải lá cà chua. Khoá đó **không** có trong danh mục JSON,
            nên backend phải xử lý riêng trước khi tra danh mục (xem #47).
        confidence: xác suất của lớp được chọn, 0..1.
        probabilities: xác suất của TẤT CẢ các lớp, ``{khoá: xác suất}``.
        heatmap: mảng (H, W) float32 trong khoảng 0..1, ĐÚNG kích thước ảnh
            gốc truyền vào. Giá trị càng cao = vùng đó càng ảnh hưởng tới
            quyết định của mô hình. Backend dùng mảng này để vẽ vùng khoanh.
        model_version: định danh phiên bản mô hình, ghi kèm mỗi bản chẩn đoán
            để sau này truy vết được kết quả do mô hình nào sinh ra.
        latency_ms: thời gian suy luận, dùng cho phần đánh giá hiệu năng.
    """

    disease_key: str
    confidence: float
    probabilities: dict[str, float] = field(default_factory=dict)
    heatmap: np.ndarray | None = None
    model_version: str = "unknown"
    latency_ms: float = 0.0


class DiseasePredictor:
    """Nạp checkpoint và chạy suy luận + Grad-CAM trên ảnh đơn lẻ.

    ``gate_checkpoint`` (#92) bật bộ chặn 2 lớp chạy **trước** mô hình bệnh: ảnh
    không phải lá cà chua thì trả thẳng ``disease_key="not_tomato_leaf"`` kèm
    ``heatmap=None``, không chạy mô hình bệnh nữa.

    ⚠️ **Mặc định TẮT, và phải bàn với Học trước khi bật.** Bật lên là backend
    nhận được một ``disease_key`` không có trong ``shared/data/tomato_diseases.json``,
    nên ``catalog.get_disease()`` sẽ lỗi nếu chưa có nhánh xử lý riêng — đây đúng
    là điểm #92 dặn phải thống nhất trước, theo dõi ở #47. Gói bộ chặn vào trong
    lớp này (thay vì thêm trường ``organ`` vào ``Prediction``) là cố ý: hợp đồng
    dùng chung giữa hai phần hệ thống không đổi.
    """

    def __init__(self, checkpoint_path: str | Path, device: str | None = None,
                 gate_checkpoint: str | Path | None = None) -> None:
        path = Path(checkpoint_path)
        if not path.exists():
            raise FileNotFoundError(
                f"Không tìm thấy checkpoint '{path}'. Huấn luyện trước bằng "
                "'python -m src.training.train', hoặc để backend dùng DummyPredictor."
            )

        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self.model, ckpt = load_checkpoint(str(path), self.device)

        self.class_keys: list[str] = ckpt["class_keys"]
        self.image_size: int = ckpt.get("image_size", 224)
        self.model_version: str = ckpt.get("model_version", path.stem)
        self.transform = build_infer_transform(self.image_size)
        self._cam = GradCAM(self.model, target_layer_for_gradcam(self.model, ckpt["arch"]))

        self._gate = None
        if gate_checkpoint is not None:
            gate_path = Path(gate_checkpoint)
            if not gate_path.exists():
                raise FileNotFoundError(
                    f"Không tìm thấy checkpoint bộ chặn '{gate_path}'. Huấn luyện "
                    "trước bằng 'python -m src.training.train_gate'."
                )
            self._gate, gate_ckpt = load_checkpoint(str(gate_path), self.device)
            self._gate_keys: list[str] = gate_ckpt["class_keys"]
            self._gate_transform = build_infer_transform(gate_ckpt.get("image_size", 224))
            self.gate_version: str = gate_ckpt.get("model_version", gate_path.stem)

    def predict(self, image: Image.Image, with_heatmap: bool = True) -> Prediction:
        """Chẩn đoán một ảnh PIL. Ảnh vào kích thước bất kỳ, mọi chế độ màu."""
        started = time.perf_counter()

        image = image.convert("RGB")
        orig_w, orig_h = image.size

        if self._gate is not None:
            gate_tensor = self._gate_transform(image).unsqueeze(0).to(self.device)
            with torch.no_grad():
                gate_probs = torch.softmax(self._gate(gate_tensor), dim=1)[0]
            gate_idx = int(gate_probs.argmax().item())
            if self._gate_keys[gate_idx] == NOT_LEAF_KEY:
                # probabilities để rỗng có chủ đích: mô hình bệnh chưa hề chạy nên
                # không có xác suất bệnh nào để trả. model_version là của bộ chặn
                # vì chính nó ra quyết định này.
                return Prediction(
                    disease_key=NOT_LEAF_KEY,
                    confidence=float(gate_probs[gate_idx].item()),
                    probabilities={},
                    heatmap=None,
                    model_version=self.gate_version,
                    latency_ms=(time.perf_counter() - started) * 1000,
                )

        tensor = self.transform(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            probs = torch.softmax(self.model(tensor), dim=1)[0]

        idx = int(probs.argmax().item())
        heatmap = None
        if with_heatmap:
            cam = self._cam(tensor, class_idx=idx)[0]          # (S, S), 0..1
            heatmap = self._resize_heatmap(cam, orig_w, orig_h)

        return Prediction(
            disease_key=self.class_keys[idx],
            confidence=float(probs[idx].item()),
            probabilities={k: float(p) for k, p in zip(self.class_keys, probs.tolist())},
            heatmap=heatmap,
            model_version=self.model_version,
            latency_ms=(time.perf_counter() - started) * 1000,
        )

    @staticmethod
    def _resize_heatmap(cam: np.ndarray, width: int, height: int) -> np.ndarray:
        """Đưa heatmap về đúng kích thước ảnh gốc để backend vẽ đè lên được."""
        img = Image.fromarray((np.clip(cam, 0, 1) * 255).astype(np.uint8), mode="L")
        img = img.resize((width, height), Image.BILINEAR)
        return np.asarray(img, dtype=np.float32) / 255.0

    def close(self) -> None:
        self._cam.close()
