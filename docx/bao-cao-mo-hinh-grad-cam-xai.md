# BÁO CÁO: MÔ HÌNH NHẬN DIỆN, GRAD-CAM VÀ CƠ SỞ LÝ THUYẾT XAI

### Đối chiếu với tài liệu khoa học đã khảo sát

**Đề tài:** Ứng dụng nhận diện bệnh cây trồng kết hợp XAI (giải thích được)
**GVHD:** TS. Nguyễn Thị Lương — Khoa Công nghệ thông tin, Trường Đại học Đà Lạt
**Người thực hiện:** Đinh Lâm Gia Bảo (2212343) — phụ trách phần mô hình
**Ngày báo cáo:** 07/09/2026

> Báo cáo này bổ sung cho *Báo cáo kết quả huấn luyện mô hình* (cùng ngày). Báo cáo
> kia trả lời câu hỏi **"kết quả ra sao"**; báo cáo này trả lời **"vì sao làm như
> vậy, người khác đã làm thế nào, và nhóm học được gì từ họ"**.

---

## MỤC LỤC

- [Phần 0. Tóm tắt](#phần-0-tóm-tắt)
- [Phần I. Mô hình nhận diện](#phần-i-mô-hình-nhận-diện)
- [Phần II. Cơ sở lý thuyết XAI](#phần-ii-cơ-sở-lý-thuyết-xai)
- [Phần III. Grad-CAM](#phần-iii-grad-cam)
- [Phần IV. Khảo sát tài liệu](#phần-iv-khảo-sát-tài-liệu)
- [Phần V. Kinh nghiệm rút ra và cách áp dụng](#phần-v-kinh-nghiệm-rút-ra-và-cách-áp-dụng)
- [Phần VI. Việc tiếp theo](#phần-vi-việc-tiếp-theo)
- [Phụ lục A. Danh mục tài liệu và mức độ đã đọc](#phụ-lục-a-danh-mục-tài-liệu-và-mức-độ-đã-đọc)
- [Phụ lục B. Backbone — vì sao đóng băng rồi lại mở khoá](#phụ-lục-b-backbone--vì-sao-đóng-băng-rồi-lại-mở-khoá)
- [Phụ lục C. Vì sao không chọn ResNet, ViT hay EfficientNet-B3](#phụ-lục-c-vì-sao-không-chọn-resnet-vit-hay-efficientnet-b3)

---

## Phần 0. Tóm tắt

Nhóm đã khảo sát **46 công trình** về nhận diện bệnh cây trồng và AI giải thích được,
chia thành 8 nhóm chủ đề, trong đó **đọc kỹ 7 bài** trực tiếp liên quan tới quyết
định kỹ thuật của đề tài.

**Bốn kết luận chính:**

1. **Mô hình đã chọn là hợp lý và có căn cứ đối chiếu.** EfficientNet-B0 huấn luyện
   bằng học chuyển giao hai giai đoạn đạt **99,60%** trên tập kiểm tra, ngang với các
   công bố quốc tế trên cùng bài toán (98,3% – 99,6%).

2. **Con số 99,60% không được hiểu là năng lực thực tế.** Ba công trình độc lập cho
   thấy mô hình huấn luyện trên PlantVillage tụt rất mạnh khi gặp ảnh chụp ngoài đồng
   — trong đó **chính tác giả của bộ dữ liệu** báo cáo tụt từ 99,35% xuống **31,40%**.

3. **Điểm khác biệt của đề tài nằm ở khâu diễn giải, không ở khâu phân loại.** Công
   trình gần nhất tìm được (XSE-TomatoNet, 2025) cũng dùng EfficientNet-B0 và
   Grad-CAM trên cà chua, nhưng dừng ở bản đồ nhiệt kỹ thuật. Đề tài này đi tiếp một
   bước: chuyển thành vùng khoanh kèm câu tiếng Việt cho nông dân.

4. **Một cảnh báo ban đầu đã được kiểm chứng là không xảy ra.** Nhóm lo lớp thiểu số
   (*virus khảm*, ít hơn lớp đông nhất 14,4 lần) sẽ bị bỏ sót; thực tế lớp này đạt
   F1 = 1,0000. Tài liệu đối chiếu cho thấy đây không phải may mắn mà có lý do.

---

## Phần I. Mô hình nhận diện

### 1.1. Vì sao chọn bài toán phân loại ảnh

Trong thị giác máy tính có ba cách tiếp cận cho bài toán bệnh cây:

| Cách tiếp cận | Đầu ra | Chi phí gán nhãn | Công trình đại diện |
|---|---|---|---|
| **Phân loại ảnh** *(nhóm chọn)* | Một nhãn bệnh cho cả ảnh | Chỉ cần nhãn thư mục | A1, B2, B3, D4 |
| Phát hiện đối tượng | Khung bao quanh từng vết bệnh | Phải vẽ khung tay từng ảnh | G5–G8 (họ YOLO) |
| Phân đoạn ảnh | Mặt nạ pixel của vùng bệnh | Phải tô từng pixel | A4 (review có nhắc) |

**Lý do chọn phân loại:** bộ PlantVillage chỉ cung cấp nhãn ở mức thư mục, không có
khung bao hay mặt nạ. Chuyển sang phát hiện đối tượng đồng nghĩa phải **gán nhãn lại
toàn bộ 18.160 ảnh bằng tay** — bất khả thi trong khung thời gian đồ án.

Điều đáng chú ý: **Grad-CAM cho phép nhóm có được thứ gần giống khoanh vùng mà không
cần nhãn khung bao.** Đây là lợi ích kép ít được nói tới — kỹ thuật XAI vừa phục vụ
mục tiêu giải thích, vừa bù đắp cho hạn chế của dữ liệu. Đây là một lập luận nên nêu
khi bảo vệ, vì hội đồng có thể hỏi "sao không dùng YOLO để khoanh vùng cho chuẩn".

### 1.2. Vì sao chọn EfficientNet-B0

**Bảng 1. Các kiến trúc được cân nhắc**

| Kiến trúc | Tham số | Nhận xét | Quyết định |
|---|---:|---|---|
| **EfficientNet-B0** | **4,0 triệu** | Nhẹ, độ chính xác cao, có sẵn trọng số ImageNet trong torchvision | **Đã chọn** |
| ResNet18 | 11,7 triệu | Đơn giản, kinh điển, dễ giải thích | Để so sánh (#19) |
| ResNet50 | 25,6 triệu | Mạnh hơn nhưng nặng gấp 6 lần | Để so sánh |
| EfficientNet-B3 | 12,2 triệu | Chính xác hơn chút ít, chậm hơn đáng kể | Để so sánh |
| ViT / Swin Transformer | 86 triệu+ | Kết quả tốt (B4: 99,17%) nhưng rất nặng | Không làm — xem 1.2.2 |

#### 1.2.1. Nguyên lý của EfficientNet

EfficientNet dựa trên ý tưởng **compound scaling** (Tan & Le, 2019): thay vì phóng to
mạng theo một chiều duy nhất — sâu hơn (nhiều tầng), rộng hơn (nhiều kênh), hoặc ảnh
vào lớn hơn — thì phóng cả ba chiều **cùng lúc theo một tỉ lệ cân đối**.

Trực giác đằng sau: nếu chỉ tăng độ sâu mà không tăng độ rộng thì mạng sâu nhưng
"hẹp", không đủ kênh để mang thông tin; nếu chỉ tăng kích thước ảnh vào mà không tăng
độ sâu thì mạng không đủ tầng để tổng hợp chi tiết mới. Ba chiều phải đi cùng nhau.

Nhờ vậy EfficientNet-B0 chỉ có **4,0 triệu tham số** — ít hơn ResNet50 sáu lần — mà
vẫn cho độ chính xác tương đương hoặc hơn trên ImageNet.

> **Ghi chú trung thực về nguồn:** phần nguyên lý trên là kiến thức nền tảng phổ biến;
> nhóm **chưa mở toàn văn** bài gốc *EfficientNet: Rethinking Model Scaling for
> Convolutional Neural Networks* (Tan & Le, ICML 2019, arXiv:1905.11946). Cần bổ sung
> vào danh mục và đọc trước khi nộp báo cáo cuối, vì đây là bài **bắt buộc phải trích
> dẫn** khi đã dùng kiến trúc của họ.

#### 1.2.2. Vì sao không dùng Vision Transformer

Đây là câu hội đồng có khả năng hỏi, vì Transformer đang là xu hướng.

Bằng chứng từ tài liệu: bài **B4** (*Early detection of tomato leaf diseases using
transformers and transfer learning*, Eur. J. Agronomy 2025) báo cáo ViT-Base đạt
**99,17%** trên PlantVillage. Bài **B6** báo cáo DenseNet121 đạt **99,61%**.

Nghĩa là Transformer **ngang chứ không vượt** CNN trên bài toán này, trong khi số
tham số lớn hơn hơn 20 lần. Với ràng buộc của đề tài — suy luận phải nhanh trên máy
demo, có thể không có GPU — đánh đổi đó không có lợi.

> Cách trả lời đề nghị: *"Em có khảo sát. Trên đúng bài toán này Transformer đạt
> 99,17%, không vượt CNN, mà nặng hơn hơn hai mươi lần. Nhóm ưu tiên tốc độ suy luận
> vì hệ thống phải chạy thật lúc demo."*

### 1.3. Học chuyển giao hai giai đoạn

Nhóm **không huấn luyện từ số không**. Backbone EfficientNet-B0 lấy trọng số đã học
sẵn trên ImageNet (1,2 triệu ảnh đời thường), sau đó dạy thêm phần chuyên môn.

**Bảng 2. Chiến lược hai giai đoạn**

| Giai đoạn | Epoch | Backbone | Learning rate | Mục đích |
|---|---|---|---|---|
| 1 | 1 – 3 | **Đóng băng** | 0,0003 | Để lớp phân loại mới (khởi tạo ngẫu nhiên) ổn định trước |
| 2 | 4 – 25 | **Mở khoá** | 0,00003 (giảm 10 lần) | Tinh chỉnh nhẹ toàn mạng |

**Vì sao phải đóng băng trước:** lớp phân loại mới có trọng số ngẫu nhiên nên lúc đầu
sai rất nhiều, sinh ra gradient lớn. Nếu để gradient đó lan ngược vào backbone ngay
thì nó sẽ **phá hỏng kiến thức tốt** mà backbone tích luỹ từ ImageNet.

**Kết quả thực nghiệm xác nhận lập luận này:** trong 3 epoch đóng băng, độ chính xác
chỉ đạt 87,42%. Ngay epoch 4 — epoch đầu tiên sau khi mở khoá — độ chính xác **nhảy
vọt 7,5 điểm phần trăm** lên 94,89%.

Đây là chi tiết đáng nêu khi bảo vệ: nhóm không chỉ áp dụng một kỹ thuật theo sách,
mà **có số đo chứng minh kỹ thuật đó hoạt động đúng như thiết kế**.

### 1.4. Kết quả đạt được

**Bảng 3. Tóm tắt kết quả (chi tiết ở báo cáo huấn luyện cùng ngày)**

| Chỉ số | Giá trị |
|---|---|
| Độ chính xác tập kiểm tra | **99,60%** |
| Macro F1 (10 lớp tính ngang nhau) | **99,55%** |
| Top-3 accuracy | 100,00% |
| Số ảnh sai | 11 / 2.719 |
| Thời gian huấn luyện | 29,6 phút (25 epoch, RTX 4060 Ti) |
| Kích thước mô hình | 15,6 MB — 4.020.358 tham số |
| Tốc độ suy luận (GPU) | 31–34 ms/ảnh |

---

## Phần II. Cơ sở lý thuyết XAI

### 2.1. XAI là gì và vì sao đề tài này bắt buộc phải có

**XAI (Explainable Artificial Intelligence)** là nhóm kỹ thuật giúp con người hiểu
**vì sao** một mô hình đưa ra kết luận, thay vì chỉ nhận một đáp án từ "hộp đen".

Mạng nơ-ron sâu là hộp đen theo đúng nghĩa kỹ thuật: 4 triệu tham số của
EfficientNet-B0 không có tham số nào tương ứng với một khái niệm con người hiểu được.
Không ai — kể cả người viết ra nó — nhìn vào bảng trọng số mà nói được vì sao mô hình
kết luận "mốc sương muộn".

**Vì sao điều này quan trọng với riêng đề tài này**, chứ không phải chỉ là điểm cộng
kỹ thuật:

Bài **D9** (*Explainability Needs in Agriculture*, arXiv 2025) khảo sát **40 nông dân
thật** và kết luận: người dùng cuối **không quan tâm mô hình hoạt động ra sao**, họ
cần **diễn giải được kết quả và các yếu tố dẫn tới kết quả đó**. Nghiên cứu này cũng
chỉ ra nhu cầu giải thích **không đồng nhất** — họ phân được 5 nhóm người dùng, có
nhóm chỉ muốn ít thông tin, có nhóm muốn minh bạch hoàn toàn.

Bài **D10** (IFPRI) nêu hệ quả thực tế: nếu nông dân dùng ứng dụng AI để ra quyết
định ảnh hưởng tới sinh kế mà **không hiểu vì sao** hệ thống khuyên vậy, họ sẽ **bỏ
qua khuyến nghị hoặc bỏ luôn cả hệ thống**.

> **Đây là căn cứ học thuật cho quyết định thiết kế cốt lõi của đề tài.** Không phải
> nhóm tự nghĩ ra rằng nông dân cần lời giải thích dễ hiểu — có nghiên cứu khảo sát
> người dùng thật chứng minh điều đó.

Còn một lý do thứ hai, thuần kỹ thuật: **XAI dùng để bắt lỗi mô hình.** Xem mục 2.1.1.

#### 2.1.1. Học tắt — vấn đề mà chỉ XAI phát hiện được

**Học tắt (shortcut learning)** là hiện tượng mô hình đạt điểm cao nhưng dựa vào dấu
hiệu sai. Ví dụ: nếu ảnh của một lớp bệnh tình cờ hay được chụp trên nền sáng hơn, mô
hình có thể học "nền sáng = bệnh đó" thay vì nhìn vết bệnh.

Bài **A2** (*Uncovering bias in the PlantVillage dataset*, Noyan 2022) đã chứng minh
điều này **xảy ra thật trên chính bộ dữ liệu nhóm đang dùng**:

> Tác giả huấn luyện một mô hình **chỉ dùng 8 điểm ảnh lấy từ phần nền**, không hề
> nhìn thấy chiếc lá. Mô hình đó đạt **49,0%** độ chính xác, trong khi đoán mò chỉ
> được 2,63%. Tác giả còn cho thấy **xoá nền đi cũng không loại bỏ được thiên lệch**.

Nghĩa là nhãn bệnh đã "rò rỉ" vào phần nền của ảnh. Một mô hình đạt 99% hoàn toàn có
thể đang lấy một phần điểm số từ chỗ không phải vết bệnh.

**Chỉ có công cụ XAI mới phát hiện được chuyện này.** Không có Grad-CAM thì nhìn vào
bảng chỉ số 99,60% không ai biết mô hình đang nhìn đâu. Đây là lý do việc kiểm tra
Grad-CAM (#17) được đặt làm **cổng kiểm soát bắt buộc** trước khi làm giao diện.

### 2.2. Phân loại các phương pháp XAI

Để chọn được phương pháp phù hợp cần biết bản đồ chung của lĩnh vực. Có bốn trục phân
loại thường dùng:

**Bảng 4. Bốn trục phân loại phương pháp XAI**

| Trục | Hai đầu | Đề tài thuộc đầu nào |
|---|---|---|
| **Thời điểm** | *Ante-hoc* (mô hình tự thân dễ hiểu, như cây quyết định) ↔ *Post-hoc* (giải thích một mô hình hộp đen đã huấn luyện xong) | **Post-hoc** — vì cần độ chính xác của mạng sâu |
| **Phạm vi** | *Local* (giải thích một dự đoán cụ thể) ↔ *Global* (giải thích hành vi chung của mô hình) | **Local** — nông dân cần biết vì sao **ảnh của họ** ra kết quả đó |
| **Tính phụ thuộc** | *Model-specific* (chỉ dùng được cho một loại mô hình) ↔ *Model-agnostic* (dùng cho mô hình bất kỳ) | **Model-specific** — Grad-CAM cần truy cập vào tầng tích chập bên trong |
| **Dạng đầu ra** | *Feature attribution* (chỉ ra vùng/đặc trưng quan trọng) ↔ *Example-based* (đưa ví dụ tương tự) ↔ *Concept-based* (khái niệm mức cao) | **Feature attribution** dạng bản đồ nhiệt không gian |

**Ba phương pháp XAI cho ảnh phổ biến nhất trong tài liệu đã khảo sát:**

| Phương pháp | Nguyên lý | Ưu | Nhược |
|---|---|---|---|
| **Grad-CAM** | Dùng gradient chảy vào tầng tích chập cuối để xác định vùng ảnh có ảnh hưởng | Nhanh (một lượt lan truyền xuôi + ngược), bám sát cơ chế thật của mô hình | Bản đồ thô, phụ thuộc kiến trúc CNN |
| **LIME** | Xáo trộn ảnh nhiều lần, xem dự đoán đổi ra sao, khớp một mô hình tuyến tính đơn giản quanh điểm đó | Dùng được cho mô hình bất kỳ | Chậm (hàng nghìn lượt suy luận mỗi ảnh), kết quả **không ổn định** giữa các lần chạy |
| **SHAP** | Dựa trên lý thuyết trò chơi, chia công bằng "đóng góp" cho từng đặc trưng | Có nền tảng toán học chặt chẽ | Rất chậm với ảnh |

> **Ghi chú trung thực về nguồn:** bài gốc của LIME (Ribeiro et al., KDD 2016,
> arXiv:1602.04938) và SHAP (Lundberg & Lee, NeurIPS 2017, arXiv:1705.07874) **nhóm
> chưa mở toàn văn**. Phần mô tả trên là kiến thức nền tảng. Vì đề tài **không dùng**
> hai phương pháp này nên chỉ cần trích dẫn ở mức nhắc tới phương án đã cân nhắc,
> không cần đọc sâu.

### 2.3. Vì sao đề tài chọn Grad-CAM

Ba lý do, xếp theo mức quan trọng:

1. **Tốc độ.** Grad-CAM chỉ cần một lượt lan truyền xuôi và một lượt ngược — cùng
   bậc chi phí với chính việc dự đoán. LIME cần hàng nghìn lượt suy luận cho **một**
   ảnh. Hệ thống của nhóm phải trả kết quả cho nông dân trong thời gian thực, nên
   LIME loại ngay từ đầu.

2. **Đầu ra đúng dạng cần.** Grad-CAM cho bản đồ nhiệt **không gian hai chiều**, tức
   chỉ thẳng được "chỗ này trên lá". Đây chính là thứ chuyển được thành vùng khoanh.
   Đầu ra dạng bảng số của SHAP không dùng trực tiếp cho mục đích đó.

3. **Có tiền lệ trong đúng lĩnh vực.** Bài **D4** (XSE-TomatoNet) dùng Grad-CAM và
   Grad-CAM++ trên đúng bài toán bệnh lá cà chua. Bài **D7** dùng cho bệnh khoai tây.
   Nghĩa là lựa chọn này đã được cộng đồng nghiên cứu chấp nhận, không phải sáng kiến
   mạo hiểm.

---

## Phần III. Grad-CAM

### 3.1. Dòng dõi phương pháp

**Bảng 5. Bốn thế hệ của họ CAM**

| Thế hệ | Phương pháp | Đóng góp | Hạn chế còn lại |
|---|---|---|---|
| 2016 | **CAM** (Zhou et al.) | Ý tưởng gốc: dùng trọng số lớp cuối để xác định vùng ảnh quan trọng | **Bắt buộc phải sửa kiến trúc mạng** và huấn luyện lại |
| 2017 | **Grad-CAM** (Selvaraju et al.) — *đề tài đang dùng* | Dùng gradient thay cho trọng số → áp dụng được cho **mạng bất kỳ, không cần sửa, không cần huấn luyện lại** | Bản đồ thô; yếu khi có nhiều vết rời rạc |
| 2018 | **Grad-CAM++** (Chattopadhay et al.) | Dùng tổ hợp có trọng số của các **đạo hàm riêng dương** → định vị tốt hơn khi có **nhiều thể hiện rời rạc của cùng một lớp** và khi đối tượng chỉ xuất hiện một phần | Vẫn phụ thuộc gradient |
| 2020 | **Score-CAM** (Wang et al.) | Bỏ hẳn gradient, dùng điểm số đầu ra → ổn định hơn | **Chậm hơn nhiều lần** |

Đây là dòng dõi cần trình bày trong báo cáo cuối, vì nó cho thấy nhóm hiểu **vị trí
của phương pháp mình dùng trong lịch sử lĩnh vực**, chứ không chỉ nhặt một kỹ thuật
rồi dùng.

### 3.2. Grad-CAM hoạt động thế nào

Ý tưởng gốc (Selvaraju et al., 2017): tầng tích chập cuối cùng của một CNN là nơi
**vừa còn thông tin vị trí, vừa đã đủ trừu tượng để mang ngữ nghĩa**. Với ảnh vào
224×224, tầng cuối của EfficientNet-B0 cho lưới **7×7** — tức mỗi ô tương ứng khoảng
32×32 điểm ảnh trên ảnh gốc.

Bốn bước:

**Bước 1 — Lấy feature map.** Cho ảnh chạy qua mạng, giữ lại đầu ra của tầng tích
chập cuối: một chồng $C$ bản đồ đặc trưng $A^k$, mỗi bản đồ kích thước $7\times7$.
Mỗi bản đồ ứng với một "bộ dò" đã học được, ví dụ một bản đồ có thể sáng lên ở chỗ có
đốm nâu tròn.

**Bước 2 — Tính gradient.** Lấy điểm số $y^c$ của lớp bệnh được dự đoán, tính đạo hàm
của nó theo từng ô của từng bản đồ đặc trưng. Gradient lớn nghĩa là **thay đổi ô đó
một chút sẽ làm điểm số của lớp $c$ đổi nhiều** — tức ô đó quan trọng.

**Bước 3 — Tính trọng số mỗi kênh.** Lấy trung bình gradient trên toàn bộ không gian
của mỗi bản đồ:

$$\alpha_k^c = \frac{1}{Z}\sum_i\sum_j \frac{\partial y^c}{\partial A_{ij}^k}$$

Con số $\alpha_k^c$ trả lời: *"bộ dò thứ $k$ quan trọng cỡ nào với kết luận này?"*

**Bước 4 — Cộng có trọng số rồi bỏ phần âm.**

$$L^c_{\text{Grad-CAM}} = \mathrm{ReLU}\left(\sum_k \alpha_k^c A^k\right)$$

Hàm **ReLU** ở đây có vai trò quan trọng và hay bị hỏi: nó **giữ lại chỉ những vùng
ủng hộ lớp $c$**, bỏ những vùng ủng hộ lớp khác. Không có ReLU thì bản đồ sẽ lẫn cả
bằng chứng chống lại kết luận, gây hiểu nhầm cho người xem.

Cuối cùng phóng bản đồ $7\times7$ về kích thước ảnh gốc bằng nội suy song tuyến tính.

### 3.3. Nhóm cài đặt như thế nào

Nhóm **tự cài đặt bằng hook của PyTorch** (`model/src/xai/gradcam.py`, khoảng 60
dòng) thay vì gọi thư viện `pytorch-grad-cam` có sẵn.

**Bảng 6. Chi tiết cài đặt**

| Hạng mục | Lựa chọn của nhóm |
|---|---|
| Tầng lấy đặc trưng | `model.features[-1]` với EfficientNet · `model.layer4[-1]` với ResNet |
| Cách bắt dữ liệu | `register_forward_hook` để bắt activation, `register_hook` trên tensor để bắt gradient |
| Trọng số kênh | Trung bình gradient trên hai chiều không gian |
| Xử lý dấu | `ReLU` sau khi cộng có trọng số |
| Phóng kích thước | Nội suy song tuyến tính về đúng kích thước ảnh vào |
| Chuẩn hoá | Min-max về khoảng 0..1 **theo từng ảnh** |
| Ngưỡng tạo vùng khoanh | `heatmap_threshold: 0.5` trong `configs/default.yaml` |

**Vì sao tự cài đặt thay vì dùng thư viện** — ba lý do, nên nêu khi bảo vệ:

1. **Để giải thích được trước hội đồng.** Gọi thư viện thì khi bị hỏi "ReLU ở đó để
   làm gì" sẽ không trả lời được. Tự viết 60 dòng thì nắm từng bước.
2. **Không phụ thuộc phiên bản.** Thư viện ngoài đổi API là hỏng cả luồng.
3. **Interface giữ tương thích** với `pytorch-grad-cam`, nên nếu sau này muốn đổi
   sang thư viện đó — hoặc dùng nó để **đối chiếu kiểm tra** — thì không phải sửa chỗ
   gọi.

> Điểm 3 là việc nên làm trong #16: chạy thư viện `pytorch-grad-cam` trên cùng ảnh,
> so kết quả với bản tự viết. Nếu trùng khớp thì có bằng chứng cài đặt đúng.

### 3.4. Hạn chế của Grad-CAM — chính tác giả thừa nhận

Đây là mục quan trọng, vì nó biến một điểm yếu thành bằng chứng đã đọc tài liệu.

**Bản đồ nhiệt của nhóm hiện còn thô.** Nguyên nhân: tầng tích chập cuối của
EfficientNet-B0 chỉ có độ phân giải **7×7**, phóng lên 224×224 thì mỗi ô gốc phủ một
mảng 32×32 điểm ảnh.

**Đây không phải lỗi cài đặt.** Chính bài gốc **D1** mô tả phương pháp của họ là cho
*"coarse localization map"* — bản đồ định vị **thô**. Các tác giả nhận biết hạn chế
này và đề xuất cách khắc phục của riêng họ: **Guided Grad-CAM**, ghép Grad-CAM với
một kỹ thuật hình ảnh hoá độ phân giải cao để có được bản đồ vừa sắc nét vừa phân
biệt được lớp.

**Ba lối ra, xếp theo công sức:**

| Lối ra | Nội dung | Chi phí | Đánh giá |
|---|---|---|---|
| 1 | Thêm **Grad-CAM++** | Thấp — sửa công thức trọng số | **Nên làm.** Mạnh đúng ở ca nhiều vết rời rạc, tức đốm lá Septoria và đốm lá vi khuẩn của nhóm |
| 2 | Lấy đặc trưng ở **tầng nông hơn** | Thấp — đổi `target_layer` | Độ phân giải cao hơn nhưng **ngữ nghĩa lớp yếu đi**. Phải thử mới biết |
| 3 | **Guided Grad-CAM** theo đúng bài gốc | Trung bình | Đúng chuẩn học thuật nhưng thêm việc |

> ⚠️ **Thứ tự ưu tiên phải đúng:** heatmap sắc nét mà **rơi vào nền** thì vô nghĩa.
> Việc kiểm tra Grad-CAM có nhìn đúng vết bệnh không (#17) phải làm **trước**, rồi mới
> bàn chuyện làm nét hơn. Lý do là bài A2.

### 3.5. Từ bản đồ nhiệt tới vùng khoanh và câu tiếng Việt

Đây là **đóng góp riêng của đề tài** và là chỗ khác biệt với mọi công trình đã khảo
sát. Luồng xử lý:

```
ảnh vào
  └─ EfficientNet-B0 → nhãn bệnh + độ tin cậy + phân bố xác suất 10 lớp
       └─ Grad-CAM → bản đồ nhiệt (H × W), giá trị 0..1
            └─ ngưỡng 0,5 → vùng khoanh đơn giản trên ảnh
                 └─ tra shared/data/tomato_diseases.json
                      └─ câu tiếng Việt + khuyến nghị xử lý
```

**Vì sao không đưa thẳng bản đồ nhiệt cho nông dân xem:** bản đồ nhiệt là quy ước của
giới kỹ thuật — người chưa quen không biết đỏ nghĩa là gì, và dễ hiểu nhầm vùng đỏ là
"chỗ bị bệnh nặng nhất" trong khi thực ra nó là "chỗ mô hình chú ý nhiều nhất". Hai
điều đó **không giống nhau**.

Kết quả thực tế của luồng này (đo trong báo cáo huấn luyện, ảnh số 2):

> **Chẩn đoán:** Virus xoăn vàng lá — độ tin cậy 96,44%
> **Ba khả năng hàng đầu:** Virus xoăn vàng lá 96,44% · Virus khảm 1,08% · Đốm lá Septoria 0,65%
> **Khuyến nghị:** KHÔNG CÓ THUỐC CHỮA VIRUS — phải nhổ bỏ và tiêu huỷ cây bệnh ngay để cắt nguồn lây.

**Chỉ số top-3 accuracy = 100%** cho phép một thiết kế an toàn: khi mô hình không
chắc chắn, giao diện hiển thị **3 khả năng kèm độ tin cậy** để nông dân tự đối chiếu,
thay vì ép một đáp án duy nhất. Điều này đúng tinh thần XAI — **hỗ trợ quyết định chứ
không thay thế con người** — và cũng đúng với kết luận của D9 rằng nhu cầu giải thích
của người dùng không đồng nhất.

---

## Phần IV. Khảo sát tài liệu

### 4.1. Cách chọn lọc

Nhóm khảo sát **46 công trình**, tổ chức trong `model/research/00-danh-muc-bai-bao.md`
theo 8 nhóm chủ đề. Tiêu chí chọn bài để **đọc kỹ**:

1. **Cùng đối tượng** — bệnh lá cà chua, hoặc bộ PlantVillage.
2. **Có số liệu đối chiếu được** — nêu rõ kiến trúc, dữ liệu, chỉ số.
3. **Chạm vào một quyết định kỹ thuật cụ thể** của nhóm, không đọc vì "có vẻ liên quan".
4. **Ưu tiên bài chỉ ra vấn đề** hơn bài khoe kết quả — bài nói "cách này không hiệu
   quả" hữu ích hơn bài thứ n báo cáo 99%.

Theo tiêu chí đó, **7 bài** được đọc kỹ.

### 4.2. Bảy bài đã đọc — họ nói gì và nhóm học được gì

---

#### **A1** · Mohanty, Hughes & Salathé (2016)
*Using Deep Learning for Image-Based Plant Disease Detection* — Frontiers in Plant Science 7:1419
📖 **Đã đọc toàn văn**

**Họ làm gì:** huấn luyện AlexNet và GoogLeNet trên 54.306 ảnh PlantVillage, 38 lớp
thuộc 14 loài cây. Thử 5 tỉ lệ chia tập, 3 phiên bản ảnh (màu / xám / đã tách nền),
2 chế độ (học chuyển giao / huấn luyện từ đầu).

**Họ nói gì:**

| Điều họ nêu | Số liệu |
|---|---|
| GoogLeNet + học chuyển giao, chia 80-20 | F1 = **0,9934** |
| Huấn luyện từ đầu luôn kém hơn học chuyển giao | 0,9836 vs 0,9934 |
| Ảnh màu tốt hơn ảnh xám rõ rệt | F1 xám thấp nhất 0,8524 |
| Càng ít dữ liệu huấn luyện càng kém, nhưng suy giảm chậm | 20-80 vẫn đạt 0,9820 |
| **Trên ảnh chụp điều kiện khác** | **31,40% và 31,69%** (đoán mò 2,63%) |

**Kinh nghiệm rút ra:**

- **Học chuyển giao là bắt buộc, có số chứng minh.** Nhóm đã làm đúng, và giờ có
  nguồn trích dẫn cho quyết định đó.
- **Giữ ảnh màu.** Nhóm đang dùng bản color của PlantVillage — phù hợp.
- **Con số 31,40% là bằng chứng domain gap mạnh nhất có thể trích**, vì nó đến từ
  chính tác giả tạo ra benchmark, không phải từ người phê bình.
- **Bài học phương pháp:** họ báo cáo cả con số xấu của mình. Đây là chuẩn mực khoa
  học nhóm sẽ theo khi đo trên ảnh thực địa.

> ⚠️ **Trích cho công bằng:** 31,40% đo trên **38 lớp của 14 loài** — bài toán khó hơn
> hẳn 10 lớp một loài của nhóm. Không được đem con số này ra rồi kết luận mô hình
> nhóm cũng sẽ tụt như vậy.

---

#### **A2** · Noyan (2022)
*Uncovering bias in the PlantVillage dataset* — arXiv:2206.04374
📖 **Đã đọc toàn văn** · **Bài quan trọng nhất trong toàn bộ khảo sát**

**Họ làm gì:** kiểm tra xem bộ PlantVillage có thiên lệch hệ thống không, bằng cách
huấn luyện mô hình **chỉ dùng phần nền ảnh**.

**Họ nói gì:**

- Mô hình huấn luyện **chỉ bằng 8 điểm ảnh lấy từ nền** đạt **49,0%** độ chính xác,
  trong khi đoán mò chỉ được 2,63%.
- **Xoá nền đi cũng không loại bỏ được thiên lệch.**
- Kết luận: nhãn bệnh có tương quan với đặc điểm nền, tức mô hình có thể đạt điểm cao
  bằng cách khai thác tương quan giả thay vì học triệu chứng bệnh.

**Kinh nghiệm rút ra:**

- **Đây là lý do tồn tại của #17.** Kiểm tra Grad-CAM không còn là việc "làm cho đẹp
  báo cáo" mà là **cổng kiểm soát chất lượng**: nếu bản đồ nhiệt rơi vào nền ở nhiều
  lớp thì mô hình đang học tắt, và toàn bộ phần XAI mất giá trị.
- **Cho một cách kiểm chứng định lượng, không chỉ nhìn bằng mắt:** đo tỉ lệ khối
  lượng heatmap rơi vào vùng lá so với rơi ra nền. Ảnh PlantVillage nền xám trơn nên
  tách lá bằng ngưỡng màu là đủ. Đây là thí nghiệm nhóm có thể tự làm.
- **Kết quả nào cũng đáng viết:** nếu heatmap tập trung trên lá → có bằng chứng phản
  bác A2 cho trường hợp của nhóm. Nếu rơi vào nền → nhóm **tự phát hiện lỗi mô hình
  bằng chính công cụ XAI của mình**, đây là kết quả mạnh nhất mà một đồ án XAI có thể có.

---

#### **A3** · Jelali (2024)
*Deep learning networks-based tomato disease and pest detection: a first review of research studies using real field datasets* — Frontiers in Plant Science
📖 **Đã đọc toàn văn**

**Họ làm gì:** review chỉ đọc những công trình dùng **ảnh đồng ruộng thật**, không
dùng ảnh phòng thí nghiệm.

**Họ nói gì:**

| Điều họ nêu | Số liệu |
|---|---|
| Trung bình các công trình dùng PlantVillage | **90,18%** |
| Trung bình các công trình dùng dữ liệu đồng ruộng tự thu | **84,66%** |
| Trên ảnh đồng ruộng: InceptionV3 · DenseNet | 93,70% · 94,93% |
| Nhận định của tác giả | Nhiều nghiên cứu dùng PlantVillage đạt trên 90% nhưng *"không hữu dụng lắm trong thực tiễn nông nghiệp"* |

Tác giả liệt kê rõ các yếu tố gây khó ở ảnh đồng ruộng: nhiều lá trong một ảnh, có cả
bộ phận khác của cây, ánh sáng và bóng đổ thay đổi, nền đất đa dạng.

**Kinh nghiệm rút ra:**

- **Cho mức tụt điển hình khi làm nghiêm túc: khoảng 5–6 điểm phần trăm.** Đây là con
  số thực tế hơn 31,40% của A1 để đặt kỳ vọng.
- Ghép A1 + A2 + A3 thành một lập luận hoàn chỉnh: **A2 giải thích nguyên nhân**
  (thiên lệch nền), **A1 cho giới hạn dưới** (31,40%), **A3 cho mức thực tế** (~85%).
- **Củng cố việc phải có `data/field/`.** Không còn là ý kiến chủ quan của nhóm mà là
  chuẩn mực của lĩnh vực.

---

#### **D4** · Assaduzzaman et al. (2025)
*XSE-TomatoNet: An explainable AI based tomato leaf disease classification method using EfficientNetB0 with squeeze-and-excitation blocks and multi-scale feature fusion* — MethodsX
📖 **Đã đọc toàn văn** · **Công trình gần đề tài nhất tìm được**

**Họ làm gì:** EfficientNetB0 + khối Squeeze-and-Excitation + hợp nhất đặc trưng đa
tỉ lệ, phân loại 11 lớp bệnh lá cà chua, kèm 4 phương pháp XAI, triển khai web Flask.

**Họ nói gì:**

- 32.532 ảnh, chia 80/10/10, độ chính xác kiểm tra **99,11%**, precision/recall/F1
  đều 99%.
- Dùng đồng thời **LIME + SHAP + Grad-CAM + Grad-CAM++**.
- Nhận định về XAI: *"Grad-CAM++ là bản cải tiến của Grad-CAM, cho lời giải thích
  chính xác và khu trú hơn"*, và *"Grad-CAM++ tập trung vào gradient dương, tạo bản
  đồ nhiệt sắc nét hơn"*.
- Cả hai kỹ thuật đều lấy từ **tầng tích chập cuối cùng**.

**Kinh nghiệm rút ra:**

- **Xác nhận lựa chọn kiến trúc của nhóm là hợp lý** — một công trình quốc tế 2025
  chọn đúng EfficientNet-B0 cho đúng bài toán này.
- **Xác nhận hướng nâng cấp Grad-CAM++ là đúng** — họ đã dùng và ghi nhận sắc nét hơn.
- **Xác nhận việc lấy tầng chập cuối là chuẩn mực**, không phải lựa chọn tuỳ tiện của nhóm.
- **Chỉ ra khoảng trống để đề tài chen vào:** họ dừng ở bản đồ nhiệt kỹ thuật cho
  người nghiên cứu. Không có bước chuyển thành ngôn ngữ người dùng cuối.

**Điểm cần thận trọng khi so sánh — quan trọng:**

> Họ dùng **32.532 ảnh cho 11 lớp cà chua**, trong khi PlantVillage gốc chỉ có
> **18.160 ảnh cho 10 lớp** cà chua. Chênh lệch này gần như chắc chắn nghĩa là họ
> dùng bản đã tăng cường sẵn hoặc gộp thêm nguồn. **Bài báo không nói rõ việc tăng
> cường dữ liệu được thực hiện trước hay sau khi chia tập.** Nếu trước, các biến thể
> của cùng một ảnh gốc sẽ nằm ở cả tập huấn luyện lẫn tập kiểm tra, và con số 99,11%
> bị thổi phồng.

Đây là **bài học phương pháp quan trọng nhất** rút ra từ toàn bộ khảo sát: xem mục 5.

---

#### **E1** · (2025)
*Data-Centric Preprocessing Outperforms Loss Modifications for Hard-Class Plant Disease Classification Using MobileNetV3* — Elinvo
📖 **Đã đọc toàn văn**

**Họ làm gì:** so sánh các cách xử lý lệch lớp trên MobileNetV3-Small, tập trung vào
12 lớp khó (F1 hoặc recall dưới 0,96).

**Họ nói gì:**

| Cách xử lý | F1 lớp khó |
|---|---:|
| Cross-entropy thường | **0,9668** |
| Focal loss (tham số mặc định) | 0,9647 |
| Trọng số theo tần suất nghịch đảo | 0,9621 |

Cả hai kỹ thuật "chống lệch lớp" đều **kém hơn** cross-entropy thường. Tác giả kết
luận: hướng **data-centric** — chẩn đoán lỗi chi tiết, đánh giá chất lượng ảnh, tăng
cường có chủ đích theo lớp — hiệu quả hơn sửa hàm mất mát, đạt **+4,08 điểm phần
trăm** trong khi vẫn giữ 98,08% độ chính xác tổng.

**Kinh nghiệm rút ra:**

- **Nhóm quyết định KHÔNG thêm class weight hay focal loss vào `train.py`** — có căn
  cứ, không phải do lười.
- **Trùng khớp với kết quả nội bộ:** nhóm đã lo lớp *virus khảm* (263 ảnh huấn luyện,
  ít hơn lớp đông nhất 14,4 lần) sẽ có recall thấp. Thực tế nó đạt precision = recall
  = F1 = **1,0000** với cross-entropy + label smoothing 0,05, không dùng bất kỳ kỹ
  thuật cân bằng lớp nào.
- **Bài học khái quát: lệch lớp là *nguy cơ* chứ không phải *hậu quả tất yếu*.** Mức
  ảnh hưởng phụ thuộc lớp thiểu số có đặc trưng thị giác riêng biệt hay không. Virus
  khảm gây lá nhăn nhúm và khảm màu — khác hẳn 9 lớp còn lại, nên ít ảnh vẫn đủ học.
- **Đây là kết quả âm tính có đo đạc**, và nêu được nó mạnh hơn im lặng.

---

#### **D1** · Selvaraju et al. (2017)
*Grad-CAM: Visual Explanations from Deep Networks via Gradient-based Localization* — ICCV 2017 / IJCV 2020
📄 **Mới đọc phần tóm tắt — chưa đọc toàn văn**

**Họ nói gì (phần đã xác minh):**

- Dùng gradient của khái niệm mục tiêu chảy vào **tầng tích chập cuối cùng** để tạo
  bản đồ định vị.
- Áp dụng được cho **nhiều họ mô hình CNN mà không cần sửa kiến trúc** — đây là bước
  tiến so với CAM.
- Tác giả **tự mô tả** kết quả là *"coarse localization map"* — bản đồ thô.
- Cách khắc phục của chính họ: ghép với hình ảnh hoá chi tiết để tạo *"high-resolution
  class-discriminative visualization"* (Guided Grad-CAM).

**Kinh nghiệm rút ra:**

- **Vấn đề heatmap thô 7×7 của nhóm là hạn chế đã biết của phương pháp**, không phải
  lỗi cài đặt. Trích được câu tự nhận của tác giả khi bị hỏi.
- Có sẵn ba hướng khắc phục để trình bày (mục 3.4).

> ⚠️ **Còn thiếu:** chưa đọc mục hạn chế đầy đủ và phần đánh giá tin cậy của người
> dùng. **Cần đọc trước khi nộp báo cáo cuối** — đây là bài bắt buộc phải trích dẫn.

---

#### **D2** · Chattopadhay et al. (2018)
*Grad-CAM++: Improved Visual Explanations for Deep Convolutional Networks* — WACV 2018
📄 **Mới đọc phần tóm tắt — chưa lấy được công thức và bảng số**

**Họ nói gì (phần đã xác minh):**

- Dùng **tổ hợp có trọng số của các đạo hàm riêng dương** của feature map tầng chập
  cuối theo điểm số lớp.
- Cải thiện ở hai tình huống cụ thể: **nhiều thể hiện của cùng một lớp trong một ảnh**,
  và **đối tượng chỉ xuất hiện một phần**.
- Chứng minh hiệu quả trên phân loại, sinh chú thích ảnh, nhận dạng hành động 3D.

**Kinh nghiệm rút ra:**

- **Đúng ca của nhóm.** Đốm lá Septoria và đốm lá vi khuẩn biểu hiện bằng **hàng chục
  đốm nhỏ rời rạc** trên một lá — chính là tình huống Grad-CAM++ mạnh hơn. Đáng chú ý
  là cặp *Đốm lá vi khuẩn → Đốm mắt cua* cũng là cặp nhầm nhiều nhất của mô hình (4/11 ảnh sai).
- Là ứng viên số 1 để nâng cấp `src/xai/gradcam.py` trong #16.

> ⚠️ **Còn thiếu:** file PDF trên arXiv không giải mã tự động được, nên **chưa lấy
> được công thức hệ số và bảng số liệu so sánh**. Phải mở đọc bằng tay trước khi cài
> đặt, vì cài sai công thức thì heatmap sẽ sai mà không báo lỗi gì.

---

### 4.3. Bảng so sánh kết quả

**Bảng 7. Đối chiếu kết quả trên bài toán bệnh lá cà chua**

| Công trình | Kiến trúc | Dữ liệu | Lớp | Accuracy | Macro-F1 | Nêu rõ cách chia tập? |
|---|---|---|---:|---:|---:|---|
| **Nhóm 3 (07/09/2026)** | EfficientNet-B0 | PlantVillage cà chua, 18.160 ảnh | 10 | **99,60%** | **99,55%** | ✅ **70/15/15 theo lớp, kiểm chứng không rò rỉ, seed 42** |
| **D4** XSE-TomatoNet (2025) | EfficientNetB0 + SE | 32.532 ảnh | 11 | 99,11% | ~0,99 | ⚠️ 80/10/10 — **không nêu augment trước hay sau khi chia** |
| **B6** (2025) | DenseNet121 | PlantVillage | — | 99,61% | — | chưa xác minh |
| | ResNet50 | | | 99,48% | — | |
| | VGG16 | | | 99,08% | — | |
| **B4** (2025) | ViT-Base | PlantVillage | — | 99,17% | — | chưa xác minh |
| **B3** (2024) | Bayesian hybrid DL+ML | PlantVillage cà chua | 10 | 98,27% | — | chưa xác minh |
| **A1** Mohanty (2016) | GoogLeNet transfer | PlantVillage đầy đủ | 38 | — | 0,9934 | ✅ **thử 5 tỉ lệ từ 80-20 tới 20-80** |

#### Cách đọc bảng này cho đúng — phần quan trọng nhất

**Nhóm KHÔNG kết luận "mô hình của em tốt hơn XSE-TomatoNet".** Ba lý do:

1. **Khác số lớp.** Họ 11 lớp (có thêm *phấn trắng*), nhóm 10 lớp. Ít lớp hơn thì bài
   toán dễ hơn — so trực tiếp là khập khiễng.
2. **Khác quy mô và nguồn dữ liệu.** 32.532 ảnh so với 18.160 ảnh.
3. **Chênh lệch 0,49 điểm phần trăm nằm trong nhiễu thống kê** với tập kiểm tra 2.719
   ảnh — tương đương khoảng 13 ảnh. Đổi vài ảnh là đảo thứ hạng.

**Nhưng có một điều nói được, và nói mạnh:** trong toàn bộ các công trình đối chiếu,
chỉ có **A1 và nhóm mình nêu rõ và kiểm chứng cách chia tập**.

> **Câu đề nghị dùng khi bảo vệ:**
> *"Con số của em không cao hơn ai đáng kể, và em không cho rằng nó cao hơn. Nhưng
> quy trình đo của em minh bạch hơn phần lớn công trình em đối chiếu: em nêu rõ chia
> 70/15/15 theo từng lớp, cố định seed 42 để tái lập được, và đã kiểm chứng không có
> ảnh nào nằm ở hai tập khác nhau. Nhiều bài báo đạt con số cao hơn nhưng không nói rõ
> việc tăng cường dữ liệu được làm trước hay sau khi chia tập."*

Đây là thế đứng vững hơn nhiều so với việc khoe con số cao.

---

## Phần V. Kinh nghiệm rút ra và cách áp dụng

**Bảng 8. Từ tài liệu tới hành động cụ thể**

| # | Kinh nghiệm | Nguồn | Đã / sẽ áp dụng thế nào |
|---|---|---|---|
| 1 | Học chuyển giao bắt buộc, không huấn luyện từ đầu | A1 | **Đã áp dụng** — hai giai đoạn, đo được bước nhảy 7,5 điểm ở epoch 4 |
| 2 | Giữ ảnh màu, không chuyển sang ảnh xám | A1 | **Đã áp dụng** — dùng bản color của PlantVillage |
| 3 | **Nêu rõ và kiểm chứng cách chia tập** | A1, D4 (phản diện) | **Đã áp dụng** — 70/15/15 theo lớp, seed 42, đã kiểm chứng không rò rỉ. Chia **trước** khi tăng cường |
| 4 | Con số trên PlantVillage không phản ánh thực tế | A1, A2, A3 | **Đã ghi rõ** trong báo cáo huấn luyện mục 9.1. Sẽ báo cáo cả hai con số |
| 5 | Phải kiểm tra mô hình có học tắt không | A2 | **Sẽ làm ở #17** — cổng kiểm soát bắt buộc trước khi làm giao diện |
| 6 | Có cách kiểm chứng heatmap **định lượng**, không chỉ nhìn mắt | A2 | **Sẽ làm** — đo tỉ lệ khối lượng heatmap trong vùng lá so với nền |
| 7 | Không vội thêm class weight / focal loss | E1 | **Đã quyết định không thêm** — có bằng chứng ngoài (E1) và trong (mosaic F1 = 1,0000) |
| 8 | Lệch lớp là nguy cơ, không phải hậu quả tất yếu | E1 + kết quả nội bộ | **Đã ghi vào phân tích** — lý giải bằng đặc trưng thị giác riêng biệt của virus khảm |
| 9 | Grad-CAM thô là hạn chế đã biết của phương pháp | D1 | **Trích dẫn khi bị hỏi**; ba lối ra đã liệt kê ở mục 3.4 |
| 10 | Grad-CAM++ mạnh ở ca nhiều vết rời rạc | D2, D4 | **Sẽ nâng cấp ở #98** — sau khi #17 xong |
| 11 | Lấy tầng chập cuối là chuẩn mực, không tuỳ tiện | D1, D4 | **Đã áp dụng** — `model.features[-1]` |
| 12 | Nông dân cần diễn giải kết quả, không cần hiểu mô hình | D9, D10 | **Là quyết định thiết kế cốt lõi** — vùng khoanh + câu tiếng Việt thay bản đồ nhiệt |
| 13 | Nhu cầu giải thích không đồng nhất giữa người dùng | D9 | **Áp dụng qua top-3** — hiển thị 3 khả năng khi mô hình không chắc |
| 14 | Báo cáo cả con số xấu của mình | A1 (làm gương) | **Cam kết** — sẽ báo cáo cả kết quả trên ảnh thực địa dù thấp |

### Bài học phương pháp lớn nhất

Điều giá trị nhất rút ra từ khảo sát **không phải một kỹ thuật**, mà là một chuẩn mực
đọc kết quả:

> **Một con số accuracy chỉ có nghĩa khi biết nó được đo thế nào.**

Nhóm phát hiện điều này khi đối chiếu D4: một công trình quốc tế 2025, đăng trên tạp
chí có phản biện, báo cáo 99,11% — nhưng **không nói rõ việc tăng cường dữ liệu được
thực hiện trước hay sau khi chia tập**. Chi tiết tưởng nhỏ đó quyết định con số có
đáng tin hay không.

Từ đó nhóm rút ra hai nguyên tắc và đã áp dụng:

1. **Với bài báo:** khi đọc, luôn tìm mục chia tập trước khi tin con số. Không thấy
   thì ghi "không nêu" và cẩn thận khi trích.
2. **Với báo cáo của mình:** nêu rõ mọi chi tiết mà người khác cần để tái lập — tỉ lệ
   chia, cách chia, seed, thứ tự chia-và-tăng-cường.

---

## Phần VI. Việc tiếp theo

**Bảng 9. Kế hoạch, xếp theo mức ưu tiên**

| Mã việc | Nội dung | Nguồn thúc đẩy | Ưu tiên |
|---|---|---|---|
| **#17** | **Kiểm tra Grad-CAM có rơi đúng vết bệnh không** — 5 ảnh × 10 lớp | **A2** | **Cao nhất — cổng kiểm soát** |
| #49 / TN-2 | Đánh giá trên bộ **H1** — 731 ảnh đồng ruộng thật, 6/7 lớp trùng, tải Mendeley | A1, A3 | Cao — có số domain gap mà không phải chờ chụp ảnh |
| #98 | Nâng cấp **Grad-CAM++**, đối chiếu với `pytorch-grad-cam` | D2, D4 | Cao — làm sau #17. ⚠️ Bản đầu ghi số issue sai là #16 (việc đó là MD-07 sinh lưới ảnh minh hoạ); issue thật tạo ngày 15/09/2026 |
| #18 | Đo tốc độ suy luận trên **CPU** máy demo | Rủi ro số 2 | Cao |
| #19 | So EfficientNet-B0 với ResNet18 / ResNet50 / B3 | B1, B6 | Trung bình — 4 lượt × 25 phút, không cần sửa code |
| — | **Đọc toàn văn D1 và D2** | D1, D2 | Trung bình — bắt buộc trước báo cáo cuối |
| — | **Bổ sung bài gốc EfficientNet vào danh mục và đọc** | mục 1.2.1 | Trung bình — bắt buộc trích dẫn |

**Mốc cần lưu ý:** **15/09/2026** là cổng go/no-go cho phần mở rộng bệnh trên quả.
Với kết quả huấn luyện đã đạt và backend đã chạy thật, nhóm đang ở vị thế thuận lợi.

---

## Phụ lục A. Danh mục tài liệu và mức độ đã đọc

Danh mục đầy đủ **46 công trình** chia 8 nhóm nằm ở
`model/research/00-danh-muc-bai-bao.md`. Tóm tắt mức độ đã đọc:

**Bảng 10. Trạng thái khảo sát**

| Nhóm chủ đề | Số bài | Đã đọc kỹ | Ghi chú |
|---|---:|---|---|
| A · Nền tảng và tổng quan | 7 | **A1, A2, A3** | Đủ để viết chương tổng quan |
| B · So sánh kiến trúc | 10 | — | Cần cho #19 |
| C · Mô hình nhẹ / thiết bị biên | 7 | — | Chưa tới lúc |
| D · XAI | 11 | **D4** kỹ · **D1, D2** tóm tắt | Trọng tâm đề tài |
| E · Lệch lớp và tăng cường dữ liệu | 8 | **E1** | Đã đủ để ra quyết định |
| F · Open-set / OOD | 5 | — | Sau cổng 15/09 |
| G · Bệnh trên quả | 8 | — | Sau cổng 15/09 |
| H · Bộ dữ liệu đo domain gap | 4 | **H1** (xác minh nguồn) | H1 dùng được ngay |
| **Tổng** | **46** | **7 bài** | |

**Bảng 11. Ghi chú trung thực về mức độ xác minh**

| Mã | Mức đã đọc | Điều còn thiếu |
|---|---|---|
| A1 | ✅ Toàn văn | — |
| A2 | ✅ Toàn văn | — |
| A3 | ✅ Toàn văn | — |
| D4 | ✅ Toàn văn (hai lượt) | — |
| E1 | ✅ Toàn văn | — |
| D1 | ⚠️ Tóm tắt | Chưa đọc mục hạn chế đầy đủ. **Bắt buộc đọc trước báo cáo cuối** |
| D2 | ⚠️ Tóm tắt | **Chưa có công thức hệ số và bảng số** — PDF không giải mã tự động được, phải mở tay |
| B3, B4, B6 | ❌ Chưa mở | Số liệu trong Bảng 7 lấy từ kết quả tìm kiếm, **phải kiểm lại trước khi trích vào báo cáo cuối** |
| Tan & Le 2019 (EfficientNet) | ❌ Chưa có trong danh mục | Bắt buộc bổ sung — đã dùng kiến trúc của họ |
| Zhou et al. 2016 (CAM) | ❌ Chưa mở | Nên trích khi trình bày dòng dõi phương pháp |
| Ribeiro 2016 (LIME) · Lundberg 2017 (SHAP) | ❌ Chưa mở | Chỉ cần nhắc ở mức phương án đã cân nhắc |

> Bảng 11 để trong báo cáo có chủ đích. Nói rõ mình đã đọc tới đâu và còn thiếu gì
> đáng tin hơn là trình bày như thể đã đọc hết.

---

## Phụ lục B. Backbone — vì sao đóng băng rồi lại mở khoá

Phần này giải thích kỹ hơn mục 1.3, vì đây là chỗ hội đồng hay hỏi sâu.

### B.1. Backbone là gì

Một mô hình phân loại ảnh gồm **hai phần nối tiếp nhau**:

| Phần | Tên trong code | Nhiệm vụ | Ví von |
|---|---|---|---|
| **Backbone** (phần xương sống) | `model.features` | Biến ảnh thành một danh sách con số mô tả nội dung ảnh | Con mắt và trí nhớ thị giác |
| **Đầu phân loại** (head) | `model.classifier` | Nhận danh sách đó rồi quyết định là bệnh gì | Bác sĩ đọc mô tả rồi kết luận |

Backbone không biết gì về bệnh cà chua. Việc của nó là nhìn ảnh rồi tóm tắt lại đại ý:
*"có nhiều đốm nâu tròn, viền hơi vàng, nằm trên nền lá xanh, bề mặt sần"*. Với
EfficientNet-B0 bản tóm tắt đó là một vector **1.280 con số**.

Đầu phân loại là phần duy nhất biết tới 10 lớp bệnh. Khi dựng mô hình, nhóm **vứt bỏ
hoàn toàn** đầu phân loại gốc của ImageNet (1.000 lớp đồ vật đời thường) và thay bằng
một lớp tuyến tính mới: 1.280 vào, 10 ra.

#### Con số làm rõ tỉ lệ hai phần

| Thành phần | Số tham số | Tỉ lệ |
|---|---:|---:|
| Backbone (thừa hưởng từ ImageNet) | 4.007.548 | **99,68 %** |
| Đầu phân loại mới (1.280 × 10 + 10) | 12.810 | **0,32 %** |
| **Tổng** | **4.020.358** | 100 % |

**Đây là con số nên nhớ khi bảo vệ.** Nó cho thấy học chuyển giao thực chất là gì:
nhóm **thừa hưởng 99,68 % mô hình** từ ImageNet và chỉ tự dựng 0,32 %. Nếu huấn luyện
từ số không thì phải học cả 4 triệu tham số kia chỉ bằng 12.722 ảnh — điều gần như
chắc chắn thất bại.

> **Kiểm chứng chéo:** bản EfficientNet-B0 gốc trên ImageNet có 5.288.548 tham số
> (tài liệu torchvision ghi 5,3 M). Bỏ đầu 1.000 lớp đi mất 1.280 × 1.000 + 1.000 =
> 1.281.000 tham số, thêm đầu 10 lớp vào được 12.810 tham số. Kết quả:
> 5.288.548 − 1.281.000 + 12.810 = **4.020.358** — **khớp chính xác** con số in ra lúc
> huấn luyện. Phép tính này xác nhận mô hình được dựng đúng như thiết kế.

### B.2. Vì sao phải đóng băng backbone vài epoch đầu

**Đóng băng** = tạm khoá backbone lại, không cho các con số bên trong nó thay đổi; chỉ
huấn luyện riêng đầu phân loại.

Lý do nằm ở chỗ **đầu phân loại mới có trọng số khởi tạo ngẫu nhiên**. Ở epoch đầu
tiên nó chưa biết gì cả, đoán gần như bừa, nên sai rất nhiều. Sai nhiều thì tín hiệu
sửa sai (gradient) rất lớn.

Trong mạng nơ-ron, tín hiệu sửa sai **lan ngược từ cuối về đầu**. Nếu không đóng băng,
gradient khổng lồ từ đầu phân loại non nớt sẽ chảy thẳng vào backbone và **phá hỏng
kiến thức tốt** mà backbone tích luỹ được từ 1,2 triệu ảnh ImageNet. Hiện tượng này
trong tài liệu gọi là **catastrophic forgetting** — quên thảm khốc.

> **Ví von dùng được khi bảo vệ:** giống như để một người mới vào nghề đọc kết quả xét
> nghiệm. Vài ngày đầu chỉ cho anh ta đọc và tập kết luận, **chưa cho phép anh ta sửa
> lại cách nhìn của người có hai mươi năm kinh nghiệm**. Đợi anh ta quen việc rồi mới
> cho cả nhóm cùng điều chỉnh.

### B.3. Vì sao lại phải mở khoá, không giữ đóng băng luôn

Vì **ImageNet không có lá cà chua bệnh**. Backbone chỉ biết những đặc trưng chung của
ảnh đời thường: cạnh, góc, kết cấu bề mặt, đốm màu. Nó chưa bao giờ phải phân biệt
*đốm có quầng vàng* với *đốm có vòng đồng tâm* — hai dấu hiệu quyết định để tách đốm
lá vi khuẩn khỏi đốm mắt cua.

Giữ đóng băng vĩnh viễn thì mô hình bị chặn trần ở mức đặc trưng chung chung.

**Số liệu thực nghiệm chứng minh điều này rất rõ:**

| Thời điểm | Trạng thái backbone | Độ chính xác kiểm định |
|---|---|---:|
| Hết epoch 3 | Đóng băng | **87,42 %** |
| Epoch 4 | **Vừa mở khoá** | **94,89 %** |

Chỉ một epoch sau khi mở khoá, độ chính xác **nhảy 7,47 điểm phần trăm**. Đây là bằng
chứng trực tiếp rằng backbone cần được tinh chỉnh riêng cho bài toán cà chua, và cũng
là bằng chứng rằng chiến lược hai giai đoạn hoạt động đúng như thiết kế.

> Đây là chi tiết đáng nêu nhất trong phần huấn luyện: nhóm **không chỉ áp dụng một kỹ
> thuật theo sách, mà có số đo chứng minh kỹ thuật đó có tác dụng thật**.

### B.4. Vì sao mở khoá thì phải hạ learning rate xuống 1/10

Khi mở khoá, learning rate hạ từ 0,0003 xuống 0,00003.

Lý do: lúc này backbone đang mang **kiến thức tốt cần được giữ gìn**, chỉ cần chỉnh
nhẹ cho hợp bài toán mới. Nếu để learning rate lớn như giai đoạn đầu thì mỗi bước cập
nhật sẽ đẩy trọng số đi quá xa, và kiến thức ImageNet bị xoá dần — đúng cái mà việc
đóng băng ba epoch đầu đã cố công tránh.

Nói ngắn: **giai đoạn 1 là dạy người mới, giai đoạn 2 là chỉnh nhẹ cả nhóm.** Hai việc
khác nhau nên cần hai tốc độ khác nhau.

### B.5. Vì sao chọn 3 epoch mà không phải 1 hay 10

Đây là siêu tham số, nhóm chọn 3 theo thông lệ chứ **chưa dò tìm bằng thực nghiệm** —
cần nói thật nếu bị hỏi.

Lập luận định tính:

- **Quá ít (1 epoch):** đầu phân loại chưa kịp ổn định, mở khoá sớm thì gradient vẫn
  còn lớn, không tránh được vấn đề ở B.2.
- **Quá nhiều (10 epoch):** phí thời gian, vì sau khi đầu phân loại đã hội tụ thì tiếp
  tục đóng băng không còn cải thiện gì.

Số liệu thực tế ủng hộ lựa chọn 3: trong giai đoạn đóng băng, độ chính xác kiểm định
đi từ 82,24 % (epoch 1) lên 86,10 % (epoch 2) rồi 87,42 % (epoch 3) — mức tăng đã chậm
lại rõ rệt, tức đúng lúc nên chuyển giai đoạn.

### B.6. Nếu hội đồng hỏi sâu hơn

| Câu hỏi | Trả lời gọn |
|---|---|
| "Đóng băng là đóng băng cái gì?" | Khoá 4.007.548 tham số của backbone, chỉ cho 12.810 tham số của đầu phân loại được thay đổi |
| "Không đóng băng thì sao?" | Gradient lớn từ đầu phân loại ngẫu nhiên sẽ phá hỏng trọng số ImageNet. **Nhóm chưa chạy thử đối chứng** — đây là lập luận theo tài liệu, không phải số đo của nhóm |
| "Sao biết mở khoá có tác dụng?" | Có số: 87,42 % → 94,89 % chỉ sau một epoch |
| "Sao chọn đúng 3 epoch?" | Theo thông lệ, chưa dò tìm. Số liệu cho thấy giai đoạn 1 đã gần chạm trần ở epoch 3 |

---

## Phụ lục C. Vì sao không chọn ResNet, ViT hay EfficientNet-B3

### C.1. Số liệu gốc

Bảng dưới lấy **trực tiếp từ tài liệu chính thức của torchvision** — thư viện nhóm
đang dùng — chứ không phải từ trí nhớ hay bài báo thứ cấp. Đây là độ chính xác trên
ImageNet-1K, ứng với đầu phân loại 1.000 lớp.

**Bảng 12. Đối chiếu các kiến trúc torchvision hỗ trợ sẵn**

| Kiến trúc | Top-1 ImageNet | Tham số | Chênh so với B0 |
|---|---:|---:|---|
| **EfficientNet-B0** *(nhóm chọn)* | **77,692 %** | **5,3 M** | — |
| EfficientNet-B3 | 82,008 % | 12,2 M | **+4,3 điểm**, nặng gấp 2,3 lần |
| ResNet18 | 69,758 % | 11,7 M | **−7,9 điểm**, nặng gấp 2,2 lần |
| ResNet50 (trọng số V1) | 76,130 % | 25,6 M | −1,6 điểm, nặng gấp 4,8 lần |
| ResNet50 (trọng số V2 — bản `build.py` đang dùng) | 80,858 % | 25,6 M | +3,2 điểm, nặng gấp 4,8 lần |
| ViT-B/16 | 81,072 % | 86,6 M | +3,4 điểm, **nặng gấp 16 lần** |

### C.2. Đọc bảng này cho trung thực

**Không được nói "EfficientNet-B0 chính xác nhất".** Bảng 12 cho thấy điều ngược lại:
B3, ResNet50-V2 và ViT-B/16 đều **chính xác hơn** B0 trên ImageNet.

Lập luận đúng là về **hiệu quả trên mỗi tham số bỏ ra**:

**Bảng 13. Cái giá phải trả cho mỗi điểm ImageNet tăng thêm so với B0**

| Kiến trúc | Điểm tăng thêm | Tham số thêm | Giá mỗi điểm |
|---|---:|---:|---|
| EfficientNet-B3 | +4,3 | +6,9 M | **1,6 M tham số / điểm** |
| ResNet50-V2 | +3,2 | +20,3 M | 6,3 M tham số / điểm |
| ViT-B/16 | +3,4 | +81,3 M | **23,9 M tham số / điểm** |
| ResNet18 | **−7,9** | +6,4 M | **thuần lỗ** |

### C.3. Kết luận cho từng kiến trúc

**ResNet18 — bị loại rõ ràng nhất.** Nó vừa **nặng hơn B0 gấp 2,2 lần** vừa **kém hơn
7,9 điểm** trên ImageNet. Không có chiều nào nó thắng. Đây là trường hợp duy nhất
trong bảng có thể loại dứt khoát mà không cần thử.

> Nhóm vẫn giữ ResNet18 trong danh sách so sánh của #19, nhưng với vai trò **đối
> chứng** — để bảng so sánh có một kiến trúc kinh điển làm mốc, chứ không phải vì kỳ
> vọng nó thắng.

**ResNet50 — mạnh hơn nhưng quá đắt.** Được thêm 3,2 điểm ImageNet nhưng phải mang
theo 25,6 triệu tham số, gấp gần 5 lần B0. Với ràng buộc tốc độ suy luận lúc demo,
đánh đổi này không có lợi.

**ViT-B/16 — đắt nhất, và có bằng chứng độc lập rằng không đáng.** Giá 23,9 triệu tham
số cho mỗi điểm ImageNet, gấp 15 lần B3. Quan trọng hơn, bài **B4** đã đo trực tiếp
trên **đúng bài toán bệnh lá cà chua PlantVillage** và ViT-Base chỉ đạt **99,17 %** —
tức **không vượt** các CNN nhẹ. Đây là bằng chứng mạnh hơn hẳn suy luận từ ImageNet,
vì nó đo trên đúng loại dữ liệu của mình.

**EfficientNet-B3 — trường hợp khó nhất, và phải nói thật.** B3 có tỉ lệ đánh đổi tốt
nhất trong bảng: 1,6 triệu tham số cho mỗi điểm ImageNet. Nếu chỉ nhìn Bảng 13 thì B3
là lựa chọn hợp lý hơn B0.

Ba lý do nhóm vẫn chọn B0:

1. **Bài toán đã gần bão hoà.** Mô hình hiện đạt 99,60 %, dư địa chỉ còn 0,40 % —
   tương đương 11 ảnh. Thêm 4,3 điểm trên ImageNet gần như chắc chắn **không chuyển
   thành** 4,3 điểm ở đây, vì trần đã quá gần.
2. **Ràng buộc tốc độ.** Nặng gấp 2,3 lần đồng nghĩa suy luận chậm hơn đáng kể trên
   máy demo có thể không có GPU.
3. **B3 vốn được thiết kế cho ảnh vào lớn hơn 224×224.** Chạy nó ở 224 là chạy dưới độ
   phân giải thiết kế, không phát huy hết năng lực.

### C.4. Ba điều phải nói thật nếu bị hỏi

Đây là phần quan trọng nhất của phụ lục này.

**1. Nhóm chưa đo các kiến trúc này trên dữ liệu của mình.** Toàn bộ Bảng 12 và 13 là
số trên **ImageNet**, không phải trên bệnh lá cà chua. Lựa chọn B0 là quyết định
**trước thực nghiệm**, dựa trên đánh đổi đã biết. Việc đo thật là **#19**, chưa chạy.

> Trả lời đề nghị: *"Em chọn B0 dựa trên tỉ lệ giữa độ chính xác và chi phí tính toán
> trên ImageNet, cộng với ràng buộc tốc độ lúc demo. Em chưa đo ResNet và B3 trên dữ
> liệu của em — đó là việc #19. Code đã hỗ trợ sẵn bốn kiến trúc nên chỉ cần đổi một
> dòng cấu hình rồi chạy bốn lượt, mỗi lượt khoảng 25 phút."*

**2. Thứ hạng trên ImageNet chưa chắc giữ nguyên ở bài toán này.** ImageNet có 1.000
lớp đồ vật đời thường; đây là 10 lớp bệnh trên cùng một loài cây. Hai bài toán khác
hẳn nhau cả về độ khó lẫn loại đặc trưng cần thiết. Hoàn toàn có khả năng ResNet18
chạy ngang B0 ở đây dù kém 7,9 điểm trên ImageNet.

**3. Nếu #19 chạy B3 thì phải chạy cho công bằng.** File `configs/default.yaml` đặt
`image_size: 224` dùng chung cho mọi kiến trúc. Chạy B3 ở 224 rồi kết luận "B3 không
hơn B0" là **kết luận không công bằng**, vì B3 vốn thiết kế cho ảnh vào lớn hơn. Khi
làm #19 phải hoặc chạy B3 ở đúng độ phân giải của nó, hoặc **ghi rõ trong báo cáo**
rằng mọi kiến trúc đều chạy ở 224 và điều đó bất lợi cho B3.

### C.5. Câu trả lời gọn khi bị hỏi

> *"Em chọn EfficientNet-B0 không phải vì nó chính xác nhất — ResNet50 và ViT đều
> chính xác hơn trên ImageNet. Em chọn vì nó cho tỉ lệ tốt nhất giữa độ chính xác và
> chi phí: 5,3 triệu tham số so với 25,6 triệu của ResNet50 và 86,6 triệu của ViT.
> Riêng ResNet18 thì em loại vì nó vừa nặng gấp đôi vừa kém hơn B0 gần 8 điểm — không
> thắng ở chiều nào. Với ViT em còn có bằng chứng trực tiếp: một nghiên cứu 2025 đo
> ViT-Base trên đúng bộ dữ liệu này chỉ được 99,17 %, không vượt các CNN nhẹ. Em chưa
> đo các kiến trúc kia trên dữ liệu của em, đó là việc kế tiếp."*
