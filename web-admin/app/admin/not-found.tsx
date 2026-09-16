import Link from "next/link";

import * as ui from "@/lib/ui";

export const metadata = { title: "Không tìm thấy — AgriXAI Admin" };

// Bắt cả hai trường hợp: route con /admin/* không tồn tại, VÀ notFound() gọi tay
// từ các trang chi tiết (ví dụ `?detail=` trỏ tới một id đã bị xoá/không có thật)
// — xem DiagnosisDetailModal.tsx, PostDetailModal.tsx.
export default function AdminNotFound() {
  return (
    <div className={`${ui.card} flex flex-col items-center gap-4 px-6 py-16 text-center`}>
      <div className="text-5xl font-extrabold tracking-[-0.02em] text-primary-dark">404</div>
      <p className="max-w-[360px] text-[14px] text-ink/65">
        Không tìm thấy nội dung này. Bản ghi có thể đã bị xoá, hoặc đường dẫn/tham số trên
        thanh địa chỉ không hợp lệ.
      </p>
      <Link href="/admin" className={ui.btnPrimary}>
        Về trang tổng quan
      </Link>
    </div>
  );
}
