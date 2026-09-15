# Từ bài báo → thí nghiệm chạy được

Đọc bài báo mà không chạy lại được gì thì chương thực nghiệm vẫn rỗng. File này nối
danh mục ở `00-danh-muc-bai-bao.md` với những thí nghiệm **thật sự chạy nổi trên RTX
4060 Ti trong thời gian còn lại**.

> ⚠️ Đây **không phải bảng công việc**. 76 issue trên GitHub mới là nguồn duy nhất
> để biết còn phải làm gì. Chốt thí nghiệm nào thì **mở issue mới cho cái đó**.

---

## Ràng buộc đã biết

| | |
|---|---|
| Thời gian một lượt 25 epoch | **≈ 22–25 phút** (đo thật 20/08, ảnh JPEG, `num_workers: 8`) |
| VRAM dùng | 1,46 / 8 GiB — còn rất nhiều chỗ trống |
| Đổi kiến trúc | Chỉ sửa `model.arch` trong `configs/default.yaml`, không sửa code |

Nghĩa là **một buổi chiều chạy được 8–10 lượt**. Đây là lợi thế lớn: mình đủ sức
dựng một bảng so sánh thật, đo bằng chính máy mình, thay vì chép số của người khác.

---

## Bảng so sánh cần điền

Đây là bảng trung tâm của chương thực nghiệm. Cột "PlantVillage test" và "PlantDoc"
đo bằng cùng một checkpoint — chênh lệch giữa hai cột **chính là domain gap**.

> ⚠️ Cột cuối trước đây ghi "H1 đồng ruộng acc". **H1 đã bị loại ngày 15/09/2026** (nhãn
> không tra được) và thay bằng **H2 — PlantDoc**, xem TN-2 dưới. Hai cột PlantVillage
> phải **lọc còn đúng 8 lớp** mà PlantDoc có, nếu không là so 10 lớp với 8 lớp.

| # | Kiến trúc | Tham số | Thời gian/epoch | PlantVillage test acc | Macro-F1 | Recall `mosaic_virus` | PlantDoc acc (8 lớp) | Ghi chú |
|---|---|---|---|---|---|---|---|---|
| 1 | EfficientNet-B0 *(baseline hiện tại)* | 4,0 M | 71 s | **99,60 %** | **0,9955** | **1,0000** | **30,81 %** | #14, #15, **#49** |
| 2 | ResNet18 | | | | | | | |
| 3 | ResNet50 | | | | | | | |
| 4 | EfficientNet-B3 | | | | | | | |
| 5 | MobileNetV3-Small | | | | | | | cần thêm vào `build.py` |
| 6 | ViT-B/16 hoặc Swin-T | | | | | | | cần thêm vào `build.py` |

**Bốn dòng đầu chạy được ngay, không sửa một dòng code nào** — `build.py` đã hỗ trợ
sẵn `efficientnet_b0`, `efficientnet_b3`, `resnet18`, `resnet50`.

Cột **Macro-F1** và **Recall `mosaic_virus`** quan trọng hơn cột accuracy. Với dữ liệu
lệch 14,4 lần, accuracy tổng gần như vô nghĩa — một mô hình bỏ hẳn lớp `mosaic_virus`
vẫn có thể đạt accuracy rất cao. Bài **E1** nói thẳng chuyện này.

---

## Bốn thí nghiệm đáng làm, xếp theo tỉ lệ được/mất

### TN-1 · So bốn kiến trúc có sẵn — **làm ngay sau #14**

Chạy dòng 1–4 của bảng trên. Bốn lượt × 25 phút ≈ **2 giờ**, không viết thêm code.

Đổi lại: một bảng so sánh do chính mình đo, trên chính máy mình, cùng một cách chia
tập. Đây là thứ hội đồng tin hơn hẳn bảng chép từ bài báo — vì bài báo mỗi người chia
tập một kiểu, số của họ so với nhau còn không công bằng.

Liên quan: **B1**, **B6**, **B8**.

### TN-2 · Đo trên bộ H2 PlantDoc (744 ảnh, 8 lớp) — **giá trị cao nhất**

> ⚠️ **Đã viết lại 15/09/2026.** Bản cũ dùng bộ **H1** và ước lượng *"mất nửa buổi"*. H1
> đã bị **loại hẳn**: export Roboflow/YOLO không kèm `data.yaml` nên không biết class ID
> nào là bệnh nào, và 230/689 ảnh có nhãn đa lớp. Nửa buổi đó đã tiêu vào việc phát hiện
> điều này. Căn cứ đầy đủ ở `docx/Plan_model.md` mục 5.2; việc đang làm là issue **#49**.

Tải phần cà chua của **PlantDoc** (GitHub `pratikkayal/PlantDoc-Dataset`), ánh xạ tên thư
mục sang khoá bệnh trong `shared/data/tomato_diseases.json` theo bảng ở `docx/Plan_model.md`
mục 5.2, sinh manifest rồi chạy `evaluate.py`.

**Ba chỗ code phải sửa trước, nếu không thì hai chỗ đầu cho ra số sai mà không báo lỗi:**

1. `src/data/prepare.py` — `scan_images()` ánh xạ tên thư mục qua `dir_to_key()`, chỉ nhận
   `Tomato___*` của PlantVillage. Tên thư mục PlantDoc rơi hết vào `unknown_dirs` →
   **manifest rỗng**, im lặng.
2. `src/evaluation/evaluate.py` — `classification_report()` thiếu `labels=` → sklearn tự suy
   nhãn từ dữ liệu (8 lớp) rồi so với `target_names` (10 lớp) → `ValueError`. Đây là chỗ
   **duy nhất báo lỗi**, nên cũng ít nguy hiểm nhất.
3. Phải truyền `--out-dir` riêng. Mặc định ghi vào `outputs/` sẽ **ghi đè
   `report-test.json` và `confusion-matrix-test.png` của PlantVillage đang nằm trong Git** —
   mất số liệu gốc của #15.

**Đo hai lần, và phải hiểu vì sao hai lần:**

| Phép đo | Dữ liệu | Dùng để làm gì |
|---|---|---|
| Chính | **toàn bộ 744 ảnh** | Con số domain gap của đề tài. Hợp lệ vì checkpoint chưa từng thấy ảnh PlantDoc nào, nên **đúng vĩnh viễn** kể cả sau khi #50 fine-tune |
| Phụ | riêng 69 ảnh `test` | Mốc "trước" cho phép so trước/sau ở #50, trên đúng những ảnh sẽ làm "sau" |
| Đối chứng | test PlantVillage **lọc còn 8 lớp** | So 10 lớp với 8 lớp là so lệch |

Bài **A3** cho con số đối chiếu: các công bố khác tụt từ 90,18% xuống 84,66%.

**Bốn hạn chế phải nói rõ trong báo cáo, đừng giấu:**

- PlantDoc có **8 trong 10 lớp** của nhóm. **Thiếu `target_spot`** hoàn toàn; `spider_mites`
  chỉ có 2 ảnh nên loại khỏi phép đo. Macro-F1 phải tính trên 8 lớp có mặt — để nguyên 10
  lớp thì hai lớp vắng đóng góp F1 = 0 và kéo macro-F1 xuống ~20 % một cách máy móc, con số
  đó không nói gì về mô hình.
- PlantDoc là ảnh **thu từ Internet**, không phải ảnh tác giả tự chụp ngoài đồng. Vẫn là
  phép thử domain shift hợp lệ, nhưng **không được gọi là "ảnh đồng ruộng"**.
- Phần `test` chỉ **69 ảnh** (6–11 ảnh/lớp) → sai số lớn, phải kèm khoảng tin cậy.
- Bản chia `train`/`test` của chính PlantDoc **rò rỉ 3 ảnh trùng byte tuyệt đối**, và 1
  trong 3 ảnh đó **mang hai nhãn khác nhau** nên bị loại hẳn. Việc lọc đã tự động hoá trong
  `src/data/prepare_plantdoc.py`.

> ✅ **TN-2 ĐÃ CHẠY XONG ngày 15/09/2026 — kết quả: 99,60 % → 30,81 % (tụt 68,79 điểm).**
> Báo cáo đầy đủ ở `docx/bao-cao-domain-gap.md`. Con số này **gần trùng khớp bài
> A1** (99,35 % → 31,40 %), lệch 0,6 điểm. Ba phát hiện kèm theo: mô hình dồn 85 % dự đoán
> vào 3 lớp; ngưỡng tin cậy không vá được; mức tập trung Grad-CAM tụt 1,58× → 1,02×.

### TN-3 · Grad-CAM có khoanh trúng vết bệnh không

Đây là thí nghiệm **đúng trọng tâm đề tài** và chưa ai trong nhóm làm.

Bài **A2** chứng minh mô hình có thể đoán đúng nhờ cái nền. Cách kiểm tra: lấy các ảnh
đoán đúng, xem tỉ lệ khối lượng heatmap **rơi vào vùng lá** so với **rơi ra nền**. Tách
lá khỏi nền bằng ngưỡng màu đơn giản là đủ, ảnh PlantVillage nền xám trơn nên dễ.

Nếu heatmap sáng ở nền đáng kể → mô hình đang gian lận, và mình **phát hiện được điều
đó bằng chính công cụ XAI của mình**. Đây là loại kết quả mạnh nhất mà một đồ án XAI
có thể có: XAI không chỉ để trình bày cho đẹp, mà để bắt lỗi mô hình.

Nếu heatmap tập trung trên lá → mình có bằng chứng phản bác thẳng A2 cho trường hợp
của mình. Kết quả nào cũng đáng viết.

Liên quan: **A2**, **D1**, **D2**, **D11**.

### TN-4 · Thử cách xử lý lệch lớp — **đọc E1 trước**

Ba cách, mỗi cách một lượt 25 phút:

1. Nguyên trạng (baseline)
2. `WeightedRandomSampler`
3. Focal loss

E1 báo rằng cả hai cách sau **không hơn** cross-entropy thường trên bài toán tương tự.
Nếu mình đo ra cũng vậy, đó là một kết quả âm tính đáng viết — và tiết kiệm được công
đi làm phức tạp `train.py` một cách vô ích.

Liên quan: **E1**, **E2**, issue **#15**.

---

## Ba thứ KHÔNG nên làm

| Việc | Vì sao không |
|---|---|
| Đổi sang YOLO / phát hiện có khung bao | Đổi hẳn bài toán và phải gán nhãn lại toàn bộ khung bao. Xem G5–G8 để biết khác biệt, đừng làm theo |
| Sinh ảnh bằng GAN (E4–E8) | Tốn thời gian huấn luyện thêm một mô hình sinh, lại mở ra câu hỏi phản biện "ảnh giả có lọt vào tập test không". Ảnh thật ở Đà Lạt đáng giá hơn nhiều |
| Làm OSR đầy đủ trước 15/09 | Ngưỡng độ tin cậy giải quyết được 80% nhu cầu với 2% công sức. Đọc F1 rồi tính sau |

---

## Nhớ ghi lại gì mỗi lượt chạy

Để chương thực nghiệm viết được, mỗi lượt phải lưu:

- `configs/` đã dùng (hoặc ghi rõ khác mặc định chỗ nào)
- `outputs/logs/history-*.json`
- `outputs/report-test.json`
- Ma trận nhầm lẫn
- Thời gian thật một epoch

Số liệu chia tập và smoke test đã có sẵn trong **PR #78** — trích từ đó, đừng đo lại
bằng trí nhớ.
