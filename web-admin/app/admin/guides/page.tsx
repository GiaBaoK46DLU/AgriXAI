import Link from "next/link";

import { adminFetch } from "@/lib/api";
import * as ui from "@/lib/ui";
import { firstStringParam } from "@/lib/params";
import { Tag } from "@/components/Tag";
import type { DiseaseGuideOut, DiseaseInfo } from "@/lib/types";

import { GuideFormModal } from "./GuideFormModal";

export const metadata = { title: "Video hướng dẫn — AgriXAI Admin" };

export default async function GuidesPage({
  searchParams,
}: {
  searchParams: Promise<{ edit?: string; error?: string }>;
}) {
  const sp = await searchParams;

  const [diseases, guides] = await Promise.all([
    adminFetch<DiseaseInfo[]>("/diseases"),
    adminFetch<DiseaseGuideOut[]>("/medicines/guides"),
  ]);
  const guideByKey = new Map(guides.map((g) => [g.disease_key, g]));
  // "Lá khoẻ mạnh" không có gì để "xử lý" — không đưa vào danh sách gán video.
  const treatableDiseases = diseases.filter((d) => !d.is_healthy);

  const editKey = firstStringParam(sp.edit);
  const editingDisease = editKey ? treatableDiseases.find((d) => d.key === editKey) : undefined;

  return (
    <div>
      <h1 className="mb-5 text-xl font-extrabold tracking-[-0.01em]">Video hướng dẫn</h1>
      <p className="mb-[18px] -mt-3 text-[13px] text-ink/60">
        Mỗi bệnh gán một video YouTube riêng — sửa video của một bệnh không ảnh hưởng các bệnh khác.
      </p>

      {sp.error && (
        <div className="mb-4 rounded-xl border border-severe/25 bg-severe-bg px-4 py-2.5 text-sm font-semibold text-severe">
          {sp.error}
        </div>
      )}

      <div className={ui.card}>
        <table className="w-full border-collapse text-[13px]">
          <thead>
            <tr className="bg-canvas">
              <th className={ui.th}>Bệnh</th>
              <th className={ui.th}>Video</th>
              <th className={ui.th}>Trạng thái</th>
              <th className={ui.th}></th>
            </tr>
          </thead>
          <tbody>
            {treatableDiseases.map((d) => {
              const guide = guideByKey.get(d.key);
              return (
                <tr key={d.key} className={ui.tr}>
                  <td className={`${ui.td} font-semibold`}>{d.name_vi}</td>
                  <td className={ui.td}>
                    {guide ? (
                      <a
                        href={guide.video_url}
                        target="_blank"
                        rel="noreferrer"
                        className="font-semibold text-primary hover:text-primary-dark"
                      >
                        Xem video
                      </a>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className={ui.td}>
                    <Tag tone={guide ? "primary" : "neutral"}>{guide ? "Đã gán" : "Chưa có"}</Tag>
                  </td>
                  <td className={`${ui.td} text-right`}>
                    <Link href={`/admin/guides?edit=${d.key}`} className={ui.btnGhost}>
                      {guide ? "Sửa" : "+ Gán video"}
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {editingDisease && (
        <GuideFormModal disease={editingDisease} guide={guideByKey.get(editingDisease.key)} />
      )}
    </div>
  );
}
