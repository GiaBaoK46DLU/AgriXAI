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

### Cấu hình đã kiểm chứng (20/08/2026 — máy của Bảo)

| | |
|---|---|
| GPU | NVIDIA RTX 4060 Ti, 8 GiB VRAM, compute capability 8.9 |
| CPU | Intel 16 luồng |
| Python | 3.12.1 |
| torch / torchvision | 2.13.0+cu126 / 0.28.0+cu126 |

Dùng Python 3.12 chứ không phải 3.11 như ghi trong `CLAUDE.md`: bản 3.11 duy nhất
trên máy là stub Microsoft Store, tạo venv từ đó hay hỏng khi Store tự cập nhật.
torch ≥ 2.2 chạy tốt trên 3.12 nên không có lý do gì phải ép 3.11.

**Thời gian huấn luyện đo được** (EfficientNet-B0, batch 32, 224px, AMP bật):

| | |
|---|---|
| Một epoch, backbone mở khoá | ≈ 39 giây |
| Một epoch, backbone đóng băng | ≈ 30 giây |
| Trọn 25 epoch | **≈ 16 phút** |
| VRAM dùng lúc cao nhất | 1,46 / 8 GiB |

Con số đo bằng tensor ngẫu nhiên, **chưa tính khâu đọc ảnh JPEG từ ổ đĩa**. Đo
riêng phần augment thì CPU cấp được ~451 ảnh/giây với `num_workers: 4`, còn GPU
tiêu thụ 343 ảnh/giây — GPU vẫn là nút cổ chai nhưng khoảng cách khá hẹp. Nếu
epoch thực tế lâu hơn 39 giây đáng kể thì thủ phạm là khâu nạp dữ liệu; máy 16
luồng nên nâng `num_workers` lên 8 là dư sức. VRAM còn trống nhiều, muốn nhanh
hơn nữa có thể tăng `batch_size` — nhưng nhớ chỉnh `lr` theo, đừng đổi mỗi batch.

### Ghi log ra file — đã xử lý sẵn

Ghi log thoải mái, không cần cấu hình gì thêm:

```bash
python -m src.training.train --config configs/default.yaml > outputs/logs/train.log
```

Lệnh này **từng làm sập chương trình**. Mọi script trong `model/` đều in tiếng
Việt; khi output bị chuyển hướng ra file hay pipe, Python trên Windows thôi dùng
console API và rơi về bảng mã cp1252 — bảng này không có ký tự tiếng Việt:

```
UnicodeEncodeError: 'charmap' codec can't encode character 'ế'
```

Nghĩa là một lượt huấn luyện 16 phút chết ngay dòng in đầu tiên, chỉ vì muốn giữ
lại log. `src/__init__.py` giờ ép UTF-8 cho `stdout`/`stderr`, đặt ở đó vì đây là
chỗ duy nhất mọi lệnh `python -m src.*` đều đi qua.

> Chú ý khi viết code mới: cái bẫy này nằm ở Python trên Windows chứ không phải ở
> `model/`. Notebook trong `notebooks/` hay script rời ngoài package `src/` sẽ
> không được `src/__init__.py` che cho, gặp lại y nguyên lỗi trên.

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
MODEL_CHECKPOINT=../model/checkpoints/leaf_disease_domain_adapted.pt
MODEL_GATE_CHECKPOINT=../model/checkpoints/organ_gate.pt
MODEL_DEVICE=cpu
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
│   └── field/plantdoc/        Ảnh PlantDoc công khai, tách train/test gốc
├── src/
│   ├── labels.py              Đọc danh mục bệnh — nguồn sự thật về thứ tự lớp
│   ├── predictor.py           ★ HỢP ĐỒNG với backend
│   ├── data/{prepare,dataset}.py
│   ├── models/build.py        Dựng mạng, chọn target layer cho Grad-CAM
│   ├── training/train.py
│   ├── evaluation/evaluate.py
│   ├── xai/{gradcam,visualize}.py
│   └── utils/common.py
├── checkpoints/               Checkpoint theo Git; bản gốc giữ riêng để đối chứng
└── outputs/                   Hình và số liệu cho báo cáo
```

---

## Ghi chú kỹ thuật cần nhớ khi bảo vệ

### Cắt lá, chốt XAI và học domain (#93, #90, #50)

[Báo cáo kết quả và giới hạn](../docx/bao-cao-cat-la-domain-adaptation.md), kèm
[số liệu từng ảnh và protocol](outputs/domain-50-20261104-b8/). Báo cáo phân biệt
kết quả CPU/GPU, mô hình bệnh/bộ chặn, tập train/validation/test. PlantDoc là ảnh
công khai từ Internet, không phải bộ ảnh tự chụp tại Đà Lạt.

- `src/data/leaf_crop.py`: tìm vùng nổi bật bằng màu; giữ ảnh đầy đủ khi mask
  không rõ. Bật/tắt bằng `preprocess.leaf_crop.enabled`. CAM của ảnh cắt được đặt
  lại vào đúng toạ độ ảnh gốc; 12 ảnh kiểm tra nằm ở
  `outputs/domain-50-20261104/coordinate-audit/`, gồm cả trường hợp tách lá chưa tốt.
- `src/xai/reliability.py`: chốt hiển thị dựa vào khối lượng CAM trong lá và lift
  so với diện tích lá. Cấu hình `xai.reliability`: `enabled`, `min_leaf_mass`,
  `min_lift`. Không đủ bằng chứng thì `Prediction.heatmap=None`; backend dùng
  nhánh giải thích/chụp lại sẵn có. Qua chốt không chứng minh chẩn đoán đúng hoặc
  vùng khoanh chính là vết bệnh.
- `src/data/domain_dataset.py`: ghép nền chỉ cho ảnh PV train, nền chỉ từ split
  train của bộ ảnh âm; thêm nắng/bóng đổ. PlantDoc giữ nền thật. Cấu hình
  `augment.outdoor` có thể bật cho `src.training.train`; thí nghiệm đầy đủ #50
  dùng entrypoint `src.training.adapt_domain`.
- Sau fine-tune, thử hiệu chỉnh BN và học nhắc lại/chưng cất từ checkpoint cha.
  Mọi biến thể được chọn bằng validation CPU, batch 1. Chỉ mở test khi đã có
  `selection.json`; không chọn lại checkpoint theo số test.

Cần PV, PlantDoc, các manifest và bộ ảnh âm #91 trên máy để học lại. Từ `model/`,
dùng thư mục đầu ra mới để giữ nguyên bằng chứng cũ:

```powershell
python -u -m src.training.adapt_domain --out outputs/domain-50-new --train-batch-size 8 --num-workers 2 --reuse-crop-validation outputs/domain-50-20261104
python -u -m src.evaluation.select_domain_crop --run outputs/domain-50-new
python -u -m src.evaluation.evaluate_domain --run outputs/domain-50-new
python -u -m src.evaluation.smoke_domain_api --run outputs/domain-50-new
python -m src.evaluation.verify_domain --run outputs/domain-50-new
python -m src.evaluation.domain_report --run outputs/domain-50-new --out ../docx/bao-cao-domain-new.md
```

`--reuse-crop-validation` chỉ dùng khi hash checkpoint, ảnh và danh sách validation
khớp. Bỏ tham số đó để đo cắt lại từ đầu. Bộ ảnh âm không được tải lại tự động;
cần dùng bản sao lưu của nhóm. Cần dependency huấn luyện trong `requirements.txt`
và dependency backend để chạy kiểm tra API. Dữ liệu thô vẫn không lên Git.

`smoke_domain_api` dùng checkpoint thật, SQLite/storage tạm và TestClient.
`smoke_domain_http` kiểm thêm Uvicorn, đăng ký/đăng nhập, loader và cấu hình mặc
định thật, sau khi đã áp dụng cấu hình được chọn. Cả hai không ghi vào DB dev.
Các ca API lặp một ảnh ba lần để kiểm hợp đồng 3–5 ảnh, không tính thành ba mẫu
đánh giá độc lập.

Hash ảnh/checkpoint kiểm byte nghiêm ngặt. Hash văn bản chuẩn hoá CRLF/LF để
kiểm chứng được khi checkout qua Git. Bản đối chứng cũ #98 gắn với mã nguồn
tại commit `c5eec2f`; verifier của thí nghiệm cũ kiểm cả hash mã nguồn nên cần
checkout commit đó để kiểm lại nguyên trạng. Số liệu cũ không bị ghi đè.

### Grad-CAM++ (#98)

Đã cài Grad-CAM++ bên cạnh Grad-CAM gốc. Chọn bằng `xai.method` trong
`configs/default.yaml`: `gradcam` hoặc `gradcam_plusplus`. Khởi động lại backend
sau khi đổi vì predictor được cache khi nạp. Checkpoint và danh mục lớp giữ nguyên.
Mặc định là **Grad-CAM++** từ 02/11/2026 theo quyết định triển khai của nhóm.
Bản ++ cải thiện một số chỉ số nhiệt trên PlantVillage; contour trên PlantDoc
ở ngưỡng hiện tại chưa tốt hơn. Xem [báo cáo và số liệu](../docx/bao-cao-gradcam-plus-plus.md)
và [bản Word ngắn có hình/bảng](../docx/bao-cao-nang-cap-gradcam-plus-plus.docx).

Có thể chọn riêng hoặc quay lại Grad-CAM mà không đổi cấu hình chung:

```python
predictor = DiseasePredictor("checkpoints/leaf_disease_detection_model.pt",
                             xai_method="gradcam_plusplus")
# Đối chứng hoặc quay lại thuật toán cũ: xai_method="gradcam".
```

```powershell
python -m src.xai.visualize --xai-method gradcam_plusplus --num 12 --out outputs/figures/gradcam-plus-plus.png
```

Grad-CAM++ chỉ áp dụng cho suy luận PyTorch; mô hình ONNX trên điện thoại vẫn dùng
CAM cổ điển. Khi bật bản ++ trên server, vùng khoanh online và offline có thể khác.
Các trường của `Prediction` và cách ánh xạ heatmap về kích thước ảnh gốc không đổi.

### Các lựa chọn của mô hình

**Vì sao chọn transfer learning?** Bộ cà chua chỉ ~18k ảnh, còn ImageNet mà backbone đã học có 1.2 triệu ảnh. Huấn luyện từ đầu với dữ liệu nhỏ như vậy gần như chắc chắn overfit.

**Vì sao lấy lớp tích chập cuối cho Grad-CAM?** Đó là điểm cân bằng: đặc trưng đã đủ trừu tượng để mang ngữ nghĩa ("vết đốm nâu có vòng đồng tâm"), nhưng vẫn còn lưới không gian 7×7 nên biết được vết bệnh nằm ở đâu trên lá. Lấy lớp nông hơn thì heatmap chi tiết nhưng vô nghĩa; lấy sau global pooling thì mất sạch thông tin vị trí.

**Vì sao tự cài Grad-CAM thay vì dùng `pytorch-grad-cam`?** Chỉ khoảng 60 dòng, không phụ thuộc phiên bản thư viện ngoài, và quan trọng nhất là nhóm nắm được từng bước để trả lời hội đồng. Interface giữ giống thư viện đó nên đổi sang dùng thư viện sau này cũng không phải sửa chỗ gọi.

**Vì sao lúc suy luận resize thẳng về vuông thay vì center crop?** Center crop cắt mất rìa ảnh, khiến heatmap lệch vị trí khi vẽ đè lên ảnh gốc. Khoanh vùng sai chỗ dù chỉ một chút là mất hết ý nghĩa với người dùng — đây là hệ thống XAI nên độ chính xác vị trí quan trọng ngang độ chính xác nhãn.
