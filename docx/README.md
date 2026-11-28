# `docx/` — Tài liệu đồ án

Nơi chứa toàn bộ tài liệu đồ án: bản Word nộp GVHD và các báo cáo/kế hoạch viết
bằng Markdown. **Không chứa code.**

> Ngày 15/09/2026, 6 file Markdown được chuyển từ thư mục gốc vào đây (quyết định
> của Bảo) để gốc repo chỉ còn `README.md` và `CLAUDE.md`. Hai file đó **phải ở
> gốc**: GitHub hiển thị `README.md` ngay trang đầu, còn `CLAUDE.md` là file
> Claude Code đọc mặc định ở thư mục gốc dự án.

## Bản Word nộp GVHD

| File | Nội dung |
|---|---|
| `Hoc_Bao_DeCuongDeTai (1).docx` | **Đề cương nộp GVHD.** Tổng quan, mục tiêu, nội dung, công cụ, kế hoạch 11 mốc (12/08 – 30/11/2026), kết quả dự kiến, tài liệu tham khảo. Đây là bản cam kết chính thức với TS. Nguyễn Thị Lương. |
| `Phân tích đề tài nhóm 3 (1).docx` | **Phân tích nội bộ nhóm.** Phạm vi (cà chua, 10 lớp PlantVillage), phân chia vai trò Bảo/Học, các giai đoạn theo tuần, phân tích 5 nhóm chức năng, đề xuất giao diện kèm 2 ảnh wireframe (mobile 4 màn, web admin 4 trang). |

## Báo cáo kỹ thuật (Markdown)

Ba báo cáo dưới đây là **nguồn số liệu cho chương thực nghiệm** của khoá luận. Mọi
con số trong đó do nhóm tự đo trên checkpoint đang chạy, không trích lại từ bài báo.

| File | Nội dung | Issue |
|---|---|---|
| `bao-cao-huan-luyen-mo-hinh.md` | Số liệu huấn luyện, chỉ số đánh giá, ma trận nhầm lẫn, phân tích lỗi, 30 thuật ngữ giải thích cho người không chuyên. **Test accuracy 99,60 %** | #14, #15 |
| `bao-cao-mo-hinh-grad-cam-xai.md` | Lý do chọn kiến trúc EfficientNet-B0, cơ sở lý thuyết XAI, Grad-CAM, đối chiếu 7 bài báo đã đọc kỹ | #14 |
| `bao-cao-domain-gap.md` | Mô hình chạy trên ảnh thật thì còn lại gì. **99,60 % → 30,81 %, tụt 68,79 điểm.** Kèm phân tích mô hình sụp về 3 lớp, bảng ngưỡng tin cậy, Grad-CAM trên nền phức tạp, và mục *Hạn chế* | #49 |

## So sánh phương pháp XAI

[Báo cáo so sánh Grad-CAM, LIME và SHAP](bao-cao-so-sanh-gradcam-lime-shap.docx)
trình bày nguyên lý, kết quả chạy trên cùng checkpoint và căn cứ lựa chọn cho
AgriXAI (issue #122). SHAP trong thực nghiệm là Kernel SHAP. Dữ liệu, hình đầu ra
và [cách chạy lại](../model/outputs/xai-comparison-122/PHUONG_PHAP.md) nằm trong
`model/outputs/xai-comparison-122/`.

[Đánh giá XAI mở rộng](bao-cao-danh-gia-xai-mo-rong.md) đo thêm năm nhóm chỉ số trên cùng
56 ảnh: đồng thuận giữa phương pháp, sanity check MPRT, Average Drop, deletion/insertion
với cách lấp ROAD/làm mờ, và độ bền khi chụp lại. Dữ liệu và
[cách chạy lại](../model/outputs/xai-evaluation-ext/PHUONG_PHAP.md) nằm trong
`model/outputs/xai-evaluation-ext/`.

[Đánh giá Grad-CAM++ trên bộ 200 ảnh mới](bao-cao-danh-gia-gradcam-plus-plus-200-anh.md)
kiểm tra lại Grad-CAM++ (đối chứng Grad-CAM) trên 200 ảnh không trùng bộ 56, bằng checkpoint
đang triển khai. [Bản Word ngắn có hình và bảng](GradCAM-200-anh.docx). Dữ liệu và [cách chạy lại](../model/outputs/xai-eval-200/PHUONG_PHAP.md) nằm
trong `model/outputs/xai-eval-200/`.

[Vùng lá và vết bệnh trên bộ 200 ảnh có mặt nạ](GradCAM-200-anh-mat-na.docx) (bản Word)
bổ sung phần báo cáo trên còn thiếu: khoanh mù mặt nạ lá/vết bệnh cho cả 200 ảnh rồi đo các
chỉ số vùng của #98 cho Grad-CAM++ và Grad-CAM. Mã chạy lại:
`python -m src.evaluation.lesion_eval_200 {sheets,run,summarize,figures}`; mặt nạ ở
`model/outputs/xai-eval-200/annotation/khoanh-tay.json`, kết quả ở `.../lesion/`.

## Kế hoạch và rà soát

[Cắt lá, chốt hiển thị XAI và cải thiện domain gap (#93/#90/#50)](bao-cao-cat-la-domain-adaptation.md):
so sánh từng hướng trên cùng tập test sạch, số CPU/GPU, ảnh kiểm tra toạ độ,
quy tắc ẩn heatmap và kiểm tra API bằng checkpoint thật. Các file số liệu nằm
trong `model/outputs/domain-50-20261104-b8/`.

[Báo cáo ngắn nâng cấp Grad-CAM++ (#98)](bao-cao-nang-cap-gradcam-plus-plus.docx):
nguyên lý, bảng so sánh định lượng, hình có chú thích và quyết định bật mặc định.
[Thực nghiệm đầy đủ](bao-cao-gradcam-plus-plus.md) lưu chi tiết công thức, đối chứng
thư viện và 56 ảnh so sánh heatmap/contour, gồm cả các chỉ số chưa cải thiện.

| File | Nội dung |
|---|---|
| `Plan_model.md` | Rà soát 4 vấn đề phát hiện khi thử app với mô hình thật (10/09/2026) + kế hoạch xử lý **gắn theo issue GitHub**. Chứa mục 5.2 — căn cứ loại bộ dữ liệu H1 |
| `bao-cao-tien-do-lan-1.md` | Báo cáo tiến độ lần 1 |
| `phan-tich-tinh-trang-va-huong-di.md` | Phân tích tình trạng và hướng đi |

⚠️ **Mấy file này KHÔNG phải bảng công việc.** Nguồn duy nhất để biết còn phải làm gì
vẫn là **issue GitHub** — xem mục *Issue GitHub* trong `CLAUDE.md`. Đừng lập danh sách
việc song song ở đây.

## Cách tham chiếu từ chỗ khác

Sau lần chuyển 15/09/2026, tài liệu nằm **ngoài** `docx/` (như `CLAUDE.md` hay
`model/research/*.md`) phải ghi đủ đường dẫn `docx/<tên file>.md`. Các file **trong**
`docx/` trỏ cho nhau thì dùng tên trần vì cùng thư mục.

## Sẽ thêm về sau

- Báo cáo tiến độ lần 2 (16–18/11/2026)
- Báo cáo thuyết minh đồ án (bắt đầu viết từ 05/11/2026)
- Slide bảo vệ (25–30/11/2026)
- Bản tóm tắt tiến độ huấn luyện mô hình 3–4 trang nộp GVHD (issue **#95**)

## Lưu ý

**Tài liệu phân tích có một điểm đã lỗi thời.** Nó mô tả việc tích hợp liên nhóm qua mã vùng trồng PUC (chốt schema JSON với nhóm 1 và nhóm 2, dùng API Gateway chung, endpoint `POST /api/disease-reports`). Nhóm đã đổi hướng ngày 11/08/2026: **làm standalone trước**, tích hợp tính sau. Xem phần *Phạm vi* trong `README.md` ở thư mục gốc.

Trường `puc` vẫn được giữ trong cơ sở dữ liệu vì bản thân nó là thuộc tính của lô đất.

File `~$*.docx` (bản tạm Word tạo ra khi đang mở file) đã được `.gitignore` bỏ qua.
