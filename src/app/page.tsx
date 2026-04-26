"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Search, History, ArrowRight, Loader2, AlertCircle, Sparkles, Database, Bot } from "lucide-react";
import axios from "axios";
import { useTexts } from "@/components/UITextsProvider";

const DC_GALLERY_URL_PATTERN =
  /^https?:\/\/gall\.dcinside\.com\/(mgallery\/|mini\/)?board\/(lists|view)\/?\?(?:[^"'<>]*[?&])?id=[a-zA-Z0-9_]+/;

const STEP_ICONS = [Search, Database, Bot, Sparkles];

export default function Home() {
  const router = useRouter();
  const t = useTexts();

  const [url, setUrl]             = useState("");
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState("");
  const [statusMsg, setStatusMsg] = useState("");

  const STEPS = [
    { icon: Search,   label: t["home.step1_label"], desc: t["home.step1_desc"] },
    { icon: Database, label: t["home.step2_label"], desc: t["home.step2_desc"] },
    { icon: Bot,      label: t["home.step3_label"], desc: t["home.step3_desc"] },
    { icon: Sparkles, label: t["home.step4_label"], desc: t["home.step4_desc"] },
  ];

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
    <main className="min-h-screen flex flex-col" style={{ backgroundColor: "var(--bg-base)" }}>

      {/* 상단 헤더 */}
      <header className="flex items-center justify-between px-6 py-4 border-b" style={{ borderColor: "var(--border)" }}>
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center">
            <Search size={14} className="text-white" />
          </div>
          <span className="font-bold text-sm tracking-wide" style={{ color: "var(--text-primary)" }}>
            DC-Thresher
          </span>
        </div>
        <button
          onClick={() => router.push("/history")}
          className="flex items-center gap-1.5 text-sm font-medium px-3 py-1.5 rounded-lg transition-colors"
          style={{ color: "var(--text-secondary)" }}
          onMouseEnter={e => (e.currentTarget.style.color = "var(--text-primary)")}
          onMouseLeave={e => (e.currentTarget.style.color = "var(--text-secondary)")}
        >
          <History size={15} />
          {t["home.nav_history"]}
        </button>
      </header>

      {/* 메인 컨텐츠 */}
      <div className="flex-1 flex flex-col items-center justify-center px-4 py-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="w-full max-w-2xl"
        >
          {/* 타이틀 */}
          <div className="text-center mb-10">
            <div
              className="inline-flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-full mb-6 border"
              style={{ backgroundColor: "rgba(99,102,241,0.1)", borderColor: "rgba(99,102,241,0.3)", color: "#818cf8" }}
            >
              <Sparkles size={12} />
              {t["home.badge"]}
            </div>
            <h1 className="text-4xl md:text-5xl font-black mb-4 leading-tight" style={{ color: "var(--text-primary)" }}>
              {t["home.title_line1"]}{" "}
              <span className="text-indigo-400">{t["home.title_accent"]}</span>
            </h1>
            <p className="text-base md:text-lg leading-relaxed max-w-lg mx-auto" style={{ color: "var(--text-secondary)" }}>
              {t["home.subtitle"]}
            </p>
          </div>

          {/* 입력 카드 */}
          <div
            className="rounded-2xl p-6 md:p-8 border mb-6"
            style={{ backgroundColor: "var(--bg-surface)", borderColor: "var(--border)" }}
          >
            <form onSubmit={handleAnalyze} className="space-y-4">
              <div>
                <label
                  htmlFor="url"
                  className="block text-sm font-semibold mb-2"
                  style={{ color: "var(--text-secondary)" }}
                >
                  {t["home.url_label"]}
                </label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Search size={16} style={{ color: "var(--text-muted)" }} />
                  </div>
                  <input
                    type="url"
                    id="url"
                    className="w-full pl-11 pr-4 py-3.5 rounded-xl text-sm outline-none transition-all border"
                    style={{
                      backgroundColor: "var(--bg-base)",
                      borderColor: "var(--border)",
                      color: "var(--text-primary)",
                    }}
                    placeholder={t["home.url_placeholder"]}
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    disabled={loading}
                    onFocus={e => (e.currentTarget.style.borderColor = "var(--accent)")}
                    onBlur={e => (e.currentTarget.style.borderColor = "var(--border)")}
                    required
                  />
                </div>
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
                    style={{ backgroundColor: "rgba(239,68,68,0.08)", borderColor: "rgba(239,68,68,0.25)", color: "#fca5a5" }}
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
                    style={{ backgroundColor: "rgba(99,102,241,0.08)", borderColor: "rgba(99,102,241,0.25)", color: "#a5b4fc" }}
                  >
                    {loading && <Loader2 size={14} className="animate-spin shrink-0" />}
                    {statusMsg}
                  </motion.div>
                )}
              </AnimatePresence>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3.5 px-6 rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all"
                style={{
                  background: loading ? "var(--bg-raised)" : "linear-gradient(135deg, #6366f1, #8b5cf6)",
                  color: loading ? "var(--text-muted)" : "#fff",
                  cursor: loading ? "not-allowed" : "pointer",
                }}
              >
                {loading ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    {t["home.submit_loading"]}
                  </>
                ) : (
                  <>
                    {t["home.submit_btn"]}
                    <ArrowRight size={16} />
                  </>
                )}
              </button>
            </form>
          </div>

          {/* 프로세스 스텝 */}
          <div className="grid grid-cols-4 gap-2">
            {STEPS.map((step, i) => {
              const Icon = STEP_ICONS[i];
              return (
                <div key={i} className="text-center">
                  <div
                    className="w-9 h-9 rounded-xl flex items-center justify-center mx-auto mb-2 border"
                    style={{ backgroundColor: "var(--bg-surface)", borderColor: "var(--border)" }}
                  >
                    <Icon size={16} style={{ color: "var(--accent-hover)" }} />
                  </div>
                  <p className="text-xs font-semibold mb-0.5" style={{ color: "var(--text-primary)" }}>{step.label}</p>
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>{step.desc}</p>
                </div>
              );
            })}
          </div>

          {/* 안내 */}
          <p className="text-center text-xs mt-6" style={{ color: "var(--text-muted)" }}>
            {t["home.footer_note"]}
          </p>
        </motion.div>
      </div>
    </main>
  );
}
