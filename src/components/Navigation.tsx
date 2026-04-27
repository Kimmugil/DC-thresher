"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Archive, BookOpen, Settings } from "lucide-react";

export default function Navigation() {
  const pathname = usePathname();

  const links = [
    { href: "/", label: "홈", icon: <Home size={16} /> },
    { href: "/history", label: "보관함", icon: <Archive size={16} /> },
    { href: "/guide", label: "분석 가이드", icon: <BookOpen size={16} /> },
    { href: "/admin", label: "관리자 패널", icon: <Settings size={16} /> },
  ];

  return (
    <nav className="sticky top-0 z-50 border-b backdrop-blur-md"
      style={{ backgroundColor: "rgba(13, 17, 23, 0.85)", borderColor: "var(--border)" }}>
      <div className="max-w-6xl mx-auto px-5 h-14 flex items-center justify-between">
        <Link href="/" className="font-black text-lg flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
          🚜 <span className="hidden sm:inline">DC 탈곡기</span>
        </Link>
        <div className="flex items-center gap-1 sm:gap-4 text-sm font-semibold">
          {links.map((link) => {
            const active = pathname === link.href || (link.href !== "/" && pathname.startsWith(link.href));
            return (
              <Link key={link.href} href={link.href}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg transition-colors ${
                  active ? "bg-indigo-500/10 text-indigo-400" : "hover:bg-white/5 text-gray-400 hover:text-gray-200"
                }`}>
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
