"use client";

import { useEffect } from "react";

import * as ui from "@/lib/ui";

// Bắt lỗi ném ra từ bất kỳ trang nào trong /admin/* (dashboard, danh sách,
// modal chi tiết...) — KHÔNG bắt lỗi của chính `app/admin/layout.tsx` (lỗi ở
// đó rơi lên `app/error.tsx` gốc, theo đúng quy tắc error boundary của
// Next.js: một segment không tự bắt lỗi của layout bao nó). Vì layout.tsx đã
// render xong trước khi page bên trong lỗi, sidebar/header vẫn hiển thị bình
// thường quanh khối lỗi này — người dùng không bị "văng" hẳn ra khỏi giao diện
// quản trị như một trang trắng 500 kiểu cũ.
export default function AdminError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className={`${ui.card} flex flex-col items-center gap-4 px-6 py-16 text-center`}>
      <div className="text-xl font-extrabold tracking-[-0.01em] text-ink">Có lỗi xảy ra</div>
      <p className="max-w-[420px] text-[14px] text-ink/65">
        Trang này gặp lỗi ngoài dự kiến khi tải dữ liệu. Thử lại — nếu vẫn còn lỗi, báo cho
        Học/Bảo kèm thời điểm xảy ra để tra log backend.
      </p>
      <div className="flex gap-2.5">
        <button type="button" onClick={reset} className={ui.btnPrimary}>
          Thử lại
        </button>
        <a href="/admin" className={ui.btnGhost}>
          Về trang tổng quan
        </a>
      </div>
    </div>
  );
}
