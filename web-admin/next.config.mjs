/** @type {import('next').NextConfig} */
const nextConfig = {
  // Ảnh chẩn đoán được backend phục vụ tại BACKEND_URL/storage/... — cho phép
  // next/image tải từ đó thay vì chỉ domain của chính web-admin.
  images: {
    remotePatterns: [
      { protocol: "http", hostname: "**" },
      { protocol: "https", hostname: "**" },
    ],
  },
};

export default nextConfig;
