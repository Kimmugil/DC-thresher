"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Archive, Settings } from "lucide-react";
import { useTexts } from "@/components/UITextsProvider";

export default function Navigation() {
  const pathname = usePathname();
  const t        = useTexts();

  const MAIN_LINKS = [
    { href: "/",        label: t["nav.home"],    icon: <Home    size={15} /> },
    { href: "/history", label: t["nav.history"], icon: <Archive size={15} /> },
  ];

  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <nav className="sticky top-0 z-50 bg-white border-b-2" style={{ borderColor: "#1A1A1A" }}>
      <div className="max-w-6xl mx-auto px-5 h-14 flex items-center justify-between">

        {/* 로고 + 메인 링크 */}
        <div className="flex items-center gap-6">
          <Link href="/" className="font-black text-lg flex items-center gap-2"
            style={{ color: "#1A1A1A" }}>
            🚜 <span className="hidden sm:inline">{t["nav.logo"]}</span>
          </Link>

          <div className="flex items-center gap-1">
            {MAIN_LINKS.map(({ href, label, icon }) => {
              const active = isActive(href);
              return (
                <Link
                  key={href}
                  href={href}
                  className="relative flex items-center gap-1.5 px-3 py-1 text-sm transition-colors"
                  style={{
                    color: active ? "#1A1A1A" : "#9CA3AF",
                    fontWeight: active ? 900 : 500,
                  }}
                  onMouseEnter={e => {
                    if (!active) (e.currentTarget as HTMLElement).style.color = "#4A4A4A";
                  }}
                  onMouseLeave={e => {
                    if (!active) (e.currentTarget as HTMLElement).style.color = "#9CA3AF";
                  }}
                >
                  {icon}
                  <span className="hidden md:inline">{label}</span>
                  {/* 활성 탭 노란 언더라인 */}
                  {active && (
                    <span
                      className="absolute bottom-0 left-0 right-0 h-0.5 rounded-full"
                      style={{ backgroundColor: "#FFD600", bottom: "-1px" }}
                    />
                  )}
                </Link>
              );
            })}
          </div>
        </div>

        {/* 관리자 — 우측, neo-button 규칙 동일 적용 */}
        <Link
          href="/admin"
          className="neo-button flex items-center gap-1.5 px-3 py-1.5 text-sm"
          style={{
            backgroundColor: isActive("/admin") ? "#1A1A1A" : "#F0EFEC",
            color:           isActive("/admin") ? "#FFFFFF"  : "#1A1A1A",
          }}
        >
          <Settings size={14} />
          <span className="hidden md:inline">{t["nav.admin"]}</span>
        </Link>

      </div>
    </nav>
  );
}
