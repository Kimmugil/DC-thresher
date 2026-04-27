"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft, Loader2, Calendar, AlertTriangle,
  CheckCircle2, Clock, Users, Database, FileText,
  ExternalLink, Tag, Flame, Info, Filter, Hash
} from "lucide-react";
import axios from "axios";
import { useTexts } from "@/components/UITextsProvider";

// ── Gemini 실제 출력 타입 ─────────────────────────────────────────
interface RelatedPost { title: string; url: string; }

interface PublicOpinion {
  opinion_title: string;
  opinion_summary: string;
  is_positive: boolean;
  related_posts?: RelatedPost[];
}

interface MajorIssue {
  issue_title: string;
  issue_category: string;
  issue_keywords?: string[];
  issue_summary: string;
  related_posts?: RelatedPost[];
}

interface ScrapeMeta {
  total_posts?: number;
  core_posts?: number;
  date_range?: string;
  max_comment_post?: { title: string; comment_count: number };
  min_comment_post?: { title: string; comment_count: number };
}

interface AiInsights {
  critic_one_liner?: string;
  top_keywords?: string[];
  public_opinions?: PublicOpinion[];
  major_issues?: MajorIssue[];
  game_name?: string;
  gallery_name?: string;
  scrape_meta?: ScrapeMeta;
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
  const opinions = insights?.public_opinions ?? [];
  const issues   = insights?.major_issues ?? [];
  const keywords = insights?.top_keywords ?? [];
  const meta     = insights?.scrape_meta;

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
      <header className="border-b py-10" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-surface)" }}>
        <div className="max-w-6xl mx-auto px-5">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
            className="flex flex-col gap-6">
            
            {/* 타이틀 영역 */}
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

            {/* 투명성 지표 (분석 대상, 분석 방법, 수집한 데이터) */}
            <div className="grid md:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl border flex flex-col gap-2" style={{ backgroundColor: "var(--bg-base)", borderColor: "var(--border)" }}>
                <div className="flex items-center gap-1.5 font-bold text-sm mb-1 text-indigo-400">
                  <Database size={16} /> 분석 대상
                </div>
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  <strong>수집 기간:</strong> {meta?.date_range || "알 수 없음"}
                </p>
                <p className="text-xs" style={{ color: "var(--text-secondary)" }}>
                  <strong>전체 게시글:</strong> {meta?.total_posts ? `${meta.total_posts.toLocaleString()}개` : "알 수 없음"}
                </p>
              </div>

              <div className="p-4 rounded-xl border flex flex-col gap-2" style={{ backgroundColor: "var(--bg-base)", borderColor: "var(--border)" }}>
                <div className="flex items-center gap-1.5 font-bold text-sm mb-1 text-emerald-400">
                  <Filter size={16} /> 분석 방법 (표본 추출)
                </div>
                <p className="text-xs leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                  전체 글 중 <strong>댓글 수 기준 상위 {meta?.core_posts || 100}개</strong>의 화제글만 선별하여 AI가 집중 분석했습니다. 단순 무작위 표본이 아닙니다.
                </p>
              </div>

              <div className="p-4 rounded-xl border flex flex-col gap-2" style={{ backgroundColor: "var(--bg-base)", borderColor: "var(--border)" }}>
                <div className="flex items-center gap-1.5 font-bold text-sm mb-1 text-amber-400">
                  <FileText size={16} /> 수집 표본 데이터 현황
                </div>
                <div className="text-xs space-y-1.5" style={{ color: "var(--text-secondary)" }}>
                  <p className="truncate" title={meta?.max_comment_post?.title}>
                    <strong>최고 댓글수:</strong> {meta?.max_comment_post?.comment_count}개 ({meta?.max_comment_post?.title})
                  </p>
                  <p className="truncate" title={meta?.min_comment_post?.title}>
                    <strong>최저 댓글수(커트라인):</strong> {meta?.min_comment_post?.comment_count}개 ({meta?.min_comment_post?.title})
                  </p>
                </div>
              </div>
            </div>

            {/* 한줄 요약 및 키워드 */}
            <div className="p-5 rounded-2xl border flex flex-col md:flex-row md:items-center justify-between gap-5"
              style={{ backgroundColor: "rgba(99,102,241,0.06)", borderColor: "rgba(99,102,241,0.2)" }}>
              <div className="flex-1">
                <p className="text-xs font-semibold mb-1.5 text-indigo-400">AI 한줄 요약</p>
                <p className="text-sm leading-relaxed" style={{ color: "var(--text-primary)" }}>
                  {insights?.critic_one_liner || "분석 결과가 없습니다."}
                </p>
              </div>
              
              {keywords.length > 0 && (
                <div className="shrink-0 flex flex-col gap-2 md:items-end">
                  <p className="text-[11px] font-semibold text-indigo-400">핵심 떡밥 키워드</p>
                  <div className="flex flex-wrap gap-1.5 md:justify-end">
                    {keywords.map((kw, i) => (
                      <span key={i} className="text-[11px] font-semibold px-2 py-0.5 rounded-full border"
                        style={{ backgroundColor: "var(--bg-base)", borderColor: "var(--border)", color: "var(--text-secondary)" }}>
                        #{kw}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

          </motion.div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-5 py-10 space-y-10">

        {/* 신뢰도 알림 박스 */}
        <div className="flex items-start gap-3 p-4 rounded-xl border"
          style={{ backgroundColor: "rgba(245,158,11,0.06)", borderColor: "rgba(245,158,11,0.2)" }}>
          <AlertTriangle size={18} className="text-amber-500 shrink-0 mt-0.5" />
          <p className="text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            이 리포트는 샘플링된 <strong>핵심 화제글(최대 {meta?.core_posts || 100}개)</strong>의 내용을 바탕으로 작성되었으며, 갤러리 전체의 의견을 100% 대변하지 않을 수 있습니다. 
            사실 확인을 위해 반드시 제공된 원문 링크를 참고하세요.
          </p>
        </div>

        {/* 주요 여론 리스트 */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <Users size={18} className="text-emerald-400" />
            <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>주요 여론 리스트</h2>
          </div>
          {opinions.length > 0 ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              {opinions.map((op, i) => (
                <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                  className="p-4 rounded-xl border flex flex-col h-full"
                  style={{ backgroundColor: "var(--bg-surface)", borderColor: "var(--border)" }}>
                  
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-base">{op.is_positive ? "🟢" : "🔴"}</span>
                    <span className="font-bold text-sm line-clamp-1" style={{ color: "var(--text-primary)" }} title={op.opinion_title}>
                      {op.opinion_title}
                    </span>
                  </div>
                  
                  <p className="text-xs leading-relaxed mb-4 flex-1" style={{ color: "var(--text-secondary)" }}>
                    {op.opinion_summary}
                  </p>

                  {op.related_posts && op.related_posts.length > 0 && (
                    <div className="mt-auto pt-3 border-t" style={{ borderColor: "var(--border)" }}>
                      <p className="text-[10px] font-semibold mb-1.5" style={{ color: "var(--text-muted)" }}>관련 게시글 레퍼런스</p>
                      <ul className="space-y-1">
                        {op.related_posts.map((post, j) => (
                          <li key={j} className="flex items-start gap-1">
                            <span className="text-[10px] text-indigo-400 mt-0.5">•</span>
                            <a href={post.url} target="_blank" rel="noopener noreferrer"
                              className="text-[11px] truncate hover:underline text-indigo-400 transition-colors"
                              title={post.title}>
                              {post.title}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          ) : (
            <Empty text="감지된 주요 여론이 없습니다." />
          )}
        </section>

        {/* 주요 이슈 리스트 */}
        <section>
          <div className="flex items-center gap-2 mb-4">
            <Flame size={18} className="text-orange-400" />
            <h2 className="text-lg font-bold" style={{ color: "var(--text-primary)" }}>주요 이슈 리스트</h2>
          </div>
          {issues.length > 0 ? (
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              {issues.map((issue, i) => (
                <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                  className="p-4 rounded-xl border flex flex-col h-full"
                  style={{ backgroundColor: "var(--bg-surface)", borderColor: "var(--border)" }}>
                  
                  <div className="flex flex-wrap items-center gap-1.5 mb-2">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded border"
                      style={{ backgroundColor: "rgba(245,158,11,0.1)", color: "#fbbf24", borderColor: "rgba(245,158,11,0.2)" }}>
                      {issue.issue_category}
                    </span>
                  </div>

                  <h3 className="font-bold text-sm mb-2" style={{ color: "var(--text-primary)" }}>
                    {issue.issue_title}
                  </h3>
                  
                  {issue.issue_keywords && issue.issue_keywords.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {issue.issue_keywords.map((kw, j) => (
                        <span key={j} className="text-[10px] text-orange-400/80 bg-orange-400/10 px-1.5 py-0.5 rounded">
                          {kw}
                        </span>
                      ))}
                    </div>
                  )}

                  <p className="text-xs leading-relaxed mb-4 flex-1" style={{ color: "var(--text-secondary)" }}>
                    {issue.issue_summary}
                  </p>

                  {issue.related_posts && issue.related_posts.length > 0 && (
                    <div className="mt-auto pt-3 border-t" style={{ borderColor: "var(--border)" }}>
                      <p className="text-[10px] font-semibold mb-1.5" style={{ color: "var(--text-muted)" }}>관련 게시글 레퍼런스</p>
                      <ul className="space-y-1">
                        {issue.related_posts.map((post, j) => (
                          <li key={j} className="flex items-start gap-1">
                            <span className="text-[10px] text-orange-400 mt-0.5">•</span>
                            <a href={post.url} target="_blank" rel="noopener noreferrer"
                              className="text-[11px] truncate hover:underline text-orange-400 transition-colors"
                              title={post.title}>
                              {post.title}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          ) : (
            <Empty text="감지된 주요 이슈가 없습니다." />
          )}
        </section>

        {/* 하단 메타 */}
        <div className="flex flex-wrap gap-4 text-xs px-5 py-4 rounded-xl border mt-10"
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

function Empty({ text }: { text: string }) {
  return (
    <div className="py-12 flex items-center justify-center rounded-xl border border-dashed" style={{ borderColor: "var(--border)" }}>
      <p className="text-sm" style={{ color: "var(--text-muted)" }}>{text}</p>
    </div>
  );
}
