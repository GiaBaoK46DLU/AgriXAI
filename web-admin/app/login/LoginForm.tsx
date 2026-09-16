"use client";

import { useActionState } from "react";
import { useFormStatus } from "react-dom";

import { loginAction, type LoginState } from "./actions";

const initialState: LoginState = { error: null };

function SubmitButton() {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className="mt-2 w-full rounded-full bg-primary py-3.5 text-[15px] font-bold text-white
                 shadow-[0_14px_30px_rgba(24,86,45,0.5)] transition hover:bg-primary-dark
                 disabled:cursor-not-allowed disabled:opacity-70"
    >
      {pending ? "Đang đăng nhập…" : "Đăng nhập"}
    </button>
  );
}

export function LoginForm() {
  const [state, formAction] = useActionState(loginAction, initialState);

  return (
    <form action={formAction} className="grid gap-3.5">
      <div>
        <label htmlFor="username" className="mb-1.5 block text-[13px] font-semibold text-ink">
          Tên đăng nhập
        </label>
        <input
          id="username"
          name="username"
          autoComplete="username"
          placeholder="admin"
          required
          className="w-full rounded-xl border border-ink/15 bg-white/85 px-3.5 py-2.5 text-sm
                     text-ink outline-none placeholder:text-ink/40 focus:border-primary"
        />
      </div>
      <div>
        <label htmlFor="password" className="mb-1.5 block text-[13px] font-semibold text-ink">
          Mật khẩu
        </label>
        <input
          id="password"
          name="password"
          type="password"
          autoComplete="current-password"
          placeholder="••••••••"
          required
          className="w-full rounded-xl border border-ink/15 bg-white/85 px-3.5 py-2.5 text-sm
                     text-ink outline-none placeholder:text-ink/40 focus:border-primary"
        />
      </div>

      {state.error && (
        <p className="text-[13px] font-semibold text-severe" role="alert">
          {state.error}
        </p>
      )}

      <SubmitButton />
    </form>
  );
}
