"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Archive, BookOpen, Settings } from "lucide-react";

export default function Navigation() {
  const pathname = usePathname();

  const links = [
    { href: "/",        label: "홈",         icon: <Home     size={16} /> },
    { href: "/history", label: "보관함",     icon: <Archive  size={16} /> },
    { href: "/guide",   label: "분석 가이드", icon: <BookOpen size={16} /> },
    { href: "/admin",   label: "관리자",     icon: <Settings size={16} /> },
  ];

  return (
    <nav
      className="sticky top-0 z-50 bg-white border-b-2"
      style={{ borderColor: "#1A1A1A" }}
    >
      <div className="max-w-6xl mx-auto px-5 h-14 flex items-center justify-between">
        <Link
          href="/"
          className="font-black text-lg flex items-center gap-2"
          style={{ color: "#1A1A1A" }}
        >
          🚜 <span className="hidden sm:inline">DC 탈곡기</span>
        </Link>

        <div className="flex items-center gap-1 sm:gap-1.5 text-sm font-bold">
          {links.map((link) => {
            const active =
              pathname === link.href ||
              (link.href !== "/" && pathname.startsWith(link.href));
            return (
              <Link
                key={link.href}
                href={link.href}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border-2 transition-all"
                style={{
                  backgroundColor: active ? "#FFD600" : "transparent",
                  borderColor: active ? "#1A1A1A" : "transparent",
                  color: "#1A1A1A",
                  boxShadow: active ? "2px 2px 0px 0px #1A1A1A" : "none",
                }}
                onMouseEnter={e => {
                  if (!active) {
                    (e.currentTarget as HTMLElement).style.backgroundColor = "#F0EFEC";
                    (e.currentTarget as HTMLElement).style.borderColor = "#1A1A1A";
                  }
                }}
                onMouseLeave={e => {
                  if (!active) {
                    (e.currentTarget as HTMLElement).style.backgroundColor = "transparent";
                    (e.currentTarget as HTMLElement).style.borderColor = "transparent";
                  }
                }}
              >
                {link.icon}
                <span className="hidden md:inline">{link.label}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
