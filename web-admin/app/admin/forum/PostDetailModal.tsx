import Link from "next/link";
import { notFound } from "next/navigation";

import { adminFetch, ApiError, storageUrl } from "@/lib/api";
import * as ui from "@/lib/ui";
import { Modal } from "@/components/Modal";
import { ConfirmSubmitButton } from "@/components/ConfirmSubmitButton";
import { Tag, severityTone } from "@/components/Tag";
import type { DiagnosisDetail, ForumPostDetail } from "@/lib/types";

import { createCommentAction, deleteCommentAction, deletePostAction } from "./actions";
import { TYPE_LABEL, TYPE_TONE, formatDateTime } from "./labels";

/** Tên quản trị phải nổi bật hơn người dùng thường — đậm màu xanh chính +
 * nhãn "Quản trị" nhỏ, để phân biệt ngay khi admin tham gia bình luận cùng
 * nông dân trong cùng một luồng. */
function AuthorName({ name, role }: { name: string; role: string }) {
  if (role === "admin") {
    return (
      <span className="inline-flex items-center gap-1.5">
        <span className="font-extrabold text-primary-dark">{name}</span>
        <span className="rounded-full bg-primary/15 px-1.5 py-[1px] text-[10px] font-bold uppercase tracking-wide text-primary-dark">
          Quản trị
        </span>
      </span>
    );
  }
  return <span className="font-bold text-ink">{name}</span>;
}

/** Trước đây chỉ có một dòng chữ liên kết ("Xem lần chẩn đoán liên kết:
 * ...") — admin phải đoán nội dung qua `diagnosis_summary` rồi bấm sang trang
 * khác mới thấy ảnh/mức độ thật. Giờ nạp thẳng bản ghi và hiện luôn ảnh +
 * bệnh + mức độ ngay trong modal bài viết, bấm vào mới điều hướng sang chi
 * tiết đầy đủ. `diagnosis_id` dùng `ondelete="SET NULL"` (xem
 * `models/forum.py`) nên về lý thuyết không bao giờ trỏ tới bản ghi đã xoá,
 * nhưng vẫn bọc try/catch cho chắc — lỗi ở khối này không được làm sập cả
 * modal bài viết. */
async function LinkedDiagnosis({ diagnosisId }: { diagnosisId: number }) {
  let d: DiagnosisDetail | null = null;
  try {
    d = await adminFetch<DiagnosisDetail>(`/diagnoses/${diagnosisId}`);
  } catch (err) {
    if (!(err instanceof ApiError && err.status === 404)) throw err;
  }

  if (!d) {
    return (
      <p className="mb-5 rounded-xl bg-canvas px-3.5 py-2.5 text-[13px] text-ink/60">
        Lần chẩn đoán đính kèm không còn tồn tại
      </p>
    );
  }

  return (
    <Link
      href={`/admin/diagnoses?detail=${diagnosisId}`}
      className="mb-5 flex items-center gap-3 rounded-xl bg-canvas p-3 transition hover:bg-primary/10"
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src={storageUrl(d.image_url)}
        alt=""
        className="h-14 w-14 shrink-0 rounded-lg object-cover"
      />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-[13px] font-bold text-ink">{d.disease_name}</span>
          <Tag tone={severityTone(d.severity)}>{d.severity_name}</Tag>
        </div>
        <div className="mt-0.5 text-xs text-ink/60">
          {formatDateTime(d.created_at)} · Độ tin cậy {d.confidence.toFixed(1)}%
        </div>
      </div>
    </Link>
  );
}

export async function PostDetailModal({ postId }: { postId: number }) {
  let post: ForumPostDetail;
  try {
    post = await adminFetch<ForumPostDetail>(`/forum/posts/${postId}`);
  } catch (err) {
    // `?detail=` bị sửa tay thành một id không tồn tại — hiện trang 404 thay vì
    // để lỗi ApiError chưa bắt làm sập cả trang diễn đàn.
    if (err instanceof ApiError && err.status === 404) notFound();
    throw err;
  }
  const submitComment = createCommentAction.bind(null, post.id);

  return (
    <Modal title={post.disease_name} closeHref="/admin/forum" maxWidth={640}>
      <div className="-mt-2 mb-4 flex flex-wrap items-center gap-2">
        <Tag tone={TYPE_TONE[post.type]}>{TYPE_LABEL[post.type]}</Tag>
        <span className="text-[13px] text-ink/65">
          <AuthorName name={post.user_full_name} role={post.user_role} /> ·{" "}
          {formatDateTime(post.created_at)} · {post.likes_count} lượt thích
        </span>
      </div>

      <p className="mb-4 whitespace-pre-wrap text-[14px] leading-relaxed">{post.content}</p>

      {post.diagnosis_id && <LinkedDiagnosis diagnosisId={post.diagnosis_id} />}

      <form action={deletePostAction.bind(null, post.id)} className="mb-6">
        <ConfirmSubmitButton
          confirmMessage="Xoá bài viết này? Mọi bình luận bên dưới cũng bị xoá theo."
          className={ui.btnDanger}
        >
          Xoá bài viết
        </ConfirmSubmitButton>
      </form>

      <div className="mb-2.5 text-[13px] font-bold">Bình luận ({post.comments.length})</div>
      <div className="mb-4 grid gap-2">
        {post.comments.map((c) => (
          <div
            key={c.id}
            className={`flex items-start justify-between gap-3 rounded-xl px-3.5 py-2.5 ${
              c.user_role === "admin" ? "bg-primary/8 ring-1 ring-primary/20" : "bg-canvas"
            }`}
          >
            <div>
              <div className="text-xs">
                <AuthorName name={c.user_full_name} role={c.user_role} />{" "}
                <span className="text-ink/60">· {formatDateTime(c.created_at)}</span>
              </div>
              <div className="mt-0.5 text-[13px]">{c.content}</div>
            </div>
            <form action={deleteCommentAction.bind(null, c.id, post.id)}>
              <ConfirmSubmitButton
                confirmMessage="Xoá bình luận này?"
                className="shrink-0 text-xs text-ink/60 hover:text-severe"
              >
                ✕
              </ConfirmSubmitButton>
            </form>
          </div>
        ))}
        {post.comments.length === 0 && (
          <p className="py-4 text-center text-sm text-ink/60">Chưa có bình luận nào</p>
        )}
      </div>

      <form action={submitComment} className="flex items-end gap-2">
        <textarea
          name="content"
          required
          rows={2}
          placeholder="Bình luận với vai trò quản trị..."
          className={`${ui.input} flex-1 resize-none`}
        />
        <button type="submit" className={ui.btnPrimary}>
          Gửi
        </button>
      </form>
    </Modal>
  );
}
