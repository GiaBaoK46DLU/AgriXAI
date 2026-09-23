import { NextResponse } from "next/server";

import { clearSessionCookie } from "@/lib/session";

// Route Handler — không phải Server Component render. `cookies().delete()` chỉ
// hợp lệ ở đây hoặc trong Server Action (xem lib/session.ts), KHÔNG hợp lệ khi
// gọi trong lúc render app/admin/layout.tsx (đó chính là lỗi "Cookies can only
// be modified in a Server Action or Route Handler" — layout giờ redirect tới
// route này thay vì tự xoá cookie).
export async function GET(request: Request) {
  await clearSessionCookie();
  return NextResponse.redirect(new URL("/login", request.url));
}
