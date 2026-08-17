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

Phạm vi: cây cà chua — 10 lớp bệnh trên **lá** theo bộ PlantVillage, cộng thêm 5 lớp
trên **quả** (xem mục mở rộng phạm vi bên dưới). Không làm bệnh trên thân.

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

## Mở rộng phạm vi: thêm bệnh trên quả (chốt 11/08/2026)

Đề tài ban đầu chỉ có 10 lớp lá. Nay thêm **5 lớp trên quả** để đề tài có quy mô hơn.
Đề cương đã nộp không ghi chi tiết số lớp nên không cần xin ý kiến GVHD.

**Bỏ hẳn phần bệnh trên thân.** Lý do: ảnh thân luôn lẫn nền phức tạp, triệu chứng ít
đặc trưng, và bệnh héo rũ (Fusarium/Ralstonia) về bản chất **không chẩn đoán được qua
ảnh** — phải cắt ngang thân xem bó mạch hoặc thử nhúng nước. Tốn công gấp đôi để ra
kết quả yếu nhất, lại là chỗ dễ bị hỏi vặn khi bảo vệ.

### 5 lớp quả

| Lớp | Ghi chú |
|---|---|
| `fruit_healthy` | lớp âm, bắt buộc có |
| `fruit_late_blight` | thối nâu cứng, mảng lớn — nối tiếp lớp lá cùng tên |
| `fruit_bacterial_spot` | đốm sần sùi nổi gờ — nối tiếp lớp lá cùng tên |
| `fruit_anthracnose` | thán thư, vết tròn lõm — **bệnh mới, chỉ có trên quả** |
| `fruit_blossom_end_rot` | thối đáy quả — **bệnh mới**, do thiếu canxi / tưới không đều |

Hai lớp cuối là phần làm đề tài thật sự rộng ra, không phải nhìn cùng một bệnh ở góc
khác. `fruit_blossom_end_rot` **không do nấm hay vi khuẩn** nên khuyến nghị xử lý khác
hẳn: không phun thuốc, mà chỉnh tưới và bón vôi. Cùng với `spider_mites` (côn trùng,
không phải bệnh nhiễm), đây là hai ca chứng minh hệ thống hiểu đúng bản chất tác nhân
chứ không chỉ dán nhãn — nên nhấn mạnh khi bảo vệ.

### Kiến trúc: thêm bộ định tuyến, KHÔNG gộp 15 lớp vào một mô hình

```
ảnh vào
   └─ organ classifier (lá / quả / khác)
        ├─ lá   → mô hình 10 lớp hiện tại  (giữ nguyên, không huấn luyện lại)
        ├─ quả  → mô hình 5 lớp mới
        └─ khác → "Ảnh chưa rõ lá hay quả cà chua, bạn chụp lại giúp mình nhé"
```

Lá và quả cà chua khác nhau rõ về hình dạng lẫn màu nên bộ phân loại bộ phận là bài
toán dễ, vài trăm ảnh mỗi lớp là đủ. Chọn cách này vì **mô hình lá không phải huấn
luyện lại** — giữ nguyên được con số accuracy đã báo cáo.

Nhánh `khác` giải quyết luôn một lỗi thật: người dùng chụp quả thối mà hệ thống vẫn
tự tin trả về "Mốc lá 87%". Việc hệ thống biết khi nào **không** nên trả lời cũng
đúng tinh thần XAI của đề tài.

### Dữ liệu

Cần ~250–300 ảnh/lớp, tổng ~1.500 ảnh. Nguồn: Roboflow Universe và Kaggle (nhãn hay
sai, **phải kiểm tra bằng mắt**), cộng với tự chụp tại Đà Lạt. Ảnh tự chụp còn xử lý
luôn rủi ro domain gap vì đó là ảnh thật ngoài đồng ngay từ đầu.

### ⚠️ Cổng go/no-go ngày 15/09/2026

Từ nay tới 15/09 **chỉ tập trung luồng lá** cho chạy thông end-to-end. Tới mốc đó nếu
luồng lá còn trục trặc thì **bỏ hẳn phần quả, không tiếc**. Phần quả là thứ để tăng
điểm, không phải thứ để cứu đề tài — bỏ đi thì đề tài vẫn đủ để bảo vệ.

Lịch dự kiến nếu qua cổng: 15/09–10/10 thu thập ảnh, 10/10–25/10 huấn luyện mô hình
quả + bộ định tuyến, 25/10–05/11 tích hợp và kiểm thử.

---

## Quy ước Git

**Branch:** `<label>/task-<XX>-<short-description>`
Label là tên người: `bao`, `hoc`.

⚠️ **`XX` là số của issue GitHub tương ứng**, không phải số thứ tự tự đếm.
Issue #26 → nhánh `hoc/task-26-mobile-result-screen`. Nhờ vậy nhìn tên nhánh
là biết ngay đọc issue nào.

Sáu nhánh `bao/task-01` … `bao/task-06` có từ **trước khi** repo có issue nên
số của chúng không liên quan gì tới số issue. Đã merge xong, để nguyên. Từ số
07 trở đi mọi nhánh đều khớp issue.

**Commit:** `type(scope): short description`
Types: `feat` `fix` `refactor` `docs` `style` `test` `chore`.
Mô tả viết tiếng Anh, chữ thường, thể mệnh lệnh, không chấm cuối câu.
Ví dụ: `feat(api): add POST /api/projects endpoint`.

Không commit thẳng lên `main`.

## Issue GitHub

Toàn bộ việc còn lại đã tạo thành **76 issue**, chia **6 mốc**. Đây là nguồn duy
nhất để biết còn phải làm gì — đừng lập bảng công việc song song ở chỗ khác.

| Mốc | Thời gian | Mục tiêu |
|---|---|---|
| 1 | 17/08 – 31/08/2026 | Nền tảng song song: backend chạy trên máy Học, khởi tạo 2 dự án giao diện, dựng môi trường mô hình |
| 2 | 01/09 – 30/09/2026 | Mô hình huấn luyện xong, có Grad-CAM, bắt đầu chụp ảnh thực địa |
| 3 | 01/09 – 15/10/2026 | Giao diện dựng trên `DummyPredictor` — **chạy song song mốc 2** |
| 4 | 01/10 – 31/10/2026 | Hợp nhất mô hình thật, tinh chỉnh XAI, đo trên ảnh thực địa |
| 5 | 15/10 – 25/11/2026 | Báo cáo, slide, tập demo |
| 6 | 15/09 – 05/11/2026 | Bệnh trên quả — **chỉ làm nếu qua cổng go/no-go 15/09** |

Mốc 2 và 3 **cố ý trùng thời gian**: Bảo huấn luyện mô hình, Học dựng giao diện
trên mô hình giả. Đây chính là lý do `DummyPredictor` tồn tại.

Tiền tố mã việc: `MD-` mô hình · `IN-` tích hợp · `FD-` ảnh thực địa ·
`BE-` backend · `MB-` mobile · `WA-` web admin · `OP-` demo/hạ tầng ·
`DC-` báo cáo · `FR-` bệnh trên quả.

Nhãn theo 4 trục: người (`bao`, `hoc`) · mảng (`mang:*`) · mức
(`muc:chan` > `muc:cao` > `muc:thuong` > `muc:tuy-chon`) · trạng thái
(`trang-thai:bi-chan`, `trang-thai:cho-cong-15-09`).

Template issue và PR nằm trong `.github/`.

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

Khi làm phần quả: **không đụng vào mảng `diseases`**. Thêm mảng mới song song
`fruit_diseases` với thứ tự riêng của nó, vì đó là output của một mô hình khác. Mỗi
mảng là không gian chỉ số độc lập — giữ nguyên bất biến "thứ tự mảng = thứ tự output"
cho từng mô hình một.

`Prediction` sẽ cần thêm trường `organ` (`"leaf"` / `"fruit"`) để backend biết tra
mảng nào. Đây là sửa **hợp đồng dùng chung** — phải báo Học trước, không tự đổi.

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
git clone https://github.com/GiaBaoK46DLU/AgriXAI.git
cd AgriXAI
```

Repo đổi tên từ `do-an-tot-nghiep` thành `AgriXAI` ngày 17/08/2026. GitHub tự
chuyển hướng URL cũ nên bản clone cũ vẫn `fetch`/`push` được, nhưng nên chạy
`git remote set-url origin https://github.com/GiaBaoK46DLU/AgriXAI.git` cho gọn.

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
