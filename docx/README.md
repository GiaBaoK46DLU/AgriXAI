# `docx/` — Tài liệu đồ án

Nơi chứa toàn bộ tài liệu Word/PDF của đồ án. Không chứa code.

## Đang có

| File | Nội dung |
|---|---|
| `Hoc_Bao_DeCuongDeTai (1).docx` | **Đề cương nộp GVHD.** Tổng quan, mục tiêu, nội dung, công cụ, kế hoạch 11 mốc (12/08 – 30/11/2026), kết quả dự kiến, tài liệu tham khảo. Đây là bản cam kết chính thức với TS. Nguyễn Thị Lương. |
| `Phân tích đề tài nhóm 3 (1).docx` | **Phân tích nội bộ nhóm.** Phạm vi (cà chua, 10 lớp PlantVillage), phân chia vai trò Bảo/Học, các giai đoạn theo tuần, phân tích 5 nhóm chức năng, đề xuất giao diện kèm 2 ảnh wireframe (mobile 4 màn, web admin 4 trang). |

## Sẽ thêm về sau

- Báo cáo tiến độ lần 1 (25–30/09/2026)
- Báo cáo tiến độ lần 2 (16–18/11/2026)
- Báo cáo thuyết minh đồ án (bắt đầu viết từ 05/11/2026)
- Slide bảo vệ (25–30/11/2026)

## Lưu ý

**Tài liệu phân tích có một điểm đã lỗi thời.** Nó mô tả việc tích hợp liên nhóm qua mã vùng trồng PUC (chốt schema JSON với nhóm 1 và nhóm 2, dùng API Gateway chung, endpoint `POST /api/disease-reports`). Nhóm đã đổi hướng ngày 11/08/2026: **làm standalone trước**, tích hợp tính sau. Xem phần *Phạm vi* trong `README.md` ở thư mục gốc.

Trường `puc` vẫn được giữ trong cơ sở dữ liệu vì bản thân nó là thuộc tính của lô đất.

File `~$*.docx` (bản tạm Word tạo ra khi đang mở file) đã được `.gitignore` bỏ qua.
