"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  History, ArrowLeft, ChevronRight, Calendar,
  Gamepad2, FileText, Loader2, AlertCircle, Plus,
} from "lucide-react";
import axios from "axios";
import Link from "next/link";

interface Report {
  uuid: string;
  gameName: string;
  galleryName: string;
  requestedAt: string;
  status: "PENDING" | "COMPLETED" | "FAILED";
}

const STATUS_CONFIG = {
  COMPLETED: { label: "완료",    bg: "rgba(34,197,94,0.1)",  border: "rgba(34,197,94,0.25)",  text: "#86efac" },
  PENDING:   { label: "분석 중", bg: "rgba(99,102,241,0.1)", border: "rgba(99,102,241,0.25)", text: "#a5b4fc" },
  FAILED:    { label: "실패",    bg: "rgba(239,68,68,0.1)",  border: "rgba(239,68,68,0.25)",  text: "#fca5a5" },
};

function StatusBadge({ status }: { status: Report["status"] }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.PENDING;
  return (
    <span
      className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full border"
      style={{ backgroundColor: cfg.bg, borderColor: cfg.border, color: cfg.text }}
    >
      {status === "PENDING" && <Loader2 size={10} className="animate-spin" />}
      {cfg.label}
    </span>
  );
}

export default function HistoryPage() {
  const router = useRouter();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState("");

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await axios.get("/api/history");
        setReports(res.data.reports);
      } catch (err: unknown) {
        const axiosError = err as { response?: { data?: { message?: string } } };
        setError(axiosError.response?.data?.message || "리포트 목록을 불러오지 못했습니다.");
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  return (
    <main className="min-h-screen" style={{ backgroundColor: "var(--bg-base)" }}>

      {/* 헤더 */}
      <header
        className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 border-b backdrop-blur-md"
        style={{ backgroundColor: "rgba(13,17,23,0.85)", borderColor: "var(--border)" }}
      >
        <button
          onClick={() => router.push("/")}
          className="flex items-center gap-2 text-sm font-medium transition-colors"
          style={{ color: "var(--text-secondary)" }}
          onMouseEnter={e => (e.currentTarget.style.color = "var(--text-primary)")}
          onMouseLeave={e => (e.currentTarget.style.color = "var(--text-secondary)")}
        >
          <ArrowLeft size={16} />
          새 분석 요청
        </button>
        <div className="flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
          <History size={16} className="text-indigo-400" />
          <span className="font-bold text-sm">분석 리포트 보관함</span>
        </div>
        <div className="w-24" />
      </header>

      <div className="max-w-4xl mx-auto px-4 py-10">

        {/* 타이틀 */}
        <div className="mb-8">
          <h1 className="text-2xl font-black mb-1" style={{ color: "var(--text-primary)" }}>
            분석 리포트 보관함
          </h1>
          <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
            지금까지 발행된 DC-Thresher AI 리포트 전체 목록입니다.
          </p>
        </div>

        {/* 에러 배너 */}
        {error && (
          <div
            className="flex items-center gap-2.5 text-sm px-4 py-3 rounded-xl border mb-6"
            style={{ backgroundColor: "rgba(239,68,68,0.08)", borderColor: "rgba(239,68,68,0.25)", color: "#fca5a5" }}
          >
            <AlertCircle size={15} className="shrink-0" />
            {error}
          </div>
        )}

        {/* 로딩 스켈레톤 */}
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div
                key={i}
                className="h-20 rounded-2xl animate-pulse border"
                style={{ backgroundColor: "var(--bg-surface)", borderColor: "var(--border)" }}
              />
            ))}
          </div>
        ) : reports.length === 0 ? (
          /* 빈 상태 */
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-24 rounded-2xl border border-dashed"
            style={{ borderColor: "var(--border)" }}
          >
            <FileText size={40} className="mx-auto mb-4" style={{ color: "var(--text-muted)" }} />
            <h3 className="text-lg font-bold mb-2" style={{ color: "var(--text-secondary)" }}>
              아직 발행된 리포트가 없습니다
            </h3>
            <p className="text-sm mb-6" style={{ color: "var(--text-muted)" }}>
              첫 번째 갤러리 분석을 요청해보세요.
            </p>
            <button
              onClick={() => router.push("/")}
              className="inline-flex items-center gap-2 text-sm font-semibold px-4 py-2.5 rounded-xl transition-all"
              style={{ backgroundColor: "var(--bg-raised)", color: "var(--text-primary)", border: "1px solid var(--border)" }}
            >
              <Plus size={15} />
              새 분석 시작
            </button>
          </motion.div>
        ) : (
          /* 리포트 목록 */
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-2"
          >
            {reports.map((report, idx) => (
              <motion.div
                key={report.uuid}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.04 }}
              >
                <Link
                  href={`/history/${report.uuid}`}
                  className="group flex items-center justify-between px-5 py-4 rounded-2xl border transition-all"
                  style={{ backgroundColor: "var(--bg-surface)", borderColor: "var(--border)" }}
                  onMouseEnter={e => {
                    (e.currentTarget as HTMLElement).style.borderColor = "rgba(99,102,241,0.4)";
                    (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-raised)";
                  }}
                  onMouseLeave={e => {
                    (e.currentTarget as HTMLElement).style.borderColor = "var(--border)";
                    (e.currentTarget as HTMLElement).style.backgroundColor = "var(--bg-surface)";
                  }}
                >
                  <div className="flex items-center gap-4 min-w-0">
                    <StatusBadge status={report.status} />
                    <div className="min-w-0">
                      <p className="font-bold text-sm truncate transition-colors group-hover:text-indigo-400" style={{ color: "var(--text-primary)" }}>
                        {report.gameName || "게임명 수집 중..."}
                      </p>
                      <p className="text-xs flex items-center gap-1 mt-0.5 truncate" style={{ color: "var(--text-muted)" }}>
                        <Gamepad2 size={11} />
                        {report.galleryName || "갤러리명 수집 중..."}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4 shrink-0 ml-4">
                    <span className="hidden sm:flex items-center gap-1 text-xs" style={{ color: "var(--text-muted)" }}>
                      <Calendar size={11} />
                      {report.requestedAt
                        ? new Date(report.requestedAt).toLocaleString("ko-KR", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" })
                        : "-"}
                    </span>
                    <ChevronRight size={16} className="transition-transform group-hover:translate-x-1" style={{ color: "var(--text-muted)" }} />
                  </div>
                </Link>
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </main>
  );
}
