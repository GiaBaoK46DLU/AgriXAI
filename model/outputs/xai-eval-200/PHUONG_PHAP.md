# Đánh giá Grad-CAM++ trên bộ 200 ảnh mới

Mục tiêu: kiểm tra lại các kết luận về Grad-CAM++ trên một bộ ảnh lớn gấp ~3,6 lần bộ 56
ảnh cũ, **không dùng lại ảnh nào của bộ 56**, và trên **checkpoint đang triển khai**.
Grad-CAM gốc chạy song song làm mốc đối chứng.

## Bộ ảnh

- Nguồn: `outputs/domain-50-20261104-b8/test-inventory.json` — đúng tập ảnh checkpoint
  `leaf_disease_domain_adapted.pt` **chưa từng học** (2.719 PlantVillage test + 66 PlantDoc test).
- Loại: 35 ảnh của bộ 56 (#17/#122/#98, so cả đường dẫn lẫn SHA-256), 1 ảnh trùng nội dung
  trong chính tập test. Đối chiếu băm với training, rehearsal và bn-calibration inventory:
  không trùng ảnh nào.
- Thành phần: **61 ảnh PlantDoc** (toàn bộ phần còn lại của PlantDoc test, 8 lớp) +
  **139 ảnh PlantVillage** chia đều 10 lớp (13–14 ảnh/lớp, seed 20261128).
- Danh sách và băm: `samples.csv`; quy tắc chọn: `sampling.json`.

## Mô hình và tiền xử lý

- Checkpoint `checkpoints/leaf_disease_domain_adapted.pt`, Grad-CAM++ và Grad-CAM ở tầng
  `features[-1]`, giải thích lớp mô hình dự đoán trên ảnh gốc.
- Ảnh resize thẳng 224 × 224 (bilinear), không cắt lá — giống cấu hình đang triển khai.
- Bộ chặn lá `organ_gate.pt` được chạy để **ghi lại** ảnh nào hệ thống thật sẽ chặn
  (`gate_pass`); mọi ảnh vẫn được đánh giá, tập con `gate_pass` báo riêng.

## Chỉ số (định nghĩa lấy nguyên từ `src/evaluation/extend_xai_eval.py`)

| Nhóm | Chỉ số | Ghi chú |
|---|---|---|
| Độ lặp lại | sai lệch tuyệt đối lớn nhất khi tính lại cùng ảnh | phương pháp xác định → kỳ vọng 0 |
| Đồng thuận | Spearman, trùng top 20% giữa Grad-CAM++ và Grad-CAM | theo mảnh SLIC và lưới 14 × 14 |
| Độ trung thực | deletion/insertion AUC, gap = insertion − deletion | 2 đơn vị (SLIC, lưới) × 3 cách lấp (trung bình, làm mờ σ = 10, ROAD) |
| Average Drop | Drop, Increase, Win% (giữa 2 phương pháp) | biến thể nhân theo điểm và giữ top 15% |
| Độ bền | IoU vùng khoanh (ngưỡng 0,62), L2 tương đối, 1 − Spearman | 5 biến đổi kiểu chụp điện thoại; chỉ tính ảnh giữ nguyên nhãn |
| MPRT | Spearman, SSIM, tương quan HOG, % bản đồ rỗng | ngẫu nhiên hoá dần 10 khối (chế độ matched) |

**Không đo** các chỉ số cần mặt nạ lá/vết bệnh (khối lượng heatmap trong lá, mức nâng,
contour ngoài lá): bộ 200 ảnh chưa có mặt nạ tham chiếu.

Khoảng tin cậy 95%: bootstrap theo ảnh 10.000 lần. Chênh lệch ghép cặp:
**Grad-CAM++ − Grad-CAM** trên cùng ảnh. Tập con: all, pv, pd, correct, wrong, gate_pass.

## Chạy lại

Cần thêm `scikit-image` (xem `requirements-xai.txt`) bên cạnh môi trường `model/.venv`.

```bash
python -m src.evaluation.eval_xai_200 sample      # tạo samples.csv, sampling.json
python -m src.evaluation.eval_xai_200 run         # records/*.json, chạy tiếp được
python -m src.evaluation.eval_xai_200 mprt        # mprt/per-image.json
python -m src.evaluation.eval_xai_200 summarize   # per-image.csv, summary.json
```

`run/protocol.json` và `mprt/protocol.json` ghi băm checkpoint, script, thư viện và phiên bản gói.
