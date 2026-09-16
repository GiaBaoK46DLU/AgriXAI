"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ComponentType, SVGProps } from "react";

import {
  DashboardIcon,
  DiseaseIcon,
  ForumIcon,
  HistoryIcon,
  MedicineIcon,
  PlotsIcon,
  UsersIcon,
  VideoIcon,
} from "@/components/icons";
import { Logo } from "@/components/Logo";

interface NavItem {
  href: string;
  label: string;
  icon: ComponentType<SVGProps<SVGSVGElement>>;
  // /admin cần so khớp tuyệt đối, các trang con so khớp theo tiền tố.
  exact?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { href: "/admin", label: "Tổng quan", icon: DashboardIcon, exact: true },
  { href: "/admin/users", label: "Người dùng", icon: UsersIcon },
  { href: "/admin/plots", label: "Lô đất", icon: PlotsIcon },
  { href: "/admin/diagnoses", label: "Lịch sử chẩn đoán", icon: HistoryIcon },
  { href: "/admin/diseases", label: "Danh mục bệnh", icon: DiseaseIcon },
  { href: "/admin/medicines", label: "Thuốc gợi ý", icon: MedicineIcon },
  { href: "/admin/guides", label: "Video hướng dẫn", icon: VideoIcon },
  { href: "/admin/forum", label: "Diễn đàn", icon: ForumIcon },
];

export function Sidebar({ adminName, adminEmail }: { adminName: string; adminEmail: string }) {
  const pathname = usePathname();

  return (
    <aside
      className="sticky top-0 flex h-screen w-64 shrink-0 flex-col gap-7 overflow-y-auto p-3.5"
      style={{ background: "linear-gradient(200deg, var(--color-primary), var(--color-primary-dark))" }}
    >
      <div className="flex items-center gap-2.5 px-2">
        <div className="flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-[10px] bg-white/18">
          <Logo size={19} colorA="#C3D24A" colorB="#FFFFFF" />
        </div>
        <div className="text-[17px] font-extrabold tracking-[-0.01em] text-white">
          AgriXAI <span className="text-xs font-semibold text-white/65">Admin</span>
        </div>
      </div>

      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map(({ href, label, icon: Icon, exact }) => {
          const active = exact ? pathname === href : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm font-semibold transition-colors ${
                active ? "bg-white text-primary-dark" : "text-white/85 hover:bg-white/12"
              }`}
            >
              <Icon />
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto flex flex-col gap-2">
        <Link
          href="/admin/account"
          className="flex items-center gap-2.5 rounded-xl bg-white/12 p-2.5 transition hover:bg-white/20"
        >
          <div className="h-[30px] w-[30px] shrink-0 rounded-full bg-olive" />
          <div className="min-w-0">
            <div className="truncate text-[13px] font-bold leading-tight text-white">
              {adminName}
            </div>
            <div className="truncate text-[11px] leading-tight text-white/65">{adminEmail}</div>
          </div>
        </Link>
      </div>
    </aside>
  );
}
