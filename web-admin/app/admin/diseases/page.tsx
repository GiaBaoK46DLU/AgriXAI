import { adminFetch } from "@/lib/api";
import * as ui from "@/lib/ui";
import { Tag } from "@/components/Tag";
import type { DiseaseInfo } from "@/lib/types";

export const metadata = { title: "Danh mục bệnh — AgriXAI Admin" };

export default async function DiseasesPage() {
  const diseases = await adminFetch<DiseaseInfo[]>("/diseases");

  return (
    <div>
      <h1 className="mb-5 text-xl font-extrabold tracking-[-0.01em]">Danh mục bệnh</h1>

      <div className="mb-[18px] rounded-2xl border border-accent/35 bg-accent/14 px-[18px] py-4 text-[13px] font-semibold text-accent-ink">
        Thứ tự {diseases.length} lớp bệnh gắn chặt với đầu ra của mô hình AI — không thể sửa, xoá
        hoặc đổi thứ tự tại đây. Đổi ở{" "}
        <code className="rounded bg-white/50 px-1">shared/data/tomato_diseases.json</code> đòi hỏi
        huấn luyện lại mô hình. Muốn sửa triệu chứng/gợi ý xử lý hiển thị, sửa trực tiếp trong file
        đó.
      </div>

      <div className={ui.card}>
        <table className="w-full border-collapse text-[13px]">
          <thead>
            <tr className="bg-canvas">
              <th className={ui.th}>#</th>
              <th className={ui.th}>Tên bệnh</th>
              <th className={ui.th}>Tác nhân</th>
              <th className={ui.th}>Triệu chứng</th>
              <th className={ui.th}>Điều kiện phát sinh</th>
              <th className={ui.th}>Thuốc gợi ý</th>
              <th className={ui.th}>Video</th>
            </tr>
          </thead>
          <tbody>
            {diseases.map((d, i) => (
              <tr key={d.key} className={ui.tr}>
                <td className={`${ui.td} text-ink/60`}>{i}</td>
                <td className={`${ui.td} font-semibold`}>
                  {d.name_vi}
                  {d.is_healthy && (
                    <span className="ml-2">
                      <Tag tone="primary">Khoẻ mạnh</Tag>
                    </span>
                  )}
                </td>
                <td className={`${ui.td} max-w-[180px]`}>{d.pathogen ?? "—"}</td>
                <td className={`${ui.td} max-w-[280px]`}>{d.symptoms || "—"}</td>
                <td className={`${ui.td} max-w-[240px] text-ink/75`}>
                  {d.favorable_conditions ?? "—"}
                </td>
                <td className={ui.td}>
                  {d.products.length > 0 ? `${d.products.length} thuốc` : "—"}
                </td>
                <td className={ui.td}>{d.video_url ? "Đã có" : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
