"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  ArrowLeft, Loader2, Calendar, AlertTriangle,
  CheckCircle2, Clock, Database,
  Flame, ExternalLink, BarChart2, MessageSquare,
} from "lucide-react";
import axios from "axios";
import { useTexts } from "@/components/UITextsProvider";

interface RelatedPost { title: string; url: string; }
interface TopPost {
  title:         string;
  url:           string;
  comment_count: number;
  date:          string;
  related_issue: string | null;
}
interface MajorIssue {
  issue_title:      string;
  issue_category:   string;
  issue_keywords?:  string[];
  issue_summary:    string;
  heat_score?:      number;
  sentiment_ratio?: { positive: number; negative: number };
  positive_posts?:  RelatedPost[];
  negative_posts?:  RelatedPost[];
}
interface ScrapeMeta {
  total_posts?:       number;
  core_posts?:        number;
  date_range?:        string;
  date_counts?:       Record<string, number>;
  max_comment_post?:  { title: string; comment_count: number; url?: string };
  min_comment_post?:  { title: string; comment_count: number; url?: string };
}
interface AiInsights {
  critic_one_liner?:   string;
  top_keywords?:       string[];
  overall_sentiment?:  { positive: number; negative: number };
  major_issues?:       MajorIssue[];
  top_posts?:          TopPost[];
  scrape_meta?:        ScrapeMeta;
}
interface ReportData {
  uuid:          string;
  status:        "PENDING" | "COMPLETED" | "FAILED";
  galleryName?:  string;
  gameName?:     string;
  requestedAt?:  string;
  completedAt?:  string;
  aiInsights?:   string;
}

const MAX_POLLS     = 60;
const POLL_INTERVAL = 10_000;

function extractGalleryUrl(insights: AiInsights | null): string | null {
  const allPosts = insights?.major_issues?.flatMap(i => [
    ...(i.positive_posts ?? []),
    ...(i.negative_posts ?? []),
  ]) ?? [];
  const firstUrl = allPosts.find(p => p.url)?.url;
  if (!firstUrl) return null;
  try {
    const u = new URL(firstUrl);
    const id = u.searchParams.get("id");
    if (!id) return null;
    const prefix = u.pathname.includes("/mgallery/") ? "mgallery/"
      : u.pathname.includes("/mini/") ? "mini/" : "";
    return `https://gall.dcinside.com/${prefix}board/lists/?id=${id}`;
  } catch { return null; }
}

export default function ReportPage() {
  const { uuid } = useParams();
  const router   = useRouter();
  const t        = useTexts();
  const pollCount = useRef(0);

  const [report,          setReport]         = useState<ReportData | null>(null);
  const [insights,        setInsights]       = useState<AiInsights | null>(null);
  const [loading,         setLoading]        = useState(true);
  const [error,           setError]          = useState("");
  const [timedOut,        setTimedOut]       = useState(false);
  const [showPeriodModal, setShowPeriodModal] = useState(false);

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
        setError(e.response?.status === 404 ? t["report.error_not_found"] : t["report.error_generic"]);
        setLoading(false);
      }
    };
    poll();
    return () => { cancelled = true; };
  }, [uuid]); // eslint-disable-line react-hooks/exhaustive-deps

  /* ── 로딩 ─────────────────────────────────────────── */
  if (loading && !report) return (
    <div className="min-h-screen flex flex-col items-center justify-center" style={{ backgroundColor: "#FAFAFA" }}>
      <Loader2 size={36} className="animate-spin mb-3" style={{ color: "#1A1A1A" }} />
      <p className="text-sm font-bold" style={{ color: "#4A4A4A" }}>{t["report.loading_text"]}</p>
    </div>
  );

  /* ── 오류 ─────────────────────────────────────────── */
  if (error) return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4" style={{ backgroundColor: "#FAFAFA" }}>
      <div className="text-center max-w-sm w-full p-8 neo-card">
        <AlertTriangle size={40} className="mx-auto mb-4" style={{ color: "#FF6B6B" }} />
        <h2 className="text-xl font-black mb-2">{t["report.error_title"]}</h2>
        <p className="text-sm mb-6" style={{ color: "#4A4A4A" }}>{error}</p>
        <button onClick={() => router.push("/history")}
          className="neo-button w-full py-2.5 text-sm"
          style={{ backgroundColor: "#FFD600", color: "#1A1A1A" }}>
          {t["report.back_to_list"]}
        </button>
      </div>
    </div>
  );

  /* ── PENDING ──────────────────────────────────────── */
  if (!report || (report.status !== "COMPLETED" && report.status !== "FAILED")) return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4" style={{ backgroundColor: "#FAFAFA" }}>
      <div className="text-center max-w-md w-full p-8 neo-card relative overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-1 overflow-hidden bg-gray-100">
          <motion.div className="h-full" style={{ backgroundColor: "#FFD600" }}
            animate={{ x: ["-100%", "100%"] }}
            transition={{ repeat: Infinity, duration: 1.8, ease: "easeInOut" }} />
        </div>
        <div className="w-14 h-14 rounded-2xl border-2 flex items-center justify-center mx-auto mb-5"
          style={{ backgroundColor: "#FFFDE7", borderColor: "#1A1A1A" }}>
          <Loader2 size={28} className="animate-spin" style={{ color: "#1A1A1A" }} />
        </div>
        <h2 className="text-xl font-black mb-2">{t["report.analyzing_title"]}</h2>
        <p className="text-sm mb-6 leading-relaxed" style={{ color: "#4A4A4A" }}>
          {t["report.analyzing_desc"]}
        </p>
        <div className="rounded-xl p-4 text-left space-y-2 border-2"
          style={{ backgroundColor: "#FAFAFA", borderColor: "#E2E8F0" }}>
          <div className="flex justify-between text-sm">
            <span style={{ color: "#9CA3AF" }}>{t["report.req_id_label"]}</span>
            <span className="font-mono font-bold">{String(uuid).slice(0, 8)}...</span>
          </div>
          <div className="flex justify-between text-sm">
            <span style={{ color: "#9CA3AF" }}>{t["report.polling_label"]}</span>
            <span className="font-bold">{pollCount.current} / {MAX_POLLS}회</span>
          </div>
        </div>
        {timedOut && <p className="mt-4 text-sm font-bold" style={{ color: "#FF6B6B" }}>{t["report.timeout_msg"]}</p>}
        <div className="mt-6">
          <button onClick={() => router.push("/")}
            className="neo-button w-full py-2.5 text-sm"
            style={{ backgroundColor: "#F0EFEC", color: "#1A1A1A" }}>
            {t["report.home_btn"]}
          </button>
        </div>
      </div>
    </div>
  );

  /* ── COMPLETED ────────────────────────────────────── */
  const issues     = insights?.major_issues ?? [];
  const keywords   = insights?.top_keywords ?? [];
  const meta       = insights?.scrape_meta;
  const galleryUrl = extractGalleryUrl(insights);

  const periodRows = [
    { cond: t["report.period_row1_cond"], period: t["report.period_row1_period"] },
    { cond: t["report.period_row2_cond"], period: t["report.period_row2_period"] },
    { cond: t["report.period_row3_cond"], period: t["report.period_row3_period"] },
  ];

  return (
    <main style={{ backgroundColor: "#FAFAFA", minHeight: "100vh", paddingBottom: 80 }}>

      {/* ── 액션바 ────────────────────────────────────── */}
      <div className="flex items-center justify-between px-5 h-14 border-b-2 bg-white"
        style={{ borderColor: "#1A1A1A" }}>
        <button onClick={() => router.push("/history")}
          className="flex items-center gap-1.5 text-sm font-bold transition-opacity hover:opacity-60"
          style={{ color: "#1A1A1A" }}>
          <ArrowLeft size={15} /> {t["report.back_btn"]}
        </button>
        <span className="font-black text-sm hidden sm:block" style={{ color: "#1A1A1A" }}>
          {report?.gameName || t["report.default_title"]}
        </span>
        <span className="font-mono text-xs" style={{ color: "#9CA3AF" }}>
          {String(uuid).slice(0, 8)}
        </span>
      </div>

      {/* ── 리포트 헤더 ───────────────────────────────── */}
      <header className="border-b-2 py-10 bg-white" style={{ borderColor: "#1A1A1A" }}>
        <div className="max-w-6xl mx-auto px-5">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
            className="flex flex-col gap-5">

            {/* ① 타이틀 블록 */}
            <div>
              {/* 분석 완료 시점 — 뱃지 없이 작은 회색 텍스트만 */}
              {report?.completedAt && (
                <p className="flex items-center gap-1 text-xs mb-3" style={{ color: "#9CA3AF" }}>
                  <Calendar size={11} />
                  <span>{t["report.completed_at_label"]}</span>
                  <span>{new Date(report.completedAt).toLocaleString("ko-KR")}</span>
                </p>
              )}

              {/* 게임명 h1 */}
              <h1 className="text-3xl md:text-4xl font-black mb-2" style={{ color: "#1A1A1A" }}>
                {report?.gameName || t["report.game_unknown"]}
              </h1>

              {/* 갤러리명 — 게임명과 다를 때만 표시 */}
              <div className="flex items-center gap-3 flex-wrap">
                {report?.galleryName && report.galleryName !== report.gameName && (
                  <p className="text-base font-bold" style={{ color: "#4A4A4A" }}>
                    {report.galleryName}
                  </p>
                )}
                {galleryUrl && (
                  <a href={galleryUrl} target="_blank" rel="noopener noreferrer"
                    className="neo-button inline-flex items-center gap-1.5 px-3 py-1.5"
                    style={{ backgroundColor: "#F0EFEC", color: "#1A1A1A", fontSize: 12 }}>
                    <ExternalLink size={11} /> {t["report.gallery_link_btn"]}
                  </a>
                )}
              </div>
            </div>

            {/* ② AI 한줄 요약 — 흰 카드 + 텍스트 노란 하이라이트 */}
            <div className="neo-card neo-card-static p-5">
              <p className="text-xs font-black mb-2 uppercase tracking-widest" style={{ color: "#9CA3AF" }}>
                {t["report.ai_summary_label"]}
              </p>
              <p className="text-lg font-black leading-snug" style={{ color: "#1A1A1A" }}>
                <span style={{ backgroundColor: "#FFD600", padding: "2px 4px", lineHeight: 1.6 }}>
                  {insights?.critic_one_liner || t["report.no_summary"]}
                </span>
              </p>
            </div>

            {/* ③ 키워드 배지 — 한줄 요약 바로 아래 */}
            {keywords.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {keywords.map((kw, i) => (
                  <span key={i}
                    className="text-sm px-4 py-1.5 font-black rounded-full border-2"
                    style={{ borderColor: "#1A1A1A", backgroundColor: "#FFFFFF", color: "#1A1A1A" }}
                  >
                    #{kw}
                  </span>
                ))}
              </div>
            )}

            {/* ④ 분석 메타 — 작은 회색 텍스트 한 줄 (카드 대신) */}
            {meta && (
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs" style={{ color: "#9CA3AF" }}>
                <span className="flex items-center gap-1">
                  <Database size={11} />
                  {t["report.collection_period_label"]} <span className="font-semibold">{meta.date_range || "–"}</span>
                  <button
                    onClick={() => setShowPeriodModal(true)}
                    className="inline-flex items-center justify-center w-3.5 h-3.5 rounded-full border text-[9px] font-black transition-colors"
                    style={{ borderColor: "#C8C8C8", color: "#C8C8C8", lineHeight: 1 }}
                    onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = "#1A1A1A"; (e.currentTarget as HTMLElement).style.color = "#1A1A1A"; }}
                    onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = "#C8C8C8"; (e.currentTarget as HTMLElement).style.color = "#C8C8C8"; }}
                  >?</button>
                </span>
                <span>·</span>
                <span>전체 {meta.total_posts?.toLocaleString() ?? "?"}개</span>
                <span>·</span>
                <span>
                  표본 {meta.core_posts ?? 100}개 (최고 댓글 {meta.max_comment_post?.comment_count ?? "?"}개 / 커트라인 {meta.min_comment_post?.comment_count ?? "?"}개)
                  {" "}
                  <span style={{ fontSize: 10 }}>· {t["report.top_posts_label"]}</span>
                </span>
              </div>
            )}

          </motion.div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-5 py-10 space-y-12">

        {/* ── 신뢰도 알림 ─────────────────────────────── */}
        <div className="flex items-start gap-3 p-4 rounded-xl border-2"
          style={{ backgroundColor: "#FAFAFA", borderColor: "#E2E8F0" }}>
          <AlertTriangle size={17} className="shrink-0 mt-0.5" style={{ color: "#B45309" }} />
          <p className="text-sm leading-relaxed font-medium" style={{ color: "#4A4A4A" }}
            dangerouslySetInnerHTML={{
              __html: t["report.reliability_notice"]
                .replace("{n}", String(meta?.core_posts || 100))
                .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>"),
            }}
          />
        </div>

        {/* ── 화제글 TOP 5 ─────────────────────────── */}
        {(insights?.top_posts?.length ?? 0) > 0 && (
          <section>
            <div className="flex items-center gap-2 mb-1">
              <MessageSquare size={18} style={{ color: "#1A1A1A" }} />
              <h2 className="text-xl font-black" style={{ color: "#1A1A1A" }}>
                {t["report.top_posts_section_title"]}
              </h2>
            </div>
            <p className="text-xs mb-5" style={{ color: "#9CA3AF" }}>
              {t["report.top_posts_section_desc"]}
            </p>
            <div className="neo-card neo-card-static overflow-hidden">
              {insights!.top_posts!.map((post, i) => (
                <div key={i}
                  className="flex items-center gap-4 px-5 py-4"
                  style={{ borderTop: i > 0 ? "1px solid #E2E8F0" : "none" }}
                >
                  {/* 순위 */}
                  <span className="shrink-0 w-5 text-center font-black text-base leading-none"
                    style={{ color: i < 3 ? "#1A1A1A" : "#C8C8C8" }}>
                    {i + 1}
                  </span>

                  {/* 제목 + 메타 */}
                  <div className="flex-1 min-w-0">
                    <a href={post.url} target="_blank" rel="noopener noreferrer"
                      className="text-sm font-black flex items-start gap-1 hover:underline"
                      style={{ color: "#1A1A1A" }}>
                      <span className="break-keep flex-1">{post.title}</span>
                      <ExternalLink size={9} className="shrink-0 mt-0.5 opacity-40" />
                    </a>
                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                      <span className="text-xs" style={{ color: "#9CA3AF" }}>{post.date}</span>
                      {post.related_issue && (
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full border"
                          style={{ borderColor: "#E2E8F0", backgroundColor: "#F0EFEC", color: "#4A4A4A" }}>
                          {post.related_issue}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* 댓글 수 */}
                  <span className="shrink-0 text-sm font-black tabular-nums" style={{ color: "#1A1A1A" }}>
                    💬 {post.comment_count.toLocaleString("ko-KR")}
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* ── 주요 이슈 — 2열, 감성바 + 열기지수 ───── */}
        <section>
          <div className="flex items-center gap-2 mb-1">
            <Flame size={18} style={{ color: "#1A1A1A" }} />
            <h2 className="text-xl font-black" style={{ color: "#1A1A1A" }}>
              {t["report.issues_section_title"]}
            </h2>
          </div>
          <p className="text-xs mb-5" style={{ color: "#9CA3AF" }}>
            {t["report.heat_score_desc"]}
          </p>

          {issues.length > 0 ? (
            <div className="grid md:grid-cols-2 gap-5">
              {[...issues]
                .sort((a, b) => (b.heat_score ?? 0) - (a.heat_score ?? 0))
                .map((issue, i) => (
                <motion.div key={i}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.05 }}
                  className="neo-card neo-card-static p-5 flex flex-col"
                >
                  {/* ── 상단 영역 (flex-1 로 늘어남) ─────────────── */}
                  <div className="flex flex-col gap-3 flex-1">

                    {/* 헤더: 카테고리 배지 + 온도 지수 */}
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-xs font-black px-2.5 py-1 rounded-full border-2 shrink-0"
                        style={{ backgroundColor: "#FAFAFA", borderColor: "#1A1A1A", color: "#1A1A1A" }}>
                        {issue.issue_category}
                      </span>
                      {issue.heat_score !== undefined && (
                        <span className="flex items-center gap-1 text-xs font-black shrink-0"
                          style={{ color: issue.heat_score >= 60 ? "#FB923C" : "#9CA3AF" }}>
                          <Flame size={11} /> {t["report.heat_label"]} {issue.heat_score}
                        </span>
                      )}
                    </div>

                    {/* 이슈 제목 */}
                    <h3 className="text-base font-black leading-snug break-keep" style={{ color: "#1A1A1A" }}>
                      {issue.issue_title}
                    </h3>

                    {/* 키워드 태그 */}
                    {issue.issue_keywords && issue.issue_keywords.length > 0 && (
                      <div className="flex flex-wrap gap-1.5">
                        {issue.issue_keywords.map((kw, j) => (
                          <span key={j} className="text-xs font-bold px-2 py-0.5 rounded-full border"
                            style={{ backgroundColor: "#F0EFEC", borderColor: "#E2E8F0", color: "#4A4A4A" }}>
                            {kw}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* 이슈 요약 */}
                    <p className="text-sm leading-relaxed" style={{ color: "#4A4A4A" }}>
                      {issue.issue_summary}
                    </p>

                  </div>

                  {/* ── 하단 영역 (항상 카드 바닥에 고정) ─────────── */}
                  <div className="flex flex-col gap-3 mt-4">

                    {/* 감성 비중 바 */}
                    {issue.sentiment_ratio && (
                      <div>
                        <div className="flex items-center justify-between text-xs font-black mb-1.5">
                          <span style={{ color: "#FF6B6B" }}>{t["report.negative_label"]} {issue.sentiment_ratio.negative}%</span>
                          <span style={{ color: "#56D0A0" }}>{t["report.positive_label"]} {issue.sentiment_ratio.positive}%</span>
                        </div>
                        <div className="flex h-2.5 rounded-full overflow-hidden border-2"
                          style={{ borderColor: "#1A1A1A" }}>
                          <div style={{ width: `${issue.sentiment_ratio.negative}%`, backgroundColor: "#FF6B6B" }} />
                          <div style={{ width: `${issue.sentiment_ratio.positive}%`, backgroundColor: "#56D0A0" }} />
                        </div>
                      </div>
                    )}

                    {/* 긍정 / 부정 게시글 */}
                    {((issue.negative_posts?.length ?? 0) > 0 || (issue.positive_posts?.length ?? 0) > 0) && (
                      <div className="grid grid-cols-2 gap-3 pt-3 border-t-2" style={{ borderColor: "#E2E8F0" }}>

                        {/* 부정 게시글 */}
                        <div>
                          {(issue.negative_posts?.length ?? 0) > 0 && (
                            <>
                              <p className="text-xs font-black mb-1.5" style={{ color: "#FF6B6B" }}>
                                {t["report.negative_label"]}
                              </p>
                              <ul className="space-y-1">
                                {issue.negative_posts!.map((post, j) => (
                                  <li key={j}>
                                    <a href={post.url} target="_blank" rel="noopener noreferrer"
                                      className="text-xs flex items-start gap-1 font-semibold hover:underline"
                                      style={{ color: "#6B7280" }} title={post.title}>
                                      <span className="shrink-0 mt-px">·</span>
                                      <span className="break-keep flex-1">{post.title}</span>
                                      <ExternalLink size={8} className="shrink-0 mt-0.5 opacity-40" />
                                    </a>
                                  </li>
                                ))}
                              </ul>
                            </>
                          )}
                        </div>

                        {/* 긍정 게시글 */}
                        <div>
                          {(issue.positive_posts?.length ?? 0) > 0 && (
                            <>
                              <p className="text-xs font-black mb-1.5" style={{ color: "#56D0A0" }}>
                                {t["report.positive_label"]}
                              </p>
                              <ul className="space-y-1">
                                {issue.positive_posts!.map((post, j) => (
                                  <li key={j}>
                                    <a href={post.url} target="_blank" rel="noopener noreferrer"
                                      className="text-xs flex items-start gap-1 font-semibold hover:underline"
                                      style={{ color: "#6B7280" }} title={post.title}>
                                      <span className="shrink-0 mt-px">·</span>
                                      <span className="break-keep flex-1">{post.title}</span>
                                      <ExternalLink size={8} className="shrink-0 mt-0.5 opacity-40" />
                                    </a>
                                  </li>
                                ))}
                              </ul>
                            </>
                          )}
                        </div>

                      </div>
                    )}

                  </div>
                </motion.div>
              ))}
            </div>
          ) : <Empty text={t["report.no_issues"]} />}
        </section>

        {/* ── 게시글 추이 (하단) ───────────────────────── */}
        {meta?.date_counts && Object.keys(meta.date_counts).length > 1 && (
          <section>
            <div className="flex items-center gap-2 mb-5">
              <BarChart2 size={18} style={{ color: "#1A1A1A" }} />
              <h2 className="text-xl font-black" style={{ color: "#1A1A1A" }}>
                {t["report.trend_section_title"]}
              </h2>
            </div>
            <div className="neo-card neo-card-static p-6">
              <DailyTrendChart data={meta.date_counts} />
            </div>
          </section>
        )}

        {/* ── 하단 메타 ──────────────────────────────── */}
        <div className="flex flex-wrap gap-4 text-sm px-5 py-4 rounded-xl border-2 bg-white"
          style={{ borderColor: "#E2E8F0", color: "#9CA3AF" }}>
          <span className="flex items-center gap-1">
            <Clock size={12} />
            {t["report.req_time"]}: {report?.requestedAt ? new Date(report.requestedAt).toLocaleString("ko-KR") : "-"}
          </span>
          <span className="flex items-center gap-1">
            <CheckCircle2 size={12} />
            {t["report.done_time"]}: {report?.completedAt ? new Date(report.completedAt).toLocaleString("ko-KR") : "-"}
          </span>
          <span className="font-mono">UUID: {String(uuid)}</span>
        </div>
      </div>

      {/* ── 수집 기간 기준 모달 ────────────────────────── */}
      {showPeriodModal && (
        <>
          {/* 딤 오버레이 */}
          <div
            className="fixed inset-0 z-40"
            style={{ backgroundColor: "rgba(0,0,0,0.35)" }}
            onClick={() => setShowPeriodModal(false)}
          />
          {/* 모달 */}
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 8 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{ duration: 0.15 }}
              className="neo-card neo-card-static w-full max-w-sm p-6 pointer-events-auto"
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-black" style={{ color: "#1A1A1A" }}>
                  {t["report.period_modal_title"]}
                </h3>
                <button
                  onClick={() => setShowPeriodModal(false)}
                  className="text-lg font-black leading-none transition-opacity hover:opacity-50"
                  style={{ color: "#1A1A1A" }}
                >×</button>
              </div>
              <p className="text-xs mb-4 leading-relaxed" style={{ color: "#4A4A4A" }}>
                {t["report.period_modal_desc"]}
              </p>
              <table className="w-full text-sm border-2 rounded-xl overflow-hidden" style={{ borderColor: "#1A1A1A" }}>
                <thead>
                  <tr style={{ backgroundColor: "#1A1A1A", color: "#FFFFFF" }}>
                    <th className="px-3 py-2 text-left font-black text-xs">{t["report.period_modal_col1"]}</th>
                    <th className="px-3 py-2 text-left font-black text-xs">{t["report.period_modal_col2"]}</th>
                  </tr>
                </thead>
                <tbody>
                  {periodRows.map(({ cond, period }, i) => (
                    <tr key={i} style={{ borderTop: "1px solid #E2E8F0", backgroundColor: i % 2 === 0 ? "#FAFAFA" : "#FFFFFF" }}>
                      <td className="px-3 py-2.5 font-bold" style={{ color: "#4A4A4A" }}>{cond}</td>
                      <td className="px-3 py-2.5 font-black" style={{ color: "#1A1A1A" }}>{period}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </motion.div>
          </div>
        </>
      )}
    </main>
  );
}

function Empty({ text }: { text: string }) {
  return (
    <div className="py-12 flex items-center justify-center rounded-2xl border-2 border-dashed"
      style={{ borderColor: "#E2E8F0" }}>
      <p className="text-sm font-bold" style={{ color: "#9CA3AF" }}>{text}</p>
    </div>
  );
}

/** 일별 게시글 추이 바 차트 (외부 라이브러리 없음) */
function DailyTrendChart({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data).sort(([a], [b]) => a.localeCompare(b));
  const max     = Math.max(...entries.map(([, v]) => v), 1);

  // 30일 이상이면 격일로 날짜 레이블 표시
  const showDateEvery = entries.length > 20 ? 3 : entries.length > 14 ? 2 : 1;

  return (
    <div>
      {/* 바 영역 — 수치 레이블 공간 확보를 위해 h-36 */}
      <div className="flex gap-0.5 h-36">
        {entries.map(([date, count]) => {
          const heightPct = Math.max((count / max) * 100, 3);
          const label = count.toLocaleString("ko-KR");
          return (
            <div key={date} className="flex-1 h-full relative min-w-0">
              {/* 항상 보이는 수치 */}
              <span
                className="absolute left-0 right-0 text-center font-bold leading-none truncate px-px"
                style={{
                  bottom:    `calc(${heightPct}% + 4px)`,
                  fontSize:  9,
                  color:     "#6B7280",
                }}
              >
                {label}
              </span>
              {/* 바 */}
              <div
                className="absolute bottom-0 left-0 right-0 rounded-t-sm"
                style={{ height: `${heightPct}%`, backgroundColor: "#D1D5DB" }}
              />
            </div>
          );
        })}
      </div>

      {/* X축 — 모든 날짜 (밀도 높으면 격일) */}
      <div className="flex gap-0.5 mt-1.5">
        {entries.map(([date], i) => (
          <div key={date} className="flex-1 min-w-0 text-center overflow-hidden">
            <span
              className="block truncate"
              style={{ fontSize: 9, color: i % showDateEvery === 0 ? "#9CA3AF" : "transparent" }}
            >
              {date.slice(5)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
