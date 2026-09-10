# Rà soát 4 vấn đề sau khi tích hợp mô hình thật, và kế hoạch xử lý

> Ghi ngày **10/09/2026**, ba ngày sau khi mô hình thật được nối vào mobile (IN-01, IN-02).
> Toàn bộ số liệu trong tài liệu này **đo trực tiếp trên checkpoint đang chạy**
> `model/checkpoints/leaf_disease_detection_model.pt`
> (`efficientnet_b0-20260907-1443`), không trích lại từ báo cáo cũ.
>
> Mục đích: trả lời bốn vấn đề Bảo nêu sau khi thử app thật, phân biệt cho rõ
> **triệu chứng** với **nguyên nhân**, rồi xếp việc theo thứ tự đáng làm.

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
| **1** | **Đo domain gap bằng bộ H1** — 731 ảnh đồng ruộng thật, Mendeley, 6/7 lớp trùng (**#49**) | Biến "khoảng 80 %" thành một con số có nguồn trích dẫn được. Mọi việc sau đều cần con số này làm mốc | Nửa buổi, không phải đi chụp |
| **2** | **Cắt lá trước khi phân loại** (**#93**) | Tấn công đúng gốc: phần lệch giữa hai phân phối chủ yếu là **nền**. Bỏ nền đi thì hai phân phối gần nhau lại. Bảng 2.1 đã chứng minh: chỉ giữ tâm ảnh vẫn 97,3 %. Dùng chung hạ tầng với bộ phát hiện lá ở mục 1.5 | Trung bình |
| **3** | **Tăng augmentation mô phỏng điều kiện đồng ruộng** — thay nền ngẫu nhiên, bóng đổ, mờ nhoè, nắng gắt (**#50** hướng 1) | Dạy mô hình bỏ qua nền ngay trong lúc học. Rẻ vì không cần dữ liệu mới | Thấp — chỉnh config + huấn luyện lại 30 phút |
| **4** | **TTA — suy luận nhiều biến thể rồi lấy trung bình** (**#94**) | Thường được thêm vài phần trăm trên dữ liệu lệch phân phối, không cần huấn luyện lại gì | Thấp, nhưng đắt lên 3–4× thời gian suy luận |
| **5** | **Tinh chỉnh (fine-tune) bằng bộ H2/H3** (**#50** hướng 2) | Cách trực tiếp nhất để kéo mô hình về phân phối thật. ⚠️ **Nguồn đã đổi** — xem mục 5.1: ảnh tự chụp ngoài đồng (#20) không thực hiện được, nên dùng bộ đồng ruộng công khai, và **giữ H1 làm tập test độc lập** | Cao |
| 6 | So sánh kiến trúc (**#19**) | **Để báo cáo, không phải để sửa lỗi.** Xem 2.3 | 4 lượt × 25 phút |

⚠️ **Thứ tự này đã đổi so với bản đầu của tài liệu.** Ban đầu "tinh chỉnh bằng ảnh thực
địa" xếp thứ 3 vì là cách hiệu quả nhất. Sau ràng buộc ngày 10/09 (không liên hệ được nhà
vườn, xem mục 5.1) nó tụt xuống thứ 5: không mất hẳn — vẫn làm được bằng bộ H2/H3 công
khai — nhưng không còn là hướng rẻ nhất nữa. Ba việc phía trên nó đều **không cần một tấm
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
> sai: `CLAUDE.md` ghi rõ *"Toàn bộ việc còn lại đã tạo thành 76 issue... Đây là nguồn
> duy nhất để biết còn phải làm gì — đừng lập bảng công việc song song ở chỗ khác."*
> Một hệ đánh số thứ hai chồng lên số issue đúng là thứ bị cấm ở đó.
>
> Đếm lại thì trong 19 việc của bản đầu, **13 việc đã có issue sẵn** — chỉ 6 việc là mới.
> Sáu việc đó nay đã thành issue thật (**#90–#95**, tạo ngày 10/09/2026), nên mục này
> chuyển hoàn toàn sang đánh số theo issue. **Số issue là danh tính duy nhất của một việc.**
>
> Giá trị của buổi rà soát vì vậy không phải "có kế hoạch mới", mà là **đổi thứ tự ưu
> tiên của các issue đã có** — và số đo đổi thứ tự đó ở hai chỗ đáng kể, xem bảng 5.3.

### 5.1. Ràng buộc mới: không chụp được ảnh đồng ruộng (chốt 10/09/2026)

Nhóm **không liên hệ được nhà vườn để xin phép chụp ảnh** và không còn thời gian cho việc
này. Đây là ràng buộc thật, không phải trì hoãn.

Hệ quả trực tiếp lên bốn issue đang có:

| Issue | Trước | Nay |
|---|---|---|
| **#20** FD-01 chụp 50–100 ảnh lá thật ngoài đồng | Việc chặn, làm trong tháng 9 | **Hoãn vô thời hạn** — không thực hiện được |
| **#21** FD-02 gán nhãn ảnh thực địa | Chặn bởi #20 | **Hoãn theo #20** |
| **#48** FD-03 xếp ảnh thực địa vào `data/field/` | Chặn bởi #21 | **Hoãn theo #20** |
| **#49** FD-04 đánh giá mô hình trên ảnh thực địa | Dùng ảnh tự chụp **hoặc** bộ H1 | **Chỉ còn đường H1** — và vẫn làm được đầy đủ |
| **#50** FD-05 cải thiện nếu accuracy rớt | Hướng 2 = fine-tune bằng ảnh tự chụp | Hướng 2 phải đổi nguồn: **H2 (PlantDoc) hoặc H3 (Taiwan)**, giữ H1 làm tập test độc lập |

**Rủi ro số 1 trong `CLAUDE.md` (domain gap) KHÔNG bị bỏ trống.** Đây là điểm quan trọng
nhất của mục này. Ba bộ dữ liệu đồng ruộng công khai trong `model/research/` thay thế được
hoàn toàn phần ảnh tự chụp:

| Mã | Bộ | Quy mô | Vai trò sau ràng buộc mới |
|---|---|---|---|
| **H1** | Imtiaz et al., Data in Brief 2025 (Mendeley) | **731 ảnh đồng ruộng thật**, 7 lớp, 6/7 trùng với 10 lớp của nhóm | **Tập test độc lập.** Giữ nguyên vai trò này, tuyệt đối không dùng để huấn luyện |
| **H2** | PlantDoc, CoDS-COMAD 2020 | 2.598 ảnh, 17 lớp, có phần cà chua | **Nguồn fine-tune** thay cho ảnh tự chụp. Bài gốc báo cải thiện tới 31 % khi huấn luyện thêm trên bộ này |
| **H3** | Taiwan tomato leaves | 622 ảnh, 6 lớp, 3 lớp trùng | Nguồn fine-tune bổ sung. Ảnh có bóng đổ, nhiều lá chồng, nền lộn xộn |

Và cần nói rõ để không hiểu thành một lời xin lỗi: **H1 có 731 ảnh, gấp 7–14 lần con số
50–100 ảnh tự chụp theo kế hoạch ban đầu**, do một nhóm độc lập thu thập và công bố trên
tạp chí có phản biện, nên **trích dẫn được**. Về mặt phương pháp đây là **lựa chọn tốt hơn**
kế hoạch cũ, không phải phương án chống cháy. Chỗ thật sự mất là tính địa phương: không có
ảnh cà chua Đà Lạt, nên không kết luận được gì riêng cho điều kiện canh tác ở đây. Phải ghi
hạn chế đó vào báo cáo, và đó là hạn chế duy nhất.

Điều **không** bị ảnh hưởng: **#91** (thu ảnh không phải lá cà chua) hoàn toàn làm được —
chụp bàn, ghế, tay, sàn nhà, lá cây khác tại nhà trong khoảng một giờ, không cần nhà vườn
nào. Đừng để nó bị hoãn lây theo #20.

### 5.2. Sáu issue mới tạo ngày 10/09/2026

| Issue | Việc | Mốc | Mức | Trạng thái |
|---|---|---|---|---|
| **#90** | MD-11 · Không khoanh vùng khi bản đồ nhiệt Grad-CAM quá yếu | 2 | `muc:cao` | Làm được ngay |
| **#91** | MD-12 · Thu bộ ảnh không phải lá cà chua | 2 | `muc:chan` | Làm được ngay, **không cần nhà vườn** |
| **#92** | MD-13 · Huấn luyện bộ phân loại 2 lớp lá / không phải lá | 2 | `muc:cao` | Chặn bởi #91 |
| **#93** | MD-14 · Cắt vùng lá trước khi phân loại | 4 | `muc:thuong` | Chặn bởi #49 |
| **#94** | MD-15 · Thử test-time augmentation khi suy luận | 4 | `muc:tuy-chon` | Chặn bởi #49 |
| **#95** | DC-09 · Bản tóm tắt tiến độ huấn luyện mô hình nộp GVHD | 2 | `muc:cao` | Nên chờ #49 nếu kịp |

Ưu tiên đã nằm trong nhãn `muc:*` của GitHub, không cần bảng ưu tiên riêng ở đây.

### 5.3. Số đo hôm nay đổi thứ tự issue ở đâu

`CLAUDE.md` mục *"Việc tiếp theo, xếp đúng thứ tự"* đang ghi 5 việc. Đối chiếu với số đo:

| Thứ tự đang ghi | Issue | Số đo hôm nay nói gì |
|---|---|---|
| 1 | **#17** kiểm Grad-CAM bằng mắt | **Giữ nguyên.** Vẫn là cổng kiểm soát của cả đề tài. Mục 2.5 đã dựng số liệu định hướng và chỉ đúng chỗ đáng nghi (`healthy`, 14 % ảnh có điểm nóng ra ngoài lá) |
| 2 | **#49** đo trên ảnh đồng ruộng | **Giữ nguyên, và nay là đường duy nhất** để có số domain gap (mục 5.1) |
| 3 | **#16** nâng Grad-CAM++ | Giữ nguyên thứ tự. Nay có căn cứ định lượng: tầng chập cuối 7×7, 40,7 % khối lượng heatmap rơi ra ngoài lá |
| 4 | **#18** đo tốc độ CPU | **Coi như đã có số** — 215 ms (4 luồng). Rút khỏi hàng chờ, chỉ còn phần đo lại trên máy demo khi #51 chốt máy |
| 5 | **#19** so kiến trúc | **Hạ cấp** — từ "cách sửa lỗi" thành "phần đánh giá cho báo cáo". Xem mục 2.3 |

Hai dòng cuối là chỗ buổi rà soát tiết kiệm được công: nếu cứ theo thứ tự cũ mà làm, khả
năng cao sẽ chạy #19 (4 lượt × 25 phút) để mong tăng accuracy — mà số đo cho thấy việc đó
**không giúp được gì** cho vấn đề đang gặp.

### 5.4. Thứ tự làm, theo issue

**Tuần này (10/09 – 15/09), trước cổng go/no-go #64:**

| Ưu tiên | Issue | Vì sao ở đây | Ước lượng |
|---|---|---|---|
| 1 | **#49** đo domain gap trên H1 | Việc duy nhất biến "khoảng 80 %" thành con số trích dẫn được. #93, #94, #50 đều chặn bởi nó. Không cần chụp ảnh | Nửa buổi |
| 2 | **#17** kiểm Grad-CAM bằng mắt, 5 ảnh × 10 lớp | Cổng kiểm soát của cả đề tài. Ưu tiên xem kỹ `healthy` và `spider_mites` | 2–3 giờ |
| 3 | **#90** không khoanh vùng khi CAM quá yếu | Chặn ngay triệu chứng nặng nhất. Rẻ nhất trong mọi việc ở đây, không cần Học sửa gì | 1 giờ |
| 4 | **#91** thu bộ ảnh không phải lá | Chặn #92 và chặn cả #47 trên thực tế. Làm được ngay | ~1 giờ |
| 5 | **#64** chốt cổng go/no-go | Đến hạn 15/09 | — |

> **Khi chốt #64:** nhánh `khác` **đã tách ra** thành #92, độc lập với phạm vi quả (mục 6).
> Phải ghi rõ điều này vào #64, để nếu kết quả là "bỏ phần quả" thì #71 bị bỏ mà #92 **không**
> bị bỏ theo.

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
| **#50** hướng 2 | Fine-tune — **nguồn đổi thành H2/H3**, không phải ảnh tự chụp | ⚠️ Ảnh dùng huấn luyện **tuyệt đối không được** nằm trong H1. Vi phạm chỗ này thì con số báo cáo vô giá trị |
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
     `trang-thai:cho-cong-15-09`; `CLAUDE.md` dặn 76 issue là nguồn duy nhất để biết
     còn phải làm gì, nên hai việc này phải có issue thật, không được chỉ nằm trong
     tài liệu này.
   - **Khi chốt #64 (cổng go/no-go)** phải ghi rõ: dù kết quả là "bỏ phần quả" thì
     #71 bị bỏ **không kéo theo** bộ 2 lớp, vì nó đã tách ra thành việc riêng.

### Còn chờ chốt

3. **Có xin phép Học** cho hai chỗ chạm vào `backend/` — nhánh hiển thị ca "không
   nhận ra lá" (#47, #26) và `torch.set_num_threads(4)` (#18, #51)?
4. **Có đưa bốn script probe vào repo** (chẳng hạn `model/src/evaluation/probe_ood.py`)
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
- **Chưa chạy `evaluate.py` trên bộ H1** — đó là việc **#49**, và sau ràng buộc ngày
  10/09 thì đây là **đường duy nhất** để có số domain gap.
- **Sẽ không có số đo trên ảnh cà chua Đà Lạt.** Nhóm không liên hệ được nhà vườn nên
  #20/#21/#48 hoãn vô thời hạn (mục 5.1). Mọi con số domain gap của đề tài sẽ đến từ bộ
  dữ liệu công khai chụp ở nơi khác — H1 chụp tại Bangladesh, H2 lấy từ Internet. Tính
  địa phương là hạn chế thật và phải ghi rõ trong báo cáo: kết luận được về domain gap
  nói chung, **không** kết luận được gì riêng cho điều kiện canh tác ở Đà Lạt.
