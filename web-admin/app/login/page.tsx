import { redirect } from "next/navigation";

import { getSessionToken } from "@/lib/session";
import { Logo } from "@/components/Logo";

import { LoginForm } from "./LoginForm";

export const metadata = { title: "Đăng nhập — AgriXAI Admin" };

export default async function LoginPage() {
  const token = await getSessionToken();
  if (token) redirect("/admin");

  return (
    <div
      className="flex min-h-screen items-center justify-center p-6"
      style={{
        background:
          "linear-gradient(160deg, var(--color-bg-top), var(--color-bg-mid) 55%, var(--color-bg-bottom))",
      }}
    >
      <div
        className="w-full max-w-[400px] rounded-3xl border border-white/65 bg-white/55 p-9
                   shadow-[0_20px_60px_rgba(18,48,29,0.25)] backdrop-blur-2xl backdrop-saturate-200"
      >
        <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary shadow-[0_10px_22px_rgba(24,86,45,0.3)]">
          <Logo size={30} />
        </div>
        <h1 className="mb-1 text-2xl font-extrabold tracking-[-0.02em] text-ink">
          AgriXAI Admin
        </h1>
        <p className="mb-7 text-sm text-ink/70">
          Hệ thống chẩn đoán bệnh cây cà chua bằng AI
        </p>

        <LoginForm />

        <p className="mt-4 text-center text-xs text-ink/65">
          Chỉ dành cho quản trị viên hợp tác xã
        </p>
      </div>
    </div>
  );
}
