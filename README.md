# Ứng dụng Nhận diện bệnh cây trồng kết hợp XAI

> Đồ án tốt nghiệp — Khoa Công nghệ Thông tin, Trường Đại học Đà Lạt
> GVHD: TS. Nguyễn Thị Lương

Hệ thống nhận diện bệnh trên lá cà chua từ ảnh chụp, **kèm phần giải thích trực quan** (Explainable AI): thay vì chỉ trả về một nhãn bệnh khô khan, hệ thống khoanh vùng đúng khu vực trên ảnh đã khiến mô hình đưa ra kết luận đó, kèm một câu giải thích bằng ngôn ngữ thông thường và gợi ý xử lý.

| | |
|---|---|
| **Sinh viên** | Đinh Lâm Gia Bảo (2212343) — mô hình học máy & XAI |
| | Triệu Quang Học (2212375) — backend, API, lưu trữ |
| **Lớp** | CTK46B |
| **Thời gian** | 12/08/2026 → 30/11/2026 |

---

## Vấn đề đang giải quyết

Các mô hình Deep Learning nhận diện bệnh cây đạt độ chính xác cao nhưng hoạt động như một **"hộp đen"** — chỉ trả về nhãn bệnh mà không giải thích được lý do. Điều này tạo rào cản về *niềm tin*: người nông dân không dám dựa vào kết quả AI để quyết định phun thuốc.

Đồ án này giải quyết rào cản đó bằng cách ghép mô hình phân loại với **Grad-CAM**, rồi đi thêm một bước nữa mà các nghiên cứu thường bỏ qua:

```
Ảnh lá  →  Mô hình phân loại  →  Grad-CAM heatmap  →  Khoanh vùng (contour/elip)  →  Câu giải thích tiếng Việt
                                   (kỹ thuật)              (dễ nhìn)                    (dễ hiểu)
```

Bản đồ nhiệt gốc quá kỹ thuật với nông dân. Hệ thống chuyển nó thành một **vùng khoanh đơn giản trên ảnh** kèm mô tả thường ngày — đây là đóng góp chính của đề tài.

---

## Phạm vi

**Cây cà chua**, 10 lớp theo bộ dữ liệu PlantVillage (9 bệnh + lá khoẻ):

| Khoá | Tên tiếng Việt |
|---|---|
| `bacterial_spot` | Đốm lá vi khuẩn |
| `early_blight` | Đốm vòng (đốm nâu) |
| `late_blight` | Mốc sương muộn |
| `leaf_mold` | Mốc lá |
| `septoria_leaf_spot` | Đốm lá Septoria |
| `spider_mites` | Nhện đỏ hai chấm |
| `target_spot` | Đốm mắt cua |
| `yellow_leaf_curl_virus` | Virus xoăn vàng lá |
| `mosaic_virus` | Virus khảm |
| `healthy` | Lá khoẻ mạnh |

Danh mục đầy đủ (triệu chứng, gợi ý xử lý) nằm ở [`shared/data/tomato_diseases.json`](shared/data/tomato_diseases.json).

> **Phạm vi hiện tại: standalone.** UI và API xây cho riêng nhóm dùng. Việc tích hợp với nhóm 1 (nhật ký canh tác) và nhóm 2 (bản đồ GIS) qua mã vùng trồng PUC sẽ tính sau — mục tiêu trước mắt là hệ thống chạy trơn tru một mình. Trường `puc` vẫn được giữ trong CSDL vì bản thân nó là thuộc tính của lô đất.

---

## Kiến trúc

```
┌─────────────────┐         ┌─────────────────┐
│  Mobile Flutter │         │  Web Admin      │
│  (nông dân)     │         │  React + Vite   │
└────────┬────────┘         └────────┬────────┘
         │      HTTP / JSON          │
         └─────────────┬─────────────┘
                       ▼
         ┌───────────────────────────┐
         │   Backend — FastAPI       │
         │   auth · lô đất · chẩn đoán│
         └─────┬───────────────┬─────┘
               │               │
       ┌───────▼──────┐  ┌─────▼──────┐
       │  PostgreSQL  │  │  storage/  │
       │  metadata    │  │  ảnh gốc + │
       │              │  │  ảnh overlay│
       └──────────────┘  └────────────┘
               ▲
      ┌────────┴─────────┐
      │  DiseasePredictor│  ← ranh giới hợp đồng giữa 2 người
      │  PyTorch + XAI   │
      └──────────────────┘
```

**Ranh giới quan trọng nhất của dự án** là lớp `DiseasePredictor` ([`model/src/predictor.py`](model/src/predictor.py)). Backend chỉ biết tới interface này:

```python
predictor.predict(image: PIL.Image) -> Prediction
# Prediction: disease_key, confidence, probabilities, heatmap (HxW float 0..1), model_version
```

Nhờ vậy hai người làm song song: Bảo thay đổi mô hình bên trong bao nhiêu tuỳ thích, Học không phải sửa một dòng nào. Khi chưa có checkpoint, backend tự động dùng `DummyPredictor` để toàn hệ thống vẫn chạy được — đây là cách nhóm khử rủi ro tích hợp ngay từ tháng 8 thay vì để tới tháng 10.

---

## Cấu trúc thư mục

```
do-an-tot-nghiep/
├── docx/            Tài liệu đồ án (đề cương, phân tích)
├── model/           [Bảo]  PyTorch: dữ liệu, huấn luyện, đánh giá, Grad-CAM
├── backend/         [Học]  FastAPI + PostgreSQL + lưu trữ ảnh
├── mobile/          Flutter — app cho nông dân (4 màn hình)
├── web-admin/       React + Vite — dashboard quản trị (4 trang)
├── shared/          Dữ liệu & hợp đồng dùng chung
│   ├── data/            Danh mục bệnh + gợi ý xử lý
│   └── api-contract/    (để trống — dành cho giai đoạn tích hợp liên nhóm sau này)
├── scripts/         Tiện ích: chuẩn bị dữ liệu, seed CSDL
└── docker-compose.yml   PostgreSQL cho môi trường phát triển
```

Mỗi thư mục con đều có README riêng hướng dẫn chi tiết.

---

## Khởi động nhanh

### 1. Cơ sở dữ liệu

```bash
docker compose up -d
```

PostgreSQL chạy ở `localhost:5432`, database `plantdx`, user/pass `plantdx`/`plantdx`.
(Nếu không dùng Docker: cài PostgreSQL thủ công rồi sửa `DATABASE_URL` trong `backend/.env`.)

### 2. Backend

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
python -m app.seed                                   # tạo tài khoản mẫu + lô đất mẫu
uvicorn app.main:app --reload
```

- API docs: http://localhost:8000/docs
- Tài khoản mẫu: `admin / admin123` (quản trị), `nongdan / nongdan123` (nông dân)

### 3. Web admin

```bash
cd web-admin
npm install
npm run dev          # http://localhost:5173
```

### 4. Mobile

```bash
cd mobile
flutter create .     # sinh android/ ios/ — chỉ chạy lần đầu
flutter pub get
flutter run
```

Xem [`mobile/README.md`](mobile/README.md) để biết cách trỏ app tới đúng địa chỉ IP của máy chạy backend.

### 5. Huấn luyện mô hình (Bảo)

```bash
cd model
pip install -r requirements.txt
# đặt dữ liệu PlantVillage tomato vào model/data/raw/ — xem model/README.md
python -m src.data.prepare
python -m src.training.train --config configs/default.yaml
python -m src.evaluation.evaluate --checkpoint checkpoints/best.pt
```

Sau khi có `checkpoints/best.pt`, trỏ `MODEL_CHECKPOINT` trong `backend/.env` tới file đó rồi khởi động lại backend — hệ thống tự chuyển từ mô hình giả sang mô hình thật.

---

## Kịch bản demo mục tiêu

Đây là đích cần đạt, dùng làm thước đo "hệ thống chạy trơn tru":

> Mở app → thấy danh sách lô đất cà chua → bấm **+** → chụp ảnh lá cà chua ngay tại chỗ → chọn lô đất → gửi → **trong vòng 3 giây** hiện ảnh có elip khoanh đúng vết bệnh, dòng chữ *"Đốm lá vi khuẩn — 87%"*, mức độ, câu giải thích và gợi ý xử lý → bấm lưu → mở web admin trên máy chiếu → bản ghi vừa tạo đã xuất hiện trong bảng và biểu đồ dashboard đã cập nhật.

Ba chỗ dễ vỡ nhất cần canh chừng:

1. **Domain gap** — PlantVillage chụp lá đơn trên nền đồng nhất trong phòng; ảnh chụp thật ngoài đồng khác hẳn. Cần thu thập ảnh thật vào `model/data/field/` và đánh giá riêng trên đó, làm sớm chứ đừng để tháng 10.
2. **Tốc độ suy luận** trên máy chạy backend lúc demo.
3. **Kết nối mạng** giữa điện thoại và backend khi demo (cùng LAN, đúng IP, tường lửa).

---

## Tiến độ theo đề cương

| # | Công việc | Thời gian |
|---|---|---|
| 1 | Phân tích đề tài | 12/08 – 19/08 |
| 2 | Thiết kế chi tiết (kiến trúc, API, CSDL) | 20/08 – 31/08 |
| 3 | Thu thập dữ liệu, tiền xử lý, huấn luyện | 01/09 – 13/09 |
| 4 | Backend + tích hợp mô hình và XAI | 14/09 – 24/09 |
| 5 | **Báo cáo tiến độ lần 1** | 25/09 – 30/09 |
| 6 | Frontend (mobile + web admin) và ghép nối | 01/10 – 04/11 |
| 7 | Tối ưu, tinh chỉnh UX/UI, viết báo cáo | 05/11 – 10/11 |
| 8 | Kiểm thử và hoàn thiện | 11/11 – 15/11 |
| 9 | **Báo cáo tiến độ lần 2** | 16/11 – 18/11 |
| 10 | Sửa chữa, hoàn thiện | 19/11 – 24/11 |
| 11 | **Bảo vệ trước hội đồng** | 25/11 – 30/11 |

---

## Lưu ý về gợi ý xử lý bệnh

Phần gợi ý thuốc bảo vệ thực vật trong `shared/data/tomato_diseases.json` mang **tính tham khảo học thuật**, dựa trên khuyến cáo canh tác phổ biến. Ứng dụng luôn hiển thị khuyến cáo người dùng đối chiếu với cán bộ khuyến nông địa phương và nhãn thuốc trước khi sử dụng. Nhóm không chịu trách nhiệm cho thiệt hại phát sinh từ việc áp dụng máy móc các gợi ý này.

---

## Tài liệu tham khảo

1. Trung tâm Khuyến nông Quốc gia, *Ứng dụng AI trong công tác khuyến nông*, 2024.
2. N. S. H. K. et al., *Leaf-Based Plant Disease Detection and Explainable AI*, arXiv:2404.16833, 2024.
3. IBM, *What is explainable AI (XAI)?*
4. C. Molnar, *Interpretable Machine Learning*, 2nd ed., 2022.
5. J. Gildenblat et al., *PyTorch library for CAM methods*, GitHub, 2021.
6. S. Ramírez, *FastAPI Official Documentation*, 2024.
