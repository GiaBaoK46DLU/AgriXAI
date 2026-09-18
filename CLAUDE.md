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

#### ⚠️ Nhánh `khác` đã TÁCH khỏi phạm vi quả (chốt 10/09/2026)

Sơ đồ trên đặt cả bộ định tuyến trong phạm vi quả, tức phụ thuộc cổng go/no-go. **Phần
đó không còn đúng.** Sau khi thử app với mô hình thật, đo được rằng lỗi "chụp vật thể
bất kỳ vẫn báo bệnh lá" nghiêm trọng hơn tưởng: một mảnh **nền bìa carton không có
cọng lá nào** được kết luận là mốc sương muộn **84,5 %**, nên ngưỡng tin cậy đơn thuần
không chặn được.

Lỗi đó thuộc **luồng lá**, tồn tại ngay hôm nay, **không liên quan gì tới bệnh trên
quả** — nên không được để nó phụ thuộc một cổng có thể cho kết quả "bỏ phần quả".

Vì vậy tách thành **bộ phân loại 2 lớp** (lá cà chua / không phải lá cà chua) độc lập:

- Issue **#91** thu bộ ảnh âm, **#92** huấn luyện — cả hai thuộc **Mốc 2**, **không**
  mang nhãn `trang-thai:cho-cong-15-09`
- Không cần một tấm ảnh quả nào. Ảnh lá đã có sẵn 18.160 tấm
- **Khi chốt #64 (cổng go/no-go): #71 bị bỏ KHÔNG kéo theo #92.** Đây là chỗ dễ nhầm nhất
- Nếu qua cổng, mở 2 lớp thành 3 lớp chỉ là **thêm dữ liệu**, không phải làm lại — #71
  kế thừa từ #92

Số đo và lý lẽ đầy đủ: `docx/Plan_model.md` mục 1 và 5.

### Dữ liệu

Cần ~250–300 ảnh/lớp, tổng ~1.500 ảnh. Nguồn: Roboflow Universe và Kaggle (nhãn hay
sai, **phải kiểm tra bằng mắt**), cộng với tự chụp tại Đà Lạt. Ảnh tự chụp còn xử lý
luôn rủi ro domain gap vì đó là ảnh thật ngoài đồng ngay từ đầu.

> ⚠️ **Phần "tự chụp tại Đà Lạt" (#67) cần xem lại trước khi chốt cổng 15/09.**
> Ngày 10/09/2026 nhóm xác nhận **không liên hệ được nhà vườn** nên #20 (chụp ảnh lá
> ngoài đồng) đã hoãn vô thời hạn. Rào cản đó áp lên #67 nặng hơn: cà chua thường thì
> mua ở chợ chụp được, nhưng **quả bị thán thư hoặc thối đáy quả thì chợ không bán** —
> hai lớp đó gần như chỉ có ngoài vườn, mà chúng lại chính là hai lớp làm đề tài rộng
> ra (xem bảng 5 lớp quả ở trên).
>
> Đây là **đầu vào cho quyết định ở #64**, chưa phải kết luận: nếu chỉ dựa được vào
> Roboflow/Kaggle thì phần quả mất hẳn phần ảnh thật, và cùng lúc mất luôn lý lẽ "ảnh
> tự chụp xử lý luôn domain gap" ghi ở đoạn trên. Phải cân nhắc rõ khi chốt cổng, đừng
> để sót.
>
> ✅ **Đã tính vào quyết định #64 (17/09/2026).** Rào cản không được gỡ — vẫn chấp
> nhận `fruit_anthracnose`/`fruit_blossom_end_rot` dựng hoàn toàn từ Roboflow/Kaggle.
> Xem mục "Cổng go/no-go ngày 15/09/2026" bên dưới.

### ⚠️ Cổng go/no-go ngày 15/09/2026

Từ nay tới 15/09 **chỉ tập trung luồng lá** cho chạy thông end-to-end. Tới mốc đó nếu
luồng lá còn trục trặc thì **bỏ hẳn phần quả, không tiếc**. Phần quả là thứ để tăng
điểm, không phải thứ để cứu đề tài — bỏ đi thì đề tài vẫn đủ để bảo vệ.

Lịch dự kiến nếu qua cổng: 15/09–10/10 thu thập ảnh, 10/10–25/10 huấn luyện mô hình
quả + bộ định tuyến, 25/10–05/11 tích hợp và kiểm thử.

**Hai đầu vào mới cho quyết định này, phát sinh ngày 10/09/2026 — đọc trước khi chốt #64:**

1. **Không tự chụp được ảnh quả bệnh.** Xem cảnh báo ở mục *Dữ liệu* ngay trên. Rào cản
   này chưa có khi đặt ra cổng go/no-go, và nó ăn thẳng vào hai lớp đáng giá nhất của
   phần quả (`fruit_anthracnose`, `fruit_blossom_end_rot`).
2. **Bộ định tuyến không còn nằm trong phạm vi quả.** Nhánh "không phải lá cà chua" đã
   tách thành #91 → #92, thuộc Mốc 2. Nghĩa là **bỏ phần quả không còn kéo theo việc mất
   bộ chặn ảnh rác** — trước đây đó là một lý do để cố giữ phần quả, nay không phải nữa.
   Quyết định về phần quả vì vậy được xét độc lập, gọn hơn trước.

#### ✅ QUYẾT ĐỊNH (17/09/2026, trễ 2 ngày so với mốc — xem #64)

**GO có điều kiện: vẫn làm phần quả, nhưng dời thời điểm bắt đầu sang tuần 2 tháng
10/2026** (thay vì 15/09). Từ 17/09 tới 30/09 chỉ dọn gọn luồng lá. Soát đủ 5 tiêu
chí trong #64 thì 2/5 không đạt (#20 và "không issue Mốc 1/2 còn treo") và 1/5 chỉ
đạt một phần (#17) — theo đúng chữ của ticket #64 đó là NO-GO, nhưng nhóm ghi đè vì
lý do cổng được đặt ra ban đầu ("luồng lá trục trặc thì bỏ") không xảy ra: luồng lá
thực tế vượt kỳ vọng (model xong sớm, backend+mobile+web-admin đã chạy thật). #20
fail vì rào cản ngoại cảnh (không liên hệ được nhà vườn), không phải vì nhóm chậm.
Toàn bộ lý lẽ, đối chiếu 5 tiêu chí và rủi ro chấp nhận: xem comment quyết định trên
issue #64 (đã đóng).

Rủi ro chấp nhận quan trọng nhất: **`fruit_anthracnose` và `fruit_blossom_end_rot`
— hai lớp giá trị nhất của phần quả — gần như chắc chắn không có ảnh tự chụp**, vì
rào cản nhà vườn ở đầu vào 1 phía trên vẫn treo. Chấp nhận dựng hai lớp này hoàn
toàn từ Roboflow/Kaggle.

**Lịch mới (thay lịch gốc 15/09–10/10–25/10–05/11 ở trên):**

| Giai đoạn | Thời gian | Việc |
|---|---|---|
| Dọn luồng lá | 17/09–30/09 | Đóng issue treo Mốc 1/2, xong #91→#92, #93 nếu kịp |
| Thu thập + kiểm ảnh quả | ~12/10–26/10 | FR-01, FR-02, FR-03 |
| Huấn luyện mô hình quả + bộ định tuyến | 26/10–09/11 | FR-05…FR-08, FR-11 |
| Tích hợp + kiểm thử | 09/11–16/11 | FR-09 (sửa hợp đồng `Prediction`, báo Học trước), FR-10 |
| Đệm trước bảo vệ | 16/11–25/11 | ~1,5 tuần — hẹp hơn nhiều so với 3 tuần đệm của lịch gốc |

⚠️ **Đệm trước bảo vệ co từ 3 tuần xuống còn ~1,5 tuần** vì lịch bắt đầu trễ hơn một
tháng so với dự kiến ban đầu. Nếu tới **26/10** mà chưa thu thập xong ảnh quả, coi đó
là điểm chốt phụ để cân nhắc bỏ hẳn — đừng đợi tới sát 16/11 mới quyết.

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

Toàn bộ việc còn lại nằm trong **issue GitHub**, chia **6 mốc**. Đây là nguồn duy
nhất để biết còn phải làm gì — đừng lập bảng công việc song song ở chỗ khác.

> Cố ý **không ghi tổng số issue** ở đây. Bản đầu ghi "76 issue" và con số đó cũ
> ngay khi nhóm thêm issue mới (đã lệch thành 89 tính tới 10/09/2026), khiến người
> đọc tưởng danh sách đã đóng. Muốn biết số thật thì chạy
> `gh issue list --repo GiaBaoK46DLU/AgriXAI --state all --limit 300`.

| Mốc | Thời gian | Mục tiêu |
|---|---|---|
| 1 | 17/08 – 31/08/2026 | Nền tảng song song: backend chạy trên máy Học, khởi tạo 2 dự án giao diện, dựng môi trường mô hình |
| 2 | 01/09 – 30/09/2026 | Mô hình huấn luyện xong, có Grad-CAM, chặn được ảnh không phải lá cà chua |
| 3 | 01/09 – 15/10/2026 | Giao diện dựng trên `DummyPredictor` — **chạy song song mốc 2** |
| 4 | 01/10 – 31/10/2026 | Hợp nhất mô hình thật, tinh chỉnh XAI, đo domain gap trên bộ ảnh **công khai** (H2 — PlantDoc) |
| 5 | 15/10 – 25/11/2026 | Báo cáo, slide, tập demo |
| 6 | 17/09 – 25/11/2026 | Bệnh trên quả — **GO có điều kiện, dời lịch (chốt #64 ngày 17/09)**: dọn luồng lá tới 30/09, phần quả bắt đầu thật ~12/10. Xem mục "Cổng go/no-go ngày 15/09/2026" |

⚠️ **Mốc 2 và Mốc 4 đã sửa mục tiêu ngày 10/09/2026.** Trước đó Mốc 2 ghi "bắt đầu
chụp ảnh thực địa" và Mốc 4 ghi "đo trên ảnh thực địa" — cả hai đều giả định nhóm tự
chụp được ảnh ngoài đồng, mà việc đó **đã hoãn vô thời hạn** (xem rủi ro số 1). Mốc 4
vẫn đo được domain gap, chỉ là bằng bộ **công khai** chứ không bằng ảnh tự chụp. Mốc 2
nhận việc mới thay vào: chặn ảnh không phải lá cà chua (#90 → #91 → #92).

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
  đó — đã backfill email `*@agrixai.vn` cho cả ba để nhất quán.

  ⚠️ **Đừng dùng domain kiểu `.local`/`.test`/`.invalid`/`.example`** cho dữ
  liệu mẫu — đây là bài học thật đã gặp: seed ban đầu dùng `@agrixai.local`,
  `email-validator` (chạy sau lưng `pydantic.EmailStr`) từ chối thẳng vì
  `.local` là tên miền dành riêng theo RFC 6762 (mDNS), làm sập
  `POST /auth/login` cho cả ba tài khoản demo với lỗi
  `ResponseValidationError` — phát hiện được nhờ test thật trên máy, bộ test
  tự động không bắt được vì `conftest.py` seed không gán email. Đã sửa hai lớp:
  đổi seed sang `.vn`, VÀ đổi `UserOut.email` từ `EmailStr` sang `str` thường
  (input — `RegisterRequest`/`UserCreate`/`UserUpdate` — vẫn giữ `EmailStr` để
  chặn email sai cú pháp lúc nhận). Lý do đổi cả hai: `EmailStr` ở output
  nghĩa là validate lại dữ liệu **đã nằm trong CSDL** mỗi lần trả response —
  một bản ghi cũ/nhập tay lỡ sai sẽ sập mọi endpoint trả `UserOut`, không chỉ
  chỗ tạo ra nó. Input vẫn cần chặn chặt; output thì dữ liệu coi như đã tin
  cậy, chỉ cần trả nguyên văn.
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

## Web admin: kiến trúc và tiến độ (chốt 16/09/2026 — thay thế kế hoạch Vite)

`web-admin/` trước đây chỉ là khung Vite trống, dựng theo 4 trang mô tả trong
`README.md` cũ (Tổng quan · Lô đất & nông dân · Lịch sử · Tài khoản). Ngày
16/09/2026 đổi hẳn hướng, theo yêu cầu trực tiếp của Học: viết lại bằng
**Next.js (App Router) + TypeScript + Tailwind CSS v4**, dự định deploy
**Vercel**, và mở rộng thành **8 trang** (thêm Danh mục bệnh, Thuốc gợi ý,
Video hướng dẫn tách riêng, và **Diễn đàn** — trang kiểm duyệt mới, chưa từng
có trong bất kỳ kế hoạch nào trước đó).

⚠️ **Hệ quả: các issue `WA-01`…`WA-10` trên GitHub (mốc 3, nhãn
`mang:web-admin`) mô tả kế hoạch Vite/4-trang cũ, nay lỗi thời.**

✅ **Đã rà và đóng (18/09/2026).** Đối chiếu từng tiêu chí gốc của
`WA-01`…`WA-10` với bản build Next.js thật, không chỉ đóng vì "đã đổi kiến
trúc". `WA-01`/`WA-02` (khởi tạo Vite, lớp gọi API + localStorage) đóng vì
**siêu việt/thay thế hoàn toàn** — Next.js không cần khởi tạo Vite, và BFF +
cookie httpOnly (`lib/api.ts`/`lib/session.ts`) làm đúng việc lớp gọi API
localStorage định làm, an toàn hơn. `WA-03`/`WA-04`/`WA-05`/`WA-10` đóng vì
**đã đạt đủ tiêu chí** khi soát lại (đăng nhập chặn theo `role`, layout +
sidebar, 4 ô số liệu, trang người dùng có khoá tự-khoá-chính-mình chặn ở
backend). Bốn ticket còn lại có **lỗ hổng thật** khi soát kỹ, đã vá trước khi
đóng — xem nhánh `hoc/task-31-web-admin-close-out-old-tickets`:

- `WA-04` (#31): sidebar chưa thu gọn được ở màn hẹp — thêm nút thu/mở.
- `WA-06` (#33): biểu đồ xu hướng vẽ thẳng `timeseries` thưa của backend vào
  recharts — đúng lỗi ticket cảnh báo trước ("ngày trống bị nén lại, biểu đồ
  sai lệch"). Thêm `fillTimeseriesGaps()`.
- `WA-07` (#34): dải cảnh báo mô hình giả chỉ hiện ở trang tổng quan, ticket
  yêu cầu **mọi trang có số liệu**. Chuyển vào `AdminLayout`, dùng `GET
  /health` (công khai, rẻ) thay vì gọi `/stats/dashboard` trên từng trang.
- `WA-08`/`WA-09` (#35/#36): thiếu lọc theo khu vực (lô đất) và lọc theo lô
  đất + khoảng ngày (lịch sử chẩn đoán) — cả hai backend đã hỗ trợ sẵn tham
  số, chỉ thiếu UI. Thêm cả hai, cùng tô màu nền cho dòng mức "Nặng".

### Vì sao Next.js trên Vercel mà không phá vỡ kiến trúc 3 phần tách biệt

Dự án vẫn giữ nguyên `backend/` (FastAPI), `web-admin/`, `mobile/` là ba phần
triển khai độc lập — Next.js chỉ đóng vai trò **BFF (backend-for-frontend)**
cho riêng web admin, không thay thế `backend/`:

- Mọi lệnh gọi `backend/` chạy ở **phía server** của Next.js (Server Component,
  Server Action, Route Handler) — trình duyệt không bao giờ gọi thẳng backend
  và không bao giờ thấy token. Xem `web-admin/lib/session.ts`, `lib/api.ts`.
- Token JWT do backend cấp được cất trong cookie **httpOnly** (`lib/session.ts`),
  khác cách mobile lưu token (đọc `AppConfig`/local storage phía app) — web
  chạy trong trình duyệt nên localStorage lộ ra cho mọi đoạn JS kể cả từ lỗ
  hổng XSS, cookie httpOnly thì không.
- `BACKEND_URL` trong `web-admin/.env.local` **cố ý không có tiền tố
  `NEXT_PUBLIC_`** — biến này chỉ cần ở phía server. Ảnh chẩn đoán vẫn hiển thị
  được vì `/storage/...` là static file công khai, không cần token.
- CSDL: **đã đẩy một bản lên Supabase (17/09/2026)** để chuẩn bị sẵn cho lúc
  deploy — xem mục "Supabase: đẩy DB chuẩn bị deploy" ngay dưới đây. Luồng chạy
  **hiện tại vẫn dùng PostgreSQL local qua `docker-compose.yml`**, chưa đổi gì
  ở `backend/`. `web-admin/` chỉ gọi qua API nên không phải đổi gì khi nào thật
  sự cutover.

### Supabase: đẩy DB chuẩn bị deploy, chưa đổi luồng chạy (chốt 17/09/2026)

Project Supabase đã tồn tại sẵn (`project_ref=zdksrzpldizpcmxzqyph`, cấu hình
trong `.mcp.json` — file này **không nằm trong Git**, chứa tham chiếu riêng của
máy). Ngày 17/09/2026 đẩy **toàn bộ schema (11 bảng, qua `pg_dump
--schema-only`) và toàn bộ dữ liệu hiện có** (seed + dữ liệu thử nghiệm: 3
user, 4 lô đất, 18 chẩn đoán, 15 bài diễn đàn...) từ container `plantdx-db`
lên project đó, đã đối chiếu số dòng từng bảng khớp 100% giữa hai bên.

**Đây chỉ là chuẩn bị trước, KHÔNG phải cutover:**

- `backend/.env` / `docker-compose.yml` **chưa đổi** — `DATABASE_URL` vẫn trỏ
  `db:5432` (container local). Muốn chạy thật trên Supabase thì phải tự đổi
  `DATABASE_URL` sang connection string của Supabase, việc đó chưa làm.
- Bản trên Supabase là **ảnh chụp một lần** (point-in-time), **không tự đồng
  bộ**. Local DB đổi tiếp (thêm chẩn đoán, bài diễn đàn mới...) sẽ không tự
  cập nhật lên Supabase — cần đẩy lại thủ công (lặp lại `pg_dump` rồi
  `execute_sql`/`apply_migration` qua Supabase MCP) khi nào cần bản mới hơn.
- **File ảnh KHÔNG được đẩy theo.** `diagnoses.image_path`/`overlay_path` chỉ
  là đường dẫn text (`uploads/...`, `overlays/...`); ảnh thật nằm trong
  `backend/storage/` trên máy local, không nằm trong Postgres nên `pg_dump`
  không thấy. Khi nào cutover thật, ảnh phải đồng bộ riêng (Supabase Storage
  hoặc cách khác) — không tự suy ra được từ việc DB đã lên Supabase.

⚠️ **RLS (Row Level Security) chưa bật trên bất kỳ bảng nào trong 11 bảng** —
`get_advisors` báo lỗi `rls_disabled_in_public` cho cả 11. Chấp nhận được ở
trạng thái hiện tại vì chưa có gì đọc project Supabase này qua PostgREST/anon
key, nó chỉ đứng đó chờ. **Nhưng đây là việc bắt buộc phải làm trước khi thật
sự chuyển `backend/` sang trỏ vào Supabase** — bảng `users` chứa
`hashed_password`, không bật RLS nghĩa là bất kỳ ai có anon key đều đọc được
qua PostgREST. Vì `backend/` (FastAPI + SQLAlchemy) luôn nói chuyện thẳng với
Postgres bằng vai trò có toàn quyền (giống cách nó nói chuyện với container
local hiện nay), hướng đúng lúc cutover là dùng connection string trực tiếp
(giữ nguyên cách SQLAlchemy đang làm) hoặc `service_role` key — **không** phải
`anon` key — và bật RLS chặn truy cập qua PostgREST công khai.

### Phong cách thiết kế: theo đúng bảng màu/font mobile, đổi layout cho web

Bản thiết kế tham khảo ban đầu (`AgriXAI Admin - Web v1.dc.html`, do Học tải
về từ claude.ai/design) dùng đúng bảng màu chốt của mobile
(`mobile/lib/core/app_colors.dart`, xanh `#2E6F40`/`#54A96A`, vàng cảnh báo
`#F2A104`, Open Sans) nhưng đổi bố cục sang sidebar + bảng dữ liệu — **không**
phải glassmorphism cuộn dọc như mobile. Bản build thật giữ đúng tinh thần đó:
`web-admin/app/globals.css` định nghĩa lại các token màu này bằng Tailwind v4
`@theme`, kính mờ (`backdrop-blur`) chỉ dùng ở màn đăng nhập và banner tổng
quan — nơi mobile cũng dùng kính mờ — còn bảng dữ liệu là nền trắng phẳng, mật
độ cao, đúng yêu cầu "chuyên nghiệp hơn app mobile" trong
`prompt-cli-forum-feature.md`/`PROMPT_WEB_ADMIN.md` (thư mục thiết kế do Học
cung cấp, không nằm trong Git).

### Tám module đã dựng

| Trang | Route | Ghi chú |
|---|---|---|
| Tổng quan | `/admin` | 4 ô số liệu + biểu đồ đường (SVG tay, không dùng thư viện chart) + phân bố theo bệnh/mức độ, dải cảnh báo khi `using_real_model=false` |
| Người dùng | `/admin/users` | CRUD đầy đủ qua `GET/POST/PATCH /users` đã có sẵn |
| Lô đất | `/admin/plots` | Chỉ đọc + xem chi tiết lịch sử — **không** có form sửa/xoá lô đất (lô đất là dữ liệu của nông dân, admin chỉ xem, đúng theo bản thiết kế gốc) |
| Lịch sử chẩn đoán | `/admin/diagnoses` | Lọc theo nông dân/bệnh/mức độ, phân trang, modal chi tiết kèm ảnh gốc + ảnh khoanh vùng Grad-CAM |
| Danh mục bệnh | `/admin/diseases` | Chỉ đọc, có banner nhắc thứ tự lớp gắn với output mô hình — **không** có CRUD (đúng quyết định "không biến `Disease` thành bảng CSDL" đã chốt trước đó) |
| Thuốc gợi ý | `/admin/medicines` | CRUD `Medicine` + gán/gỡ theo bệnh — **endpoint mới**, xem mục dưới |
| Video hướng dẫn | `/admin/guides` | Đặt/đổi/gỡ video YouTube theo bệnh — **endpoint mới** |
| Diễn đàn | `/admin/forum` | **Module mới, không có trong bất kỳ bản thiết kế nào trước đó** — kiểm duyệt bài viết/bình luận (lọc theo bệnh/loại phản hồi, xem chi tiết, xoá) |

### Backend bổ sung để web admin có endpoint ghi thật (không còn "CHƯA LÀM")

Bảng "việc còn thiếu" ở bản trước của mục này nay đã làm xong:

- **`backend/app/api/v1/endpoints/medicines.py`** (mới, đăng ký prefix
  `/medicines`) — CRUD `Medicine`, gán/gỡ `DiseaseMedicine` theo
  `disease_key` (validate khoá tồn tại trong danh mục JSON trước khi gán),
  và `PUT`/`DELETE` `DiseaseGuide` theo từng bệnh (tối đa một video/bệnh, đặt
  lại là ghi đè). Toàn bộ chỉ `AdminUser` gọi được.
- **`backend/app/api/v1/endpoints/forum.py`** — thêm `DELETE /forum/posts/{id}`
  và `DELETE /forum/comments/{id}`, admin-only. Đây chính là phần
  "chưa cần kiểm duyệt — để dành cho lúc làm web admin" mà
  `prompt-cli-forum-feature.md` mục 3 đã nói trước — nay đến lúc làm.
- Test tương ứng: `backend/tests/test_medicines.py` (mới),
  `backend/tests/test_forum.py` (bổ sung 3 test kiểm duyệt).

⚠️ **Phát hiện khi chạy lại bộ test đầy đủ:** `test_like_post_increments_counter`
thất bại từ trước khi có thay đổi này (endpoint like đã đổi sang toggle
like/unlike qua bảng `forum_post_likes` ở một thời điểm nào đó, nhưng test cũ
vẫn giả định đếm dồn 1→2). Không liên quan gì tới web admin, chưa sửa — để lại
cho ai đụng tới `like_post` tiếp theo.

### Đã kiểm thử thật, không chỉ build qua

`npm run build` qua strict TypeScript sạch cho cả 10 route. Ngoài ra đã chạy
backend thật (SQLite tạm + `python -m app.seed --diagnoses`) song song
`npm run dev`, đăng nhập bằng token thật, và xác nhận cả 8 trang + modal chi
tiết (chẩn đoán/lô đất/bài diễn đàn) + panel theo bệnh (gán thuốc/video) render
đúng dữ liệu thật, không lỗi. Chưa test được luồng bấm nút thật qua trình duyệt
(Chrome MCP không kết nối được trong phiên chạy nền) — các Server Action tạo/
sửa/xoá mới chỉ được xác nhận qua build type-check + test backend, chưa qua
click thật.

### Vòng sửa lỗi + mở rộng thứ hai (16/09/2026, cùng ngày)

Sau khi xem bản dựng đầu, Học yêu cầu một loạt sửa/thêm trong cùng phiên:

- **Logo**: thay ô màu giữ chỗ (sidebar, màn đăng nhập, favicon) bằng đúng
  glyph "lá hai tông" của app mobile (`AgriIcons.leaf` trong
  `mobile/lib/widgets/agri_icons.dart`) — chép path SVG nguyên văn vào
  `web-admin/components/Logo.tsx`, không vẽ icon mới.
- **Tương phản màu**: nhiều chip trạng thái gần như vô hình hoặc chữ chìm vào
  nền. Đo thử bằng công thức WCAG thì `moderate`/`neutral` tone cũ trong
  `components/Tag.tsx` chỉ đạt ~2.9:1 (dưới cả ngưỡng AA-large 3:1) — nền
  pastel quá nhạt so với nền trắng/canvas xung quanh. Đổi `severe`/`moderate`
  sang nền đặc màu + chữ trắng (~4.3–4.9:1, giống cách mobile tô nhãn "Nặng"),
  `neutral` đổi nền xám nhẹ có độ tương phản thật (`bg-ink/10`) thay vì gần
  trùng màu trang. Đồng thời rà toàn bộ `text-ink/45` và `text-ink/50` (đo
  được ~2.7–3.1:1, đều fail AA) nâng lên tối thiểu `/60`, và `hover:bg-canvas`
  (gần như không thấy hover trên nền trắng) đổi sang `hover:bg-ink/8`.
- **Tài khoản quản trị**: thêm trang tự phục vụ "Tài khoản của tôi"
  (`/admin/account`) — sửa hồ sơ qua `PATCH /auth/me` (chỉ `full_name`/`phone`,
  đúng như backend đã giới hạn từ trước — **không** thêm khả năng đổi email
  qua đường này) và đổi mật khẩu qua `POST /auth/change-password`. Trước đó
  admin không có cách nào tự sửa hồ sơ/đổi mật khẩu của chính mình qua web.
- **Dashboard**: bản đầu chỉ có một đường SVG tay không nhãn trục — Học phản
  hồi "không hiểu gì cả". Viết lại bằng `recharts` (`components/charts/`):
  biểu đồ vùng có trục ngày/tooltip, biểu đồ cột ngang cho phân bố bệnh,
  biểu đồ tròn (donut) cho mức độ nặng, cộng thêm khối "Hoạt động gần đây"
  (5 chẩn đoán + 5 bài diễn đàn mới nhất, bấm vào mở thẳng modal chi tiết) —
  biến trang tổng quan từ một biểu đồ trừu tượng thành thứ đọc được ngay.
- **Diễn đàn — admin bình luận được**: `POST /forum/posts/{id}/comments` vốn
  đã mở cho mọi `CurrentUser` nên không cần sửa quyền ở backend, chỉ thiếu ô
  nhập ở web admin (`PostDetailModal.tsx` thêm form). Thêm `user_role` vào
  `ForumCommentOut`/`ForumPostOut` (schema, không phải khoá ngoại — đọc từ
  `comment.user.role`/`post.user.role` đã join sẵn) để tên quản trị tô đậm +
  nhãn "Quản trị" nổi bật giữa các bình luận của nông dân.
- **Bug: liên kết "Xem lần chẩn đoán liên kết" từ bài diễn đàn**. Modal chi
  tiết chẩn đoán trước đó tìm bản ghi bằng cách `.find()` trong danh sách ĐÃ
  PHÂN TRANG/LỌC của trang `/admin/diagnoses` — mở từ diễn đàn tới một chẩn
  đoán không nằm trong 20 bản ghi trang 1 thì modal không hiện gì, không báo
  lỗi. Sửa: modal tự `GET /diagnoses/{id}` và `GET /users/{user_id}` trực
  tiếp theo id, không phụ thuộc danh sách gọi nó vào. Đã kiểm bằng cách gọi
  API tạo một chẩn đoán + bài viết đính kèm, lọc nó ra khỏi danh sách bằng
  `severity=severe` (bản ghi thật là `mild`), xác nhận modal vẫn mở đúng.
- **docker-compose.yml**: service `web-admin` đổi cổng 5173→3000, lệnh
  `npm run dev -- -H 0.0.0.0`, thêm `BACKEND_URL=http://backend:8000` (gọi
  qua tên service trong mạng compose). Thêm volume riêng cho
  `node_modules`/`.next` để không bị bind mount từ host (thường là Windows)
  đè lên bản cài cho Linux trong container. `db`/`adminer` giữ nguyên —
  **không đổi ORM sang Prisma** dù có đề xuất ban đầu: Supabase chỉ là
  PostgreSQL có host sẵn, SQLAlchemy hiện tại đã dùng được ngay bằng cách đổi
  `DATABASE_URL`, không cần viết lại tầng dữ liệu (quyết định của Học sau khi
  cân nhắc rủi ro, xem lịch sử trao đổi nếu cần chi tiết).
- ⚠️ **Docker chưa kiểm thử chạy thật được trong phiên này** — Docker Desktop
  trên máy chạy phiên nền không lên engine kịp (WSL `docker-desktop` đã
  `Running` nhưng pipe engine không mở, có thể cần thao tác tay như một hộp
  thoại đang chờ). `docker-compose.yml` đã kiểm cú pháp bằng
  `docker compose config` (parse thành công, không cần daemon) nhưng **chưa**
  chạy `docker compose up --build` thật để xác nhận cả bốn service lên đúng.
  Việc còn lại: ai đó chạy `docker compose up --build` và báo lại nếu có gì
  sai — nhiều khả năng nhất là quên biến `MODEL_CHECKPOINT` cần file thật
  trong `model/checkpoints/` như phần "Tích hợp mô hình thật" đã nói.

---

## Nhận diện ngoại tuyến trên điện thoại (chốt 07/09/2026)

Mobile giờ chạy được suy luận **ngay trên máy** khi không gọi được backend —
nông dân ở vùng sóng yếu vẫn chẩn đoán được. Không phải hướng đi trong tập issue
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

## Dọn 9 issue mobile cũ còn sót (chốt 18/09/2026)

9 issue `#22, #24, #25, #26, #27, #28, #29, #81, #85` đã đóng từ trước (phần
lớn tiêu chí đạt) nhưng mỗi issue còn sót vài mục nhỏ — dọn gộp một lượt thay
vì để treo. Chi tiết đáng nhớ, không suy ra được từ diff:

- **Refresh token (từ #22 MB-03) — quyết định làm backend thật, không chỉ vá
  phía mobile.** Trước đó hệ thống chỉ có một access token JWT sống 7 ngày
  (`ACCESS_TOKEN_EXPIRE_MINUTES = 60*24*7`), không hề có khái niệm refresh
  token nào. Hỏi trực tiếp Học và chọn hướng làm đúng nghĩa: access token hạ
  xuống **30 phút**, thêm bảng `refresh_tokens` (băm SHA-256, không lưu token
  thô), `POST /auth/refresh` (xoay vòng — token cũ bị thu hồi ngay sau khi
  dùng, chỉ dùng được một lần) và `POST /auth/logout` (thu hồi phía server).
  `LoginResponse`/`RegisterRequest` nay trả thêm `refresh_token`.
  - Mobile (`ApiClient`) tự bắt 401 rồi làm mới token ở nền, **chỉ khi response
    có header `WWW-Authenticate`** — header này CHỈ `get_current_user`
    (`backend/app/api/deps.py`) gắn. Đây là cách phân biệt "401 vì hết phiên"
    với "401 nghiệp vụ" (ví dụ sai mật khẩu hiện tại ở
    `POST /auth/change-password`) mà không cần đổi mã lỗi phía backend — nếu
    không phân biệt, đổi mật khẩu sai sẽ bị hiểu nhầm thành hết phiên và tự
    gọi refresh.
  - Refresh/session hết hạn thật sự (refresh token cũng không còn dùng được)
    thì `ApiClient.onSessionExpired` được gọi — `main.dart` gán callback này
    để dọn `session.currentUser` và điều hướng thẳng về `LoginScreen` qua một
    `GlobalKey<NavigatorState>` toàn cục (`appNavigatorKey`), vì lúc đó không
    có `BuildContext` nào để dùng `Navigator.of(context)`.
  - `backend/.env`/`backend/.env.example` đã sửa `ACCESS_TOKEN_EXPIRE_MINUTES`
    xuống `30` và thêm `REFRESH_TOKEN_EXPIRE_DAYS=30` — **máy khác đã có
    `.env` từ trước phải tự sửa tay**, giá trị cũ (`10080`) không tự mất vì
    `.env` không nằm trong Git (giống bài học ở mục "Tự đăng ký tài khoản").
    Bảng `refresh_tokens` đã tạo trên DB dev của Học bằng
    `docker exec plantdx-backend python -m app.db.init_db` (an toàn, chỉ tạo
    bảng thiếu, không đụng bảng có sẵn) — máy khác `pull` code mới rồi dựng
    container mới hoàn toàn thì `create_all` tự lo, chỉ DB **đã tồn tại** từ
    trước mới cần tự chạy lệnh này một lần, cùng kiểu với cột `email` trước đó.
- **Nén ảnh (#25):** vòng lặp giảm `quality`/kích thước tối đa 5 lần, mỗi lần
  nén lại từ **file gốc** (không nén chồng lên ảnh đã nén — tránh mất chất
  lượng oan do nén JPEG nhiều lớp).
- **Quyền camera bị từ chối (#24):** thêm gói `permission_handler` chỉ để gọi
  `openAppSettings()` — không dùng để tự xin quyền (`image_picker` đã tự lo
  phần đó), chỉ dùng khi đã bị từ chối và cần mở thẳng màn Cài đặt hệ thống.
- **Danh mục bệnh (#81):** xác nhận **không có** đường nào vào được
  `CatalogScreen` khi chưa đăng nhập — `main.dart` đã bắt đăng nhập cho toàn
  bộ app từ trước, comment cũ trong `catalog_screen.dart` ghi ngược lại
  ("tra cứu được khi chưa đăng nhập") là hồi quy, đã xoá.
- **Không làm:** phần "chưa rõ các màn khác có phân biệt được lỗi mất mạng
  hay không" (#29) được giải quyết ở tầng `ApiClient` (mọi `SocketException`/
  `TimeoutException` gộp thành `NetworkException` dùng chung), nhưng KHÔNG đi
  sửa lại từng dòng thông báo lỗi hiện có ở các màn khác ngoài
  login/register — thông báo cũ ("kiểm tra kết nối mạng rồi thử lại") vẫn
  đúng ngữ cảnh vì `ApiException` (backend trả lỗi) đã luôn tách riêng từ
  trước, không lẫn với lỗi mạng.

### Video YouTube ở màn Gợi ý xử lý — bỏ WebView rồi phục hồi bằng gói khác (18/09/2026)

Hai quyết định trái ngược nhau trong cùng một ngày, đọc theo đúng thứ tự xảy ra:

**Vòng 1 — bỏ hẳn WebView.** Kiểm thử thật trên máy ảo Android phát hiện
`youtube_player_flutter` (dùng từ trước) không ổn định: phải nhấn hai lần mới
dừng được video (WebView có lớp bắt cử chỉ riêng chồng lên nút play/pause của
app), có lúc vòng xoay tải mãi không phát được gì, và **một lần crash gốc thật
sự** bắt được qua `adb logcat` — `Fatal signal 5 (SIGTRAP)` trong
`libwebviewchromium.so`, thread `NetworkService`. Phản ứng đầu tiên: bỏ hẳn
WebView, chỉ hiện thumbnail tĩnh + luôn mở video bằng trình duyệt ngoài.

**Vòng 2 — phục hồi phát tại chỗ, theo yêu cầu trực tiếp của Học** ("tôi muốn
video được phát trong ô của app luôn chứ không phải nhảy qua youtube"). Không
quay lại `youtube_player_flutter` — đổi sang **`youtube_player_iframe`**, khác
biệt quan trọng: gói này dùng `webview_flutter` (chính chủ Flutter team) và để
nguyên khung điều khiển play/pause/seek của chính YouTube chạy bên trong
WebView, không vẽ thêm một lớp nút bấm Flutter đè lên trên. `youtube_player_flutter`
(gói cũ) vẽ nút play/pause riêng bằng Flutter đè lên WebView, tạo ra hai lớp
bắt cử chỉ tranh nhau — đó chính là gốc rễ lỗi "nhấn hai lần mới dừng được".
Đổi gói nên sửa được đúng hai trong ba lỗi ban đầu (double-tap, vòng xoay tải
mãi — cả hai đều là lỗi cách `youtube_player_flutter` tự vẽ chồng UI, không
phải lỗi WebView hệ điều hành).

⚠️ **Rủi ro KHÔNG sửa được bằng cách đổi gói:** bản chất crash `SIGTRAP` là lỗi
ở System WebView của máy/máy ảo (backtrace nằm hoàn toàn trong
`libwebviewchromium.so`, không chạm gì tới code Dart của app hay của bất kỳ
gói Flutter nào) — mọi gói nhúng video qua WebView, kể cả `youtube_player_iframe`,
đều render qua đúng một System WebView đó nên đều mang chung rủi ro này ở mức
độ nào đó. Không có cách nào từ phía code Flutter đảm bảo tuyệt đối World
WebView của một máy cụ thể không crash. Giảm thiểu đã áp dụng:

- Chỉ dựng `YoutubePlayerController`/nạp WebView khi người dùng thật sự bấm
  play (trước đó chỉ hiện ảnh thumbnail tĩnh `Image.network`) — giảm số lần
  WebView phải khởi tạo.
- Luôn kèm nút phụ "Mở trên YouTube" cạnh khung phát, kể cả khi đang phát tại
  chỗ — lối thoát thủ công nếu WebView của máy nào đó vẫn không ổn định.
- Đã kiểm thử phát/dừng/tua trực tiếp trên máy ảo sau khi đổi gói, theo dõi
  song song `adb logcat` — không tái hiện crash, nhưng đây **không phải bằng
  chứng loại trừ vĩnh viễn** vì bản chất là lỗi tuỳ máy/tuỳ phiên bản WebView.

Nếu vấn đề tái diễn trên máy demo thật, phương án dự phòng đã biết hoạt động
(vòng 1) là bỏ WebView, quay về thumbnail + mở ngoài — giữ nguyên logic tách
ID video (`_youtubeVideoId`) nên chuyển đổi qua lại giữa hai cách không tốn
nhiều công.

### Thứ tự các phần ở màn Gợi ý xử lý (chốt 18/09/2026, theo yêu cầu của Học)

Đổi từ: tên bệnh+tag → Triệu chứng → Điều kiện thuận lợi → cảnh báo (nếu có)
→ Video → Cần làm ngay → ...

Sang: tên bệnh+tag → **cảnh báo "bệnh lan nhanh"** (chỉ hiện khi mức độ Nặng)
→ Video hướng dẫn xử lý → Triệu chứng → Điều kiện thuận lợi cho bệnh → Cần
làm ngay → Thuốc gợi ý → Phòng ngừa lâu dài → tham khảo/khuyến cáo → nút hành
động.

Thẻ cảnh báo cũng đổi hẳn kiểu dáng: từ nền vàng cam nhạt 16% opacity (dễ
chìm lẫn vào các thẻ thông tin trung tính xung quanh) sang nền vàng cam ĐẶC
(`AgriColors.accent`) kèm viền đậm, bóng đổ, và dòng tiêu đề in hoa "CẢNH BÁO:
BỆNH CÓ THỂ LAN NHANH" — yêu cầu trực tiếp là cảnh báo này "cần được thể hiện
rõ hơn, màu sắc nhấn mạnh nội dung".

---

## Trạng thái hiện tại (20/08/2026 — model/backend/mobile cập nhật 07/09/2026)

| Phần | Tình trạng |
|---|---|
| Cấu trúc thư mục + README các cấp | Đã commit lên `main` |
| `shared/data/tomato_diseases.json` | Đã commit |
| `model/` code | **Đã huấn luyện xong** — `leaf_disease_detection_model.pt` (07/09/2026), xem `docx/bao-cao-huan-luyen-mo-hinh.md` cho số liệu đầy đủ. Từ 07/09/2026, **`model/checkpoints/` và `model/outputs/` đã theo Git** (quyết định của Bảo, đảo ngược quyết định ban đầu) — máy khác `pull` về là chạy được model thật ngay, không phải huấn luyện lại. Chỉ **dữ liệu PlantVillage `model/data/raw/` (18.160 ảnh / 10 lớp, ~275 MB) vẫn nằm ngoài Git** vì tải lại được từ Kaggle (nguồn ghi ở issue #11), không cần bắt repo gánh dung lượng đó. **Đã đo xong hai việc đánh giá lớn (15/09/2026):** #49 domain gap (**30,81 %** trên ảnh thật) và #17 kiểm Grad-CAM (**đủ tin trên PlantVillage, chưa đủ trên ảnh thật**) — xem hai báo cáo trong `docx/`. **Từ 18/09/2026 có thêm mô hình thứ hai: bộ chặn 2 lớp `checkpoints/organ_gate.pt`** (#92, mặc định TẮT — xem mục riêng bên dưới). ⚠️ **Ảnh PlantDoc `model/data/field/plantdoc/` (746 ảnh / 231 MB) cũng ngoài Git**, tải lại từ `pratikkayal/PlantDoc-Dataset`; **bộ ảnh âm `model/data/negative/` (342 ảnh) cũng ngoài Git và KHÔNG tải lại được** — phải sao lưu riêng |
| `model/research/` | Đã commit — danh mục 46 bài báo chia 8 nhóm + bản tổng hợp đối chiếu kết quả với các công bố. Xem mục "Phần việc của Bảo" bên dưới |
| `backend/` code | **Chạy mô hình thật** (không còn `DummyPredictor` mặc định) — 59/59 test pass (tính tới 18/09/2026, thêm `test_leaf_gate.py`/`test_overlay.py` cho #47), xem mục "Tích hợp mô hình thật" phía trên. **Từ 18/09/2026, bộ chặn #92 cũng đã bật** (`MODEL_GATE_CHECKPOINT`) — xem mục "#47" |
| `mobile/` (Flutter) | Giao diện đã dựng xong từ trước; **luồng chính đã nối API thật** ngày 07/09/2026: đăng nhập/đăng ký → danh mục → chụp/chọn ảnh → chẩn đoán thật kèm khoanh vùng → gợi ý xử lý (thuốc + video). Có màn **Đăng ký** tự phục vụ (xem mục "Tự đăng ký tài khoản") và **chẩn đoán ngoại tuyến** khi mất mạng (xem mục "Nhận diện ngoại tuyến trên điện thoại"). Màn **Lịch sử đã nối `GET /diagnoses` thật** từ trước — dòng cũ ghi "còn dữ liệu mẫu, chưa nối" ở đây đã lỗi thời, xoá (xem mục "Dọn 9 issue mobile cũ" bên dưới) |
| `web-admin/` (Next.js) | **Dựng xong 8 module** ngày 16/09/2026, kéo sớm hơn nhiều so với đề cương (dự kiến 01/10/2026) — theo yêu cầu trực tiếp của Học. Đổi từ kế hoạch Vite/4-trang sang Next.js App Router + TypeScript + Tailwind, xem "Web admin: kiến trúc và tiến độ" phía trên. Đã kiểm thử với backend thật + dữ liệu mẫu, **chưa** kiểm thử bằng cách bấm nút thật qua trình duyệt |

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

**#15 — đánh giá tập test.** Kết quả đầy đủ trong `docx/bao-cao-huan-luyen-mo-hinh.md`
(đã commit).

**IN-01, IN-02 — đã nối mô hình thật vào backend và mobile** ngày 07/09/2026, kéo
sớm hơn lịch mốc 4. Chi tiết ở mục "Tích hợp mô hình thật" phía trên.

**#49 — đo domain gap.** Xong 15/09/2026: **99,60 % → 30,81 %** trên PlantDoc.
Xem rủi ro số 1 bên dưới và `docx/bao-cao-domain-gap.md`.

**#17 — kiểm Grad-CAM có rơi đúng vết bệnh không.** Xong 15/09/2026, khoanh lá
**bằng tay** 56 ảnh trên cả hai bộ. Báo cáo: `docx/bao-cao-kiem-gradcam-vet-benh.md`.

| | PlantVillage (n=30) | PlantDoc (n=26) |
|---|--:|--:|
| Khối lượng heatmap: **vết bệnh / lá lành / nền** | 31,7 / 36,9 / 31,4 % | 20,3 / 51,8 / 28,0 % |
| Nâng chuẩn hoá vào lá *(0 = đoán mò, 1 = hoàn hảo)* | **0,41** (KTC 0,34–0,48) | **0,03** (KTC −0,12–0,17) |
| Vùng app thật sự khoanh — phần nằm trên nền | 7,3 % | **25,4 %** |

**Kết luận: đủ tin cậy để hiển thị với ảnh kiểu phòng thí nghiệm, CHƯA đủ với ảnh
chụp ngoài đồng.** Trên ảnh thật khoảng tin cậy **chứa số 0**, tức không chứng minh
được Grad-CAM ưu tiên lá hơn nền.

Bốn điều không suy ra được từ code, phải nhớ:

1. **Khả năng tìm VẾT BỆNH thì không tụt.** Nhóm lớp có vết khu trú được cho nâng
   chuẩn hoá vào vết bệnh **0,098** (PlantVillage) so với **0,102** (PlantDoc), cả
   hai khoảng tin cậy đều không chứa 0. Thứ hỏng trên ảnh thật là khả năng **không
   nhìn ra ngoài lá**, không phải khả năng tìm triệu chứng.
2. **#17 đính chính hai chỗ trong `docx/bao-cao-domain-gap.md` mục 5** — con số
   "điểm nóng trong lá chỉ 42 %" là lỗi mặt nạ (khoanh tay ra **80,8 %**), và cơ chế
   "mặt nạ phình ra" là ngược (mặt nạ **hụt** một phần ba vùng lá). Đã sửa tại chỗ.
3. **Heatmap biết khi nào mô hình sai.** Ảnh PlantDoc đoán đúng có đỉnh trên vết bệnh
   57,1 % / vùng khoanh trên nền 9,1 %; đoán sai là 15,8 % / 31,4 %. Mới là tương
   quan (n=7 vs 19) nhưng kiểm chứng trên cả 742 ảnh **không tốn thêm công khoanh
   tay** — tín hiệu tin cậy tốt hơn softmax, đầu vào cho #47 và #90.
4. **Người khoanh là trợ lý AI, chưa ai soát lại.** Đã khoanh **mù** (phiếu không in
   heatmap). Mặt nạ lưu dạng chữ trong `khoanh-tay.json`, sửa tay rồi chạy lại
   `audit_score` là ra số mới.

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

> Cập nhật **15/09/2026** sau khi #49 xong. Bản 10/09 (sau buổi rà soát bốn vấn đề khi
> thử app với mô hình thật) có ba chỗ nay đã sửa: **#17 bị lặp hai dòng**, **Grad-CAM++
> ghi sai số issue là #16** (nay là #98 — trước 15/09 việc đó không có issue nào), và
> **thiếu hẳn ba việc cải thiện độ chính xác** #93/#50/#94 dù chúng là phần trả lời trực
> tiếp cho kết quả #49.
>
> **Cập nhật lần hai, cũng ngày 15/09/2026 — #17 xong.** Hai dòng đầu bảng nay đều là
> việc đã xong, và thứ tự 1–3 đã đổi: xem ghi chú ngay dưới bảng.
>
> Số đo và lý lẽ: `docx/bao-cao-kiem-gradcam-vet-benh.md` (mới nhất),
> `docx/bao-cao-domain-gap.md`, `docx/Plan_model.md` mục 5.4.

| Thứ tự | Việc | Vì sao thứ tự này |
|---|---|---|
| ~~—~~ | ~~**#49 — đo domain gap**~~ | ✅ **XONG 15/09/2026: 99,60 % → 30,81 %** trên bộ H2 PlantDoc (742 ảnh, 8/10 lớp). Xem `docx/bao-cao-domain-gap.md`. Đã mở chốt cho #93, #94, #50 |
| ~~—~~ | ~~**#17 — kiểm Grad-CAM có rơi đúng vết bệnh không**~~ | ✅ **XONG 15/09/2026.** Khoanh tay 56 ảnh, cả hai bộ. **Đủ tin cậy trên PlantVillage (nâng chuẩn hoá 0,41), CHƯA đủ trên ảnh thật (0,03, khoảng tin cậy chứa số 0).** Số liệu và bốn điều phải nhớ ở mục "Đã xong" phía trên. Báo cáo: `docx/bao-cao-kiem-gradcam-vet-benh.md` |
| ~~—~~ | ~~**#91** thu bộ ảnh không phải lá → **#92** huấn luyện bộ 2 lớp~~ | ✅ **XONG 17–18/09/2026.** #91: 342 ảnh/6 nhóm, **dựng từ ảnh Internet** chứ không tự chụp (PR #105 đã merge). #92: bộ chặn `checkpoints/organ_gate.pt`, cho qua **91,18 %** ảnh lá thật, chặn **96,78 %** ảnh rác (PR #107). Bản đầu **đạt đủ tiêu chí ticket mà vẫn hỏng** — xem mục "#92 — bộ chặn 2 lớp" bên dưới, đó là phần đáng đọc nhất |
| **1** | **#93 — cắt vùng lá trước khi phân loại** | **Nay còn mở khoá cho #90, không chỉ là việc cải thiện độ chính xác.** Lý do cũ: xem 16 ca sai của #49 bằng mắt thì phần đáng kể là ảnh **chụp cả bụi cây** thay vì phiến lá cận cảnh — mô hình bị hỏi sai câu hỏi, và không augmentation nào sửa được. Lý do mới từ #17: diện tích lá trung bình trên PlantDoc là **70 %** khung hình, và tiêu chí chặn của #90 phải dựa vào vùng lá. Vẫn là hướng **duy nhất không cần một tấm ảnh mới nào**; phép thử che nền 10/09 chứng minh cắt nền không mất gì (bỏ hết viền nền vẫn đạt 97,3 %) |
| **2** | **#90 — không khoanh vùng khi bản đồ nhiệt quá yếu** | ⚠️ **#17 ĐỔI TIÊU CHÍ và ĐỔI THỨ TỰ việc này — đọc trước khi làm.** Bản cũ xếp số 2 và ghi "1 giờ, không cần Học sửa gì", với ý tưởng chặn khi CAM "quá yếu / quá phẳng". #17 đo độ phẳng CAM thô: **0,30 (PlantVillage) so với 0,32 (PlantDoc)** — **phẳng như nhau**, nên độ phẳng **không phân biệt được** ảnh phòng thí nghiệm với ảnh thật. Tiêu chí hứa hẹn hơn là **tỉ lệ khối lượng heatmap nằm trong vùng lá** → **phụ thuộc #93**. Vấn đề thì vẫn thật: **25,4 %** vùng app khoanh trên ảnh thật nằm ngoài lá |
| **3** | **#50 hướng 1 — tăng augmentation mô phỏng đồng ruộng** | Thay nền ngẫu nhiên, bóng đổ, mờ nhoè, nắng gắt. Rẻ nhất trong nhóm cải thiện: chỉ chỉnh config + huấn luyện lại ~30 phút, không cần dữ liệu mới |
| 4 | **#98 — nâng Grad-CAM++** | **Cổng #17 đã mở**, nhưng #17 chốt thứ tự là **sau #93**: nét hơn mà đặt sai vật thể thì vô nghĩa. #17 cho căn cứ định lượng: lớp `target_spot` (đốm chỉ chiếm 1,9 % ảnh) và `bacterial_spot` có **0/3 ảnh** điểm nóng trúng đốm — đúng vì heatmap 7×7 là **một khối tròn**, không thể chỉ vào nhiều đốm nhỏ rải rác. ⚠️ **Bảng này trước ghi sai là "#16"** — #16 thật là MD-07 sinh lưới ảnh minh hoạ cho slide |
| 5 | **#50 hướng 2 — fine-tune bằng `train` của PlantDoc** | Hiệu quả nhất nhưng là hướng **duy nhất tiêu dữ liệu đo**, nên để sau. 674 ảnh `train` (đã bỏ `tomato_V8.jpg` vì nhãn mâu thuẫn), đo lại trên đúng 66 ảnh `test`. Mốc "trước" đã có: **28,79 %**. ⚠️ KTC rộng 21 điểm nên phải cải thiện hơn ~12 điểm mới kết luận được |
| 6 | **#94 — test-time augmentation** | Rẻ, không huấn luyện lại gì. Làm **sau #93** để biết phần cải thiện đến từ đâu |
| ~~—~~ | ~~#18 — đo tốc độ suy luận trên CPU~~ | **Đã có số 10/09/2026: 215 ms** (CPU 4 luồng) cho `predict()` đầy đủ ở 1280 px, so với **452 ms** khi để torch tự lấy 16 luồng — tranh chấp luồng. Rủi ro số 2 hạ mức. Chỉ còn phần đo lại trên máy demo khi #51 chốt máy |
| 7 | **#19 — so ResNet18 / ResNet50 / B3** | ⚠️ **Hạ cấp 10/09/2026: làm để BÁO CÁO, không phải để sửa lỗi.** #49 xác nhận: điểm nghẽn là **68,8 điểm domain gap**, không phải 0,4 điểm còn lại trên PlantVillage. Đổi backbone không thu hẹp khoảng cách đó. `build.py` đã hỗ trợ sẵn, chỉ đổi `model.arch`. 4 lượt × 25 phút |

> ⚠️ **#90 vẫn phụ thuộc #93, đừng xếp nó lên trước.** #17 đo độ phẳng CAM thô ra
> **0,30 (PlantVillage) so với 0,32 (PlantDoc)** — phẳng như nhau, nên tiêu chí "CAM
> yếu/phẳng" mà bản gốc của #90 định dùng **không phân biệt được gì**. Tiêu chí thay thế
> (tỉ lệ khối lượng heatmap nằm trong vùng lá) cần vùng lá từ #93. Muốn làm #90 sớm hơn
> thì phải chọn một tiêu chí thứ ba, không phải chỉ đổi thứ tự.
> *(Bảng này từng xếp #91 số 1 và ghi "Bảo chưa xác nhận thứ tự" — #91/#92 nay đã xong,
> phần đó hết hiệu lực.)*

> **Ba việc cải thiện độ chính xác là #93, #50 và #94** — nếu cần tra nhanh thì đó là câu
> trả lời. Riêng **#50 hướng 2 là chỗ duy nhất "học thêm bộ dữ liệu khác"**. #19 KHÔNG
> thuộc nhóm này dù nghe giống: đã đo và bác bỏ.

### Bốn cái bẫy đã biết trước

1. **`configs/default.yaml` đặt `image_size: 224` dùng chung cho mọi kiến trúc.**
   Chạy EfficientNet-B3 ở 224 là dưới độ phân giải thiết kế của nó. Nếu #19 chạy vậy
   rồi kết luận "B3 không hơn B0" là **kết luận không công bằng** — phải ghi rõ.
2. **Không đo lại bằng trí nhớ.** Bảng chia tập và smoke test nằm trong PR #78; kết
   quả huấn luyện nằm trong `docx/bao-cao-huan-luyen-mo-hinh.md`. Trích từ đó.
3. **Checkpoint đã theo Git từ 07/09/2026.** File đang dùng là
   `model/checkpoints/leaf_disease_detection_model.pt` (backend trỏ tới qua
   `MODEL_CHECKPOINT` trong `backend/.env`), commit thẳng cùng `best.pt`. Trước
   đó hai file này nằm ngoài Git — đảo lại vì mục tiêu là máy khác `pull` về
   dùng được model ngay, không phải tự huấn luyện lại. `model/data/raw/` (ảnh
   gốc PlantVillage) vẫn ngoài Git — tải lại từ Kaggle theo issue #11.
4. **Đừng tin con số ảnh in trong bài báo — tự đếm file.** Bài học thật ngày 15/09/2026:
   bộ H1 công bố "731 ảnh, 7 lớp" trên một tạp chí có phản biện; tải về đếm thì chỉ có
   **308 ảnh gốc** (phần còn lại là bản nhân bản của Roboflow) và **không có file nào
   cho biết class ID nào là bệnh nào**. Nửa ngày mất vào đó, nhưng nếu cứ đoán ánh xạ rồi
   chạy thì `evaluate.py` sẽ cho ra một con số accuracy **trông hoàn toàn bình thường mà
   vô nghĩa**, không có gì báo lỗi, và con số đó đã thành số domain gap chính thức của đề
   tài. Với **bất kỳ** bộ dữ liệu ngoài nào: đếm file theo lớp, băm để tìm ảnh trùng, và
   kiểm ánh xạ nhãn **trước khi** chạy phép đo. Số liệu PlantDoc trong file này đã qua
   đúng ba bước đó. Mặt tốt: phần kiểm chứng này là nội dung **đánh giá chất lượng dữ
   liệu** đáng đưa vào báo cáo, trả lời trực tiếp câu "nhóm chọn dữ liệu thế nào".

### Quy ước về tài liệu trong `model/research/`

- Mỗi bài có **mã** (`A1`, `D4`, `E1`…). Nhắc mã là biết bài nào.
- Cột trạng thái: ✅ đã mở toàn văn · ⚠️ mới đọc tóm tắt · ⚪ mới thấy qua tìm kiếm.
  **Số liệu của bài ⚪ chỉ để biết bài đó có đáng đọc hay không, không được trích
  thẳng vào báo cáo.**
- Thư mục này **không phải bảng công việc**. Nguồn duy nhất vẫn là issue GitHub.

---

## #91 — bộ ảnh âm dựng từ Internet (chốt 17/09/2026 — lệch hướng có chủ đích so với ticket)

Ticket #91 (mục "Gợi ý triển khai") ghi thẳng: **"Không lấy ảnh từ Internet cho bộ
này"** — lý do kỹ thuật: ảnh mạng đã qua nén/chỉnh màu, phân phối khác ảnh điện thoại
chụp thật, và bộ phân loại 2 lớp #92 có nguy cơ học nhầm "ảnh nén web" so với "ảnh
điện thoại" thay vì "không phải lá cà chua" so với "lá cà chua".

**Quyết định:** dùng ảnh Internet thay vì tự chụp, vì Bảo xác nhận trực tiếp không
tự chụp được ảnh vào lúc này. Rủi ro phân phối nêu trên **vẫn còn nguyên**, không bị
gỡ bỏ chỉ vì đổi nguồn ảnh — khi báo cáo #91/#92 hoặc bảo vệ phải nói rõ bộ âm dựng
từ ảnh Internet, không phải ảnh điện thoại thật.

**Cách làm:** script `model/src/data/fetch_negative_images.py`, tải qua API Wikimedia
Commons (không đoán URL — mọi ảnh có giấy phép tái sử dụng rõ ràng, ghi lại trong
`model/data/negative/manifest.csv` cùng nguồn/license). Nhóm "ảnh mờ/tối/rung" không
tìm bằng từ khoá như 5 nhóm kia — thử rồi kiểm bằng mắt thấy Commons gần như không có
kho ảnh chụp hỏng thật (kết quả toàn ảnh nét dùng "blur" làm hiệu ứng nghệ thuật) — nên
nhóm này **tổng hợp** bằng cách lấy ảnh thật đã tải từ 5 nhóm kia rồi làm méo bằng
PIL/numpy (mờ nét, mờ chuyển động, thiếu sáng).

**Kết quả (17/09/2026):** 342 ảnh, 6/6 nhóm đều vượt tối thiểu 25 ảnh/nhóm:

| Nhóm | Số ảnh |
|---|--:|
| `indoor_objects` | 60 |
| `hand_face_clothing` | 61 |
| `other_plant_leaves` | 60 |
| `soil_ground` | 55 |
| `screenshot_document` | 52 |
| `blur_dark_shake` | 54 |

Hai vòng soát thủ công đã loại các loại ảnh lọt lưới do tìm từ khoá trên Commons
trúng nhầm (giữ lại làm bài học cho ai chạy lại script hoặc thêm nhóm mới):
trang scan sách/tạp chí cũ (Internet Archive Book Images, Biodiversity Heritage
Library — khớp từ khoá qua caption OCR dù ảnh thật là trang giấy), tranh khắc/thạch
bản/minh hoạ y khoa cổ và chữ cái trang trí bản thảo Phúc Âm trung cổ (Wellcome
Collection, Walters Manuscript — khớp "hand"/"face" nhưng là tranh vẽ, không phải
ảnh chụp), và một loạt ảnh phong cảnh/hoa/kiến trúc không liên quan lọt vào nhóm
`screenshot_document` do một bug đếm file (đếm `*.jpg` bỏ sót `*.png` đã tải, khiến
vòng lặp tưởng chưa đủ target và tải dư bằng từ khoá cuối cùng — kém liên quan nhất
trong danh sách truy vấn). Bug đã sửa trong script; ai chạy lại vẫn nên kiểm bằng mắt
vì tìm từ khoá trên Commons không ổn định 100%.

`model/data/negative/` nằm trong `.gitignore` như `data/raw/` — nhưng khác `data/raw/`
(tải lại được từ Kaggle), bộ này **không tải lại được từ đâu** vì đã qua chọn lọc thủ
công, nên **phải backup riêng**. `manifest.csv` có ngoại lệ giữ trong Git (nhẹ, chỉ
đường dẫn + nguồn + license, không phải ảnh) để biết ảnh đến từ đâu ngay cả khi chưa
backup xong.

**✅ Bước 3 "Cách kiểm tra" của ticket đã làm xong (17/09/2026):** chạy checkpoint lên
toàn bộ 342 ảnh, đo phân bố độ tin cậy + energy. Số liệu:
`model/outputs/negative-confidence/{results.csv,summary.json}`, script
`src/evaluation/audit_negative_confidence.py`.

**Kết quả đáng nhớ: ngưỡng tin cậy đơn thuần KHÔNG chặn nổi.** Ở ngưỡng 0,90 chỉ chặn
được **98,8 %**, và ảnh lọt qua có ảnh đạt **0,967** — một ảnh sân vườn (cỏ, hàng rào,
hoa vàng, không có cà chua) được kết luận là virus xoăn vàng lá, nhiều khả năng vì mô
hình bám **màu vàng** của hoa. Ngưỡng energy (`−logsumexp`) tốt hơn nhưng cũng chỉ tới
98,5 % ở mức −3,34. Ước lượng cũ trong `docx/Plan_model.md` bảng 1.3/1.4 nói cả hai
chặn được 100 % — con số đó dựa trên 11–16 ảnh tổng hợp, **lạc quan vì mẫu quá nhỏ**.
→ Đây là căn cứ để #47 bỏ hướng "ngưỡng tin cậy" và chuyển sang dùng bộ chặn #92.

**Cố ý không làm:** đăng bảng thống kê lên issue #91 (Bảo bảo không cần).

---

## #92 — bộ chặn 2 lớp lá / không phải lá (chốt 18/09/2026)

`checkpoints/organ_gate.pt`, EfficientNet-B0 2 lớp `tomato_leaf` / `not_tomato_leaf`,
đứng **trước** mô hình bệnh. Code: `src/data/prepare_gate.py` (chia tập),
`src/data/gate_augment.py` (phá lối tắt), `src/training/train_gate.py`,
`src/evaluation/evaluate_gate.py`. Số liệu máy sinh: `outputs/gate/report.json`.

### ⚠️ Bài học lớn nhất: tiêu chí của chính ticket cho qua một bộ chặn hỏng

Bản huấn luyện đầu (lớp dương chỉ PlantVillage, lớp âm chỉ ảnh Internet của #91)
**đạt đủ mọi tiêu chí #92**: recall lá 1,0000 trên tập test của chính nó, 0,9993 trên
2.719 ảnh test PlantVillage, chặn 342/342 ảnh âm. Nếu chỉ chạy đúng ba phép đo ticket
yêu cầu thì #92 đã "xong" và lỗi đi thẳng vào bản demo.

Thực tế nó **chặn oan 92,0 % ảnh lá cà chua thật** (PlantDoc). Nó không học "lá / không
phải lá" mà học **"ảnh phòng thí nghiệm / ảnh Internet"** — hai lớp tách được bằng phong
cách ảnh nên mạng không cần nhìn cái lá. Nông dân chụp ngoài vườn thì ảnh giống PlantDoc
chứ không giống PlantVillage, tức app sẽ từ chối gần như mọi lần chụp.

**Lý do phép đo của ticket không bắt được:** cả ba đều lấy ảnh dương từ PlantVillage, nên
đo đúng cái miền mà lối tắt hoạt động. Bất kỳ bộ phân loại nào có **lớp dương và lớp âm
đến từ hai nguồn ảnh khác nhau** đều dính bẫy này — phải có một tập đánh giá lấy lớp
dương từ nguồn thứ ba. Ghi lại để #71 (mở 2 lớp thành 3 lớp lá/quả/khác) không lặp lại:
ảnh quả mà lấy từ Roboflow/Kaggle còn ảnh lá từ PlantVillage thì y hệt tình huống này.

### Ba bản đã chạy, đo trên cùng 68 ảnh PlantDoc test

| Bản | Recall lá thật (PlantDoc test) | Recall lá PlantVillage | Recall lớp âm |
|---|--:|--:|--:|
| 1. Lớp dương chỉ PlantVillage | **0,0882** | 0,9993 | 1,0000 |
| 2. + phá lối tắt bằng augmentation | ~0,35 \* | 0,9978 | 0,9912 |
| 3. + 674 ảnh PlantDoc `train` (bản đang dùng) | **0,9118** | 0,9989 | 0,9678 |

\* Bản 2 đo trên cả 742 ảnh (lúc đó PlantDoc còn sạch hoàn toàn) chứ không đo riêng 68
ảnh, và checkpoint của nó đã bị ghi đè. Bản 1 thì **còn nguyên**:
`checkpoints/organ_gate_shortcut_baseline.pt` — giữ lại chính vì nó là bằng chứng trực
tiếp của bài học ở trên, đừng xoá. Dựng lại bản 1 hoặc bản 2 từ đầu:

```bash
# bản 1: bỏ PlantDoc khỏi lớp dương, tắt luôn phá lối tắt
python -m src.data.prepare_gate --plantdoc-manifest /khong/ton/tai --out data/processed/gate-v1.csv
python -m src.training.train_gate --manifest data/processed/gate-v1.csv \
       --no-domain-augment --out checkpoints/gate-v1.pt
# bản 2: như trên nhưng BỎ cờ --no-domain-augment
```

Đọc bảng cho đúng: **augmentation một mình không đủ** (0,09 → ~0,35, vẫn hai phần ba ảnh
thật bị chặn oan). Nó chỉ xoá được manh mối *nền*; phiến lá vẫn cắt rời, nét, nằm giữa
khung. Phải cho bộ chặn nhìn lá thật ngoài đồng mới xong. Giá phải trả là recall lớp âm
tụt 1,0000 → 0,9678 — **đúng chiều mong muốn**, vì #92 nói rõ chặn oan lá thật tệ hơn để
lọt ảnh rác.

### ⚠️ Ranh giới PlantDoc đã đổi — đọc trước khi đo bất cứ thứ gì trên PlantDoc

Bộ chặn **đã học 674 ảnh PlantDoc thuộc thư mục `train` gốc**. Đúng ranh giới `CLAUDE.md`
đặt sẵn cho #50 hướng 2, nhưng từ nay:

- **68 ảnh thư mục `test` là thước đo sạch DUY NHẤT còn lại cho bộ chặn.** Không được
  đưa vào huấn luyện dưới bất kỳ hình thức nào.
  ⚠️ **68 ở đây và 66 ở dòng "#50 hướng 2" trong bảng việc KHÔNG mâu thuẫn**, đừng ai
  "sửa" cho khớp: 68 là phần `/test/` của manifest `plantdoc-all`, còn 66 là
  `plantdoc-official` đã bỏ thêm 2 ảnh rò rỉ/mâu thuẫn nhãn. Bộ chặn đo trên 68 vì nó
  không quan tâm nhãn bệnh (chỉ cần biết "có phải lá cà chua không"), còn #50 đo
  accuracy theo lớp bệnh nên phải bỏ 2 ảnh đó.
- Con số domain gap của #49 (**99,60 % → 30,81 %** trên cả 742 ảnh) **vẫn đúng**, vì nó
  đo checkpoint *mô hình bệnh* — mô hình đó chưa từng thấy PlantDoc.
- Nhưng **mọi phép đo cả pipeline (bộ chặn + mô hình bệnh) trên toàn bộ 742 ảnh từ nay là
  nhiễm.** `evaluate_gate.py` in riêng hai dòng D1 (sạch, 68 ảnh) và D2 (nhiễm, 742 ảnh)
  kèm cảnh báo, đừng trích nhầm D2.

### Điểm yếu thật, phải nói khi bảo vệ

Nhóm **`other_plant_leaves`** (lá cây khác, ưu tiên họ Cà: khoai tây, cà tím, *Solanum
torvum*) là chỗ lọt nhiều nhất: **8/60 ảnh toàn nhóm, 2/9 ảnh phần test**. Đúng như #92
dự đoán đây là ca khó nhất. Năm nhóm còn lại gần như không lọt (0–2 ảnh mỗi nhóm).

Và giới hạn bản chất, ticket bắt ghi rõ: đây là **bộ phân loại nhị phân trên một bộ âm
hữu hạn**, không phải bộ phát hiện ngoài phân phối tổng quát. Nó chặn được thứ *giống*
342 ảnh âm đã học, không bảo đảm chặn được mọi thứ trên đời.

### Cách nối vào hệ thống: MẶC ĐỊNH TẮT, phải bàn với Học trước khi bật

`DiseasePredictor(checkpoint, gate_checkpoint=...)` — không truyền `gate_checkpoint` thì
hành vi cũ y nguyên, không nạp gì thêm. Bật lên thì ảnh bị chặn trả
`disease_key="not_tomato_leaf"`, `heatmap=None`, `probabilities={}`.

Gói bộ chặn *vào trong* `DiseasePredictor` là cố ý: **hợp đồng dùng chung không đổi**,
không phải thêm trường `organ` vào `Prediction`, backend không cần biết có mô hình thứ
hai. Đã bật ở `backend/.env` (18/09/2026) — chi tiết cách nối vào ở mục **#47** ngay dưới.

⚠️ **Đính chính (18/09/2026): ticket #92 — và bản đầu của chính mục này — viết rằng
`catalog.get_disease()` sẽ LỖI với khoá `not_tomato_leaf`. Sai.** Đọc
`backend/app/services/catalog.py:37` thì nó trả về một **bản ghi rỗng an toàn** với
`name_vi = key`. Nghĩa là bật bộ chặn mà quên xử lý thì **không có exception nào**,
nông dân chỉ thấy tên bệnh là dòng chữ `not_tomato_leaf` — sai âm thầm, không hiện
trong log, tệ hơn là sập hẳn. Phần overlay thì đã an toàn sẵn:
`diagnosis_service.py:70` có kiểm `heatmap is not None` nên không vẽ elip bừa.

---

## #47 — nối bộ chặn #92 vào backend/app, đổi vùng khoanh từ elip sang contour thật (chốt 18/09/2026)

**Bộ chặn.** `MODEL_GATE_CHECKPOINT` (mới, `backend/app/core/config.py`) — để trống thì
tắt hẳn, y hệt trước #47. Bật bằng cách trỏ tới
`../model/checkpoints/organ_gate.pt` trong `.env` (đã bật trên máy này, xem
`backend/.env.example`). `services/inference/loader.py` kiểm file checkpoint bộ chặn
tồn tại **trước khi** đưa vào `DiseasePredictor` — thiếu/lỗi checkpoint bộ chặn chỉ log
lỗi rồi bỏ qua bộ chặn, KHÔNG kéo cả mô hình bệnh thật rơi về `DummyPredictor` (bộ chặn
là phụ, mô hình bệnh mới là chính).

**Ba quyết định "phải có ý thức" mà ticket #47 yêu cầu ghi lại:**

1. **Không lưu `Diagnosis` khi CẢ LÔ ảnh đều bị chặn.** `diagnosis_service.py` thêm
   `NotTomatoLeafError`; `_run_and_aggregate` loại các ảnh có
   `disease_key == "not_tomato_leaf"` ra khỏi phần tổng hợp bệnh, và nếu **không còn ảnh
   lá nào** thì raise lỗi này thay vì để `ranked[0]` sập vì rỗng. Endpoint bắt lỗi, trả
   `422` kèm câu tiếng Việt — không tạo bản ghi CSDL nào, giữ Lịch sử/bộ lọc `disease_key`
   của web admin/thống kê dashboard sạch, đúng lo ngại chính ticket #92 nêu ra.
2. **Lô ảnh hỗn hợp (một phần bị chặn) thì loại phần bị chặn khỏi việc tính bệnh/mức độ
   chung, nhưng vẫn lưu một dòng `DiagnosisImage` riêng cho ảnh đó** (đúng
   `disease_key="not_tomato_leaf"`) — nông dân thấy đúng ảnh nào trong lô bị từ chối,
   ảnh đó không kéo tụt xác suất trung bình của các ảnh lá thật còn lại.
3. **`catalog.get_disease()` xử lý riêng `NOT_TOMATO_LEAF_KEY`**, trả
   `name_vi = "Ảnh chưa rõ lá cà chua, bạn chụp lại giúp mình nhé"` — không rơi vào nhánh
   "khoá lạ" (vốn trả nguyên văn khoá, đúng cái bẫy mục #92 cảnh báo). Hằng số khoá chép
   lại thành `NOT_TOMATO_LEAF_KEY` trong `backend/app/services/inference/base.py` (không
   import từ `model/`, đúng ranh giới kiến trúc) thay vì import trực tiếp từ
   `model/src/predictor.py`.

**Bug thật phát hiện khi nối vào mobile — không nằm trong phạm vi ticket gốc nhưng phải
sửa để #47 có tác dụng:** `AnalyzingScreen._run()` (mobile) trước đó bắt `catch (_)`
**mọi** lỗi từ `POST /diagnoses` rồi tự động rơi xuống `OfflineInferenceService` — kể cả
`ApiException` (backend đã trả lời, không phải mất mạng). Nghĩa là ảnh bị bộ chặn #92 từ
chối ở luồng online sẽ bị **âm thầm chạy lại ở luồng ngoại tuyến, nơi không hề có bộ
chặn** (xem mục "Nhận diện ngoại tuyến trên điện thoại" — offline vốn đã ghi rõ ngoài
phạm vi #47), và có thể vẫn ra một tên bệnh cho ảnh cái bàn. Sửa: chỉ bắt `on
NetworkException` để rơi xuống offline; `ApiException` (bao gồm cả lỗi 422 của #47) rơi
xuống nhánh `on ApiException` đã có sẵn, hiện đúng thông báo tiếng Việt.

**Màn hiển thị khi bị chặn:** dùng lại màn lỗi có sẵn của `AnalyzingScreen` (không phải
màn `ResultScreen` — nên tự động không có elip/độ tin cậy/gợi ý thuốc, đúng tiêu chí
ticket), chỉ đổi icon (máy ảnh thay vì tam giác cảnh báo) và tiêu đề khi thông báo khớp
đúng câu của bộ chặn — phân biệt "hệ thống đang làm đúng việc" với "có lỗi thật sự".
Câu thông báo chép tay sang Dart (`_notTomatoLeafMessage`), same lý do/cùng kiểu với
`tomato_diseases.json` chép tay ở mục ngoại tuyến — hai bên khác ngôn ngữ, không import
chung được.

⚠️ **Chưa làm — cần Học/Bảo tự kiểm trên máy thật trước khi coi #47 là xong hẳn:** ticket
yêu cầu "kiểm thủ công 2 ca: chụp cái bàn → màn chưa nhận ra lá; chụp lá bệnh nặng → vẫn
chẩn đoán bình thường". Phiên làm việc này chỉ kiểm bằng test tự động (predictor giả lập
gate, không phải checkpoint thật — máy chạy phiên này không có torch/GPU) và
`dart analyze` (không lỗi). Chưa chạy được `organ_gate.pt` thật lẫn app thật trên thiết
bị. Việc còn thiếu: bấm thử trên điện thoại/máy ảo thật với backend chạy mô hình thật.

**Đổi cách vẽ vùng khoanh: contour thật thay vì elip khớp.** `backend/app/services/xai/overlay.py`
trước đó dùng `cv2.fitEllipse` quanh contour lớn nhất — với vết bệnh không lồi (hình chữ
L, dải dài, nhiều nhánh...) elip sẽ bao trùm cả phần lá lành nằm giữa các "nhánh" của vết
bệnh, không phải lỗi code mà là giới hạn hình học của chính việc dùng elip. Đổi sang vẽ
đúng contour (làm mượt bằng Gaussian blur + `approxPolyDP` để bỏ răng cưa do CAM gốc chỉ
7×7 phóng to, không phải để đổi hình dạng), kèm tô nhẹ 22% alpha bên trong (không phải
overlay đặc như heatmap cầu vồng) để vùng khoanh "rõ hơn" mà vẫn nhìn xuyên thấy lá bên
dưới. Test khoá hành vi: `backend/tests/test_overlay.py` — dựng một heatmap hình chữ L,
xác nhận điểm nằm trong "hốc" của chữ L (nằm trong bounding box/elip nhưng ngoài vùng
thật) không bị tô.

1. **Domain gap.** PlantVillage chụp lá đơn trên nền đồng nhất trong phòng; mô hình
   thường đạt >99% trên tập test nhưng rớt mạnh với ảnh chụp thật ngoài đồng.

   ⚠️ **Kế hoạch "thu thập 50–100 ảnh thật vào `model/data/field/`" đã BỎ HẲN
   (chốt 17/09/2026, trước đó hoãn vô thời hạn từ 10/09)** — nhóm không liên hệ được
   nhà vườn để xin phép chụp. Issue #20/#21/#48 **đã đóng** (không phải "not planned"
   để mở chờ nữa) — mở lại nếu tình hình đổi thật sự. **`model/data/field/` sẽ vẫn
   rỗng.**

   Rủi ro này **không** vì thế mà bỏ trống — nhưng bộ dữ liệu để đo **đã đổi một lần**,
   và đó là chỗ dễ đọc sai nhất trong cả file này.

   #### ❌ Bộ H1 đã bị LOẠI (15/09/2026) — đừng tìm cách dùng lại

   Bản trước của mục này ghi *"#49 chạy trên bộ H1 là đường duy nhất, và vẫn đủ"*, dựa
   trên con số 731 ảnh mà bài báo công bố. Ngày 15/09 tải bộ về kiểm thì **cả hai câu
   đều sai**:

   - Bộ trên Mendeley là bản xuất **Roboflow định dạng YOLO** (phát hiện vật thể), và
     **không kèm `data.yaml`** — đúng 0 file ngoài `.jpg`/`.txt`. Nên **không biết class
     ID nào là bệnh nào.** Đã thử khôi phục bằng cách đếm hộp theo từng class ID rồi đối
     chiếu bảng trong bài báo: **2.278 hộp đo được so với 1.621 bài báo ghi**, và class 1
     một mình chiếm 51,7 % số hộp trong khi lớp đông nhất của bài báo chỉ có 325. Không
     khớp theo thứ tự bảng, cũng không khớp theo thứ tự chữ cái.
   - **230 trong 689 ảnh có nhãn chứa hộp của nhiều lớp khác nhau** → không gán được một
     nhãn/ảnh để chạy `evaluate.py`.
   - Con số **731 ảnh là số đã bị nhân bản**: 1.420 file `.jpg` chỉ ứng với **308 ảnh
     gốc**, thư mục "731 ảnh" ứng đúng 302 ảnh gốc. Quy mô thật nhỏ hơn công bố ~2,4 lần.
     (Dù vậy 302 ảnh vẫn nhiều hơn mốc 50–100 ảnh tự chụp — **quy mô không phải lý do
     loại H1**, nhãn không tra được mới là lý do.)

   Loại hẳn, không phải hoãn: nhãn không tra được thì không có cách dùng lại về sau, trừ
   khi tác giả công bố thêm `data.yaml`. Căn cứ đầy đủ ở `docx/Plan_model.md` **mục 5.2**.

   #### ✅ Thay bằng H2 — PlantDoc (chốt 15/09/2026)

   GitHub `pratikkayal/PlantDoc-Dataset`, bộ **phân loại chia thư mục theo lớp**, tên thư
   mục viết rõ bằng chữ nên **không phải đoán ánh xạ**. Số liệu dưới đây **tự đếm**, không
   trích lại từ bài báo:

   - **744 ảnh cà chua dùng được trên 8 lớp** (675 `train` + 69 `test`) — nhiều hơn H1 hai
     lớp, và gấp 7–15 lần con số 50–100 ảnh tự chụp theo kế hoạch ban đầu.
   - `spider_mites` chỉ có **2 ảnh** (và một trong hai tên file nói về bệnh loét) →
     **loại khỏi phép đo**. `target_spot` **không có** trong PlantDoc. Mô hình vẫn trả 10
     lớp, nên phải truyền `labels=` khi tính chỉ số và báo macro-F1 trên 8 lớp có mặt.
   - ⚠️ **Bản chia `train`/`test` của chính PlantDoc có rò rỉ 3 ảnh trùng byte tuyệt đối**
     (so bằng sha256), và **1 trong 3 ảnh đó mang hai nhãn khác nhau** (`tomato_V8.jpg`:
     `bacterial_spot` ở `test`, `septoria_leaf_spot` ở `train`) nên bị loại hẳn. Việc lọc
     đã tự động hoá trong `src/data/prepare_plantdoc.py`, lý do từng ảnh bị bỏ ghi vào
     `audit.json` — đừng lọc tay.

   **Ranh giới phải giữ:** con số domain gap chính của #49 đo trên **toàn bộ 742 ảnh** (744
   trừ ảnh rò rỉ/mâu thuẫn), hợp lệ vì checkpoint hiện tại chưa từng thấy một ảnh PlantDoc
   nào — và con số đó **đúng vĩnh viễn**, kể cả sau khi #50 fine-tune. Phần fine-tune (#50
   hướng 2) chỉ được dùng **`train`**, rồi đo lại trên **`test`**. Trộn hai phần thì con số
   domain gap của cả đề tài mất giá trị, mà lỗi đó không báo lỗi gì.

   #### ✅ #49 ĐÃ XONG (15/09/2026) — con số domain gap của nhóm

   > **99,60 % → 30,81 %. Tụt 68,79 điểm.** Báo cáo đầy đủ:
   > **`docx/bao-cao-domain-gap.md`**. Số liệu máy sinh:
   > `model/outputs/plantdoc-{all,8lop,official}/` và
   > `model/outputs/plantvillage-8lop/`.

   Cả hai con số đo trên **đúng 8 lớp** mà PlantDoc có (đã lọc tập test PlantVillage cho
   khớp — so 10 lớp với 8 lớp là so lệch). Hai khoảng tin cậy 95 % **không chồng lấn**
   (99,24–99,79 % so với 27,59–34,23 %).

   Kết quả **gần trùng khớp bài A1** — chính tác giả PlantVillage báo 99,35 % → 31,40 %,
   nhóm lệch 0,6 điểm ở con số cuối. Đó là bằng chứng phép đo đúng, và là câu trả lời mạnh
   cho phản biện. **Rủi ro số 1 từ nay không còn là dự đoán mà là số đo.**

   Ba hệ quả **đã đổi thứ tự việc**, đọc trước khi chọn việc tiếp theo:

   1. **#47 thu hẹp phạm vi.** Ngưỡng tin cậy **không** vá được độ chính xác trên ảnh thật:
      ở ngưỡng 0,90 hệ thống từ chối 85,4 % ảnh thật mà accuracy phần còn lại vẫn chỉ
      56,5 %, đồng thời chặn oan 8,5 % ảnh PlantVillage. Vẫn làm #47, nhưng **chỉ để chặn
      ảnh không phải lá** — đừng kỳ vọng nó cải thiện accuracy.

      ➕ **#17 bổ sung một tín hiệu tin cậy khác, có vẻ tốt hơn softmax:** *vị trí* của bản
      đồ nhiệt. Trên PlantDoc, ảnh mô hình đoán **đúng** có đỉnh heatmap rơi trên vết bệnh
      **57,1 %** và chỉ **9,1 %** vùng khoanh nằm trên nền; ảnh đoán **sai** là **15,8 %**
      và **31,4 %**. Mới là tương quan (n=7 so với 19) và ảnh đoán đúng phần lớn là ảnh cận
      cảnh vết bệnh lớn — nhưng **kiểm chứng trên cả 742 ảnh không tốn thêm công khoanh tay
      nào**. Đáng thử trước khi chốt ngưỡng cho #47.
   2. ~~**#17 nâng ưu tiên và mở rộng phạm vi.**~~ ✅ **#17 ĐÃ LÀM XONG cùng ngày, và
      đính chính chính mục này.** Cảnh báo cũ ghi *"điểm nóng nhất nằm trong lá chỉ 42 %"* —
      con số đó là **lỗi của mặt nạ Otsu**, khoanh tay ra **80,8 %**. Phần *mức tập trung*
      thì đúng: khoanh tay ra **1,65× → 1,10×**. Kết luận cuối: **đủ tin cậy trên
      PlantVillage, chưa đủ trên ảnh thật**. Số liệu đầy đủ ở mục "Đã xong" phía trên và
      `docx/bao-cao-kiem-gradcam-vet-benh.md`.
   3. **#93 nâng ưu tiên — nay lên số 1 trong nhóm cải thiện.** Xem 16 ca sai bằng mắt thì
      một phần đáng kể là ảnh **chụp cả bụi cây**, không phải phiến lá cận cảnh — tức mô
      hình bị hỏi sai câu hỏi. #17 đo thêm: diện tích lá trung bình trên PlantDoc là **70 %**
      khung hình. Cắt vùng lá đánh đúng chỗ đó, là hướng duy nhất **không cần dữ liệu mới**,
      và **nay còn mở khoá cho #90** vì tiêu chí chặn phải dựa vào vùng lá.

   **Hạn chế phải ghi vào báo cáo:** PlantDoc là ảnh **thu từ Internet**, không phải ảnh tự
   chụp ngoài đồng — vẫn là phép thử domain shift hợp lệ (nền lộn xộn, nhiều lá chồng, ánh
   sáng tự nhiên) nhưng **đừng gọi là "ảnh đồng ruộng"**. Đề tài kết luận được về domain gap
   **nói chung**, **không** kết luận được gì riêng cho điều kiện canh tác ở Đà Lạt. Đừng
   trình bày như thể đã đo trên ảnh địa phương. PlantDoc cũng có tiếng nhãn hơi nhiễu nên
   phải xem mẫu bằng mắt.

   Ba con số có nguồn trích dẫn được (chi tiết trong `model/research/`): chính tác
   giả PlantVillage báo cáo tụt từ 99,35% xuống **31,40%** trên ảnh điều kiện khác
   (bài A1); review 2024 đo trung bình **90,18% → 84,66%** (A3); và có người huấn
   luyện **chỉ bằng 8 pixel nền** vẫn đạt 49% (A2).

   ⚠️ **Bốn tài liệu trong `model/research/` vẫn ghi H1 dùng được** (`00-danh-muc-bai-bao.md`,
   `01-ke-hoach-thi-nghiem.md` TN-2, `02-cau-hoi-phan-bien.md`, `03-tong-hop-doi-chieu.md`)
   — chưa sửa, đang chờ Bảo quyết. Đọc mục này trước khi tin chúng.
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
