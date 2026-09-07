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

## Trạng thái hiện tại (20/08/2026 — model/backend/mobile cập nhật 07/09/2026)

| Phần | Tình trạng |
|---|---|
| Cấu trúc thư mục + README các cấp | Đã commit lên `main` |
| `shared/data/tomato_diseases.json` | Đã commit |
| `model/` code | **Đã huấn luyện xong** — `leaf_disease_detection_model.pt` (07/09/2026), xem `docs/bao-cao-huan-luyen-mo-hinh.md` cho số liệu đầy đủ |
| `backend/` code | **Chạy mô hình thật** (không còn `DummyPredictor` mặc định) — 19/19 test pass, xem mục "Tích hợp mô hình thật" phía trên |
| `mobile/` (Flutter) | Giao diện đã dựng xong từ trước; **luồng chính đã nối API thật** ngày 07/09/2026: đăng nhập → danh mục → chụp/chọn ảnh → chẩn đoán thật kèm khoanh vùng → gợi ý xử lý (thuốc + video). Màn Lịch sử vẫn còn dữ liệu mẫu — chưa nối, để sau |
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

Việc tiếp theo: chạy #14 — huấn luyện đầy đủ 25 epoch. Đo thật 20/08 với ảnh
JPEG (không phải tensor ngẫu nhiên) sau khi nâng `num_workers` lên 8 (PR #78):
một epoch ≈ 35 giây, trọn 25 epoch **≈ 22–25 phút** trên RTX 4060 Ti — Mốc 2
không cần lùi hạn, không cần Colab. Con số "≈ 16 phút" trong `model/README.md`
đo bằng tensor ngẫu nhiên, chưa tính khâu đọc ảnh — biết là lạc quan, chưa sửa.

Hai điều cần nhớ khi đọc kết quả huấn luyện sau này:

- Dữ liệu **lệch lớp 14,4 lần**: `yellow_leaf_curl_virus` 5.357 ảnh còn
  `mosaic_virus` chỉ 373 (tập test ~55 ảnh). Loss không đặt trọng số lớp, nên
  accuracy tổng có thể đẹp mà recall `mosaic_virus` thấp — soi kỹ ở #15.
  Đây là đặc tính của bộ dữ liệu gốc, không phải lỗi tải.
- Bảng chia tập train/val/test và số đo smoke test nằm trong PR #78 — báo cáo
  chương thực nghiệm trích từ đó, đừng đo lại bằng trí nhớ.

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
