# Đánh giá XAI mở rộng — tóm tắt kết quả

Mở rộng phép so sánh #122/#98 bằng năm nhóm chỉ số phổ biến trong tài liệu đánh giá XAI.
Cùng 56 ảnh (30 PlantVillage — PV, 26 PlantDoc — PD), cùng checkpoint gốc
`efficientnet_b0-20260907-1443`, cùng lớp mục tiêu và SLIC như #122. Số trong ngoặc là
KTC 95% bootstrap theo ảnh — **tập thăm dò nhỏ, đọc như xu hướng, không phải kết luận
tổng quát**. Thiết kế đầy đủ: `model/outputs/xai-evaluation-ext/PHUONG_PHAP.md`.

## Kết luận chính

1. **Kết luận "LIME/SHAP trung thực hơn Grad-CAM" của #122 không bền.** Nó chỉ đúng khi che
   ảnh bằng màu trung bình trên vùng SLIC — đúng kiểu nhiễu LIME/SHAP dùng để tạo giải thích.
   Lấp kiểu ROAD thì Grad-CAM ngang LIME, hơn Kernel SHAP; xoá theo lưới đều thì Grad-CAM tốt
   nhất (mục 5). Đây là bổ sung quan trọng cho lý do chọn Grad-CAM, ngoài tốc độ.
2. **Grad-CAM qua sanity check MPRT rõ ràng; Grad-CAM++ chỉ qua một phần.** Phá lớp phân loại
   mà bản đồ Grad-CAM++ gần như không đổi (Spearman 0,90) — nó chủ yếu chỉ "chỗ đặc trưng
   mạnh", ít phụ thuộc lớp bệnh (mục 3).
3. **Grad-CAM++ bền nhất khi chụp lại** (IoU vùng khoanh 0,76 so với 0,71 của Grad-CAM;
   LIME 0,52, SHAP 0,45) nhưng **kém Grad-CAM về độ trung thực**: ở Drop nhân theo điểm và ở
   cả 6 cấu hình deletion/insertion, KTC không chứa 0 (Drop giữ top 15% thì chưa phân biệt được). Quyết định bật Grad-CAM++ mặc định (#98) vì vậy là đánh
   đổi: vùng khoanh ổn định hơn, đổi lại bám quyết định của mô hình kém hơn. Nên cân nhắc lại.
4. **Các phương pháp chỉ đồng thuận thấp–vừa** (Grad-CAM với LIME/SHAP Spearman 0,34–0,42), và
   tách xa hơn trên ảnh thật/ảnh đoán sai: vùng khoanh là lời giải thích của *một* phương pháp,
   không phải sự thật duy nhất (mục 2).
5. **Average Drop đảo thứ hạng theo cách che** (mục 4): không chỉ số trung thực nào đủ để
   tuyên bố một phương pháp "tốt nhất" — phải báo nhiều cách đo cùng lúc.
6. Phát hiện phụ về mô hình: chỉ làm mờ nhẹ (σ = 1) đã đổi nhãn bệnh ở 8/56 ảnh (mục 6).

| Phép đo | Grad-CAM | Grad-CAM++ | LIME | Kernel SHAP |
|---|---|---|---|---|
| Sanity check MPRT | ✅ qua rõ | ⚠️ qua một phần | không đo được* | không đo được* |
| Độ trung thực (gap, lấp ROAD) | **tốt nhất / ngang** | kém hơn Grad-CAM | ngang Grad-CAM | kém hơn |
| Average Drop nhân theo điểm | **tốt nhất** | kém hơn | kém hơn (chưa chắc) | kém hơn |
| Average Drop giữ top 15% | kém | kém | tốt | **tốt nhất** |
| Độ bền khi chụp lại | tốt | **tốt nhất** | kém | kém nhất |

\* Softmax của mô hình ngẫu nhiên bão hoà, phép thử suy biến với phương pháp giải thích xác suất.

## 2. Các phương pháp có chỉ cùng một chỗ không? (đồng thuận)

Spearman giữa thứ hạng vùng SLIC (1 = trùng hoàn toàn, 0 = không liên quan).
"Trần" là hai seed của cùng một phương pháp lấy mẫu.

| Cặp | Tất cả | PV | PD |
|---|---:|---:|---:|
| Grad-CAM ~ Grad-CAM++ | 0,715 [0,638; 0,784] | 0,873 | 0,532 |
| Grad-CAM ~ LIME | 0,416 [0,371; 0,461] | 0,499 | 0,320 |
| Grad-CAM ~ Kernel SHAP | 0,337 [0,297; 0,377] | 0,354 | 0,318 |
| Grad-CAM++ ~ LIME | 0,362 [0,301; 0,422] | 0,500 | 0,203 |
| Grad-CAM++ ~ Kernel SHAP | 0,275 [0,223; 0,326] | 0,364 | 0,172 |
| LIME ~ Kernel SHAP | 0,634 [0,593; 0,674] | 0,574 | 0,704 |
| *Trần: LIME ~ LIME (đổi seed)* | *0,858* | *0,825* | *0,897* |
| *Trần: SHAP ~ SHAP (đổi seed)* | *0,645* | *0,507* | *0,804* |

- Hai nhóm phương pháp **chỉ đồng thuận ở mức thấp–vừa**: Grad-CAM với LIME/SHAP chỉ
  0,34–0,42; top 20% vùng quan trọng trùng 43–48%. Đây đúng là "disagreement problem":
  vùng khoanh là lời giải thích của **một** phương pháp, không phải sự thật duy nhất.
- Hai họ nội bộ đồng thuận hơn nhiều (Grad-CAM~Grad-CAM++ 0,72; LIME~SHAP 0,63) — khác
  biệt chủ yếu đến từ **cách tạo giải thích** (gradient so với che vùng), không phải nhiễu.
- **Trên ảnh thật (PD) và ảnh đoán sai, nhóm CAM tách khỏi nhóm lấy mẫu**: Grad-CAM~Grad-CAM++
  tụt từ 0,87 (PV) xuống 0,53 (PD), 0,46 ở ảnh đoán sai; Grad-CAM++~SHAP chỉ 0,17 trên PD.
  Ngược lại LIME~SHAP lại tăng trên PD (0,70). Khớp với #17: giải thích kém ổn định đúng
  ở loại ảnh mô hình làm kém.
- So trên lưới 14×14 thay cho vùng SLIC cho cùng thứ tự các cặp; mức đồng thuận cao hơn
  một chút (chênh tối đa 0,07, ví dụ Grad-CAM~LIME 0,475 thay vì 0,416).

## 3. Giải thích có thật sự phụ thuộc mô hình? (MPRT)

Ngẫu nhiên hoá dần trọng số từ đầu ra về đầu vào (10 bước), rồi so bản đồ với bản gốc.
Qua phép thử nghĩa là bản đồ **phải đổi mạnh** khi mô hình bị phá.

| Bước ngẫu nhiên hoá | Grad-CAM: Spearman | Grad-CAM: bản đồ rỗng | Grad-CAM++: Spearman | Grad-CAM++: SSIM |
|---|---:|---:|---:|---:|
| 1 — chỉ `classifier` | −0,334 [−0,42; −0,24] | 0% | **0,897** [0,87; 0,92] | 0,798 |
| 2 — thêm `features.8` | −0,375 | 0% | 0,834 | 0,652 |
| 3 — thêm `features.7` | — | **100%** | 0,382 | 0,352 |
| 6 — tới `features.4` | — | 100% | 0,067 | 0,406 |
| 10 — toàn bộ mạng | — | 100% | 0,007 [−0,06; 0,07] | 0,393 |

- **Grad-CAM qua rõ ràng**, khớp Adebayo et al. (2018): phá riêng lớp phân loại là bản đồ
  đã đảo chiều (−0,33); từ bước 3 bản đồ biến mất hoàn toàn trên cả 56 ảnh.
- **Grad-CAM++ chỉ qua một phần.** Phá lớp phân loại mà bản đồ gần như giữ nguyên
  (Spearman 0,90, SSIM 0,80), phải phá sâu tới `features.4` mới về ~0, và SSIM vẫn ~0,4.
  Nghĩa là Grad-CAM++ — **đang bật mặc định từ #98** — chủ yếu chỉ ra "chỗ đặc trưng mạnh"
  và **ít phụ thuộc vào trọng số của lớp bệnh** được giải thích. Kết quả này lặp lại y hệt
  ở cách khởi tạo đối chứng (0,895), nên không phải do cách làm.
- Smooth MPRT (trung bình 10 bản ảnh nhiễu) cho cùng xu hướng; ở Grad-CAM++ bước 1 vẫn 0,92.
- **Chi tiết phương pháp phải nói được khi bảo vệ:** cách ngẫu nhiên hoá mặc định của
  PyTorch (`reset_parameters`, giữ BatchNorm) làm phép thử **vô hiệu**: từ bước 4 mạng cho
  activation giống hệt nhau với hai ảnh khác nhau (tương quan 1,00), số liệu "đóng băng".
  Đã thay bằng lấy mẫu theo phân phối của chính trọng số đã huấn luyện; bảng chẩn đoán lan
  truyền tín hiệu lưu trong `mprt/summary.json`.
- **Không đo được LIME/SHAP**: trên mô hình ngẫu nhiên hoàn toàn, softmax bão hoà thành
  one-hot cố định (xác suất lớn nhất = 1,0 trên cả 56 ảnh), nên hai phương pháp giải thích
  xác suất luôn ra bản đồ rỗng — phép thử suy biến, không mang thông tin.

## 4. Chỉ giữ vùng được giải thích, mô hình còn tự tin không? (Average Drop)

| Phương pháp | Drop nhân theo điểm ↓ | Drop giữ top 15% ↓ | Win% (top 15%) ↑ |
|---|---:|---:|---:|
| Grad-CAM | **25,2** [16,8; 34,4] | 63,9 [55,2; 72,1] | 11,8 |
| Grad-CAM++ | 31,4 [21,7; 41,3] | 66,6 [58,9; 73,9] | 6,4 |
| LIME | 32,1 [23,8; 41,0] | 48,0 [38,7; 57,4] | 33,8 |
| Kernel SHAP | 35,2 [26,5; 44,4] | **46,2** [36,4; 55,8] | 48,1 |

- **Thứ hạng đảo chiều theo cách che.** Với định nghĩa gốc của bài Grad-CAM++ (nhân ảnh
  với bản đồ), Grad-CAM tốt nhất; chênh với Grad-CAM++ −6,1 điểm [−10,7; −2,1] và với
  Kernel SHAP −10,0 [−18,0; −1,8] — KTC không chứa 0. Với cách giữ top 15% pixel, LIME
  và Kernel SHAP tốt hơn Grad-CAM 15,9 [10,6; 21,5] và 17,7 [12,0; 24,0] điểm.
- **Grad-CAM++ không thắng Grad-CAM trên chính chỉ số do bài Grad-CAM++ đề xuất** trong
  cấu hình này. Đáng nói khi được hỏi vì sao bật Grad-CAM++ mặc định (#98): quyết định đó
  dựa trên chỉ số định vị trong lá, không dựa trên độ trung thực.
- Trên PD, che ảnh làm xác suất **tăng** ở 50% ảnh (biến thể nhân) — phần lớn ảnh PD bị
  đoán sai (19/26), bỏ bớt bối cảnh có thể đẩy mô hình về lớp nó đã chọn. Không đọc Drop
  trên PD như bằng chứng giải thích "đúng".

## 5. Kết luận deletion/insertion của #122 có bền khi đổi cách che? (ROAD)

#122 kết luận LIME/Kernel SHAP tốt hơn Grad-CAM ở deletion/insertion. Phép đo đó che vùng
bằng **màu trung bình** trên **vùng SLIC** — đúng kiểu nhiễu LIME/SHAP dùng khi tạo giải
thích. Ở đây đo lại cùng 56 ảnh với 3 cách lấp × 2 đơn vị xoá. Chỉ số gộp:
**gap = insertion − deletion** (cao tốt; tương ứng LeRF − MoRF của ROAD).

| Cách đo | Grad-CAM | Grad-CAM++ | LIME | Kernel SHAP | Tốt nhất |
|---|---:|---:|---:|---:|---|
| SLIC + trung bình *(= #122)* | 0,260 | 0,210 | **0,447** | 0,413 | LIME |
| SLIC + làm mờ | 0,306 | 0,247 | **0,360** | 0,309 | LIME |
| SLIC + ROAD | **0,297** | 0,243 | 0,284 | 0,233 | Grad-CAM |
| Lưới + trung bình | 0,290 | 0,217 | **0,385** | 0,354 | LIME |
| Lưới + làm mờ | **0,336** | 0,278 | 0,329 | 0,280 | Grad-CAM |
| Lưới + ROAD | **0,345** | 0,278 | 0,287 | 0,246 | Grad-CAM |

Chênh ghép cặp Grad-CAM − LIME về gap: −0,187 [−0,222; −0,153] ở cấu hình #122, nhưng
+0,013 [−0,022; 0,047] với SLIC + ROAD và **+0,059 [0,025; 0,092]** với lưới + ROAD.
Grad-CAM − Kernel SHAP: −0,153 ở cấu hình #122, **+0,064 [0,023; 0,102]** với SLIC + ROAD.

- **Kết luận "LIME/SHAP trung thực hơn" của #122 không bền với cách đo.** Ưu thế đó gần
  như chỉ tồn tại khi đánh giá bằng đúng kiểu nhiễu LIME/SHAP được tối ưu (nền trung bình,
  vùng SLIC). Khi lấp bằng ROAD — cách được đề xuất để giảm rò rỉ thông tin qua hình dạng
  mặt nạ — Grad-CAM ngang LIME và hơn Kernel SHAP; xoá theo lưới đều thì Grad-CAM tốt nhất.
- Riêng **deletion** (xoá vùng quan trọng trước), LIME vẫn nhỉnh hơn Grad-CAM ở vài cấu hình
  nhưng chênh nhỏ (≤ 0,03 với ROAD).
- **Grad-CAM++ kém Grad-CAM ở cả 6 cấu hình** (gap thấp hơn 0,05–0,07, KTC không chứa 0) —
  cùng chiều với Average Drop ở mục 4 và MPRT ở mục 3.
- Trên ảnh thật (PD), lợi thế của LIME/SHAP ở cấu hình #122 (gap ~0,46 so với 0,25) biến mất
  hoàn toàn khi dùng ROAD (Grad-CAM 0,20, LIME 0,19, SHAP 0,18; Grad-CAM++ chỉ 0,11).
- Kiểm chứng: ô (SLIC, trung bình) tái tạo đúng số #122, sai lệch tối đa 3,3e-6.

## 6. Chụp lại hơi khác, vùng khoanh có giữ nguyên? (độ bền)

Năm biến đổi kiểu chụp lại: sáng/tối ±15%, JPEG q70, mờ σ = 1, nhiễu sd 5. Chỉ đo khi
nhãn dự đoán giữ nguyên. Chỉ số chính: **IoU của chính vùng app khoanh** (ngưỡng 0,62)
giữa ảnh gốc và ảnh biến đổi — 1 là vùng khoanh y hệt.

| Phương pháp | IoU trung bình ↑ | IoU trường hợp xấu nhất ↑ | Sàn nhiễu (chỉ đổi seed) |
|---|---:|---:|---:|
| Grad-CAM | 0,713 [0,670; 0,754] | 0,532 | — (xác định) |
| Grad-CAM++ | **0,758** [0,716; 0,796] | **0,594** | — (xác định) |
| LIME | 0,515 [0,471; 0,559] | 0,224 | 0,732 |
| Kernel SHAP | 0,446 [0,403; 0,492] | 0,159 | 0,502 |

- **Grad-CAM++ bền nhất**, hơn Grad-CAM 0,045 [0,014; 0,077]. Grad-CAM hơn LIME 0,20 và
  Kernel SHAP 0,27 (KTC không chứa 0). Đây là điểm cộng thật của Grad-CAM++ cho app: nông
  dân chụp lại cùng chiếc lá thì vùng khoanh ít nhảy hơn.
- LIME đổi nhiều hơn hẳn mức dao động do riêng việc đổi seed (0,52 so với 0,73): phần lớn
  thay đổi đến từ ảnh, không phải từ lấy mẫu. Kernel SHAP vốn đã dao động gần bằng mức đó
  ngay khi giữ nguyên ảnh (sàn 0,50).
- Biến đổi gây xáo trộn nhất là **mờ σ = 1** và **JPEG q70** (Grad-CAM IoU 0,63/0,67;
  LIME 0,35/0,40); đổi sáng ±15% gần như không ảnh hưởng (Grad-CAM 0,81–0,84).
- Ảnh thật kém bền hơn ảnh phòng thí nghiệm ở mọi phương pháp (Grad-CAM IoU 0,81 PV so
  với 0,60 PD).
- **Phát hiện phụ về mô hình, không phải XAI:** chỉ làm mờ nhẹ σ = 1 đã **đổi nhãn bệnh ở
  8/56 ảnh**, JPEG q70 đổi 7/56, sáng +15% đổi 3/56. Đây là thêm một bằng chứng về độ
  mong manh trước điều kiện chụp, bổ sung cho kết quả domain gap #49.
- Kiểm tái lập: LIME/SHAP seed 42 tính lại trong môi trường mới trùng #122 tuyệt đối
  (sai lệch 0 trên 6 ảnh kiểm).

## Giới hạn

- 56 ảnh là tập thăm dò đã chọn cho #17; mặt nạ lá/vết bệnh do AI khoanh mù, chưa có
  chuyên gia xác nhận. Đo trên **checkpoint gốc**, không phải bản domain-adapted đang
  chạy; không áp dụng cho bản ONNX ngoại tuyến (CAM cổ điển).
- Mọi phép che/xoá đều có thể đưa ảnh ra ngoài phân phối; đổi cách lấp để kiểm độ bền
  của kết luận, không có "cách đúng duy nhất". ROAD ở đây cài theo mô tả bài báo.
- Grad-CAM giải thích logit, LIME/SHAP giải thích xác suất. Kernel SHAP không đại diện
  cho mọi biến thể SHAP.

## Tái lập

Mã: `model/src/evaluation/extend_xai_eval.py` (`agreement`, `mprt`, `drop`,
`faithfulness`, `sensitivity`), kiểm thử `model/tests/test_extend_xai_eval.py`. Kết quả từng
ảnh, `summary.json` và `protocol.json` (hash checkpoint/script, phiên bản thư viện, sai
lệch đối chiếu) nằm trong `model/outputs/xai-evaluation-ext/`.
