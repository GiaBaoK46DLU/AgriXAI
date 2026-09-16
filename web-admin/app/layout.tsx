import type { Metadata } from "next";
import { Open_Sans } from "next/font/google";

import "./globals.css";

const openSans = Open_Sans({
  subsets: ["latin", "vietnamese"],
  weight: ["400", "600", "700", "800"],
  variable: "--font-open-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AgriXAI Admin",
  description: "Quản trị nội dung hệ thống chẩn đoán bệnh cây cà chua AgriXAI",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" className={openSans.variable}>
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
