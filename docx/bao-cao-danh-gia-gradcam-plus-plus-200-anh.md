# Đánh giá Grad-CAM++ trên bộ 200 ảnh mới

Kiểm tra lại Grad-CAM++ — phương pháp đang bật mặc định trên server — bằng một bộ ảnh
**lớn gấp ~3,6 lần** bộ 56 ảnh cũ, **không trùng ảnh nào** với bộ đó, và trên **checkpoint
đang triển khai** (`leaf_disease_domain_adapted.pt`). Grad-CAM gốc chạy song song làm mốc.
Số trong ngoặc là khoảng tin cậy 95% bootstrap theo ảnh. Thiết kế và lệnh chạy lại:
`model/outputs/xai-eval-200/PHUONG_PHAP.md`.

## Kết luận chính

1. **Kết luận của bộ 56 ảnh được xác nhận trên bộ mới lớn hơn và checkpoint thật.** Cả bốn
   xu hướng đều lặp lại, nay với khoảng tin cậy hẹp hơn nhiều.
2. **Grad-CAM++ bền hơn rõ rệt khi chụp lại:** IoU vùng khoanh 0,842 so với 0,789 của Grad-CAM
   (+0,053 [0,039; 0,067]); trên ảnh thật PlantDoc chênh còn lớn hơn (+0,097). Thắng ở cả 5
   kiểu biến đổi. Đây là điểm mạnh thật của bản ++ cho trải nghiệm người dùng.
3. **Nhưng Grad-CAM++ kém trung thực hơn Grad-CAM** ở cả 6 cấu hình deletion/insertion và ở
   Average Drop; mọi khoảng tin cậy đều không chứa 0. Khoảng cách lớn nhất trên ảnh thật.
4. **Grad-CAM++ chỉ qua sanity check MPRT một phần:** phá lớp phân loại mà bản đồ gần như
   giữ nguyên (Spearman 0,945). Grad-CAM qua rõ ràng (−0,573).
5. Hệ quả cho quyết định bật Grad-CAM++ mặc định (#98): đó là **đánh đổi**, không phải nâng
   cấp toàn diện — vùng khoanh ổn định hơn, đổi lại bám quyết định của mô hình kém hơn.

## Bộ ảnh

| | Số ảnh | Mô hình đoán đúng | Qua bộ chặn lá |
|---|--:|--:|--:|
| PlantVillage test (10 lớp, 13–14 ảnh/lớp) | 139 | 136 (97,8%) | 139 |
| PlantDoc test (8 lớp, toàn bộ phần còn lại) | 61 | 38 (62,3%) | 55 |
| **Tổng** | **200** | **174** | **194** |

- Lấy từ `test-inventory.json` của checkpoint đang triển khai — đúng tập ảnh mô hình **chưa
  từng học**. Loại 35 ảnh của bộ 56 cũ (30 PV + 5 PD) và 1 ảnh trùng nội dung; đối chiếu
  SHA-256 với toàn bộ dữ liệu huấn luyện: không trùng ảnh nào.
- PlantDoc chỉ có 61 ảnh vì checkpoint này đã học PlantDoc train; dùng ảnh train sẽ làm
  phép đo bị rò rỉ dữ liệu.
- **Không có mặt nạ lá/vết bệnh** cho bộ này, nên không đo khối lượng heatmap trong lá, mức
  nâng hay contour ngoài lá. Các chỉ số đó vẫn chỉ có trên bộ 56.

## 1. Độ bền khi chụp lại — Grad-CAM++ tốt hơn

IoU vùng khoanh (ngưỡng 0,62) giữa ảnh gốc và ảnh biến đổi; chỉ tính ảnh giữ nguyên nhãn.

| Biến đổi | Số ảnh | Grad-CAM++ | Grad-CAM | Chênh (++ − GC) |
|---|--:|--:|--:|--:|
| Sáng hơn 15% | 198 | 0,918 | 0,890 | +0,028 [0,016; 0,041] |
| Tối hơn 15% | 196 | 0,922 | 0,892 | +0,030 [0,018; 0,043] |
| Nén JPEG q70 | 187 | 0,792 | 0,731 | +0,062 [0,041; 0,084] |
| Mờ nhẹ σ = 1 | 189 | 0,761 | 0,695 | +0,066 [0,042; 0,090] |
| Nhiễu sd 5 | 185 | 0,806 | 0,740 | +0,066 [0,048; 0,086] |
| **Trung bình mỗi ảnh** | 200 | **0,842** | 0,789 | **+0,053 [0,039; 0,067]** |
| Trường hợp xấu nhất mỗi ảnh | 200 | 0,709 | 0,633 | +0,076 [0,054; 0,099] |

Trên PlantDoc: 0,788 so với 0,690 (+0,097 [0,059; 0,138]). Phát hiện phụ về mô hình: nhiễu
sd 5 đổi nhãn 15/200 ảnh, JPEG q70 đổi 13/200, mờ nhẹ đổi 11/200.

## 2. Độ trung thực — Grad-CAM tốt hơn

Gap = insertion − deletion (cao hơn là tốt hơn).

| Cách đo | Grad-CAM++ | Grad-CAM | Chênh (++ − GC) |
|---|--:|--:|--:|
| SLIC + màu trung bình | 0,244 | 0,257 | −0,013 [−0,022; −0,005] |
| SLIC + làm mờ | 0,383 | 0,409 | −0,026 [−0,037; −0,016] |
| SLIC + ROAD | 0,403 | 0,433 | −0,030 [−0,041; −0,020] |
| Lưới + màu trung bình | 0,264 | 0,283 | −0,019 [−0,027; −0,010] |
| Lưới + làm mờ | 0,392 | 0,431 | −0,039 [−0,051; −0,026] |
| **Lưới + ROAD** | 0,405 | **0,451** | **−0,046 [−0,060; −0,033]** |

Grad-CAM++ thua ở **cả 6 cấu hình**, ở cả deletion (xoá vùng của ++ làm xác suất tụt chậm hơn)
lẫn insertion. Trên PlantDoc chênh lớn gấp đôi (lưới + ROAD: −0,084 [−0,119; −0,051]).

## 3. Average Drop — Grad-CAM tốt hơn

| Chỉ số | Grad-CAM++ | Grad-CAM | Chênh (++ − GC) |
|---|--:|--:|--:|
| Average Drop, nhân theo điểm ↓ | 29,3% | **22,1%** | +7,2 [4,9; 9,7] |
| Increase ↑ | 16,0% | **21,0%** | −5,0 [−9,0; −1,0] |
| Win% (giữa 2 phương pháp) ↑ | 32,0% | **68,0%** | −36,0 [−47,5; −24,5] |
| Average Drop, giữ top 15% ↓ | 73,0% | **71,1%** | +1,9 [0,5; 3,4] |

Grad-CAM++ thua ở cả hai biến thể; Grad-CAM giảm ít hơn ở 68% số ảnh.

## 4. Sanity check MPRT — Grad-CAM++ chỉ qua một phần

Ngẫu nhiên hoá dần trọng số từ đầu ra về đầu vào; qua phép thử nghĩa là bản đồ **phải đổi mạnh**.

| Bước | Grad-CAM++: Spearman | Grad-CAM++: SSIM | Grad-CAM: Spearman | Grad-CAM: bản đồ rỗng |
|---|--:|--:|--:|--:|
| 1 — chỉ lớp phân loại | **0,945** [0,941; 0,950] | 0,842 | **−0,573** [−0,608; −0,538] | 0% |
| 2 — thêm `features.8` | 0,902 | 0,716 | −0,568 | 0% |
| 3 — thêm `features.7` | 0,649 | 0,285 | — | 100% |
| 6 — tới `features.4` | 0,077 | 0,299 | — | 100% |
| 10 — toàn bộ mạng | −0,024 [−0,054; 0,007] | 0,307 | — | 100% |

Phá riêng lớp phân loại — tức phá đúng phần biết "đây là bệnh gì" — mà bản đồ Grad-CAM++ gần
như không đổi. Nghĩa là Grad-CAM++ chủ yếu chỉ ra "chỗ có đặc trưng mạnh" chứ ít phụ thuộc
vào lớp bệnh đang được giải thích. Grad-CAM đảo chiều ngay bước 1 và biến mất từ bước 3.

## 5. Độ lặp lại và đồng thuận

- Cả hai phương pháp **xác định**: tính lại cùng ảnh, sai lệch lớn nhất bằng 0. Không bản đồ
  nào rỗng trên 200 ảnh gốc.
- Hai phương pháp đồng thuận cao: Spearman 0,835 [0,808; 0,859] theo mảnh SLIC, trùng top 20%
  ở 86,8% — khác nhau chủ yếu ở cách phân bố cường độ, không phải chỉ vào chỗ khác hẳn.

## So với bộ 56 ảnh cũ

| Chỉ số | Bộ 56 (checkpoint gốc) | Bộ 200 mới (checkpoint đang chạy) |
|---|---|---|
| IoU vùng khoanh trung bình: ++ / GC | 0,758 / 0,713 | 0,842 / 0,789 |
| Gap lưới + ROAD: ++ / GC | 0,278 / 0,345 | 0,405 / 0,451 |
| Average Drop nhân theo điểm: ++ / GC | 31,4% / 25,2% | 29,3% / 22,1% |
| MPRT bước 1, Spearman: ++ / GC | 0,897 / −0,334 | 0,945 / −0,573 |

Giá trị tuyệt đối khác vì **khác checkpoint** và khác bộ ảnh, nên không so trực tiếp từng con
số. Điều đáng chú ý là **chiều chênh lệch giữa hai phương pháp giữ nguyên ở mọi chỉ số**, nay
trên bộ lớn hơn và độc lập.

## Giới hạn

- PlantDoc chỉ có 61 ảnh (giới hạn bởi tập test chưa bị học); kết quả PlantDoc có khoảng tin
  cậy rộng hơn PlantVillage.
- Không có chỉ số định vị theo mặt nạ lá/vết bệnh trên bộ này.
- Mọi phép che/xoá có thể tạo ảnh ngoài phân phối; vì vậy báo cáo nhiều cách lấp cùng lúc.
- Không đo LIME/Kernel SHAP trên bộ 200 ảnh; so sánh với hai phương pháp đó vẫn chỉ có trên bộ 56.
- Chỉ đánh giá server PyTorch; bản ONNX ngoại tuyến dùng CAM cổ điển, không thuộc phạm vi này.

## Tái lập

Mã: `model/src/evaluation/eval_xai_200.py` (`sample`, `run`, `mprt`, `summarize`), kiểm thử
`model/tests/test_eval_xai_200.py`. Dữ liệu: `model/outputs/xai-eval-200/` — `samples.csv`,
`sampling.json`, `records/` (từng ảnh), `per-image.csv`, `summary.json`, `mprt/`, và
`run/protocol.json`, `mprt/protocol.json` (băm checkpoint, script, phiên bản thư viện).
