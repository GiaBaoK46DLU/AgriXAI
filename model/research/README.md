# `model/research/` — Thư mục đọc bài báo

Chỗ gom tài liệu khoa học phục vụ **chương tổng quan** và **phần so sánh mô hình**
của báo cáo. Không chứa code, không chứa dữ liệu.

## Có gì trong này

| File | Dùng để làm gì |
|---|---|
| `00-danh-muc-bai-bao.md` | **File chính.** Danh sách bài báo đã lọc, chia theo 8 nhóm chủ đề, kèm link và lý do nên đọc |
| `01-ke-hoach-thi-nghiem.md` | Từ bài báo → thí nghiệm cụ thể chạy được trên máy Bảo, và bảng so sánh để điền dần |
| `02-cau-hoi-phan-bien.md` | Câu hỏi hội đồng hay hỏi ↔ bài báo trả lời được câu đó |
| `notes/` | Ghi chú từng bài đã đọc, một file một bài |

## Cách làm việc

1. Mở `00-danh-muc-bai-bao.md`, chọn bài theo thứ tự ưu tiên ghi ở đầu file.
2. Đọc xong thì copy `notes/_mau-ghi-chu.md` thành `notes/<ma-bai>-<ten-ngan>.md`
   rồi điền vào. Ví dụ: `notes/A2-plantvillage-bias.md`.
3. Đánh dấu ✅ vào cột trạng thái trong danh mục.
4. Báo Claude mã bài (A2, D1, …) để cùng mổ xẻ và bàn xem áp dụng được gì.

## ⚠️ Về số liệu ghi trong danh mục

Con số accuracy trong bảng lấy từ **abstract hoặc tóm tắt kết quả tìm kiếm**, chỉ để
biết bài đó có đáng đọc hay không. **Trước khi trích vào báo cáo phải mở toàn văn
kiểm lại** — abstract hay làm tròn và hay bỏ mất điều kiện đo (số lớp, cách chia tập,
có augment hay không).

Cột "Trạng thái" phân biệt hai mức:

- ✅ — đã mở toàn văn, số liệu ghi ở đây đúng với bài
- ⚪ — mới lấy từ kết quả tìm kiếm, **chưa mở**, coi như tin đồn cho tới khi đọc

## Liên quan tới issue nào

Tài liệu ở đây phục vụ **#14 (huấn luyện đầy đủ)**, **#15 (phân tích lỗi và mất cân
bằng lớp)** và các issue tiền tố `DC-` (báo cáo). Thư mục này **không phải bảng công
việc** — nguồn duy nhất để biết còn phải làm gì vẫn là 76 issue trên GitHub. Nếu đọc
xong thấy cần chạy thêm thí nghiệm thì **mở issue mới**, đừng ghi thành danh sách
việc ở đây.
