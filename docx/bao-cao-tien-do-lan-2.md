# BÁO CÁO TIẾN ĐỘ DỰ ÁN — AgriXAI
**Lần 2 · Ngày 22/09/2026**
Đồ án tốt nghiệp — Khoa CNTT, Trường Đại học Đà Lạt
GVHD: TS. Nguyễn Thị Lương · Bảo vệ dự kiến 25–30/11/2026

---

## 1. TỔNG QUAN DỰ ÁN

**AgriXAI** là ứng dụng nhận diện bệnh cây cà chua kết hợp giải thích AI (XAI). Điểm khác biệt cốt lõi: thay vì chỉ trả về nhãn bệnh, hệ thống **khoanh trực tiếp vùng nghi ngờ lên ảnh** bằng Grad-CAM và diễn giải thành câu tiếng Việt thông thường — nông dân thấy được "mô hình đang nhìn vào đâu" mà không cần kiến thức kỹ thuật.

Phạm vi hiện tại: **10 lớp bệnh trên lá cà chua** (bộ PlantVillage). Phần bệnh trên quả (5 lớp) đang chuẩn bị triển khai từ ~12/10/2026.

**Trạng thái tổng thể:**

| Mảng | Trạng thái |
|---|---|
| Model (Bảo) | ✅ Huấn luyện xong, tích hợp thật, có bộ chặn ảnh không phải lá |
| Backend & API | ✅ Chạy đầy đủ, 59/59 test pass |
| Mobile App (Học) | ✅ 17 màn hình, nối API thật, có suy luận ngoại tuyến |
| Web Admin | 🔲 Chưa bắt đầu — đang lên kế hoạch |

---

## 2. TIẾN ĐỘ CHI TIẾT CÁC MẢNG

### 2.1 UI/UX — Design System & User Flow

**Design system** được định nghĩa nhất quán trong `mobile/lib/core/`:

- **Bảng màu:** xanh chủ đạo `#2E6F40` / `#54A96A`, vàng cảnh báo `#F2A104`, hỗ trợ đầy đủ theme sáng/tối.
- **Font chữ:** Open Sans (tất cả màn hình đồng nhất).
- **Component library tùy chỉnh:** `GlassCard`, `GlassBackground`, `AgriButton`, `MetaChip`, `ImageSlot`, `GlassBottomBar`, `AgriIcons` (icon lá hai tông). Tất cả sử dụng lại qua toàn app, không copy-paste.
- **Glassmorphism:** dùng cho bottom navigation và màn đăng nhập; bảng dữ liệu và danh sách dùng nền phẳng, mật độ thông tin cao.

**Toàn bộ luồng người dùng (User Flow):**

```
Mở app
  └─ Chưa đăng nhập → [Đăng nhập] hoặc [Đăng ký] ──────────────────────┐
                                                                         │
  └─ Đã đăng nhập ──────────────────────────────────────────────────────┘
       │
       ├─ [Trang chủ] — xem lô đất, thời tiết, 3 chẩn đoán gần nhất
       │       ├─ Bấm lô đất → [Chi tiết lô đất] → [Sửa lô đất]
       │       └─ Bấm "Chẩn đoán nhanh" ──────────────────────────────┐
       │                                                               │
       ├─ [Chụp / Chọn ảnh] ←─────────────────────────────────────────┘
       │       └─ Chọn 3–5 ảnh → [Đang phân tích]
       │               ├─ Online → gọi POST /diagnoses (backend + Grad-CAM)
       │               └─ Offline/lỗi mạng → ONNX trên máy (CAM cổ điển)
       │                       └─ [Kết quả chẩn đoán]
       │                               ├─ Bật/tắt vùng khoanh XAI
       │                               ├─ Đọc to (TTS)
       │                               ├─ "+ Gán lô đất" (nếu chưa gắn)
       │                               ├─ Chia sẻ lên diễn đàn
       │                               └─ [Gợi ý xử lý]
       │                                       ├─ Cảnh báo lây lan (mức Nặng)
       │                                       ├─ Video hướng dẫn (YouTube)
       │                                       ├─ Triệu chứng / Điều kiện
       │                                       ├─ Cần làm ngay
       │                                       ├─ Thuốc gợi ý
       │                                       └─ Phòng ngừa lâu dài
       │
       ├─ [Danh mục bệnh] → [Chi tiết bệnh]
       ├─ [Lịch sử chẩn đoán] — lọc, phân trang, gán lô từ đây
       ├─ [Diễn đàn] → [Chi tiết bài] → [Soạn bài]
       └─ [Hồ sơ cá nhân] — sửa thông tin, đổi mật khẩu, đăng xuất
```

---

### 2.2 Mobile App — Chi tiết màn hình đã hoàn thành

**Tổng số màn hình: 17/17 (bao gồm navigation shell)**

| # | Màn hình | File | Tình trạng |
|---|---|---|---|
| 1 | Đăng nhập | `login_screen.dart` | ✅ Nối API thật |
| 2 | Đăng ký | `register_screen.dart` | ✅ Nông dân tự tạo tài khoản |
| 3 | Navigation Shell | `app_shell.dart` | ✅ Bottom bar 5 tab |
| 4 | Trang chủ & Lô đất | `home_screen.dart` | ✅ Nối API thật (plots + diagnoses + weather) |
| 5 | Chụp / Chọn ảnh | `capture_screen.dart` | ✅ Camera + thư viện, ghi chú tùy chọn |
| 6 | Đang phân tích | `analyzing_screen.dart` | ✅ Nén ảnh, gọi POST /diagnoses, fallback offline |
| 7 | Kết quả chẩn đoán | `result_screen.dart` | ✅ XAI carousel, TTS, gán lô đất |
| 8 | Gợi ý xử lý | `treatment_screen.dart` | ✅ Thuốc + video YouTube nhúng |
| 9 | Danh mục bệnh | `catalog_screen.dart` | ✅ 10 bệnh, tìm kiếm |
| 10 | Chi tiết bệnh | `disease_detail_screen.dart` | ✅ Triệu chứng, xử lý, phòng ngừa |
| 11 | Lịch sử chẩn đoán | `history_screen.dart` | ✅ Nối API thật, phân trang |
| 12 | Hồ sơ cá nhân | `profile_screen.dart` | ✅ Sửa hồ sơ, đổi mật khẩu |
| 13 | Chi tiết lô đất | `plot_detail_screen.dart` | ✅ Ảnh lô, lịch sử, gán ảnh |
| 14 | Tạo/Sửa lô đất | `plot_form_screen.dart` | ✅ Form + chọn ảnh |
| 15 | Diễn đàn | `forum_screen.dart` | ✅ Danh sách bài, lọc theo bệnh |
| 16 | Chi tiết bài viết | `forum_detail_screen.dart` | ✅ Bình luận, like |
| 17 | Soạn bài viết | `forum_compose_screen.dart` | ✅ Gắn chẩn đoán |

**Tính năng đặc biệt đã hoàn thành:**

- **Suy luận ngoại tuyến (Offline AI):** khi mất mạng, app tự chạy mô hình ONNX trực tiếp trên điện thoại — nông dân ở vùng sóng yếu vẫn chẩn đoán được. Kết quả gồm cả vùng khoanh XAI (CAM cổ điển).
- **Tự đăng ký tài khoản:** nông dân tự tạo tài khoản, đăng nhập luôn mà không cần chờ admin.
- **Chẩn đoán nhiều ảnh:** gửi 3–5 ảnh cùng lúc, kết quả tổng hợp theo đa số phiếu.
- **Bộ chặn ảnh không phải lá:** ảnh cái bàn, sân vườn, bàn tay... bị từ chối trước khi vào mô hình bệnh, tránh kết quả sai gây hiểu lầm.
- **Đọc to kết quả (TTS):** màn Kết quả có nút đọc to kết luận — hỗ trợ nông dân cao tuổi hoặc đang bận tay.
- **Gán lô đất sau khi chẩn đoán:** chẩn đoán nhanh không cần lô đất trước, có thể gán vào lô từ màn Lịch sử về sau.

---

### 2.3 Backend & API

**Tổng endpoints: ~37 endpoints, 59/59 test tự động pass**

| Nhóm endpoint | Endpoint chính | Ghi chú |
|---|---|---|
| **Xác thực** | POST /auth/register, /login, /refresh, /logout; GET+PATCH /auth/me; POST /auth/change-password | Refresh token xoay vòng, access token 30 phút |
| **Người dùng** | GET/POST /users; GET/PATCH/DELETE /users/{id} | Admin-only (tạo/sửa/xóa) |
| **Lô đất** | GET/POST /plots; GET/PATCH/DELETE /plots/{id}; POST /plots/{id}/image | Nông dân chỉ thấy lô của mình |
| **Chẩn đoán** | POST /diagnoses; GET /diagnoses; GET /diagnoses/{id}; PATCH /diagnoses/{id} | Trung tâm của hệ thống, gồm Grad-CAM |
| **Danh mục bệnh** | GET /diseases; GET /diseases/{key} | Đọc từ `shared/data/tomato_diseases.json` |
| **Thuốc gợi ý** | GET/POST /medicines; PATCH/DELETE /medicines/{id}; gán/gỡ theo `disease_key` | Admin CRUD |
| **Video hướng dẫn** | PUT/DELETE /diseases/{key}/guide | Tối đa 1 video/bệnh |
| **Diễn đàn** | GET/POST /forum/posts; GET/DELETE /forum/posts/{id}; POST bình luận; DELETE bình luận; POST like | Kiểm duyệt bởi admin |
| **Thống kê** | GET /stats/dashboard | Số liệu cho admin |
| **Thời tiết** | GET /weather | OpenWeatherMap, cache 10 phút |

**Tích hợp dịch vụ bên thứ ba:**
- OpenWeatherMap API — thời tiết thực tế theo tọa độ
- YouTube (nhúng qua `youtube_player_iframe`) — video hướng dẫn xử lý bệnh

---

### 2.4 Database

**11 bảng, PostgreSQL 16 (Docker)**

| Bảng | Mô tả | Ghi chú thiết kế |
|---|---|---|
| `users` | Tài khoản người dùng (nông dân / admin) | `hashed_password`, cột `email` nullable |
| `refresh_tokens` | Bảng thu hồi token | Lưu băm SHA-256, không lưu token thô |
| `plots` | Lô đất của nông dân | `puc` (mã vùng), `image_path` nullable |
| `diagnoses` | Kết quả chẩn đoán tổng hợp (bản ghi chính) | `disease_key`, `confidence`, `severity`, `affected_ratio`, `model_version` |
| `diagnosis_images` | Kết quả từng ảnh trong lô 3–5 ảnh | Cho phép vẽ carousel XAI từng ảnh |
| `medicines` | Danh sách thuốc gợi ý | Admin CRUD |
| `disease_medicines` | Gán thuốc ↔ bệnh (n-n) | Khoá là `disease_key` (chuỗi, không phải FK) |
| `disease_guides` | Video hướng dẫn theo bệnh (1-1) | Tối đa 1 video/bệnh |
| `forum_posts` | Bài viết diễn đàn | Tùy chọn gắn `diagnosis_id` |
| `forum_comments` | Bình luận bài viết | |
| `forum_post_likes` | Lượt thích bài viết | Toggle like/unlike |

**Quyết định thiết kế đáng chú ý:**
- `disease_key` trong `disease_medicines`/`disease_guides` là **chuỗi thường, không phải khóa ngoại** — vì danh mục bệnh (`Disease`) sống trong file JSON, không có bảng `diseases` trong CSDL.
- Thứ tự bệnh trong `tomato_diseases.json` **khóa chặt với output của mô hình** — đây là bất biến cốt lõi của hệ thống, không được thay đổi sau khi huấn luyện.
- `Diagnosis` lưu `model_version` để truy vết kết quả của từng checkpoint khác nhau về sau.

---

## 3. CÔNG NGHỆ, KIẾN TRÚC & THUẬT TOÁN

### 3.1 Kiến trúc & Tối ưu

**Kiến trúc tổng thể** gồm 3 phần triển khai độc lập:

```
[Mobile App — Flutter]
        │  HTTP / REST (port 8000)
        ↓
[Backend — FastAPI + PostgreSQL]
        │  sys.path import (cùng tiến trình)
        ↓
[Model — PyTorch EfficientNet-B0]
```

**Ranh giới kiến trúc then chốt:** `DiseasePredictor.predict(image) → Prediction` là **hợp đồng duy nhất** giữa backend và model. Backend không import PyTorch trực tiếp; mọi thay đổi bên trong model (augmentation, kiến trúc mạng, kỹ thuật XAI) đều trong suốt với backend.

**Chế độ hybrid online/offline:** ứng dụng luôn thử gọi backend trước; bất kỳ lỗi mạng nào (mất kết nối, timeout 8s, backend sập) đều rơi tự động về suy luận ONNX trên máy — người dùng không cần thao tác thêm.

**Bộ chặn ảnh không phải lá (organ_gate.pt):** đứng trước mô hình bệnh như một cổng lọc. Ảnh bị chặn trả về thông báo tiếng Việt thân thiện, không tạo bản ghi CSDL, không ảnh hưởng số liệu thống kê.

### 3.2 Thuật toán & Hiệu năng

**Mô hình bệnh:**
- Kiến trúc: EfficientNet-B0, huấn luyện 25 epoch (~30 phút trên GPU RTX 4060 Ti)
- Tập dữ liệu: PlantVillage — 18.160 ảnh, 10 lớp lá cà chua
- Chia tập: 70/15/15 theo từng lớp, seed 42

| Chỉ số | Giá trị |
|---|---|
| Test Accuracy (PlantVillage) | **99,60%** |
| Macro F1-Score | **99,55%** |
| Top-3 Accuracy | **100%** |
| Accuracy (PlantDoc — ảnh thực tế) | **30,81%** |
| Thời gian suy luận (GPU) | 31–34 ms |
| Thời gian suy luận (CPU, 4 luồng) | ~215 ms |

**Grad-CAM & XAI:**
- Vùng khoanh được tính bằng Grad-CAM (backend) và CAM cổ điển (mobile offline)
- Hai ngưỡng tách biệt: `HEATMAP_THRESHOLD=0.5` (tính mức độ nặng), `OVERLAY_DRAW_THRESHOLD=0.62` (vẽ vùng khoanh) — tránh việc điều chỉnh hiển thị ảnh hưởng đến phân loại Nhẹ/Trung bình/Nặng
- Đường viền vẽ theo contour thật (sau làm mượt), không phải elip khớp — xử lý đúng vết bệnh không lồi (hình chữ L, dải dài, nhiều nhánh)

**Tổng hợp kết quả nhiều ảnh:** kết quả cuối cùng theo **đa số phiếu** từ 3–5 ảnh gửi lên — giảm sai số do một ảnh chụp không rõ.

**Bộ chặn (organ_gate):**
- EfficientNet-B0, 2 lớp: `tomato_leaf` / `not_tomato_leaf`
- Recall lá thật (PlantDoc): **91,18%** — chặn oan dưới 9%
- Recall lớp âm (ảnh rác): **96,78%**

### 3.3 Bảo mật & Cấu hình

**Xác thực:** JWT (access token 30 phút) + refresh token xoay vòng (30 ngày). Refresh token lưu bản **băm SHA-256** trong bảng `refresh_tokens` — không lưu giá trị thô, thu hồi được phía server khi logout hoặc đổi mật khẩu.

**Phân biệt lỗi 401:** header `WWW-Authenticate` chỉ gắn khi token hết hạn (`get_current_user`), không gắn khi sai mật khẩu nghiệp vụ — tránh app nhầm "sai mật khẩu khi đổi mật khẩu" thành "hết phiên" và tự gọi refresh.

**Upload ảnh:** giới hạn 10 MB/ảnh, nén tối đa 5 vòng từ file gốc (không nén chồng lên ảnh đã nén), kiểm MIME type trước khi xử lý.

**Phân quyền:** `CurrentUser` vs `AdminUser` dependency tách bạch ở tầng FastAPI — API ghi dữ liệu quản trị (thuốc, video, xóa diễn đàn) chỉ `admin` gọi được, không thể leo thang quyền.

**Token mobile:** lưu trong `TokenStore` (SharedPreferences Android được mã hóa bởi OS) — không lưu trong biến toàn cục hay plain text.

---

## 4. VẤN ĐỀ, RỦI RO & ĐIỂM NGHẼN

| Vấn đề / Rủi ro | Mức độ ảnh hưởng | Trạng thái | Giải pháp đề xuất |
|---|:---:|---|---|
| **Domain gap 68,79 điểm** — model đạt 99,6% trên lab nhưng chỉ 30,81% trên ảnh thực tế (PlantDoc) | 🔴 Cao | Đã đo, đang giải quyết | Cắt vùng lá trước khi phân loại (#93), tăng augmentation mô phỏng đồng ruộng (#50) — Bảo đang thực hiện |
| **Grad-CAM chưa đủ tin cậy trên ảnh thực tế** — vùng khoanh rơi ra ngoài lá 25,4% | 🔴 Cao | Đã đo (audit 56 ảnh), phụ thuộc #93 | Sau khi có vùng lá từ #93, dùng tỉ lệ heatmap-trong-lá làm tiêu chí chặn (#90) |
| **Không tự chụp được ảnh ngoài đồng** — nhà vườn không liên hệ được, domain gap đo bằng PlantDoc thay vì ảnh thực địa Đà Lạt | 🟡 Trung bình | Chấp nhận rủi ro (chốt 17/09) | Dùng PlantDoc làm bộ đo; ảnh tự chụp nếu có thêm sau |
| **Video YouTube lỗi "Error code 152"** trên máy ảo | 🟡 Trung bình | Giảm nhẹ (luôn có nút "Mở YouTube") | Kiểm trên điện thoại thật — nhiều khả năng là đặc thù AVD, không phải lỗi trên máy thật |
| **Docker chưa kiểm thử chạy thật** (`docker compose up --build` 4 service) | 🟡 Trung bình | Chưa làm | Ai pull về chạy `docker compose up --build` và báo lại lỗi nếu có |
| **Demo trên IP LAN cố định** — `app_config.dart` hardcode IP, phải đổi khi đổi mạng | 🟢 Thấp | Đã biết, xử lý thủ công | Ghi chú rõ trong `app_config.dart`; xem xét build flavor `demo` trước ngày bảo vệ |
| **Bộ ảnh âm (#91) từ Internet** — khác phân phối ảnh điện thoại | 🟢 Thấp | Chấp nhận rủi ro | Ghi rõ hạn chế khi bảo vệ |

---

## 5. KẾ HOẠCH GIAI ĐOẠN TIẾP THEO

### 5.1 Model (Bảo) — Mốc 2, 4

Các việc theo thứ tự ưu tiên đã chốt:

1. **#93** — Cắt vùng lá trước khi phân loại (nâng accuracy ảnh thực tế)
2. **#90** — Không hiển thị vùng khoanh khi heatmap quá yếu (phụ thuộc #93)
3. **#50 hướng 1** — Tăng augmentation nền ngẫu nhiên, bóng đổ, ánh sáng
4. **#98** — Nâng cấp lên Grad-CAM++
5. **#50 hướng 2** — Fine-tune bằng ảnh PlantDoc (tiêu dữ liệu đo, để sau cùng)

### 5.2 Web Admin — Mốc 3 (dự kiến bắt đầu sau 30/09)

Dựa trên các API đã sẵn sàng ở backend, web admin sẽ được xây dựng với **8 module**:

| # | Module | Chức năng chính | API tương ứng (đã có) |
|---|---|---|---|
| 1 | **Đăng nhập** | Đăng nhập bằng tài khoản admin | POST /auth/login |
| 2 | **Tổng quan** | 4 ô số liệu (người dùng, lô đất, chẩn đoán, bài viết), biểu đồ xu hướng theo ngày, phân bố bệnh, dải cảnh báo khi dùng mô hình giả | GET /stats/dashboard |
| 3 | **Người dùng** | Xem, tạo, sửa, khóa tài khoản; phân quyền farmer/admin | GET/POST/PATCH/DELETE /users |
| 4 | **Lô đất** | Xem danh sách, chi tiết lịch sử chẩn đoán trên từng lô | GET /plots, GET /diagnoses |
| 5 | **Lịch sử chẩn đoán** | Lọc theo nông dân/bệnh/mức độ/ngày, phân trang, xem ảnh gốc + ảnh khoanh Grad-CAM | GET /diagnoses |
| 6 | **Danh mục bệnh** | Xem 10 lớp bệnh (chỉ đọc — thứ tự gắn chặt với output mô hình) | GET /diseases |
| 7 | **Thuốc gợi ý** | CRUD thuốc, gán/gỡ theo từng bệnh | GET/POST/PATCH/DELETE /medicines |
| 8 | **Video hướng dẫn** | Đặt/đổi/gỡ video YouTube cho từng bệnh | PUT/DELETE /diseases/{key}/guide |
| 9 | **Diễn đàn** | Xem, lọc, xóa bài viết/bình luận vi phạm | GET/DELETE /forum/posts |
| 10 | **Tài khoản quản trị** | Sửa hồ sơ cá nhân, đổi mật khẩu | PATCH /auth/me, POST /auth/change-password |

**Công nghệ dự kiến:** Next.js (App Router) + TypeScript + Tailwind CSS, deploy Vercel.
**Lưu ý:** toàn bộ API ghi cần đến backend đều đã sẵn sàng — web admin chỉ cần xây phần giao diện.

### 5.3 Lịch tổng thể còn lại

| Thời gian | Việc |
|---|---|
| 17/09 – 30/09 | Dọn gọn luồng lá (#93, #90, bộ chặn), đóng issue treo Mốc 1/2 |
| ~12/10 – 26/10 | Thu thập + kiểm ảnh quả bệnh (Mốc 6 — có điều kiện) |
| 26/10 – 09/11 | Huấn luyện mô hình quả + bộ định tuyến (lá/quả/khác) |
| 09/11 – 16/11 | Tích hợp phần quả vào backend + mobile |
| 16/11 – 25/11 | Đệm hoàn thiện, tập demo, chuẩn bị bảo vệ |

> ⚠️ **Điểm chốt phụ:** nếu tới 26/10 chưa thu thập xong ảnh quả → bỏ hẳn phần quả, đề tài vẫn đủ bảo vệ với 10 lớp lá.

---

*Tài liệu chi tiết kỹ thuật: `docx/bao-cao-huan-luyen-mo-hinh.md`, `docx/bao-cao-domain-gap.md`, `docx/bao-cao-kiem-gradcam-vet-benh.md`*
