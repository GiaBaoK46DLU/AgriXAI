# Bối cảnh dự án

File này ghi lại những quyết định **không suy ra được từ code hay lịch sử Git**.
Đọc trước khi bắt tay vào bất cứ việc gì trong repo này.

---

## Đề tài

Đồ án tốt nghiệp — Khoa CNTT, Trường Đại học Đà Lạt. GVHD: TS. Nguyễn Thị Lương.
Bảo vệ 25–30/11/2026.

**Ứng dụng nhận diện bệnh cây trồng kết hợp XAI.** Điểm khác biệt của đề tài không
phải việc phân loại bệnh — cái đó đã có nhiều người làm — mà là **giải thích được
vì sao mô hình kết luận như vậy**: heatmap Grad-CAM được chuyển thành vùng khoanh
đơn giản trên ảnh kèm một câu tiếng Việt thường ngày, thay vì đưa bản đồ nhiệt kỹ
thuật cho nông dân xem.

Phạm vi: cây cà chua, 10 lớp theo bộ PlantVillage.

## Nhóm

| Người | Phụ trách |
|---|---|
| Đinh Lâm Gia Bảo (2212343) — chủ repo | `model/` — dữ liệu, huấn luyện, Grad-CAM |
| Triệu Quang Học (2212375) | `backend/` — API, CSDL, lưu trữ |
| Cả hai | Tích hợp XAI vào luồng, giao diện |

Trao đổi bằng tiếng Việt. Comment và tài liệu trong repo cũng viết tiếng Việt.

---

## Quyết định về phạm vi (11/08/2026)

Tài liệu `docx/Phân tích đề tài nhóm 3 (1).docx` mô tả việc tích hợp với hai nhóm
khác (nhóm 1 nhật ký canh tác, nhóm 2 bản đồ GIS) qua mã vùng trồng PUC, dùng API
Gateway chung, endpoint `POST /api/disease-reports`.

**Phần đó đã hoãn.** UI và API xây cho riêng nhóm 3 dùng. Mục tiêu trước mắt là hệ
thống chạy trơn tru một mình, end-to-end. Việc gộp với hai nhóm kia tính sau.

Lý do: cách làm cũ bắt nhóm phải chốt schema JSON với hai nhóm khác ngay từ tuần
đầu, tạo phụ thuộc ngoài tầm kiểm soát và rủi ro trễ tiến độ.

Hệ quả khi làm việc:

- Chọn phương án đơn giản nhất phục vụ luồng nội bộ.
- **Không** tự thêm abstraction, versioning hay trường dữ liệu chỉ để "sau này dễ
  tích hợp".
- Trường `puc` vẫn giữ trong CSDL vì bản thân nó là thuộc tính của lô đất.
- `shared/api-contract/` cố ý để trống.
- Nếu đề xuất việc gì chỉ có ý nghĩa cho tích hợp liên nhóm, phải nói rõ đó là việc
  đang hoãn.

---

## Quy ước Git

**Branch:** `<label>/task-<XX>-<short-description>`
Label là tên người: `bao`, `hoc`, `phuc`.
Ví dụ: `bao/task-03-project-list-ui`, `hoc/task-01-project-crud-api`.

**Commit:** `type(scope): short description`
Types: `feat` `fix` `refactor` `docs` `style` `test` `chore`.
Mô tả viết tiếng Anh, chữ thường, thể mệnh lệnh, không chấm cuối câu.
Ví dụ: `feat(api): add POST /api/projects endpoint`.

Không commit thẳng lên `main`.

---

## Ranh giới kiến trúc quan trọng nhất

`model/src/predictor.py` — lớp `DiseasePredictor` là **hợp đồng duy nhất** giữa hai
phần của hệ thống:

```python
predictor.predict(image: PIL.Image) -> Prediction
# Prediction: disease_key, confidence, probabilities, heatmap, model_version, latency_ms
```

Backend chỉ được biết tới interface này, không import trực tiếp PyTorch hay bất cứ
thứ gì khác trong `model/`. Nhờ vậy Bảo đổi kiến trúc mạng, cách augment, kỹ thuật
XAI tuỳ ý mà Học không phải sửa dòng nào.

Khi chưa có checkpoint, backend tự dùng `DummyPredictor` (cùng interface, không cần
torch) nên toàn hệ thống vẫn chạy được để phát triển giao diện song song. Đây là
quyết định có chủ đích, không phải code tạm bợ.

## Danh mục bệnh dùng chung

`shared/data/tomato_diseases.json` là **nguồn sự thật duy nhất** về 10 lớp bệnh —
cả `model/` và `backend/` đều đọc từ đây.

⚠️ **Thứ tự phần tử trong mảng `diseases` chính là thứ tự output của mô hình.** Đổi
thứ tự sau khi đã huấn luyện là làm sai toàn bộ nhãn trả về mà không báo lỗi gì.
Thêm bệnh mới thì thêm vào cuối và phải huấn luyện lại.

---

## Trạng thái hiện tại (11/08/2026)

| Phần | Tình trạng |
|---|---|
| Cấu trúc thư mục + README các cấp | Đã commit lên `main` |
| `shared/data/tomato_diseases.json` | Đã commit |
| `model/` code | Đã commit — **CHƯA CHẠY THỬ**, cần `torch` và bộ PlantVillage |
| `backend/` code | Đã commit — **đã chạy thật**, 17/17 test pass, luồng end-to-end chạy trên PostgreSQL 16 |
| `mobile/` (Flutter) | Chưa bắt đầu — theo đề cương làm từ 01/10/2026 |
| `web-admin/` (React) | Chưa bắt đầu — theo đề cương làm từ 01/10/2026 |

Backend đã chạy được thật: đăng nhập, tạo lô đất, tải ảnh lên, chẩn đoán bằng
`DummyPredictor`, sinh ảnh khoanh vùng, xem lịch sử, dashboard quản trị. Lần chạy
đầu tiên phát hiện hai lỗi thật, đã sửa:

- `CAST(... AS DATE)` làm sập dashboard trên SQLite (SQLite trả về số nguyên, còn
  PostgreSQL trả về `date` — cùng câu SQL cho hai kiểu khác nhau).
- App **không khởi động nổi khi có file `.env`**: pydantic-settings chạy
  `json.loads()` lên field kiểu `list` trước khi validator tách dấu phẩy được gọi.
  Nghĩa là ai làm đúng theo hướng dẫn `copy .env.example .env` sẽ gặp crash ngay.
  Test trước đó pass chỉ vì trong repo không có `.env` — đây vẫn là điểm mù của
  bộ test hiện tại.

Việc tiếp theo: chạy thử `model/` (cần cài torch, tải PlantVillage).

---

## Ba rủi ro đã nhận diện

1. **Domain gap.** PlantVillage chụp lá đơn trên nền đồng nhất trong phòng; mô hình
   thường đạt >99% trên tập test nhưng rớt mạnh với ảnh chụp thật ngoài đồng. Cần
   thu thập 50–100 ảnh thật vào `model/data/field/` và báo cáo cả hai con số. Làm
   sớm trong tháng 9, đừng để tháng 10.
2. **Tốc độ suy luận** trên máy chạy backend lúc demo.
3. **Kết nối mạng** giữa điện thoại và backend khi demo — cùng LAN, đúng IP, tường
   lửa mở cổng.

---

## Thiết lập trên máy mới

```bash
git clone https://github.com/GiaBaoK46DLU/do-an-tot-nghiep.git
cd do-an-tot-nghiep
```

Cần có: Git, Python 3.11, Docker Desktop (cho PostgreSQL), và Flutter + Node khi bắt
đầu phần giao diện.

File `.env` của backend **không nằm trong Git** (chứa khoá bí mật). Trên máy mới phải
tạo lại từ `backend/.env.example`.

⚠️ **Nếu máy đã cài sẵn PostgreSQL** thì dịch vụ đó chiếm cổng 5432 và container
Docker không tranh được. Triệu chứng: `password authentication failed for user
"plantdx"` — vì kết nối đang đi vào PostgreSQL của máy chứ không phải container.
Hoặc tắt dịch vụ đó đi, hoặc đổi cổng publish trong `docker-compose.yml` rồi sửa
`DATABASE_URL` trong `.env` cho khớp.

Máy của Bảo đã vướng đúng chuyện này (PostgreSQL 18 cài sẵn) và **đã xử lý xong**
ngày 11/08/2026 bằng cách chuyển dịch vụ đó sang khởi động thủ công:

```powershell
# PowerShell chạy bằng quyền Administrator
Set-Service postgresql-x64-18 -StartupType Manual
Stop-Service  postgresql-x64-18 -Force
```

Chọn cách này thay vì đổi cổng vì CSDL của dự án là PostgreSQL 16 trong Docker —
giữ nguyên `docker-compose.yml` thì mọi máy trong nhóm chạy giống hệt nhau.
PG18 cài sẵn trên máy không dùng cho việc gì khác nên tắt được, không mất mát gì.

Chi tiết cách chạy từng phần xem `README.md` ở thư mục gốc và README trong mỗi thư
mục con.
