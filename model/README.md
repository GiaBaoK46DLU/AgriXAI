# `model/` — Mô hình nhận diện bệnh + XAI

**Phụ trách: Đinh Lâm Gia Bảo**

Phần này lo toàn bộ vòng đời mô hình: chuẩn bị dữ liệu → huấn luyện → đánh giá → sinh bản đồ nhiệt Grad-CAM. Sản phẩm bàn giao cho backend là **một file checkpoint** và **một lớp Python duy nhất**: `src/predictor.py::DiseasePredictor`.

---

## Cài đặt

```bash
cd model
python -m venv .venv
.venv\Scripts\activate          # Windows;  Linux/macOS: source .venv/bin/activate
```

**Cài PyTorch trước**, đúng theo phần cứng của máy:

```bash
# Có GPU NVIDIA (CUDA 12.1)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Chỉ có CPU
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

Rồi cài phần còn lại:

```bash
pip install -r requirements.txt
```

Kiểm tra GPU đã nhận chưa:

```bash
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

> Huấn luyện bằng CPU vẫn chạy được nhưng chậm khoảng 20–30 lần. Nếu máy không có GPU, dùng **Google Colab** (bản miễn phí đủ dùng cho EfficientNet-B0 với 18k ảnh) rồi tải `best.pt` về.

---

## Chuẩn bị dữ liệu

Tải bộ **PlantVillage** (một trong hai nguồn):

- Kaggle: `abdallahalidev/plantvillage-dataset` — bản color
- Mendeley Data: *Plant Village Dataset* của Hughes & Salathé

Chỉ lấy 10 thư mục cà chua, đặt vào `data/raw/` sao cho có dạng:

```
model/data/raw/
├── Tomato___Bacterial_spot/
├── Tomato___Early_blight/
├── Tomato___Late_blight/
├── Tomato___Leaf_Mold/
├── Tomato___Septoria_leaf_spot/
├── Tomato___Spider_mites Two-spotted_spider_mite/
├── Tomato___Target_Spot/
├── Tomato___Tomato_Yellow_Leaf_Curl_Virus/
├── Tomato___Tomato_mosaic_virus/
└── Tomato___healthy/
```

Tên thư mục phải khớp chính xác với trường `plantvillage_dir` trong `shared/data/tomato_diseases.json`.

Chia tập:

```bash
python -m src.data.prepare
```

Script **không copy ảnh**, chỉ ghi `data/processed/split.csv` gồm đường dẫn + nhãn + tập (train/val/test), chia theo từng lớp để giữ tỉ lệ cân bằng. In ra bảng thống kê số ảnh mỗi lớp — chụp lại bảng này để đưa vào báo cáo.

---

## Huấn luyện

```bash
python -m src.training.train --config configs/default.yaml
```

Chiến lược **transfer learning hai giai đoạn**:

1. **3 epoch đầu** — đóng băng backbone, chỉ huấn luyện lớp phân loại mới. Tránh việc lớp mới (khởi tạo ngẫu nhiên) tạo gradient lớn phá hỏng trọng số đã học từ ImageNet.
2. **Còn lại** — mở khoá toàn bộ, hạ learning rate xuống 1/10 để tinh chỉnh nhẹ nhàng.

Kèm theo: cosine LR schedule, label smoothing, early stopping, mixed precision khi có GPU.

Kết quả: `checkpoints/best.pt` (theo val accuracy tốt nhất) và `outputs/logs/history-*.json`.

Checkpoint **tự mô tả** — chứa cả `arch`, `class_keys`, `image_size` — nên backend nạp được mà không cần biết trước cấu hình huấn luyện.

Đổi kiến trúc: sửa `model.arch` trong config (`efficientnet_b0`, `efficientnet_b3`, `resnet18`, `resnet50`).

---

## Đánh giá

```bash
python -m src.evaluation.evaluate --checkpoint checkpoints/best.pt
```

Sinh ra `outputs/figures/confusion-matrix-test.png` và `outputs/report-test.json` (accuracy, top-3, precision/recall/f1 từng lớp, ma trận nhầm lẫn). Script còn in ra cặp lớp bị nhầm nhiều nhất — đưa vào phần phân tích lỗi của báo cáo.

### ⚠️ Cảnh báo quan trọng về con số accuracy

Ảnh PlantVillage được chụp **lá đơn trên nền đồng nhất trong phòng thí nghiệm**. Mô hình train trên đó thường đạt **>99% trên tập test** nhưng rớt rất mạnh với ảnh chụp thật ngoài đồng (ánh sáng thay đổi, nhiều lá chồng lên nhau, nền lộn xộn, ảnh mờ). Hiện tượng này gọi là **domain gap**, và hội đồng gần như chắc chắn sẽ hỏi.

Cách xử lý:

1. Tự chụp **50–100 ảnh lá cà chua thật** ngoài vườn, gán nhãn (nhờ người có chuyên môn xác nhận nếu được), xếp vào `data/field/` theo đúng cấu trúc thư mục như trên.
2. Sinh manifest riêng cho tập này:
   ```bash
   python -m src.data.prepare --raw-dir data/field --out-dir data/processed/field --test-ratio 1.0 --val-ratio 0.0
   python -m src.evaluation.evaluate --checkpoint checkpoints/best.pt --manifest data/processed/field/split.csv
   ```
3. **Báo cáo cả hai con số.** Thành thật về khoảng cách giữa chúng và giải thích nguyên nhân sẽ được đánh giá cao hơn nhiều so với chỉ khoe con số 99%.

Làm việc này **sớm** (tháng 9), đừng để tháng 10 — nếu kết quả tệ còn kịp bổ sung dữ liệu và tăng cường augmentation.

---

## Sinh hình Grad-CAM cho báo cáo

```bash
python -m src.xai.visualize --checkpoint checkpoints/best.pt --num 12
```

Tạo `outputs/figures/gradcam-samples.png` — lưới ảnh có bản đồ nhiệt phủ lên, tiêu đề xanh nếu đoán đúng, đỏ nếu sai. Đây là hình minh hoạ trung tâm cho phần XAI trong báo cáo.

---

## Bàn giao cho backend

```python
from src.predictor import DiseasePredictor
from PIL import Image

predictor = DiseasePredictor("checkpoints/best.pt")
result = predictor.predict(Image.open("la_ca_chua.jpg"))

result.disease_key     # "early_blight"
result.confidence      # 0.87
result.probabilities   # {"bacterial_spot": 0.02, "early_blight": 0.87, ...}
result.heatmap         # ndarray (H, W) float 0..1 — ĐÚNG kích thước ảnh gốc
result.model_version   # "efficientnet_b0-20260913-1042"
result.latency_ms      # 84.2
```

**Đây là toàn bộ giao diện mà backend được phép biết tới.** Mọi thứ khác bên trong `model/` có thể thay đổi tự do — đổi kiến trúc, đổi cách augment, đổi kỹ thuật XAI — miễn là `predict()` vẫn trả về đúng các trường trên thì backend không phải sửa một dòng nào.

Cách backend nạp:

```env
# backend/.env
MODEL_CHECKPOINT=../model/checkpoints/best.pt
```

Khi biến này rỗng hoặc file không tồn tại, backend tự chuyển sang `DummyPredictor` — toàn hệ thống vẫn chạy được để phát triển giao diện song song.

---

## Cấu trúc

```
model/
├── configs/default.yaml       Toàn bộ siêu tham số — đổi ở đây, không sửa code
├── data/
│   ├── raw/                   PlantVillage gốc (git bỏ qua)
│   ├── processed/split.csv    Manifest chia tập
│   └── field/                 Ảnh tự chụp ngoài đồng
├── src/
│   ├── labels.py              Đọc danh mục bệnh — nguồn sự thật về thứ tự lớp
│   ├── predictor.py           ★ HỢP ĐỒNG với backend
│   ├── data/{prepare,dataset}.py
│   ├── models/build.py        Dựng mạng, chọn target layer cho Grad-CAM
│   ├── training/train.py
│   ├── evaluation/evaluate.py
│   ├── xai/{gradcam,visualize}.py
│   └── utils/common.py
├── checkpoints/best.pt        (git bỏ qua — quá nặng)
└── outputs/                   Hình và số liệu cho báo cáo
```

---

## Ghi chú kỹ thuật cần nhớ khi bảo vệ

**Vì sao chọn transfer learning?** Bộ cà chua chỉ ~18k ảnh, còn ImageNet mà backbone đã học có 1.2 triệu ảnh. Huấn luyện từ đầu với dữ liệu nhỏ như vậy gần như chắc chắn overfit.

**Vì sao lấy lớp tích chập cuối cho Grad-CAM?** Đó là điểm cân bằng: đặc trưng đã đủ trừu tượng để mang ngữ nghĩa ("vết đốm nâu có vòng đồng tâm"), nhưng vẫn còn lưới không gian 7×7 nên biết được vết bệnh nằm ở đâu trên lá. Lấy lớp nông hơn thì heatmap chi tiết nhưng vô nghĩa; lấy sau global pooling thì mất sạch thông tin vị trí.

**Vì sao tự cài Grad-CAM thay vì dùng `pytorch-grad-cam`?** Chỉ khoảng 60 dòng, không phụ thuộc phiên bản thư viện ngoài, và quan trọng nhất là nhóm nắm được từng bước để trả lời hội đồng. Interface giữ giống thư viện đó nên đổi sang dùng thư viện sau này cũng không phải sửa chỗ gọi.

**Vì sao lúc suy luận resize thẳng về vuông thay vì center crop?** Center crop cắt mất rìa ảnh, khiến heatmap lệch vị trí khi vẽ đè lên ảnh gốc. Khoanh vùng sai chỗ dù chỉ một chút là mất hết ý nghĩa với người dùng — đây là hệ thống XAI nên độ chính xác vị trí quan trọng ngang độ chính xác nhãn.
