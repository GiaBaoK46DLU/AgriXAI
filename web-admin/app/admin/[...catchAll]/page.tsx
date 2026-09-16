import { notFound } from "next/navigation";

// Next.js chỉ tự tìm tới `app/admin/not-found.tsx` (giữ nguyên sidebar/header) khi
// notFound() được gọi TỪ BÊN TRONG một route đã khớp — một URL /admin/* hoàn toàn
// không khớp route nào (gõ sai, ví dụ /admin/asdasd) thì Next.js không biết đường
// dẫn đó "thuộc" cây /admin/ nên rơi thẳng về not-found gốc (mất sidebar). Route
// catch-all này khớp MỌI đường dẫn con /admin/* chưa có trang riêng, rồi tự gọi
// notFound() để luôn rơi vào not-found.tsx trong thư mục admin/, không phải bản gốc.
export default function AdminCatchAll() {
  notFound();
}
