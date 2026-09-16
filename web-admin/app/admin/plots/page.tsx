import Link from "next/link";

import { adminFetch } from "@/lib/api";
import * as ui from "@/lib/ui";
import { Tag, plotStatusTone, severityTone } from "@/components/Tag";
import { Modal } from "@/components/Modal";
import type { DiagnosisPage, PlotWithStats } from "@/lib/types";

export const metadata = { title: "Lô đất — AgriXAI Admin" };

const STATUS_LABEL: Record<string, string> = {
  active: "Đang canh tác",
  fallow: "Bỏ hoá",
  archived: "Lưu trữ",
};

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("vi-VN", { dateStyle: "short", timeStyle: "short" });
}

export default async function PlotsPage({
  searchParams,
}: {
  searchParams: Promise<{ q?: string; detail?: string }>;
}) {
  const sp = await searchParams;
  const q = sp.q ?? "";

  const plots = await adminFetch<PlotWithStats[]>("/plots", { searchParams: { q: q || undefined } });
  const detailPlot = sp.detail ? plots.find((p) => p.id === Number(sp.detail)) : undefined;

  return (
    <div>
      <h1 className="mb-5 text-xl font-extrabold tracking-[-0.01em]">Lô đất</h1>

      <form className="mb-[18px] flex gap-2.5">
        <input
          name="q"
          defaultValue={q}
          placeholder="Tìm theo tên lô, mã PUC hoặc chủ lô..."
          className={`${ui.input} w-[320px]`}
        />
        <button type="submit" className={ui.btnGhost}>
          Lọc
        </button>
      </form>

      <div className={ui.card}>
        <table className="w-full border-collapse text-[13px]">
          <thead>
            <tr className="bg-canvas">
              <th className={ui.th}>Mã PUC</th>
              <th className={ui.th}>Tên lô</th>
              <th className={ui.th}>Chủ lô</th>
              <th className={ui.th}>Khu vực</th>
              <th className={ui.th}>Diện tích</th>
              <th className={ui.th}>Trạng thái</th>
              <th className={ui.th}>Bệnh gần nhất</th>
              <th className={ui.th}>Số lần</th>
              <th className={ui.th}>Lần gần nhất</th>
            </tr>
          </thead>
          <tbody>
            {plots.map((p) => (
              <tr key={p.id} className={ui.tr}>
                <td colSpan={9} className="p-0">
                  <Link
                    href={`/admin/plots?detail=${p.id}`}
                    className="grid grid-cols-[repeat(9,minmax(0,1fr))] items-center hover:bg-ink/6"
                  >
                    <span className={`${ui.td} font-semibold`}>{p.puc}</span>
                    <span className={ui.td}>{p.name}</span>
                    <span className={ui.td}>{p.owner_name ?? "—"}</span>
                    <span className={ui.td}>{p.region ?? "—"}</span>
                    <span className={ui.td}>{p.area_m2 ? `${(p.area_m2 / 10000).toFixed(2)} ha` : "—"}</span>
                    <span className={ui.td}>
                      <Tag tone={plotStatusTone(p.status)}>{STATUS_LABEL[p.status] ?? p.status}</Tag>
                    </span>
                    <span className={ui.td}>
                      {p.last_severity ? (
                        <Tag tone={severityTone(p.last_severity)}>{p.last_disease_name}</Tag>
                      ) : (
                        "—"
                      )}
                    </span>
                    <span className={ui.td}>{p.diagnosis_count}</span>
                    <span className={`${ui.td} text-ink/70`}>
                      {p.last_diagnosis_at ? formatDateTime(p.last_diagnosis_at) : "—"}
                    </span>
                  </Link>
                </td>
              </tr>
            ))}
            {plots.length === 0 && (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-ink/60">
                  Không có lô đất nào khớp tìm kiếm
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {detailPlot && <PlotDetail plot={detailPlot} />}
    </div>
  );
}

async function PlotDetail({ plot }: { plot: PlotWithStats }) {
  const history = await adminFetch<DiagnosisPage>("/diagnoses", {
    searchParams: { plot_id: plot.id, page_size: 50 },
  });

  return (
    <Modal
      title={plot.name}
      closeHref="/admin/plots"
      maxWidth={560}
    >
      <p className="mb-4 -mt-2 text-[13px] text-ink/65">
        {plot.puc} · {plot.owner_name ?? "—"} · {plot.region ?? "—"}
      </p>

      <div className="mb-2.5 text-sm font-bold">Lịch sử chẩn đoán của lô này</div>
      <div className="grid gap-2">
        {history.items.map((d) => (
          <div key={d.id} className="flex items-center justify-between rounded-xl bg-canvas px-3.5 py-2.5">
            <div>
              <div className="text-[13px] font-bold">{d.disease_name}</div>
              <div className="text-xs text-ink/60">{formatDateTime(d.created_at)}</div>
            </div>
            <Tag tone={severityTone(d.severity)}>{d.severity_name}</Tag>
          </div>
        ))}
        {history.items.length === 0 && (
          <p className="py-6 text-center text-sm text-ink/60">Lô này chưa có lần chẩn đoán nào</p>
        )}
      </div>
    </Modal>
  );
}
