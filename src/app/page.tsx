"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Search, ArrowRight, Loader2, AlertCircle, ChevronRight, CheckCircle2, Clock, XCircle } from "lucide-react";
import axios from "axios";
import { useTexts } from "@/components/UITextsProvider";

const DC_GALLERY_URL_PATTERN =
  /^https?:\/\/gall\.dcinside\.com\/(mgallery\/|mini\/)?board\/(lists|view)\/?\?(?:[^"'<>]*[?&])?id=[a-zA-Z0-9_]+/;

const STATUS_CONFIG = {
  COMPLETED: { label: "분석 완료", icon: CheckCircle2, color: "#16A34A", bg: "#F0FDF4", border: "#BBF7D0" },
  PENDING:   { label: "진행 중",   icon: Clock,        color: "#D97706", bg: "#FFFBEB", border: "#FDE68A" },
  FAILED:    { label: "실패",      icon: XCircle,      color: "#DC2626", bg: "#FEF2F2", border: "#FECACA" },
} as const;

export default function Home() {
  const router = useRouter();
  const t = useTexts();

  const [url, setUrl]               = useState("");
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState("");
  const [statusMsg, setStatusMsg]   = useState("");
  const [focused, setFocused]       = useState(false);
  const [recentReports, setRecentReports] = useState<any[]>([]);

  useEffect(() => {
    const fetchReports = async () => {
      try {
        const res = await axios.get("/api/history");
        setRecentReports(res.data.reports?.slice(0, 6) || []);
      } catch {
        // ignore
      }
    };
    fetchReports();
    const interval = setInterval(fetchReports, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setStatusMsg("");

    const trimmed = url.trim();
    if (!trimmed) {
      setError(t["home.error_empty_url"]);
      return;
    }
    if (!DC_GALLERY_URL_PATTERN.test(trimmed)) {
      setError(t["home.error_invalid_url"]);
      return;
    }

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
    <main style={{ backgroundColor: "#F9F8F5", minHeight: "100vh" }}>

      {/* 히어로 */}
      <div className="flex flex-col items-center px-4 pt-20 pb-16">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
          className="w-full max-w-2xl"
        >
          {/* 브랜드 */}
          <div className="text-center mb-10">
            <div className="text-5xl mb-5 select-none">🚜</div>
            <h1
              className="text-4xl md:text-5xl font-black mb-3 leading-tight tracking-tight"
              style={{ color: "#18181B" }}
            >
              {t["home.title_line1"]}{" "}
              <span style={{ color: "#6366F1" }}>{t["home.title_accent"]}</span>
            </h1>
            <p className="text-base leading-relaxed max-w-md mx-auto" style={{ color: "#71717A" }}>
              {t["home.subtitle"]}
            </p>
          </div>

          {/* 입력 폼 */}
          <form onSubmit={handleAnalyze} className="space-y-3">
            <div
              className="flex items-center gap-2 p-2 rounded-2xl border-2 transition-all"
              style={{
                backgroundColor: "#FFFFFF",
                borderColor: focused ? "#6366F1" : "#E8E6E1",
              }}
            >
              <div className="flex items-center pl-3 shrink-0">
                <Search size={16} style={{ color: "#A1A1AA" }} />
              </div>
              <input
                type="url"
                id="url"
                className="flex-1 py-2.5 text-sm outline-none bg-transparent"
                style={{ color: "#18181B" }}
                placeholder={t["home.url_placeholder"]}
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                onFocus={() => setFocused(true)}
                onBlur={() => setFocused(false)}
                disabled={loading}
                required
              />
              <button
                type="submit"
                disabled={loading}
                className="shrink-0 flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm transition-all"
                style={{
                  backgroundColor: loading ? "#E4E4E7" : "#18181B",
                  color: loading ? "#A1A1AA" : "#FFFFFF",
                  cursor: loading ? "not-allowed" : "pointer",
                }}
              >
                {loading ? (
                  <>
                    <Loader2 size={14} className="animate-spin" />
                    {t["home.submit_loading"]}
                  </>
                ) : (
                  <>
                    {t["home.submit_btn"]}
                    <ArrowRight size={14} />
                  </>
                )}
              </button>
            </div>

            {/* 에러 / 상태 메시지 */}
            <AnimatePresence mode="wait">
              {error && (
                <motion.div
                  key="error"
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="flex items-start gap-2 text-sm px-4 py-3 rounded-xl border"
                  style={{ backgroundColor: "#FEF2F2", borderColor: "#FECACA", color: "#DC2626" }}
                >
                  <AlertCircle size={15} className="shrink-0 mt-0.5" />
                  {error}
                </motion.div>
              )}
              {statusMsg && !error && (
                <motion.div
                  key="status"
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="flex items-center gap-2 text-sm px-4 py-3 rounded-xl border"
                  style={{ backgroundColor: "#EEF2FF", borderColor: "#C7D2FE", color: "#4338CA" }}
                >
                  {loading && <Loader2 size={14} className="animate-spin shrink-0" />}
                  {statusMsg}
                </motion.div>
              )}
            </AnimatePresence>
          </form>

          <p className="text-center text-xs mt-4" style={{ color: "#A1A1AA" }}>
            {t["home.footer_note"]}
          </p>
        </motion.div>
      </div>

      {/* 최근 분석 리포트 */}
      {recentReports.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.15 }}
          className="max-w-2xl mx-auto px-4 pb-20"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold" style={{ color: "#18181B" }}>
              최근 분석
            </h2>
            <Link
              href="/history"
              className="flex items-center gap-0.5 text-xs font-medium transition-colors hover:opacity-70"
              style={{ color: "#71717A" }}
            >
              전체 보기
              <ChevronRight size={13} />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {recentReports.map((r, i) => {
              const status = r.status as keyof typeof STATUS_CONFIG;
              const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.PENDING;
              const Icon = cfg.icon;
              const name = r.gameName || r.galleryName || "분석 중...";

              return (
                <Link key={r.uuid ?? i} href={`/history/${r.uuid}`}>
                  <motion.div
                    whileHover={{ y: -2 }}
                    transition={{ duration: 0.15 }}
                    className="p-4 rounded-2xl border-2 bg-white transition-colors hover:border-indigo-300"
                    style={{ borderColor: "#E8E6E1" }}
                  >
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <span
                        className="font-bold text-sm leading-snug line-clamp-2"
                        style={{ color: "#18181B" }}
                      >
                        {name}
                      </span>
                      <span
                        className="shrink-0 flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-lg border"
                        style={{ backgroundColor: cfg.bg, borderColor: cfg.border, color: cfg.color }}
                      >
                        <Icon size={11} />
                        {cfg.label}
                      </span>
                    </div>
                    <p className="text-xs" style={{ color: "#A1A1AA" }}>
                      {new Date(r.requestedAt).toLocaleString("ko-KR", {
                        month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
                      })}
                    </p>
                  </motion.div>
                </Link>
              );
            })}
          </div>
        </motion.div>
      )}
    </main>
  );
}
