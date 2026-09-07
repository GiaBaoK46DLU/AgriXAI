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

Đây là bảng trung tâm của chương thực nghiệm. Cột "PlantVillage test" và "H1 đồng
ruộng" đo bằng cùng một checkpoint — chênh lệch giữa hai cột **chính là domain gap**.

| # | Kiến trúc | Tham số | Thời gian/epoch | PlantVillage test acc | Macro-F1 | Recall `mosaic_virus` | H1 đồng ruộng acc | Ghi chú |
|---|---|---|---|---|---|---|---|---|
| 1 | EfficientNet-B0 *(baseline hiện tại)* | | | | | | | #14 |
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

### TN-2 · Đo trên bộ H1 (731 ảnh đồng ruộng Bangladesh) — **giá trị cao nhất**

Tải bộ **H1** từ Mendeley, ánh xạ 6 lớp trùng sang khoá bệnh trong
`shared/data/tomato_diseases.json`, sinh manifest rồi chạy:

```bash
python -m src.data.prepare --raw-dir data/field/bangladesh --out-dir data/processed/bangladesh --test-ratio 1.0 --val-ratio 0.0
python -m src.evaluation.evaluate --checkpoint checkpoints/best.pt --manifest data/processed/bangladesh/split.csv
```

Mất nửa buổi. Đổi lại là **con số domain gap có nguồn trích dẫn được**, có ngay trong
tháng 8 thay vì phải chờ đi chụp ảnh tháng 9. Bài **A3** cho con số đối chiếu: các
công bố khác tụt từ 90,18% xuống 84,66%.

Lưu ý: H1 có 7 lớp, mình có 10. Chỉ đánh giá trên **6 lớp giao nhau**, và phải nói rõ
điều đó trong báo cáo — đừng giấu.

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
