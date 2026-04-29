"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search, ArrowRight, Loader2, AlertCircle,
  ChevronRight, CheckCircle2, Clock, XCircle, Flame, X,
} from "lucide-react";
import axios from "axios";
import { useTexts } from "@/components/UITextsProvider";

interface GalleryResult {
  name: string;
  id:   string;
  type: 'regular' | 'minor' | 'mini';
  url:  string;
}

interface ConfirmedGallery {
  name: string;
  url:  string;
  type?: GalleryResult['type'];
  /** URL 직접 입력이면 'url', 검색 결과 선택이면 'search' */
  source: 'url' | 'search';
}

const DC_GALLERY_URL_PATTERN =
  /^https?:\/\/gall\.dcinside\.com\/(mgallery\/|mini\/)?board\/(lists|view)\/?\?(?:[^"'<>]*[?&])?id=[a-zA-Z0-9_]+/;

const STATUS_CONFIG = {
  COMPLETED: { label: "분석 완료", icon: CheckCircle2, color: "#166534", bg: "#56D0A0" },
  PENDING:   { label: "진행 중",   icon: Clock,        color: "#1A1A1A", bg: "#FFD600" },
  FAILED:    { label: "실패",      icon: XCircle,      color: "#FFFFFF", bg: "#FF6B6B" },
} as const;

const CARD_ROTATIONS = [1.2, -1.0, 0.8, -1.5, 1.0, -0.8];

// ── 롤링 텍스트: 한 줄 전체를 블록으로 애니메이션 → 레이아웃 이동 없음 ──
function RollingGalleryName({ names }: { names: string[] }) {
  const [idx, setIdx] = useState(0);
  useEffect(() => {
    if (names.length < 2) return;
    const t = setInterval(() => setIdx(i => (i + 1) % names.length), 2200);
    return () => clearInterval(t);
  }, [names.length]);

  if (names.length === 0) return null;

  return (
    <div className="relative h-6 overflow-hidden">
      <AnimatePresence mode="wait">
        <motion.p
          key={idx}
          initial={{ y: 16, opacity: 0 }}
          animate={{ y: 0,  opacity: 1 }}
          exit={{ y: -16, opacity: 0 }}
          transition={{ duration: 0.28 }}
          className="absolute inset-x-0 text-sm text-center"
        >
          <span className="font-semibold" style={{ color: "#9CA3AF" }}>방금 탈곡된 갤러리: </span>
          <span className="font-black" style={{ color: "#1A1A1A" }}>{names[idx]}</span>
        </motion.p>
      </AnimatePresence>
    </div>
  );
}

export default function Home() {
  const router = useRouter();
  const t = useTexts();

  // 입력창 텍스트 (URL 또는 검색어)
  const [inputText, setInputText]           = useState("");
  // 확정된 분석 대상 갤러리
  const [confirmed, setConfirmed]           = useState<ConfirmedGallery | null>(null);
  const [loading,   setLoading]             = useState(false);
  const [error,     setError]               = useState("");
  const [statusMsg, setStatusMsg]           = useState("");
  const [recentReports, setRecentReports]   = useState<any[]>([]);
  const [searchResults, setSearchResults]   = useState<GalleryResult[]>([]);
  const [isSearching,   setIsSearching]     = useState(false);

  const pendingReports = recentReports.filter(r => r.status === "PENDING");
  const doneReports    = recentReports.filter(r => r.status !== "PENDING").slice(0, 6);
  const completedNames = recentReports
    .filter(r => r.status === "COMPLETED" && (r.gameName || r.galleryName))
    .map(r => r.gameName || r.galleryName);

  // 최근 분석 목록 폴링
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await axios.get("/api/history");
        setRecentReports(res.data.reports?.slice(0, 12) || []);
      } catch { /* ignore */ }
    };
    fetchHistory();
    const iv = setInterval(fetchHistory, 10000);
    return () => clearInterval(iv);
  }, []);

  // 입력 변경 처리 — URL 감지 or 갤러리명 검색
  useEffect(() => {
    const trimmed = inputText.trim();

    // URL 패턴 감지 → 자동 확정
    if (DC_GALLERY_URL_PATTERN.test(trimmed)) {
      const id = (() => {
        try { return new URL(trimmed).searchParams.get("id") || trimmed; }
        catch { return trimmed; }
      })();
      setConfirmed({ name: id, url: trimmed, source: "url" });
      setSearchResults([]);
      return;
    }

    // URL 지워지면 URL-sourced 확정 초기화 (검색으로 선택한 건 유지)
    setConfirmed(prev => (prev?.source === "url" ? null : prev));
    setSearchResults([]);

    if (trimmed.length < 2) return;

    // 갤러리명 검색 (debounce 400ms)
    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await axios.get(`/api/search-gallery?q=${encodeURIComponent(trimmed)}`);
        setSearchResults(res.data.galleries ?? []);
      } catch {
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [inputText]);

  // 검색 결과에서 갤러리 선택
  const handleSelectGallery = (g: GalleryResult) => {
    setConfirmed({ name: g.name, url: g.url, type: g.type, source: "search" });
    setInputText("");
    setSearchResults([]);
    setError("");
  };

  // 입력/선택 초기화
  const handleClear = () => {
    setConfirmed(null);
    setInputText("");
    setSearchResults([]);
    setError("");
    setStatusMsg("");
  };

  // 분석 시작
  const handleAnalyze = async () => {
    if (!confirmed) return;
    setError("");
    setStatusMsg("");
    try {
      setLoading(true);
      setStatusMsg(t["home.status_sending"]);
      const res = await axios.post("/api/analyze", { url: confirmed.url });
      setStatusMsg(t["home.status_redirecting"]);
      setTimeout(() => router.push(`/history/${res.data.uuid}`), 1200);
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { message?: string } } };
      setError(axiosError.response?.data?.message || t["home.error_generic"]);
      setLoading(false);
    }
  };

  // 타입 배지 레이블
  const typeBadge = (type?: GalleryResult['type']) =>
    type === 'minor' ? '마이너' : type === 'mini' ? '미니' : '일반';
  const typeBadgeColor = (type?: GalleryResult['type']) =>
    type === 'minor' ? "#FFD600" : type === 'mini' ? "#56D0A0" : "#F0EFEC";

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
            <span className="px-2 inline-block" style={{ backgroundColor: "#FFD600" }}>
              {t["home.title_accent"]}
            </span>
          </h1>

          <p className="text-base mb-3" style={{ color: "#4A4A4A" }}>
            {t["home.subtitle"]}
          </p>

          <div className="mb-8">
            <RollingGalleryName names={completedNames} />
          </div>

          {/* ── 입력 영역 ─────────────────────────────────── */}
          <div className="space-y-3">

            {/* 검색/URL 입력창 */}
            <div className="neo-input-wrap">
              <Search size={18} className="ml-2 shrink-0" style={{ color: "#9CA3AF" }} />
              <input
                type="text"
                className="flex-1 py-3 text-sm outline-none bg-transparent"
                style={{ color: "#1A1A1A" }}
                placeholder="갤러리명 검색 또는 갤러리 URL 입력"
                value={inputText}
                onChange={e => { setInputText(e.target.value); setError(""); }}
                onKeyDown={e => { if (e.key === "Enter" && confirmed) handleAnalyze(); }}
                disabled={loading}
                autoComplete="off"
              />
              {isSearching && (
                <Loader2 size={14} className="animate-spin shrink-0 mr-1" style={{ color: "#9CA3AF" }} />
              )}
              {(inputText || confirmed) && !loading && (
                <button
                  type="button"
                  onClick={handleClear}
                  className="shrink-0 mr-1 p-1 rounded-full transition-colors"
                  style={{ color: "#9CA3AF" }}
                  onMouseEnter={e => (e.currentTarget.style.color = "#1A1A1A")}
                  onMouseLeave={e => (e.currentTarget.style.color = "#9CA3AF")}
                  aria-label="초기화"
                >
                  <X size={15} />
                </button>
              )}
            </div>

            {/* 갤러리 검색 결과 드롭다운 */}
            <AnimatePresence>
              {searchResults.length > 0 && !confirmed && (
                <motion.div
                  key="search-results"
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  transition={{ duration: 0.15 }}
                  className="neo-card p-2 text-left"
                  style={{ boxShadow: "2px 2px 0px 0px #1A1A1A" }}
                >
                  <p className="text-[11px] font-bold px-3 pt-1 pb-1.5" style={{ color: "#9CA3AF" }}>
                    갤러리 검색 결과 — 선택하면 분석 준비가 시작됩니다
                  </p>
                  {searchResults.map(g => (
                    <button
                      key={g.id}
                      type="button"
                      onClick={() => handleSelectGallery(g)}
                      className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-colors"
                      style={{ backgroundColor: "transparent" }}
                      onMouseEnter={e => (e.currentTarget.style.backgroundColor = "#F0EFEC")}
                      onMouseLeave={e => (e.currentTarget.style.backgroundColor = "transparent")}
                    >
                      <span
                        className="shrink-0 text-[10px] font-black px-2 py-0.5 rounded-full border"
                        style={{
                          borderColor: "#1A1A1A",
                          color: "#1A1A1A",
                          backgroundColor: typeBadgeColor(g.type),
                        }}
                      >
                        {typeBadge(g.type)}
                      </span>
                      <span className="text-sm font-bold truncate" style={{ color: "#1A1A1A" }}>
                        {g.name}
                      </span>
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>

            {/* 갤러리 확정 — 분석 확인 카드 */}
            <AnimatePresence>
              {confirmed && !loading && (
                <motion.div
                  key="confirmed"
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  transition={{ duration: 0.15 }}
                  className="neo-card p-4 text-left"
                  style={{ boxShadow: "2px 2px 0px 0px #1A1A1A" }}
                >
                  {/* 헤더 */}
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2 min-w-0">
                      <CheckCircle2 size={15} style={{ color: "#56D0A0" }} className="shrink-0" />
                      <p className="text-sm font-black truncate" style={{ color: "#1A1A1A" }}>
                        <span
                          className="inline-flex items-center mr-1.5 text-[10px] px-2 py-0.5 rounded-full border font-black"
                          style={{
                            borderColor: "#1A1A1A",
                            backgroundColor: typeBadgeColor(confirmed.type),
                          }}
                        >
                          {typeBadge(confirmed.type)}
                        </span>
                        {confirmed.name} 갤러리를 분석할까요?
                      </p>
                    </div>
                    <button
                      onClick={handleClear}
                      className="shrink-0 ml-2 text-xs font-bold transition-opacity hover:opacity-60"
                      style={{ color: "#9CA3AF" }}
                    >
                      다시 선택
                    </button>
                  </div>

                  {/* 분석 시작 버튼 */}
                  <button
                    onClick={handleAnalyze}
                    disabled={loading}
                    className="neo-button w-full flex items-center justify-center gap-2 py-3 text-sm font-black"
                    style={{ backgroundColor: "#FFD600", color: "#1A1A1A" }}
                  >
                    🌾 분석 시작하기 <ArrowRight size={14} />
                  </button>
                </motion.div>
              )}
            </AnimatePresence>

            {/* 분석 진행 중 상태 */}
            <AnimatePresence>
              {loading && (
                <motion.div
                  key="loading"
                  initial={{ opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="neo-card p-4"
                  style={{ backgroundColor: "#FFFDE7", boxShadow: "2px 2px 0px 0px #1A1A1A" }}
                >
                  <div className="flex items-center gap-3 mb-3">
                    <Loader2 size={18} className="animate-spin shrink-0" style={{ color: "#1A1A1A" }} />
                    <p className="text-sm font-black" style={{ color: "#1A1A1A" }}>
                      {confirmed?.name} 갤러리 분석 중...
                    </p>
                  </div>
                  {statusMsg && (
                    <p className="text-xs" style={{ color: "#4A4A4A" }}>{statusMsg}</p>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            {/* 에러 */}
            <AnimatePresence>
              {error && (
                <motion.div
                  key="error"
                  initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                  className="flex items-start gap-2 text-sm px-4 py-3 rounded-xl border-2"
                  style={{ backgroundColor: "#FFF5F5", borderColor: "#FF6B6B", color: "#C0392B" }}
                >
                  <AlertCircle size={15} className="shrink-0 mt-0.5" />{error}
                </motion.div>
              )}
            </AnimatePresence>

            {/* 안내 텍스트 */}
            {!confirmed && !loading && (
              <p className="text-xs" style={{ color: "#9CA3AF" }}>
                갤러리명을 입력하면 검색 결과가 표시됩니다 · 갤러리 URL을 그대로 붙여넣어도 됩니다
              </p>
            )}
          </div>

          <p className="text-xs mt-6" style={{ color: "#9CA3AF" }}>
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
                  <span className="flex items-center gap-1 text-xs font-bold shrink-0" style={{ color: "#1A1A1A" }}>
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
