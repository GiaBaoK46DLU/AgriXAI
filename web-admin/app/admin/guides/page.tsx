import { adminFetch } from "@/lib/api";
import * as ui from "@/lib/ui";
import { ConfirmSubmitButton } from "@/components/ConfirmSubmitButton";
import { toYoutubeEmbedUrl } from "@/lib/youtube";
import type { DiseaseGuideOut, DiseaseInfo } from "@/lib/types";

import { deleteGuideAction, saveGuideAction } from "./actions";

export const metadata = { title: "Video hướng dẫn — AgriXAI Admin" };

export default async function GuidesPage({
  searchParams,
}: {
  searchParams: Promise<{ disease?: string; error?: string }>;
}) {
  const sp = await searchParams;
  const diseases = await adminFetch<DiseaseInfo[]>("/diseases");
  const selectedDisease = sp.disease || diseases[0]?.key || "";

  const guide = selectedDisease
    ? await adminFetch<DiseaseGuideOut | null>(`/medicines/guides/${selectedDisease}`)
    : null;
  const embedUrl = guide ? toYoutubeEmbedUrl(guide.video_url) : null;
  const saveAction = saveGuideAction.bind(null, selectedDisease);

  return (
    <div>
      <h1 className="mb-5 text-xl font-extrabold tracking-[-0.01em]">Video hướng dẫn</h1>

      {sp.error && (
        <div className="mb-4 rounded-xl border border-severe/25 bg-severe-bg px-4 py-2.5 text-sm font-semibold text-severe">
          {sp.error}
        </div>
      )}

      <div className={`${ui.card} max-w-[640px] p-[22px]`}>
        <form className="mb-4">
          <div className={ui.label}>Chọn bệnh</div>
          <select name="disease" defaultValue={selectedDisease} className={`${ui.select} mb-2`}>
            {diseases.map((d) => (
              <option key={d.key} value={d.key}>
                {d.name_vi}
              </option>
            ))}
          </select>
          <button type="submit" className={ui.btnGhost}>
            Xem
          </button>
        </form>

        <form action={saveAction} className="mb-4">
          <div className={ui.label}>Link video YouTube</div>
          <div className="flex gap-2">
            <input
              name="video_url"
              defaultValue={guide?.video_url ?? ""}
              placeholder="https://youtube.com/watch?v=..."
              className={`${ui.input} flex-1`}
            />
            <button type="submit" className={ui.btnPrimary}>
              Lưu
            </button>
          </div>
        </form>

        {guide && embedUrl && (
          <div>
            <iframe
              src={embedUrl}
              className="aspect-video w-full rounded-2xl border-0"
              allowFullScreen
            />
            <form action={deleteGuideAction.bind(null, selectedDisease)} className="mt-3">
              <ConfirmSubmitButton confirmMessage="Gỡ video hướng dẫn của bệnh này?" className={ui.btnDanger}>
                Gỡ video
              </ConfirmSubmitButton>
            </form>
          </div>
        )}

        {guide && !embedUrl && (
          <p className="rounded-2xl bg-severe-bg px-4 py-3 text-[13px] text-severe">
            Link đã lưu nhưng không nhận ra được là URL YouTube hợp lệ — kiểm tra lại.
          </p>
        )}

        {!guide && (
          <div className="rounded-2xl bg-canvas p-10 text-center text-[13px] text-ink/65">
            Chưa có video hướng dẫn cho bệnh này
          </div>
        )}
      </div>
    </div>
  );
}
