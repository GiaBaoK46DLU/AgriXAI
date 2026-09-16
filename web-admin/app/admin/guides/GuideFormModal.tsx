import { Modal } from "@/components/Modal";
import { ConfirmSubmitButton } from "@/components/ConfirmSubmitButton";
import * as ui from "@/lib/ui";
import { toYoutubeEmbedUrl } from "@/lib/youtube";
import type { DiseaseGuideOut, DiseaseInfo } from "@/lib/types";

import { deleteGuideAction, saveGuideAction } from "./actions";

/** Nhận `disease` (khoá + tên cụ thể của MỘT bệnh) thay vì đọc lại state chọn
 * bệnh từ nơi khác — action lưu được `.bind()` thẳng vào `disease.key` ngay
 * tại đây, nên không có đường nào để lưu nhầm sang bệnh khác dù người dùng
 * điều hướng qua lại nhiều lần trước khi bấm Lưu. */
export function GuideFormModal({
  disease,
  guide,
}: {
  disease: DiseaseInfo;
  guide?: DiseaseGuideOut;
}) {
  const saveAction = saveGuideAction.bind(null, disease.key);
  const embedUrl = guide ? toYoutubeEmbedUrl(guide.video_url) : null;

  return (
    <Modal title={`Video hướng dẫn — ${disease.name_vi}`} closeHref="/admin/guides" maxWidth={560}>
      <form action={saveAction} className="grid gap-3">
        <div>
          <label className={ui.label}>Link video YouTube</label>
          <input
            name="video_url"
            defaultValue={guide?.video_url ?? ""}
            placeholder="https://youtube.com/watch?v=..."
            required
            className={ui.input}
          />
        </div>
        <div className="mt-1 flex justify-end gap-2.5">
          <a href="/admin/guides" className={ui.btnGhost}>
            Huỷ
          </a>
          <button type="submit" className={ui.btnPrimary}>
            Lưu
          </button>
        </div>
      </form>

      {guide && embedUrl && (
        <iframe
          src={embedUrl}
          className="mt-4 aspect-video w-full rounded-2xl border-0"
          allowFullScreen
        />
      )}
      {guide && !embedUrl && (
        <p className="mt-4 rounded-2xl bg-severe-bg px-4 py-3 text-[13px] text-severe">
          Link đã lưu nhưng không nhận ra được là URL YouTube hợp lệ — kiểm tra lại.
        </p>
      )}

      {guide && (
        <form action={deleteGuideAction.bind(null, disease.key)} className="mt-3">
          <ConfirmSubmitButton
            confirmMessage={`Gỡ video hướng dẫn của bệnh "${disease.name_vi}"?`}
            className={ui.btnDanger}
          >
            Gỡ video
          </ConfirmSubmitButton>
        </form>
      )}
    </Modal>
  );
}
