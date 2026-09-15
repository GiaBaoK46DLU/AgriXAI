# Rà soát 4 vấn đề sau khi tích hợp mô hình thật, và kế hoạch xử lý

> Ghi ngày **10/09/2026**, ba ngày sau khi mô hình thật được nối vào mobile (IN-01, IN-02).
> Toàn bộ số liệu trong tài liệu này **đo trực tiếp trên checkpoint đang chạy**
> `model/checkpoints/leaf_disease_detection_model.pt`
> (`efficientnet_b0-20260907-1443`), không trích lại từ báo cáo cũ.
>
> Mục đích: trả lời bốn vấn đề Bảo nêu sau khi thử app thật, phân biệt cho rõ
> **triệu chứng** với **nguyên nhân**, rồi xếp việc theo thứ tự đáng làm.
>
> ⚠️ **Đã sửa ngày 15/09/2026 — bộ H1 bị loại, thay bằng H2 (PlantDoc).** Bản ngày
> 10/09 khẳng định *"#49 chạy trên bộ H1 là đường duy nhất, và vẫn đủ"*. Khi bắt tay
> làm #49 thì phát hiện H1 **không gán nhãn phân loại được** và con số "731 ảnh" là
> số đã bị nhân bản. Toàn bộ căn cứ ở **mục 5.2** (mới thêm). Các mục 1–4 đo trên
> checkpoint và không bị ảnh hưởng, giữ nguyên.

---

## 0. Đã chạy những gì để kiểm chứng

Bốn phép thử, chạy bằng `model/.venv`, GPU RTX 4060 Ti. Script đặt ở thư mục tạm
của phiên làm việc (`scratchpad/probe_*.py`) — **chưa commit vào repo**, xem câu
hỏi 4 ở mục 6.

| # | Phép thử | Câu hỏi cần trả lời |
|---|---|---|
| 1 | `probe_ood.py` | Mô hình phản ứng thế nào với ảnh không phải lá? Ngưỡng tin cậy có chặn được không? |
| 2 | `probe_shortcut.py` | Mô hình có học "tắt" theo nền ảnh thay vì theo vết bệnh không? (tái hiện bài **A2**) |
| 3 | `probe_gradcam.py` | Grad-CAM có rơi vào lá hay rơi ra nền? (tiền kiểm cho **#17**) |
| 4 | `lat.py` | Độ trễ thật của `predict()` đầy đủ trên CPU (**#18**) |

Ba ảnh thực địa dùng để thử là ba ảnh Bảo đã tự tải lên qua app ngày 07/09
(`backend/storage/uploads/2026/09/`) — ảnh #2 và #3 là **cùng một ảnh** tải lên
hai lần, kết quả trùng khớp tuyệt đối, xác nhận luồng suy luận có tính tất định.

---

## 1. Vấn đề 2 — chụp vật thể bất kỳ vẫn báo bệnh lá

**Đây là vấn đề nghiêm trọng nhất trong bốn vấn đề.** Không phải vì khó sửa, mà vì
nó là câu hỏi gần như chắc chắn sẽ bị hỏi khi bảo vệ, và vì hiện tại hệ thống
**không có một dòng code nào** để xử lý.

### 1.1. Nguyên nhân — đã xác định chính xác

Không phải mô hình "kém". Đây là hệ quả toán học tất yếu của kiến trúc hiện tại:

Lớp cuối của mô hình trả về 10 con số (logit), rồi `softmax` biến chúng thành 10
xác suất **luôn cộng lại đúng bằng 1**. Cấu trúc này không có chỗ nào để biểu đạt
"không thuộc lớp nào cả" — dù ảnh vào là cái bàn, bàn tay hay tờ giấy trắng, tổng
xác suất vẫn phải là 1, nên bắt buộc phải chia cho 10 lớp bệnh lá.

Đã rà toàn bộ đường đi của một lần chẩn đoán và xác nhận **không có bất kỳ chốt
kiểm tra nào**:

| Nơi | Điều đã kiểm | Kết quả |
|---|---|---|
| [`model/src/predictor.py:79`](model/src/predictor.py#L79) | `predict()` có xét ngưỡng không | Không. `argmax` thẳng rồi trả về |
| [`backend/app/services/diagnosis_service.py:28`](backend/app/services/diagnosis_service.py#L28) | `run_diagnosis()` có chặn không | Không. Nhận gì ghi thẳng vào CSDL |
| [`backend/app/services/xai/explain.py:98`](backend/app/services/xai/explain.py#L98) | `interpret()` có xét `confidence` không | **Không** — chỉ xét diện tích vùng khoanh, không hề xét độ tin cậy |
| [`backend/app/core/config.py`](backend/app/core/config.py) | Có biến ngưỡng nào không | Chỉ có `HEATMAP_THRESHOLD`, không có ngưỡng tin cậy |

Nói cách khác: câu tiếng Việt trả về cho người dùng **luôn khẳng định một loại
bệnh**, bất kể mô hình tin bao nhiêu phần trăm.

### 1.2. Số đo — mô hình nói gì khi xem ảnh không phải lá

**Bảng 1.1. Ảnh tổng hợp không phải lá**

| Ảnh vào | Mô hình kết luận | Độ tin cậy |
|---|---|---|
| Nền xám trơn | Đốm mắt cua (`septoria_leaf_spot`) | 39,7 % |
| Nền trắng trơn | Xoăn vàng lá (`yellow_leaf_curl_virus`) | 36,5 % |
| Nền đen trơn | Xoăn vàng lá | 37,2 % |
| Nền đỏ trơn | Xoăn vàng lá | 40,6 % |
| Nhiễu ngẫu nhiên | Xoăn vàng lá | 35,1 % |
| Ô bàn cờ đen trắng | Xoăn vàng lá | **59,6 %** |
| Vật thể màu da trên nền tường | Xoăn vàng lá | **65,4 %** |

**Bảng 1.2. Ảnh thật không phải lá** — quan trọng hơn bảng trên

| Ảnh vào | Mô hình kết luận | Độ tin cậy |
|---|---|---|
| Ảnh biểu đồ `training-curves.png` | Lá khoẻ | 30,9 % |
| Ảnh ma trận nhầm lẫn | Đốm mắt cua | 22,3 % |
| Icon ứng dụng Flutter | Mốc lá (`leaf_mold`) | **55,6 %** |
| **Crop góc nền của chính ảnh thực địa Bảo chụp** (bìa carton, không có lá) | **Mốc sương muộn (`late_blight`)** | **84,5 %** |

Dòng cuối là dòng đáng lo nhất, và cũng là dòng chỉ ra đúng cách xử lý. Một mảnh
**nền carton trơn, không có một cọng lá nào**, cắt ra từ chính bức ảnh Bảo đã chụp
bằng chính chiếc điện thoại đó, được mô hình kết luận là mốc sương muộn với
**84,5 % tin cậy**.

### 1.3. Vì sao ngưỡng độ tin cậy một mình là không đủ

Issue **#47** đề xuất một ngưỡng tin cậy tối thiểu. Đó là bước đi đúng, nhưng dòng
84,5 % ở trên cho thấy nó **không đủ**. Số đo cụ thể:

**Bảng 1.3. Đặt ngưỡng ở đâu thì chặn được gì**

| Ngưỡng tin cậy | Chặn được bao nhiêu % ảnh không phải lá | Chặn oan bao nhiêu % ảnh test PlantVillage |
|---|---|---|
| 0,50 | 68,8 % | 0,2 % |
| 0,60 | 81,2 % | 1,2 % |
| 0,70 | 87,5 % | 2,2 % |
| 0,80 | 87,5 % | 3,8 % |
| **0,90** | **100 %** | **9,2 %** |
| 0,95 | 100 % | 30,0 % |

Đọc bảng này cho đúng: muốn chặn hết ảnh rác thì phải đặt ngưỡng 0,90, và khi đó
**9,2 % ảnh lá thật hợp lệ cũng bị từ chối oan**. Đó là cái giá không nhỏ. Còn đặt
ở 0,80 cho an toàn thì mảnh carton 84,5 % vẫn lọt qua.

Đây chính là điều issue #47 đã tự cảnh báo ở mục "Gợi ý triển khai" — mạng nơ-ron
nổi tiếng tự tin quá mức. Số đo trên là bằng chứng cụ thể của chính nhóm cho câu
cảnh báo đó, và rất đáng đưa vào báo cáo.

### 1.4. Hai tín hiệu khác đo được, tách tốt hơn độ tin cậy

**(a) Điểm năng lượng (energy score)** = `−logsumexp(logits)`. Không chuẩn hoá về
tổng 1 nên giữ được thông tin về **độ lớn tuyệt đối** của logit — thứ mà softmax
bỏ mất. Ảnh lạ thì mọi logit đều nhỏ, energy cao.

| Ngưỡng energy | Chặn được % ảnh không phải lá | Chặn oan % ảnh test |
|---|---|---|
| > −3,34 | **100 %** | **5,0 %** |
| > −2,67 | 93,8 % | 1,0 % |

Ở mức chặn 100 %, energy chỉ mất 5,0 % ảnh hợp lệ so với 9,2 % của ngưỡng tin
cậy — tốt hơn gần gấp đôi, mà chi phí cài đặt bằng nhau (một dòng `torch.logsumexp`).

**(b) Cường độ Grad-CAM trước khi chuẩn hoá.** Đây là phát hiện đáng giá nhất của
buổi rà soát, vì nó vừa là một lỗi thiết kế thật, vừa giải thích đúng cái triệu
chứng "khoanh vùng bừa" mà Bảo nhìn thấy.

[`model/src/xai/gradcam.py:95-99`](model/src/xai/gradcam.py#L95-L99) chuẩn hoá
min-max bản đồ nhiệt **cho từng ảnh một**:

```python
cam = (cam - cam_min) / (cam_max - cam_min + 1e-8)
```

Hệ quả: một CAM phẳng lét, yếu ớt, hoàn toàn vô nghĩa cũng bị **kéo giãn** thành
đúng dải 0..1, rồi vượt ngưỡng `HEATMAP_THRESHOLD = 0.5` của backend, rồi được vẽ
elip lên ảnh. Bước chuẩn hoá xoá sạch thông tin "bản đồ nhiệt này mạnh hay yếu",
chỉ còn giữ lại hình dạng tương đối.

Số đo cụ thể trên ảnh nền xám trơn: **79,6 % diện tích ảnh** vượt ngưỡng 0,5 và
được đưa vào khoanh vùng — trong khi giá trị CAM thô cao nhất chỉ là **0,047**.

**Bảng 1.4. Giá trị CAM thô cao nhất (trước chuẩn hoá)**

| Nhóm ảnh | Nhỏ nhất | Trung vị | Lớn nhất |
|---|---|---|---|
| 11 ảnh không phải lá | 0,035 | 0,072 | 0,267 |
| 300 ảnh test PlantVillage | **0,135** | 0,294 | 0,858 |
| 3 ảnh lá thực địa | 0,199 | 0,732 | 0,732 |

Hai nhóm **gần như không chồng lấn**: ảnh PlantVillage yếu nhất (0,135) vẫn mạnh
hơn trung vị nhóm ảnh rác (0,072) gần gấp đôi. Đặt ngưỡng ở 0,20 chặn được 72,7 %
ảnh rác.

**Điểm hay nhất của tín hiệu này: dùng nó KHÔNG cần sửa hợp đồng dùng chung.**
`Prediction.heatmap` đã cho phép giá trị `None`, và cả hai phía đã xử lý sẵn:

- [`diagnosis_service.py:49`](backend/app/services/diagnosis_service.py#L49) — `heatmap is None` thì bỏ qua bước vẽ overlay
- [`explain.py:105`](backend/app/services/xai/explain.py#L105) — `heatmap is None` thì `ratio = 0.0`, rơi vào nhánh `ratio < MIN_REGION_RATIO` và sinh đúng câu *"không khoanh được vùng nào đủ rõ trên ảnh. Nên chụp lại gần hơn, đủ sáng…"*

Nghĩa là chỉ cần `predictor.py` trả `heatmap = None` khi CAM thô quá yếu, thì hành
vi đúng xuất hiện ngay, **không cần Học sửa một dòng nào**, không cần thêm trường
vào `Prediction`, không cần báo trước ai. Đúng ranh giới kiến trúc mà `CLAUDE.md`
đã dựng — và là ví dụ tốt cho thấy ranh giới đó có giá trị thật.

### 1.5. Cách sửa đúng, không phải cách sửa tạm

Ba tín hiệu trên đều là **chốt hậu kiểm** — chúng đoán "ảnh này lạ" từ phản ứng của
một mô hình chỉ biết 10 loại lá bệnh. Chúng giảm nhẹ triệu chứng chứ không chữa
gốc, và cả issue #47 lẫn `CLAUDE.md` đều đã nói đúng điều đó.

Cách chữa gốc là **một bộ phân loại riêng đứng trước**, quyết định "có phải lá cà
chua hay không" trước khi mô hình bệnh được gọi. `CLAUDE.md` đã mô tả kiến trúc
này ở mục mở rộng phạm vi quả (nhánh `khác` của bộ định tuyến 3 lớp lá/quả/khác,
issue **#71**).

**Đề xuất quan trọng nhất của tài liệu này: tách nhánh `khác` ra khỏi phạm vi quả.**

Lý do:

- Issue #71 đang gắn Mốc 6, nhãn `trang-thai:cho-cong-15-09`, tức là **bị chặn bởi
  cổng go/no-go còn 5 ngày nữa**. Nếu cổng đó cho kết quả "bỏ phần quả" thì #71 bị
  bỏ theo, và vấn đề 2 **không còn ai xử lý ngoài một ngưỡng tin cậy**.
- Nhưng vấn đề 2 **không liên quan gì tới bệnh trên quả**. Nó là lỗi của luồng lá,
  tồn tại ngay hôm nay, trên hệ thống hiện tại.
- Bộ phân loại **2 lớp** (lá cà chua / không phải) rẻ hơn hẳn bộ 3 lớp: không cần
  một tấm ảnh quả nào. Ảnh lá đã có sẵn 18.160 tấm; chỉ cần thu ~300–500 ảnh "không
  phải lá cà chua", mà loại ảnh này lấy dễ hơn ảnh bệnh rất nhiều — chụp bàn, ghế,
  tay, sàn nhà, lá cây khác, ảnh chụp màn hình, và **chính các ảnh Bảo đã chụp thử
  app**. Huấn luyện một EfficientNet-B0 nhị phân trên bộ đó là bài toán dễ, vài
  phút GPU.
- Việc này còn dùng luôn được cho phần quả nếu qua cổng: bộ 2 lớp mở rộng thành 3
  lớp chỉ là thêm dữ liệu, không phải làm lại.

Nói ngắn: **giữ nhánh `khác`, bỏ điều kiện phải làm phần quả mới có nó.**

---

## 2. Vấn đề 1 và 3 — độ chính xác thực tế khoảng 80 %

Gộp hai vấn đề này vì vấn đề 3 ("có nên đổi mô hình khác không") chỉ trả lời được
sau khi biết vì sao vấn đề 1 xảy ra.

### 2.1. Trước hết: con số 80 % hiện chưa đo được

Cần nói thẳng điều này. Con số ~80 % là **cảm nhận khi dùng thử app**, không phải
một phép đo. Hiện trong repo:

- `model/data/field/` **rỗng** — chưa có tập ảnh thực địa nào
- Chỉ có 3 ảnh Bảo tải lên qua app, mà 2 trong 3 là trùng nhau → thực chất **2 ảnh**
- Không có nhãn đúng đi kèm bất kỳ ảnh nào

Với 2 ảnh thì không thể nói accuracy là 80, 60 hay 95 %. **Không thể sửa thứ chưa
đo được** — đây là lý do việc số 1 trong kế hoạch là đo, chứ không phải sửa.

Dù vậy, hai ảnh đó cũng đã nói được một điều: ảnh thực địa #1 (phiến lá xanh đậm,
nhìn bằng mắt không thấy dấu bệnh rõ) bị kết luận **Đốm lá vi khuẩn, 95,3 % tin
cậy**. Sai với độ tin cậy rất cao, trên ảnh chụp thật — đó đúng là dấu hiệu kinh
điển của domain gap, không phải của một mô hình yếu.

### 2.2. Đã loại trừ được nguyên nhân "học tắt theo nền"

Đây là nghi vấn đáng ngại nhất, vì `CLAUDE.md` đã cảnh báo dựa trên bài **A2** —
có người huấn luyện **chỉ bằng 8 pixel nền** PlantVillage mà vẫn đạt 49 % (đoán mò
2,63 %). Nếu mô hình của nhóm cũng vậy thì toàn bộ phần XAI mất giá trị.

Đã tái hiện đúng thí nghiệm đó trên mô hình của nhóm: 300 ảnh test (30 ảnh × 10
lớp), bốn điều kiện ảnh vào.

**Bảng 2.1. Mô hình dựa vào lá hay dựa vào nền?**

| Điều kiện ảnh vào | Accuracy | Độ tin cậy trung vị |
|---|---|---|
| Ảnh đầy đủ (đối chứng) | **99,3 %** | 97,3 % |
| **Chỉ 4 góc nền**, ghép lại (không có lá) | **18,7 %** | 57,1 % |
| Che tâm ảnh bằng xám (xoá lá, giữ viền nền) | 28,0 % | 50,4 % |
| **Chỉ giữ tâm ảnh** (bỏ hết viền nền) | **97,3 %** | 96,5 % |
| *Đoán mò* | *10,0 %* | — |

**Kết luận: mô hình không học tắt theo nền.** Hai dòng quan trọng:

- Bỏ hết nền đi, mô hình vẫn đạt **97,3 %** → nó thực sự đọc phiến lá.
- Chỉ đưa nền, mô hình rơi về **18,7 %**, mà 84 % trong số đó dồn hết vào một lớp
  duy nhất là `healthy`. Lớp `healthy` chiếm 1/10 tập mẫu, nên riêng việc dồn về
  `healthy` đã tự sinh ra ~10 % "đúng" một cách máy móc. Trừ phần đó ra, phần còn
  lại **xấp xỉ mức đoán mò**.

So với 49 % của bài A2, con số 18,7 % (thực chất ~ đoán mò) là **kết quả tốt và
bảo vệ được**. Nguyên nhân hợp lý: nhóm dùng `random_resized_crop_scale: [0.7, 1.0]`
và `color_jitter` khá mạnh, hai phép này phá vỡ tương quan giữa nền và nhãn ngay
trong lúc huấn luyện. Đáng viết vào báo cáo như một quyết định có ích ngoài dự tính.

> Lưu ý khi trích: đây là biến thể của A2, **không phải** tái hiện y nguyên. A2
> huấn luyện lại mô hình chỉ bằng pixel nền; phép thử ở đây giữ nguyên mô hình đã
> huấn luyện rồi bịt/cắt ảnh đầu vào. Hai cách đo hai thứ khác nhau — A2 đo "nền có
> mang thông tin nhãn không", còn cách ở đây đo "mô hình này có dùng nền không".
> Phải ghi rõ khác biệt đó, đừng viết là đã lặp lại A2.

### 2.3. Vậy nguyên nhân là gì — và vì sao đổi kiến trúc không giúp được

Ghép ba số đo lại:

| Bằng chứng | Ý nghĩa |
|---|---|
| Test PlantVillage 99,75 % (mẫu 400 ảnh, khớp 99,60 % trong báo cáo) | Mô hình đã học rất tốt **phân phối PlantVillage** |
| Bỏ nền vẫn 97,3 % | Nó đọc đúng chỗ cần đọc, không ăn may theo nền |
| Ảnh thực địa: sai với 95,3 % tin cậy | Nó **không biết mình đang ở ngoài vùng đã học** |

Ba dòng này chỉ về đúng một nguyên nhân: **domain gap** — chênh lệch giữa phân phối
ảnh huấn luyện và ảnh thật. PlantVillage chụp lá đơn, ngắt rời, đặt ngay ngắn trên
nền đồng nhất, ánh sáng phòng thí nghiệm. Ảnh Bảo chụp: lá còn nguyên cụm, nền bìa
carton hoặc xi măng, có bóng đổ, nắng ngoài trời.

Từ đó trả lời trực tiếp câu hỏi 3:

> **Đổi sang EfficientNet-B3, ResNet50 hay Vision Transformer sẽ gần như không cải
> thiện được gì cho vấn đề Bảo đang gặp.**

Lý do: accuracy trên PlantVillage đã là 99,60 %. Kiến trúc mạnh hơn cùng lắm đưa
con số đó lên 99,7–99,8 % — tức là sửa được thêm vài ảnh trong 2.719 ảnh của một
tập test **mà bản thân tập test đó không phản ánh điều kiện thực tế**. Phần bị mất
nằm ở chỗ khác hẳn: ở khoảng cách giữa hai phân phối ảnh. Đổi backbone không thu
hẹp khoảng cách đó.

Đây cũng là chỗ dễ bị hỏi vặn khi bảo vệ, nên xin nói rõ cách trả lời: *"Nhóm không
chọn cách đổi kiến trúc vì đã đo và biết điểm nghẽn không nằm ở năng lực mô hình.
Nhóm có chạy so sánh kiến trúc (#19) nhưng dùng nó làm phần đánh giá trong báo cáo,
không dùng làm cách sửa lỗi."*

### 2.4. Những cách thật sự có tác dụng, xếp theo tỉ lệ hiệu quả trên công sức

| Ưu tiên | Cách | Vì sao có tác dụng | Công sức |
|---|---|---|---|
| **1** | **Đo domain gap bằng bộ H2 PlantDoc** — 744 ảnh, 8/10 lớp trùng (**#49**) | Biến "khoảng 80 %" thành một con số có nguồn trích dẫn được. Mọi việc sau đều cần con số này làm mốc. ⚠️ **Nguồn đã đổi từ H1 sang PlantDoc ngày 15/09** — xem mục 5.2 | Nửa buổi, không phải đi chụp |
| **2** | **Cắt lá trước khi phân loại** (**#93**) | Tấn công đúng gốc: phần lệch giữa hai phân phối chủ yếu là **nền**. Bỏ nền đi thì hai phân phối gần nhau lại. Bảng 2.1 đã chứng minh: chỉ giữ tâm ảnh vẫn 97,3 %. Dùng chung hạ tầng với bộ phát hiện lá ở mục 1.5 | Trung bình |
| **3** | **Tăng augmentation mô phỏng điều kiện đồng ruộng** — thay nền ngẫu nhiên, bóng đổ, mờ nhoè, nắng gắt (**#50** hướng 1) | Dạy mô hình bỏ qua nền ngay trong lúc học. Rẻ vì không cần dữ liệu mới | Thấp — chỉnh config + huấn luyện lại 30 phút |
| **4** | **TTA — suy luận nhiều biến thể rồi lấy trung bình** (**#94**) | Thường được thêm vài phần trăm trên dữ liệu lệch phân phối, không cần huấn luyện lại gì | Thấp, nhưng đắt lên 3–4× thời gian suy luận |
| **5** | **Tinh chỉnh (fine-tune) bằng phần `train` của PlantDoc, hoặc H3** (**#50** hướng 2) | Cách trực tiếp nhất để kéo mô hình về phân phối thật. ⚠️ **Nguồn đã đổi hai lần** — xem mục 5.1 (ảnh tự chụp #20 không thực hiện được) và mục 5.2 (H1 bị loại). Ranh giới phải giữ: huấn luyện chỉ trên `train`, đo trên `test`, và con số chính của #49 đo **trước** khi fine-tune nên vẫn đúng | Cao |
| 6 | So sánh kiến trúc (**#19**) | **Để báo cáo, không phải để sửa lỗi.** Xem 2.3 | 4 lượt × 25 phút |

⚠️ **Thứ tự này đã đổi so với bản đầu của tài liệu.** Ban đầu "tinh chỉnh bằng ảnh thực
địa" xếp thứ 3 vì là cách hiệu quả nhất. Sau ràng buộc ngày 10/09 (không liên hệ được nhà
vườn, xem mục 5.1) nó tụt xuống thứ 5: không mất hẳn — vẫn làm được bằng bộ công khai —
nhưng không còn là hướng rẻ nhất nữa. Ba việc phía trên nó đều **không cần một tấm
ảnh mới nào**, nên phải làm hết chúng trước.

Về việc số 6, nhắc lại cái bẫy `CLAUDE.md` đã ghi: `configs/default.yaml` đặt
`image_size: 224` cho mọi kiến trúc, mà EfficientNet-B3 thiết kế cho 300. Chạy B3 ở
224 rồi kết luận "B3 không hơn B0" là **kết luận không công bằng** — phải ghi rõ,
hoặc chạy B3 ở đúng 300.

### 2.5. Tiền kiểm cho #17 — Grad-CAM có rơi đúng lá không

`CLAUDE.md` xếp **#17 là cổng kiểm soát của cả đề tài**, nên đã đo định lượng sơ bộ
trước: 200 ảnh test (20 ảnh × 10 lớp), mặt nạ lá xấp xỉ bằng ngưỡng Otsu trên kênh
độ bão hoà màu.

**Bảng 2.2. Bao nhiêu phần bản đồ nhiệt nằm trong lá**

| Lớp | Khối lượng heatmap trong lá | Diện tích lá | Mức tập trung | Điểm nóng nhất nằm trong lá |
|---|---|---|---|---|
| `bacterial_spot` | 61,9 % | 44,9 % | 1,38× | 100 % |
| `early_blight` | 56,1 % | 40,9 % | 1,37× | 85 % |
| `late_blight` | 60,5 % | 30,3 % | 2,00× | 90 % |
| `leaf_mold` | 72,9 % | 47,9 % | 1,52× | 90 % |
| `septoria_leaf_spot` | 57,3 % | 38,5 % | 1,49× | 80 % |
| `spider_mites` | 64,3 % | 31,4 % | 2,05× | 85 % |
| `target_spot` | 51,5 % | 35,8 % | 1,44× | 80 % |
| `yellow_leaf_curl_virus` | 70,8 % | 36,4 % | 1,94× | 95 % |
| `mosaic_virus` | 55,7 % | 24,5 % | 2,27× | 95 % |
| **`healthy`** | **42,2 %** | 29,9 % | 1,41× | **55 %** |
| **Tổng** | **59,3 %** | **36,1 %** | **1,65×** | **86 %** |

Cách đọc cột "mức tập trung": nếu bản đồ nhiệt rải đều khắp ảnh thì khối lượng
trong lá sẽ đúng bằng diện tích lá, tức 1,00×. Đo được 1,65× nghĩa là Grad-CAM
**có** ưu tiên phiến lá, hơn mức ngẫu nhiên rõ rệt ở cả 10 lớp.

Nhưng chưa thể gọi là đạt hẳn:

- **40,7 % khối lượng bản đồ nhiệt vẫn rơi ra ngoài lá.**
- 18 % số ảnh có dưới một nửa khối lượng nằm trong lá.
- 14 % số ảnh có **điểm nóng nhất rơi hẳn ra nền**.
- Lớp `healthy` kém nhất, đúng như issue #17 dự đoán: chỉ 42,2 % khối lượng trong
  lá, điểm nóng nhất nằm trong lá chỉ 55 % — gần như tung đồng xu. Cũng dễ hiểu về
  mặt bản chất: lá khoẻ **không có vết bệnh nào** để chỉ vào, nên Grad-CAM không có
  chỗ neo. Cần ghi rõ hạn chế này vào báo cáo thay vì tìm cách che.

Một phần nguyên nhân là độ phân giải: tầng chập cuối của B0 chỉ **7×7** ô cho ảnh
224×224, mỗi ô phủ 32×32 pixel. Rìa lá chắc chắn bị "tràn" sang nền ở độ thô đó.
Đây là căn cứ định lượng cho #16 (Grad-CAM++), và cũng khớp với thứ tự `CLAUDE.md`
đã chốt: **làm #17 trước #16**, vì nét hơn mà sai chỗ thì vô nghĩa.

> Giới hạn của phép đo này, phải nói rõ khi trích: mặt nạ lá là **xấp xỉ tự động**
> bằng ngưỡng màu, không phải khoanh tay. Các con số trên dùng để **định hướng**
> #17, tuyệt đối không thay thế #17 — việc xem bằng mắt 5 ảnh × 10 lớp vẫn phải làm,
> vì chỉ mắt người phân biệt được "rơi vào vết bệnh" với "rơi vào phiến lá nhưng chỗ
> lành".

---

## 3. Vấn đề 4 — báo cáo tổng quan cho giảng viên

Trong repo **đã có sẵn hai báo cáo** khá đầy đủ, cần kiểm lại xem có phải giảng
viên đang cần đúng thứ đã có hay không trước khi viết mới:

| File | Nội dung | Dung lượng |
|---|---|---|
| `bao-cao-huan-luyen-mo-hinh.md` | Số liệu huấn luyện, chỉ số đánh giá, ma trận nhầm lẫn, phân tích lỗi, giải thích thuật ngữ cho người không chuyên | 638 dòng |
| `bao-cao-mo-hinh-grad-cam-xai.md` | Lý do chọn kiến trúc, cơ sở lý thuyết XAI, Grad-CAM, đối chiếu 7 bài báo đã đọc | ~800 dòng |

Hai file này cộng lại đã che gần hết một "báo cáo tổng quan về công việc huấn
luyện". Thiếu ba thứ:

1. **Chưa có phần nào nói về vấn đề 2** (ảnh không phải lá) — mà đây lại là chỗ hay
   nhất để nói, vì "hệ thống biết khi nào không nên trả lời" đúng tinh thần XAI.
2. **Chưa có số liệu của mục 2.2** (mô hình không học tắt theo nền) — đây là câu trả
   lời trực tiếp cho phản biện mạnh nhất về PlantVillage, đang bỏ trống.
3. **Chưa có con số domain gap của chính nhóm** — phải chờ #49.

Đề xuất: **không viết báo cáo thứ ba.** Thay vào đó bổ sung ba mục trên vào
`bao-cao-huan-luyen-mo-hinh.md`, rồi làm thêm một bản **tóm tắt 3–4 trang** để nộp
cho giảng viên, trỏ về hai báo cáo chi tiết làm phụ lục. Giảng viên cần nắm được
mạch việc, không cần đọc 1.400 dòng.

**✅ Bảo đã chốt (10/09/2026): làm bản tóm tắt tiến độ 3–4 trang.** Không viết báo
cáo thứ ba, không viết chương chuẩn khoá luận lúc này — loại đó thuộc issue #53–#58
(Mốc 5, bắt đầu 15/10). Bản tóm tắt sẽ trỏ hai báo cáo chi tiết làm phụ lục.

---

## 4. Thu thêm được: hai số đo ngoài phạm vi câu hỏi

### 4.1. Issue #18 — tốc độ suy luận trên CPU: coi như đã có số

Đo `predict()` **đầy đủ** (mở ảnh 1280×1280, biến đổi, suy luận, Grad-CAM, phóng
bản đồ nhiệt về cỡ gốc) — tức đúng thứ backend chịu, không phải chỉ forward pass:

| Thiết bị | Trung vị | p95 |
|---|---|---|
| GPU (RTX 4060 Ti) | 90,9 ms | 102,7 ms |
| **CPU, 4 luồng** | **214,7 ms** | 263,3 ms |
| CPU, 2 luồng | 238,5 ms | 261,2 ms |
| CPU, 16 luồng (mặc định) | **452,0 ms** | 497,3 ms |

Hai điều rút ra:

- **Rủi ro tốc độ trên CPU không thành vấn đề.** 215 ms cho một lần chẩn đoán là
  hoàn toàn chấp nhận được với luồng người dùng thật — họ vừa bấm chụp ảnh xong. Có
  thể hạ mức rủi ro số 2 trong `CLAUDE.md`.
- **Phát hiện đáng chú ý: 16 luồng chậm gấp đôi 4 luồng.** Đây là hiện tượng tranh
  chấp luồng cổ điển — với mô hình nhỏ như B0 và batch bằng 1, chi phí đồng bộ giữa
  16 luồng lớn hơn phần tính toán chia ra được. Torch mặc định lấy hết số lõi nên
  đang chạy ở cấu hình **tệ nhất**. Thêm `torch.set_num_threads(4)` là rút một nửa
  độ trễ, đổi một dòng code.

  Cần đo lại trên đúng máy sẽ dùng hôm bảo vệ (#51 — OP-01) vì con số tối ưu phụ
  thuộc số lõi thật. Và lưu ý: dòng này thuộc `model/`, nhưng nó thay đổi hành vi
  của tiến trình uvicorn (`loader.py` import code `model/` **trong cùng tiến trình**,
  theo quyết định IN-01) → phải nói với Học trước khi đặt.

### 4.2. Mobile không làm hỏng ảnh — đã loại trừ

Đã kiểm giả thuyết "app nén ảnh quá mạnh nên mô hình đoán kém":

- [`capture_screen.dart:70`](mobile/lib/screens/capture/capture_screen.dart#L70) — `maxWidth: 1600, imageQuality: 90`
- [`analyzing_screen.dart:76`](mobile/lib/screens/capture/analyzing_screen.dart#L76) — nén lại `quality: 82, minWidth/minHeight: 1280`
- Backend giữ tối đa 1280 px (`MAX_IMAGE_DIMENSION`), xoay đúng chiều theo EXIF

Chuỗi này lành mạnh. Ba ảnh trong `storage/uploads/` là 256×256 nhưng đó là ảnh thử
qua công cụ dòng lệnh, không phải từ app. **Không phải nguyên nhân.**

---

## 5. Kế hoạch xử lý — gắn theo issue GitHub

> **Bản đầu của mục này (10/09/2026) tự đánh số A1–A4, B1–B6, C1–C6, D1–D3.** Cách đó
> sai: `CLAUDE.md` ghi rõ *"Toàn bộ việc còn lại nằm trong issue GitHub... Đây là nguồn
> duy nhất để biết còn phải làm gì — đừng lập bảng công việc song song ở chỗ khác."*
> Một hệ đánh số thứ hai chồng lên số issue đúng là thứ bị cấm ở đó.
>
> Đếm lại thì trong 19 việc của bản đầu, **13 việc đã có issue sẵn** — chỉ 6 việc là mới.
> Sáu việc đó nay đã thành issue thật (**#90–#95**, tạo ngày 10/09/2026), nên mục này
> chuyển hoàn toàn sang đánh số theo issue. **Số issue là danh tính duy nhất của một việc.**
>
> Giá trị của buổi rà soát vì vậy không phải "có kế hoạch mới", mà là **đổi thứ tự ưu
> tiên của các issue đã có** — và số đo đổi thứ tự đó ở hai chỗ đáng kể, xem bảng 5.4.

### 5.1. Ràng buộc mới: không chụp được ảnh đồng ruộng (chốt 10/09/2026)

Nhóm **không liên hệ được nhà vườn để xin phép chụp ảnh** và không còn thời gian cho việc
này. Đây là ràng buộc thật, không phải trì hoãn.

Hệ quả trực tiếp lên bốn issue đang có:

| Issue | Trước | Nay |
|---|---|---|
| **#20** FD-01 chụp 50–100 ảnh lá thật ngoài đồng | Việc chặn, làm trong tháng 9 | **Hoãn vô thời hạn** — không thực hiện được |
| **#21** FD-02 gán nhãn ảnh thực địa | Chặn bởi #20 | **Hoãn theo #20** |
| **#48** FD-03 xếp ảnh thực địa vào `data/field/` | Chặn bởi #21 | **Hoãn theo #20** |
| **#49** FD-04 đánh giá mô hình trên ảnh thực địa | Dùng ảnh tự chụp **hoặc** bộ H1 | Chỉ còn đường bộ công khai. ⚠️ Ngày 15/09 **H1 bị loại**, chuyển sang **H2 (PlantDoc)** — xem mục 5.2 |
| **#50** FD-05 cải thiện nếu accuracy rớt | Hướng 2 = fine-tune bằng ảnh tự chụp | Hướng 2 phải đổi nguồn: phần **`train` của PlantDoc** hoặc **H3 (Taiwan)**, tách khỏi phần dùng để đo (mục 5.2) |

**Rủi ro số 1 trong `CLAUDE.md` (domain gap) KHÔNG bị bỏ trống.** Đây là điểm quan trọng
nhất của mục này. Ba bộ dữ liệu đồng ruộng công khai trong `model/research/` thay thế được
hoàn toàn phần ảnh tự chụp:

| Mã | Bộ | Quy mô | Vai trò |
|---|---|---|---|
| ~~**H1**~~ | ~~Imtiaz et al., Data in Brief 2025 (Mendeley)~~ | ~~731 ảnh, 7 lớp~~ | ❌ **ĐÃ LOẠI ngày 15/09/2026** — nhãn không tra được, ảnh bị nhân bản. Toàn bộ căn cứ ở mục 5.2 |
| **H2** | PlantDoc, CoDS-COMAD 2020 (GitHub `pratikkayal/PlantDoc-Dataset`) | **744 ảnh cà chua dùng được / 8 lớp** — tự đếm 15/09, xem bảng ở mục 5.2 | **Tập đo chính.** Phần `test` (69 ảnh) để so trước/sau, phần `train` (675 ảnh) để fine-tune ở #50 |
| **H3** | Taiwan tomato leaves | 622 ảnh, 6 lớp, 3 lớp trùng | Nguồn fine-tune bổ sung, nếu #50 cần thêm dữ liệu. Ảnh có bóng đổ, nhiều lá chồng, nền lộn xộn |

Và cần nói rõ để không hiểu thành một lời xin lỗi: **PlantDoc cho 744 ảnh trên 8 lớp, gấp
7–15 lần con số 50–100 ảnh tự chụp theo kế hoạch ban đầu**, do một nhóm độc lập thu thập và
công bố tại hội nghị có phản biện, nên **trích dẫn được**. Về mặt quy mô đây là lựa chọn tốt
hơn kế hoạch cũ. Hai chỗ thật sự mất:

- **Tính địa phương** — không có ảnh cà chua Đà Lạt, nên không kết luận được gì riêng cho
  điều kiện canh tác ở đây.
- **PlantDoc là ảnh thu từ Internet**, không phải ảnh tác giả tự chụp ngoài đồng. Phép thử
  domain shift vẫn hợp lệ, nhưng **không được gọi là "ảnh đồng ruộng"** trong báo cáo.

> ⚠️ Đoạn trên ban đầu ghi H1 và nói "đó là hạn chế duy nhất". Sau ngày 15/09 thì cả nguồn
> dữ liệu lẫn câu đó đều phải sửa — xem mục 5.2.

Điều **không** bị ảnh hưởng: **#91** (thu ảnh không phải lá cà chua) hoàn toàn làm được —
chụp bàn, ghế, tay, sàn nhà, lá cây khác tại nhà trong khoảng một giờ, không cần nhà vườn
nào. Đừng để nó bị hoãn lây theo #20.

### 5.2. Bộ H1 đã bị LOẠI — kiểm chứng ngày 15/09/2026

Mục 5.1 ở trên chốt rằng H1 là đường duy nhất còn lại để có số domain gap. **Câu đó
nay đã sai.** Ngày 15/09 tôi tải bộ H1 về để bắt đầu #49 và phát hiện bộ này **không
dùng được** cho mục đích của đề tài. Ghi lại đầy đủ vì đây là căn cứ cho việc đổi
nguồn dữ liệu, và bản thân nó là nội dung đáng đưa vào báo cáo.

Bộ tải từ Mendeley (DOI `10.17632/bpfd9cns5g.2`), 48,5 MB, 1.420 file `.jpg` và 689
file `.txt`. Tên file có dạng `IMG_0210_JPG.rf.<băm>.jpg` — dấu hiệu của bản xuất
Roboflow, tức bộ này là **dữ liệu phát hiện vật thể (object detection) theo định dạng
YOLO**, không phải bộ phân loại chia thư mục theo lớp như PlantVillage.

**Bốn phát hiện, xếp theo mức nghiêm trọng:**

**(1) Không thể biết class ID nào là bệnh nào.** Bản xuất Roboflow bình thường luôn
kèm `data.yaml` ghi tên lớp theo thứ tự. Bộ này **không có một file nào ngoài `.jpg`
và `.txt`** — đã đếm, đúng 0 file khác. Vậy nên con số `0`…`6` ở đầu mỗi dòng nhãn
không có nghĩa nào tra được. Đã thử khôi phục bằng cách đếm số hộp mỗi class ID rồi
đối chiếu bảng phân bố lớp trong bài báo:

| class ID | Số hộp đo được | Lớp thứ tương ứng trong bảng bài báo | Bài báo ghi |
|---|---|---|---|
| 0 | 84 | Early Blight | 325 |
| **1** | **1.177** | Black Spot | 254 |
| 2 | 179 | Late Blight | 202 |
| 3 | 303 | Leaf Mold | 194 |
| 4 | 93 | Bacterial Spot | 233 |
| 5 | 47 | Target Spot | 213 |
| 6 | 395 | Healthy | 200 |
| **Tổng** | **2.278** | | **1.621** |

Không khớp theo bất kỳ cách nào. Đã thử cả thứ tự bảng trong bài báo và thứ tự chữ
cái (mặc định của Roboflow). Riêng class 1 chiếm **1.177 hộp, tức 51,7 %** toàn bộ, trong
khi lớp đông nhất mà bài báo ghi chỉ có 325 hộp. Tổng cũng lệch: 2.278 so với 1.621.

**(2) Không có nhãn phân loại cho từng ảnh.** Đề tài cần một nhãn/ảnh để chạy
`evaluate.py`. Trong 689 ảnh có file nhãn: **230 ảnh chứa hộp của từ hai lớp khác
nhau trở lên**, 19 ảnh không có hộp nào, chỉ 440 ảnh có đúng một lớp. Với 230 ảnh đa
lớp thì không có cách gán một nhãn duy nhất mà không tự bịa ra quy tắc.

**(3) Thư mục 731 ảnh không hề được chia theo lớp.** Bài báo viết *"organized into
seven types"*, nhưng trên Mendeley cả 731 file nằm **phẳng trong một thư mục**, không
có thư mục con nào.

**(4) Con số "731 ảnh" mà tài liệu của nhóm đang trích là số đã bị nhân bản.** Trong
1.420 file `.jpg` chỉ có **984 ảnh khác nhau về byte**, và truy theo tên ảnh gốc thì
chỉ còn **308 ảnh gốc** — có 163 ảnh gốc xuất hiện tới 6 bản. Thư mục "731 ảnh" tương
ứng đúng **302 ảnh gốc**. Nghĩa là quy mô thật của H1 nhỏ hơn con số công bố khoảng
2,4 lần.

> Nói cho chính xác, vì đây là chỗ dễ nói quá: **302 ảnh gốc vẫn nhiều hơn mốc 50–100 ảnh
> tự chụp** của kế hoạch cũ — khoảng 3–6 lần. Bản ngày 10/09 của mục 5.1 ghi H1 "gấp 7–14
> lần", tức con số đó bị thổi phồng khoảng hai lần vì đếm cả ảnh nhân bản. Nhưng **quy mô
> không phải là lý do loại H1** — một bộ 302 ảnh có nhãn đúng thì vẫn dùng được. **Lý do
> loại là phát hiện (1) và (2): nhãn không tra được.** Một bộ 731 ảnh mà không biết nhãn
> nào là bệnh gì thì dù lớn đến đâu cũng không dùng được.

**Vì sao phải loại thay vì đoán ánh xạ rồi chạy.** Nếu đoán thứ tự lớp rồi cứ chạy
`evaluate.py`, kết quả sẽ ra một con số accuracy **trông hoàn toàn bình thường** —
chẳng hạn 35 % — mà vô nghĩa, vì nhãn đối chiếu đã sai. Không có gì báo lỗi. Rồi con
số đó thành số domain gap chính thức của đề tài, vào báo cáo, vào slide. Đây đúng loại
lỗi mà `CLAUDE.md` cảnh báo ở cả hai chỗ: bất biến thứ tự lớp trong
`shared/data/tomato_diseases.json`, và cái bẫy "không đo lại bằng trí nhớ".

**Đây là nội dung đáng đưa vào báo cáo, không phải công toi.** Nhóm đã lấy một bộ dữ
liệu công bố trên tạp chí có phản biện, tự kiểm nhãn thay vì tin con số in trong bài,
và phát hiện bộ đó không dùng được cho bài toán phân loại. Đó là phần **đánh giá chất
lượng dữ liệu** — trả lời trực tiếp cho câu phản biện "nhóm chọn dữ liệu thế nào". Chi
phí thật: nửa ngày, đúng bằng ước lượng cũ cho #49.

**Đã thay bằng H2 (PlantDoc) — số liệu tự đếm ngày 15/09/2026:**

Đếm qua GitHub API trên repo `pratikkayal/PlantDoc-Dataset`, không trích lại từ bài
báo. PlantDoc là bộ **phân loại chia thư mục theo lớp**, tên thư mục viết rõ bằng chữ
nên **không phải đoán ánh xạ**:

| Thư mục PlantDoc | Khoá bệnh của nhóm | `train` | `test` |
|---|---|---|---|
| `Tomato leaf bacterial spot` | `bacterial_spot` | 101 | 9 |
| `Tomato Early blight leaf` | `early_blight` | 79 | 9 |
| `Tomato leaf late blight` | `late_blight` | 101 | 10 |
| `Tomato mold leaf` | `leaf_mold` | 85 | 6 |
| `Tomato Septoria leaf spot` | `septoria_leaf_spot` | 140 | 11 |
| `Tomato leaf yellow virus` | `yellow_leaf_curl_virus` | 70 | 6 |
| `Tomato leaf mosaic virus` | `mosaic_virus` | 44 | 10 |
| `Tomato leaf` | `healthy` | 55 | 8 |
| | **8 lớp dùng được** | **675** | **69** |
| `Tomato two spotted spider mites leaf` | `spider_mites` | **2** | **0** |
| *(không có thư mục)* | `target_spot` | — | — |

**Dùng được 8 trong 10 lớp, tổng 744 ảnh.** So với H1: 8 lớp thay vì 6, và nhãn tường
minh thay vì không tra được.

Ba điều phải ghi rõ, phát hiện trong lúc đếm:

- **`spider_mites` chỉ có 2 ảnh** trong `train`, 0 trong `test` → **loại khỏi phép đo**,
  không tính vào accuracy. Hai ảnh đó tên là `SpotSpeckBlightMite-1l4v879.jpg` và
  `comparing-diseases-4-canker-tomato-1y51ejs.jpg` — tên thứ hai nói về bệnh loét
  (canker), tức nhãn của chính nó cũng đáng nghi.
- **`target_spot` không có trong PlantDoc.** Mô hình vẫn trả về 10 lớp, nên phải xử lý
  bằng tham số `labels=` khi tính chỉ số, không được để sklearn tự suy ra (xem 5.5).
- ⚠️ **Bản chia `train`/`test` của chính PlantDoc có rò rỉ: 3 ảnh trùng byte tuyệt đối**
  (so bằng sha256 sau khi tải về, không phải bằng tên): `early-blight-septoria-ls-fig-3.jpg`,
  `tylcv-seminar-1-638.jpg` và `tomato_V8.jpg` nằm đồng thời ở cả hai bên. Phải bỏ khỏi
  `test` trước khi dùng cho phép so trước/sau ở #50.
- ⚠️ **`tomato_V8.jpg` nặng hơn hai ca kia: cùng một ảnh nhưng mang HAI NHÃN khác nhau** —
  `test/Tomato leaf bacterial spot` và `train/Tomato Septoria leaf spot`. Bản ghi lúc đầu
  ngày 15/09 chưa xác nhận được (hết hạn mức GitHub API); sau khi tải về và băm thì **đã
  xác nhận trùng byte tuyệt đối**. Không có cách biết nhãn nào đúng nên **loại hẳn** — giữ
  lại thì dù mô hình trả lời gì cũng có một nhãn gọi nó là sai.

**Cách dùng PlantDoc cho đúng — chỗ dễ sai nhất.** #50 hướng 2 định **fine-tune** bằng
PlantDoc. Nếu đo và huấn luyện trên cùng dữ liệu thì lặp lại đúng cái sai mà mục 5.1 đã
dặn về H1. Cách làm:

| Phép đo | Dữ liệu | Vì sao |
|---|---|---|
| **#49 — số domain gap chính** | **Toàn bộ 744 ảnh** (8 lớp) | Checkpoint hiện tại **chưa từng thấy một ảnh PlantDoc nào**, nên đo trên toàn bộ là hợp lệ và cho thống kê tốt nhất. Con số này **đúng vĩnh viễn**, kể cả sau khi #50 fine-tune |
| **#49 — mốc phụ** | Riêng 69 ảnh `test` | Để #50 có mốc "trước" trên **đúng những ảnh** sẽ dùng làm "sau" |
| Mốc so công bằng | Tập test PlantVillage, **lọc còn đúng 8 lớp đó** | So 10 lớp với 8 lớp là so lệch. Phải có hai con số cạnh nhau |
| **#50 hướng 2 — fine-tune** | 675 ảnh `train`, **đã bỏ 3 ảnh rò rỉ** | Đo lại trên 66 ảnh `test`, so với mốc phụ ở trên |

⚠️ **69 ảnh là ít** (còn 66 sau khi bỏ ảnh rò rỉ). Mỗi lớp chỉ 5–10 ảnh, nên con số trên
riêng tập `test` có sai số lớn — đo được khoảng tin cậy 95 % rộng tới **21 điểm**
(19,27–40,64 %). Phải ghi khoảng tin cậy, đừng trình bày như một con số chính xác. Đây
chính là lý do con số chính của #49 lấy trên cả 742 ảnh.

**Hạn chế của PlantDoc, phải ghi vào báo cáo:** ảnh **thu từ Internet**, không phải
ảnh tác giả tự chụp ngoài đồng. Vẫn là phép thử domain shift hợp lệ — nền lộn xộn,
nhiều lá chồng nhau, ánh sáng tự nhiên, khác hẳn PlantVillage — nhưng **không được gọi
là "ảnh đồng ruộng"**. PlantDoc cũng có tiếng là nhãn hơi nhiễu (hai ví dụ ở trên tự
chứng minh điều đó), nên phải xem mẫu bằng mắt và ghi lại những ảnh đáng nghi.

### ✅ Kết quả #49 — đã chạy xong ngày 15/09/2026

> **Báo cáo đầy đủ: `bao-cao-domain-gap.md`** (cùng thư mục này). Mục này chỉ ghi con số
> đầu và ba phát hiện đổi thứ tự việc; mọi bảng chi tiết, cách chạy lại và phần hạn
> chế đều ở tài liệu kia.

| Chỉ số | PlantVillage test (8 lớp, n=2.258) | **PlantDoc (8 lớp, n=740)** | Chênh |
|---|---|---|---|
| Accuracy | 99,60 % | **30,81 %** | **−68,79 điểm** |
| KTC 95 % | 99,24 – 99,79 % | 27,59 – 34,23 % | *không chồng lấn* |
| Macro-F1 | 0,9970 | 0,2331 | −0,7639 |
| Top-3 | 100,00 % | 62,70 % | −37,30 điểm |

**Vậy là con số "khoảng 80 %" ở mục 2.1 đã có câu trả lời, và nó thấp hơn nhiều: 30,81 %.**
Cảm nhận 80 % khi dùng thử app cao hơn thực tế — dễ hiểu, vì ảnh Bảo tự chụp là lá cận
cảnh trên nền phẳng, gần phân phối PlantVillage hơn PlantDoc nhiều.

Kết quả gần như **trùng khớp bài A1** (chính tác giả PlantVillage: 99,35 % → 31,40 %,
tụt 67,9 điểm — nhóm lệch 0,6 điểm). Đây là bằng chứng phép đo đúng, không phải một con
số lạ.

**Ba phát hiện đổi thứ tự việc — chi tiết ở `bao-cao-domain-gap.md` mục 3, 4, 5:**

1. **Mô hình dồn 85 % dự đoán vào 3 lớp** (`early_blight` 35,6 %, `late_blight` 33,2 %,
   `septoria_leaf_spot` 16,3 %). Không phải suy giảm đều mà **sụp về mấy lớp "tổng quát"**.
   Đáng lo nhất về mặt sản phẩm: **52 % lá khoẻ bị gọi là mốc sương muộn** — đảo chiều so
   với #15, nơi ca nguy hiểm là bỏ sót bệnh. Trên ảnh thật thì lỗi chủ yếu là **báo động giả**.
2. **Ngưỡng tin cậy KHÔNG cứu được** (mục 1.3 đã nghi, nay có số). Ở ngưỡng 0,90 hệ
   thống từ chối **85,4 %** ảnh thật, mà accuracy phần còn lại vẫn chỉ **56,5 %**, đồng
   thời chặn oan 8,5 % ảnh PlantVillage. → **#47 phải thu hẹp phạm vi**: dùng ngưỡng để
   chặn ảnh không phải lá, **đừng** kỳ vọng nó vá độ chính xác.
3. **Grad-CAM suy biến gần về mức ngẫu nhiên trên ảnh nền phức tạp**: mức tập trung tụt
   **1,58× → 1,02×**, điểm nóng nhất nằm trong lá chỉ **42 %** (PlantVillage 75 %). Đây
   là phát hiện nặng nhất vì nó chạm vào đóng góp chính của đề tài. ⚠️ Nhưng phép đo có
   hạn chế thật (mặt nạ lá bằng ngưỡng màu kém tin cậy trên nền thật) nên là **cảnh báo,
   chưa phải kết luận** → **#17 nâng ưu tiên và mở rộng: kiểm cả hai bộ, khoanh lá bằng tay.**

### 5.3. Sáu issue mới tạo ngày 10/09/2026

| Issue | Việc | Mốc | Mức | Trạng thái |
|---|---|---|---|---|
| **#90** | MD-11 · Không khoanh vùng khi bản đồ nhiệt Grad-CAM quá yếu | 2 | `muc:cao` | Làm được ngay |
| **#91** | MD-12 · Thu bộ ảnh không phải lá cà chua | 2 | `muc:chan` | Làm được ngay, **không cần nhà vườn** |
| **#92** | MD-13 · Huấn luyện bộ phân loại 2 lớp lá / không phải lá | 2 | `muc:cao` | Chặn bởi #91 |
| **#93** | MD-14 · Cắt vùng lá trước khi phân loại | 4 | `muc:thuong` | Chặn bởi #49 |
| **#94** | MD-15 · Thử test-time augmentation khi suy luận | 4 | `muc:tuy-chon` | Chặn bởi #49 |
| **#95** | DC-09 · Bản tóm tắt tiến độ huấn luyện mô hình nộp GVHD | 2 | `muc:cao` | Nên chờ #49 nếu kịp |

Ưu tiên đã nằm trong nhãn `muc:*` của GitHub, không cần bảng ưu tiên riêng ở đây.

### 5.4. Số đo hôm nay đổi thứ tự issue ở đâu

`CLAUDE.md` mục *"Việc tiếp theo, xếp đúng thứ tự"* đang ghi 5 việc. Đối chiếu với số đo:

| Thứ tự đang ghi | Issue | Số đo hôm nay nói gì |
|---|---|---|
| 1 | **#17** kiểm Grad-CAM bằng mắt | **Giữ nguyên.** Vẫn là cổng kiểm soát của cả đề tài. Mục 2.5 đã dựng số liệu định hướng và chỉ đúng chỗ đáng nghi (`healthy`, 14 % ảnh có điểm nóng ra ngoài lá) |
| 2 | **#49** đo trên ảnh đồng ruộng | **Giữ nguyên thứ tự, nhưng nguồn dữ liệu đã đổi** — H1 bị loại ngày 15/09, thay bằng PlantDoc (mục 5.2) |
| 3 | **#16** nâng Grad-CAM++ | Giữ nguyên thứ tự. Nay có căn cứ định lượng: tầng chập cuối 7×7, 40,7 % khối lượng heatmap rơi ra ngoài lá |
| 4 | **#18** đo tốc độ CPU | **Coi như đã có số** — 215 ms (4 luồng). Rút khỏi hàng chờ, chỉ còn phần đo lại trên máy demo khi #51 chốt máy |
| 5 | **#19** so kiến trúc | **Hạ cấp** — từ "cách sửa lỗi" thành "phần đánh giá cho báo cáo". Xem mục 2.3 |

Hai dòng cuối là chỗ buổi rà soát tiết kiệm được công: nếu cứ theo thứ tự cũ mà làm, khả
năng cao sẽ chạy #19 (4 lượt × 25 phút) để mong tăng accuracy — mà số đo cho thấy việc đó
**không giúp được gì** cho vấn đề đang gặp.

### 5.5. Thứ tự làm, theo issue

**Tuần 10/09 – 15/09, trước cổng go/no-go #64:**

> **Trạng thái thật tính tới hết ngày 15/09/2026:** chỉ #49 được bắt tay làm, và nửa ngày
> đầu tiên tiêu vào việc phát hiện bộ H1 không dùng được (mục 5.2). Ba việc #17, #90, #91
> **chưa bắt đầu**. Bảng dưới vì vậy là việc *còn phải làm*, không phải việc đã xong.

| Ưu tiên | Issue | Vì sao ở đây | Ước lượng |
|---|---|---|---|
| 1 | **#49** đo domain gap trên **PlantDoc** | Việc duy nhất biến "khoảng 80 %" thành con số trích dẫn được. #93, #94, #50 đều chặn bởi nó. Không cần chụp ảnh. ⚠️ Cần ba sửa đổi code trước — xem ngay dưới bảng | Nửa buổi |
| 2 | **#17** kiểm Grad-CAM bằng mắt, 5 ảnh × 10 lớp | Cổng kiểm soát của cả đề tài. Ưu tiên xem kỹ `healthy` và `spider_mites` | 2–3 giờ |
| 3 | **#90** không khoanh vùng khi CAM quá yếu | Chặn ngay triệu chứng nặng nhất. Rẻ nhất trong mọi việc ở đây, không cần Học sửa gì | 1 giờ |
| 4 | **#91** thu bộ ảnh không phải lá | Chặn #92 và chặn cả #47 trên thực tế. Làm được ngay | ~1 giờ |
| 5 | **#64** chốt cổng go/no-go | Đến hạn 15/09 | — |

> **Khi chốt #64:** nhánh `khác` **đã tách ra** thành #92, độc lập với phạm vi quả (mục 6).
> Phải ghi rõ điều này vào #64, để nếu kết quả là "bỏ phần quả" thì #71 bị bỏ mà #92 **không**
> bị bỏ theo.

**Ba chỗ trong code phải sửa trước khi #49 chạy được.** Cả ba đã xác định bằng cách đọc code
ngày 15/09, không phải phỏng đoán. Rủi ro của chúng không đồng đều — chỉ một chỗ báo lỗi, hai
chỗ còn lại **im lặng cho ra số sai**:

| # | Chỗ | Chuyện gì xảy ra nếu không sửa | Cách sửa |
|---|---|---|---|
| 1 | [`prepare.py:27-44`](model/src/data/prepare.py#L27-L44) — `scan_images()` ánh xạ tên thư mục qua `dir_to_key()`, chỉ nhận các thư mục `Tomato___*` của PlantVillage | Tên thư mục PlantDoc (`Tomato leaf bacterial spot`…) rơi hết vào `unknown_dirs` → **manifest rỗng**, không báo lỗi | Thêm bảng ánh xạ cho PlantDoc, hoặc đổi tên thư mục lúc tải về. Bảng ánh xạ đã có ở mục 5.2 |
| 2 | [`evaluate.py:114`](model/src/evaluation/evaluate.py#L114) — `classification_report()` **không** truyền `labels=` | sklearn tự suy nhãn từ `y_true ∪ y_pred` (8–10 lớp) rồi so với `target_names` (10 lớp) → **`ValueError`, sập thẳng**. Đây là chỗ duy nhất báo lỗi nên cũng là chỗ ít nguy hiểm nhất | Thêm `labels=list(range(len(keys)))`. Hai dòng ngay cạnh (`confusion_matrix`, `top_k_accuracy_score`) **đã** truyền `labels` — chỉ dòng này bị sót |
| 3 | `evaluate.py` mặc định ghi vào `outputs/` | **Ghi đè `report-test.json` và `confusion-matrix-test.png` của PlantVillage đang nằm trong Git** — mất số liệu gốc của #15 mà không báo gì | Bắt buộc truyền `--out-dir outputs/plantdoc` |

Kèm theo: macro-F1 phải tính **chỉ trên những lớp thật sự có mặt**. Để nguyên 10 lớp thì hai
lớp vắng (`target_spot`, `spider_mites`) đóng góp F1 = 0 và kéo macro-F1 xuống khoảng 20 % một
cách máy móc — con số đó không nói gì về mô hình. Phải báo cả hai: macro-F1 trên 8 lớp có mặt,
và ghi rõ hai lớp kia **không đo được**, chứ không phải "đo được 0".

⚠️ Sửa `evaluate.py` là **Bảo đã cho phép ngày 15/09/2026**. Sửa `prepare.py` nằm trong cùng
phạm vi #49.

**15/09 – 30/09 — xử lý vấn đề ảnh không phải lá cho tới gốc:**

| Issue | Việc | Ghi chú |
|---|---|---|
| **#92** | Huấn luyện bộ 2 lớp | Cách chữa gốc. Chặn bởi #91 |
| **#47** | Chốt ngưỡng bằng số liệu thật, nối vào backend | ⚠️ **Phần của Học.** Đề nghị dùng **energy** làm tín hiệu chính thay vì chỉ softmax: chặn 100 % ảnh rác chỉ mất 5,0 % ảnh hợp lệ, so với 9,2 % của ngưỡng tin cậy (bảng 1.3, 1.4) |
| **#26** | Màn riêng cho ca "không nhận ra lá" — không elip, không phần trăm | Phần của Học |

**Sau khi có số của #49 — xử lý độ chính xác thực tế:**

`#50` đặt mốc can thiệp là **rớt dưới ~70 %**. Chỉ khởi động nhóm này sau khi biết con số.

| Issue | Việc | Điều kiện |
|---|---|---|
| **#50** hướng 1 | Tăng augmentation mô phỏng đồng ruộng (thay nền ngẫu nhiên, bóng đổ, nắng gắt) | Rẻ nhất, thử trước |
| **#93** | Cắt vùng lá trước khi phân loại | Đánh đúng gốc domain gap. **Nay quan trọng hơn dự kiến** vì là hướng duy nhất không cần dữ liệu mới |
| **#94** | Test-time augmentation | Rẻ, không huấn luyện lại. Làm sau #93 để biết cải thiện đến từ đâu |
| **#50** hướng 2 | Fine-tune — nguồn là phần **`train` của PlantDoc** (675 ảnh) hoặc **H3**, không phải ảnh tự chụp | ⚠️ Chỉ huấn luyện trên `train`, chỉ đo trên `test`, và **bỏ 3 ảnh trùng byte** mà chính PlantDoc để lẫn giữa hai bên (mục 5.2). Con số chính của #49 đo **trước** khi fine-tune nên không bị ảnh hưởng; nhưng phép so trước/sau thì phải đúng cùng 66 ảnh. **Mốc "trước" đã có: 28,79 %** |
| **#19** | So kiến trúc B0 / ResNet18 / ResNet50 / B3 | **Làm để báo cáo, không phải để sửa lỗi** (mục 2.3). B3 phải chạy ở `image_size: 300` |
| **#18** + **#51** | Đặt `torch.set_num_threads(4)` sau khi chốt máy demo | Rút một nửa độ trễ CPU. ⚠️ Đổi hành vi tiến trình uvicorn → phải bàn với Học |

**Báo cáo:**

| Issue | Việc |
|---|---|
| **#95** | Bổ sung 3 mục thiếu vào `bao-cao-huan-luyen-mo-hinh.md` rồi viết bản tóm tắt 3–4 trang nộp GVHD |
| **#57** | DC-05 chương thực nghiệm — nguồn số liệu là mục 1, 2, 4 của tài liệu này |
| **#60** | DC-08 thêm câu trả lời phản biện: "vì sao không đổi kiến trúc mạnh hơn", "làm sao biết mô hình không học theo nền", "chụp cái bàn thì sao", "vì sao không có ảnh tự chụp ngoài đồng" |

---

## 6. Những việc cần chốt

### Đã chốt ngày 10/09/2026

1. ✅ **Giảng viên nhận bản tóm tắt tiến độ 3–4 trang**, không phải chương chuẩn
   khoá luận. (mục 3, issue **#95**)
2. ✅ **Tách nhánh `khác` ra khỏi phạm vi quả** — làm bộ phân loại **2 lớp** (lá cà
   chua / không phải lá cà chua) độc lập, không cần một tấm ảnh quả nào. Vấn đề 2 vì
   vậy được xử lý **bất kể cổng go/no-go 15/09 ra kết quả nào**. (mục 1.5, issue **#92**)

   Ba hệ quả phải xử lý theo:

   - **`CLAUDE.md` cần ghi lại quyết định này.** Hiện mục "Kiến trúc: thêm bộ định
     tuyến" đặt bộ định tuyến 3 lớp nằm hoàn toàn trong phạm vi quả. Sau quyết định
     này, bộ 2 lớp là việc của **luồng lá**, không phụ thuộc cổng go/no-go — không
     ghi lại thì phiên làm việc sau sẽ đọc `CLAUDE.md` rồi tưởng nó vẫn bị chặn.
   - ✅ **Đã tạo issue** — **#91** (thu ảnh không phải lá) và **#92** (huấn luyện bộ 2
     lớp), ngày 10/09/2026. Cần issue riêng vì #71 vẫn thuộc Mốc 6 và vẫn mang nhãn
     `trang-thai:cho-cong-15-09`; `CLAUDE.md` dặn issue GitHub là nguồn duy nhất để
     biết còn phải làm gì, nên hai việc này phải có issue thật, không được chỉ nằm
     trong tài liệu này.
   - **Khi chốt #64 (cổng go/no-go)** phải ghi rõ: dù kết quả là "bỏ phần quả" thì
     #71 bị bỏ **không kéo theo** bộ 2 lớp, vì nó đã tách ra thành việc riêng.

### Đã chốt ngày 15/09/2026

3. ✅ **Đổi nguồn dữ liệu của #49 từ H1 sang H2 (PlantDoc).** Bảo duyệt sau khi xem bằng
   chứng ở mục 5.2. H1 bị loại hẳn, không phải hoãn — nhãn của nó không tra được nên không
   có cách nào dùng lại về sau, trừ khi tác giả công bố thêm file `data.yaml`.
4. ✅ **Được phép sửa `evaluate.py`** (và `prepare.py` trong cùng phạm vi #49) — ba sửa đổi
   cụ thể ở bảng cuối mục 5.5.

### Còn chờ chốt

5. **Có sửa luôn bốn tài liệu trong `model/research/` không?** Chúng vẫn ghi H1 dùng được —
   `00-danh-muc-bai-bao.md` (dòng 168, 173), `01-ke-hoach-thi-nghiem.md` (TN-2, và cột
   "H1 đồng ruộng acc" của bảng trung tâm chương thực nghiệm), `02-cau-hoi-phan-bien.md`
   (dòng 25–27), `03-tong-hop-doi-chieu.md` (dòng 65, 124, 155). Câu *"tải Mendeley về là
   chạy `evaluate.py --manifest` được ngay, nửa buổi có số"* nay đã được chứng minh là sai.
   Để nguyên thì tài liệu trong repo tự mâu thuẫn nhau.
6. **Có xin phép Học** cho hai chỗ chạm vào `backend/` — nhánh hiển thị ca "không
   nhận ra lá" (#47, #26) và `torch.set_num_threads(4)` (#18, #51)?
7. **Có đưa bốn script probe vào repo** (chẳng hạn `model/src/evaluation/probe_ood.py`)
   hay để nguyên ở thư mục tạm? Đưa vào thì mọi số liệu trong tài liệu này **chạy
   lại được** khi hội đồng hỏi "em đo thế nào" — đó là lý do nên đưa. Lý do ngược
   lại: `CLAUDE.md` dặn không thêm thứ chưa ai cần. Ý kiến của tôi là **nên đưa**,
   vì bảng 1.3, 1.4 và 2.1 sẽ được trích vào báo cáo nên phải tái lập được.

---

## 7. Điều gì trong tài liệu này CHƯA được kiểm chứng

Ghi lại cho minh bạch, để không trích quá điều đã đo:

- **Bộ ảnh không phải lá chỉ có 11–16 tấm**, phần lớn là ảnh tổng hợp. Mọi ngưỡng ở
  bảng 1.3, 1.4 là **định hướng, chưa phải hiệu chỉnh**. Phải làm lại sau **#91**.
- **Con số ~80 % chưa xác nhận được** — chỉ có 2 ảnh thực địa riêng biệt.
- **Mặt nạ lá ở bảng 2.2 là xấp xỉ tự động** bằng ngưỡng màu, không phải khoanh tay.
- **Phép thử ở bảng 2.1 là biến thể của A2, không phải tái hiện A2** — xem lưu ý ở
  mục 2.2.
- **Độ trễ đo trên máy Bảo**, chưa phải máy demo (#51 chưa chốt).
- **Vẫn chưa có con số domain gap nào.** Đó là việc **#49**, tính tới hết 15/09 chưa chạy
  được vì nửa ngày đầu tiêu vào việc loại bộ H1 (mục 5.2). Mọi câu trong tài liệu này về
  "độ chính xác thực tế" vẫn là suy luận, chưa phải số đo.
- **Số liệu PlantDoc ở mục 5.2 là đếm file, chưa phải xem ảnh.** Đếm qua GitHub API trên
  danh sách thư mục — biết chắc mỗi lớp có bao nhiêu file và file nào trùng byte, nhưng
  **chưa mở một tấm ảnh nào**. Nhãn có đúng hay không thì phải xem bằng mắt sau khi tải về;
  PlantDoc có tiếng là nhãn nhiễu và hai ví dụ trong mục 5.2 đã gợi đúng điều đó.
- **`tomato_V8.jpg` xuất hiện ở hai lớp khác nhau nhưng chưa đối chiếu được nội dung** (hết
  hạn mức GitHub API lúc đếm). Phải kiểm sau khi tải về — nếu là cùng một ảnh thì đó là một
  nhãn mâu thuẫn trong bộ đo, phải loại.
- **Phần `test` của PlantDoc chỉ có 69 ảnh**, mỗi lớp 6–11 ảnh. Con số đo riêng trên nó có
  sai số lớn; phải kèm khoảng tin cậy khi trích.
- **Sẽ không có số đo trên ảnh cà chua Đà Lạt.** Nhóm không liên hệ được nhà vườn nên
  #20/#21/#48 hoãn vô thời hạn (mục 5.1). Mọi con số domain gap của đề tài sẽ đến từ
  **PlantDoc — ảnh thu từ Internet**. Hai hạn chế phải ghi rõ trong báo cáo: kết luận được
  về domain gap nói chung nhưng **không** kết luận được gì riêng cho điều kiện canh tác ở
  Đà Lạt, và **không được gọi PlantDoc là "ảnh đồng ruộng"**.
