---
name: Báo lỗi
about: Lỗi phát hiện khi chạy thử
title: "[LỖI] "
labels: ["bug"]
assignees: []
---

## Môi trường

- **Thiết bị / trình duyệt:** <!-- Chrome 120 · Windows 11 · Samsung A54 Android 14 -->
- **Nhánh / commit:** <!-- main, commit a1b2c3d -->
- **Phần nào:** <!-- backend · mobile · web-admin · model -->
- **Đang chạy mô hình nào:** <!-- DummyPredictor hay mô hình thật? Xem `using_real_model` ở GET /health -->
- **Issue liên quan:** <!-- #26 -->

## Các bước tái hiện

1. 
2. 
3. 

## Kết quả mong đợi

<!-- Lẽ ra phải thế nào -->

## Kết quả thực tế

<!-- Thực tế xảy ra gì. Dán nguyên văn thông báo lỗi, đừng kể lại. -->

## Ảnh chụp màn hình

<!-- Kéo thả vào đây -->

## Mức độ

- [ ] 🔴 **Nặng** — chức năng chính hỏng, không có cách vòng qua
- [ ] 🟡 **Vừa** — hỏng nhưng còn cách vòng qua
- [ ] 🟢 **Nhẹ** — sai chính tả, lệch canh lề, chuyện hình thức

## Ghi chú thêm

<!--
Log console, log mạng, log uvicorn.

Nếu lỗi chỉ xảy ra trên PostgreSQL mà không xảy ra trên SQLite (hoặc ngược lại)
thì ghi rõ — bộ test chạy SQLite còn ứng dụng chạy PostgreSQL, đã có lỗi thật
lọt qua đúng khe hở này.
-->
