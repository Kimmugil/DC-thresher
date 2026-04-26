"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft, Loader2, Calendar, AlertTriangle,
  CheckCircle2, Clock, TrendingUp, TrendingDown,
  ExternalLink, Tag, Flame, BarChart2,
} from "lucide-react";
import axios from "axios";
import { useTexts } from "@/components/UITextsProvider";

// ── Gemini 실제 출력 타입 ─────────────────────────────────────────
interface SentimentItem { summary: string; ref_url: string }
interface MajorIssue {
  issue_title:   string;
  issue_detail:  string;
  mention_score: number;
  ref_url:       string;
}
interface ComplaintCategory {
  score:       number;
  summary:     string;
  example:     string;
  example_url: string;
}
interface AiInsights {
  critic_one_liner?: string;
  top_keywords?:     string[];
  sentiment_summary?: {
    positive?: SentimentItem[];
    negative?: SentimentItem[];
  };
  major_issues?:      MajorIssue[];
  complaint_analysis?: {
    balance?:   ComplaintCategory;
    operation?: ComplaintCategory;
    bug?:       ComplaintCategory;
    payment?:   ComplaintCategory;
    content?:   ComplaintCategory;
  };
  game_name?:    string;
  gallery_name?: string;
}

interface ReportData {
  uuid:         string;
  status:       "PENDING" | "COMPLETED" | "FAILED";
  galleryName?: string;
  gameName?:    string;
  requestedAt?: string;
  completedAt?: string;
  aiInsights?:  string;
}

// ── 상수 ──────────────────────────────────────────────────────────
const MAX_POLLS     = 60;
const POLL_INTERVAL = 10_000;

// ── 헬퍼 ──────────────────────────────────────────────────────────
function scoreColor(score: number, max = 10) {
  const ratio = score / max;
  if (ratio >= 0.7) return { text: "#fca5a5", bg: "rgba(239,68,68,0.12)",  border: "rgba(239,68,68,0.25)"  };
  if (ratio >= 0.4) return { text: "#fcd34d", bg: "rgba(245,158,11,0.12)", border: "rgba(245,158,11,0.25)" };
  return                   { text: "#a5b4fc", bg: "rgba(99,102,241,0.1)",  border: "rgba(99,102,241,0.2)"  };
}

function MentionBar({ score }: { score: number }) {
  const pct   = Math.min(100, Math.max(0, score));
  const color = pct >= 60 ? "#f87171" : pct >= 30 ? "#fbbf24" : "#818cf8";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: "var(--bg-raised)" }}>
        <motion.div
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        />
      </div>
      <span className="text-xs font-bold w-8 text-right" style={{ color }}>{pct}</span>
    </div>
  );
}

// ── 메인 컴포넌트 ─────────────────────────────────────────────────
export default function ReportPage() {
  const { uuid }  = useParams();
  const router    = useRouter();
  const t         = useTexts();
  const pollCount = useRef(0);

  const [report,   setReport]   = useState<ReportData | null>(null);
  const [insights, setInsights] = useState<AiInsights | null>(null);
  const [loading,  setLoading]  = useState(true);
  const [error,    setError]    = useState("");
  const [timedOut, setTimedOut] = useState(false);

  // 불만 카테고리 레이블 (텍스트 CMS에서 읽기)
  const COMPLAINT_META: Record<string, { label: string; emoji: string }> = {
    balance:   { label: t["report.complaint_balance"],   emoji: "⚖️"  },
    operation: { label: t["report.complaint_operation"], emoji: "📢"  },
    bug:       { label: t["report.complaint_bug"],       emoji: "🐛"  },
    payment:   { label: t["report.complaint_payment"],   emoji: "💳"  },
    content:   { label: t["report.complaint_content"],   emoji: "🎮"  },
  };

  useEffect(() => {
    if (!uuid) return;
    pollCount.current = 0;
    let cancelled = false;

    const poll = async () => {
      if (cancelled) return;
      try {
        const res  = await axios.get(`/api/history/${uuid}`);
        const data = res.data.report as ReportData;
        if (cancelled) return;

        setReport(data);

        if (data.status === "COMPLETED" || data.status === "FAILED") {
          if (data.aiInsights) {
            try { setInsights(JSON.parse(data.aiInsights)); } catch { /* ignore */ }
          }
          setLoading(false);
          return;
        }

        setLoading(false);
        pollCount.current += 1;
        if (pollCount.current >= MAX_POLLS) { setTimedOut(true); return; }
        setTimeout(poll, POLL_INTERVAL);

      } catch (err: unknown) {
        if (cancelled) return;
        const e = err as { response?: { status?: number } };
        setError(e.response?.status === 404
          ? t["report.error_not_found"]
          : t["report.error_generic"]);
        setLoading(false);
      }
    };

    poll();
    return () => { cancelled = true; };
  }, [uuid]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── 로딩 ────────────────────────────────────────────────────────
  if (loading && !report) return (
    <div className="min-h-screen flex flex-col items-center justify-center" style={{ backgroundColor: "var(--bg-base)" }}>
      <Loader2 size={36} className="animate-spin text-indigo-400 mb-3" />
      <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{t["report.loading_text"]}</p>
    </div>
  );

  // ── 오류 ────────────────────────────────────────────────────────
  if (error) return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4" style={{ backgroundColor: "var(--bg-base)" }}>
      <div className="text-center max-w-sm w-full p-8 rounded-2xl border" style={{ backgroundColor: "var(--bg-surface)", borderColor: "var(--border)" }}>
        <AlertTriangle size={40} className="text-red-400 mx-auto mb-4" />
        <h2 className="text-xl font-bold mb-2" style={{ color: "var(--text-primary)" }}>{t["report.error_title"]}</h2>
        <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>{error}</p>
        <button onClick={() => router.push("/history")}
          className="w-full py-2.5 rounded-xl text-sm font-semibold border"
          style={{ backgroundColor: "var(--bg-raised)", color: "var(--text-primary)", borderColor: "var(--border)" }}>
          {t["report.back_to_list"]}
        </button>
      </div>
    </div>
  );

  // ── PENDING ──────────────────────────────────────────────────────
  if (report?.status === "PENDING" || (!report?.status || (report.status !== "COMPLETED" && report.status !== "FAILED"))) return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4" style={{ backgroundColor: "var(--bg-base)" }}>
      <div className="text-center max-w-md w-full p-8 rounded-2xl border relative overflow-hidden"
        style={{ backgroundColor: "var(--bg-surface)", borderColor: "var(--border)" }}>
        <div className="absolute top-0 left-0 right-0 h-0.5 overflow-hidden" style={{ backgroundColor: "var(--bg-raised)" }}>
          <motion.div className="h-full bg-indigo-500"
            animate={{ x: ["-100%", "100%"] }}
            transition={{ repeat: Infinity, duration: 1.8, ease: "easeInOut" }} />
        </div>
        <div className="w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-5"
          style={{ backgroundColor: "rgba(99,102,241,0.1)" }}>
          <Loader2 size={28} className="animate-spin text-indigo-400" />
        </div>
        <h2 className="text-xl font-black mb-2" style={{ color: "var(--text-primary)" }}>{t["report.analyzing_title"]}</h2>
        <p className="text-sm mb-6 leading-relaxed" style={{ color: "var(--text-secondary)" }}>
          {t["report.analyzing_desc"]}
        </p>
        <div className="rounded-xl p-4 text-left space-y-2 border"
          style={{ backgroundColor: "var(--bg-base)", borderColor: "var(--border)" }}>
          <div className="flex justify-between text-xs">
            <span style={{ color: "var(--text-muted)" }}>{t["report.req_id_label"]}</span>
            <span className="font-mono" style={{ color: "var(--text-secondary)" }}>{String(uuid).slice(0, 8)}...</span>
          </div>
          <div className="flex justify-between text-xs">
            <span style={{ color: "var(--text-muted)" }}>{t["report.polling_label"]}</span>
            <span style={{ color: "var(--text-secondary)" }}>{pollCount.current} / {MAX_POLLS}회</span>
          </div>
        </div>
        {timedOut && (
          <p className="mt-4 text-xs text-red-400">{t["report.timeout_msg"]}</p>
        )}
      </div>
    </div>
  );

  // ── COMPLETED ─────────────────────────────────────────────────────
  const pos        = insights?.sentiment_summary?.positive ?? [];
  const neg        = insights?.sentiment_summary?.negative ?? [];
  const issues     = insights?.major_issues ?? [];
  const keywords   = insights?.top_keywords ?? [];
  const complaints = insights?.complaint_analysis ?? {};

  return (
    <main className="min-h-screen pb-20" style={{ backgroundColor: "var(--bg-base)" }}>

      {/* 네비게이션 */}
      <nav className="sticky top-0 z-10 flex items-center justify-between px-5 h-14 border-b backdrop-blur-md"
        style={{ backgroundColor: "rgba(13,17,23,0.9)", borderColor: "var(--border)" }}>
        <button onClick={() => router.push("/history")}
          className="flex items-center gap-1.5 text-sm font-medium transition-colors"
          style={{ color: "var(--text-secondary)" }}
          onMouseEnter={e => (e.currentTarget.style.color = "var(--text-primary)")}
          onMouseLeave={e => (e.currentTarget.style.color = "var(--text-secondary)")}>
          <ArrowLeft size={15} /> {t["report.back_btn"]}
        </button>
        <span className="font-bold text-sm hidden sm:block" style={{ color: "var(--text-primary)" }}>
          {report?.gameName || t["report.default_title"]}
        </span>
        <span className="font-mono text-xs" style={{ color: "var(--text-muted)" }}>
          {String(uuid).slice(0, 8)}
        </span>
      </nav>

      {/* 헤더 */}
      <header className="border-b py-10" style={{ borderColor: "var(--border)" }}>
        <div className="max-w-5xl mx-auto px-5">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
            className="flex flex-col md:flex-row items-start md:items-end justify-between gap-6">
            <div>
              <div className="flex items-center gap-2.5 mb-3">
                <span className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full border"
                  style={{ backgroundColor: "rgba(34,197,94,0.1)", borderColor: "rgba(34,197,94,0.25)", color: "#86efac" }}>
                  <CheckCircle2 size={10} /> {t["report.status_completed"]}
                </span>
                <span className="flex items-center gap-1 text-xs" style={{ color: "var(--text-muted)" }}>
                  <Calendar size={12} />
                  {report?.completedAt ? new Date(report.completedAt).toLocaleString("ko-KR") : "-"}
                </span>
              </div>
              <h1 className="text-3xl md:text-4xl font-black mb-1.5" style={{ color: "var(--text-primary)" }}>
                {report?.gameName || t["report.game_unknown"]}
              </h1>
              <p className="text-base font-medium" style={{ color: "var(--text-secondary)" }}>
                {report?.galleryName || ""}
              </p>
            </div>

            {/* 한줄 요약 */}
            {insights?.critic_one_liner && (
              <div className="rounded-2xl p-5 max-w-sm border"
                style={{ backgroundColor: "rgba(99,102,241,0.06)", borderColor: "rgba(99,102,241,0.2)" }}>
                <p className="text-xs font-semibold mb-1.5 text-indigo-400">{t["report.ai_summary_label"]}</p>
                <p className="text-sm leading-relaxed" style={{ color: "var(--text-primary)" }}>
                  {insights.critic_one_liner}
                </p>
              </div>
            )}
          </motion.div>

          {/* 키워드 태그 */}
          {keywords.length > 0 && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 }}
              className="flex flex-wrap gap-2 mt-5">
              <Tag size={13} style={{ color: "var(--text-muted)" }} className="self-center" />
              {keywords.map((kw, i) => (
                <span key={i} className="text-xs font-semibold px-2.5 py-1 rounded-full border"
                  style={{ backgroundColor: "var(--bg-raised)", borderColor: "var(--border)", color: "var(--text-secondary)" }}>
                  {kw}
                </span>
              ))}
            </motion.div>
          )}
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-5 py-8 space-y-6">

        {/* 긍정 / 부정 여론 */}
        <div className="grid md:grid-cols-2 gap-6">
          <Section icon={<TrendingUp size={15} className="text-emerald-400" />} title={t["report.section_positive"]}>
            {pos.length ? pos.map((item, i) => (
              <SentimentCard key={i} item={item} tone="positive" readOriginal={t["report.read_original"]} />
            )) : <Empty text={t["report.no_positive"]} />}
          </Section>

          <Section icon={<TrendingDown size={15} className="text-red-400" />} title={t["report.section_negative"]}>
            {neg.length ? neg.map((item, i) => (
              <SentimentCard key={i} item={item} tone="negative" readOriginal={t["report.read_original"]} />
            )) : <Empty text={t["report.no_negative"]} />}
          </Section>
        </div>

        {/* 주요 이슈 */}
        {issues.length > 0 && (
          <Section icon={<Flame size={15} className="text-orange-400" />} title={t["report.section_issues"]}>
            <div className="space-y-3">
              {issues.map((issue, i) => (
                <motion.div key={i} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.06 }}
                  className="p-4 rounded-xl border"
                  style={{ backgroundColor: "var(--bg-base)", borderColor: "var(--border)" }}>
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <span className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>
                      {issue.issue_title}
                    </span>
                    {issue.ref_url && (
                      <a href={issue.ref_url} target="_blank" rel="noopener noreferrer"
                        className="shrink-0 text-indigo-400 hover:text-indigo-300 transition-colors">
                        <ExternalLink size={13} />
                      </a>
                    )}
                  </div>
                  <p className="text-xs mb-3 leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                    {issue.issue_detail}
                  </p>
                  <div>
                    <p className="text-xs mb-1" style={{ color: "var(--text-muted)" }}>{t["report.mention_freq"]}</p>
                    <MentionBar score={issue.mention_score ?? 0} />
                  </div>
                </motion.div>
              ))}
            </div>
          </Section>
        )}

        {/* 불만 카테고리 */}
        {Object.keys(complaints).length > 0 && (
          <Section icon={<BarChart2 size={15} className="text-violet-400" />} title={t["report.section_complaints"]}>
            <div className="grid sm:grid-cols-2 gap-3">
              {(Object.entries(complaints) as [string, ComplaintCategory][]).map(([key, cat], i) => {
                const meta = COMPLAINT_META[key] ?? { label: key, emoji: "📌" };
                const sty  = scoreColor(cat.score ?? 0, 10);
                return (
                  <motion.div key={key} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.07 }}
                    className="p-4 rounded-xl border"
                    style={{ backgroundColor: sty.bg, borderColor: sty.border }}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-bold" style={{ color: "var(--text-primary)" }}>
                        {meta.emoji} {meta.label}
                      </span>
                      <span className="text-xs font-black px-2 py-0.5 rounded-full"
                        style={{ backgroundColor: sty.bg, color: sty.text, border: `1px solid ${sty.border}` }}>
                        {cat.score ?? 0}/10
                      </span>
                    </div>
                    {cat.summary && (
                      <p className="text-xs leading-relaxed mb-2" style={{ color: "var(--text-secondary)" }}>
                        {cat.summary}
                      </p>
                    )}
                    {cat.example && (
                      <div className="flex items-start gap-1.5">
                        <span className="text-xs shrink-0" style={{ color: "var(--text-muted)" }}>{t["report.complaint_example_label"]}</span>
                        <p className="text-xs italic leading-relaxed" style={{ color: "var(--text-muted)" }}>
                          &ldquo;{cat.example}&rdquo;
                          {cat.example_url && (
                            <a href={cat.example_url} target="_blank" rel="noopener noreferrer"
                              className="inline-block ml-1 text-indigo-400 hover:text-indigo-300">
                              <ExternalLink size={10} />
                            </a>
                          )}
                        </p>
                      </div>
                    )}
                  </motion.div>
                );
              })}
            </div>
          </Section>
        )}

        {/* 하단 메타 */}
        <div className="flex flex-wrap gap-4 text-xs px-5 py-4 rounded-xl border"
          style={{ backgroundColor: "var(--bg-surface)", borderColor: "var(--border)", color: "var(--text-muted)" }}>
          <span className="flex items-center gap-1">
            <Clock size={11} />
            {t["report.req_time"]}: {report?.requestedAt ? new Date(report.requestedAt).toLocaleString("ko-KR") : "-"}
          </span>
          <span className="flex items-center gap-1">
            <CheckCircle2 size={11} />
            {t["report.done_time"]}: {report?.completedAt ? new Date(report.completedAt).toLocaleString("ko-KR") : "-"}
          </span>
          <span className="font-mono">UUID: {String(uuid)}</span>
        </div>
      </div>
    </main>
  );
}

// ── 서브 컴포넌트 ──────────────────────────────────────────────────
function Section({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <AnimatePresence>
      <motion.section initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl border" style={{ backgroundColor: "var(--bg-surface)", borderColor: "var(--border)" }}>
        <div className="flex items-center gap-2 px-6 py-4 border-b" style={{ borderColor: "var(--border)" }}>
          {icon}
          <h2 className="font-bold text-sm" style={{ color: "var(--text-primary)" }}>{title}</h2>
        </div>
        <div className="p-4">{children}</div>
      </motion.section>
    </AnimatePresence>
  );
}

function SentimentCard({ item, tone, readOriginal }: {
  item:         SentimentItem;
  tone:         "positive" | "negative";
  readOriginal: string;
}) {
  const isPos = tone === "positive";
  return (
    <div className="flex items-start gap-3 p-3 rounded-xl border mb-2 last:mb-0"
      style={{
        backgroundColor: isPos ? "rgba(34,197,94,0.05)" : "rgba(239,68,68,0.05)",
        borderColor:      isPos ? "rgba(34,197,94,0.15)" : "rgba(239,68,68,0.15)",
      }}>
      <span className="text-base shrink-0 mt-0.5">{isPos ? "🟢" : "🔴"}</span>
      <div className="min-w-0">
        <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
          {item.summary}
        </p>
        {item.ref_url && (
          <a href={item.ref_url} target="_blank" rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-xs mt-1.5 text-indigo-400 hover:text-indigo-300 transition-colors">
            {readOriginal} <ExternalLink size={10} />
          </a>
        )}
      </div>
    </div>
  );
}

function Empty({ text }: { text: string }) {
  return (
    <p className="py-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>{text}</p>
  );
}
