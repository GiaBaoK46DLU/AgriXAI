"use client";

import { useEffect } from "react";

import { Logo } from "@/components/Logo";
import * as ui from "@/lib/ui";

// error.tsx BẮT BUỘC là Client Component (quy ước Next.js) — đây là error
// boundary React thật, khác hẳn `middleware.ts` (chạy ở edge TRƯỚC khi route
// khớp, chỉ kiểm tra cookie đăng nhập, không thấy được lỗi ném ra lúc render).
// Boundary này chỉ bắt lỗi của segment NGOÀI /admin (vd. /login) và của chính
// `app/admin/layout.tsx` — lỗi bên trong các trang /admin/* đã có
// `app/admin/error.tsx` xử lý trước, giữ nguyên sidebar/header.
export default function RootError({
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
    <div className="flex min-h-screen flex-col items-center justify-center gap-5 bg-canvas px-6 text-center">
      <div
        className="flex h-14 w-14 items-center justify-center rounded-2xl"
        style={{ background: "linear-gradient(200deg, var(--color-primary), var(--color-primary-dark))" }}
      >
        <Logo size={28} />
      </div>
      <div>
        <div className="text-xl font-extrabold tracking-[-0.01em] text-ink">Có lỗi xảy ra</div>
        <p className="mt-2 max-w-[420px] text-[15px] text-ink/65">
          Trang gặp lỗi ngoài dự kiến. Thử lại — nếu vẫn còn lỗi, báo cho quản trị hệ thống kèm
          thời điểm xảy ra.
        </p>
      </div>
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
