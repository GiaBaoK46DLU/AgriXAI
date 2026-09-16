// Server Component nào cũng nhận `searchParams` thẳng từ URL — người dùng gõ tay
// được, ví dụ đổi `?detail=14` thành `?detail=14,15` hoặc `?detail=abc`. Coi mọi
// giá trị dạng id trong URL là không đáng tin: lấy số hợp lệ ĐẦU TIÊN, phần còn lại
// (sau dấu phẩy, hoặc các giá trị lặp lại của cùng một key) vứt đi thay vì để
// `Number(...)` trả `NaN` rồi làm sập fetch/`.find()` phía sau.
export function firstIntParam(value: string | string[] | undefined): number | undefined {
  const raw = Array.isArray(value) ? value[0] : value;
  if (!raw) return undefined;
  const first = raw.split(",")[0]?.trim();
  if (!first) return undefined;
  const n = Number(first);
  return Number.isFinite(n) ? n : undefined;
}

// Bản dành cho id dạng chuỗi (ví dụ `disease_key`) — cùng lý do với
// `firstIntParam`: `?edit=early_blight,late_blight` chỉ lấy `early_blight`.
export function firstStringParam(value: string | string[] | undefined): string | undefined {
  const raw = Array.isArray(value) ? value[0] : value;
  if (!raw) return undefined;
  const first = raw.split(",")[0]?.trim();
  return first || undefined;
}
