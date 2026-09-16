import Link from "next/link";

function hrefFor(basePath: string, params: URLSearchParams, page: number): string {
  const next = new URLSearchParams(params);
  next.set("page", String(page));
  return `${basePath}?${next.toString()}`;
}

export function Pagination({
  page,
  pageSize,
  total,
  basePath,
  searchParams,
}: {
  page: number;
  pageSize: number;
  total: number;
  basePath: string;
  /** searchParams hiện tại của trang (đã lọc bỏ `page`) để giữ nguyên bộ lọc khi chuyển trang. */
  searchParams: Record<string, string | undefined>;
}) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(searchParams)) {
    if (value) params.set(key, value);
  }

  return (
    <div className="flex items-center justify-between border-t border-border px-4 py-3.5">
      <span className="text-xs text-ink/65">
        Trang {page} / {totalPages} · {total} bản ghi
      </span>
      <div className="flex gap-2">
        <Link
          href={hrefFor(basePath, params, Math.max(1, page - 1))}
          aria-disabled={page <= 1}
          className={`rounded-full border border-border px-3.5 py-1.5 text-xs font-semibold ${
            page <= 1 ? "pointer-events-none opacity-40" : "bg-surface hover:bg-ink/8"
          }`}
        >
          ← Trước
        </Link>
        <Link
          href={hrefFor(basePath, params, Math.min(totalPages, page + 1))}
          aria-disabled={page >= totalPages}
          className={`rounded-full border border-border px-3.5 py-1.5 text-xs font-semibold ${
            page >= totalPages ? "pointer-events-none opacity-40" : "bg-surface hover:bg-ink/8"
          }`}
        >
          Sau →
        </Link>
      </div>
    </div>
  );
}
