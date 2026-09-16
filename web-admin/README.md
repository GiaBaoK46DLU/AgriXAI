# `web-admin/` — Dashboard quản trị (Next.js)

Giao diện quản lý nội dung hệ thống AgriXAI cho cán bộ kỹ thuật/quản lý hợp
tác xã — khác hẳn app di động (dành cho nông dân). Xây bằng **Next.js (App
Router) + TypeScript + Tailwind CSS v4**, dự định deploy lên **Vercel**.

> Bản trước của thư mục này là khung Vite/React trống theo kế hoạch 4 trang.
> Ngày 16/09/2026 đổi hẳn sang Next.js và mở rộng thành 8 module — xem mục
> "Web admin: kiến trúc và tiến độ" trong `CLAUDE.md` ở thư mục gốc để biết
> đầy đủ lý do và các quyết định không suy ra được từ code.

## Kiến trúc: BFF, không gọi thẳng backend từ trình duyệt

`backend/` (FastAPI), `web-admin/`, `mobile/` vẫn là ba phần triển khai độc
lập. Next.js chỉ đóng vai trò **backend-for-frontend** cho riêng web admin:

- Mọi lệnh gọi `backend/` chạy ở **phía server** của Next.js — Server
  Component (đọc dữ liệu), Server Action (ghi dữ liệu). Trình duyệt không
  bao giờ gọi thẳng backend hay thấy token đăng nhập.
- Token JWT backend cấp được cất trong cookie **httpOnly** (`lib/session.ts`),
  không phải `localStorage` — tránh lộ token qua một lỗ hổng XSS bất kỳ.
- `middleware.ts` chặn truy cập `/admin/*` ở tầng edge nếu chưa có cookie
  phiên; từng trang trong `/admin` tự gọi `/auth/me` để xác nhận vai trò
  `admin` còn hợp lệ (tài khoản có thể đã bị khoá sau khi đăng nhập).

## Cấu trúc thư mục

```
web-admin/
├── app/
│   ├── login/              màn đăng nhập (Server Action gọi POST /auth/login)
│   └── admin/
│       ├── layout.tsx      sidebar + topbar, xác thực phiên
│       ├── page.tsx        Tổng quan
│       ├── users/          Người dùng (CRUD)
│       ├── plots/          Lô đất (chỉ xem)
│       ├── diagnoses/      Lịch sử chẩn đoán
│       ├── diseases/       Danh mục bệnh (chỉ xem, khoá thứ tự)
│       ├── medicines/      Thuốc gợi ý (CRUD + gán theo bệnh)
│       ├── guides/         Video hướng dẫn theo bệnh
│       └── forum/          Diễn đàn — kiểm duyệt bài viết/bình luận
├── components/             Sidebar, Modal, Tag, StatCard, Pagination...
├── lib/
│   ├── api.ts              gọi backend phía server (adminFetch/apiFetch)
│   ├── session.ts          đọc/ghi cookie phiên httpOnly
│   ├── types.ts             kiểu TypeScript khớp schema Pydantic
│   ├── ui.ts                chuỗi class Tailwind dùng lặp lại
│   └── chart.ts, youtube.ts  tiện ích nhỏ (sparkline SVG, nhúng YouTube)
└── middleware.ts           chặn /admin/* khi chưa đăng nhập
```

Mỗi trang danh sách theo cùng một khuôn: Server Component đọc `searchParams`
(bộ lọc, trang, id đang xem/sửa) → gọi `adminFetch` lấy dữ liệu → render bảng.
Modal thêm/sửa/xem chi tiết là **server-render được**: trạng thái mở/đóng nằm
ở URL (`?new=1`, `?edit=5`, `?detail=9`), không phải state phía client — nút
đóng chỉ là một `<Link>` quay lại URL không có tham số đó. Form ghi dữ liệu
gọi thẳng Server Action trong `actions.ts` của từng module.

## Thiết lập trên máy mới

```bash
cd web-admin
npm install
cp .env.example .env.local     # rồi chỉnh BACKEND_URL nếu backend không chạy ở localhost:8000
npm run dev                    # http://localhost:3000
```

Cần backend đang chạy (xem `backend/README.md`) — mặc định
`BACKEND_URL=http://localhost:8000`. **Không cần thêm origin của web-admin
vào `CORS_ORIGINS` của backend** vì mọi lệnh gọi đều xuất phát từ server
Next.js, không phải trình duyệt — khác với bản Vite cũ.

Đăng nhập bằng một tài khoản vai trò `admin` đã seed sẵn (xem
`backend/app/seed.py`, ví dụ `admin` / `admin123` trên dữ liệu mẫu).

## Deploy lên Vercel

Đặt biến môi trường `BACKEND_URL` trỏ tới địa chỉ backend đã triển khai (ví
dụ một máy chủ FastAPI public, hoặc tunnel khi demo). Không cần biến nào có
tiền tố `NEXT_PUBLIC_` — kiến trúc BFF cố tình giữ mọi thứ ở phía server.

## Lưu ý

- **`GET /diseases`** trả `using_real_model`/thứ tự lớp cố định — trang Danh
  mục bệnh cố tình **không có** nút sửa/xoá, đúng bất biến "thứ tự lớp = thứ
  tự output mô hình" ghi trong `CLAUDE.md`.
- **Trang Lô đất chỉ xem, không CRUD** — lô đất là dữ liệu của nông dân, admin
  chỉ cần theo dõi (đúng theo bản thiết kế tham khảo ban đầu).
- **Diễn đàn là module mới**, không có trong bản thiết kế `.dc.html` tham
  khảo ban đầu — tự thiết kế theo đúng phong cách các module còn lại.
