import { adminFetch } from "@/lib/api";
import * as ui from "@/lib/ui";
import type { UserOut } from "@/lib/types";

import { changePasswordAction, updateProfileAction } from "./actions";

export const metadata = { title: "Tài khoản của tôi — AgriXAI Admin" };

export default async function AccountPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string; saved?: string }>;
}) {
  const sp = await searchParams;
  const me = await adminFetch<UserOut>("/auth/me");

  return (
    <div className="max-w-[1100px]">
      <h1 className="mb-5 text-xl font-extrabold tracking-[-0.01em]">Tài khoản của tôi</h1>

      {sp.error && (
        <div className="mb-4 rounded-xl border border-severe/25 bg-severe-bg px-4 py-2.5 text-sm font-semibold text-severe">
          {sp.error}
        </div>
      )}
      {sp.saved === "1" && !sp.error && (
        <div className="mb-4 rounded-xl border border-primary/25 bg-primary/10 px-4 py-2.5 text-sm font-semibold text-primary-dark">
          Đã lưu thay đổi.
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 md:items-start">
      <div className={`${ui.card} p-6`}>
        <div className="mb-4 text-[15px] font-bold">Hồ sơ</div>
        <form action={updateProfileAction} className="grid gap-3">
          <div>
            <label className={ui.label}>Tên đăng nhập</label>
            <input value={me.username} disabled className={`${ui.input} bg-canvas text-ink/60`} />
          </div>
          <div>
            <label className={ui.label}>Email</label>
            <input
              value={me.email ?? "—"}
              disabled
              className={`${ui.input} bg-canvas text-ink/60`}
            />
            <p className="mt-1 text-xs text-ink/60">
              Email chưa đổi được qua trang này — cần Học bổ sung endpoint nếu cần.
            </p>
          </div>
          <div>
            <label className={ui.label}>Họ tên</label>
            <input name="full_name" defaultValue={me.full_name} required className={ui.input} />
          </div>
          <div>
            <label className={ui.label}>Số điện thoại</label>
            <input name="phone" defaultValue={me.phone ?? ""} className={ui.input} />
          </div>
          <div className="mt-1 flex justify-end">
            <button type="submit" className={ui.btnPrimary}>
              Lưu hồ sơ
            </button>
          </div>
        </form>
      </div>

      <div className={`${ui.card} p-6`}>
        <div className="mb-4 text-[15px] font-bold">Đổi mật khẩu</div>
        <form action={changePasswordAction} className="grid gap-3">
          <div>
            <label className={ui.label}>Mật khẩu hiện tại</label>
            <input
              name="current_password"
              type="password"
              required
              minLength={6}
              className={ui.input}
            />
          </div>
          <div>
            <label className={ui.label}>Mật khẩu mới</label>
            <input name="new_password" type="password" required minLength={6} className={ui.input} />
          </div>
          <div>
            <label className={ui.label}>Nhập lại mật khẩu mới</label>
            <input
              name="confirm_password"
              type="password"
              required
              minLength={6}
              className={ui.input}
            />
          </div>
          <div className="mt-1 flex justify-end">
            <button type="submit" className={ui.btnPrimary}>
              Đổi mật khẩu
            </button>
          </div>
        </form>
      </div>
      </div>
    </div>
  );
}
