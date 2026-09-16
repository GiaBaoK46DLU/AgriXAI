import Link from "next/link";

import { adminFetch } from "@/lib/api";
import * as ui from "@/lib/ui";
import { firstIntParam } from "@/lib/params";
import { Tag } from "@/components/Tag";
import { Pagination } from "@/components/Pagination";
import type { DiseaseInfo, ForumPostPage, ForumPostType } from "@/lib/types";

import { PostDetailModal } from "./PostDetailModal";
import { TYPE_LABEL, TYPE_TONE, formatDateTime } from "./labels";

export const metadata = { title: "Diễn đàn — AgriXAI Admin" };

export default async function ForumPage({
  searchParams,
}: {
  searchParams: Promise<{
    disease_key?: string;
    type?: string;
    page?: string;
    detail?: string;
    error?: string;
  }>;
}) {
  const sp = await searchParams;
  const page = Math.max(1, firstIntParam(sp.page) ?? 1);
  const detailId = firstIntParam(sp.detail);
  const pageSize = 20;

  const [postPage, diseases] = await Promise.all([
    adminFetch<ForumPostPage>("/forum/posts", {
      searchParams: {
        disease_key: sp.disease_key || undefined,
        type: sp.type || undefined,
        page,
        page_size: pageSize,
      },
    }),
    adminFetch<DiseaseInfo[]>("/diseases"),
  ]);

  return (
    <div>
      <h1 className="mb-5 text-xl font-extrabold tracking-[-0.01em]">Diễn đàn nông dân</h1>
      <p className="mb-[18px] -mt-3 text-[13px] text-ink/60">
        Kiểm duyệt bài viết và bình luận — nông dân trao đổi kinh nghiệm quanh một lần chẩn đoán.
      </p>

      {sp.error && (
        <div className="mb-4 rounded-xl border border-severe/25 bg-severe-bg px-4 py-2.5 text-sm font-semibold text-severe">
          {sp.error}
        </div>
      )}

      <form className="mb-[18px] flex flex-wrap gap-2.5">
        <select name="disease_key" defaultValue={sp.disease_key ?? ""} className={`${ui.select} w-auto`}>
          <option value="">Tất cả loại bệnh</option>
          {diseases.map((d) => (
            <option key={d.key} value={d.key}>
              {d.name_vi}
            </option>
          ))}
        </select>
        <select name="type" defaultValue={sp.type ?? ""} className={`${ui.select} w-auto`}>
          <option value="">Tất cả loại phản hồi</option>
          {(Object.keys(TYPE_LABEL) as ForumPostType[]).map((t) => (
            <option key={t} value={t}>
              {TYPE_LABEL[t]}
            </option>
          ))}
        </select>
        <button type="submit" className={ui.btnGhost}>
          Lọc
        </button>
      </form>

      <div className={ui.card}>
        <table className="w-full border-collapse text-[13px]">
          <thead>
            <tr className="bg-canvas">
              <th className={ui.th}>Bệnh</th>
              <th className={ui.th}>Loại</th>
              <th className={ui.th}>Tác giả</th>
              <th className={ui.th}>Nội dung</th>
              <th className={ui.th}>Thích</th>
              <th className={ui.th}>Bình luận</th>
              <th className={ui.th}>Thời gian</th>
              <th className={ui.th}></th>
            </tr>
          </thead>
          <tbody>
            {postPage.items.map((p) => (
              <tr key={p.id} className={ui.tr}>
                <td className={`${ui.td} font-semibold`}>{p.disease_name}</td>
                <td className={ui.td}>
                  <Tag tone={TYPE_TONE[p.type]}>{TYPE_LABEL[p.type]}</Tag>
                </td>
                <td className={ui.td}>{p.user_full_name}</td>
                <td className={`${ui.td} max-w-[280px] truncate`}>{p.content}</td>
                <td className={ui.td}>{p.likes_count}</td>
                <td className={ui.td}>{p.comments_count}</td>
                <td className={`${ui.td} text-ink/70`}>{formatDateTime(p.created_at)}</td>
                <td className={`${ui.td} text-right`}>
                  <Link
                    href={`/admin/forum?${new URLSearchParams({
                      ...(sp.disease_key ? { disease_key: sp.disease_key } : {}),
                      ...(sp.type ? { type: sp.type } : {}),
                      page: String(page),
                      detail: String(p.id),
                    }).toString()}`}
                    className="rounded-full border border-primary px-3 py-1.5 text-xs font-bold text-primary hover:bg-primary/10"
                  >
                    Xem
                  </Link>
                </td>
              </tr>
            ))}
            {postPage.items.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-ink/60">
                  Không có bài viết nào khớp bộ lọc
                </td>
              </tr>
            )}
          </tbody>
        </table>
        <Pagination
          page={postPage.page}
          pageSize={postPage.page_size}
          total={postPage.total}
          basePath="/admin/forum"
          searchParams={{ disease_key: sp.disease_key, type: sp.type }}
        />
      </div>

      {detailId !== undefined && <PostDetailModal postId={detailId} />}
    </div>
  );
}
