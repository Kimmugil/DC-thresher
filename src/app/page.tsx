"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Search, History, ArrowRight, Loader2, AlertCircle, Sparkles, Database, Bot } from "lucide-react";
import axios from "axios";

const DC_GALLERY_URL_PATTERN =
  /^https?:\/\/gall\.dcinside\.com\/(mgallery\/|mini\/)?board\/(lists|view)\/?\?[^"'<>]*[?&]id=[a-zA-Z0-9_]+/;

const STEPS = [
  { icon: Search,   label: "URL 입력",  desc: "갤러리 주소 붙여넣기" },
  { icon: Database, label: "자동 수집", desc: "최신 게시글 스크래핑" },
  { icon: Bot,      label: "AI 분석",   desc: "Gemini 여론 심층 분석" },
  { icon: Sparkles, label: "리포트",    desc: "결과 즉시 열람 가능" },
];

export default function Home() {
  const router = useRouter();
  const [url, setUrl]           = useState("");
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");
  const [statusMsg, setStatusMsg] = useState("");

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setStatusMsg("");

    const trimmed = url.trim();
    if (!trimmed) {
      setError("디시인사이드 갤러리 URL을 입력해주세요.");
      return;
    }
    if (!DC_GALLERY_URL_PATTERN.test(trimmed)) {
      setError("올바른 디시인사이드 갤러리 URL이 아닙니다. 주소창 URL을 그대로 붙여넣어 주세요.");
      return;
    }

    try {
      setLoading(true);
      setStatusMsg("분석 요청을 전송하는 중...");
      const res = await axios.post("/api/analyze", { url: trimmed });
      setStatusMsg("요청 완료! 분석 페이지로 이동합니다...");
      setTimeout(() => router.push(`/history/${res.data.uuid}`), 1200);
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { message?: string } } };
      setError(axiosError.response?.data?.message || "분석 요청에 실패했습니다. 잠시 후 다시 시도해주세요.");
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
          보관함
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
              Powered by Gemini 2.5 Flash
            </div>
            <h1 className="text-4xl md:text-5xl font-black mb-4 leading-tight" style={{ color: "var(--text-primary)" }}>
              갤러리 민심,{" "}
              <span className="text-indigo-400">AI가 읽다</span>
            </h1>
            <p className="text-base md:text-lg leading-relaxed max-w-lg mx-auto" style={{ color: "var(--text-secondary)" }}>
              DC Inside 갤러리 URL 하나로 게시글을 자동 수집하고,
              Gemini AI가 여론·불만·이슈를 심층 분석한 리포트를 발행합니다.
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
                  갤러리 URL
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
                    placeholder="https://gall.dcinside.com/mgallery/board/lists?id=..."
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
                    분석 준비 중...
                  </>
                ) : (
                  <>
                    리포트 발행 시작하기
                    <ArrowRight size={16} />
                  </>
                )}
              </button>
            </form>
          </div>

          {/* 프로세스 스텝 */}
          <div className="grid grid-cols-4 gap-2">
            {STEPS.map((step, i) => (
              <div key={i} className="text-center">
                <div
                  className="w-9 h-9 rounded-xl flex items-center justify-center mx-auto mb-2 border"
                  style={{ backgroundColor: "var(--bg-surface)", borderColor: "var(--border)" }}
                >
                  <step.icon size={16} style={{ color: "var(--accent-hover)" }} />
                </div>
                <p className="text-xs font-semibold mb-0.5" style={{ color: "var(--text-primary)" }}>{step.label}</p>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>{step.desc}</p>
              </div>
            ))}
          </div>

          {/* 안내 */}
          <p className="text-center text-xs mt-6" style={{ color: "var(--text-muted)" }}>
            마이너·정식·미니 갤러리 지원 &nbsp;·&nbsp; 분석 소요 약 1~3분 &nbsp;·&nbsp; 리포트는 고유 링크로 영구 보관
          </p>
        </motion.div>
      </div>
    </main>
  );
}
