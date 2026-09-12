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

## Quy trình khởi chạy mỗi lần (Docker + máy ảo)

Backend giờ chạy qua `docker-compose` (không còn gõ `uvicorn` tay), container đã
bind `0.0.0.0:8000` sẵn trong `Dockerfile.dev` — bước hay thiếu là **IP LAN đổi
theo mạng, còn `AppConfig.backendHost` thì đứng yên**. Theo đúng thứ tự:

1. **Mở Docker Desktop**, đợi chạy hẳn rồi kiểm tra 4 container đã lên:
   ```bash
   docker compose up -d          # ở gốc repo, nếu chưa bật
   docker ps                     # phải thấy plantdx-backend, plantdx-db,
                                  # plantdx-adminer, plantdx-web-admin đều "Up"
   ```
2. **Lấy IP LAN hiện tại của máy chạy backend:**
   ```powershell
   ipconfig            # tìm IPv4 Address ở adapter đang thật sự online
                        # (Wi-Fi hoặc Ethernet — bỏ qua adapter ảo kiểu 172.x)
   ```
3. **So với `mobile/lib/core/app_config.dart`** — dòng `backendHost`. IP này
   **thay đổi mỗi khi máy đổi mạng** (về nhà, đổi router, đổi Wi-Fi công cộng...)
   nhưng file không tự cập nhật. Lệch IP là nguyên nhân phổ biến nhất của lỗi
   "không thể kết nối tới server" dù Docker đã chạy đúng.

   ⚠️ **Sửa xong file này chưa đủ — phải build lại app.** `backendHost` là
   hằng số `const`, bị đóng cứng vào APK lúc biên dịch. App đã cài sẵn trên máy
   ảo (mở lại bằng cách bấm icon, không qua `flutter run`) **vẫn chạy đúng bản
   build cũ** dù bạn vừa sửa xong source — nó tiếp tục gọi vào IP cũ đã không
   còn tồn tại và báo y hệt lỗi "Không kết nối được tới máy chủ". Đây là lỗi
   thật đã gặp 12/09/2026: sửa `app_config.dart` xong, mở lại app bằng icon
   trên máy ảo, vẫn báo lỗi y như cũ — vì máy ảo đang chạy bản cài từ trước.
   Cách khắc phục đúng, tuỳ tình huống:
   - **Đang có sẵn phiên `flutter run` gắn với máy ảo** (cửa sổ terminal còn
     mở, chưa `q` thoát) → gõ **`R`** (hot restart, chữ hoa) vào cửa sổ đó.
     Hot reload (`r` thường) **không ăn thua** vì đây là hằng số, không phải
     state — Flutter không áp lại giá trị `const` mới qua hot reload.
   - **Không có phiên nào đang chạy** (trường hợp thường gặp nhất — mở app
     bằng icon, không qua terminal) → phải build lại từ đầu:
     ```bash
     cd mobile
     flutter run -d emulator-5554   # hoặc id máy ảo đang mở, xem `flutter devices`
     ```
     Lệnh này build APK mới (kèm IP mới), cài đè lên bản cũ, rồi tự mở app.
     Mất khoảng 30–60 giây cho lần build lại này.
4. **Xác nhận backend sống** trước khi mở app, đỡ mất công đoán:
   ```bash
   curl http://<IP-vừa-lấy>:8000/api/v1/diseases   # kỳ vọng HTTP 200 kèm JSON
   ```
   Lỗi kết nối/timeout ở bước này nghĩa là do mạng/tường lửa/Docker, chưa liên
   quan gì tới `app_config.dart`.
5. **Mở máy ảo Android rồi `flutter run`.** Máy ảo và máy tính chạy Docker dùng
   chung adapter mạng ảo qua NAT của Android Emulator nên vẫn gọi được IP LAN
   của máy thật bình thường — không cần đổi `backendHost` thành `10.0.2.2` (giá
   trị đó chỉ dùng khi backend chạy trực tiếp bằng `uvicorn` trên chính máy host,
   không áp dụng ở đây vì hiện đã chuyển hẳn sang Docker Compose).

### Checklist khi vẫn báo "không thể kết nối tới server"

| Kiểm tra | Lệnh | Kỳ vọng |
|---|---|---|
| Container backend còn sống? | `docker ps` | `plantdx-backend` trạng thái `Up` |
| Backend log có lỗi không? | `docker logs plantdx-backend --tail 50` | Không có traceback, thấy dòng `Uvicorn running` |
| IP trong app có khớp máy hiện tại? | `ipconfig` so với `app_config.dart` | Trùng số |
| Backend trả lời được từ máy tính? | `curl http://<IP>:8000/docs` | HTTP 200 |
| Điện thoại/máy ảo cùng mạng với máy tính? | — | Cùng Wi-Fi/router; máy ảo Android thì không cần, luôn NAT được ra máy host |
| Windows Firewall chặn cổng 8000? | Thử tắt tạm Firewall hoặc thêm rule cho `8000/tcp` | Kết nối được sau khi mở cổng |

**Hai chỗ chắc chắn sẽ vướng khác:**

**1. Điện thoại thật (không phải máy ảo) không gọi được `localhost`.** Trên điện
thoại thật, `localhost` là chính nó chứ không phải máy tính chạy backend — luôn
phải dùng IP LAN như quy trình ở trên, và điện thoại + máy tính phải cùng WiFi.

**2. Ảnh chụp từ điện thoại thường rất nặng** (5–12 MB). Backend giới hạn 10 MB
(`MAX_UPLOAD_MB`). Nên nén ảnh phía app trước khi gửi — vừa tránh lỗi, vừa nhanh
hơn hẳn khi mạng yếu. Ảnh cũng hay bị xoay ngang do thẻ EXIF; backend đã tự xử lý
bước này nên app không cần lo.

## Hiệu năng

Blur là thao tác tốn GPU. Nếu danh sách dài bị rớt khung hình trên máy yếu, cho
các hàng list dùng `GlassStyle.faint` / `softFlat` (bán trong suốt, **không** blur)
thay cho `listRow`; chỉ giữ blur ở thẻ lớn và thanh tab. Nhìn gần như không khác.

Không lưu vào DB. Ảnh được ghi ra đĩa (file thật trong backend/storage/), CSDL chỉ lưu đường dẫn dạng chuỗi (String(255) ở Diagnosis.image_path/overlay_path và DiagnosisImage), không phải BLOB. Đây là cách làm chuẩn — tránh đúng loại nghẽn mà bạn lo (BLOB lớn trong Postgres làm chậm backup/query/replication).

Quy trình khi nhận ảnh (diagnoses.py → storage/local.py):
1. Kiểm tra dung lượng — chặn ngay nếu vượt MAX_UPLOAD_MB = 10.
2. Mở bằng Pillow, tự xoay theo EXIF, resize nếu cạnh lớn nhất > 1280px.
3. Luôn nén lại thành JPEG quality 88, kể cả ảnh gốc là PNG/WEBP/HEIC.
4. Ghi ra storage/uploads/YYYY/MM/<giờ-giây>-<uuid8>.jpg (và storage/overlays/YYYY/MM/... cho ảnh khoanh vùng XAI) — chia theo năm/tháng, không chia theo user/lô đất.
5. Phục vụ lại qua StaticFiles mount thẳng ở /storage/... (không phải endpoint xử lý riêng, không presigned URL).

Có nghẽn khi nhiều ảnh không?

Không đáng lo ở quy mô đồ án. Ba quyết định thiết kế ở trên chính là thứ n
- Resize + nén JPEG trước khi lưu → mỗi ảnh chỉ còn vài trăm KB dù điện thoại chụp ra 5–12 MB, giữ dung lượng đĩa và băng thông ổn định bất kể ảnh gốc nặng cỡ nào.
- Chia thư mục theo năm/tháng → tránh kiểu nghẽn thật của filesystem khi mìn file (tra cứu chậm dần trên ext4/NTFS) — dù ở quy mô demo phải tới hàngchục nghìn ảnh/tháng mới chạm ngưỡng này.
- CSDL chỉ giữ path (255 ký tự) nên bảng diagnoses/diagnosis_images luôn n

Điểm cần biết, không phải bug: khi chẩn đoán nhanh không gắn lô đất (save= nhưng không có bản ghi DB trỏ tới — file "mồ côi", không có cơ chế dọn rác tự động. Đây là đánh đổi có chủ đích (ghi rõ trong code), chấp nhận được ở quy mô đồ án — chỉ là đĩa sẽ tăng dần theo thời gian nếu dùng lâu, không phải vấn đề tốc độ.           
Giới hạn thật sự (nếu sau này mở rộng ngoài phạm vi đồ án): toàn bộ chạy trên một máy, một ổ đĩa — không phải kiến trúc scale-out nhiều server. Nhưng với mục tiêu "chạy trơn tru một mình, end-to-end" mà CLAUDE.md đã chốt phạm vi, cách làm hiện tại là h