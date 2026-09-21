import "server-only";

import { getSessionToken } from "@/lib/session";

// Không có tiền tố NEXT_PUBLIC_ — biến này chỉ được đọc ở phía server, xem
// .env.example và lib/session.ts.
const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";
const API_PREFIX = "/api/v1";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

type FetchOptions = {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  searchParams?: Record<string, string | number | boolean | undefined | null>;
  token?: string;
};

function buildUrl(path: string, searchParams?: FetchOptions["searchParams"]): string {
  const url = new URL(`${API_PREFIX}${path}`, BACKEND_URL);
  if (searchParams) {
    for (const [key, value] of Object.entries(searchParams)) {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

/** Gọi thẳng backend, tự đính token nếu có. Ném `ApiError` khi backend trả lỗi,
 * kèm nguyên văn thông điệp tiếng Việt từ `detail` để hiển thị lại cho người dùng. */
export async function apiFetch<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const { method = "GET", body, searchParams, token } = options;

  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const response = await fetch(buildUrl(path, searchParams), {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    // Dữ liệu quản trị phải luôn mới — không để Next.js cache lại response.
    cache: "no-store",
  });

  if (!response.ok) {
    let message = `Yêu cầu thất bại (mã ${response.status})`;
    try {
      const data = await response.json();
      if (typeof data?.detail === "string") message = data.detail;
    } catch {
      // body không phải JSON — giữ nguyên thông điệp mặc định
    }
    throw new ApiError(response.status, message);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

/** Bản tiện dụng cho Server Component/Action: tự lấy token phiên hiện tại. */
export async function adminFetch<T>(
  path: string,
  options: Omit<FetchOptions, "token"> = {},
): Promise<T> {
  const token = await getSessionToken();
  return apiFetch<T>(path, { ...options, token: token ?? undefined });
}

/** Trước đây ghép thẳng `BACKEND_URL` vào trước đường dẫn để trình duyệt tải
 * ảnh trực tiếp từ backend — vỡ hoàn toàn khi chạy trong docker-compose vì
 * `BACKEND_URL=http://backend:8000` chỉ phân giải được TRONG mạng compose,
 * trình duyệt (chạy trên máy host) không gọi nổi tên "backend" (bug thật
 * 17/09/2026, ảnh trắng 100%). `next.config.mjs` giờ rewrite `/storage/...`
 * sang backend ngay ở tầng server Next.js, nên đường dẫn tương đối này đã là
 * URL dùng được thẳng — giữ hàm lại (không xoá, không inline) để mọi nơi gọi
 * ảnh vẫn đi qua một điểm chung, đổi cách ghép URL sau này không phải sửa lại
 * từng chỗ gọi. */
export function storageUrl(relativePath: string): string {
  return relativePath;
}

export { BACKEND_URL };

/** `/health` nằm ngoài tiền tố `/api/v1` và không cần token — public, rẻ (không
 * chạy truy vấn CSDL nào), nên đây là endpoint đúng để gọi trên MỌI trang admin
 * (không chỉ trang tổng quan) cho dải cảnh báo mô hình giả (#34). Dùng
 * `/stats/dashboard` cho việc này sẽ vừa cần token vừa nặng hơn nhiều lần. */
export async function getHealth(): Promise<{
  status: string;
  using_real_model: boolean;
  model_version: string;
}> {
  const response = await fetch(new URL("/health", BACKEND_URL), { cache: "no-store" });
  return response.json();
}
