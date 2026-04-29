"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Search, ArrowRight, Loader2, AlertCircle, ChevronRight, CheckCircle2, Clock, XCircle, Flame } from "lucide-react";
import axios from "axios";
import { useTexts } from "@/components/UITextsProvider";

const DC_GALLERY_URL_PATTERN =
  /^https?:\/\/gall\.dcinside\.com\/(mgallery\/|mini\/)?board\/(lists|view)\/?\?(?:[^"'<>]*[?&])?id=[a-zA-Z0-9_]+/;

const STATUS_CONFIG = {
  COMPLETED: { label: "분석 완료", icon: CheckCircle2, color: "#166534", bg: "#56D0A0" },
  PENDING:   { label: "진행 중",   icon: Clock,        color: "#1A1A1A", bg: "#FFD600" },
  FAILED:    { label: "실패",      icon: XCircle,      color: "#FFFFFF", bg: "#FF6B6B" },
} as const;

const CARD_ROTATIONS = [1.2, -1.0, 0.8, -1.5, 1.0, -0.8];

// 최근 완료 갤러리를 순환하는 롤링 텍스트
function RollingGalleryName({ names }: { names: string[] }) {
  const [idx, setIdx] = useState(0);
  useEffect(() => {
    if (names.length < 2) return;
    const t = setInterval(() => setIdx(i => (i + 1) % names.length), 2200);
    return () => clearInterval(t);
  }, [names.length]);

  if (names.length === 0) return null;

  return (
    <div className="inline-flex items-center gap-2 overflow-hidden">
      <span className="text-sm font-semibold" style={{ color: "#9CA3AF" }}>방금 탈곡된 갤러리:</span>
      <div className="relative h-6 overflow-hidden" style={{ minWidth: 120 }}>
        <AnimatePresence mode="wait">
          <motion.span
            key={idx}
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0,  opacity: 1 }}
            exit={{ y: -20, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="absolute text-sm font-black whitespace-nowrap"
            style={{ color: "#1A1A1A" }}
          >
            {names[idx]}
          </motion.span>
        </AnimatePresence>
      </div>
    </div>
  );
}

export default function Home() {
  const router = useRouter();
  const t = useTexts();

  const [url, setUrl]             = useState("");
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState("");
  const [statusMsg, setStatusMsg] = useState("");
  const [recentReports, setRecentReports] = useState<any[]>([]);

  const pendingReports = recentReports.filter(r => r.status === "PENDING");
  const doneReports    = recentReports.filter(r => r.status !== "PENDING").slice(0, 6);

  const completedNames = recentReports
    .filter(r => r.status === "COMPLETED" && (r.gameName || r.galleryName))
    .map(r => r.gameName || r.galleryName);

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await axios.get("/api/history");
        setRecentReports(res.data.reports?.slice(0, 12) || []);
      } catch { /* ignore */ }
    };
    fetch();
    const iv = setInterval(fetch, 10000);
    return () => clearInterval(iv);
  }, []);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setStatusMsg("");
    const trimmed = url.trim();
    if (!trimmed) { setError(t["home.error_empty_url"]); return; }
    if (!DC_GALLERY_URL_PATTERN.test(trimmed)) { setError(t["home.error_invalid_url"]); return; }
    try {
      setLoading(true);
      setStatusMsg(t["home.status_sending"]);
      const res = await axios.post("/api/analyze", { url: trimmed });
      setStatusMsg(t["home.status_redirecting"]);
      setTimeout(() => router.push(`/history/${res.data.uuid}`), 1200);
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { message?: string } } };
      setError(axiosError.response?.data?.message || t["home.error_generic"]);
      setLoading(false);
    }
  };

  return (
    <main style={{ backgroundColor: "#FAFAFA", minHeight: "100vh" }}>

      {/* ── 히어로 ─────────────────────────────────────────────── */}
      <section className="flex flex-col items-center px-4 pt-16 pb-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="w-full max-w-2xl text-center"
        >
          {/* 타이틀 */}
          <h1
            className="text-5xl md:text-6xl font-black mb-4 leading-tight tracking-tight"
            style={{ color: "#1A1A1A" }}
          >
            {t["home.title_line1"]}<br />
            <span
              className="px-2 inline-block"
              style={{ backgroundColor: "#FFD600" }}
            >
              {t["home.title_accent"]}
            </span>
          </h1>

          <p className="text-base mb-3" style={{ color: "#4A4A4A" }}>
            {t["home.subtitle"]}
          </p>

          <div className="mb-8">
            <RollingGalleryName names={completedNames} />
          </div>

          {/* 입력 폼 */}
          <form onSubmit={handleAnalyze} className="space-y-3">
            <div className="neo-input-wrap">
              <Search size={18} className="ml-2 shrink-0" style={{ color: "#9CA3AF" }} />
              <input
                type="url"
                id="url"
                className="flex-1 py-3 text-sm outline-none bg-transparent"
                style={{ color: "#1A1A1A" }}
                placeholder={t["home.url_placeholder"]}
                value={url}
                onChange={e => setUrl(e.target.value)}
                disabled={loading}
                required
              />
              <button
                type="submit"
                disabled={loading}
                className="neo-button shrink-0 flex items-center gap-2 px-6 py-2.5 text-sm"
                style={{
                  backgroundColor: loading ? "#E2E8F0" : "#FFD600",
                  color: "#1A1A1A",
                }}
              >
                {loading ? (
                  <><Loader2 size={14} className="animate-spin" />{t["home.submit_loading"]}</>
                ) : (
                  <>{t["home.submit_btn"]}<ArrowRight size={14} /></>
                )}
              </button>
            </div>

            {/* 에러 / 상태 */}
            <AnimatePresence mode="wait">
              {error && (
                <motion.div key="error"
                  initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                  className="flex items-start gap-2 text-sm px-4 py-3 rounded-xl border-2"
                  style={{ backgroundColor: "#FFF5F5", borderColor: "#FF6B6B", color: "#C0392B" }}>
                  <AlertCircle size={15} className="shrink-0 mt-0.5" />{error}
                </motion.div>
              )}
              {statusMsg && !error && (
                <motion.div key="status"
                  initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                  className="flex items-center gap-2 text-sm px-4 py-3 rounded-xl border-2"
                  style={{ backgroundColor: "#FFFDE7", borderColor: "#FFD600", color: "#1A1A1A" }}>
                  {loading && <Loader2 size={14} className="animate-spin shrink-0" />}{statusMsg}
                </motion.div>
              )}
            </AnimatePresence>
          </form>

          <p className="text-xs mt-4" style={{ color: "#9CA3AF" }}>
            {t["home.footer_note"]}
          </p>
        </motion.div>
      </section>

      {/* ── 탈곡 진행 중 배너 ───────────────────────────────────── */}
      {pendingReports.length > 0 && (
        <section className="max-w-2xl mx-auto px-4 pb-4">
          <div className="flex items-center gap-2 mb-3">
            <Flame size={15} style={{ color: "#1A1A1A" }} />
            <h2 className="text-base font-black" style={{ color: "#1A1A1A" }}>탈곡 진행 중</h2>
          </div>
          <div className="space-y-2">
            {pendingReports.map(r => (
              <Link key={r.uuid} href={`/history/${r.uuid}`}>
                <motion.div
                  initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }}
                  className="flex items-center gap-4 px-5 py-4 rounded-2xl border-2 cursor-pointer"
                  style={{ borderColor: "#1A1A1A", backgroundColor: "#FFFDE7" }}
                  whileHover={{ backgroundColor: "#FFF9C4" }}
                  transition={{ duration: 0.15 }}
                >
                  <Loader2 size={20} className="animate-spin shrink-0" style={{ color: "#1A1A1A" }} />
                  <div className="flex-1 min-w-0">
                    <p className="font-black text-sm truncate" style={{ color: "#1A1A1A" }}>
                      {r.gameName || r.galleryName || "분석 준비 중..."}
                    </p>
                    <p className="text-xs mt-0.5" style={{ color: "#9CA3AF" }}>
                      {r.requestedAt
                        ? new Date(r.requestedAt).toLocaleString("ko-KR", {
                            month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
                          })
                        : "방금 요청됨"}
                    </p>
                  </div>
                  <span className="flex items-center gap-1 text-xs font-bold shrink-0"
                    style={{ color: "#1A1A1A" }}>
                    결과 보기 <ChevronRight size={13} />
                  </span>
                </motion.div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* ── 최근 분석 카드 ──────────────────────────────────────── */}
      {doneReports.length > 0 && (
        <section className="max-w-2xl mx-auto px-4 pb-20">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-base font-black" style={{ color: "#1A1A1A" }}>최근 분석</h2>
            <Link href="/history"
              className="flex items-center gap-0.5 text-xs font-bold border-b-2 pb-0.5 transition-colors hover:opacity-70"
              style={{ borderColor: "#1A1A1A", color: "#1A1A1A" }}>
              전체 보기 <ChevronRight size={13} />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5">
            {doneReports.map((r, i) => {
              const status = r.status as keyof typeof STATUS_CONFIG;
              const cfg    = STATUS_CONFIG[status] ?? STATUS_CONFIG.COMPLETED;
              const Icon   = cfg.icon;
              const name   = r.gameName || r.galleryName || "-";
              const rot    = CARD_ROTATIONS[i % CARD_ROTATIONS.length];

              return (
                <Link key={r.uuid ?? i} href={`/history/${r.uuid}`}>
                  <motion.div
                    style={{ rotate: rot }}
                    whileHover={{ rotate: 0, y: -4 }}
                    transition={{ type: "spring", stiffness: 300, damping: 20 }}
                    className="neo-card p-4 cursor-pointer"
                  >
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <span className="font-black text-sm leading-snug line-clamp-2"
                        style={{ color: "#1A1A1A" }}>{name}</span>
                      <span
                        className="shrink-0 flex items-center gap-1 text-[11px] font-bold px-2 py-1 rounded-full border-2"
                        style={{ backgroundColor: cfg.bg, borderColor: "#1A1A1A", color: cfg.color }}>
                        <Icon size={10} />{cfg.label}
                      </span>
                    </div>
                    <p className="text-xs" style={{ color: "#9CA3AF" }}>
                      {new Date(r.requestedAt).toLocaleString("ko-KR", {
                        month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
                      })}
                    </p>
                  </motion.div>
                </Link>
              );
            })}
          </div>
        </section>
      )}
    </main>
  );
}
