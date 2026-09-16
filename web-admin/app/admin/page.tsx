import Link from "next/link";

import { adminFetch, storageUrl } from "@/lib/api";
import type {
  DashboardStats,
  DiagnosisPage,
  ForumPostPage,
  UserOut,
} from "@/lib/types";
import { RangeSelect } from "@/components/RangeSelect";
import { StatCard } from "@/components/StatCard";
import { Tag, severityTone } from "@/components/Tag";
import { DashboardIcon, DiseaseIcon, PlotsIcon, UsersIcon, WarningIcon } from "@/components/icons";
import { TrendAreaChart } from "@/components/charts/TrendAreaChart";
import { DiseaseBarChart } from "@/components/charts/DiseaseBarChart";
import { SeverityDonutChart } from "@/components/charts/SeverityDonutChart";
import { TYPE_LABEL, TYPE_TONE } from "@/app/admin/forum/labels";

export const metadata = { title: "Tổng quan — AgriXAI Admin" };

const RANGE_OPTIONS = [7, 30, 90, 365];

function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "vừa xong";
  if (mins < 60) return `${mins} phút trước`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} giờ trước`;
  const days = Math.floor(hours / 24);
  return `${days} ngày trước`;
}

export default async function DashboardPage({
  searchParams,
}: {
  searchParams: Promise<{ days?: string }>;
}) {
  const { days: daysParam } = await searchParams;
  const days = RANGE_OPTIONS.includes(Number(daysParam)) ? Number(daysParam) : 30;

  const [stats, recentDiagnoses, recentPosts, farmers] = await Promise.all([
    adminFetch<DashboardStats>("/stats/dashboard", { searchParams: { days } }),
    adminFetch<DiagnosisPage>("/diagnoses", { searchParams: { page_size: 5 } }),
    adminFetch<ForumPostPage>("/forum/posts", { searchParams: { page_size: 5 } }),
    adminFetch<UserOut[]>("/users", { searchParams: { role: "farmer", limit: 500 } }),
  ]);

  const farmerName = new Map(farmers.map((f) => [f.id, f.full_name]));
  const totalDiseaseCases = stats.by_disease.reduce((s, d) => s + d.count, 0);

  return (
    <div>
      {!stats.using_real_model && (
        <div className="mb-5 flex items-start gap-3 rounded-2xl border border-accent/35 bg-accent/14 px-5 py-3.5 text-sm font-semibold text-accent-ink">
          <WarningIcon className="mt-0.5 shrink-0" width={18} height={18} />
          <span>
            Đang chạy mô hình giả (DummyPredictor) — số liệu chẩn đoán bên dưới không có ý nghĩa
            thực tế. Trỏ <code className="rounded bg-white/50 px-1">MODEL_CHECKPOINT</code> trong{" "}
            <code className="rounded bg-white/50 px-1">backend/.env</code> tới checkpoint thật để
            chuyển đổi.
          </span>
        </div>
      )}

      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-extrabold tracking-[-0.01em]">Tổng quan hệ thống</h1>
          <p className="mt-1 text-[13px] text-ink/60">
            Mô hình đang chạy: <span className="font-semibold text-ink/80">{stats.model_version}</span>
            {!stats.using_real_model && " (giả lập)"}
          </p>
        </div>
        <RangeSelect options={RANGE_OPTIONS} value={days} />
      </div>

      <div className="mb-6 grid grid-cols-4 gap-4">
        <StatCard
          label="Tổng số lô đất"
          value={stats.overview.total_plots}
          icon={<PlotsIcon width={18} height={18} />}
        />
        <StatCard
          label="Tổng số nông dân"
          value={stats.overview.total_farmers}
          icon={<UsersIcon width={18} height={18} />}
        />
        <StatCard
          label="Tổng lượt chẩn đoán"
          value={stats.overview.total_diagnoses}
          icon={<DashboardIcon width={18} height={18} />}
        />
        <StatCard
          label="Cảnh báo Nặng (7 ngày)"
          value={stats.overview.recent_alerts}
          icon={<WarningIcon width={18} height={18} />}
          accent
        />
      </div>

      <div className="mb-6 grid grid-cols-[2fr_1fr] gap-5">
        <div className="rounded-[20px] border border-border bg-surface p-5">
          <div className="mb-1 text-[15px] font-bold text-ink">Số lượt chẩn đoán theo ngày</div>
          <p className="mb-3 text-xs text-ink/55">
            {days} ngày gần nhất · {stats.timeseries.reduce((s, p) => s + p.count, 0)} lượt
          </p>
          {stats.timeseries.length === 0 ? (
            <p className="py-16 text-center text-sm text-ink/60">Chưa có dữ liệu trong khoảng này</p>
          ) : (
            <TrendAreaChart data={stats.timeseries} />
          )}
        </div>

        <div className="rounded-[20px] border border-border bg-surface p-5">
          <div className="mb-1 text-[15px] font-bold text-ink">Phân bố theo mức độ nặng</div>
          <p className="mb-3 text-xs text-ink/55">{days} ngày gần nhất</p>
          {stats.by_severity.length === 0 ? (
            <p className="py-16 text-center text-sm text-ink/60">Chưa có dữ liệu</p>
          ) : (
            <SeverityDonutChart data={stats.by_severity} />
          )}
        </div>
      </div>

      <div className="mb-6 rounded-[20px] border border-border bg-surface p-5">
        <div className="mb-1 flex items-center gap-2 text-[15px] font-bold text-ink">
          <DiseaseIcon width={16} height={16} />
          Phân bố theo loại bệnh
        </div>
        <p className="mb-3 text-xs text-ink/55">
          {days} ngày gần nhất · {totalDiseaseCases} ca trên {stats.by_disease.length} loại bệnh
        </p>
        {stats.by_disease.length === 0 ? (
          <p className="py-16 text-center text-sm text-ink/60">Chưa có dữ liệu</p>
        ) : (
          <DiseaseBarChart data={stats.by_disease} />
        )}
      </div>

      <div className="grid grid-cols-2 gap-5">
        <div className="rounded-[20px] border border-border bg-surface p-5">
          <div className="mb-3.5 text-[15px] font-bold text-ink">Chẩn đoán gần đây</div>
          <div className="grid gap-2">
            {recentDiagnoses.items.map((d) => (
              <Link
                key={d.id}
                href={`/admin/diagnoses?detail=${d.id}`}
                className="flex items-center gap-3 rounded-xl px-2.5 py-2 transition hover:bg-canvas"
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={storageUrl(d.image_url)}
                  alt=""
                  className="h-10 w-10 shrink-0 rounded-lg object-cover"
                />
                <div className="min-w-0 flex-1">
                  <div className="truncate text-[13px] font-semibold text-ink">{d.disease_name}</div>
                  <div className="truncate text-xs text-ink/55">
                    {farmerName.get(d.user_id) ?? "—"} · {timeAgo(d.created_at)}
                  </div>
                </div>
                <Tag tone={severityTone(d.severity)}>{d.severity_name}</Tag>
              </Link>
            ))}
            {recentDiagnoses.items.length === 0 && (
              <p className="py-8 text-center text-sm text-ink/60">Chưa có lượt chẩn đoán nào</p>
            )}
          </div>
        </div>

        <div className="rounded-[20px] border border-border bg-surface p-5">
          <div className="mb-3.5 text-[15px] font-bold text-ink">Bài viết diễn đàn gần đây</div>
          <div className="grid gap-2">
            {recentPosts.items.map((p) => (
              <Link
                key={p.id}
                href={`/admin/forum?detail=${p.id}`}
                className="block rounded-xl px-2.5 py-2 transition hover:bg-canvas"
              >
                <div className="mb-1 flex items-center gap-2">
                  <span className="truncate text-[13px] font-semibold text-ink">{p.disease_name}</span>
                  <Tag tone={TYPE_TONE[p.type]}>{TYPE_LABEL[p.type]}</Tag>
                </div>
                <div className="truncate text-xs text-ink/55">
                  {p.user_full_name} · {timeAgo(p.created_at)} · {p.comments_count} bình luận
                </div>
              </Link>
            ))}
            {recentPosts.items.length === 0 && (
              <p className="py-8 text-center text-sm text-ink/60">Chưa có bài viết nào</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
