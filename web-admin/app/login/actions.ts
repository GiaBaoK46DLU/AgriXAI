"use server";

import { redirect } from "next/navigation";

import { ApiError, apiFetch } from "@/lib/api";
import { setSessionCookie } from "@/lib/session";

export type LoginState = { error: string | null };

interface LoginResponse {
  access_token: string;
  expires_in: number;
  user: { role: string };
}

export async function loginAction(_prev: LoginState, formData: FormData): Promise<LoginState> {
  const username = String(formData.get("username") ?? "").trim();
  const password = String(formData.get("password") ?? "");

  if (!username || !password) {
    return { error: "Nhập đầy đủ tên đăng nhập và mật khẩu" };
  }

  let result: LoginResponse;
  try {
    result = await apiFetch<LoginResponse>("/auth/login", {
      method: "POST",
      body: { username, password },
    });
  } catch (err) {
    return { error: err instanceof ApiError ? err.message : "Không kết nối được tới máy chủ" };
  }

  if (result.user.role !== "admin") {
    return { error: "Tài khoản này không có quyền quản trị" };
  }

  await setSessionCookie(result.access_token, result.expires_in);
  redirect("/admin");
}
