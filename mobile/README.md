# `mobile/` — App cho nông dân (Flutter)

**Chưa bắt đầu.** Mới chỉ dựng khung thư mục. Theo đề cương, phần frontend làm từ **01/10/2026**.

## Vai trò

App di động là giao diện chính mà **nông dân** dùng. Thiết kế theo hướng tối giản — người dùng ngoài đồng, một tay cầm điện thoại, nắng chói, không rành công nghệ.

Đây cũng là thứ hội đồng sẽ nhìn thấy nhiều nhất khi demo.

## Bốn màn hình (theo wireframe trong `docx/`)

| # | Màn hình | Nội dung | API dùng |
|---|---|---|---|
| 1 | **Trang chủ** | Danh sách lô đất theo PUC, nút tròn `+` để chẩn đoán mới | `GET /api/v1/plots` |
| 2 | **Chụp / tải ảnh** | Chụp trực tiếp hoặc chọn ảnh có sẵn, dropdown chọn lô đất | — |
| 3 | **Kết quả chẩn đoán** | Ảnh có elip khoanh vùng nghi ngờ, tên bệnh, mức độ, câu giải thích, nút *Xem gợi ý xử lý* | `POST /api/v1/diagnoses` |
| 4 | **Lịch sử** | Các lần chẩn đoán trước, lọc theo lô đất | `GET /api/v1/diagnoses` |

Màn hình 3 là **trọng tâm của cả đồ án** — nơi phần XAI được thể hiện ra cho người dùng. Đáng đầu tư thời gian nhất.

## Cấu trúc thư mục đã dựng

```
mobile/
├── lib/
│   ├── core/            hằng số, theme, cấu hình địa chỉ API
│   ├── data/            gọi HTTP, lưu token
│   ├── models/          lớp Dart tương ứng schema JSON của backend
│   ├── screens/         home · capture · result · history
│   ├── services/        xử lý nghiệp vụ, chụp ảnh
│   └── widgets/         thành phần dùng lại
├── assets/{images,icons}/
└── test/
```

## Khi bắt đầu làm

```bash
cd mobile
flutter create .          # sinh android/ ios/ — chỉ chạy lần đầu
flutter pub get
flutter run
```

`flutter create .` chạy được trong thư mục đã có sẵn `lib/`, nó không xoá thư mục con có nội dung. Các thư mục `android/`, `ios/`, `build/` đã được `.gitignore` bỏ qua — ai clone repo về chỉ cần chạy lại lệnh trên.

Gói dự kiến cần: `http` hoặc `dio`, `image_picker`, `shared_preferences`, `intl`.

## ⚠️ Hai chỗ chắc chắn sẽ vướng

**1. Điện thoại không gọi được `localhost`.** `localhost` trên điện thoại là chính nó, không phải máy tính chạy backend. Phải dùng IP LAN:

```bash
# Trên máy chạy backend
ipconfig                                          # tìm IPv4, ví dụ 192.168.1.15
uvicorn app.main:app --host 0.0.0.0 --port 8000   # bắt buộc có --host 0.0.0.0
```

Rồi trỏ app tới `http://192.168.1.15:8000`. Điện thoại và máy tính phải cùng WiFi, và tường lửa Windows phải cho phép cổng 8000.

Nên để địa chỉ này ở một chỗ duy nhất trong `lib/core/` để đổi nhanh lúc demo.

**2. Ảnh chụp từ điện thoại thường rất nặng** (5–12 MB). Backend giới hạn 10 MB (`MAX_UPLOAD_MB`). Nên nén ảnh phía app trước khi gửi — vừa tránh lỗi, vừa nhanh hơn hẳn khi mạng yếu.

Ảnh cũng hay bị xoay ngang do thẻ EXIF; backend đã tự xử lý bước này nên app không cần lo.
