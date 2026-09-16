import Link from "next/link";

import { adminFetch } from "@/lib/api";
import * as ui from "@/lib/ui";
import { Tag, roleTone, statusTone } from "@/components/Tag";
import { ConfirmSubmitButton } from "@/components/ConfirmSubmitButton";
import type { UserOut } from "@/lib/types";

import { toggleLockAction } from "./actions";
import { UserFormModal } from "./UserFormModal";

export const metadata = { title: "Người dùng — AgriXAI Admin" };

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("vi-VN");
}

export default async function UsersPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; role?: string; new?: string; edit?: string; error?: string }>;
}) {
  const sp = await searchParams;
  const q = sp.q ?? "";
  const role = sp.role ?? "all";

  const users = await adminFetch<UserOut[]>("/users", {
    searchParams: { q: q || undefined, role: role === "all" ? undefined : role },
  });

  const editingUser = sp.edit ? users.find((u) => u.id === Number(sp.edit)) : undefined;

  return (
    <div>
      <h1 className="mb-5 text-xl font-extrabold tracking-[-0.01em]">Người dùng</h1>

      {sp.error && (
        <div className="mb-4 rounded-xl border border-severe/25 bg-severe-bg px-4 py-2.5 text-sm font-semibold text-severe">
          {sp.error}
        </div>
      )}

      <form className="mb-[18px] flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2.5">
          <input
            name="q"
            defaultValue={q}
            placeholder="Tìm theo tên hoặc tên đăng nhập..."
            className={`${ui.input} w-[260px]`}
          />
          <select name="role" defaultValue={role} className={`${ui.select} w-auto`}>
            <option value="all">Tất cả vai trò</option>
            <option value="admin">Admin</option>
            <option value="farmer">Farmer</option>
          </select>
          <button type="submit" className={ui.btnGhost}>
            Lọc
          </button>
        </div>
        <Link href="/admin/users?new=1" className={ui.btnPrimary}>
          + Thêm người dùng
        </Link>
      </form>

      <div className={ui.card}>
        <table className="w-full border-collapse text-[13px]">
          <thead>
            <tr className="bg-canvas">
              <th className={ui.th}>Tên đăng nhập</th>
              <th className={ui.th}>Họ tên</th>
              <th className={ui.th}>Email</th>
              <th className={ui.th}>SĐT</th>
              <th className={ui.th}>Vai trò</th>
              <th className={ui.th}>Trạng thái</th>
              <th className={ui.th}>Ngày tạo</th>
              <th className={ui.th}></th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className={ui.tr}>
                <td className={`${ui.td} font-semibold`}>{u.username}</td>
                <td className={ui.td}>{u.full_name}</td>
                <td className={ui.td}>{u.email ?? "—"}</td>
                <td className={ui.td}>{u.phone ?? "—"}</td>
                <td className={ui.td}>
                  <Tag tone={roleTone(u.role)}>{u.role === "admin" ? "Admin" : "Farmer"}</Tag>
                </td>
                <td className={ui.td}>
                  <Tag tone={statusTone(u.is_active)}>{u.is_active ? "Hoạt động" : "Khoá"}</Tag>
                </td>
                <td className={`${ui.td} text-ink/70`}>{formatDate(u.created_at)}</td>
                <td className={`${ui.td} whitespace-nowrap text-right`}>
                  <Link
                    href={`/admin/users?edit=${u.id}`}
                    className="mr-1 rounded-lg p-1.5 text-ink/60 hover:bg-ink/8"
                    aria-label="Sửa"
                  >
                    ✎
                  </Link>
                  <form action={toggleLockAction.bind(null, u.id, !u.is_active)} className="inline">
                    <ConfirmSubmitButton
                      confirmMessage={
                        u.is_active
                          ? `Khoá tài khoản "${u.username}"?`
                          : `Mở khoá tài khoản "${u.username}"?`
                      }
                      className="rounded-lg p-1.5 text-xs font-bold text-severe hover:bg-severe-bg"
                    >
                      {u.is_active ? "Khoá" : "Mở khoá"}
                    </ConfirmSubmitButton>
                  </form>
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-ink/60">
                  Không có tài khoản nào khớp bộ lọc
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {sp.new === "1" && <UserFormModal />}
      {editingUser && <UserFormModal user={editingUser} />}
    </div>
  );
}
