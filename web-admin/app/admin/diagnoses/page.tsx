import Link from "next/link";

import { adminFetch, storageUrl } from "@/lib/api";
import * as ui from "@/lib/ui";
import { firstIntParam } from "@/lib/params";
import { Tag, severityTone } from "@/components/Tag";
import { Pagination } from "@/components/Pagination";
import type { DiagnosisPage, DiseaseInfo, UserOut } from "@/lib/types";

import { DiagnosisDetailModal } from "./DiagnosisDetailModal";

export const metadata = { title: "Lịch sử chẩn đoán — AgriXAI Admin" };

const SEVERITY_OPTIONS = [
  { value: "", label: "Tất cả mức độ" },
  { value: "none", label: "Không có dấu hiệu" },
  { value: "mild", label: "Nhẹ" },
  { value: "moderate", label: "Trung bình" },
  { value: "severe", label: "Nặng" },
];

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("vi-VN", { dateStyle: "short", timeStyle: "short" });
}

export default async function DiagnosesPage({
  searchParams,
}: {
  searchParams: Promise<{
    user_id?: string;
    disease_key?: string;
    severity?: string;
    page?: string;
    detail?: string;
  }>;
}) {
  const sp = await searchParams;
  const page = Math.max(1, firstIntParam(sp.page) ?? 1);
  const detailId = firstIntParam(sp.detail);
  const pageSize = 20;

  const [diagPage, farmers, diseases] = await Promise.all([
    adminFetch<DiagnosisPage>("/diagnoses", {
      searchParams: {
        user_id: sp.user_id || undefined,
        disease_key: sp.disease_key || undefined,
        severity: sp.severity || undefined,
        page,
        page_size: pageSize,
      },
    }),
    adminFetch<UserOut[]>("/users", { searchParams: { role: "farmer", limit: 500 } }),
    adminFetch<DiseaseInfo[]>("/diseases"),
  ]);

  const userNameById = new Map(farmers.map((u) => [u.id, u.full_name]));

  return (
    <div>
      <h1 className="mb-5 text-xl font-extrabold tracking-[-0.01em]">Lịch sử chẩn đoán</h1>

      <form className="mb-[18px] flex flex-wrap gap-2.5">
        <select name="user_id" defaultValue={sp.user_id ?? ""} className={`${ui.select} w-auto`}>
          <option value="">Tất cả nông dân</option>
          {farmers.map((f) => (
            <option key={f.id} value={f.id}>
              {f.full_name}
            </option>
          ))}
        </select>
        <select name="disease_key" defaultValue={sp.disease_key ?? ""} className={`${ui.select} w-auto`}>
          <option value="">Tất cả loại bệnh</option>
          {diseases.map((d) => (
            <option key={d.key} value={d.key}>
              {d.name_vi}
            </option>
          ))}
        </select>
        <select name="severity" defaultValue={sp.severity ?? ""} className={`${ui.select} w-auto`}>
          {SEVERITY_OPTIONS.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
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
              <th className={ui.th}></th>
              <th className={ui.th}>Bệnh</th>
              <th className={ui.th}>Độ tin cậy</th>
              <th className={ui.th}>Mức độ</th>
              <th className={ui.th}>Nông dân</th>
              <th className={ui.th}>Lô đất</th>
              <th className={ui.th}>Thời gian</th>
              <th className={ui.th}></th>
            </tr>
          </thead>
          <tbody>
            {diagPage.items.map((d) => (
              <tr key={d.id} className={ui.tr}>
                <td className="py-2 pl-4">
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={storageUrl(d.image_url)}
                    alt=""
                    className="h-11 w-11 rounded-lg object-cover"
                  />
                </td>
                <td className={`${ui.td} font-semibold`}>{d.disease_name}</td>
                <td className={ui.td}>{d.confidence.toFixed(1)}%</td>
                <td className={ui.td}>
                  <Tag tone={severityTone(d.severity)}>{d.severity_name}</Tag>
                </td>
                <td className={ui.td}>{userNameById.get(d.user_id) ?? "—"}</td>
                <td className={ui.td}>{d.plot_puc ?? "—"}</td>
                <td className={`${ui.td} text-ink/70`}>{formatDateTime(d.created_at)}</td>
                <td className={`${ui.td} text-right`}>
                  <Link
                    href={`/admin/diagnoses?${new URLSearchParams({
                      ...(sp.user_id ? { user_id: sp.user_id } : {}),
                      ...(sp.disease_key ? { disease_key: sp.disease_key } : {}),
                      ...(sp.severity ? { severity: sp.severity } : {}),
                      page: String(page),
                      detail: String(d.id),
                    }).toString()}`}
                    className="rounded-full border border-primary px-3 py-1.5 text-xs font-bold text-primary hover:bg-primary/10"
                  >
                    Xem
                  </Link>
                </td>
              </tr>
            ))}
            {diagPage.items.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-ink/60">
                  Không có bản ghi nào khớp bộ lọc
                </td>
              </tr>
            )}
          </tbody>
        </table>
        <Pagination
          page={diagPage.page}
          pageSize={diagPage.page_size}
          total={diagPage.total}
          basePath="/admin/diagnoses"
          searchParams={{ user_id: sp.user_id, disease_key: sp.disease_key, severity: sp.severity }}
        />
      </div>

      {detailId !== undefined && <DiagnosisDetailModal diagnosisId={detailId} />}
    </div>
  );
}
