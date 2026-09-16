"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { adminFetch, ApiError } from "@/lib/api";
import type { UserOut } from "@/lib/types";

const BASE = "/admin/users";

function errorRedirect(message: string): never {
  redirect(`${BASE}?error=${encodeURIComponent(message)}`);
}

export async function createUserAction(formData: FormData) {
  const payload = {
    username: String(formData.get("username") ?? "").trim(),
    password: String(formData.get("password") ?? ""),
    full_name: String(formData.get("full_name") ?? "").trim(),
    email: String(formData.get("email") ?? "").trim() || null,
    phone: String(formData.get("phone") ?? "").trim() || null,
    role: String(formData.get("role") ?? "farmer"),
  };

  try {
    await adminFetch<UserOut>("/users", { method: "POST", body: payload });
  } catch (err) {
    errorRedirect(err instanceof ApiError ? err.message : "Không tạo được tài khoản");
  }

  revalidatePath(BASE);
  redirect(BASE);
}

export async function updateUserAction(userId: number, formData: FormData) {
  const payload = {
    full_name: String(formData.get("full_name") ?? "").trim(),
    email: String(formData.get("email") ?? "").trim() || null,
    phone: String(formData.get("phone") ?? "").trim() || null,
    role: String(formData.get("role") ?? "farmer"),
  };

  try {
    await adminFetch<UserOut>(`/users/${userId}`, { method: "PATCH", body: payload });
  } catch (err) {
    errorRedirect(err instanceof ApiError ? err.message : "Không cập nhật được tài khoản");
  }

  revalidatePath(BASE);
  redirect(BASE);
}

export async function toggleLockAction(userId: number, nextIsActive: boolean) {
  try {
    await adminFetch<UserOut>(`/users/${userId}`, {
      method: "PATCH",
      body: { is_active: nextIsActive },
    });
  } catch (err) {
    errorRedirect(err instanceof ApiError ? err.message : "Không đổi được trạng thái tài khoản");
  }

  revalidatePath(BASE);
  redirect(BASE);
}
