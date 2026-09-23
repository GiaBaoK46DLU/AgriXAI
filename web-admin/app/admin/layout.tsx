import Link from "next/link";
import { redirect } from "next/navigation";

import { Sidebar } from "@/components/Sidebar";
import { DummyModelBanner } from "@/components/DummyModelBanner";
import { ApiError, apiFetch } from "@/lib/api";
import { requireToken } from "@/lib/session";
import type { UserOut } from "@/lib/types";

import { logoutAction } from "./actions";

export default async function AdminLayout({ children }: { children: React.ReactNode }) {
  const token = await requireToken();

  let me: UserOut;
  try {
    me = await apiFetch<UserOut>("/auth/me", { token });
  } catch (err) {
    // Token hết hạn hoặc tài khoản đã bị khoá kể từ lúc đăng nhập — xoá cookie
    // cũ rồi quay lại /login thay vì để trang trắng lỗi 401.
    if (err instanceof ApiError && (err.status === 401 || err.status === 403)) {
      // Không tự xoá cookie ở đây — layout đang render (không phải Server
      // Action/Route Handler), gọi cookies().delete() thẳng sẽ crash với lỗi
      // "Cookies can only be modified in a Server Action or Route Handler".
      // Chuyển việc xoá cookie sang Route Handler ở app/auth/clear-session.
      redirect("/auth/clear-session");
    }
    throw err;
  }

  if (me.role !== "admin") {
    redirect("/auth/clear-session");
  }

  return (
    <div className="flex min-h-screen bg-canvas text-ink">
      <Sidebar adminName={me.full_name} adminEmail={me.email ?? me.username} />
      <main className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 flex h-[64px] shrink-0 items-center justify-end gap-4 border-b border-border bg-surface px-7">
          <Link
            href="/admin/account"
            className="text-[13px] font-semibold text-ink/70 transition hover:text-primary-dark"
          >
            Tài khoản của tôi
          </Link>
          <span className="h-4 w-px bg-border" />
          <form action={logoutAction}>
            <button
              type="submit"
              className="text-[13px] font-semibold text-ink/70 transition hover:text-severe"
            >
              Đăng xuất
            </button>
          </form>
        </header>
        <DummyModelBanner />
        <div className="flex-1 p-7">{children}</div>
      </main>
    </div>
  );
}
