import { NextRequest, NextResponse } from "next/server";

// Middleware chạy ở edge, không có next/headers cookies() — dùng
// request.cookies. Chỉ kiểm tra SỰ TỒN TẠI của cookie, không giải mã JWT
// (không đáng để kéo thêm thư viện jwt vào edge runtime cho một lớp chặn
// tuyến đầu — token hết hạn/không hợp lệ vẫn bị mọi Server Component chặn
// lại ở lib/session.ts khi gọi backend, backend trả 401 sẽ được xử lý ở đó).
const COOKIE_NAME = "agrixai_admin_token";

export function middleware(request: NextRequest) {
  const hasToken = request.cookies.has(COOKIE_NAME);

  if (request.nextUrl.pathname.startsWith("/admin") && !hasToken) {
    const loginUrl = new URL("/login", request.url);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/admin/:path*"],
};
