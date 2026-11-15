# Hướng dẫn triển khai và sử dụng AgriXAI

> **Phiên bản:** 15/11/2026 | **Nhóm 3 — Khoa CNTT, Trường ĐH Đà Lạt**

---

## Tổng quan hệ thống

AgriXAI gồm 4 thành phần chạy song song qua Docker Compose:

| Thành phần | Công nghệ | Cổng | Mục đích |
|---|---|---|---|
| Backend API | FastAPI + PostgreSQL | **8000** | Nhận ảnh, chẩn đoán, lưu kết quả |
| Web Admin | Next.js (App Router) | **3000** | Quản trị hệ thống |
| Cơ sở dữ liệu | PostgreSQL 16 | 5432 | Lưu trữ dữ liệu |
| Adminer | Web UI | **8080** | Quản lý DB trực tiếp (dev) |
| Mobile App | Flutter 3.47+ | — | Ứng dụng dành cho nông dân |

---

## 1. Triển khai bằng Docker

### Yêu cầu

- **Docker Desktop** đang chạy (Windows/Mac)
- Git
- RAM trống ≥ 4 GB | Dung lượng ổ đĩa ≥ 3 GB

### Bước 1 — Clone repo

```bash
git clone https://github.com/GiaBaoK46DLU/AgriXAI.git
cd AgriXAI
```

### Bước 2 — Tạo file `.env`

```bash
cp backend/.env.example backend/.env
```

Không cần chỉnh thêm gì. `docker-compose.yml` đã khai báo trực tiếp các biến
quan trọng (`MODEL_CHECKPOINT`, `DATABASE_URL`...) — chúng ghi đè `.env` khi
chạy trong container.

### Bước 3 — Khởi động

```bash
docker compose up --build
```

Lần đầu: 5–10 phút (tải image, build). Các lần sau: ~30 giây.

Dữ liệu seed tự động khi container DB khởi động lần đầu (3 người dùng, 4 lô
đất, 18 chẩn đoán, 15 bài diễn đàn).

### Bước 4 — Kiểm tra

| Dịch vụ | URL |
|---|---|
| API Swagger | http://localhost:8000/docs |
| Web Admin | http://localhost:3000 |
| Adminer | http://localhost:8080 |

### Dừng hệ thống

```bash
docker compose down
```

Dữ liệu giữ nguyên trong Docker volume, không mất khi dừng.

---

## 2. Tài khoản demo

| Vai trò | Tên đăng nhập | Mật khẩu |
|---|---|---|
| Quản trị viên | `admin` | `admin123` |
| Nông dân 1 | `nongdan` | `nongdan123` |
| Nông dân 2 | `nongdan2` | `nongdan123` |

---

## 3. Cài đặt mobile (Flutter)

### Yêu cầu

- Flutter SDK 3.47.2 trở lên
- Android Studio + Android SDK
- Điện thoại thật hoặc máy ảo Android

### Bước 1 — Đổi địa chỉ backend

Mở `mobile/lib/core/app_config.dart`, dòng:

```dart
static const String backendHost = '192.168.1.10';
```

Đổi thành IP LAN của máy đang chạy Docker. Kiểm tra IP bằng:

```powershell
# Windows
ipconfig
# Tìm dòng "IPv4 Address" ở mục Wi-Fi hoặc Ethernet
```

> ⚠️ Điện thoại thật và máy chạy Docker **phải cùng mạng Wi-Fi**.  
> Máy ảo Android dùng địa chỉ cố định **`10.0.2.2`** thay vì IP LAN.

### Bước 2 — Chạy app

```bash
cd mobile
flutter pub get
flutter run
```

> Phải dùng `flutter run` (build lại hoàn toàn) mỗi khi đổi `backendHost`.  
> `backendHost` là `const` nên hot-reload **không có tác dụng**.

### Bước 3 — Build APK (cài thẳng lên điện thoại)

```bash
cd mobile
flutter build apk --release
# APK tại: mobile/build/outputs/flutter-apk/app-release.apk
```

Chép APK vào điện thoại và cài đặt (cần bật "Cài từ nguồn không rõ").

---

## 4. Mô hình AI

| Mô hình | File checkpoint | Mục đích |
|---|---|---|
| Phân loại bệnh lá | `leaf_disease_domain_adapted.pt` | EfficientNet-B0, 10 lớp bệnh lá cà chua |
| Bộ chặn ảnh rác | `organ_gate.pt` | Từ chối ảnh không phải lá cà chua |

Cả hai checkpoint có sẵn trong `model/checkpoints/` và Docker tự nạp khi khởi
động qua biến môi trường `MODEL_CHECKPOINT` / `MODEL_GATE_CHECKPOINT`.

**Phương pháp XAI:** Grad-CAM++ (Chattopadhyay et al., 2017) — tạo heatmap
vùng ảnh hưởng quyết định của mô hình, chuyển thành vùng khoanh elip kèm mô
tả vị trí bằng tiếng Việt thường ngày.

### 10 lớp bệnh

| Khoá | Tên tiếng Việt |
|---|---|
| `bacterial_spot` | Đốm lá vi khuẩn |
| `early_blight` | Đốm nâu (Alternaria) |
| `late_blight` | Mốc sương muộn |
| `leaf_mold` | Mốc lá |
| `septoria_leaf_spot` | Đốm lá Septoria |
| `spider_mites` | Nhện đỏ |
| `target_spot` | Đốm đồng tâm |
| `yellow_leaf_curl_virus` | Xoăn vàng lá (virus) |
| `mosaic_virus` | Virus khảm |
| `healthy` | Lá khoẻ mạnh |

---

## 5. Luồng sử dụng (nông dân)

```
Mở app → Đăng nhập / Đăng ký
    ↓
Trang chủ → Chọn lô đất
    ↓
Nút "Chẩn đoán cho lô này" → Chụp ảnh / Chọn từ thư viện
    ↓          (tối thiểu 1 ảnh, khuyến nghị 3 ảnh nhiều góc)
Màn đang xử lý → Nén ảnh → Gọi POST /diagnoses → Grad-CAM++
    ↓
Kết quả: Tên bệnh + % tin cậy + Ảnh khoanh vùng Grad-CAM++
    ↓
Gợi ý xử lý: Mô tả bệnh · Thuốc khuyến nghị · Video hướng dẫn
    ↓
Lịch sử tự lưu → Xem lại trong tab Lịch sử
```

**Chế độ ngoại tuyến:** Khi mất mạng, app tự chuyển sang suy luận trên máy
(ONNX Runtime + CAM cổ điển) — kết quả tương đương, không có overlay vẽ sẵn từ
backend nhưng vẫn có vùng khoanh tính tại chỗ.

---

## 6. Luồng sử dụng (quản trị viên)

```
http://localhost:3000 → Đăng nhập tài khoản admin
    ↓
Tổng quan: Số liệu hệ thống + Biểu đồ xu hướng + Hoạt động gần đây
    ↓
Người dùng: Thêm/sửa/khoá tài khoản nông dân và admin
Lô đất: Tạo lô đất gán cho nông dân (admin tạo, nông dân canh tác)
Lịch sử: Xem tất cả chẩn đoán, lọc theo bệnh/mức/người dùng
Danh mục bệnh: Xem 10 lớp bệnh (chỉ đọc)
Thuốc gợi ý: CRUD thuốc, gán theo từng bệnh
Video hướng dẫn: Gán URL YouTube theo từng bệnh
Diễn đàn: Kiểm duyệt bài viết và bình luận của nông dân
Tài khoản: Sửa hồ sơ và đổi mật khẩu admin
```

---

## 7. Xử lý sự cố thường gặp

### Container backend liên tục restart

```bash
docker logs plantdx-backend --tail 50
```

Nguyên nhân phổ biến:
- Thiếu file `backend/.env` → tạo từ `backend/.env.example`
- Cổng 8000 bị chiếm → tắt ứng dụng khác dùng cổng đó

### Điện thoại không kết nối được backend

Kiểm tra theo thứ tự:
1. Điện thoại và máy tính **cùng mạng Wi-Fi**?
2. `backendHost` trong `app_config.dart` đúng IP LAN?
3. Tường lửa Windows có chặn cổng 8000?

Mở cổng 8000 trên Windows Firewall (PowerShell quyền Admin):
```powershell
New-NetFirewallRule -DisplayName "AgriXAI Backend" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

### Web Admin hiện dải cảnh báo "Đang dùng mô hình giả"

Dải vàng xuất hiện khi `GET /health` trả `using_real_model: false`:
```bash
docker logs plantdx-backend | grep -i "checkpoint\|model\|error"
```

Thường do `MODEL_CHECKPOINT` trỏ tới file không tồn tại — kiểm tra
`model/checkpoints/` có đủ file không.

### Overlay Grad-CAM++ không hiện

1. Kiểm tra `model/configs/default.yaml` → `xai.reliability.enabled` phải là `false`
2. Thử ảnh chụp cận cảnh hơn (vùng lá chiếm phần lớn khung hình)
3. Kiểm tra response `POST /diagnoses` có trường `overlay_url` không

### PostgreSQL trên máy chiếm cổng 5432

Nếu máy đã cài sẵn PostgreSQL, nó tranh cổng với container. Trên Windows:
```powershell
# Chuyển sang khởi động thủ công (cần quyền Admin)
Set-Service postgresql-x64-18 -StartupType Manual
Stop-Service  postgresql-x64-18 -Force
```

---

## 8. Cấu trúc thư mục

```
AgriXAI/
├── backend/          # FastAPI — API, CSDL, XAI overlay
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   ├── services/xai/   # overlay.py, explain.py
│   │   └── core/config.py
│   ├── tests/
│   └── .env.example
├── model/            # PyTorch — EfficientNet-B0, Grad-CAM++
│   ├── checkpoints/  # leaf_disease_domain_adapted.pt, organ_gate.pt
│   ├── configs/      # default.yaml
│   └── src/
│       ├── predictor.py        # hợp đồng backend ↔ model
│       └── xai/gradcam_plusplus.py
├── mobile/           # Flutter — ứng dụng nông dân
│   ├── lib/
│   │   ├── core/app_config.dart   # ← đổi IP tại đây
│   │   └── services/offline_inference_service.dart
│   └── assets/model/  # ONNX + metadata cho offline
├── web-admin/        # Next.js App Router — giao diện quản trị
│   └── app/admin/
├── shared/
│   └── data/tomato_diseases.json  # nguồn sự thật 10 lớp bệnh
└── docker-compose.yml
```

---

## 9. Thông tin môi trường sản xuất (nếu triển khai lên cloud)

| Thành phần | Hướng đề xuất |
|---|---|
| Backend | Docker container trên VPS (DigitalOcean, AWS EC2, Render) |
| Database | Supabase hoặc PostgreSQL managed (đã chuẩn bị bản Supabase, xem CLAUDE.md) |
| Web Admin | Vercel (Next.js App Router — deploy thẳng bằng `vercel --prod`) |
| Ảnh lưu trữ | Chuyển `storage.local` sang Supabase Storage hoặc S3 |
| Mobile | APK phát tay hoặc Google Play Internal Testing |

> ⚠️ Trước khi cutover sang Supabase: bật RLS cho tất cả bảng (đặc biệt bảng `users`
> chứa `hashed_password`) và dùng `service_role` key cho backend — **không** dùng `anon` key.
