# Báo cáo đo domain gap — mô hình chạy trên ảnh thật thì còn lại gì

> Kết quả của issue **#49 (FD-04)**, đo ngày **15/09/2026**.
> Checkpoint đo: `model/checkpoints/leaf_disease_detection_model.pt`
> (`efficientnet_b0-20260907-1443`) — **đúng checkpoint đang chạy trong app**, không
> phải bản huấn luyện lại.
>
> Mọi con số trong tài liệu này do nhóm tự đo, script và manifest đều trong repo nên
> **chạy lại được**. Lệnh cụ thể ở mục 7.

---

## 0. Một câu trả lời trước khi vào số

Câu hỏi của #49 là *"ra ảnh thật thì tụt bao nhiêu?"*. Câu trả lời:

> **Từ 99,60 % xuống 30,81 %. Tụt 68,8 điểm.**

Con số này xấu, và nó **phải được báo cáo đúng như vậy**. Ba lý do nó vẫn là một kết
quả tốt cho đồ án, chứ không phải một thất bại:

1. **Nó gần như trùng khớp với công bố của chính tác giả PlantVillage** (bài A1:
   99,35 % → 31,40 %). Nhóm không đo ra một con số lạ — nhóm đo lại được đúng hiện
   tượng mà tài liệu đã mô tả, trên mô hình của mình. Đó là bằng chứng phép đo đúng.
2. **Nó chỉ ra đúng chỗ cần sửa**, chứ không chỉ nói "mô hình kém" — xem mục 3 (mô
   hình dồn 85 % dự đoán vào 3 lớp) và mục 5 (Grad-CAM suy biến về mức ngẫu nhiên).
3. **Nó bác bỏ một hướng sửa sai.** Mục 4 chứng minh bằng số rằng ngưỡng tin cậy —
   hướng mà issue #47 đề xuất — **không cứu được** vấn đề này.

---

## 1. Đo trên bộ nào, và vì sao không phải bộ đã định

Kế hoạch ban đầu (#20) là tự chụp 50–100 ảnh ngoài đồng. **Không thực hiện được** —
nhóm không liên hệ được nhà vườn. Kế hoạch dự phòng là bộ **H1** (Data in Brief 2025,
công bố "731 ảnh đồng ruộng Bangladesh").

**H1 cũng không dùng được**, phát hiện ngày 15/09 khi tải về kiểm: bản phát hành trên
Mendeley là export Roboflow/YOLO **không kèm `data.yaml`**, nên không biết class ID nào
ứng với bệnh nào; 230 trong 689 ảnh có nhãn của nhiều lớp; và "731 ảnh" thật ra là 302
ảnh gốc bị nhân bản. Chi tiết đầy đủ ở `Plan_model.md` mục 5.2.

Bộ dùng cuối cùng: **PlantDoc** (Singh et al., CoDS-COMAD 2020), phần cà chua.

### 1.1. Số ảnh thật, tự đếm

| Lớp của đề tài | PlantDoc `train` | PlantDoc `test` |
|---|---|---|
| `bacterial_spot` | 101 | 9 |
| `early_blight` | 79 | 9 |
| `late_blight` | 101 | 10 |
| `leaf_mold` | 85 | 6 |
| `septoria_leaf_spot` | 140 | 11 |
| `yellow_leaf_curl_virus` | 70 | 6 |
| `mosaic_virus` | 44 | 10 |
| `healthy` | 55 | 8 |
| **8 lớp dùng được** | **675** | **69** |
| `spider_mites` | 2 | 0 |
| `target_spot` | *không có thư mục* | — |

**744 ảnh trên 8 lớp.** Hai lớp không đo được: `target_spot` (PlantDoc không có) và
`spider_mites` (2 ảnh — n=2 không nói được gì, và một trong hai file tên
`comparing-diseases-4-canker-tomato…`, tức nhãn của chính nó cũng đáng nghi).

### 1.2. Ba vấn đề toàn vẹn của PlantDoc và cách xử lý

Kiểm bằng sha256 trên toàn bộ 746 file. **Bản chia `train`/`test` của chính PlantDoc bị
rò rỉ: 3 ảnh trùng byte tuyệt đối** nằm đồng thời ở cả hai bên (3 cặp file).

| File | Vị trí | Xử lý |
|---|---|---|
| `early-blight-septoria-ls-fig-3.jpg` | `train` + `test`, cùng lớp `septoria_leaf_spot` | Giữ 1 bản |
| `tylcv-seminar-1-638.jpg` | `train` + `test`, cùng lớp `yellow_leaf_curl_virus` | Giữ 1 bản |
| **`tomato_V8.jpg`** | `test/bacterial_spot` **và** `train/septoria_leaf_spot` | **Loại hẳn** |

Ca thứ ba nghiêm trọng hơn hai ca đầu: **cùng một ảnh, hai nhãn khác nhau**. Không có
cách biết nhãn nào đúng, và giữ lại thì dù mô hình trả lời gì cũng có một nhãn gọi nó
là sai — nên loại.

Kết quả sau khi lọc: **742 ảnh** (chế độ đo chính), trong đó 740 thuộc 8 lớp so sánh
được. Toàn bộ danh sách ảnh bị loại kèm lý do nằm trong
`model/data/processed/plantdoc-all/audit.json` — máy sinh ra, không phải chép tay.

### 1.3. Vì sao đo trên cả 742 ảnh, không chỉ trên phần `test`

`train` của PlantDoc **không phải** tập huấn luyện của đề tài. Checkpoint hiện tại
huấn luyện 100 % trên PlantVillage và **chưa từng thấy một ảnh PlantDoc nào**, nên đo
trên toàn bộ là hợp lệ và cho thống kê tốt nhất (742 thay vì 66 ảnh).

Con số này vì vậy **đúng vĩnh viễn**, kể cả sau khi #50 fine-tune bằng PlantDoc
`train` — vì nó được đo *trước* khi điều đó xảy ra. Để #50 có mốc so trước/sau đúng
trên cùng những ảnh, nhóm đo thêm riêng 66 ảnh `test` (mục 2.2).

---

## 2. Kết quả chính

### 2.1. Domain gap, so 1:1 trên đúng 8 lớp

Cột PlantVillage **đã lọc còn đúng 8 lớp** mà PlantDoc đo được. So 10 lớp với 8 lớp là
so hai bài toán khác độ khó — phải lọc, nếu không con số chênh lệch bị thổi phồng.

| Chỉ số | PlantVillage test (n=2.258) | **PlantDoc (n=740)** | Chênh |
|---|---|---|---|
| **Accuracy** | **99,60 %** | **30,81 %** | **−68,79 điểm** |
| Khoảng tin cậy 95 % | 99,24 – 99,79 % | 27,59 – 34,23 % | *không chồng lấn* |
| Macro-F1 (8 lớp) | 0,9970 | 0,2331 | −0,7639 |
| Top-3 accuracy | 100,00 % | 62,70 % | −37,30 điểm |

Hai khoảng tin cậy **không chồng lấn**, nên chênh lệch này không thể do ngẫu nhiên của
phép lấy mẫu.

Một chi tiết đáng nói khi trình bày: accuracy PlantVillage lọc còn 8 lớp vẫn là
**99,60 %** — đúng bằng con số trên đủ 10 lớp đã báo cáo ở #15. Nghĩa là việc bỏ 2 lớp
ra **không** làm bài toán dễ đi, nên không ai nói được rằng nhóm chọn tập lớp cho dễ.

### 2.2. Ba phép đo trên PlantDoc có nhất quán với nhau

| Tập đo | n | Accuracy | KTC 95 % |
|---|---|---|---|
| Toàn bộ, 9 lớp có mặt | 742 | 30,73 % | 27,51 – 34,14 % |
| **8 lớp so sánh được** | **740** | **30,81 %** | **27,59 – 34,23 %** |
| Riêng `test` gốc của PlantDoc | 66 | 28,79 % | 19,27 – 40,64 % |

Con số trên 66 ảnh **nằm trong** khoảng tin cậy của phép đo chính — hai phép đo độc lập
cho cùng một kết luận. Nhưng khoảng tin cậy của nó rộng tới 21 điểm, nên **đừng trích
con số 28,79 % như một con số chính xác**; nó tồn tại để làm mốc cho #50, không để báo cáo.

### 2.3. Đối chiếu tài liệu — chỗ mạnh nhất của kết quả này

| Nguồn | Trong phòng | Ảnh điều kiện khác | Tụt |
|---|---|---|---|
| **Nhóm (bài này)** | **99,60 %** | **30,81 %** | **68,8 điểm** |
| **A1** — chính tác giả PlantVillage | 99,35 % | 31,40 % | 67,9 điểm |
| **A3** — review 2024, trung bình nhiều công bố | 90,18 % | 84,66 % | 5,5 điểm |

Kết quả của nhóm **lệch 0,6 điểm so với A1** ở con số cuối. Đây là điều đáng nhấn mạnh
khi bảo vệ: nhóm không đo ra một con số bất thường, mà **tái hiện được đúng hiện tượng
đã công bố** bằng phép đo độc lập của mình.

Lưu ý khi trích A1 cho công bằng (đã ghi trong `model/research/03-tong-hop-doi-chieu.md`):
A1 đo trên 38 lớp của 14 loài cây, bài toán khó hơn 10 lớp một loài. Việc hai con số
gần nhau là **trùng hợp có ý nghĩa về độ lớn**, không phải hai phép đo tương đương.

Khoảng cách với A3 (chỉ tụt 5,5 điểm) cũng phải giải thích, đừng bỏ qua: A3 là trung
bình của nhiều công bố mà **phần lớn đã fine-tune trên dữ liệu thực địa** — tức là đã
làm đúng việc mà #50 sắp làm. Con số 68,8 điểm của nhóm là **mức tụt khi chưa làm gì
cả**, nên so với A3 là so hai trạng thái khác nhau.

---

## 3. Lớp nào rớt, và mô hình dồn dự đoán vào đâu

### 3.1. Recall từng lớp

| Lớp | PlantVillage | PlantDoc | Chênh | n (PD) |
|---|---|---|---|---|
| `mosaic_virus` | 1,00 | **0,02** | −0,98 | 54 |
| `leaf_mold` | 1,00 | **0,02** | −0,98 | 91 |
| `bacterial_spot` | 0,99 | **0,04** | −0,95 | 109 |
| `healthy` | 1,00 | **0,08** | −0,92 | 63 |
| `septoria_leaf_spot` | 0,99 | 0,34 | −0,65 | 149 |
| `yellow_leaf_curl_virus` | 1,00 | 0,44 | −0,56 | 75 |
| `late_blight` | 0,99 | **0,67** | −0,32 | 111 |
| `early_blight` | 1,00 | **0,66** | −0,34 | 88 |

Bốn lớp gần như **mất hẳn** (recall ≤ 0,08). Hai lớp giữ được khá là `early_blight` và
`late_blight` — nhưng mục tiếp theo cho thấy đó không phải tin tốt.

### 3.2. Phát hiện quan trọng nhất: mô hình sụp về 3 lớp

Đếm số lần mỗi lớp **được dự đoán** trên 742 ảnh:

| Lớp | Thật có | Được đoán | Tỉ lệ dự đoán |
|---|---|---|---|
| `early_blight` | 88 | **264** | **35,6 %** |
| `late_blight` | 111 | **246** | **33,2 %** |
| `septoria_leaf_spot` | 149 | 121 | 16,3 % |
| `yellow_leaf_curl_virus` | 75 | 60 | 8,1 % |
| `healthy` | 63 | 29 | 3,9 % |
| `bacterial_spot` | 109 | 12 | 1,6 % |
| `leaf_mold` | 91 | 5 | 0,7 % |
| `mosaic_virus` | 54 | 2 | 0,3 % |
| `spider_mites` | 2 | 2 | 0,3 % |
| `target_spot` | **0** | **1** | 0,1 % |

**Ba lớp chiếm 85,0 % toàn bộ dự đoán.** `early_blight` được đoán gấp 3 lần số ảnh
thật có. Và `target_spot` bị đoán 1 lần dù bộ đo **không có ảnh nào** thuộc lớp đó.

Đây không phải "suy giảm đều" — đây là **sụp về một vài lớp**. Cách đọc đúng: khi gặp
ảnh ngoài phân phối đã học, mô hình mất khả năng phân biệt chi tiết và rơi về mấy lớp
"tổng quát" nhất — đại khái *"lá có vết nâu"* (`early_blight`/`late_blight`) và *"lá có
đốm sẫm"* (`septoria_leaf_spot`).

### 3.3. Cặp nhầm nhiều nhất

| Thật | Bị đoán thành | Số ảnh | % của lớp |
|---|---|---|---|
| `septoria_leaf_spot` | `early_blight` | 66 | 44 % |
| `bacterial_spot` | `early_blight` | 55 | 50 % |
| `leaf_mold` | `late_blight` | 53 | 58 % |
| **`healthy`** | **`late_blight`** | **33** | **52 %** |
| `late_blight` | `early_blight` | 31 | 28 % |
| `bacterial_spot` | `septoria_leaf_spot` | 22 | 20 % |

**Dòng `healthy` → `late_blight` là dòng đáng chú ý nhất về mặt sản phẩm, và nó đảo
chiều so với kết quả trên PlantVillage.**

Ở #15, ca nguy hiểm nhất trên PlantVillage là **1 ảnh** mốc sương muộn bị gọi là lá
khoẻ — bỏ sót bệnh. Trên ảnh thật thì chiều ngược lại: **52 % lá khoẻ bị gọi là mốc
sương muộn**. Với ứng dụng cho nông dân, đây là **báo động giả**, hướng an toàn hơn bỏ
sót bệnh, nhưng phá vỡ lòng tin và có thể khiến người ta phun thuốc không cần thiết —
đúng thứ đề tài muốn tránh. Phải nói thẳng điều này trong báo cáo.

---

## 4. Ngưỡng tin cậy có cứu được không? — Không

Issue **#47** đề xuất đặt ngưỡng tin cậy tối thiểu. Câu hỏi: trên ảnh thật thì ngưỡng
đó mua được gì? Đo trên 742 ảnh PlantDoc:

**Độ tin cậy khi đúng và khi sai**

| Tập | | n | Trung vị | Trung bình | > 0,9 |
|---|---|---|---|---|---|
| PlantDoc | khi **đúng** | 228 | 0,773 | 0,708 | 26,8 % |
| PlantDoc | khi **sai** | 514 | 0,528 | 0,568 | **9,1 %** |
| PlantVillage | khi đúng | 2.249 | 0,964 | 0,951 | 91,8 % |

Hai điều đọc được ngay: trên ảnh thật, mô hình **tự tin thấp hơn hẳn** kể cả khi đúng
(0,773 so với 0,964) — nên tín hiệu tin cậy *có* mang thông tin. Nhưng **9,1 % các ca
sai vẫn có độ tin cậy trên 0,9**.

**Đặt ngưỡng thì được gì, mất gì**

| Ngưỡng | PlantDoc còn trả lời | Accuracy phần còn lại | Số ca vẫn sai mà vẫn trả lời | PlantVillage bị chặn oan |
|---|---|---|---|---|
| — (không ngưỡng) | 100,0 % | 30,73 % | 514 / 514 | 0,0 % |
| 0,50 | 60,5 % | 38,31 % | 277 | 0,2 % |
| 0,70 | 38,0 % | 47,16 % | 149 | 1,4 % |
| 0,80 | 26,1 % | 50,00 % | 97 | 3,0 % |
| **0,90** | **14,6 %** | **56,48 %** | **47** | **8,5 %** |
| 0,95 | 6,3 % | 63,83 % | 17 | 30,2 % |

**Kết luận, có số liệu chống lưng: ngưỡng tin cậy không phải cách sửa domain gap.** Ở
ngưỡng 0,90 — mức mà phiên 10/09 đo được là cần để chặn ảnh rác — hệ thống **từ chối
85,4 % ảnh thật**, và trong 14,6 % còn lại thì accuracy vẫn chỉ **56,5 %**, tức nhích
hơn tung đồng xu một chút. Cùng lúc **8,5 % ảnh PlantVillage hợp lệ bị chặn oan**.

Điều này **không** phủ định #47. Ngưỡng tin cậy vẫn cần, nhưng để làm đúng việc của
nó — **chặn ảnh không phải lá cà chua** (vấn đề 2 của phiên 10/09) — chứ không phải để
vá độ chính xác trên ảnh thật. Hai vấn đề khác nhau, đừng dùng một công cụ cho cả hai.

---

## 5. Grad-CAM trên ảnh nền phức tạp — phần đáng lo nhất cho đề tài

Đây là tiêu chí mà #49 đặt ra và cũng là chỗ liên quan trực tiếp tới đóng góp chính của
đề tài: *heatmap có còn rơi đúng vết bệnh khi nền phức tạp không?*

Đo trên 150 ảnh mỗi bộ, mặt nạ lá xấp xỉ bằng ngưỡng Otsu trên kênh bão hoà màu — **đúng
cách đã dùng ở phiên 10/09** để so được với nhau:

| | PlantDoc (ảnh thật) | PlantVillage |
|---|---|---|
| Khối lượng heatmap trong lá | 46,3 % | 55,4 % |
| Diện tích "lá" theo mặt nạ | 45,4 % | 35,1 % |
| **Mức tập trung** | **1,02×** | **1,58×** |
| Điểm nóng nhất nằm trong lá | **42 %** | 75 % |

**Cách đọc "mức tập trung":** nếu heatmap rải đều khắp ảnh thì khối lượng trong lá bằng
đúng diện tích lá, tức 1,00×. PlantVillage đo được 1,58× — Grad-CAM có ưu tiên phiến lá
rõ rệt. PlantDoc đo được **1,02×**, tức **gần như không phân biệt được với rải ngẫu
nhiên**. Điểm nóng nhất nằm trong lá chỉ 42 %, thấp hơn cả tung đồng xu.

> ⚠️ **Hạn chế của phép đo này, phải nói rõ.** Mặt nạ lá bằng ngưỡng màu **kém tin cậy
> hẳn trên PlantDoc**: nền thật có cỏ, cây khác, đất, tay người — đều bão hoà màu cao,
> nên bị tính là "lá" (diện tích mặt nạ 45,4 % so với 35,1 % của PlantVillage). Bản thân
> việc mặt nạ phình ra đã đẩy mức tập trung về gần 1,00×. Vì vậy **một phần** mức tụt
> 1,58× → 1,02× là hiện tượng của phép đo, không phải của mô hình. Con số này dùng để
> **cảnh báo**, không dùng để kết luận dứt khoát — muốn kết luận thì phải khoanh lá bằng
> tay, và đó là việc của **#17**.

### 5.1. Xem bằng mắt 16 ca đoán sai

Bảng ảnh: `model/outputs/plantdoc-all/figures/gradcam-sai-plantdoc.png` (16 ca sai, chia
đều 8 lớp, heatmap chồng lên ảnh gốc). Câu hỏi #49 đặt ra là *sai vì ảnh khó, hay vì mô
hình học nhầm đặc trưng?* — **cả hai, và tách được ra thành ba nhóm**:

**Nhóm 1 — sai vì ảnh không phải loại ảnh mô hình được huấn luyện cho (đoán được, sửa được).**
Nhiều ảnh PlantDoc là **cảnh chụp cả bụi cây** hoặc nhiều lá chồng nhau, chứ không phải
một phiến lá cận cảnh như PlantVillage. Có ảnh chụp cả giàn trong nhà kính, có ảnh lá
nằm trên nền đất lẫn cọng rơm, có ảnh người cầm lá bằng tay. Với loại ảnh này mô hình
không có lỗi gì về bệnh học — nó **bị hỏi sai câu hỏi**. Đây chính là phần mà **#93 (cắt
vùng lá trước khi phân loại)** giải quyết, và là căn cứ định lượng để nâng ưu tiên #93.

**Nhóm 2 — sai giữa các bệnh giống nhau về thị giác (lỗi thật, nhưng có lý).**
`bacterial_spot` → `septoria_leaf_spot` xảy ra trên ảnh lá đầy đốm sẫm tròn, và heatmap
**rơi đúng vào các đốm đó** (58 %, 67 % khối lượng trong lá). Mô hình nhìn đúng chỗ rồi
chọn sai giữa hai bệnh mà **cả hai đều gây đốm sẫm**. Điểm đáng chú ý: đây **cũng là cặp
nhầm nhiều nhất trên PlantVillage** (4 ảnh, theo #15). Tức kiến thức bệnh học của mô
hình không phải vô nghĩa — nó sụp về nhóm chứ không loạn.

**Nhóm 3 — sai với độ tin cậy cao trong khi nhìn ra ngoài lá (nhóm đáng lo thật).**
Hai ca rõ nhất trong bảng:

- `late_blight` → `early_blight`, **98 % tin cậy**, chỉ **23 %** khối lượng heatmap nằm
  trong lá. Rất tự tin, sai, và nhìn chủ yếu vào nền.
- `healthy` → `late_blight`, **82 % tin cậy**, 45 % trong lá. Lá xanh khoẻ rõ ràng bằng
  mắt thường, bị kết luận là mốc sương muộn.
- `mosaic_virus` → `early_blight`, 61 % tin cậy, chỉ **29 %** trong lá.

Nhóm 3 là câu trả lời cho phần thứ hai của câu hỏi: **có, trên ảnh nền phức tạp thì
heatmap chuyển sang bám vào nền ở một tỉ lệ đáng kể.** Và đúng như #49 dự đoán, đây là
**phát hiện đáng giá phải nói thẳng** — vì nó chứng minh một điều mạnh hơn cả con số
accuracy: XAI của nhóm không chỉ để trình bày cho đẹp, mà **bắt được lỗi của chính mô
hình**. Một hệ thống trả lời "mốc sương muộn 98 %" trong khi bản đồ nhiệt nằm 77 % ngoài
phiến lá là hệ thống đang nói một câu nó không có căn cứ để nói.

---

## 6. Hệ quả cho các việc còn lại

| Issue | Số đo này nói gì |
|---|---|
| **#93** cắt vùng lá trước khi phân loại | **Nâng ưu tiên.** Nhóm 1 ở mục 5.1 cho thấy một phần đáng kể lỗi đến từ việc ảnh chứa cả bụi cây thay vì một phiến lá. Đây là hướng duy nhất **không cần dữ liệu mới** |
| **#50** hướng 2 fine-tune | Mốc "trước" đã có: **28,79 %** trên 66 ảnh `test` (69 trừ 3 ảnh rò rỉ). Huấn luyện **chỉ trên** `train` — 675 ảnh 8 lớp, nên bỏ thêm `tomato_V8.jpg` vì nhãn mâu thuẫn, còn **674**. Hai ảnh rò rỉ kia giữ được trong `train` vì đã bị loại khỏi `test`. Đo lại trên đúng 66 ảnh đó |
| **#47** ngưỡng tin cậy | **Thu hẹp phạm vi.** Mục 4 chứng minh ngưỡng không vá được độ chính xác trên ảnh thật. Vẫn làm #47, nhưng để chặn ảnh không phải lá — đừng kỳ vọng nó cải thiện accuracy |
| **#17** kiểm Grad-CAM bằng mắt | **Nâng ưu tiên, và mở rộng phạm vi.** Mục 5 đo được mức tập trung tụt về 1,02× nhưng phép đo tự nó có hạn chế. #17 nay phải kiểm **cả PlantVillage lẫn PlantDoc**, khoanh lá bằng tay |
| **#98** Grad-CAM++ | Giữ nguyên thứ tự (sau #17). Nhưng lưu ý: nét hơn mà vẫn bám nền thì vô nghĩa — mục 5 làm lý lẽ này mạnh hơn trước. ⚠️ Bản đầu của báo cáo này ghi sai là #16; #16 thật là MD-07 sinh lưới ảnh minh hoạ, còn Grad-CAM++ **trước 15/09/2026 không có issue nào** — nay đã tạo **#98** |
| **#19** so kiến trúc | **Giữ nguyên mức hạ cấp.** Điểm nghẽn là 68,8 điểm domain gap, không phải 0,4 điểm còn lại trên PlantVillage. Đổi backbone không thu hẹp khoảng cách đó |
| **#95** báo cáo GVHD | Tài liệu này là nội dung chính của phần "còn thiếu" thứ ba đã ghi ở `Plan_model.md` mục 3 |

---

## 7. Cách chạy lại toàn bộ

Dữ liệu gốc **không nằm trong Git** (`model/data/field/` — theo `CLAUDE.md`). Tải lại:

```bash
# 1. Tải PlantDoc, giải nén riêng phần cà chua vào
#    model/data/field/plantdoc/{train,test}/<thư mục lớp>/
#    Nguồn: https://github.com/pratikkayal/PlantDoc-Dataset (branch master)

cd model

# 2. Sinh manifest — script tự lọc ảnh trùng byte và ảnh nhãn mâu thuẫn,
#    ghi lý do từng ảnh bị bỏ vào audit.json
python -m src.data.prepare_plantdoc --mode all      --out-dir data/processed/plantdoc-all
python -m src.data.prepare_plantdoc --mode official --out-dir data/processed/plantdoc-official

# 3. Lọc cả hai bộ còn đúng 8 lớp so sánh được
KEEP=bacterial_spot,early_blight,late_blight,leaf_mold,septoria_leaf_spot,yellow_leaf_curl_virus,mosaic_virus,healthy
python -m src.data.filter_manifest --manifest data/processed/split.csv \
    --out data/processed/plantvillage-8lop/split.csv --keep $KEEP
python -m src.data.filter_manifest --manifest data/processed/plantdoc-all/split.csv \
    --out data/processed/plantdoc-8lop/split.csv --keep $KEEP

# 4. Đánh giá — CHÚ Ý --out-dir, bỏ trống là ghi đè số liệu PlantVillage trong Git
for M in plantdoc-all plantdoc-8lop plantdoc-official plantvillage-8lop; do
  python -m src.evaluation.evaluate \
      --checkpoint checkpoints/leaf_disease_detection_model.pt \
      --manifest "data/processed/$M/split.csv" --split test --out-dir "outputs/$M"
done
```

Kết quả sinh ra (đã commit): `model/outputs/plantdoc-all/`,
`model/outputs/plantdoc-8lop/`, `model/outputs/plantdoc-official/`,
`model/outputs/plantvillage-8lop/` — mỗi thư mục có `report-test.json` và
`figures/confusion-matrix-test.png`.

### 7.1. Ba thay đổi code mà #49 buộc phải làm

Hai trong ba chỗ này **cho ra số sai mà không báo lỗi gì** — đáng ghi lại:

| Chỗ | Nếu không sửa | Đã sửa thành |
|---|---|---|
| `src/data/prepare.py` chỉ nhận tên thư mục `Tomato___*` | Tên thư mục PlantDoc rơi hết vào `unknown_dirs` → **manifest rỗng**, im lặng | Viết script riêng `src/data/prepare_plantdoc.py`, **không đụng** `prepare.py` để giữ tính tái lập của #14/#15 |
| `src/evaluation/evaluate.py` gọi `classification_report()` **không** truyền `labels=` | sklearn tự suy nhãn từ dữ liệu (8 lớp) rồi so với `target_names` (10 lớp) → `ValueError`. Chỗ **duy nhất báo lỗi** | Thêm `labels=list(range(len(keys)))` |
| `--out-dir` mặc định là `outputs/` | **Ghi đè** `report-test.json` + `confusion-matrix-test.png` của PlantVillage đang trong Git — mất số liệu #15 | Bắt buộc truyền `--out-dir` riêng; ghi cảnh báo vào docstring |

Ngoài ra `evaluate.py` được bổ sung ba chỉ số mà tập đo thiếu lớp bắt buộc phải có:
`macro_f1_present` (chỉ lớp có mặt), `macro_f1_min_support` (chỉ lớp có ≥ 5 ảnh), và
`accuracy_ci95` (khoảng tin cậy Wilson — cần vì tập `test` chỉ 66 ảnh).

Lý do phải có `macro_f1_present`: để nguyên 10 lớp thì `target_spot` và `spider_mites`
đóng góp F1 = 0 và kéo macro-F1 xuống **0,1865**, trong khi con số thật trên 8 lớp đo
được là **0,2331**. Con số 0,1865 không nói gì về mô hình, chỉ nói rằng bộ đo thiếu lớp.

---

## 8. Hạn chế của báo cáo này

Ghi lại đầy đủ để không trích quá điều đã đo:

- **PlantDoc là ảnh thu từ Internet**, không phải ảnh tác giả tự chụp ngoài đồng. Vẫn
  là phép thử domain shift hợp lệ (nền lộn xộn, nhiều lá chồng, ánh sáng tự nhiên) nhưng
  **không được gọi là "ảnh đồng ruộng"** trong báo cáo.
- **Không có ảnh cà chua Đà Lạt.** Đề tài kết luận được về domain gap **nói chung**,
  **không** kết luận được gì riêng cho điều kiện canh tác ở đây. Đừng trình bày như thể
  đã đo trên ảnh địa phương.
- **Hai lớp không đo được**: `target_spot` (PlantDoc không có) và `spider_mites` (n=2).
  Con số 30,81 % là accuracy trên **8 trong 10 lớp** của hệ thống.
- **Nhãn PlantDoc có nhiễu.** Bộ này nổi tiếng về điểm đó, và chính phép kiểm của nhóm
  tìm được hai ví dụ: `tomato_V8.jpg` mang hai nhãn khác nhau, và một ảnh
  `spider_mites` tên là `comparing-diseases-4-canker-tomato`. Nghĩa là **một phần** mức
  tụt 68,8 điểm đến từ nhãn sai của bộ đo, không phải từ mô hình. Chưa lượng hoá được
  phần đó — muốn lượng hoá thì phải kiểm nhãn 742 ảnh bằng mắt, và đó là công việc chưa
  làm.
- **Mặt nạ lá ở mục 5 là xấp xỉ tự động** và kém tin cậy trên PlantDoc — xem cảnh báo
  trong mục đó. Kết luận về Grad-CAM ở đây là **cảnh báo**, không phải kết luận dứt
  khoát; #17 mới là chỗ kết luận.
- **Chỉ xem bằng mắt 16 ảnh** trong 514 ảnh bị đoán sai. Ba nhóm ở mục 5.1 là **mô tả
  định tính**, chưa có tỉ lệ. Muốn có tỉ lệ thì phải phân loại tay nhiều ảnh hơn.
- **Đo trên máy Bảo**, GPU RTX 4060 Ti. Không liên quan tới độ chính xác nhưng liên quan
  nếu ai đó chạy lại và so thời gian.
