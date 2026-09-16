import type { TimeseriesPoint } from "@/lib/types";

/** Sinh path SVG cho biểu đồ đường + phần tô mờ bên dưới, từ chuỗi
 * (ngày, số lượng). Thuần hàm toán học nên chạy được ngay trong Server
 * Component — không cần thư viện biểu đồ hay client JS nào cho một
 * sparkline đơn giản. */
export function buildLineChart(
  points: TimeseriesPoint[],
  width = 600,
  height = 160,
): { linePath: string; areaPath: string; maxCount: number } {
  if (points.length === 0) {
    return { linePath: "", areaPath: "", maxCount: 0 };
  }

  const maxCount = Math.max(1, ...points.map((p) => p.count));
  const stepX = points.length > 1 ? width / (points.length - 1) : 0;
  const coords = points.map((p, i) => {
    const x = points.length > 1 ? i * stepX : width / 2;
    const y = height - (p.count / maxCount) * (height - 12) - 4;
    return { x, y };
  });

  const linePath = coords
    .map((c, i) => `${i === 0 ? "M" : "L"}${c.x.toFixed(1)},${c.y.toFixed(1)}`)
    .join(" ");

  const first = coords[0]!;
  const last = coords[coords.length - 1]!;
  const areaPath = `${linePath} L${last.x.toFixed(1)},${height} L${first.x.toFixed(1)},${height} Z`;

  return { linePath, areaPath, maxCount };
}
