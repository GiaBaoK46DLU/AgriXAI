"use client";

import type { ReactNode } from "react";

/** Nút submit cho các form xoá/khoá — chặn submit bằng `confirm()` gốc của
 * trình duyệt nếu người dùng bấm "Huỷ". Dùng bên trong <form action={...}>
 * gọi Server Action, không tự quản lý state riêng. */
export function ConfirmSubmitButton({
  confirmMessage,
  className,
  children,
}: {
  confirmMessage: string;
  className: string;
  children: ReactNode;
}) {
  return (
    <button
      type="submit"
      className={className}
      onClick={(e) => {
        if (!confirm(confirmMessage)) e.preventDefault();
      }}
    >
      {children}
    </button>
  );
}
