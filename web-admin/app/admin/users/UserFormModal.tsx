import { Modal } from "@/components/Modal";
import * as ui from "@/lib/ui";
import type { UserOut } from "@/lib/types";

import { createUserAction, updateUserAction } from "./actions";

export function UserFormModal({ user }: { user?: UserOut }) {
  const isEdit = Boolean(user);
  const action = isEdit ? updateUserAction.bind(null, user!.id) : createUserAction;

  return (
    <Modal title={isEdit ? "Sửa tài khoản" : "Thêm người dùng"} closeHref="/admin/users">
      <form action={action} className="grid gap-3">
        {!isEdit && (
          <>
            <div>
              <label className={ui.label}>Tên đăng nhập</label>
              <input name="username" required minLength={3} className={ui.input} />
            </div>
            <div>
              <label className={ui.label}>Mật khẩu</label>
              <input name="password" type="password" required minLength={6} className={ui.input} />
            </div>
          </>
        )}
        <div>
          <label className={ui.label}>Họ tên</label>
          <input name="full_name" defaultValue={user?.full_name} required className={ui.input} />
        </div>
        <div>
          <label className={ui.label}>Email</label>
          <input name="email" type="email" defaultValue={user?.email ?? ""} className={ui.input} />
        </div>
        <div>
          <label className={ui.label}>Số điện thoại</label>
          <input name="phone" defaultValue={user?.phone ?? ""} className={ui.input} />
        </div>
        <div>
          <label className={ui.label}>Vai trò</label>
          <div className="flex gap-2">
            {(["admin", "farmer"] as const).map((r) => (
              <label
                key={r}
                className="flex items-center gap-1.5 rounded-[10px] border border-border px-3 py-2 text-[13px]"
              >
                <input
                  type="radio"
                  name="role"
                  value={r}
                  defaultChecked={(user?.role ?? "farmer") === r}
                />
                {r === "admin" ? "Admin" : "Farmer"}
              </label>
            ))}
          </div>
        </div>

        <div className="mt-2 flex justify-end gap-2.5">
          <a href="/admin/users" className={ui.btnGhost}>
            Huỷ
          </a>
          <button type="submit" className={ui.btnPrimary}>
            Lưu
          </button>
        </div>
      </form>
    </Modal>
  );
}
