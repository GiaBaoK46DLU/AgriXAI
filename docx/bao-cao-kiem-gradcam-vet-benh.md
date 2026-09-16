# Báo cáo kiểm Grad-CAM: bản đồ nhiệt có rơi đúng vết bệnh không?

**Issue #17 (MD-08) · 15/09/2026 · nhánh `bao/task-17-kiem-gradcam-vet-benh`**

Số liệu máy sinh: `model/outputs/audit-gradcam-17/ket-qua.md` (bảng đầy đủ),
`ket-qua.json` (số thô), `tung-anh.csv` (từng ảnh một).
Mặt nạ khoanh tay: `model/outputs/audit-gradcam-17/{pv,pd}/khoanh-tay.json`.
Hình: `model/outputs/audit-gradcam-17/figures/gradcam-vet-benh-17.png`.

---

## 0. Trả lời trước khi vào số

Đây là việc kiểm tra xem **đóng góp chính của đồ án** — vùng khoanh giải thích "vì
sao mô hình kết luận như vậy" — có thật hay chỉ là hình trang trí. Câu trả lời ngắn
gồm bốn ý, và ý thứ hai là ý phải nhớ:

1. **Trên ảnh PlantVillage: bản đồ nhiệt nằm đúng trên lá.** 93,3 % số ảnh có điểm
   nóng nhất nằm trong phiến lá; mức nâng so với rải ngẫu nhiên là **0,41** (khoảng
   tin cậy 95 %: 0,34–0,48). Mô hình **không** học tắt theo nền như bài A2 cảnh báo.

2. **Trên ảnh thật (PlantDoc): bản đồ nhiệt không còn phân biệt được lá với nền.**
   Mức nâng chỉ **0,03** (KTC 95 %: **−0,12 đến 0,17** — khoảng này *chứa số 0*, tức
   **không phân biệt được với rải ngẫu nhiên**). Một phần tư vùng mà app khoanh cho
   nông dân (**25,4 %**, KTC 18,1–32,4 %) nằm trên nền chứ không trên lá.

3. **Nhưng cảnh báo nặng nhất của #49 là do phép đo, không phải do mô hình.** #49
   báo "điểm nóng nhất nằm trong lá chỉ **42 %**, thấp hơn cả tung đồng xu". Trên 26
   ảnh PlantDoc của báo cáo này, mặt nạ Otsu cho **42,3 %** — tái lập đúng con số đó —
   còn mặt nạ khoanh tay trên **chính những ảnh ấy** cho **80,8 %**. Chênh lệch 38 điểm
   là lỗi của mặt nạ, không phải của mô hình — xem mục 4.

4. **Bản đồ nhiệt biết khi nào mô hình sai.** Trên PlantDoc, nhóm ảnh mô hình đoán
   **đúng** có 57,1 % số ảnh điểm nóng rơi trên vết bệnh và chỉ 9,1 % vùng khoanh
   nằm trên nền; nhóm đoán **sai** lần lượt là 15,8 % và 31,4 %. Đây là phát hiện
   dùng được ngay: heatmap là **tín hiệu cảnh báo có sẵn, chưa ai khai thác**.

**Kết luận cho câu hỏi cuối của issue — *đủ tin cậy để hiển thị cho người dùng
chưa?*** → **Đủ với ảnh chụp kiểu phòng thí nghiệm, CHƯA đủ với ảnh chụp ngoài
đồng.** Không được để app vẽ vòng khoanh kèm khẳng định bệnh trên ảnh thật khi chưa
làm xong **#90** (không khoanh khi bản đồ nhiệt quá yếu) và **#93** (cắt vùng lá
trước khi phân loại). Chi tiết ở mục 8.

---

## 1. Vì sao #17 không thể bị thay bằng #49

#49 đã đo Grad-CAM rồi, và ra con số đáng lo (mức tập trung tụt 1,58× → 1,02×).
#17 vẫn phải làm, vì phép đo đó có **hai lỗ hổng**, và cả hai đều nằm ở chỗ *mặt nạ
lá lấy từ đâu* và *"trong lá" nghĩa là gì*:

| | #49 | #17 (báo cáo này) |
|---|---|---|
| Mặt nạ lá | Ngưỡng Otsu tự động trên kênh bão hoà màu | **Người khoanh tay từng ô** |
| Số nhãn | 2 (trong lá / ngoài lá) | **3 (vết bệnh / lá lành / nền)** |
| Số ảnh | 150 mỗi bộ | 30 (PlantVillage) + 26 (PlantDoc) |

**Lỗ hổng 1 — mặt nạ tự động không đáng tin trên nền phức tạp.** Ngưỡng màu không
biết đâu là lá cà chua: cỏ, đất, tay người, lá cây khác đều có thể vượt ngưỡng, và
ngược lại lá trong bóng râm hay lá mất nét thì bị bỏ. Mục 4 đo được sai lệch đó là
bao nhiêu.

**Lỗ hổng 2 — "trong lá" gộp hai chuyện khác hẳn nhau.** Con số 46,3 % của #49 cộng
chung *heatmap rơi vào vết bệnh* với *heatmap rơi vào phiến lá chỗ lành*. Hai thứ đó
có ý nghĩa trái ngược: cái đầu là mô hình **nhìn vào triệu chứng**, cái sau là mô
hình chỉ **nhận ra có cái lá ở đây**. Với một đồ án lấy XAI làm đóng góp chính thì
phân biệt này chính là vấn đề. Tách được ba trường hợp là giá trị thật của #17, và
là việc **chỉ mắt người làm được**.

---

## 2. Cách làm — năm quyết định phải bảo vệ được

Toàn bộ mã nguồn nằm trong repo lần này (`model/src/xai/audit_*.py`), khác với #49
chạy bằng script trong thư mục tạm. Lý do ở mục 10.2.

### 2.1. Khoanh trên ảnh 224×224, không khoanh trên ảnh gốc

`build_infer_transform` resize thẳng ảnh về vuông 224×224 (cố ý không center-crop —
xem `dataset.py`). Mô hình **chỉ nhìn thấy bản đó**, Grad-CAM cũng sinh ra trên đúng
lưới đó. Khoanh trên ảnh gốc rồi ánh xạ ngược sẽ thêm một bước nội suy nữa, tự đưa
sai số vào phép đo mà không được gì.

### 2.2. Lưới 14×14, không khoanh đa giác tự do

Lớp tích chập cuối của EfficientNet-B0 ở ảnh 224 cho feature map **7×7**. Mọi phần
"mịn" của heatmap sau đó chỉ là nội suy song tuyến — **không mang thêm thông tin
nào**. Mặt nạ khoanh tay mịn hơn 7×7 vì vậy là *độ chính xác giả*. Lưới 14×14 = đúng
2× độ phân giải gốc của CAM: đủ mịn để không mất thông tin, đủ thô để khoanh nhất
quán và để **người khác kiểm lại được từng ô**.

Mỗi ô một trong ba nhãn:

- **V** — nhìn thấy rõ triệu chứng bệnh (đốm hoại tử, viền cháy nâu, mảng vàng/bạc
  màu do bệnh).
- **L** — phiến lá cà chua nhưng không thấy triệu chứng. Cuống lá tính L.
- **N** — không phải mô lá cà chua: nền, đất, bóng đổ, tay người, quả, chữ chèn.
  Ô lẫn thì theo phần chiếm ưu thế.

Quy tắc này **rộng rãi với V** (thấy triệu chứng là tính, không đòi chiếm hết ô), nên
mọi con số "heatmap trúng vết bệnh" trong báo cáo là **cận trên**.

### 2.3. Khoanh MÙ — phiếu không in bản đồ nhiệt

Nếu vừa nhìn heatmap vừa khoanh vết bệnh thì mặt nạ sẽ bị chính heatmap dẫn dắt, và
con số "heatmap trúng vết bệnh" thành ra tự chứng minh chính nó. Vì vậy phiếu khoanh
(`{pv,pd}/phieu/`) **chỉ có ảnh**; bản chồng heatmap (`{pv,pd}/doi-chieu/`) chỉ được
sinh **sau khi** file `khoanh-tay.json` đã ghi xong. Thứ tự này ép bằng cờ `--overlay`
riêng chứ không phải bằng lời hứa.

### 2.4. Chọn mẫu bằng seed, không chọn tay

3 ảnh mỗi lớp, bốc ngẫu nhiên có seed 42 **theo từng lớp** (`audit_sample.py`). Bốc
trên cả tập thì lớp đông sẽ chiếm hết, mà #17 cần nhận xét **từng lớp**. Cùng manifest
+ cùng seed thì ra cùng danh sách ảnh trên máy nào cũng vậy.

- **PlantVillage**: 10 lớp × 3 = **30 ảnh** (tập `test`).
- **PlantDoc**: 9 lớp có mặt × 3, riêng `spider_mites` cả bộ chỉ có 2 ảnh = **26 ảnh**.

> ⚠️ Tiêu chí gốc của issue ghi "xem ít nhất 5 ảnh mỗi lớp". Bản này làm **3 ảnh mỗi
> lớp trên HAI bộ**, đổi lấy việc khoanh tay từng ô — đắt hơn nhiều so với "nhìn lướt
> rồi nhận xét" mà tiêu chí gốc hình dung, và cho ra **số** thay vì chỉ cảm nhận.
> Đây là đánh đổi có chủ ý, ghi ra để không ai tưởng là làm thiếu.

### 2.5. Ba nhóm lớp phải đọc riêng — đây cũng là một phát hiện

Khi khoanh mới lộ ra: **không phải lớp nào cũng có "vết bệnh" để chỉ vào.**

| Nhóm | Lớp | Tỉ lệ V/L đọc được không? |
|---|---|---|
| **Cục bộ** | `bacterial_spot`, `early_blight`, `late_blight`, `septoria_leaf_spot`, `target_spot` | **Có** — vết bệnh và lá lành là hai vùng khác nhau thật |
| **Khuếch tán** | `leaf_mold`, `mosaic_virus`, `yellow_leaf_curl_virus`, `spider_mites` | **Không** — triệu chứng trải đều cả phiến lá nên V ≈ cả lá. Chỉ đọc được lá-vs-nền |
| **Không có vết** | `healthy` | Không có ô V nào, theo định nghĩa |

Gộp cả ba nhóm rồi báo một con số "% trúng vết bệnh" là **sai về phương pháp**. Mọi
bảng dưới đây vì vậy đều tách ba nhóm, và **con số chính lấy từ nhóm cục bộ**.

---

## 3. Kết quả chính — ba trường hợp

Mọi con số là trung bình theo từng ảnh (mỗi ảnh một phiếu), KTC 95 % bằng bootstrap
percentile 10.000 lần.

**KL** = tỉ lệ khối lượng bản đồ nhiệt · **DT** = tỉ lệ diện tích ô ·
**Tập trung** = KL ÷ DT (1,00× = rải đều) ·
**Nâng chuẩn hoá** = (KL − DT) ÷ (1 − DT), tức đi được bao nhiêu phần đoạn đường từ
đoán mò (0,00) tới hoàn hảo (1,00).

| | PlantVillage (n=30) | PlantDoc (n=26) |
|---|--:|--:|
| Mô hình đoán đúng | 30/30 | 7/26 |
| **KL rơi vào vết bệnh** | **31,7 %** (22,8–41,0) | **20,3 %** (12,7–28,9) |
| **KL rơi vào phiến lá lành** | **36,9 %** (27,5–46,2) | **51,8 %** (43,4–59,5) |
| **KL rơi ra nền** | **31,4 %** (28,2–34,6) | **28,0 %** (20,1–35,9) |
| Diện tích lá (khoanh tay) | 45,2 % | 70,0 % |
| KL trong lá (= vết bệnh + lá lành) | 68,6 % | 72,0 % |
| Mức tập trung vào lá | 1,65× (1,46–1,87) | 1,10× (0,99–1,23) |
| *Trần lý thuyết của mức tập trung* | *2,21×* | *1,43×* |
| **Nâng chuẩn hoá vào lá** | **0,41** (0,34–0,48) | **0,03** (−0,12–0,17) |
| Đỉnh heatmap nằm trong lá | 93,3 % | 80,8 % |
| Đỉnh heatmap nằm trên vết bệnh | 53,3 % | 26,9 % |

### 3.1. Vì sao phải có cột "trần lý thuyết" — chỗ dễ đọc sai nhất

Mức tập trung = khối lượng ÷ diện tích **có trần khác nhau tuỳ ảnh**. Nếu vùng lá đã
chiếm 70 % khung hình thì dù CAM dồn 100 % khối lượng vào lá, mức tập trung cũng chỉ
đạt 1 ÷ 0,70 = **1,43×**. Ảnh PlantVillage có lá chiếm 45 %, trần là **2,21×**.

Nên **so thẳng 1,65× với 1,10× là so sai** — và đây đúng là chỗ bảng của #49 dễ bị
đọc quá tay. Ảnh PlantDoc phần lớn là **cảnh chụp cả bụi cây, tán lá phủ kín khung
hình**: có ảnh (`pd-late_blight-1`) không có lấy một ô nền nào. Lá chiếm 70 % thì
"nằm trong lá" gần như không còn là thành tích.

Đại lượng **nâng chuẩn hoá** sửa đúng chỗ đó, và nó nói điều tệ hơn con số tập trung:
**0,41 → 0,03**, với khoảng tin cậy trên PlantDoc chứa số 0. Trên ảnh thật, khả năng
Grad-CAM ưu tiên lá hơn nền là **không chứng minh được**.

### 3.2. Nhưng khả năng tìm VẾT BỆNH thì không tụt

Chỉ tính nhóm **cục bộ** — nhóm duy nhất mà tỉ lệ vết-bệnh/lá-lành có nghĩa:

| | PlantVillage (n=15) | PlantDoc (n=13) |
|---|--:|--:|
| Diện tích vết bệnh | 11,4 % | 18,3 % |
| KL heatmap trên vết bệnh | 19,8 % | 26,1 % |
| Mức tập trung vào vết bệnh | 1,88× (1,38–2,46) | 1,56× (1,05–2,17) |
| **Nâng chuẩn hoá vào vết bệnh** | **0,098** (0,037–0,172) | **0,102** (0,022–0,191) |

Hai con số cuối **gần như bằng nhau**, và cả hai khoảng tin cậy đều **không chứa số
0**. Đọc ra: Grad-CAM có ưu tiên vết bệnh hơn phần lá lành, **yếu nhưng có thật, và
mức độ đó không đổi khi chuyển sang ảnh thật.**

Ghép hai mục lại được câu trả lời đầy đủ hơn cả câu hỏi ban đầu:

> Trên ảnh thật, thứ hỏng không phải là khả năng tìm vết bệnh — mà là khả năng
> **không nhìn ra ngoài lá**.

Điều này khớp với việc nhìn hình: heatmap của EfficientNet-B0 ở 7×7 gần như luôn là
**một khối tròn to** đặt lên vật thể chính, chứ không phải nhiều điểm bám theo từng
đốm bệnh. Khi vật thể chính là một phiến lá cận cảnh thì khối tròn đó nằm đúng chỗ.
Khi ảnh là cả bụi cây hay có tay người cầm lá, "vật thể chính" không còn là cái lá
bệnh nữa.

---

## 4. So mặt nạ tay với mặt nạ tự động — trên đúng cùng một tập ảnh

Đây là phép so mà #49 không làm được, và nó đính chính một con số đã ghi vào báo cáo
domain gap. Cột "Otsu" là **cài lại đúng cách làm của #49** (ngưỡng Otsu trên kênh
bão hoà màu, `audit_sheets.nguong_otsu`) rồi chạy trên **chính 56 ảnh này**, với
**chính bản đồ nhiệt này**. Khác nhau duy nhất: mặt nạ lá lấy từ đâu.

| | PV tay | PV Otsu | PD tay | PD Otsu |
|---|--:|--:|--:|--:|
| Diện tích lá | 45,2 % | 33,2 % | **70,0 %** | **47,3 %** |
| KL heatmap trong lá | 68,6 % | 55,7 % | **72,0 %** | **46,8 %** |
| Mức tập trung | 1,65× | 1,82× | 1,10× | 0,99× |
| Nâng chuẩn hoá | 0,41 | 0,33 | 0,03 | 0,01 |
| **Đỉnh heatmap nằm trong lá** | **93,3 %** | **73,3 %** | **80,8 %** | **42,3 %** |

**Bản cài lại tái lập gần đúng số của #49**, dù chạy trên tập ảnh khác và số ảnh khác
(56 so với 150):

| | #49 báo cáo | #17 cài lại |
|---|--:|--:|
| PlantVillage — KL trong lá | 55,4 % | 55,7 % |
| PlantVillage — đỉnh trong lá | 75 % | 73,3 % |
| PlantDoc — KL trong lá | 46,3 % | 46,8 % |
| PlantDoc — đỉnh trong lá | 42 % | **42,3 %** |

Khớp tới mức này thì cột "Otsu" đúng là cách làm của #49, và bảng trên trở thành phép
so **có kiểm soát**. Ba hệ quả:

**(a) Đính chính con số 42 %.** #49 viết *"điểm nóng nhất nằm trong lá chỉ 42 %, thấp
hơn cả tung đồng xu"* — câu đáng lo nhất của cả báo cáo đó. Với mặt nạ khoanh tay,
trên **đúng những ảnh này**, con số là **80,8 %**. Chênh lệch 38 điểm đó **hoàn toàn
do mặt nạ**. Rút lại câu đó.

**(b) Đính chính cả cơ chế mà #49 đoán.** #49 giải thích rằng mặt nạ Otsu **phình ra**
trên PlantDoc vì cỏ, đất, tay người bão hoà màu cao nên bị tính nhầm là lá. Đo được
thì **ngược lại**: Otsu cho diện tích lá 47,3 % trong khi thật là 70,0 % — mặt nạ
**thiếu mất một phần ba vùng lá**, chủ yếu là lá trong bóng râm, lá mất nét và lá
ngả vàng (bão hoà thấp). Mặt nạ hụt thì cả tử số lẫn mẫu số cùng hụt, nên mức tập
trung chỉ lệch chút, nhưng "đỉnh nằm trong lá" thì sai thảm hại — vì đỉnh chỉ cần rơi
vào một ô lá bị mặt nạ bỏ sót là bị đếm thành "ngoài lá".

**(c) Kết luận chính của #49 vẫn đứng.** Mức tập trung trên PlantDoc gần 1,00× ở **cả
hai** cách khoanh (1,10× tay, 0,99× Otsu). Việc Grad-CAM mất khả năng phân biệt lá với
nền trên ảnh thật là **thật**, không phải hiện tượng của phép đo. Cảnh báo được hạ
mức, không được gỡ bỏ.

---

## 5. Nhận xét từng lớp

Mỗi lớp chỉ có 3 ảnh nên đây là **nhận xét định tính**, không phải số để trích. Cột
"Đỉnh trên vết" là *trong 3 ảnh, mấy ảnh có điểm nóng nhất rơi trúng vết bệnh*.

### 5.1. PlantVillage (30/30 đoán đúng)

| Lớp | KL vết | KL lá lành | KL nền | TT vết | Nâng lá | Đỉnh trên vết | Nhận xét |
|---|--:|--:|--:|--:|--:|--:|---|
| Mốc sương muộn | 45,9 % | 29,6 % | 24,5 % | 3,31× | 0,61 | 3/3 | **Tốt nhất.** Mảng hoại tử lớn, heatmap bám đúng, thường đúng vào *rìa đang lan* của vết — hợp bệnh học |
| Nhện đỏ | 57,5 % | 10,6 % | 31,9 % | 2,25× | 0,54 | 3/3 | Nhóm khuếch tán, V ≈ cả lá nên con số cao là đương nhiên. Xem cảnh báo 5.3 |
| Virus xoăn vàng lá | 52,0 % | 22,0 % | 26,1 % | 1,77× | 0,55 | 2/3 | Khuếch tán. Ảnh có vàng rìa lá rõ thì heatmap bám đúng rìa |
| Mốc lá | 45,8 % | 24,8 % | 29,4 % | 2,39× | 0,50 | 3/3 | Khuếch tán |
| Virus khảm | 62,4 % | **0,7 %** | 36,9 % | 2,08× | 0,46 | 3/3 | Khuếch tán, gần như không có ô "lá lành" nào để so |
| Đốm mắt cua | **3,5 %** | 74,9 % | 21,6 % | 1,53× | 0,57 | **0/3** | ⚠️ **Đáng lo nhất.** Đốm quá nhỏ (chiếm 1,9 % ảnh); heatmap thành một khối tròn giữa phiến lá, **không ảnh nào** có đỉnh trúng đốm. Đúng 3/3 nhưng **không nhìn vào bằng chứng** |
| Đốm lá Septoria | 20,7 % | 40,5 % | 38,8 % | 1,98× | 0,24 | 1/3 | Ảnh có cụm đốm dày thì trúng (`pv-septoria_leaf_spot-3`, xem hình); ảnh đốm thưa thì trượt |
| Đốm vòng (đốm nâu) | 17,3 % | 40,9 % | 41,8 % | 1,33× | **0,05** | 1/3 | ⚠️ **Rò ra nền nhiều nhất (41,8 %).** `pv-early_blight-3` có đỉnh nằm hẳn trên nền, và **50 %** vùng app khoanh nằm trên nền — vẫn đoán đúng |
| Đốm lá vi khuẩn | 11,8 % | 58,4 % | 29,8 % | 1,23× | 0,27 | **0/3** | ⚠️ Đốm nhỏ và rải rác; heatmap phủ giữa lá, trùng vài đốm một cách tình cờ |
| Lá khoẻ mạnh | — | 66,7 % | 33,3 % | — | 0,29 | — | **Đạt yêu cầu của issue.** Không có vết để chỉ vào, và heatmap rơi **vào phiến lá** đúng như mong đợi: 3/3 ảnh đỉnh nằm trong lá, chỉ 4,8 % vùng khoanh nằm trên nền |

> **Ghi chú về lớp `healthy` — sửa một lo ngại cũ.** Tiền kiểm 10/09 đo được "chỉ
> 42,2 % khối lượng heatmap trong lá, điểm nóng nhất trong lá 55 %" và `CLAUDE.md`
> ghi đó là chỗ đáng nghi. Đo lại bằng mặt nạ khoanh tay: **66,7 % khối lượng trong
> lá, 3/3 ảnh đỉnh nằm trong lá**. Lo ngại đó là hệ quả của mặt nạ tự động, giống
> hệt trường hợp ở mục 4. Vẫn phải ghi hạn chế thật của lớp này vào báo cáo — lá khoẻ
> **không có vết bệnh nào** để Grad-CAM neo vào, nên vùng khoanh cho ảnh lá khoẻ
> không mang thông tin gì ngoài "đây là cái lá"; app **không nên vẽ vòng khoanh cho
> kết quả `healthy`**.

### 5.2. PlantDoc (7/26 đoán đúng)

| Lớp | KL vết | KL nền | Nâng lá | Đỉnh trên vết | Nhận xét |
|---|--:|--:|--:|--:|---|
| Mốc sương muộn | 52,3 % | **0,3 %** | 0,54 | 3/3 | Đúng 3/3 với 93–99 % tin cậy. Đều là ảnh cận cảnh mà vết bệnh chiếm gần hết khung — dễ cho cả mô hình lẫn Grad-CAM |
| Virus xoăn vàng lá | 22,7 % | 13,4 % | 0,21 | 1/3 | Tán lá phủ kín khung (lá 81,8 %), heatmap ở đâu cũng "trong lá" |
| Đốm lá vi khuẩn | 24,1 % | **46,8 %** | 0,21 | 1/3 | Gần nửa khối lượng ra nền — hai trong ba ảnh có nền đen tuyền hoặc nền xanh dương phông chụp |
| Mốc lá | 7,6 % | 21,6 % | 0,17 | 0/3 | Ảnh mờ, triệu chứng gần như không nhận ra bằng mắt; heatmap không có gì để bám |
| Virus khảm | 34,0 % | 41,2 % | 0,15 | 1/3 | Gồm một ảnh chụp slide thuyết trình — xem mục 6 |
| Lá khoẻ mạnh | — | 36,8 % | 0,06 | — | ⚠️ **0/3 đoán đúng.** `pd-healthy-2` bị gọi là mốc sương muộn 45 % và bằng chứng mô hình dùng là **mảng đất ở đáy ảnh**; `pd-healthy-1` có **50 %** vùng khoanh nằm trên nền |
| Đốm vòng (đốm nâu) | 12,5 % | 32,9 % | **−0,04** | 0/3 | ⚠️ `pd-early_blight-2`: đúng **một** vết hoại tử rõ ở giữa phiến lá, heatmap nằm ở **mép phải ảnh**, **53,8 %** vùng khoanh trên nền cát, **0 %** trên vết bệnh |
| Đốm lá Septoria | 19,4 % | 28,2 % | **−0,46** | 1/3 | ⚠️ **Tệ nhất.** Cả ba ảnh đều nhiều đốm rõ, cả ba đều bị đoán thành đốm vòng, và heatmap **né** vùng lá có đốm — `pd-septoria_leaf_spot-2` heatmap nằm hẳn ở nửa dưới ảnh trong khi đốm ở nửa trên |
| Nhện đỏ (n=2) | 4,7 % | 31,7 % | −0,22 | 0/2 | **Không đọc được** — cả hai "ảnh" là ảnh ghép 2×2 của bốn bệnh khác nhau, xem mục 6 |

### 5.3. Riêng `spider_mites` — trả lời trực tiếp một tiêu chí của issue

Issue yêu cầu kiểm riêng lớp này vì "dấu hiệu là chấm li ti và tơ nhện, rất nhỏ. Nếu
Grad-CAM không bắt được thì ghi rõ hạn chế này". Kết quả:

**Ở độ phân giải 224×224 mà mô hình nhìn thấy, chấm li ti do nhện đỏ gần như không
còn nhìn thấy được — kể cả với mắt người.** Trong 3 ảnh PlantVillage, chỉ
`pv-spider_mites-2` có triệu chứng khu trú được (nửa trái phiến lá bạc màu xám-lục
rõ); hai ảnh còn lại phải khoanh cả phiến lá là V vì không chỉ được vào đâu cụ thể.

Nghĩa là con số 57,5 % "khối lượng trên vết bệnh" của lớp này **không chứng minh
Grad-CAM bắt được triệu chứng nhện đỏ** — nó chỉ phản ánh việc cả phiến lá đã được
đánh dấu V. Đây là **hạn chế của phép đo, không phải thành tích của mô hình**, và
phải ghi đúng như vậy trong báo cáo tốt nghiệp.

Đáng chú ý là mô hình vẫn đúng 3/3 trên PlantVillage với 98 % tin cậy. Nó phân biệt
được lớp này bằng **màu và kết cấu chung của phiến lá**, không bằng từng chấm — hợp
lý về thị giác, nhưng có nghĩa là vùng khoanh cho `spider_mites` không chỉ được vào
"chỗ có nhện".

---

## 6. Ba phát hiện về chất lượng dữ liệu PlantDoc — chỉ lộ ra khi xem từng ảnh

Đây là sản phẩm phụ của #17 nhưng đáng đưa vào báo cáo, vì nó trả lời trực tiếp câu
"nhóm kiểm tra dữ liệu thế nào" và nối tiếp bài học đã ghi ở `CLAUDE.md` cái bẫy số 4.

1. **Hai ảnh `spider_mites` duy nhất của PlantDoc không phải ảnh chụp lá.** Cả hai là
   **ảnh ghép 2×2** từ tài liệu khuyến nông, bốn ô có **chữ trắng đè** ghi tên bốn
   bệnh khác nhau: *Bacterial Spot*, *Bacterial Speck*, *Early Blight*, *Mite Damage*.
   Chỉ 1/4 khung hình là nhện đỏ. Gán nhãn `spider_mites` cho cả tấm là sai về bản
   chất. → `docx/bao-cao-domain-gap.md` đã loại lớp này khỏi phép đo vì n=2; căn cứ
   thật ra còn mạnh hơn thế.

2. **`pd-mosaic_virus-3` là ảnh chụp màn hình một slide thuyết trình tiếng Thổ Nhĩ Kỳ**
   ("Mosaic virüsleri"), gồm chữ tiêu đề, một ảnh lá cà chua trông khoẻ, một ảnh **dưa
   chuột** và một ảnh **rổ cà chua chín**. Không nhìn thấy triệu chứng khảm ở đâu.
   Mô hình kết luận tấm này là **mốc sương muộn 89 %** — mức tin cậy cao nhất trong 19 ảnh
   đoán sai của PlantDoc. Đây là một ca mẫu cho **#92** (chặn ảnh không phải lá cà chua):
   ảnh chụp màn hình một slide, không có phiến lá bệnh nào, vẫn được khẳng định gần 90 %.

3. **`pd-bacterial_spot-1` chủ thể chính là một QUẢ cà chua**, không phải lá — trong
   lớp lá. (Trớ trêu là đúng lớp `fruit_bacterial_spot` của phần mở rộng đang chờ cổng
   go/no-go #64.)

Bốn ảnh trên được đánh dấu `co_van_de_du_lieu: true` trong file khoanh tay. Bỏ chúng
ra khỏi bảng PlantDoc thì con số **hầu như không đổi** (nâng chuẩn hoá 0,03 → 0,04;
KL nền 28,0 % → 24,1 %), nên các kết luận ở mục 3 không phụ thuộc vào chúng.

---

## 7. Hai phép kiểm chứng

### 7.1. Kết luận không phụ thuộc phép chuẩn hoá min-max

`gradcam.py:95–99` kéo giãn min-max từng ảnh về 0..1, nên một CAM phẳng lét vô nghĩa
cũng ra đúng dải 0..1 như một CAM tập trung rõ. Để chắc kết luận không phải hệ quả của
phép kéo giãn đó, đo lại toàn bộ trên **CAM thô** (thêm `normalize=False` vào
`GradCAM.__call__`, mặc định vẫn là `True` nên không đổi hành vi của hệ thống):

| | PV chuẩn hoá | PV thô | PD chuẩn hoá | PD thô |
|---|--:|--:|--:|--:|
| KL vết bệnh | 31,7 % | 29,4 % | 20,3 % | 19,7 % |
| KL nền | 31,4 % | 34,9 % | 28,0 % | 27,9 % |
| Tập trung lá | 1,65× | 1,44× | 1,10× | 1,03× |

Cùng hướng, cùng độ lớn. **Kết luận giữ nguyên.**

Nhân tiện đo luôn được **độ phẳng** của CAM thô (trung bình ÷ đỉnh; càng gần 1 càng
phẳng): PlantVillage **0,30** (KTC 0,26–0,34), PlantDoc **0,32** (KTC 0,28–0,37). Hai
bộ **phẳng như nhau** — tức không thể dùng riêng độ phẳng để phát hiện ảnh lạ. Đây là
dữ kiện đầu vào cho **#90**: ngưỡng chặn nên dựa vào cái khác, không dựa vào "CAM có
phẳng không".

### 7.2. Bản đồ nhiệt biết khi nào mô hình sai

Tách 26 ảnh PlantDoc theo việc mô hình đoán đúng hay sai:

| | Đoán đúng (n=7) | Đoán sai (n=19) |
|---|--:|--:|
| KL trên vết bệnh | **36,7 %** | **14,2 %** |
| Đỉnh nằm trên vết bệnh | **57,1 %** | **15,8 %** |
| Nâng chuẩn hoá vào lá | **0,31** | **−0,03** |
| Vùng app khoanh nằm trên nền | **9,1 %** | **31,4 %** |

Cách nhau rất xa trên cả bốn dòng. Nhưng **đây là tương quan, chưa phải nhân quả**:
ảnh mà mô hình đoán đúng phần lớn là ảnh cận cảnh vết bệnh lớn — loại ảnh vừa dễ phân
loại vừa dễ cho Grad-CAM. n=7 cũng quá nhỏ để kết luận. Dù vậy hướng đi rất rõ và
**rẻ để kiểm chứng ở quy mô lớn**: chạy trên cả 742 ảnh PlantDoc, không cần khoanh tay
thêm tấm nào nếu chỉ cần tỉ lệ khối lượng trong vùng khoanh.

Nếu đứng vững thì đây là thứ dùng được ngay cho nông dân: khi bản đồ nhiệt tản mát
hoặc nằm ngoài lá, app **giảm mức khẳng định** thay vì nói "Mốc sương muộn 98 %". Đó
đúng là tinh thần XAI của đề tài — hệ thống biết khi nào nó không nên trả lời.

---

## 8. Hệ quả cho các việc còn lại

| Issue | Số liệu này nói gì |
|---|---|
| **#90** không khoanh khi bản đồ nhiệt quá yếu | **Thành bắt buộc, và phải đổi tiêu chí.** 25,4 % vùng app khoanh trên ảnh thật nằm ngoài lá. Nhưng mục 7.1 cho thấy **độ phẳng CAM không phân biệt được hai bộ** (0,30 vs 0,32) — nên đừng chặn theo "CAM có phẳng không". Tiêu chí hứa hẹn hơn: **tỉ lệ khối lượng nằm trong vùng lá**, cần #93 làm trước |
| **#93** cắt vùng lá trước khi phân loại | **Xác nhận lại là ưu tiên đúng.** Diện tích lá trung bình trên PlantDoc là 70 % vì phần lớn là ảnh chụp cả bụi cây. Cắt vùng lá vừa sửa việc "mô hình bị hỏi sai câu hỏi", vừa **tạo ra cái mặt nạ mà #90 đang thiếu** |
| **#98** nâng Grad-CAM++ | **Vẫn để sau #93, và nay có lý lẽ định lượng.** Lớp `target_spot` (0/3 đỉnh trúng đốm, đốm chỉ chiếm 1,9 % ảnh) và `bacterial_spot` (0/3) hỏng vì đúng lý do độ phân giải 7×7: heatmap là một khối tròn, không thể chỉ vào nhiều đốm nhỏ rải rác. Nhưng nét hơn mà đặt sai vật thể thì vô nghĩa — thứ tự giữ nguyên |
| **#47** ngưỡng tin cậy | **Thêm một đầu vào.** Mục 7.2 gợi ý một tín hiệu tin cậy **tốt hơn xác suất softmax**: vị trí của bản đồ nhiệt. Đáng thử trước khi chốt ngưỡng |
| **#49** báo cáo domain gap | **Phải sửa hai chỗ ở mục 5** — xem mục 4 (a) và (b). Con số 42 % và cách giải thích "mặt nạ phình ra" đều sai |
| **#16** sinh lưới ảnh minh hoạ | Hình `gradcam-vet-benh-17.png` và 56 bản đối chiếu dùng lại được. Nhưng **đừng chỉ chọn ảnh đẹp** — bộ này có sẵn cả ca hỏng, và trình bày cả hai mạnh hơn nhiều |
| **Mobile / backend** | ⚠️ **Chưa sửa gì, và không tự sửa** (ngoài phạm vi #17, `backend/` là phần của Học). Nhưng phải báo: cả hai đang vẽ vòng khoanh **vô điều kiện** ở ngưỡng 0,5. Trên ảnh thật, trung bình 1/4 vòng đó nằm ngoài lá. Đề xuất cụ thể ở mục 8.1 |

### 8.1. Đề xuất gửi Học (chưa làm — cần Bảo duyệt trước)

Không đụng vào `backend/` trong nhánh này. Ba việc nên bàn, xếp theo mức dễ:

1. **Không vẽ vòng khoanh khi kết quả là `healthy`.** Lá khoẻ không có vết bệnh để
   chỉ vào; vòng khoanh ở đó chỉ nói "có cái lá", không giải thích gì. Sửa một dòng
   điều kiện, không đụng hợp đồng dùng chung.
2. **Hạ giọng câu giải thích khi bản đồ nhiệt yếu hoặc tản mát**, thay vì khẳng định
   "Mốc sương muộn 98 %". Thuộc **#90**, cần chốt tiêu chí trước.
3. Nếu #93 xong thì truyền thêm **tỉ lệ khối lượng heatmap nằm trong vùng lá** qua
   `Prediction` — nhưng đó là **sửa hợp đồng dùng chung**, phải báo Học trước, đúng
   theo `CLAUDE.md`.

---

## 9. Hạn chế của báo cáo này

Viết đủ để không bị hỏi vặn, theo đúng cách `bao-cao-domain-gap.md` mục 8 đã làm.

1. **Mẫu nhỏ.** 30 + 26 ảnh, mỗi lớp 3 ảnh. Số gộp cả bộ có khoảng tin cậy chấp nhận
   được, nhưng **số từng lớp (n=3) chỉ để đọc định tính** — đừng trích một mình vào
   báo cáo. Đây là cái giá của việc khoanh tay từng ô; tăng mẫu là tăng đúng tuyến
   tính công sức.

2. **Người khoanh là trợ lý AI trong phiên làm việc 15/09/2026, chưa có người thứ hai
   soát lại.** Đây là hạn chế lớn nhất và phải nói thẳng. Ba việc đã làm để hạn chế
   ảnh hưởng: (a) khoanh **mù**, không nhìn heatmap; (b) quy tắc ba nhãn viết ra
   trước, ghi trong file khoanh tay; (c) **toàn bộ mặt nạ lưu dưới dạng chữ, sửa tay
   được** — ai không đồng ý với ô nào thì sửa `khoanh-tay.json` rồi chạy lại
   `audit_score` là ra số mới. **Việc còn phải làm: Bảo soát lại ít nhất một mẫu con**,
   tốt nhất là khoanh độc lập vài ảnh rồi so độ đồng thuận.

3. **Ranh giới "vết bệnh" vốn mờ ở vài lớp.** `leaf_mold` và `mosaic_virus` gây đổi
   màu loang lổ chứ không tạo vết rõ mép; ranh giới đặt ở đâu là phán đoán. Đã xử lý
   bằng cách tách nhóm khuếch tán (mục 2.5) và **không** đọc tỉ lệ V/L cho nhóm đó,
   nhưng con số của nhóm đó vẫn nhạy với cách khoanh hơn nhóm cục bộ.

4. **Quy tắc V rộng rãi ⇒ mọi con số "trúng vết bệnh" là cận trên.** Khoanh chặt hơn
   thì các con số đó chỉ giảm, không tăng. Kết luận tiêu cực vì vậy **vững**; kết luận
   tích cực (mục 3.2) thì nên đọc dè dặt.

5. **Lưới 14×14 không phân giải được đốm nhỏ hơn một ô (16×16 px).** Với `target_spot`
   và `bacterial_spot` — đúng hai lớp đốm nhỏ nhất — một ô V có thể chỉ chứa vài phần
   trăm là vết bệnh thật. Điều này làm diện tích V **bị thổi lên**, tức mức tập trung
   vào vết bệnh của hai lớp đó **bị đánh giá thấp đi**. Lưới mịn hơn không sửa được,
   vì bản thân Grad-CAM chỉ có 7×7.

6. **Cột "Otsu" ở mục 4 là cài lại từ mô tả**, không phải chạy lại đúng mã nguồn của
   #49 (mã đó chưa bao giờ được commit). Bốn con số tái lập ở mục 4 khớp rất sát nên
   khả năng cài sai là thấp, nhưng vẫn phải ghi ra.

7. **PlantDoc là ảnh thu từ Internet, không phải ảnh tự chụp ngoài đồng.** Giống hạn
   chế đã ghi ở `bao-cao-domain-gap.md`: **đừng gọi đây là "ảnh đồng ruộng"**, và
   **không** kết luận được gì riêng cho điều kiện canh tác ở Đà Lạt.

8. **Chưa đo phương án thay thế nào.** Báo cáo này nói Grad-CAM hiện tại làm được gì,
   **không** nói Grad-CAM++ hay lớp mục tiêu nông hơn sẽ tốt hơn. Đó là #98.

---

## 10. Cách chạy lại toàn bộ

Ảnh gốc không nằm trong Git (`model/data/`). Có checkpoint và dữ liệu rồi thì bốn
lệnh, ~3 phút trên GPU:

```bash
cd model

# 1. Chọn mẫu — cùng seed thì cùng danh sách ảnh, trên máy nào cũng vậy
python -m src.xai.audit_sample --manifest data/processed/split.csv \
    --dataset pv --per-class 3 --seed 42 --out outputs/audit-gradcam-17/mau-pv.csv
python -m src.xai.audit_sample --manifest data/processed/plantdoc-all/split.csv \
    --dataset pd --per-class 3 --seed 42 --out outputs/audit-gradcam-17/mau-pd.csv

# 2. Phiếu khoanh MÙ (không có heatmap) + dữ liệu CAM
python -m src.xai.audit_sheets --samples outputs/audit-gradcam-17/mau-pv.csv \
    --out-dir outputs/audit-gradcam-17/pv
python -m src.xai.audit_sheets --samples outputs/audit-gradcam-17/mau-pd.csv \
    --out-dir outputs/audit-gradcam-17/pd

# 3. NGƯỜI khoanh -> {pv,pd}/khoanh-tay.json   (đã có trong Git, sửa tay được)

# 4. Chấm điểm
python -m src.xai.audit_score --bo pv=outputs/audit-gradcam-17/pv \
    --bo pd=outputs/audit-gradcam-17/pd --out-dir outputs/audit-gradcam-17

# 5. Bản đối chiếu có heatmap — CHỈ chạy sau bước 3, nếu không là mất tính khoanh mù
python -m src.xai.audit_sheets --samples outputs/audit-gradcam-17/mau-pv.csv \
    --out-dir outputs/audit-gradcam-17/pv --overlay
```

### 10.1. File nào theo Git, file nào không

| Theo Git | Không theo Git |
|---|---|
| `khoanh-tay.json` — **mặt nạ khoanh tay, thứ duy nhất máy không tái tạo được** | `{pv,pd}/phieu/` — phiếu khoanh mù (56 ảnh, ~35 MB) |
| `cam-cells.json` — CAM đã gộp về lưới 14×14 | `{pv,pd}/doi-chieu/` — bản chồng heatmap (~35 MB) |
| `ket-qua.{json,md}`, `tung-anh.csv`, `mau-*.csv` | |
| `figures/gradcam-vet-benh-17.png` | |

Hai thư mục ảnh sinh lại được bằng một lệnh nên đã thêm vào `.gitignore`.

### 10.2. Mã nguồn lần này nằm trong repo — có chủ ý

`docx/Plan_model.md` mục 6 (việc chờ chốt số 7) ghi rằng script đo của #49 chạy trong
thư mục tạm và chưa commit. Bốn module của #17 (`audit_sample`, `audit_sheets`,
`audit_score`, `audit_figure`) commit ngay từ đầu, vì mọi con số trong báo cáo này sẽ
vào báo cáo tốt nghiệp và hội đồng gần như chắc chắn hỏi "em đo thế nào".

Một thay đổi nhỏ ngoài bốn module đó: `GradCAM.__call__` nhận thêm tham số tuỳ chọn
`normalize` (mặc định `True`). Mọi chỗ gọi sẵn có — `DiseasePredictor`, `visualize.py`,
backend — không truyền gì nên **chạy y hệt như trước**; đã kiểm lại bằng cách gọi
`DiseasePredictor.predict()` sau khi sửa. Tham số này cần cho phép kiểm ở mục 7.1.
