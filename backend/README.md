# `backend/` — API chẩn đoán bệnh

**Phụ trách: Triệu Quang Học**

FastAPI + PostgreSQL. Nhận ảnh từ app di động, gọi mô hình, sinh phần giải thích XAI, lưu kết quả, phục vụ cả app di động lẫn web admin.

---

## Chạy lần đầu

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate              # Windows
pip install -r requirements.txt
copy .env.example .env              # rồi mở ra sửa nếu cần
```

Khởi động PostgreSQL (ở thư mục gốc dự án):

```bash
docker compose up -d
```

Tạo bảng và dữ liệu mẫu:

```bash
python -m app.seed --diagnoses      # tài khoản + lô đất + 40 bản chẩn đoán giả
```

Chạy server:

```bash
uvicorn app.main:app --reload
```

- API docs (bấm **Authorize** để đăng nhập ngay trong trang): http://localhost:8000/docs
- Kiểm tra tình trạng: http://localhost:8000/health

**Tài khoản mẫu**

| Tài khoản | Mật khẩu | Vai trò |
|---|---|---|
| `admin` | `admin123` | Quản trị — thấy toàn hệ thống |
| `nongdan` | `nongdan123` | Nông dân — chỉ thấy dữ liệu của mình |
| `nongdan2` | `nongdan123` | Nông dân |

> Để điện thoại thật gọi được, chạy `uvicorn app.main:app --host 0.0.0.0 --port 8000` và dùng IP LAN của máy (`ipconfig`) thay cho `localhost`.

---

## Backend chạy được ngay cả khi chưa có mô hình

Đây là điểm thiết kế quan trọng nhất của phần này.

Khi `MODEL_CHECKPOINT` trong `.env` để trống (mặc định), hệ thống dùng **`DummyPredictor`** — trả kết quả giả nhưng **đúng hình dạng** với kết quả thật, kèm cả bản đồ nhiệt giả để phần vẽ vùng khoanh vẫn chạy. Nhờ vậy backend, app di động và web admin được xây và kiểm thử đầy đủ **song song** với việc huấn luyện mô hình, thay vì phải chờ nhau.

Kết quả giả là **tất định theo nội dung ảnh** — cùng một ảnh luôn cho cùng kết quả — nên viết được kiểm thử tự động.

Khi có checkpoint thật:

```env
MODEL_CHECKPOINT=../model/checkpoints/best.pt
```

rồi cài thêm `torch` + `torchvision` và khởi động lại. Không sửa một dòng code nào. Endpoint `/health` và dashboard đều báo rõ đang chạy mô hình thật hay giả — để không ai nhầm số liệu demo là số liệu thật.

---

## Các endpoint

Tất cả nằm dưới tiền tố `/api/v1`.

### Xác thực

| Method | Đường dẫn | Mô tả |
|---|---|---|
| POST | `/auth/login` | Đăng nhập bằng JSON (app di động, web admin) |
| POST | `/auth/token` | Đăng nhập dạng form (cho nút Authorize của Swagger) |
| GET | `/auth/me` | Thông tin tài khoản đang đăng nhập |
| PATCH | `/auth/me` | Đổi họ tên, số điện thoại, mật khẩu |

### Lô đất

| Method | Đường dẫn | Mô tả |
|---|---|---|
| GET | `/plots` | Danh sách lô đất, **kèm sẵn tình trạng lần chẩn đoán gần nhất** |
| POST | `/plots` | Tạo lô mới (tự sinh mã PUC nếu bỏ trống) |
| GET | `/plots/{id}` | Chi tiết |
| PATCH | `/plots/{id}` | Cập nhật |
| DELETE | `/plots/{id}` | Xoá (lịch sử chẩn đoán được giữ lại) |

### Chẩn đoán — endpoint trung tâm

| Method | Đường dẫn | Mô tả |
|---|---|---|
| **POST** | **`/diagnoses`** | **Gửi ảnh → nhận kết quả + giải thích XAI** |
| GET | `/diagnoses` | Lịch sử, có phân trang và lọc |
| GET | `/diagnoses/{id}` | Chi tiết đầy đủ |
| PATCH | `/diagnoses/{id}` | Sửa ghi chú, gán lại lô đất |
| DELETE | `/diagnoses/{id}` | Xoá |

Bộ lọc của `GET /diagnoses`: `plot_id`, `user_id` (chỉ admin), `disease_key`, `severity`, `date_from`, `date_to`, `page`, `page_size`.

### Danh mục bệnh (không cần đăng nhập)

| Method | Đường dẫn | Mô tả |
|---|---|---|
| GET | `/diseases` | Toàn bộ 10 lớp |
| GET | `/diseases/{key}` | Triệu chứng, điều kiện phát sinh, gợi ý xử lý, phòng ngừa |

### Thống kê & tài khoản (chỉ quản trị)

| Method | Đường dẫn | Mô tả |
|---|---|---|
| GET | `/stats/dashboard` | **Toàn bộ số liệu trang tổng quan trong 1 request** |
| GET / POST | `/users` | Danh sách / tạo tài khoản |
| GET / PATCH | `/users/{id}` | Chi tiết / cập nhật, khoá, phân quyền |

Ảnh được phục vụ tĩnh tại `/storage/uploads/...` và `/storage/overlays/...`.

---

## Ví dụ gọi thử

```bash
# 1. Đăng nhập, lấy token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"nongdan\",\"password\":\"nongdan123\"}"

# 2. Chẩn đoán một ảnh
curl -X POST http://localhost:8000/api/v1/diagnoses \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@la_ca_chua.jpg" \
  -F "plot_id=1"
```

Kết quả trả về:

```json
{
  "id": 12,
  "disease_key": "early_blight",
  "disease_name": "Đốm vòng (đốm nâu)",
  "confidence": 0.87,
  "severity": "moderate",
  "severity_name": "Trung bình",
  "affected_ratio": 0.24,
  "explanation": "Hệ thống tập trung vào phần giữa của lá — nơi xuất hiện các đốm nâu sẫm có vòng đồng tâm như hình bia bắn, xung quanh ngả vàng. Đây là dấu hiệu đặc trưng của Đốm vòng (đốm nâu) (độ tin cậy 87%, vùng nghi ngờ chiếm khoảng 24% diện tích ảnh).",
  "image_url": "/storage/uploads/2026/09/14103022-a1b2c3d4.jpg",
  "overlay_url": "/storage/overlays/2026/09/14103023-e5f6a7b8.jpg",
  "top_predictions": [
    { "disease_key": "early_blight", "name_vi": "Đốm vòng (đốm nâu)", "probability": 0.87 },
    { "disease_key": "target_spot", "name_vi": "Đốm mắt cua", "probability": 0.07 },
    { "disease_key": "septoria_leaf_spot", "name_vi": "Đốm lá Septoria", "probability": 0.03 }
  ],
  "disease": { "treatments": ["..."], "prevention": ["..."] },
  "model_version": "efficientnet_b0-20260913-1042",
  "disclaimer": "Gợi ý xử lý mang tính tham khảo học thuật..."
}
```

---

## Luồng bên trong `POST /diagnoses`

```
bytes ảnh
  ├─ kiểm tra dung lượng, định dạng
  ├─ open_and_normalize()      xoay đúng chiều theo EXIF, thu nhỏ về ≤1280px
  ├─ predictor.predict()       mô hình + Grad-CAM  → nhãn, độ tin cậy, heatmap
  ├─ explain.interpret()       heatmap → mức độ nặng + vị trí + câu giải thích
  ├─ overlay.draw_regions()    heatmap → elip khoanh vùng trên ảnh
  ├─ lưu 2 ảnh xuống storage/
  └─ ghi 1 bản ghi vào bảng diagnoses
```

Toàn bộ nằm ở `app/services/diagnosis_service.py`.

**Xoay ảnh theo EXIF là bước dễ bị quên nhất.** Ảnh chụp từ điện thoại thường nằm ngang trong file và chỉ hiển thị đúng nhờ thẻ EXIF Orientation. Không xử lý thì mô hình nhận ảnh xoay 90° và độ chính xác tụt hẳn — mà nhìn ảnh trên máy tính lại thấy hoàn toàn bình thường, rất khó phát hiện.

---

## Kiểm thử

```bash
pytest -v
```

Chạy trên SQLite tạm và thư mục lưu trữ tạm, không đụng tới PostgreSQL hay ảnh thật. Luôn dùng `DummyPredictor` nên không cần cài torch.

Bộ test bảo vệ hai thứ quan trọng nhất:
1. Luồng "gửi ảnh → nhận kết quả kèm giải thích XAI" luôn chạy được.
2. Nông dân không bao giờ thấy được dữ liệu của nông dân khác.

---

## Cấu trúc

```
backend/
├── app/
│   ├── main.py                     Khởi động, CORS, mount /storage, /health
│   ├── seed.py                     Dữ liệu mẫu
│   ├── core/{config,security}.py   Cấu hình, băm mật khẩu, JWT
│   ├── db/{session,init_db}.py     Engine, Base, tạo bảng
│   ├── models/                     Bảng: users, plots, diagnoses
│   ├── schemas/                    Pydantic — hợp đồng với frontend
│   ├── api/
│   │   ├── deps.py                 get_current_user, require_admin
│   │   └── v1/endpoints/           auth, plots, diagnoses, diseases, stats, users
│   └── services/
│       ├── diagnosis_service.py    ★ luồng chẩn đoán chính
│       ├── catalog.py              đọc danh mục bệnh dùng chung
│       ├── inference/              base (hợp đồng) · dummy · loader
│       ├── xai/                    explain (mức độ, vị trí, câu chữ) · overlay (vẽ)
│       └── storage/local.py        lưu ảnh (đổi sang S3 chỉ cần sửa file này)
├── migrations/                     Alembic (dùng khi cấu trúc bảng đã ổn định)
├── storage/                        Ảnh người dùng (git bỏ qua)
└── tests/
```

---

## Cơ sở dữ liệu

Ba bảng:

**`users`** — `id`, `username`, `hashed_password`, `full_name`, `phone`, `role` (`admin`/`farmer`), `is_active`, `created_at`

**`plots`** — `id`, `puc`, `name`, `owner_id`, `region`, `area_m2`, `crop`, `status`, `note`, `created_at`

**`diagnoses`** — `id`, `user_id`, `plot_id`, `image_path`, `overlay_path`, `disease_key`, `disease_name`, `confidence`, `probabilities` (JSON), `severity`, `severity_name`, `affected_ratio`, `explanation`, `model_version`, `latency_ms`, `note`, `created_at`

Ghi chú thiết kế:

- **`model_version` lưu theo từng bản chẩn đoán**, không phải cấu hình toàn cục. Cần thiết để sau này giải thích được vì sao cùng một ảnh mà kết quả hôm nay khác hôm qua, và để so sánh chất lượng giữa các lần huấn luyện.
- **Xoá lô đất không xoá lịch sử chẩn đoán** — `plot_id` chỉ được gỡ về `NULL`. Bản ghi chẩn đoán là bằng chứng đã ghi nhận tại thời điểm đó.
- **`probabilities` lưu đủ 10 lớp**, không chỉ lớp thắng. Dùng cho top-3 và cho phân tích lỗi khi viết báo cáo.
- **`role` dùng chuỗi thay vì ENUM của PostgreSQL** — thêm vai trò mới chỉ cần sửa hằng số, không phải viết migration đổi kiểu cột.

Đổi cấu trúc bảng trong giai đoạn phát triển: sửa model rồi chạy lại `python -m app.db.init_db --drop` (mất dữ liệu). Khi đã có dữ liệu cần giữ, chuyển sang Alembic:

```bash
alembic revision --autogenerate -m "mo ta thay doi"
alembic upgrade head
```

---

## Việc còn để ngỏ

- Chưa có rate limit. Demo trong mạng nội bộ thì không cần, triển khai thật thì phải có.
- Ảnh lưu trên ổ đĩa local. Đổi sang S3/MinIO chỉ cần viết lại thân các hàm trong `app/services/storage/local.py`.
- Chưa có refresh token — token sống 7 ngày rồi phải đăng nhập lại.
- Phần tích hợp liên nhóm (nhóm nhật ký canh tác, nhóm bản đồ GIS) chưa làm, theo đúng phạm vi đã chốt: chạy trơn tru một mình trước đã.
