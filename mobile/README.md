# `mobile/` — App cho nông dân (Flutter)

Giao diện đã dựng xong theo bản thiết kế **AgriXAI Farmer v4** (Claude Design).
Toàn bộ 12 màn hình / 13 use case đã có. Luồng đăng nhập/đăng ký, chẩn đoán và
hồ sơ cá nhân đã nối API thật (xem CLAUDE.md mục "Tích hợp mô hình thật" và
"Tự đăng ký tài khoản"); một số màn (Trang chủ, Lịch sử) vẫn còn dữ liệu mẫu.

## Vai trò

App di động là giao diện chính mà **nông dân** dùng. Thiết kế theo hướng tối giản —
người dùng ngoài đồng, một tay cầm điện thoại, nắng chói, không rành công nghệ.

Đây cũng là thứ hội đồng sẽ nhìn thấy nhiều nhất khi demo.

Màn **05 Kết quả chẩn đoán** là trọng tâm của cả đồ án — nơi phần XAI được thể
hiện ra cho người dùng.

---

## Chạy lần đầu

```bash
cd mobile
flutter create --project-name agrixai_farmer --platforms=android,ios .
flutter pub get
flutter run
```

⚠️ Dùng đúng `--platforms=android,ios` chứ **không** chạy `flutter create .` trơn.
Có `--platforms`, lệnh chỉ sinh thư mục `android/` `ios/` và không đụng vào
`lib/` hay `pubspec.yaml` đã có.

Kiểm tra nhanh:

```bash
flutter analyze
flutter test
```

## Chạy thử end-to-end (backend + app)

**1. Bật backend** (từ thư mục gốc repo, không phải `mobile/`):

```bash
docker compose up -d
```

Chạy xong kiểm tra `http://localhost:8000/health` trả `{"status":"ok",...}`.
Container `plantdx-backend` tự nạp mô hình thật từ `model/checkpoints/` — không
cần cài Python/torch trên máy để chạy backend (chỉ cần Docker Desktop đang mở).

**2. Trỏ app tới đúng backend** — `lib/core/app_config.dart`, hằng số
`backendHost`:

| Chạy app ở đâu | `backendHost` | Vì sao |
|---|---|---|
| Máy ảo Android (AVD, `flutter run`/`flutter build apk`) | `10.0.2.2` (giá trị mặc định hiện tại) | Với máy ảo, `10.0.2.2` là địa chỉ cố định trỏ vào `localhost` của máy thật chạy Docker |
| Điện thoại thật | IP LAN của máy chạy backend, ví dụ `192.168.1.15` (xem bằng `ipconfig`) | `localhost` trên điện thoại thật là chính nó, không phải máy tính — và `10.0.2.2` chỉ có nghĩa trong máy ảo |
| iOS Simulator / Chrome (`flutter run -d chrome`) | `localhost` | Các môi trường này dùng chung mạng với máy host nên `localhost` trỏ đúng |

Đổi xong, chạy `flutter run` (hoặc build lại APK nếu đã cài) — không cần build
lại gì phía backend.

**3. Tài khoản đăng nhập** — ba tài khoản mẫu tạo sẵn bởi
`python -m app.seed` (xem `backend/app/seed.py`):

| Tài khoản | Mật khẩu | Vai trò | Ghi chú |
|---|---|---|---|
| `admin` | `admin123` | Quản trị | Chỉ dùng được qua API/web admin, không cần cho test app di động |
| `nongdan` | `nongdan123` | Nông dân | Có sẵn 3 lô đất + lịch sử chẩn đoán mẫu — tài khoản chính để demo |
| `nongdan2` | `nongdan123` | Nông dân | Có 1 lô đất riêng — dùng để kiểm tra dữ liệu không lẫn giữa hai người dùng |

Ngoài ra màn Đăng nhập có nút **"Chưa có tài khoản? Đăng ký ngay"** (tự tạo tài
khoản `farmer` mới qua `POST /auth/register`, không cần admin cấp trước) và nút
**"Tra cứu bệnh mà không cần đăng nhập"** (vào thẳng app ở chế độ khách — xem
mục "Trạng thái khách" bên dưới).

### Trạng thái khách (chưa đăng nhập)

Vào app qua "Tra cứu bệnh mà không cần đăng nhập" thì dùng được Trang chủ (dữ
liệu mẫu), Danh mục bệnh (dữ liệu thật, không cần đăng nhập) và tab **Tôi**
(hiện "Bạn chưa đăng nhập" kèm nút "Đăng nhập"), nhưng **không** chẩn đoán/lưu
lô đất được — các API đó yêu cầu token. Đăng nhập từ tab Tôi bất cứ lúc nào để
chuyển sang tài khoản thật; đăng xuất từ tab Tôi để quay lại trạng thái khách.
Phiên đăng nhập được lưu lại trên máy (`flutter_secure_storage`) nên tắt mở lại
app không phải đăng nhập lại.

## Nguồn thiết kế

Bản thiết kế gốc: `thi-t-k-mobile-app-farmer-agrixai/project/AgriXAI Farmer v4.dc.html`
(ở gốc repo). Bộ bàn giao kèm ghi chú token và bản đồ màn hình → API nằm trong
`design_handoff_farmer_mobile/README.md` cùng thư mục đó.

⚠️ README bàn giao mô tả bản **v3** (nền xanh nhạt, kính mờ nhẹ). Bản đang dựng là
**v4**: nền xanh đậm hơn và hiệu ứng liquid glass mạnh hơn. Khi hai bên lệch nhau
thì **file `v4.dc.html` là chuẩn** — mọi màu, bo góc, đổ bóng trong `lib/core/`
lấy từ đó.

## Cấu trúc

```
lib/
├── main.dart
├── core/
│   ├── app_colors.dart      bảng màu v4 (rgba giữ nguyên như CSS)
│   ├── app_typography.dart  Open Sans + agriStyle(), letter-spacing theo em
│   ├── app_glass.dart       công thức kính mờ, gradient, đổ bóng
│   ├── app_metrics.dart     padding trên/dưới theo thanh trạng thái máy thật
│   ├── app_theme.dart       ThemeData
│   ├── app_transitions.dart agriRise (.32s ease-out) + agriPulse
│   └── app_scope.dart       trạng thái tab dùng chung + AppNav
├── models/models.dart       Disease · Plot · DiagnosisEntry · DiagnosisCase…
├── data/demo_data.dart      toàn bộ nội dung tiếng Việt của bản thiết kế
├── widgets/                 GlassBackground · GlassCard · nút · chip · hàng list
└── screens/                 12 màn hình
```

### Ba điểm cần biết trước khi sửa

**1. Nền phải nằm dưới thẻ kính.** `BackdropFilter` chỉ làm mờ những gì nằm
**dưới nó trong cây widget**. `GlassBackground` (gradient + 3 quầng sáng) bọc mọi
màn hình qua `AgriScreen`; bỏ ba quầng sáng đi thì thẻ kính không có gì để làm mờ
và trông như màu phẳng.

**2. Icon là SVG hai tông, không phải icon Material.** `widgets/agri_icons.dart`
chép nguyên path SVG từ file thiết kế, mỗi tông một lớp được tô bằng
`ColorFilter` — nhờ vậy đúng màu tuyệt đối. Đừng thay bằng icon nét mảnh của
Material.

**3. Font là bản variable.** `assets/fonts/OpenSans-Variable.ttf` được khai báo
lại cho từng weight trong `pubspec.yaml`, và `agriStyle()` đặt trục `wght` qua
`fontVariations`. Nếu chỉ đặt `fontWeight` thì chữ sẽ ra weight mặc định.

## Đường chuyển giữa các trang

Thiết kế không dùng hiệu ứng trượt ngang kiểu iOS. Mọi màn hình "nổi lên" tại chỗ:
`opacity 0→1` kèm `translateY 12px→0` trong **320ms ease-out** (`agriRise`). Toàn
bộ điều hướng đi qua `AgriRiseRoute`; đổi tab thì `RiseIn` chạy lại đúng hiệu ứng
đó.

Bốn màn có thanh tab (02 · 07 · 10 · 12) nằm trong `AppShell`; tám màn còn lại
được đẩy chồng lên bằng `Navigator` và không có thanh tab.

## Còn lại phải làm

| Việc | Ghi chú |
|---|---|
| Nối API | Đã xong cho đăng nhập/đăng ký, chẩn đoán, hồ sơ cá nhân — xem mục "Chạy thử end-to-end" phía trên. Trang chủ và Lịch sử vẫn còn dữ liệu mẫu (`data/demo_data.dart`) |
| Chụp / chọn ảnh thật | `image_picker` + `flutter_image_compress` (giới hạn 10 MB) |
| Ảnh vườn, ảnh lô đất | `assets/images/` đang trống — cần ảnh thật ở Cam Ly, Đà Lạt. Chưa có ảnh thì `ImageSlot` hiện khung nét đứt |
| Ô thời tiết | Chưa có endpoint. Open-Meteo là phương án gọn nhất (không cần API key) |
| Link thuốc | `products[].product_url` chưa có. Thẻ thuốc đã dựng sẵn chỗ; có link thì mở bằng `url_launcher` |
| `productNote` | Bản v4 **không** hiển thị dòng này. Với Virus xoăn vàng lá, thuốc là trừ bọ phấn (môi giới) chứ không trị virus — nên bàn lại xem có thêm dòng đó vào màn 06 không |

## ⚠️ Một chỗ chắc chắn sẽ vướng

**Ảnh chụp từ điện thoại thường rất nặng** (5–12 MB). Backend giới hạn 10 MB
(`MAX_UPLOAD_MB`). Nên nén ảnh phía app trước khi gửi — vừa tránh lỗi, vừa nhanh
hơn hẳn khi mạng yếu. Ảnh cũng hay bị xoay ngang do thẻ EXIF; backend đã tự xử lý
bước này nên app không cần lo.

## Hiệu năng

Blur là thao tác tốn GPU. Nếu danh sách dài bị rớt khung hình trên máy yếu, cho
các hàng list dùng `GlassStyle.faint` / `softFlat` (bán trong suốt, **không** blur)
thay cho `listRow`; chỉ giữ blur ở thẻ lớn và thanh tab. Nhìn gần như không khác.
