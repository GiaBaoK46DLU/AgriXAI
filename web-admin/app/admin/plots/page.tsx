import Link from "next/link";

import { adminFetch } from "@/lib/api";
import * as ui from "@/lib/ui";
import { firstIntParam } from "@/lib/params";
import { Tag, plotStatusTone, severityTone } from "@/components/Tag";
import { Modal } from "@/components/Modal";
import type { DiagnosisPage, PlotWithStats, UserOut } from "@/lib/types";

import { PlotFormModal } from "./PlotFormModal";

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
  searchParams: Promise<{ q?: string; region?: string; detail?: string; new?: string; error?: string }>;
}) {
  const sp = await searchParams;
  const q = sp.q ?? "";
  const region = sp.region ?? "";

  // Lấy toàn bộ lô (không lọc) riêng để dựng danh sách khu vực cho bộ lọc —
  // `region` là chuỗi tự do trong CSDL (không phải enum), nên không có danh
  // sách cố định nào để hardcode; phải suy ra từ dữ liệu thật đang có.
  const [plots, farmers, allPlots] = await Promise.all([
    adminFetch<PlotWithStats[]>("/plots", {
      searchParams: { q: q || undefined, region: region || undefined },
    }),
    adminFetch<UserOut[]>("/users", { searchParams: { role: "farmer", limit: 500 } }),
    adminFetch<PlotWithStats[]>("/plots", {}),
  ]);
  const regions = Array.from(
    new Set(allPlots.map((p) => p.region).filter((r): r is string => Boolean(r))),
  ).sort((a, b) => a.localeCompare(b, "vi"));

  const detailId = firstIntParam(sp.detail);
  const detailPlot = detailId !== undefined ? plots.find((p) => p.id === detailId) : undefined;

  return (
    <div>
      <h1 className="mb-5 text-xl font-extrabold tracking-[-0.01em]">Lô đất</h1>

      {sp.error && (
        <div className="mb-4 rounded-xl border border-severe/25 bg-severe-bg px-4 py-2.5 text-sm font-semibold text-severe">
          {sp.error}
        </div>
      )}

      <div className="mb-[18px] flex flex-wrap items-center justify-between gap-3">
        <form className="flex gap-2.5">
          <input
            name="q"
            defaultValue={q}
            placeholder="Tìm theo tên lô, mã PUC hoặc chủ lô..."
            className={`${ui.input} w-[320px]`}
          />
          <select name="region" defaultValue={region} className={ui.select}>
            <option value="">Mọi khu vực</option>
            {regions.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
          <button type="submit" className={ui.btnGhost}>
            Lọc
          </button>
        </form>
        <Link href="/admin/plots?new=1" className={ui.btnPrimary}>
          + Thêm lô đất
        </Link>
      </div>

      <div className={ui.card}>
        {/* Cột dữ liệu bản trước dùng một <td colSpan={9}> bọc lưới CSS riêng để
            cả hàng bấm được — nhưng lưới đó chia cột đều nhau (1fr) trong khi
            <th> của <thead> lại tự co giãn theo nội dung (table-layout mặc
            định), hai hệ tính cột độc lập nên header và dữ liệu không bao giờ
            thẳng hàng. Đổi lại thành <td> thật cho từng cột — cùng một bảng
            <table> thật thì trình duyệt tự căn đúng, giống cách trang Lịch sử
            chẩn đoán/Diễn đàn đã làm — và nút "Xem" thay cho việc bọc cả hàng
            trong <Link>. */}
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
              <th className={ui.th}></th>
            </tr>
          </thead>
          <tbody>
            {plots.map((p) => (
              <tr key={p.id} className={ui.tr}>
                <td className={`${ui.td} font-semibold`}>{p.puc}</td>
                <td className={ui.td}>{p.name}</td>
                <td className={ui.td}>{p.owner_name ?? "—"}</td>
                <td className={ui.td}>{p.region ?? "—"}</td>
                <td className={ui.td}>{p.area_m2 ? `${(p.area_m2 / 10000).toFixed(2)} ha` : "—"}</td>
                <td className={ui.td}>
                  <Tag tone={plotStatusTone(p.status)}>{STATUS_LABEL[p.status] ?? p.status}</Tag>
                </td>
                <td className={ui.td}>
                  {p.last_severity ? (
                    <Tag tone={severityTone(p.last_severity)}>{p.last_disease_name}</Tag>
                  ) : (
                    "—"
                  )}
                </td>
                <td className={ui.td}>{p.diagnosis_count}</td>
                <td className={`${ui.td} text-ink/70`}>
                  {p.last_diagnosis_at ? formatDateTime(p.last_diagnosis_at) : "—"}
                </td>
                <td className={`${ui.td} text-right`}>
                  <Link
                    href={`/admin/plots?detail=${p.id}`}
                    className="rounded-full border border-primary px-3 py-1.5 text-xs font-bold text-primary hover:bg-primary/10"
                  >
                    Xem
                  </Link>
                </td>
              </tr>
            ))}
            {plots.length === 0 && (
              <tr>
                <td colSpan={10} className="px-4 py-8 text-center text-ink/60">
                  Không có lô đất nào khớp tìm kiếm
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {detailPlot && <PlotDetail plot={detailPlot} />}
      {sp.new === "1" && <PlotFormModal farmers={farmers} />}
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
