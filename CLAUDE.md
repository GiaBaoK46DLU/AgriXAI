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

## Tự đăng ký tài khoản (chốt 07/09/2026 — đổi quyết định ban đầu)

Thiết kế cũ (ghi trong comment `mobile/lib/screens/login_screen.dart` trước đây):
"Tài khoản do admin cấp, không có màn tự đăng ký". Học đổi quyết định này vì cần
đăng nhập "thật" — nông dân tự tạo tài khoản được, không phải chờ admin tạo hộ.

- `POST /api/v1/auth/register` — công khai, không cần đăng nhập trước. Luôn tạo
  tài khoản vai trò `farmer`, không nhận tham số `role` như `POST /users` (endpoint
  đó vẫn giữ nguyên, chỉ admin gọi được, dùng khi cần tạo tài khoản `admin`).
  Đăng ký xong đăng nhập luôn (trả về access token), không bắt quay lại màn
  Đăng nhập gõ lại mật khẩu.
- Bảng `users` thêm cột `email` (`nullable`, `unique`) — bắt buộc ở tầng schema
  `RegisterRequest` cho người tự đăng ký, nhưng nullable ở DB vì 3 tài khoản
  seed tạo trước khi có cột này (`admin`/`nongdan`/`nongdan2`) không có email lúc
  đó — đã backfill email `*@agrixai.local` cho cả ba để nhất quán.
- Cột `email` được thêm bằng `ALTER TABLE` thủ công trực tiếp trên DB dev, **không
  qua Alembic** dù `Dockerfile.dev` có chạy `alembic upgrade head` mỗi lần khởi
  động. Lý do: `alembic upgrade head` từ trước tới giờ luôn là no-op (thư mục
  `migrations/versions/` rỗng, `alembic_version` rỗng) — toàn bộ schema hiện tại
  sinh ra bằng `create_all` (`app/db/init_db.py`), không qua migration nào. Viết
  một migration lẻ cho riêng cột này mà không có migration nền cho 7 bảng còn lại
  sẽ phá `alembic upgrade head` trên máy mới (thiếu bước tạo bảng gốc). Máy khác
  `pull` code mới rồi chạy container mới hoàn toàn (DB trống) vẫn tự đúng vì
  `create_all` tạo bảng `users` kèm cột `email` ngay từ đầu — chỉ DB **đã tồn tại**
  từ trước (như trên máy Học) mới cần tự chạy `ALTER TABLE users ADD COLUMN email
  VARCHAR(255)` một lần. Bao giờ thật sự cần Alembic (nhiều máy có dữ liệu thật
  cần đồng bộ schema) thì phải viết migration nền cho toàn bộ 7 bảng trước.
- `email-validator` thêm vào `backend/requirements.txt` (bắt buộc để dùng
  `pydantic.EmailStr`).

---

## Tích hợp mô hình thật (chốt 07/09/2026 — IN-01, IN-02)

Mốc 4 lẽ ra bắt đầu 01/10 nhưng Bảo chủ động kéo sớm phần này lên ngay sau khi có
`checkpoints/best.pt` (07/09/2026), vì checkpoint đã sẵn sàng và không có lý do để
chờ. Làm trên nhánh riêng `bao/task-42-real-model-and-mobile-integration`, tự
kiểm tra rồi merge thẳng — Bảo chủ động bỏ bước chờ review cho riêng lần này.

**IN-01 — cài torch ở đâu:** chọn **một môi trường chung** (Option 1 trong issue),
không phải venv riêng. Lý do không suy ra được từ code: `services/inference/loader.py`
nạp mô hình bằng cách `sys.path.insert` rồi `import` thẳng code trong `model/`
**trong cùng tiến trình** chạy uvicorn — không qua RPC hay subprocess nào. Vậy nên
venv riêng cho torch là bất khả thi trừ khi xây thêm một lớp giao tiếp giữa hai
tiến trình, việc đó không đáng để làm chỉ vì muốn tách gọn dependency. Cài bản
**CPU-only** (`backend/requirements-model.txt`, `--index-url
https://download.pytorch.org/whl/cpu`) vì máy demo không có GPU — bản CPU nhẹ hơn
nhiều so với bản CUDA. `backend/requirements.txt` giữ nguyên không có torch để máy
chỉ cần `DummyPredictor` (CI, dựng giao diện) không phải tải PyTorch.

**IN-02 — bật mô hình thật:** `MODEL_CHECKPOINT` trong `backend/.env` trỏ tới
`../model/checkpoints/leaf_disease_detection_model.pt`. Đã xác minh trước khi bật:
`class_keys` trong checkpoint khớp **đúng thứ tự** mảng `diseases` trong
`shared/data/tomato_diseases.json` (so bằng code, không phải bằng mắt) — an toàn
với cảnh báo ở đầu file này về việc lệch thứ tự.

### Danh mục thuốc gợi ý + video hướng dẫn — lệch hướng so với issue #84

Issue **#84 (MB-15)** đề xuất thêm mảng `products` thẳng vào
`shared/data/tomato_diseases.json`. Bảo chọn hướng khác: ba bảng CSDL mới
(`medicines`, `disease_medicines`, `disease_guides`), **không đụng file JSON**.

Lý do: `products`/video là thứ web admin cần **CRUD được thật** sau này (theo yêu
cầu 07/09/2026 của Bảo — xem mục "Phạm vi tương lai: web admin" bên dưới). File
JSON tĩnh nằm trong Git không phải chỗ để admin sửa qua giao diện web. Đặt trong
CSDL thay vì JSON cũng tự nó tránh được đúng rủi ro issue #84 lo ngại ("nguồn sự
thật thứ hai" cho danh mục bệnh) vì không hề đụng tới file JSON.

`disease_key` trong ba bảng mới là **chuỗi thường, không phải khoá ngoại** — vì
`Disease` vẫn chỉ tồn tại trong JSON, không có bảng `diseases` trong CSDL để tham
chiếu tới. Cố tình để vậy, đừng "sửa" thành FK.

**Cân nhắc đã bỏ qua có chủ đích:** không biến toàn bộ danh mục bệnh (`Disease`)
thành bảng CSDL luôn trong lần này. Thứ tự lớp trong JSON gắn chặt với output của
một checkpoint cụ thể — đưa vào CSDL sẽ cần thêm câu chuyện versioning/thứ tự mà
chưa ai yêu cầu, đúng kiểu abstraction "để sau này dễ hơn" mà phần *Quyết định về
phạm vi* ở trên đã nói không nên tự thêm. Khi nào web admin thật sự cần "CRUD bệnh
cây" (sửa triệu chứng/cách xử lý), hướng làm nên là bảng `disease_overrides` khoá
theo `disease_key`, đọc đè lên JSON — JSON vẫn giữ quyền quyết khoá/thứ tự.

---

## Phạm vi tương lai: web admin (chốt hướng 07/09/2026 — CHƯA LÀM)

`web-admin/` hiện chỉ là khung Vite trống (xem bảng Trạng thái hiện tại bên dưới).
Mục này **chỉ ghi lại hướng đi** để phiên làm việc sau không phải suy nghĩ lại từ
đầu — không phải việc cần làm ngay, và không có issue GitHub nào cho phần này.

| Chức năng | Bảng/endpoint đã có sẵn | Việc còn thiếu |
|---|---|---|
| CRUD thuốc (`medicines`) | Model đã có (`app/models/medicine.py`) | Chưa có endpoint ghi — hiện chỉ đọc qua `GET /diseases/{key}` |
| Gán thuốc theo bệnh, sửa link mua (`disease_medicines`) | Model đã có, seed mẫu trong `app/seed.py` | Chưa có endpoint ghi |
| CRUD video hướng dẫn theo bệnh (`disease_guides`) | Model đã có | Chưa có endpoint ghi |
| CRUD bệnh cây (triệu chứng, cách xử lý) | — | Chưa có gì. Hướng làm: bảng `disease_overrides` khoá theo `disease_key`, đọc đè lên `shared/data/tomato_diseases.json` ở `services/catalog.py` (xem mục ngay phía trên) — **không** biến `Disease` thành bảng chính vì phá vỡ bất biến thứ tự lớp = thứ tự output mô hình |
| CRUD người dùng | `GET/POST /users`, `GET/PATCH /users/{id}` đã có, chỉ quản trị mới gọi được | Đã đủ cho CRUD cơ bản — web admin chỉ cần dựng giao diện |
| Quản lý lô đất theo người dùng (biết lô nào đang bệnh gì) | `GET /plots` (admin xem được lô của mọi người dùng), `PlotWithStats` đã kèm `last_disease_name`/`last_severity` | Đã đủ — chỉ cần giao diện bảng/lọc |
| Xem lịch sử chẩn đoán toàn hệ thống | `GET /diagnoses` đã hỗ trợ lọc `user_id` (chỉ admin), `plot_id`, `disease_key`, `severity`, khoảng ngày, phân trang | Đã đủ — chỉ cần giao diện bảng |

Ba dòng đầu (thuốc/gán thuốc/video) là phần duy nhất thật sự cần viết **endpoint
mới** ở backend trước khi web admin đụng vào được — theo đúng pattern CRUD chuẩn
(`router.post`/`patch`/`delete` trong `app/api/v1/endpoints/`, tương tự
`plots.py` đã có), chỉ khác đối tượng thao tác là `Medicine`/`DiseaseMedicine`/
`DiseaseGuide` thay vì `Plot`.

---

## Nhận diện ngoại tuyến trên điện thoại (chốt 07/09/2026)

Mobile giờ chạy được suy luận **ngay trên máy** khi không gọi được backend —
nông dân ở vùng sóng yếu vẫn chẩn đoán được. Không phải hướng đi trong 76 issue
gốc, làm theo yêu cầu trực tiếp của Học.

**Chế độ hybrid:** `AnalyzingScreen` luôn thử gọi `POST /diagnoses` trước; bất
kỳ lỗi nào (mất mạng, timeout 8s, backend sập...) đều rơi thẳng sang
`OfflineInferenceService` mà không phân biệt loại lỗi — với nông dân, có kết
quả quan trọng hơn thông báo lỗi chi tiết.

**Vì sao ONNX chứ không phải chạy thẳng file `.pt`:** không có runtime PyTorch
nào chạy tốt trên Flutter/Android ở mức nhẹ cân; ONNX Runtime có plugin Flutter
ổn định (`flutter_onnxruntime`) và `torch.onnx.export` xuất thẳng từ checkpoint
hiện có mà không cần đổi gì ở `model/`.

**Vì sao vẫn giữ được vùng khoanh (XAI) mà không cần Grad-CAM thật:** Grad-CAM
cần lan truyền ngược (backward), ONNX Runtime trên điện thoại chỉ chạy forward.
Kiến trúc hiện tại (EfficientNet-B0: GAP rồi một lớp Linear duy nhất) cho phép
dùng **CAM cổ điển** (Zhou et al., 2016) — về công thức, với đúng kiểu kiến
trúc này, gần tương đương Grad-CAM — tính được bằng một phép nhân ma trận duy
nhất trong lúc forward. `model/src/export_onnx.py` cài luôn phép nhân đó thành
một `Conv2d` 1×1 (trọng số copy từ lớp `Linear` cuối) và xuất chung vào MỘT đồ
thị ONNX, output ra cả xác suất lẫn CAM thô của **mọi lớp** — điện thoại tự
chọn đúng lớp theo `argmax`, tự ReLU + chuẩn hoá min-max, không cần biết gì về
kiến trúc gốc.

**Nếu đổi kiến trúc mô hình** (khác GAP + một lớp `Linear` cuối, ví dụ thêm
tầng ẩn hay dùng attention pooling) thì `_ExportWrapper` trong `export_onnx.py`
không còn đúng nữa — phải viết lại cách tính CAM, không chỉ export lại.

**Cách sinh file mô hình cho mobile** (không tự động, làm lại thủ công mỗi khi
`model/checkpoints/leaf_disease_detection_model.pt` đổi):

```bash
docker exec plantdx-backend pip install onnx onnxruntime  # nếu image chưa có
docker exec -w /model plantdx-backend python -m src.export_onnx \
    --checkpoint /model/checkpoints/leaf_disease_detection_model.pt \
    --out /app/model_export_tmp
docker cp plantdx-backend:/app/model_export_tmp/tomato_leaf_v1.onnx mobile/assets/model/
docker cp plantdx-backend:/app/model_export_tmp/tomato_leaf_v1_meta.json mobile/assets/model/
cp shared/data/tomato_diseases.json mobile/assets/model/tomato_diseases.json
```

`mobile/assets/model/tomato_diseases.json` là **bản sao thủ công** của
`shared/data/tomato_diseases.json`, đóng gói cứng vào app để tra tên bệnh/mức
độ nặng/câu giải thích lúc không có mạng (không gọi `GET /diseases` được).
Cố tình không tự động đồng bộ hai file này — sửa nội dung bệnh (triệu chứng, xử
lý...) trong `shared/data/` mà quên chép lại thì bản offline sẽ hiển thị nội
dung cũ, tự nhắc bản thân kiểm tra khi sửa danh mục bệnh.

`mobile/lib/services/offline_inference_service.dart` cũng **chép tay lại**
logic của `backend/app/services/xai/explain.py` + `overlay.py` (ngưỡng cắt
heatmap 0.5, tỉ lệ vùng tối thiểu 0.5%, cách mô tả vị trí, câu giải thích) bằng
Dart thuần — không dùng chung code với backend vì khác ngôn ngữ. Sửa một bên
phải nhớ soát lại bên kia. Điểm khác duy nhất với backend: backend vẽ elip
bằng OpenCV `fitEllipse` trên đường viền thật của vùng heatmap; bản Dart tìm
vùng liên thông lớn nhất bằng BFS trên lưới 56×56 rồi vẽ elip theo khung bao —
đơn giản hơn nhưng đủ dùng vì CAM gốc chỉ có độ phân giải 7×7.

**Nâng cấp toolchain Android đi kèm bắt buộc** (không phải lựa chọn — thiếu là
build APK lỗi ngay): Gradle 8.3→8.14.1, AGP 8.2.1→8.11.1, Kotlin 2.1.0→2.2.20,
vì Flutter SDK trên máy (3.47.2, cài 26/08/2026) yêu cầu tối thiểu các mức đó.
`ndkVersion` ghim cứng về bản NDK 27.1 đã cài sẵn máy vì bản 28.2 Flutter đòi
tải không tải được (không phải NDK bắt buộc cho tính năng offline, chỉ là bản
mới nhất không tải nổi trên mạng lúc làm).

---

## Trạng thái hiện tại (20/08/2026 — model/backend/mobile cập nhật 07/09/2026)

| Phần | Tình trạng |
|---|---|
| Cấu trúc thư mục + README các cấp | Đã commit lên `main` |
| `shared/data/tomato_diseases.json` | Đã commit |
| `model/` code | **Đã huấn luyện xong** — `leaf_disease_detection_model.pt` (07/09/2026), xem `bao-cao-huan-luyen-mo-hinh.md` ở thư mục gốc cho số liệu đầy đủ. Từ 07/09/2026, **`model/checkpoints/` và `model/outputs/` đã theo Git** (quyết định của Bảo, đảo ngược quyết định ban đầu) — máy khác `pull` về là chạy được model thật ngay, không phải huấn luyện lại. Chỉ **dữ liệu PlantVillage `model/data/raw/` (18.160 ảnh / 10 lớp, ~275 MB) vẫn nằm ngoài Git** vì tải lại được từ Kaggle (nguồn ghi ở issue #11), không cần bắt repo gánh dung lượng đó |
| `model/research/` | Đã commit — danh mục 46 bài báo chia 8 nhóm + bản tổng hợp đối chiếu kết quả với các công bố. Xem mục "Phần việc của Bảo" bên dưới |
| `backend/` code | **Chạy mô hình thật** (không còn `DummyPredictor` mặc định) — 19/19 test pass, xem mục "Tích hợp mô hình thật" phía trên |
| `mobile/` (Flutter) | Giao diện đã dựng xong từ trước; **luồng chính đã nối API thật** ngày 07/09/2026: đăng nhập/đăng ký → danh mục → chụp/chọn ảnh → chẩn đoán thật kèm khoanh vùng → gợi ý xử lý (thuốc + video). Có màn **Đăng ký** tự phục vụ (xem mục "Tự đăng ký tài khoản") và **chẩn đoán ngoại tuyến** khi mất mạng (xem mục "Nhận diện ngoại tuyến trên điện thoại"). Màn Lịch sử vẫn còn dữ liệu mẫu — chưa nối, để sau |
| `web-admin/` (React) | Chưa bắt đầu — theo đề cương làm từ 01/10/2026, xem "Phạm vi tương lai: web admin" phía trên |

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

---

## Phần việc của Bảo (`model/`) — cập nhật 07/09/2026

Mục này để mở repo trên **máy khác** là biết ngay đang ở đâu và làm gì tiếp.

### Đã xong

**#14 — huấn luyện đầy đủ.** EfficientNet-B0, 25 epoch, 29,6 phút trên RTX 4060 Ti.

| | |
|---|---|
| Test accuracy | **99,60 %** · macro-F1 **99,55 %** · top-3 **100 %** |
| Sai | **11 / 2.719 ảnh**, không ca nào vô lý về bệnh học |
| Cặp nhầm nhiều nhất | Đốm lá vi khuẩn → Đốm mắt cua (4 ảnh) |
| Ca nguy hiểm nhất | 1 ảnh mốc sương muộn → **lá khoẻ** (chiều ngược lại không xảy ra) |
| Suy luận | 31–34 ms trên GPU. **Chưa đo trên CPU** |
| Chia tập | 70/15/15 theo từng lớp, seed 42, đã kiểm chứng không rò rỉ |

**#15 — đánh giá tập test.** Kết quả đầy đủ trong `bao-cao-huan-luyen-mo-hinh.md`
(thư mục gốc, đã commit).

**IN-01, IN-02 — đã nối mô hình thật vào backend và mobile** ngày 07/09/2026, kéo
sớm hơn lịch mốc 4. Chi tiết ở mục "Tích hợp mô hình thật" phía trên.

**Khảo sát tài liệu.** `model/research/` — 46 bài chia 8 nhóm, **7 bài đã đọc kỹ**,
kèm `03-tong-hop-doi-chieu.md` đối chiếu kết quả của nhóm với các công bố.

### ⚠️ Cảnh báo lệch lớp: đã kiểm chứng là KHÔNG xảy ra

Ghi chú cũ lo `mosaic_virus` (373 ảnh, ít hơn lớp đông nhất 14,4 lần) sẽ có recall
thấp. **Thực tế nó đạt precision = recall = F1 = 1,0000.**

Lý do: triệu chứng virus khảm khác biệt rõ về thị giác so với 9 lớp còn lại, nên ít
ảnh vẫn đủ học. **Lệch lớp là nguy cơ chứ không phải hậu quả tất yếu.**

→ **Không thêm class weight hay focal loss vào `train.py`.** Quyết định này có căn
cứ: bài E1 trong `model/research/` đo được cross-entropy thường (F1 0,9668) **thắng
cả** focal loss (0,9647) lẫn trọng số tần suất nghịch đảo (0,9621). Ai định "cải
tiến" chỗ này phải đọc E1 trước.

### Việc tiếp theo, xếp đúng thứ tự

| Thứ tự | Việc | Vì sao thứ tự này |
|---|---|---|
| **1** | **#17 — kiểm tra Grad-CAM có rơi đúng vết bệnh không** (5 ảnh × 10 lớp) | **Cổng kiểm soát của cả đề tài.** Nếu heatmap rơi vào nền thì toàn bộ phần XAI mất giá trị. Lý do là bài A2: có người huấn luyện **chỉ bằng 8 pixel nền** PlantVillage mà vẫn đạt 49 % (đoán mò 2,63 %) |
| 2 | **#49 — đo trên ảnh đồng ruộng.** Dùng bộ **H1** trong `model/research/` (731 ảnh thật, 6/7 lớp trùng, tải từ Mendeley) | Có số domain gap **mà không phải chờ đi chụp ảnh**. Nửa buổi là xong |
| 3 | **#16 — nâng Grad-CAM++** | Heatmap hiện thô vì tầng chập cuối B0 chỉ 7×7. Làm **sau** #17, vì nét hơn mà sai chỗ thì vô nghĩa |
| 4 | **#18 — đo tốc độ suy luận trên CPU** | Rủi ro số 2. Cần chốt máy demo là máy nào |
| 5 | **#19 — so ResNet18 / ResNet50 / B3** | `build.py` đã hỗ trợ sẵn, chỉ đổi `model.arch` trong config. 4 lượt × 25 phút |

### Ba cái bẫy đã biết trước

1. **`configs/default.yaml` đặt `image_size: 224` dùng chung cho mọi kiến trúc.**
   Chạy EfficientNet-B3 ở 224 là dưới độ phân giải thiết kế của nó. Nếu #19 chạy vậy
   rồi kết luận "B3 không hơn B0" là **kết luận không công bằng** — phải ghi rõ.
2. **Không đo lại bằng trí nhớ.** Bảng chia tập và smoke test nằm trong PR #78; kết
   quả huấn luyện nằm trong `bao-cao-huan-luyen-mo-hinh.md`. Trích từ đó.
3. **Checkpoint đã theo Git từ 07/09/2026.** File đang dùng là
   `model/checkpoints/leaf_disease_detection_model.pt` (backend trỏ tới qua
   `MODEL_CHECKPOINT` trong `backend/.env`), commit thẳng cùng `best.pt`. Trước
   đó hai file này nằm ngoài Git — đảo lại vì mục tiêu là máy khác `pull` về
   dùng được model ngay, không phải tự huấn luyện lại. `model/data/raw/` (ảnh
   gốc PlantVillage) vẫn ngoài Git — tải lại từ Kaggle theo issue #11.

### Quy ước về tài liệu trong `model/research/`

- Mỗi bài có **mã** (`A1`, `D4`, `E1`…). Nhắc mã là biết bài nào.
- Cột trạng thái: ✅ đã mở toàn văn · ⚠️ mới đọc tóm tắt · ⚪ mới thấy qua tìm kiếm.
  **Số liệu của bài ⚪ chỉ để biết bài đó có đáng đọc hay không, không được trích
  thẳng vào báo cáo.**
- Thư mục này **không phải bảng công việc**. Nguồn duy nhất vẫn là 76 issue GitHub.

---

## Ba rủi ro đã nhận diện

1. **Domain gap.** PlantVillage chụp lá đơn trên nền đồng nhất trong phòng; mô hình
   thường đạt >99% trên tập test nhưng rớt mạnh với ảnh chụp thật ngoài đồng. Cần
   thu thập 50–100 ảnh thật vào `model/data/field/` và báo cáo cả hai con số. Làm
   sớm trong tháng 9, đừng để tháng 10.

   Ba con số có nguồn trích dẫn được (chi tiết trong `model/research/`): chính tác
   giả PlantVillage báo cáo tụt từ 99,35% xuống **31,40%** trên ảnh điều kiện khác
   (bài A1); review 2024 đo trung bình **90,18% → 84,66%** (A3); và có người huấn
   luyện **chỉ bằng 8 pixel nền** vẫn đạt 49% (A2).

   **Không cần chờ đi chụp ảnh mới có số của mình:** bộ **H1** (731 ảnh đồng ruộng
   thật, 6/7 lớp trùng, tải từ Mendeley) chạy `evaluate.py --manifest` là ra.
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

Cần có: Git, Python 3.11 trở lên, Docker Desktop (cho PostgreSQL), và Flutter + Node
khi bắt đầu phần giao diện.

⚠️ Trên Windows, **đừng dùng bản Python cài từ Microsoft Store** (đường dẫn có
`WindowsApps`). Đó là stub, venv tạo từ nó hay hỏng mỗi khi Store tự cập nhật.
Cài bản tải thẳng từ python.org. Máy Bảo đang chạy 3.12.1 cho `model/` — torch
≥ 2.2 hỗ trợ 3.12 nên không cần ép về đúng 3.11.

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
