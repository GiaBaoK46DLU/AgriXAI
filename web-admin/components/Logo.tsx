/** Logo "lá hai tông" của app mobile, chép nguyên path SVG từ
 * `mobile/lib/widgets/agri_icons.dart` (`AgriIcons.leaf`) để web admin dùng
 * đúng một biểu tượng thương hiệu với app — không phải icon mới tự vẽ. */
export function Logo({
  size = 24,
  colorA = "#C3D24A", // AgriColors.olive
  colorB = "#F1F6EF", // AgriColors.cream
}: {
  size?: number;
  colorA?: string;
  colorB?: string;
}) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 22C12 13 16 4 22 2c0 10-4 18-10 20Z" fill={colorA} />
      <path d="M12 22C12 14 8 6 2 5c0 9 4 16 10 17Z" fill={colorB} />
    </svg>
  );
}
