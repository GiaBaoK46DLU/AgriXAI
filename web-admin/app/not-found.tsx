import Link from "next/link";

import { Logo } from "@/components/Logo";
import * as ui from "@/lib/ui";

export const metadata = { title: "Không tìm thấy trang — AgriXAI Admin" };

export default function RootNotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-5 bg-canvas px-6 text-center">
      <div
        className="flex h-14 w-14 items-center justify-center rounded-2xl"
        style={{ background: "linear-gradient(200deg, var(--color-primary), var(--color-primary-dark))" }}
      >
        <Logo size={28} />
      </div>
      <div>
        <div className="text-5xl font-extrabold tracking-[-0.02em] text-primary-dark">404</div>
        <p className="mt-2 text-[15px] text-ink/65">
          Không tìm thấy trang này. Đường dẫn có thể đã bị gõ sai hoặc không còn tồn tại.
        </p>
      </div>
      <Link href="/admin" className={ui.btnPrimary}>
        Về trang tổng quan
      </Link>
    </div>
  );
}
