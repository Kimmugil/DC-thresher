"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  History, FileText, Loader2, AlertCircle, Plus,
  Clock, XCircle, CheckCircle2,
} from "lucide-react";
import axios from "axios";
import { useTexts } from "@/components/UITextsProvider";
import ReportCard, { ReportCardData } from "@/components/ReportCard";

interface Report extends ReportCardData {
  status: "PENDING" | "COMPLETED" | "FAILED";
}

const CARD_ROTATIONS = [1.2, -1.0, 0.8, -1.5, 1.0, -0.8];

const STATUS_CONFIG = {
  COMPLETED: { labelKey: "status.completed", Icon: CheckCircle2, bg: "#56D0A0", color: "#166534" },
  PENDING:   { labelKey: "status.pending",   Icon: Clock,        bg: "#FFD600", color: "#1A1A1A" },
  FAILED:    { labelKey: "status.failed",    Icon: XCircle,      bg: "#FF6B6B", color: "#FFFFFF" },
} as const;

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
    <main style={{ backgroundColor: "#FAFAFA", minHeight: "100vh" }}>
      <div className="max-w-7xl mx-auto px-4 py-10">

        {/* 헤더 */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <History size={20} style={{ color: "#1A1A1A" }} />
              <h1 className="text-2xl font-black" style={{ color: "#1A1A1A" }}>
                {t["history.title"]}
              </h1>
            </div>
            <p className="text-sm" style={{ color: "#4A4A4A" }}>
              {t["history.subtitle"]}
            </p>
          </div>
          <button
            onClick={() => router.push("/")}
            className="neo-button flex items-center gap-2 px-5 py-2.5 text-sm"
            style={{ backgroundColor: "#FFD600", color: "#1A1A1A" }}
          >
            <Plus size={15} /> {t["history.new_analysis_btn"]}
          </button>
        </div>

        {/* 에러 */}
        {error && (
          <div className="flex items-center gap-2.5 text-sm px-4 py-3 rounded-xl border-2 mb-6"
            style={{ backgroundColor: "#FFF5F5", borderColor: "#FF6B6B", color: "#C0392B" }}>
            <AlertCircle size={15} className="shrink-0" />{error}
          </div>
        )}

        {/* 스켈레톤 */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {[1, 2, 3, 4, 5, 6].map(i => (
              <div key={i} className="w-full rounded-2xl animate-pulse border-2"
                style={{ backgroundColor: "#F0EFEC", borderColor: "#E2E8F0", height: 300 }} />
            ))}
          </div>

        ) : reports.length === 0 ? (
          /* 빈 상태 */
          <motion.div
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            className="text-center py-24 neo-card border-dashed"
            style={{ boxShadow: "none", borderStyle: "dashed" }}
          >
            <FileText size={44} className="mx-auto mb-4" style={{ color: "#9CA3AF" }} />
            <h3 className="text-lg font-black mb-2" style={{ color: "#1A1A1A" }}>
              {t["history.empty_title"]}
            </h3>
            <p className="text-sm mb-6" style={{ color: "#4A4A4A" }}>
              {t["history.empty_desc"]}
            </p>
            <button onClick={() => router.push("/")}
              className="neo-button inline-flex items-center gap-2 text-sm px-5 py-2.5"
              style={{ backgroundColor: "#FFD600", color: "#1A1A1A" }}>
              <Plus size={15} />{t["history.empty_btn"]}
            </button>
          </motion.div>

        ) : (
          /* 카드 그리드 */
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 items-start"
          >
            {reports.map((report, idx) => {
              const rot = report.status === "COMPLETED"
                ? CARD_ROTATIONS[idx % CARD_ROTATIONS.length]
                : 0;
              return (
                <motion.div
                  key={report.uuid}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.04 }}
                  className="flex justify-center sm:justify-start"
                >
                  {report.status === "COMPLETED" ? (
                    <ReportCard report={report} rotate={rot} />
                  ) : (
                    /* PENDING / FAILED — 간단 상태 카드 */
                    <PendingCard report={report} t={t} />
                  )}
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </div>
    </main>
  );
}

/* ── PENDING / FAILED 상태 카드 (인라인) ───────────────────────── */
function PendingCard({ report, t }: { report: Report; t: Record<string, string> }) {
  const cfg  = STATUS_CONFIG[report.status] ?? STATUS_CONFIG.PENDING;
  const Icon = cfg.Icon;
  const name = report.gameName || report.galleryName || t["history.loading_game"];

  return (
    <a href={`/history/${report.uuid}`} className="block w-[360px]">
      <div
        className="neo-card w-[360px] flex flex-col"
        style={{ boxShadow: "2px 2px 0px 0px #1A1A1A", opacity: 0.75 }}
      >
        <div className="px-5 pt-5 pb-3.5 border-b-2" style={{ borderColor: "#E2E8F0" }}>
          <div className="flex items-center gap-2">
            <span
              className="shrink-0 flex items-center gap-1 text-[11px] font-bold px-2.5 py-1 rounded-full border-2"
              style={{ backgroundColor: cfg.bg, borderColor: "#1A1A1A", color: cfg.color }}
            >
              {report.status === "PENDING"
                ? <Loader2 size={10} className="animate-spin" />
                : <Icon size={10} />}
              {t[cfg.labelKey]}
            </span>
          </div>
          <p className="font-black text-lg leading-tight mt-2 line-clamp-1" style={{ color: "#1A1A1A" }}>
            {name} 갤러리
          </p>
        </div>
        <div className="px-5 py-4">
          <p className="text-xs" style={{ color: "#9CA3AF" }}>
            {report.requestedAt
              ? new Date(report.requestedAt).toLocaleString("ko-KR", {
                  year: "numeric", month: "2-digit", day: "2-digit",
                  hour: "2-digit", minute: "2-digit",
                })
              : "-"}
          </p>
        </div>
      </div>
    </a>
  );
}
