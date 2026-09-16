import "server-only";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

// Kiến trúc BFF: token JWT do backend FastAPI cấp được cất trong cookie
// httpOnly, KHÔNG bao giờ chuyển xuống JavaScript phía trình duyệt. Mọi lệnh
// gọi backend chạy trong Server Component / Server Action / Route Handler —
// xem lib/api.ts. Đây là lựa chọn thay vì lưu token trong localStorage (cách
// app mobile làm) vì web-admin chạy trên trình duyệt, nơi localStorage lộ ra
// cho bất kỳ đoạn JS nào (kể cả từ một lỗ hổng XSS), còn cookie httpOnly thì
// không.
const COOKIE_NAME = "agrixai_admin_token";

export async function setSessionCookie(token: string, maxAgeSeconds: number) {
  const store = await cookies();
  store.set(COOKIE_NAME, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: maxAgeSeconds,
  });
}

export async function clearSessionCookie() {
  const store = await cookies();
  store.delete(COOKIE_NAME);
}

export async function getSessionToken(): Promise<string | null> {
  const store = await cookies();
  return store.get(COOKIE_NAME)?.value ?? null;
}

/** Dùng trong Server Component/Action cần chắc chắn có token — tự chuyển
 * hướng về /login nếu chưa đăng nhập, để mỗi trang không phải tự kiểm tra. */
export async function requireToken(): Promise<string> {
  const token = await getSessionToken();
  if (!token) {
    redirect("/login");
  }
  return token;
}
