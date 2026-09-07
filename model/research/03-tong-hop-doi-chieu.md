# Tổng hợp đối chiếu — kết quả của nhóm so với công bố khoa học

Lập ngày **07/09/2026**, ngay sau khi có kết quả huấn luyện đầy đủ (PR #86).
Đối chiếu con số **99,60%** của nhóm với tài liệu đã đọc.

**Sáu bài đã đọc toàn văn:** A1, A2, A3, D4, E1 · **đọc phần tóm tắt:** D1, D2.

---

## 1. Nhóm đứng ở đâu so với các công bố

**Bảng 1. Đối chiếu kết quả trên bài toán bệnh lá cà chua**

| Công trình | Kiến trúc | Dữ liệu | Số lớp | Accuracy | Macro-F1 | Có nói rõ cách chia tập? |
|---|---|---|---:|---:|---:|---|
| **Nhóm 3 (07/09/2026)** | EfficientNet-B0 | PlantVillage cà chua, 18.160 ảnh | 10 | **99,60%** | **99,55%** | **Có — 70/15/15 theo lớp, đã kiểm chứng không rò rỉ, seed 42** |
| **D4** XSE-TomatoNet (MethodsX 2025) | EfficientNetB0 + SE + multi-scale fusion | 32.532 ảnh (Kaggle) | 11 | 99,11% | ~0,99 | 80/10/10 — **không nói rõ augment trước hay sau khi chia** |
| **B6** (Discov. Sustain. 2025) | DenseNet121 | PlantVillage | — | 99,61% | — | chưa xác minh |
| | ResNet50 | | | 99,48% | — | |
| | VGG16 | | | 99,08% | — | |
| **B4** (Eur. J. Agronomy 2025) | ViT-Base | PlantVillage | — | 99,17% | — | chưa xác minh |
| **B3** (Sci. Rep. 2024) | Bayesian hybrid DL+ML | PlantVillage cà chua | 10 | 98,27% | — | chưa xác minh |
| **A1** Mohanty (2016) | GoogLeNet transfer | PlantVillage đầy đủ, 54.306 ảnh | 38 | — | 0,9934 (F1) | **Có — thử 5 tỉ lệ chia từ 80-20 tới 20-80** |

### Đọc bảng này thế nào cho đúng

**Không được nói "mô hình của em tốt hơn XSE-TomatoNet".** Ba lý do:

1. **Khác số lớp** — họ 11 lớp (có thêm *phấn trắng*), mình 10 lớp. Ít lớp hơn thì bài toán dễ hơn.
2. **Khác quy mô dữ liệu** — họ 32.532 ảnh cho 11 lớp cà chua, trong khi PlantVillage gốc chỉ có **18.160 ảnh cho 10 lớp** cà chua. Chênh lệch này gần như chắc chắn nghĩa là họ dùng **bản đã tăng cường sẵn** (New Plant Disease Dataset) hoặc gộp thêm nguồn khác.
3. **Chênh lệch 0,49 điểm phần trăm là trong khoảng nhiễu thống kê** với tập test 2.719 ảnh. Đổi vài ảnh là đảo thứ hạng.

**Nhưng có một điều nói được, và nói mạnh:** trong toàn bộ các công trình đối chiếu, chỉ có **A1 và nhóm mình nói rõ cách chia tập**. D4 dùng 32.532 ảnh mà không nêu augment trước hay sau khi chia — nếu augment trước thì các biến thể của cùng một ảnh gốc nằm ở cả train lẫn test, và con số 99,11% bị thổi phồng.

> **Câu chốt khi bảo vệ:** "Con số của em không cao hơn ai đáng kể, nhưng **quy trình đo của em minh bạch hơn phần lớn các công bố em đối chiếu** — em nêu rõ 70/15/15 chia theo lớp, cố định seed 42, và đã kiểm chứng không có ảnh nào nằm ở hai tập."

Đây là thế đứng vững hơn nhiều so với việc khoe con số.

---

## 2. Domain gap — ba nguồn độc lập, cùng một kết luận

Đây là phần **quan trọng nhất** để báo cáo tối nay.

**Bảng 2. Bằng chứng khoảng cách miền từ tài liệu**

| Nguồn | Đo cái gì | Kết quả | Ý nghĩa |
|---|---|---|---|
| **A1** Mohanty 2016 — *chính tác giả PlantVillage* | Cùng mô hình, đem ra ảnh chụp điều kiện khác | **99,35% → 31,40% và 31,69%** (38 lớp, đoán mò 2,63%) | Bằng chứng mạnh nhất, vì đến từ chính bài tạo ra benchmark |
| **A3** Jelali 2024 — review chỉ đọc bài dùng ảnh đồng ruộng | Trung bình các công bố | PlantVillage **90,18%** · đồng ruộng **84,66%** | Cho biết mức tụt điển hình khi làm nghiêm túc |
| **A2** Noyan 2022 | Huấn luyện **chỉ bằng 8 pixel nền** | **49,0%** (đoán mò 2,63%). Xoá nền **không** hết thiên lệch | Chứng minh nhãn rò rỉ vào cái nền — mô hình có thể đúng vì lý do sai |

### Ba con số này nói gì với nhau

Chúng **không mâu thuẫn mà bổ sung cho nhau**, và ghép lại thành một lập luận hoàn chỉnh:

- **A2 giải thích nguyên nhân**: PlantVillage có thiên lệch nền, mô hình học được nhãn từ chỗ không phải vết bệnh.
- **A1 cho giới hạn dưới**: tệ nhất thì tụt xuống ~31%.
- **A3 cho giới hạn trên thực tế**: nếu thu dữ liệu đồng ruộng đàng hoàng thì giữ được ~85%.

**Lưu ý khi trích A1 cho công bằng:** con số 31,40% đo trên **38 lớp của 14 loài cây** — bài toán khó hơn hẳn 10 lớp một loài của nhóm. Không được đem 31,40% ra doạ rồi bảo mô hình mình cũng sẽ vậy. Nói đúng là: *"mức tụt có thể rất lớn, khoảng dao động trong tài liệu là từ tụt 5 điểm (A3) tới tụt hai phần ba (A1), và nhóm chưa đo được của mình nên chưa dám nói."*

### Hệ quả: việc phải làm

Nhóm **chưa có số domain gap của chính mình**. Trong khi chờ chụp ảnh ở Đà Lạt, dùng bộ **H1** — 731 ảnh đồng ruộng thật (Data in Brief 2025), 6/7 lớp trùng với 10 lớp của mình, tải Mendeley về là chạy `evaluate.py --manifest` được ngay. Nửa buổi có số.

---

## 3. Lệch lớp — kết quả của nhóm trùng khớp tài liệu

Nhóm đã cảnh báo trước rằng `mosaic_virus` (263 ảnh train, ít hơn lớp đông nhất 14,4 lần) sẽ có recall thấp. **Thực tế nó đạt P = R = F1 = 1,0000.**

Bài **E1** đo trên bài toán tương tự và ra kết luận cùng hướng:

| Cách xử lý lệch lớp | F1 lớp khó |
|---|---:|
| Cross-entropy thường | **0,9668** |
| Focal loss (tham số mặc định) | 0,9647 |
| Trọng số theo tần suất nghịch đảo | 0,9621 |

Cả hai kỹ thuật "chống lệch lớp" đều **kém hơn** cross-entropy thường. Tác giả kết luận: cải thiện **chất lượng dữ liệu** hiệu quả hơn sửa hàm mất mát (+4,08 điểm phần trăm bằng hướng data-centric).

**Kết luận cho nhóm:**

- **Không thêm class weight hay focal loss vào `train.py`.** Có bằng chứng bên ngoài (E1) và bằng chứng nội bộ (mosaic_virus đạt 1,0000 với cross-entropy + label smoothing 0,05).
- Ghi đây là **kết quả âm tính có đo đạc** vào báo cáo. Nêu được "em đã cân nhắc, có căn cứ để không làm" mạnh hơn hẳn im lặng.
- Lý giải vì sao lớp ít ảnh vẫn tốt: triệu chứng virus khảm khác biệt rõ về thị giác. **Lệch lớp là nguy cơ, không phải hậu quả tất yếu** — mức ảnh hưởng phụ thuộc lớp thiểu số có đặc trưng riêng hay không.

---

## 4. XAI — hướng xử lý cho #16 và #17

Báo cáo #14 nêu bản đồ nhiệt còn thô vì tầng chập cuối của EfficientNet-B0 chỉ có độ phân giải **7×7**. Tài liệu xác nhận đây là hạn chế **đã biết**, không phải lỗi cài đặt:

| Bài | Nói gì | Dùng được gì |
|---|---|---|
| **D1** Grad-CAM (gốc) | Tác giả **tự nhận** phương pháp cho "coarse localization map". Lấy tầng chập cuối vì đó là chỗ giữ được thông tin không gian mà vẫn mang ngữ nghĩa lớp. Cách khắc phục của chính họ: **Guided Grad-CAM** — ghép với hình ảnh hoá độ phân giải cao | Trích thẳng khi bị hỏi "sao heatmap thô vậy" — hạn chế của phương pháp, không phải của nhóm |
| **D2** Grad-CAM++ | Dùng tổ hợp có trọng số của các **đạo hàm riêng dương**. Tốt hơn khi ảnh có **nhiều thể hiện rời rạc của cùng một lớp** và khi đối tượng chỉ xuất hiện một phần | Đúng ca **đốm lá Septoria** và **đốm lá vi khuẩn** — hàng chục đốm nhỏ rải rác. Ứng viên số 1 để nâng cấp `src/xai/gradcam.py` |
| **D4** XSE-TomatoNet | Cũng lấy tầng chập cuối, cũng công nhận Grad-CAM++ cho heatmap **sắc nét hơn**. Họ dùng cả LIME + SHAP + Grad-CAM + Grad-CAM++ | Xác nhận hướng đi đúng; đồng thời cho thấy dùng 4 phương pháp XAI là chuyện làm được |

**Ba lối ra cho vấn đề 7×7, xếp theo công sức:**

1. **Thêm Grad-CAM++** — rẻ nhất, có thư viện `pytorch-grad-cam` (D11) đối chiếu. Làm trong #16.
2. **Lấy đặc trưng ở tầng nông hơn** — độ phân giải cao hơn nhưng ngữ nghĩa lớp yếu hơn. Đúng như báo cáo #14 đã dự đoán.
3. **Guided Grad-CAM** — theo đúng bài gốc D1, nhưng thêm việc.

> ⚠️ Nhắc lại cổng kiểm soát: heatmap sắc nét mà **rơi vào nền** thì vô nghĩa. #17 (kiểm tra 5 ảnh/lớp × 10 lớp) phải làm **trước**, rồi mới bàn chuyện làm nét hơn. A2 là lý do.

---

## 5. Đề tài khác gì người ta — trả lời bằng D4 và D9

**D4 XSE-TomatoNet là bài gần đề tài nhất từng tìm được:** cùng EfficientNet-B0, cùng cà chua, cùng Grad-CAM/Grad-CAM++, 99,11%. Phải chủ động nêu ra chứ đừng chờ hội đồng tìm thấy.

**Bảng 3. Đối chiếu với công trình gần nhất**

| | D4 XSE-TomatoNet (2025) | Đề tài nhóm 3 |
|---|---|---|
| Kiến trúc | EfficientNetB0 + SE + multi-scale fusion | EfficientNet-B0 |
| XAI | LIME + SHAP + Grad-CAM + Grad-CAM++ | Grad-CAM |
| **Đầu ra XAI cho người dùng** | **Bản đồ nhiệt kỹ thuật** | **Vùng khoanh + một câu tiếng Việt thường ngày** |
| Người dùng nhắm tới | Nhà nghiên cứu, kỹ sư | **Nông dân** |
| Triển khai | Web Flask | Ứng dụng di động + backend + web quản trị |
| Đo trên ảnh đồng ruộng | Không thấy nêu | **Có kế hoạch — H1 + ảnh tự chụp Đà Lạt** |
| Khuyến nghị xử lý | Không | **Có, theo từng bệnh, bằng tiếng Việt** |

Khoảng trống này **không phải nhóm tự nghĩ ra**. Bài **D9** khảo sát **40 nông dân thật** và kết luận: họ cần *diễn giải kết quả*, không cần biết mô hình hoạt động thế nào. Tức việc đưa bản đồ nhiệt kỹ thuật cho nông dân xem là **sai đối tượng**, và đó chính là chỗ đề tài chen vào.

> **Câu định vị:** "Phân loại bệnh cà chua đã bão hoà — ai làm cũng ra 99%. Chỗ chưa ai làm là **biến lời giải thích của mô hình thành thứ nông dân dùng được**. D9 cho thấy nhu cầu đó có thật và chưa được đáp ứng."

---

## 6. Chốt lại: bốn câu nói được ngay tối nay

1. **"Mô hình đạt 99,60%, macro-F1 99,55%, sai 11/2.719 ảnh — và không có ca sai nào vô lý về bệnh học."**
   Toàn bộ nhầm lẫn rơi vào cặp bệnh giống nhau về triệu chứng.

2. **"Con số đó chưa chứng minh hệ thống dùng được ngoài đồng, và nhóm có bằng chứng cụ thể cho điều đó."**
   A1: chính tác giả PlantVillage tụt còn 31,40%. A3: trung bình các công bố tụt từ 90,18% xuống 84,66%. A2: 8 pixel nền cũng đoán được 49%.

3. **"Cảnh báo lệch lớp đã không thành hiện thực, và nhóm không sửa hàm mất mát — có căn cứ."**
   `mosaic_virus` đạt F1 = 1,0000. E1 đo được rằng class weighting và focal loss đều **kém hơn** cross-entropy thường trên bài toán tương tự.

4. **"Việc tiếp theo là kiểm tra Grad-CAM có nhìn đúng vết bệnh không — đây là cổng kiểm soát của cả đề tài."**
   Nếu heatmap rơi vào nền thì đúng như A2 mô tả, và toàn bộ phần XAI mất giá trị.

---

## 7. Việc đọc tiếp, xếp theo giá trị

| Ưu tiên | Mã | Vì sao bây giờ mới cần |
|---|---|---|
| 1 | **D2** đọc kỹ công thức | Chuẩn bị nâng cấp `gradcam.py` trong #16. Bản PDF arXiv không tự đọc được, phải mở tay |
| 2 | **B1** benchmark đa bộ dữ liệu | Chuẩn bị #19 (so EfficientNet-B0 với ResNet18), lấy cách trình bày bảng |
| 3 | **H1** tải bộ 731 ảnh đồng ruộng | Có số domain gap của chính mình mà không phải chờ đi chụp |
| 4 | **A2** đọc lại phần biện pháp giảm thiểu | Sau khi #17 xong, đối chiếu heatmap của mình với mô tả thiên lệch của họ |

Nhóm C (mô hình nhẹ), E4–E8 (GAN), F (open-set), G (bệnh quả) **chưa cần đọc** — chưa tới lúc.

---

## Nguồn đã kiểm chứng tới đâu

| Mã | Mức đã đọc | Ghi chú |
|---|---|---|
| A1 | ✅ toàn văn | Lấy được bảng 5 tỉ lệ chia tập và con số 31,40% |
| A2 | ✅ toàn văn | 8 pixel nền → 49,0% |
| A3 | ✅ toàn văn | 90,18% vs 84,66% |
| D4 | ✅ toàn văn, hai lượt | Có bảng chỉ số từng lớp; **không nêu rõ augment trước hay sau khi chia** |
| E1 | ✅ toàn văn | Ba con số F1 đối chiếu |
| D1 | ⚠️ mới phần tóm tắt | Xác nhận "coarse localization map" và Guided Grad-CAM. **Chưa đọc phần hạn chế đầy đủ** |
| D2 | ⚠️ mới phần tóm tắt | Xác nhận dùng đạo hàm riêng dương và ưu thế khi có nhiều thể hiện rời rạc. **Chưa lấy được công thức và bảng số — PDF không giải mã được, phải mở tay** |
