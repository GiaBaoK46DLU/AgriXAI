"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { adminFetch, ApiError } from "@/lib/api";
import type { UserOut } from "@/lib/types";

const BASE = "/admin/account";

function errorRedirect(message: string): never {
  redirect(`${BASE}?error=${encodeURIComponent(message)}`);
}

export async function updateProfileAction(formData: FormData) {
  const payload = {
    full_name: String(formData.get("full_name") ?? "").trim(),
    phone: String(formData.get("phone") ?? "").trim() || null,
  };

  try {
    await adminFetch<UserOut>("/auth/me", { method: "PATCH", body: payload });
  } catch (err) {
    errorRedirect(err instanceof ApiError ? err.message : "Không cập nhật được hồ sơ");
  }

  revalidatePath(BASE);
  redirect(`${BASE}?saved=1`);
}

export async function changePasswordAction(formData: FormData) {
  const currentPassword = String(formData.get("current_password") ?? "");
  const newPassword = String(formData.get("new_password") ?? "");
  const confirmPassword = String(formData.get("confirm_password") ?? "");

  if (newPassword !== confirmPassword) {
    errorRedirect("Mật khẩu mới nhập lại không khớp");
  }

  try {
    await adminFetch<UserOut>("/auth/change-password", {
      method: "POST",
      body: { current_password: currentPassword, new_password: newPassword },
    });
  } catch (err) {
    errorRedirect(err instanceof ApiError ? err.message : "Không đổi được mật khẩu");
  }

  revalidatePath(BASE);
  redirect(`${BASE}?saved=1`);
}
