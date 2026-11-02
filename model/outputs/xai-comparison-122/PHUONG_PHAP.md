# Phép so sánh Grad-CAM, LIME và Kernel SHAP

Issue: https://github.com/GiaBaoK46DLU/AgriXAI/issues/122

## Câu hỏi và phạm vi

Phương pháp nào phù hợp với yêu cầu tạo giải thích theo ảnh của AgriXAI, xét cả
thời gian, chi phí và chất lượng giải thích? Giả thuyết trước khi chạy là
Grad-CAM nhanh hơn hai phương pháp lấy mẫu; không giả định Grad-CAM thắng mọi
chỉ số chất lượng. Không đổi checkpoint hoặc mẫu sau khi thấy kết quả.

Đây là ba **phương pháp giải thích hậu nghiệm**, không phải ba mô hình phân
loại được huấn luyện lại. Accuracy của bộ phân loại không thay đổi theo XAI.
Kết quả Kernel SHAP không đại diện mọi biến thể thuộc họ SHAP.

## Thiết kế cố định trước khi đo

- Checkpoint `checkpoints/leaf_disease_detection_model.pt`, giữ nguyên danh mục.
- Toàn bộ 56 ảnh của hai manifest `audit-gradcam-17/mau-pv.csv` (30 ảnh) và
  `mau-pd.csv` (26 ảnh), gồm cả dự đoán đúng và sai. Đây là tập chẩn đoán nhỏ
  đã chọn từ tháng 9, không phải mẫu ngẫu nhiên đại diện toàn bộ dữ liệu.
- Input RGB 224 × 224, resize trực tiếp như pipeline sản phẩm; chuẩn hóa ImageNet.
- Cùng lớp mục tiêu: lớp mô hình dự đoán trên ảnh gốc, không thay lớp để làm đẹp.
- Grad-CAM: dùng nguyên cài đặt sản phẩm, lớp tích chập cuối, gradient của logit.
- LIME Image và Kernel SHAP: cùng superpixel SLIC, yêu cầu 50 vùng, compactness
  10, sigma 1; số vùng thực tế được lưu từng ảnh. Cùng hàm xác suất của mạng.
- Cùng cách che vùng: giá trị RGB trung bình toàn ảnh, làm tròn xuống uint8.
- LIME: 1.000 ảnh nhiễu, cosine distance, kernel mặc định 0,25, Ridge mặc định,
  không chọn bớt feature. Kernel SHAP: `nsamples=1000`, identity link,
  `l1_reg=0`; số ảnh thực sự suy luận được đếm, kể cả ảnh nền/ảnh gốc.
- Seed 42, 123, 2026. Không tăng ngân sách riêng cho một phương pháp sau khi đo.
- Cùng batch 32 và 4 luồng CPU. Làm nóng trước đo; luân phiên thứ tự phương pháp.
- Chất lượng: 56 ảnh × 3 seed × 3 phương pháp, trên GPU để giảm thời gian chạy.
- Thời gian triển khai CPU: lấy ảnh đầu tiên của mỗi lớp trong mỗi manifest,
  19 ảnh cố định × 3 seed × 3 phương pháp; không tính load model, dự đoán chung,
  I/O và phép đo chất lượng. Có tính thời gian SLIC cho LIME/SHAP.
- Không chạy hai phép đo CPU/GPU đồng thời, tránh tranh chấp tài nguyên.

## Các phép đo

1. Thời gian mỗi giải thích và số ảnh đi qua mạng. Grad-CAM gồm một forward
   và một backward; LIME/Kernel SHAP không cần backward nhưng cần nhiều forward.
2. Tính ổn định **theo seed lấy mẫu**: IoU mềm của vùng top 20% giữa ba lần.
   Đây không phải độ bền trước thay đổi ảnh, không chứng minh đúng về bệnh học.
3. Khối lượng đóng góp dương trong lá và mức nâng chuẩn hóa
   `(khối lượng trong lá − diện tích lá)/(1 − diện tích lá)`.
4. Mức nâng vào vết bệnh chỉ cho ảnh dự đoán đúng thuộc nhóm triệu chứng khu trú;
   không gộp lá khỏe hoặc triệu chứng khuếch tán. Không dùng nhãn vết bệnh thật
   để chấm một giải thích cho lớp bệnh sai. Vùng gán nhãn có cờ dữ liệu đáng ngờ bị loại khỏi
   chỉ số không gian, nhưng ảnh vẫn chạy và vẫn tính thời gian/fidelity.
5. Deletion AUC (thấp tốt hơn) và insertion AUC (cao tốt hơn): xóa/chèn cùng
   các vùng SLIC theo thứ tự đóng góp dương; 11 mức và tích phân theo diện tích
   pixel thật. Thay vùng bằng cùng nền trung bình. Đây là phép thử nhiễu ảnh,
   không phải chứng minh quan hệ nhân quả hoặc độ chính xác chẩn đoán.

LIME/SHAP có cả đóng góp âm và dương; lưu đầy đủ trọng số có dấu. Để so sánh
với Grad-CAM sau ReLU, chỉ phần dương được vẽ và đo. Đóng góp vùng được chia
cho diện tích vùng khi chuyển thành mật độ pixel, bảo toàn tổng đóng góp.
Vùng top 20% có điểm bằng nhau được chia đều trọng số, tránh ưu tiên vị trí.
Deletion/insertion dùng thứ tự mật độ trung bình trên vùng cho cả ba phương pháp.

Tổng hợp bằng trung bình ba seed **trên từng ảnh** trước khi bootstrap 10.000
lần theo ảnh; không xem 168 lượt seed là 168 ảnh độc lập. Lưu kết quả PV và PD
riêng. Khoảng tin cậy của tập nhỏ chỉ mang tính thăm dò; không dùng p-value để
tuyên bố ưu thế tổng quát.

## Giới hạn bắt buộc khi diễn giải

Các lưới 14 × 14 của #17 do trợ lý AI gán vùng mù từ trước; chưa có bằng chứng
thẩm định độc lập bởi chuyên gia. Chúng là tham chiếu thăm dò, không gọi là
ground truth y khoa/bệnh học. Grad-CAM giải thích logit, còn hai phương pháp
lấy mẫu giải thích xác suất theo cấu hình phổ biến của chúng. Phép thử này so
sánh các cấu hình triển khai đã nêu, không xếp hạng toàn bộ họ phương pháp.

SLIC, ngân sách nhiễu và nền che ảnh ảnh hưởng kết quả LIME/SHAP. Bản đồ 7 × 7
của Grad-CAM được nội suy, không phải segmentation vết bệnh. Không suy accuracy
99,60% của bộ phân loại thành accuracy của XAI. Không tuyên bố phương pháp nào
định vị tốt nhất nếu số đo không hỗ trợ.

## Chạy lại

Từ `model/`, dùng môi trường Python riêng có torch/torchvision tương thích:

```powershell
python -m pip install -r requirements-xai.txt
python -m pytest tests/test_compare_xai.py -q -p no:cacheprovider
python -m pytest tests/test_verify_xai_comparison.py -q -p no:cacheprovider
python -m src.evaluation.compare_xai --device cuda --out outputs/xai-comparison-122/quality
$env:OMP_NUM_THREADS = '4'
$env:OPENBLAS_NUM_THREADS = '4'
$env:MKL_NUM_THREADS = '4'
$env:NUMEXPR_NUM_THREADS = '4'
python -m src.evaluation.compare_xai --device cpu --timing-only --one-per-class --out outputs/xai-comparison-122/cpu
python -m src.evaluation.xai_comparison_report --figures-only
python -m src.evaluation.xai_comparison_report --document-only
python -m src.evaluation.verify_xai_comparison
```

Ảnh gốc vẫn cần có ở `model/data/`, theo đường dẫn hai manifest. Mỗi lần chạy
ghi `protocol.json` trước kết quả, gồm hash checkpoint/code/ảnh, seed, môi trường
và danh sách mẫu. Có thể tiếp tục lệnh đang dở; không chạy lại khi tiến trình cũ
còn sống. Nếu thay code/cấu hình, phải dùng output mới để không trộn kết quả.
Mã thực nghiệm được cố định LF trong `.gitattributes`. Bộ kiểm chứng chấp nhận
LF/CRLF cho mã nguồn và JSON danh mục để tránh báo sai sau khi Git checkout;
mọi khác biệt nội dung vẫn bị chặn. Hash checkpoint và ảnh luôn so byte chính xác.

Kiểm tra bố cục trên Windows có Microsoft Word, từ thư mục gốc repo:

```powershell
./scripts/render-xai-report-word.ps1 -InputDocx docx/bao-cao-so-sanh-gradcam-lime-shap.docx -OutputDirectory "$env:TEMP/agrixai-xai-render"
```

Script mở tài liệu chỉ đọc trong Word instance riêng và xuất ảnh PNG từng trang
bằng `Page.EnhMetaFileBits`; không cần bộ xuất PDF. Phải xem lại toàn bộ các trang
sau khi tạo hoặc đổi bố cục báo cáo.

## Nguồn phương pháp

1. Selvaraju và cộng sự. Grad-CAM. ICCV 2017. https://arxiv.org/abs/1610.02391
2. Ribeiro, Singh và Guestrin. LIME. KDD 2016. https://arxiv.org/abs/1602.04938
3. Lundberg và Lee. SHAP. NeurIPS 2017. https://arxiv.org/abs/1705.07874
4. Tài liệu LIME Image: https://lime-ml.readthedocs.io/en/latest/lime.html#module-lime.lime_image
5. Tài liệu Kernel SHAP: https://shap.readthedocs.io/en/latest/generated/shap.KernelExplainer.html
6. Petsiuk, Das và Saenko. RISE. BMVC 2018. https://arxiv.org/abs/1806.07421
