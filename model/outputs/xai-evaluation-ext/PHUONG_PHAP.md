# Đánh giá XAI mở rộng: đồng thuận, MPRT, Average Drop, deletion/insertion, độ bền

Mở rộng phép so sánh #122 (Grad-CAM, LIME, Kernel SHAP) và #98 (Grad-CAM++) bằng
năm nhóm chỉ số phổ biến trong tài liệu đánh giá XAI mà dự án chưa đo. Mã:
`src/evaluation/extend_xai_eval.py`; kiểm thử: `tests/test_extend_xai_eval.py`.

## Thiết kế cố định trước khi đo

- **Checkpoint gốc** `checkpoints/leaf_disease_detection_model.pt`
  (`efficientnet_b0-20260907-1443`), đúng checkpoint của #122/#98 để so được với số
  cũ. Kết quả **không** áp dụng nguyên cho checkpoint domain-adapted đang chạy.
- Cùng **56 ảnh** của #17/#122 (30 PlantVillage, 26 PlantDoc), ảnh 224×224 đã lưu ở
  `xai-comparison-122/quality/images` (đối chiếu từng byte với ảnh gốc resize trước khi đo).
- Cùng lớp mục tiêu (lớp dự đoán trên ảnh gốc), cùng SLIC, cùng nền RGB trung bình.
- Bản đồ LIME/Kernel SHAP 3 seed **đọc lại từ #122**, không tính lại. Grad-CAM và
  Grad-CAM++ tính lại trên GPU rồi đối chiếu: Grad-CAM khớp #122 tuyệt đối,
  Grad-CAM++ lệch #98 (CPU) tối đa cỡ 1e-6; số thật ghi trong mỗi `protocol.json`.
- Tổng hợp như #122: trung bình theo seed trên từng ảnh rồi bootstrap 10.000 lần theo
  ảnh; báo riêng PV/PD và đoán đúng/sai. KTC chỉ mang tính thăm dò.

## 2. Đồng thuận giữa phương pháp (`agreement/`)

Theo Krishna et al. (TMLR 2024). Hai bản đồ được quy về **cùng đơn vị** trước khi so,
vì Grad-CAM mượt còn LIME/SHAP là hằng số trên vùng SLIC: (a) mật độ trung bình trên
mỗi vùng SLIC, (b) trên lưới 14×14. Chỉ số: Spearman giữa thứ hạng đơn vị; tỉ lệ trùng
top 20% đơn vị (feature agreement, chia đều khi hoà điểm). Cặp lấy mẫu–lấy mẫu ghép cùng
seed; lấy mẫu–xác định ghép từng seed. Thêm **trần tham chiếu**: hai seed của cùng
LIME/SHAP — hai phương pháp khác nhau khó đồng thuận hơn mức này.

## 3. MPRT — sanity check ngẫu nhiên hoá (`mprt/`, `mprt-reset_keep_bn/`)

Theo Adebayo et al. (NeurIPS 2018), cascading từ đầu ra về đầu vào: `classifier` →
`features.8` → … → `features.0` (10 bước), cùng seed theo bước cho mọi phương pháp.
So bản đồ trên mô hình ngẫu nhiên với bản gốc bằng Spearman, SSIM, tương quan HOG; thêm
**Smooth MPRT** (Hedström et al., 2024: trung bình 10 bản ảnh nhiễu σ = 0,1 × biên độ
input) và tỉ số entropy kiểu **eMPRT**. Bản đồ rỗng sau ngẫu nhiên hoá được đếm riêng
(`randomized_empty`), không bị bỏ khỏi trung bình.

**Cách ngẫu nhiên hoá — quyết định có chẩn đoán đi kèm.** `reset_parameters()` mặc định
của PyTorch, giữ BN đã huấn luyện, làm đầu ra tầng Grad-CAM **ngừng thay đổi từ bước 4**:
BN đặt trên trọng số khác thang xoá tín hiệu của các tầng dưới, nên phép thử không còn
thử gì. Reset cả BN thì activation tắt dần về ~1e-13. Mặc định vì vậy là **`matched`**:
lấy mẫu N(mean, std) của chính tensor đã huấn luyện cho Conv/Linear, giữ BN. Bảng
`propagation_diagnostics` trong `summary.json` ghi cho cả hai chế độ: activation còn phụ
thuộc ảnh không và có đổi theo từng bước không. Bản `reset_keep_bn` vẫn chạy để đối chứng.

**Không chạy MPRT cho LIME/Kernel SHAP.** Ban đầu định đo bước cuối (mô hình ngẫu nhiên
hoàn toàn) cho hai phương pháp này, nhưng trên mô hình đó logit cỡ −3,7e6 làm softmax bão
hoà thành one-hot cố định. LIME/SHAP giải thích *xác suất*, nên bản đồ luôn rỗng một cách
hiển nhiên: phép thử suy biến, không cho thông tin gì (forward cũng chậm ~10 phút/ảnh).
Số liệu bão hoà ghi trong `summary.json` mục `sampled_methods_note`. Grad-CAM/Grad-CAM++
dùng gradient logit và chuẩn hoá bản đồ nên không bị ảnh hưởng. Đây cũng là lý do
Adebayo et al. chủ yếu áp MPRT cho phương pháp dựa trên gradient.

## 4. Average Drop / Increase in Confidence (`drop/`)

Theo Chattopadhay et al. (2018, bài Grad-CAM++). Hai biến thể: **nhân theo điểm**
`x ⊙ H` (H chia max) như bài gốc; **giữ top 15% pixel**, phần còn lại thay bằng nền
trung bình (kiểu Score-CAM). Drop = trung bình `max(0, Y − O)/Y × 100` (thấp tốt);
Increase = % ảnh có `O > Y` (cao tốt); Win% = tỉ lệ ảnh phương pháp có Drop thấp nhất
(hoà chia đều). Nhân theo điểm làm ảnh tối — đây là phép thử nhiễu ảnh, không phải đo
định vị bệnh.

## 5. Deletion/insertion với cách lấp khác (`faithfulness/`)

Giữ 11 mức và trục diện tích pixel như #122. Lưới 2 đơn vị × 3 cách lấp:
- đơn vị: vùng SLIC (như #122) hoặc lưới 14×14 — vì SLIC là đúng đơn vị LIME/SHAP tối ưu;
- cách lấp: **trung bình** (như #122), **làm mờ** Gaussian σ = 10 px (kiểu RISE),
  **ROAD** noisy linear imputation (Rong et al., ICML 2022): pixel bị xoá = trung bình
  có trọng số 8 láng giềng (1/6 cạnh, 1/12 chéo), giải hệ tuyến tính thưa, nhiễu
  σ = 0,01. Đây là cài đặt theo mô tả bài báo, không phải mã chính thức.
- Insertion trên trục diện tích được giữ trùng diện tích với đường LeRF của ROAD, nên
  `gap = insertion − deletion` tương ứng điểm LeRF − MoRF ROAD khuyến nghị.

Ô (SLIC, trung bình) phải tái tạo đúng số #122 — sai lệch thực đo ghi trong `summary.json`.

## 6. Độ bền trước nhiễu kiểu điện thoại (`sensitivity/`)

Theo ý Avg-/Max-Sensitivity (Yeh et al., 2019) nhưng thay nhiễu ngẫu nhiên bằng năm biến
đổi kiểu chụp lại: sáng +15%, tối −15%, JPEG q70, mờ σ = 1, nhiễu Gaussian sd 5. Áp trên
ảnh 224 (xấp xỉ: ngoài đời biến đổi xảy ra trước resize). **Chỉ đo khi nhãn dự đoán giữ
nguyên**; số lần nhãn đổi báo riêng. LIME/SHAP tính lại seed 42 trên ảnh nhiễu (SLIC và
nền tính lại theo ảnh nhiễu, như app sẽ làm) và so với seed 42 gốc; **sàn nhiễu** = khoảng
cách seed 42 với 123/2026 trên ảnh gốc. Khoảng cách sau khi chia max: L2 tương đối,
1 − Spearman, và **IoU vùng app khoanh** ở ngưỡng 0,62 (`OVERLAY_DRAW_THRESHOLD`).
`worst_*` là trường hợp xấu nhất trong năm biến đổi. Vài ảnh đầu được tính lại LIME/SHAP
seed 42 không nhiễu để kiểm môi trường tái lập đúng #122.

## Giới hạn

Mặt nạ lá/vết bệnh của #17 do AI khoanh mù, chưa có chuyên gia xác nhận. 56 ảnh là tập
thăm dò đã chọn từ trước. Mọi phép che/xoá ảnh đều có thể đưa ảnh ra ngoài phân phối;
đổi cách lấp là để xem kết luận có bền không, không phải để có "cách đúng duy nhất".
Grad-CAM giải thích logit, LIME/SHAP giải thích xác suất. Không đo bản ONNX ngoại tuyến.

## Chạy lại

Từ `model/`, trong môi trường có `requirements-xai.txt` và torch tương thích:

```powershell
python -m pytest tests/test_extend_xai_eval.py -q -p no:cacheprovider
python -u -m src.evaluation.extend_xai_eval agreement
python -u -m src.evaluation.extend_xai_eval drop
python -u -m src.evaluation.extend_xai_eval mprt
python -u -m src.evaluation.extend_xai_eval mprt --init reset_keep_bn
python -u -m src.evaluation.extend_xai_eval faithfulness
python -u -m src.evaluation.extend_xai_eval sensitivity   # tiếp tục được nếu bị ngắt
```

Cần đầu ra #122 (`xai-comparison-122/quality`) và #98 (`gradcam-plus-plus-98/maps`) cùng
ảnh gốc trong `model/data/`. Mỗi lệnh ghi `protocol.json` (hash checkpoint/script, git
HEAD, phiên bản thư viện, danh sách ảnh, sai lệch đối chiếu Grad-CAM/Grad-CAM++).

## Nguồn phương pháp

1. Krishna et al. The Disagreement Problem in Explainable ML. TMLR 2024. https://arxiv.org/abs/2202.01602
2. Adebayo et al. Sanity Checks for Saliency Maps. NeurIPS 2018. https://arxiv.org/abs/1810.03292
3. Hedström et al. A Fresh Look at Sanity Checks for Saliency Maps. 2024. https://arxiv.org/abs/2405.02383
4. Chattopadhay et al. Grad-CAM++. WACV 2018. https://arxiv.org/abs/1710.11063
5. Wang et al. Score-CAM. CVPR-W 2020. https://arxiv.org/abs/1910.01279
6. Rong et al. A Consistent and Efficient Evaluation Strategy for Attribution Methods (ROAD). ICML 2022. https://arxiv.org/abs/2202.00449
7. Petsiuk et al. RISE. BMVC 2018. https://arxiv.org/abs/1806.07421
8. Yeh et al. On the (In)fidelity and Sensitivity of Explanations. NeurIPS 2019. https://arxiv.org/abs/1901.09392
