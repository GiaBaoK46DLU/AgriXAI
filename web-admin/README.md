# `web-admin/` — Dashboard quản trị (React + Vite)

**Chưa bắt đầu.** Mới chỉ dựng khung thư mục. Theo đề cương, phần frontend làm từ **01/10/2026**.

## Vai trò

Khác hẳn app di động: giao diện này **không dành cho nông dân**, mà cho cán bộ kỹ thuật, người quản lý hợp tác xã, hoặc chính nhóm phát triển khi cần theo dõi hệ thống.

Vì đối tượng khác nên mục tiêu thiết kế cũng khác: thay vì tối giản như mobile, web cần **hiển thị nhiều thông tin tổng hợp cùng lúc**, theo dõi trên diện rộng (nhiều lô đất, nhiều nông dân), kèm các thao tác quản lý mà nông dân không cần dùng tới.

## Bốn trang (theo wireframe trong `docx/`)

| # | Trang | Nội dung | API dùng |
|---|---|---|---|
| 1 | **Tổng quan** | 4 ô số liệu (lô đất, nông dân, lượt chẩn đoán, cảnh báo) + biểu đồ ca bệnh theo thời gian + bảng cảnh báo gần đây | `GET /api/v1/stats/dashboard` |
| 2 | **Lô đất & nông dân** | Bảng: Mã PUC, Nông dân, Khu vực, Diện tích, Trạng thái. Có tìm kiếm, lọc | `GET/POST/PATCH /api/v1/plots` |
| 3 | **Lịch sử toàn hệ thống** | Bảng mọi kết quả chẩn đoán, lọc theo lô đất / nông dân / thời gian / mức độ | `GET /api/v1/diagnoses` |
| 4 | **Tài khoản & phân quyền** | Danh sách tài khoản, thêm, khoá, đổi vai trò | `GET/POST/PATCH /api/v1/users` |

Trang 4 được tài liệu phân tích đánh dấu là **tuỳ chọn** — làm nếu còn thời gian. Backend đã có sẵn API nên phần việc còn lại chỉ là giao diện.

## Cấu trúc thư mục đã dựng

```
web-admin/
├── public/
└── src/
    ├── api/          gọi backend, gắn token vào header
    ├── components/   thành phần dùng lại (bảng, ô số liệu, bộ lọc)
    ├── hooks/
    ├── layouts/      khung có sidebar + header
    ├── pages/        dashboard · plots · history · accounts
    ├── styles/
    └── utils/
```

## Khi bắt đầu làm

Thư mục đã có sẵn nội dung nên `npm create vite@latest .` sẽ báo *"Directory not empty"* và đòi xoá hết. Cách vòng qua:

```bash
cd web-admin
npm create vite@latest temp -- --template react
# copy nội dung trong temp/ ra ngoài, giữ lại src/ đã có, rồi xoá temp/
npm install
npm run dev          # http://localhost:5173
```

Gói dự kiến cần: `axios`, `react-router-dom`, và một thư viện biểu đồ (`recharts` là lựa chọn nhẹ nhàng nhất cho biểu đồ cột đơn giản trong wireframe).

## Lưu ý

**CORS đã được cấu hình sẵn** cho `http://localhost:5173` trong `backend/.env.example`. Nếu Vite chạy ở cổng khác, phải thêm địa chỉ đó vào `CORS_ORIGINS` rồi khởi động lại backend.

**Toàn bộ số liệu trang tổng quan lấy trong một request duy nhất** (`/stats/dashboard`) — cố ý gộp để trang không phải chờ nhiều lượt mạng mới vẽ xong.

**Dashboard trả về `using_real_model`.** Nên hiển thị một dải cảnh báo rõ ràng khi giá trị này là `false`, để không ai nhầm số liệu do mô hình giả sinh ra là số liệu thật.
