import Link from "next/link";
import type { ReactNode } from "react";

import { CloseIcon } from "@/components/icons";

/** Modal server-render được: trạng thái đóng/mở là chính sự hiện diện của
 * component trong cây (điều khiển bởi searchParams của trang cha, ví dụ
 * `?new=1`), không phải state phía client — nút đóng chỉ là một <Link> quay
 * lại URL không có tham số đó. Nhờ vậy form bên trong dùng Server Action
 * thẳng, không cần bọc thêm client state cho việc mở/đóng. */
export function Modal({
  title,
  closeHref,
  children,
  maxWidth = 440,
}: {
  title: string;
  closeHref: string;
  children: ReactNode;
  maxWidth?: number;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/45 p-5">
      <div
        className="max-h-[85vh] w-full overflow-y-auto rounded-3xl bg-surface p-7 shadow-[0_24px_60px_rgba(18,48,29,0.3)]"
        style={{ maxWidth }}
      >
        <div className="mb-[18px] flex items-start justify-between gap-3">
          <h2 className="text-[17px] font-extrabold text-ink">{title}</h2>
          <Link
            href={closeHref}
            className="rounded-full p-1 text-ink/60 transition hover:bg-ink/8 hover:text-ink"
            aria-label="Đóng"
          >
            <CloseIcon />
          </Link>
        </div>
        {children}
      </div>
    </div>
  );
}
