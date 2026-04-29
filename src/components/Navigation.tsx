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
      className="sticky top-0 z-50 border-b backdrop-blur-md"
      style={{ backgroundColor: "rgba(249,248,245,0.9)", borderColor: "var(--border)" }}
    >
      <div className="max-w-6xl mx-auto px-5 h-14 flex items-center justify-between">
        <Link
          href="/"
          className="font-black text-lg flex items-center gap-2"
          style={{ color: "var(--text-primary)" }}
        >
          🚜 <span className="hidden sm:inline">DC 탈곡기</span>
        </Link>

        <div className="flex items-center gap-1 sm:gap-2 text-sm font-semibold">
          {links.map((link) => {
            const active = pathname === link.href || (link.href !== "/" && pathname.startsWith(link.href));
            return (
              <Link
                key={link.href}
                href={link.href}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-colors"
                style={{
                  backgroundColor: active ? "#EEF2FF" : "transparent",
                  color: active ? "#4338CA" : "var(--text-secondary)",
                }}
                onMouseEnter={e => { if (!active) (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-raised)"; }}
                onMouseLeave={e => { if (!active) (e.currentTarget as HTMLElement).style.backgroundColor = "transparent"; }}
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
