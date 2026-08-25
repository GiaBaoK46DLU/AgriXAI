# `mobile/` — App cho nông dân (Flutter)

Giao diện đã dựng xong theo bản thiết kế **AgriXAI Farmer v4** (Claude Design).
Toàn bộ 12 màn hình / 13 use case đã có, chạy trên **dữ liệu mẫu hard-code** —
phần gọi API backend là bước tiếp theo.

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
| Nối API | `data/api_client.dart` + `models/` khớp `backend/app/schemas/` |
| Chụp / chọn ảnh thật | `image_picker` + `flutter_image_compress` (giới hạn 10 MB) |
| Ảnh vườn, ảnh lô đất | `assets/images/` đang trống — cần ảnh thật ở Cam Ly, Đà Lạt. Chưa có ảnh thì `ImageSlot` hiện khung nét đứt |
| Ô thời tiết | Chưa có endpoint. Open-Meteo là phương án gọn nhất (không cần API key) |
| Link thuốc | `products[].product_url` chưa có. Thẻ thuốc đã dựng sẵn chỗ; có link thì mở bằng `url_launcher` |
| `productNote` | Bản v4 **không** hiển thị dòng này. Với Virus xoăn vàng lá, thuốc là trừ bọ phấn (môi giới) chứ không trị virus — nên bàn lại xem có thêm dòng đó vào màn 06 không |

## ⚠️ Hai chỗ chắc chắn sẽ vướng

**1. Điện thoại không gọi được `localhost`.** `localhost` trên điện thoại là chính
nó, không phải máy tính chạy backend. Phải dùng IP LAN:

```bash
# Trên máy chạy backend
ipconfig                                          # tìm IPv4, ví dụ 192.168.1.15
uvicorn app.main:app --host 0.0.0.0 --port 8000   # bắt buộc có --host 0.0.0.0
```

Rồi trỏ app tới `http://192.168.1.15:8000`. Điện thoại và máy tính phải cùng WiFi,
và tường lửa Windows phải cho phép cổng 8000. Để địa chỉ này ở một chỗ duy nhất
trong `lib/core/` để đổi nhanh lúc demo.

**2. Ảnh chụp từ điện thoại thường rất nặng** (5–12 MB). Backend giới hạn 10 MB
(`MAX_UPLOAD_MB`). Nên nén ảnh phía app trước khi gửi — vừa tránh lỗi, vừa nhanh
hơn hẳn khi mạng yếu. Ảnh cũng hay bị xoay ngang do thẻ EXIF; backend đã tự xử lý
bước này nên app không cần lo.

## Hiệu năng

Blur là thao tác tốn GPU. Nếu danh sách dài bị rớt khung hình trên máy yếu, cho
các hàng list dùng `GlassStyle.faint` / `softFlat` (bán trong suốt, **không** blur)
thay cho `listRow`; chỉ giữ blur ở thẻ lớn và thanh tab. Nhìn gần như không khác.
