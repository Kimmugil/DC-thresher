"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  History, ChevronRight, Calendar,
  Gamepad2, FileText, Loader2, AlertCircle, Plus,
} from "lucide-react";
import axios from "axios";
import Link from "next/link";
import { useTexts } from "@/components/UITextsProvider";

interface Report {
  uuid:        string;
  gameName:    string;
  galleryName: string;
  requestedAt: string;
  status:      "PENDING" | "COMPLETED" | "FAILED";
}

const STATUS_CONFIG = {
  COMPLETED: { label: "분석 완료", bg: "#F0FDF4", border: "#BBF7D0", text: "#15803D" },
  PENDING:   { label: "진행 중",   bg: "#FFFBEB", border: "#FDE68A", text: "#B45309" },
  FAILED:    { label: "실패",      bg: "#FEF2F2", border: "#FECACA", text: "#DC2626" },
} as const;

function StatusBadge({ status, t }: { status: Report["status"]; t: Record<string, string> }) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.PENDING;
  const label = t[`history.status_${status.toLowerCase()}`] ?? cfg.label;
  return (
    <span
      className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full border shrink-0"
      style={{ backgroundColor: cfg.bg, borderColor: cfg.border, color: cfg.text }}
    >
      {status === "PENDING" && <Loader2 size={10} className="animate-spin" />}
      {label}
    </span>
  );
}

export default function HistoryPage() {
  const router = useRouter();
  const t = useTexts();
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
        setError(axiosError.response?.data?.message || t["history.error_load"]);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <main className="min-h-screen" style={{ backgroundColor: "var(--bg-base)" }}>

      <div className="max-w-4xl mx-auto px-4 py-10">

        {/* 타이틀 */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <History size={18} style={{ color: "var(--accent)" }} />
              <h1 className="text-2xl font-black" style={{ color: "var(--text-primary)" }}>
                {t["history.title"]}
              </h1>
            </div>
            <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
              {t["history.subtitle"]}
            </p>
          </div>
          <button
            onClick={() => router.push("/")}
            className="flex items-center gap-2 text-sm font-semibold px-4 py-2 rounded-xl border transition-colors"
            style={{ borderColor: "var(--border)", color: "var(--text-secondary)", backgroundColor: "var(--bg-surface)" }}
            onMouseEnter={e => (e.currentTarget.style.backgroundColor = "var(--bg-raised)")}
            onMouseLeave={e => (e.currentTarget.style.backgroundColor = "var(--bg-surface)")}
          >
            <Plus size={15} />
            새 분석
          </button>
        </div>

        {/* 에러 배너 */}
        {error && (
          <div
            className="flex items-center gap-2.5 text-sm px-4 py-3 rounded-xl border mb-6"
            style={{ backgroundColor: "#FEF2F2", borderColor: "#FECACA", color: "#DC2626" }}
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
                style={{ backgroundColor: "var(--bg-raised)", borderColor: "var(--border)" }}
              />
            ))}
          </div>
        ) : reports.length === 0 ? (
          /* 빈 상태 */
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center py-24 rounded-2xl border-2 border-dashed bg-white"
            style={{ borderColor: "var(--border)" }}
          >
            <FileText size={40} className="mx-auto mb-4" style={{ color: "var(--text-muted)" }} />
            <h3 className="text-lg font-bold mb-2" style={{ color: "var(--text-primary)" }}>
              {t["history.empty_title"]}
            </h3>
            <p className="text-sm mb-6" style={{ color: "var(--text-secondary)" }}>
              {t["history.empty_desc"]}
            </p>
            <button
              onClick={() => router.push("/")}
              className="inline-flex items-center gap-2 text-sm font-semibold px-5 py-2.5 rounded-xl transition-all"
              style={{ backgroundColor: "#18181B", color: "#FFFFFF" }}
            >
              <Plus size={15} />
              {t["history.empty_btn"]}
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
                  className="group flex items-center justify-between px-5 py-4 rounded-2xl border-2 bg-white transition-all"
                  style={{ borderColor: "var(--border)" }}
                  onMouseEnter={e => {
                    (e.currentTarget as HTMLElement).style.borderColor = "#C7D2FE";
                  }}
                  onMouseLeave={e => {
                    (e.currentTarget as HTMLElement).style.borderColor = "var(--border)";
                  }}
                >
                  <div className="flex items-center gap-4 min-w-0">
                    <StatusBadge status={report.status} t={t} />
                    <div className="min-w-0">
                      <p
                        className="font-bold text-sm truncate transition-colors group-hover:text-indigo-600"
                        style={{ color: "var(--text-primary)" }}
                      >
                        {report.gameName || t["history.loading_game"]}
                      </p>
                      <p className="text-xs flex items-center gap-1 mt-0.5 truncate" style={{ color: "var(--text-muted)" }}>
                        <Gamepad2 size={11} />
                        {report.galleryName || t["history.loading_gallery"]}
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
