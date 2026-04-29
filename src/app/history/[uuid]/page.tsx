"use client";

import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  ArrowLeft, Loader2, Calendar, AlertTriangle,
  CheckCircle2, Clock, Database, FileText,
  Flame, ExternalLink, BarChart2,
} from "lucide-react";
import axios from "axios";
import { useTexts } from "@/components/UITextsProvider";

interface RelatedPost { title: string; url: string; }
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
            홈으로 돌아가기 (백그라운드에서 계속 진행됩니다)
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
            className="flex flex-col gap-6">

            {/* 타이틀 */}
            <div>
              <div className="flex items-center gap-2.5 mb-3">
                <span className="inline-flex items-center gap-1 text-xs font-black px-3 py-1 rounded-full border-2"
                  style={{ backgroundColor: "#56D0A0", borderColor: "#1A1A1A", color: "#1A1A1A" }}>
                  <CheckCircle2 size={10} /> {t["report.status_completed"]}
                </span>
                <span className="flex items-center gap-1 text-sm font-semibold" style={{ color: "#9CA3AF" }}>
                  <Calendar size={13} />
                  {report?.completedAt ? new Date(report.completedAt).toLocaleString("ko-KR") : "-"}
                </span>
              </div>
              <h1 className="text-3xl md:text-4xl font-black mb-2" style={{ color: "#1A1A1A" }}>
                {report?.gameName || t["report.game_unknown"]}
              </h1>
              <div className="flex items-center gap-3 flex-wrap">
                <p className="text-base font-bold" style={{ color: "#4A4A4A" }}>
                  {report?.galleryName || ""}
                </p>
                {galleryUrl && (
                  <a href={galleryUrl} target="_blank" rel="noopener noreferrer"
                    className="neo-button inline-flex items-center gap-1.5 px-3 py-1.5"
                    style={{ backgroundColor: "#F0EFEC", color: "#1A1A1A", fontSize: 12 }}>
                    <ExternalLink size={11} /> 갤러리 바로가기
                  </a>
                )}
              </div>
            </div>

            {/* 투명성 지표 2칸 */}
            <div className="grid md:grid-cols-2 gap-4">

              {/* 분석 대상 */}
              <div className="neo-card neo-card-static p-4 flex flex-col gap-1.5">
                <div className="flex items-center gap-2 font-black text-sm mb-1" style={{ color: "#1A1A1A" }}>
                  <Database size={15} /> 분석 대상
                </div>
                <p className="text-sm" style={{ color: "#4A4A4A" }}>
                  수집 기간: {meta?.date_range || "알 수 없음"}
                </p>
                <p className="text-sm" style={{ color: "#4A4A4A" }}>
                  전체 게시글: {meta?.total_posts ? `${meta.total_posts.toLocaleString()}개` : "알 수 없음"}
                </p>
                <p className="text-xs mt-1.5" style={{ color: "#9CA3AF" }}>
                  ※ 표본 추출: 댓글 수 기준 상위 {meta?.core_posts || 100}개 화제글을 AI가 집중 분석
                </p>
              </div>

              {/* 표본 데이터 현황 */}
              <div className="neo-card neo-card-static p-4 flex flex-col gap-1.5">
                <div className="flex items-center gap-2 font-black text-sm mb-1" style={{ color: "#1A1A1A" }}>
                  <FileText size={15} /> 표본 데이터 현황 (댓글수 기준)
                </div>
                <p className="text-sm flex items-baseline gap-1 flex-wrap" style={{ color: "#4A4A4A" }}>
                  <span className="shrink-0">최고 댓글수: {meta?.max_comment_post?.comment_count ?? "-"}개</span>
                  {meta?.max_comment_post && (
                    meta.max_comment_post.url
                      ? <a href={meta.max_comment_post.url} target="_blank" rel="noopener noreferrer"
                          className="truncate max-w-[200px] hover:underline flex items-center gap-0.5"
                          style={{ color: "#4D96FF" }} title={meta.max_comment_post.title}>
                          ({meta.max_comment_post.title}) <ExternalLink size={10} className="shrink-0" />
                        </a>
                      : <span className="truncate max-w-[200px]" title={meta.max_comment_post.title}>
                          ({meta.max_comment_post.title})
                        </span>
                  )}
                </p>
                <p className="text-sm flex items-baseline gap-1 flex-wrap" style={{ color: "#4A4A4A" }}>
                  <span className="shrink-0">커트라인: {meta?.min_comment_post?.comment_count ?? "-"}개</span>
                  {meta?.min_comment_post && (
                    meta.min_comment_post.url
                      ? <a href={meta.min_comment_post.url} target="_blank" rel="noopener noreferrer"
                          className="truncate max-w-[200px] hover:underline flex items-center gap-0.5"
                          style={{ color: "#4D96FF" }} title={meta.min_comment_post.title}>
                          ({meta.min_comment_post.title}) <ExternalLink size={10} className="shrink-0" />
                        </a>
                      : <span className="truncate max-w-[200px]" title={meta.min_comment_post.title}>
                          ({meta.min_comment_post.title})
                        </span>
                  )}
                </p>
              </div>

            </div>

            {/* AI 한줄 요약 */}
            <div className="neo-card neo-card-static p-5" style={{ backgroundColor: "#FFD600" }}>
              <p className="text-xs font-black mb-2 uppercase tracking-widest" style={{ color: "#1A1A1A", opacity: 0.55 }}>
                🤖 AI 한줄 요약
              </p>
              <p className="text-lg font-black leading-snug" style={{ color: "#1A1A1A" }}>
                "{insights?.critic_one_liner || "분석 결과가 없습니다."}"
              </p>
            </div>

            {/* 키워드 배지 */}
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
          </motion.div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-5 py-10 space-y-12">

        {/* ── 신뢰도 알림 ─────────────────────────────── */}
        <div className="flex items-start gap-3 p-4 rounded-xl border-2"
          style={{ backgroundColor: "#FAFAFA", borderColor: "#E2E8F0" }}>
          <AlertTriangle size={17} className="shrink-0 mt-0.5" style={{ color: "#B45309" }} />
          <p className="text-sm leading-relaxed font-medium" style={{ color: "#4A4A4A" }}>
            이 리포트는 <strong>핵심 화제글(최대 {meta?.core_posts || 100}개)</strong> 기반으로 작성되었으며, 갤러리 전체 여론을 100% 대변하지 않을 수 있습니다. 카드 하단 링크로 원문을 직접 확인하세요.
          </p>
        </div>

        {/* ── ① 일별 게시글 추이 ──────────────────────── */}
        {meta?.date_counts && Object.keys(meta.date_counts).length > 1 && (
          <section>
            <div className="flex items-center gap-2 mb-5">
              <BarChart2 size={18} style={{ color: "#1A1A1A" }} />
              <h2 className="text-xl font-black" style={{ color: "#1A1A1A" }}>기간 내 게시글 추이</h2>
            </div>
            <div className="neo-card neo-card-static p-6">
              <DailyTrendChart data={meta.date_counts} />
            </div>
          </section>
        )}

        {/* ── 주요 이슈 — 2열, 감성바 + 열기지수 ───── */}
        <section>
          <div className="flex items-center gap-2 mb-1">
            <Flame size={18} style={{ color: "#1A1A1A" }} />
            <h2 className="text-xl font-black" style={{ color: "#1A1A1A" }}>주요 이슈</h2>
          </div>
          <p className="text-xs mb-5" style={{ color: "#9CA3AF" }}>
            열기 지수: 분석 게시글 중 해당 이슈 관련 언급 비율 (0–100) · 높은 순 정렬
          </p>

          {issues.length > 0 ? (
            <div className="grid md:grid-cols-2 gap-5 items-start">
              {[...issues]
                .sort((a, b) => (b.heat_score ?? 0) - (a.heat_score ?? 0))
                .map((issue, i) => (
                <motion.div key={i}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.05 }}
                  className="neo-card neo-card-static p-5 flex flex-col gap-3"
                >
                  {/* 헤더: 카테고리 배지 + 열기 지수 */}
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-xs font-black px-2.5 py-1 rounded-full border-2 shrink-0"
                      style={{ backgroundColor: "#FAFAFA", borderColor: "#1A1A1A", color: "#1A1A1A" }}>
                      {issue.issue_category}
                    </span>
                    {issue.heat_score !== undefined && (
                      <span className="flex items-center gap-1 text-xs font-black shrink-0"
                        style={{ color: issue.heat_score >= 60 ? "#FB923C" : "#9CA3AF" }}>
                        <Flame size={11} /> 열기 {issue.heat_score}
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

                  {/* ② 감성 비중 바 */}
                  {issue.sentiment_ratio && (
                    <div>
                      <div className="flex items-center justify-between text-xs font-black mb-1.5">
                        <span style={{ color: "#FF6B6B" }}>부정 {issue.sentiment_ratio.negative}%</span>
                        <span style={{ color: "#56D0A0" }}>긍정 {issue.sentiment_ratio.positive}%</span>
                      </div>
                      <div className="flex h-2.5 rounded-full overflow-hidden border-2"
                        style={{ borderColor: "#1A1A1A" }}>
                        <div style={{ width: `${issue.sentiment_ratio.negative}%`, backgroundColor: "#FF6B6B" }} />
                        <div style={{ width: `${issue.sentiment_ratio.positive}%`, backgroundColor: "#56D0A0" }} />
                      </div>
                    </div>
                  )}

                  {/* 긍정 / 부정 게시글 분리 표시 */}
                  {((issue.negative_posts?.length ?? 0) > 0 || (issue.positive_posts?.length ?? 0) > 0) && (
                    <div className="grid grid-cols-2 gap-3 pt-3 border-t-2" style={{ borderColor: "#E2E8F0" }}>

                      {/* 부정 게시글 */}
                      <div>
                        {(issue.negative_posts?.length ?? 0) > 0 && (
                          <>
                            <p className="text-xs font-black mb-1.5" style={{ color: "#FF6B6B" }}>부정</p>
                            <ul className="space-y-1">
                              {issue.negative_posts!.map((post, j) => (
                                <li key={j}>
                                  <a href={post.url} target="_blank" rel="noopener noreferrer"
                                    className="text-xs block truncate font-semibold hover:underline"
                                    style={{ color: "#4D96FF" }} title={post.title}>
                                    · {post.title}
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
                            <p className="text-xs font-black mb-1.5" style={{ color: "#56D0A0" }}>긍정</p>
                            <ul className="space-y-1">
                              {issue.positive_posts!.map((post, j) => (
                                <li key={j}>
                                  <a href={post.url} target="_blank" rel="noopener noreferrer"
                                    className="text-xs block truncate font-semibold hover:underline"
                                    style={{ color: "#4D96FF" }} title={post.title}>
                                    · {post.title}
                                  </a>
                                </li>
                              ))}
                            </ul>
                          </>
                        )}
                      </div>

                    </div>
                  )}
                </motion.div>
              ))}
            </div>
          ) : <Empty text="감지된 주요 이슈가 없습니다." />}
        </section>

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
  const mid     = entries[Math.floor(entries.length / 2)]?.[0].slice(5);

  return (
    <div>
      {/* 높이 고정 컨테이너 — 각 column이 h-full을 쓸 수 있도록 */}
      <div className="flex gap-0.5 h-28">
        {entries.map(([date, count]) => (
          <div key={date} className="flex-1 h-full relative group min-w-0">
            {/* 툴팁 */}
            <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-black text-white
              text-xs px-2 py-1 rounded whitespace-nowrap opacity-0 group-hover:opacity-100
              transition-opacity pointer-events-none z-10 font-bold text-center">
              {date.slice(5)}<br />{count}개
            </div>
            {/* 바: 아래에서 위로 성장 */}
            <div
              className="absolute bottom-0 left-0 right-0 rounded-t-sm"
              style={{
                height:          `${Math.max((count / max) * 100, 3)}%`,
                backgroundColor: "#1A1A1A",
              }}
            />
          </div>
        ))}
      </div>
      {/* X축: 첫날 / 중간 / 마지막날 */}
      <div className="flex justify-between mt-2 text-xs" style={{ color: "#9CA3AF" }}>
        <span>{entries[0]?.[0].slice(5)}</span>
        {entries.length > 2 && <span>{mid}</span>}
        <span>{entries[entries.length - 1]?.[0].slice(5)}</span>
      </div>
    </div>
  );
}
