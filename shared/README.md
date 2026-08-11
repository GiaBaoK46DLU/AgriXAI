# `shared/` — Dữ liệu dùng chung

Thứ mà **nhiều phần của hệ thống cùng đọc**, để không bị lệch nhau. Không chứa code chạy được.

## `data/tomato_diseases.json`

Danh mục 10 lớp bệnh cà chua — **nguồn sự thật duy nhất** cho cả `model/` lẫn `backend/`.

Mỗi bệnh có: `key`, tên Việt/Anh, tác nhân gây bệnh, tên thư mục PlantVillage tương ứng, triệu chứng, điều kiện phát sinh, gợi ý xử lý, biện pháp phòng ngừa, và `visual_cue` (mô tả dấu hiệu bằng lời — dùng để sinh câu giải thích XAI cho nông dân).

Ngoài ra có `severity_levels` — thang quy đổi tỉ lệ diện tích vùng nghi ngờ thành mức độ nhẹ/trung bình/nặng.

**Vì sao phải dùng chung một file:** thứ tự các lớp trong file này chính là thứ tự output của mô hình. Nếu backend và model đọc hai danh sách khác nhau, nhãn trả về sẽ sai hết mà không báo lỗi gì — loại lỗi rất khó phát hiện.

Ai đọc file này:
- `model/src/labels.py` → thứ tự lớp khi huấn luyện, ánh xạ tên thư mục PlantVillage
- `backend/app/services/catalog.py` → tên bệnh, gợi ý xử lý, thang mức độ

⚠️ **Đổi thứ tự các phần tử trong mảng `diseases` sau khi đã huấn luyện xong là hỏng mô hình.** Thêm bệnh mới thì thêm vào cuối và phải huấn luyện lại.

Trường `reference_url` hiện đang `null` ở tất cả các bệnh — chỗ để nhóm điền link tài liệu hoặc trang sản phẩm thuốc khi thu thập được.

## `api-contract/`

**Đang để trống — có chủ đích.**

Dành cho giai đoạn tích hợp với nhóm 1 (nhật ký canh tác) và nhóm 2 (bản đồ GIS): schema JSON trao đổi, quy ước mã PUC, tài liệu OpenAPI xuất ra cho nhóm khác.

Theo phạm vi đã chốt ngày 11/08/2026, phần này **hoãn lại**. Ưu tiên trước mắt là hệ thống chạy trơn tru một mình.
