# BÁO CÁO TIẾN ĐỘ ĐỒ ÁN TỐT NGHIỆP — LẦN 1

**Đề tài:** Ứng dụng nhận diện bệnh cây trồng kết hợp XAI (giải thích được)
**GVHD:** TS. Nguyễn Thị Lương — Khoa Công nghệ thông tin, Trường Đại học Đà Lạt
**Thời điểm báo cáo:** 21/08/2026 (số liệu chốt đến hết ngày 20/08/2026)
**Lịch bảo vệ dự kiến:** 25–30/11/2026

| Thành viên | MSSV | Phụ trách |
|---|---|---|
| Đinh Lâm Gia Bảo (chủ repo) | 2212343 | `model/` — dữ liệu, huấn luyện, Grad-CAM |
| Triệu Quang Học | 2212375 | `backend/` — API, CSDL, lưu trữ |
| Cả hai | — | Tích hợp XAI vào luồng, giao diện |

Mã nguồn: https://github.com/GiaBaoK46DLU/AgriXAI

---

## 1. Tóm tắt đề tài và phạm vi

Hệ thống nhận ảnh lá/quả cà chua do nông dân chụp, phân loại bệnh bằng học sâu,
và — điểm khác biệt của đề tài — **giải thích vì sao mô hình kết luận như vậy**:
bản đồ nhiệt Grad-CAM được chuyển thành vùng khoanh đơn giản trên ảnh kèm một
câu tiếng Việt thường ngày, thay vì đưa bản đồ nhiệt kỹ thuật cho nông dân xem.

**Phạm vi đã chốt:**

- Cây cà chua, **10 lớp bệnh trên lá** theo bộ dữ liệu PlantVillage (đốm lá vi
  khuẩn, đốm vòng, mốc sương muộn, mốc lá, đốm Septoria, nhện đỏ, đốm mắt cua,
  virus xoăn vàng lá, virus khảm, lá khỏe).
- Mở rộng thêm **5 lớp bệnh trên quả** (mục 6.2) — chỉ thực hiện nếu qua cổng
  kiểm soát ngày 15/09/2026.
- **Không** làm bệnh trên thân: triệu chứng ít đặc trưng, và bệnh héo rũ về bản
  chất không chẩn đoán được qua ảnh (phải cắt thân xem bó mạch).
- Việc tích hợp với hai nhóm khác (nhật ký canh tác, bản đồ GIS) **tạm hoãn**
  theo quyết định ngày 11/08/2026 — ưu tiên hệ thống của nhóm chạy thông suốt
  end-to-end trước, tránh phụ thuộc tiến độ ngoài tầm kiểm soát.

## 2. Kiến trúc tổng thể

```
[App Flutter / Web admin React]
        │ HTTP
        ▼
[Backend FastAPI + PostgreSQL 16 (Docker)]
        │ predictor.predict(image) → Prediction
        ▼
[model/ — EfficientNet-B0 + Grad-CAM]
```

Ranh giới quan trọng nhất: lớp `DiseasePredictor` trong `model/src/predictor.py`
là **hợp đồng duy nhất** giữa hai phần. Backend chỉ biết interface
`predict(image) → Prediction` (nhãn bệnh, độ tin cậy, bản đồ nhiệt, phiên bản
mô hình), không phụ thuộc PyTorch. Khi chưa có mô hình thật, backend tự dùng
`DummyPredictor` cùng interface — nhờ đó hai thành viên làm việc **song song
hoàn toàn**: một người huấn luyện mô hình, một người dựng giao diện trên mô
hình giả, ghép lại sau mà không sửa code của nhau.

Danh mục 10 lớp bệnh đặt tại `shared/data/tomato_diseases.json` làm **nguồn sự
thật duy nhất** cho cả hai phần (tên lớp, thứ tự lớp, tên tiếng Việt, triệu
chứng, gợi ý xử lý); thứ tự phần tử trong file chính là thứ tự đầu ra của mô hình.

## 3. Quản lý công việc

Toàn bộ công việc còn lại được lập thành **76 issue trên GitHub**, chia 6 mốc
(Bảng 1). Quy ước nhánh `<tên>/task-<số issue>-<mô tả>`, commit theo chuẩn
`type(scope): description`, không commit thẳng lên `main`, có template issue/PR
riêng. Mốc 2 và mốc 3 cố ý chạy trùng thời gian nhờ cơ chế `DummyPredictor` nêu trên.

**Bảng 1. Sáu mốc công việc và tiến độ tính đến 20/08/2026**

| Mốc | Thời gian | Mục tiêu | Đã đóng / tổng issue |
|---|---|---|---|
| 1 | 17/08 – 31/08 | Nền tảng song song: backend chạy, môi trường mô hình, dữ liệu | **5 / 14** |
| 2 | 01/09 – 30/09 | Mô hình huấn luyện xong, có Grad-CAM, bắt đầu ảnh thực địa | 0 / 8 |
| 3 | 01/09 – 15/10 | Giao diện chạy với mô hình giả (song song mốc 2) | 0 / 19 |
| 4 | 01/10 – 31/10 | Hợp nhất mô hình thật, tinh chỉnh XAI | 0 / 12 |
| 5 | 15/10 – 25/11 | Báo cáo, slide, tập demo | 0 / 11 |
| 6 | 15/09 – 05/11 | Bệnh trên quả (chờ cổng 15/09) | 0 / 12 |

Mốc 1 đang đi trước tiến độ: 5 issue nền tảng của phần mô hình và hạ tầng đã
xong trước hạn 31/08, trong đó 4 issue thuộc chuỗi chuẩn bị huấn luyện
(#10 → #13) hoàn thành ngay trong ngày 20/08.

## 4. Kết quả đạt được

### 4.1. Phần backend (Triệu Quang Học) — đã chạy thật end-to-end

Backend FastAPI hoàn chỉnh (72 file), **17/17 ca kiểm thử tự động pass**, luồng
nghiệp vụ đầy đủ đã chạy thật trên PostgreSQL 16 trong Docker: đăng nhập → tạo
lô đất → tải ảnh lên → chẩn đoán (qua `DummyPredictor`) → sinh ảnh khoanh vùng
kèm câu giải thích → xem lịch sử → dashboard quản trị.

Thành phần chính: xác thực và phân quyền (nông dân / quản trị), quản lý lô đất
(có trường mã vùng trồng PUC), tiếp nhận và lưu ảnh, điều phối chẩn đoán, mô-đun
XAI chuyển bản đồ nhiệt thành vùng khoanh + câu tiếng Việt, thống kê quản trị,
migration CSDL bằng Alembic, seeder dữ liệu mẫu.

Lần chạy thật đầu tiên phát hiện và sửa **hai lỗi thật** mà bộ test không bắt được:

1. `CAST(... AS DATE)` trả kiểu khác nhau giữa SQLite (môi trường test) và
   PostgreSQL (môi trường thật) làm sập dashboard.
2. Ứng dụng không khởi động được khi tồn tại file `.env` do thứ tự parse của
   pydantic-settings — nghĩa là làm đúng theo hướng dẫn cài đặt sẽ gặp crash.
   Đã sửa; điểm mù tương ứng của bộ test đã được ghi nhận.

### 4.2. Phần mô hình (Đinh Lâm Gia Bảo)

**Mã nguồn hoàn chỉnh** cho toàn bộ pipeline: quét dữ liệu và chia tập
(manifest CSV, không nhân bản ảnh), dataset và augmentation, dựng mô hình
transfer learning (4 kiến trúc: EfficientNet-B0/B3, ResNet18/50), vòng huấn
luyện hai giai đoạn (3 epoch đầu đóng băng backbone, sau đó mở khóa với learning
rate giảm 10 lần; kèm cosine schedule, label smoothing, early stopping, mixed
precision), đánh giá per-class kèm ma trận nhầm lẫn, Grad-CAM và công cụ trực
quan hóa, lớp `DiseasePredictor` đóng gói toàn bộ cho backend.

Kiến trúc chọn ban đầu: **EfficientNet-B0** (5,3 triệu tham số, checkpoint
15,6 MB) — ưu tiên suy luận nhanh trên CPU của máy demo; sẽ đối chiếu với
ResNet18 ở giai đoạn sau để phần lựa chọn kiến trúc trong báo cáo có căn cứ
thực nghiệm.

**Môi trường huấn luyện đã kiểm chứng** (20/08): Python 3.12.1, PyTorch
2.13.0+cu126, GPU NVIDIA RTX 4060 Ti 8 GB, Grad-CAM chạy thật trên GPU.

**Dữ liệu đã sẵn sàng** (20/08): tải bộ PlantVillage từ Kaggle
(`abdallahalidev/plantvillage-dataset`, bản màu), trích đúng 10 lớp cà chua —
**18.160 ảnh RGB 256×256**, đối chiếu tự động tên thư mục với danh mục dùng
chung. Dữ liệu chia 70/15/15 theo từng lớp (Bảng 2), kiểm chứng: không có ảnh
nào xuất hiện ở hai tập, chạy lại hai lần cho kết quả trùng khớp từng byte
(seed cố định 42).

**Bảng 2. Phân bố dữ liệu sau khi chia tập**

| Lớp | Huấn luyện | Kiểm định | Kiểm tra | Tổng |
|---|---:|---:|---:|---:|
| Đốm lá vi khuẩn | 1.489 | 319 | 319 | 2.127 |
| Đốm vòng | 700 | 150 | 150 | 1.000 |
| Mốc sương muộn | 1.337 | 286 | 286 | 1.909 |
| Mốc lá | 668 | 142 | 142 | 952 |
| Đốm Septoria | 1.241 | 265 | 265 | 1.771 |
| Nhện đỏ hai chấm | 1.174 | 251 | 251 | 1.676 |
| Đốm mắt cua | 984 | 210 | 210 | 1.404 |
| Virus xoăn vàng lá | 3.751 | 803 | 803 | 5.357 |
| Virus khảm | 263 | 55 | 55 | 373 |
| Lá khỏe mạnh | 1.115 | 238 | 238 | 1.591 |
| **Tổng** | **12.722** | **2.719** | **2.719** | **18.160** |

Ghi nhận từ Bảng 2: dữ liệu **lệch lớp 14,4 lần** (virus xoăn vàng lá 5.357 ảnh
so với virus khảm 373 ảnh) — đây là đặc tính của bộ dữ liệu gốc. Nhóm chủ động
ghi nhận trước để đọc đúng kết quả đánh giá: độ chính xác tổng có thể cao trong
khi recall của lớp ít ảnh thấp; sẽ được theo dõi riêng ở bước đánh giá.

**Chạy thử huấn luyện 1 epoch** (smoke test, 20/08) trước khi huấn luyện đầy đủ:
hoàn tất không lỗi trên GPU; checkpoint tự mô tả đủ 8 trường; thứ tự lớp trong
checkpoint khớp danh mục dùng chung (kiểm bằng code); độ chính xác kiểm định
đạt 0,81 sau đúng 1 epoch đóng băng backbone — xác nhận toàn bộ pipeline nối
đúng. Phép đo thời gian phát hiện khâu nạp ảnh là điểm nghẽn (GPU chờ CPU ~12
giây mỗi epoch); đã tăng số tiến trình nạp dữ liệu từ 4 lên 8, rút thời gian
mỗi epoch từ ~42 giây còn ~35 giây. Ước tính lượt huấn luyện đầy đủ 25 epoch
khoảng **22–25 phút** — hoàn toàn khả thi trên máy cá nhân, không cần Colab.

### 4.3. Hạ tầng chung

- Cấu trúc monorepo 6 phần (`model/`, `backend/`, `mobile/`, `web-admin/`,
  `shared/`, `scripts/`) kèm README hướng dẫn từng cấp.
- Docker Compose cho PostgreSQL 16 — mọi máy trong nhóm chạy môi trường giống nhau.
- Danh mục bệnh `tomato_diseases.json`: 10 lớp × (triệu chứng, điều kiện phát
  sinh, gợi ý xử lý, phòng ngừa) bằng tiếng Việt — vừa là nhãn mô hình, vừa là
  nội dung hiển thị cho nông dân.
- Template issue/PR, quy ước Git, và file bối cảnh dự án (`CLAUDE.md`) để làm
  việc đồng nhất giữa các máy.

Hai phần giao diện (`mobile/` Flutter, `web-admin/` React) đã khởi tạo khung dự
án, theo kế hoạch bắt đầu làm từ 01/10/2026 (mốc 3 cho phép làm sớm từ 01/09
trên `DummyPredictor`).

## 5. Khó khăn đã gặp và cách giải quyết

**Bảng 3. Các vấn đề kỹ thuật đã xử lý**

| Vấn đề | Nguyên nhân | Cách giải quyết |
|---|---|---|
| PostgreSQL trong Docker không nhận kết nối | Máy có sẵn PostgreSQL 18 chiếm cổng 5432, kết nối đi nhầm vào dịch vụ của máy | Chuyển dịch vụ cài sẵn sang khởi động thủ công, giữ nguyên cấu hình Docker để mọi máy giống nhau |
| Ứng dụng backend sập khi có file `.env` | pydantic-settings parse JSON trước khi validator tách dấu phẩy chạy | Sửa cách khai báo field; ghi nhận điểm mù của bộ test |
| Huấn luyện sập ngay dòng in đầu tiên khi ghi log ra file | Python trên Windows rơi về bảng mã cp1252 khi output bị chuyển hướng, không in được tiếng Việt | Ép UTF-8 cho stdout/stderr tại điểm vào chung của package |
| GPU chờ CPU khi huấn luyện với ảnh thật | 4 tiến trình nạp dữ liệu không theo kịp tốc độ GPU trên máy 16 luồng | Tăng lên 8 tiến trình, đo đối chứng xác nhận epoch giảm ~17% |

## 6. Nội dung đáng chú ý về mặt phương pháp

### 6.1. Tính giải thích được (XAI) là trọng tâm

Việc phân loại bệnh cây bằng CNN đã có nhiều nghiên cứu; đóng góp của đề tài
nằm ở tầng giải thích: (1) Grad-CAM chuyển thành vùng khoanh + câu tiếng Việt
cho nông dân; (2) bước **kiểm tra thủ công bắt buộc** xem heatmap có rơi đúng
vết bệnh hay không (phát hiện shortcut learning) trước khi cho hiển thị tới
người dùng; (3) hệ thống biết **từ chối trả lời** khi ảnh không rõ là lá hay
quả cà chua, thay vì đoán bừa với độ tin cậy cao.

### 6.2. Mở rộng sang bệnh trên quả — có cổng kiểm soát rủi ro

Kế hoạch thêm 5 lớp trên quả (khỏe, mốc sương, đốm vi khuẩn, thán thư, thối
đáy quả) theo kiến trúc **bộ định tuyến bộ phận**: ảnh vào được phân loại
lá/quả/khác trước, rồi chuyển cho mô hình 10 lớp lá (giữ nguyên, không huấn
luyện lại) hoặc mô hình 5 lớp quả. Hai lớp mới (thán thư, thối đáy quả) mở
rộng thật sự phạm vi bệnh học; riêng thối đáy quả là rối loạn sinh lý do thiếu
canxi — không phun thuốc mà chỉnh tưới và bón vôi — minh chứng hệ thống phân
biệt đúng bản chất tác nhân chứ không chỉ dán nhãn.

Ràng buộc tự đặt: đến **15/09/2026** nếu luồng lá chưa chạy thông end-to-end
thì bỏ phần quả, không tiếc — phần quả là điểm cộng, không phải điểm tựa của đề tài.

## 7. Rủi ro đang theo dõi

1. **Domain gap** — PlantVillage chụp lá đơn trên nền đồng nhất trong phòng;
   mô hình đạt điểm cao trên tập test cùng phân phối nhưng thường giảm mạnh với
   ảnh chụp thật ngoài đồng. Đối sách: augmentation mạnh ngay từ đầu; thu thập
   50–100 ảnh thực địa tại Đà Lạt trong tháng 9 và báo cáo **cả hai** con số.
2. **Lệch lớp dữ liệu** (mục 4.2) — theo dõi recall từng lớp khi đánh giá,
   đặc biệt lớp virus khảm.
3. **Tốc độ suy luận trên CPU** máy demo (mỗi chẩn đoán kèm một lượt lan truyền
   ngược cho Grad-CAM) — đã chọn kiến trúc nhẹ từ đầu, sẽ đo thực tế sau khi
   huấn luyện xong.
4. **Kết nối mạng khi demo** (điện thoại ↔ backend cùng LAN) — kiểm tra trong
   giai đoạn tập demo.

## 8. Kế hoạch đến kỳ báo cáo tiếp theo

| Việc | Người | Thời gian dự kiến |
|---|---|---|
| Huấn luyện đầy đủ 25 epoch, ghi nhận độ chính xác | Bảo | cuối tháng 08 |
| Đánh giá tập test, ma trận nhầm lẫn, phân tích cặp lớp dễ nhầm | Bảo | đầu tháng 09 |
| Sinh lưới minh họa Grad-CAM; kiểm tra thủ công heatmap 10 lớp | Bảo | đầu tháng 09 |
| Đo tốc độ suy luận trên CPU | Bảo | tháng 09 |
| Bắt đầu chụp ảnh thực địa tại Đà Lạt | Bảo | trong tháng 09 |
| Dựng giao diện mobile + web admin trên `DummyPredictor` (mốc 3) | Học | từ 01/09 |
| Quyết định cổng go/no-go phần quả | cả nhóm | 15/09 |

---

*Số liệu trong báo cáo trích từ các issue và pull request tương ứng trên
repository (issue #10–#13, PR #77–#78), có thể đối chiếu trực tiếp.*
