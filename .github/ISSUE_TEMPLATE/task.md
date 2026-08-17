---
name: Đầu việc
about: Một việc cụ thể — một chức năng, một endpoint, một màn hình
title: "XX-00: "
labels: []
assignees: []
---

<!--
Tiêu đề đặt theo mã nhóm việc:
  MD- mô hình · IN- tích hợp · FD- ảnh thực địa · BE- backend
  MB- mobile  · WA- web admin · OP- demo/hạ tầng · DC- báo cáo · FR- bệnh trên quả
Ví dụ: "BE-07: POST /api/v1/plots/{id}/archive"

Mỗi issue là MỘT việc. Nếu phải dùng chữ "và" trong tiêu đề thì
nhiều khả năng nên tách thành hai issue.
-->

## Mô tả

<!-- Làm gì, VÌ SAO cần, nối tiếp hoặc chặn issue nào. Hai ba câu là đủ. -->

## API backend

<!--
Với việc gọi API: ghi hợp đồng THẬT, không viết vo.
  - đường dẫn đầy đủ kèm tiền tố /api/v1
  - thân request mẫu
  - thân response mẫu
  - đủ các mã lỗi (401 / 403 / 404 / 413 / 422)
Mở http://localhost:8000/docs để đối chiếu.

Với việc mô hình hoặc dữ liệu: đổi mục này thành "## Đầu ra"
và ghi rõ file / số liệu nào phải xuất hiện sau khi xong.
-->

## Tiêu chí hoàn thành

<!--
Mỗi dòng phải KIỂM CHỨNG ĐƯỢC. Người khác đọc xong phải tự xác nhận
được là đúng hay sai, không cần hỏi lại.

  Tốt:  - [ ] Sai mật khẩu → hiện đúng câu `detail` của backend
  Kém:  - [ ] Xử lý lỗi cho tốt
-->

- [ ] 
- [ ] 
- [ ] 

## Gợi ý triển khai

<!-- Bẫy đã biết, pattern có sẵn để dùng lại, quyết định cần cân nhắc. Bỏ được nếu không có gì. -->

## Phụ thuộc

<!--
Ghi "Chặn bởi #N" và nói rõ chưa merge thì chưa bắt đầu được.
Không có thì ghi "Không có".
Nếu bị chặn, gắn thêm nhãn `trang-thai:bi-chan`.
-->

## Cách kiểm tra

<!-- Thao tác cụ thể, có cả ca lỗi. Tài khoản seed: admin/admin123 · nongdan/nongdan123 -->

1. 
2. 

## Nhánh

<!-- XX = SỐ CỦA ISSUE NÀY. Issue #42 → task-42 -->

`<bao|hoc>/task-XX-mo-ta-ngan`
