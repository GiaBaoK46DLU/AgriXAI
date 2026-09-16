/** @type {import('next').NextConfig} */
const nextConfig = {
  // Ảnh chẩn đoán hiện lên bằng <img src={storageUrl(...)}> chạy TRONG TRÌNH
  // DUYỆT — storageUrl() trước đây ghép thẳng BACKEND_URL (biến chỉ dùng phía
  // server, xem lib/session.ts) vào src, nên chạy ngoài Docker (BACKEND_URL=
  // http://localhost:8000, trình duyệt gọi được) thì vẫn thấy ảnh, nhưng chạy
  // trong docker-compose (BACKEND_URL=http://backend:8000 — tên service chỉ
  // phân giải được TRONG mạng compose) thì trình duyệt không gọi nổi, ảnh vỡ
  // trắng toàn bộ 100% (bug thật phát hiện 17/09/2026). Rewrite này khiến
  // /storage/... vẫn là same-origin với chính trang web-admin ở mọi nơi truy
  // cập (localhost:3000, IP LAN, sau này có domain thật) — Next.js server tự
  // proxy sang backend, trình duyệt không cần biết BACKEND_URL là gì.
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";
    return [{ source: "/storage/:path*", destination: `${backendUrl}/storage/:path*` }];
  },
};

export default nextConfig;
