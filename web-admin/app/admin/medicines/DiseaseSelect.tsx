"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";

import * as ui from "@/lib/ui";
import type { DiseaseInfo } from "@/lib/types";

/** Điều hướng NGAY khi đổi lựa chọn — không còn nút "Xem" tách rời. Bản cũ có
 * nút "Xem" riêng khiến người dùng đổi dropdown rồi bấm thẳng "Gán" mà quên
 * bấm "Xem" trước: form gán vẫn mang `disease_key` của bệnh CŨ (giá trị
 * server-render sẵn trong input ẩn), lưu nhầm thuốc sang bệnh khác mà không
 * báo lỗi gì — đúng lỗi "mọi bệnh dùng chung 1 link" từng gặp ở trang Video
 * hướng dẫn, chỉ khác chỗ biểu hiện. Auto-submit xoá hẳn khoảng hở đó: bệnh
 * hiển thị luôn khớp bệnh trong URL, form gán render lại theo đúng bệnh đang
 * xem, không có state trung gian nào để lệch. */
export function DiseaseSelect({ diseases, value }: { diseases: DiseaseInfo[]; value: string }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  function handleChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const params = new URLSearchParams(searchParams.toString());
    params.set("disease", e.target.value);
    params.set("tab", "assign");
    router.push(`${pathname}?${params.toString()}`);
  }

  return (
    <select defaultValue={value} onChange={handleChange} className={`${ui.select} w-auto`}>
      {diseases.map((d) => (
        <option key={d.key} value={d.key}>
          {d.name_vi}
        </option>
      ))}
    </select>
  );
}
