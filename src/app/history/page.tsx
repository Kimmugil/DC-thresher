"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  History, ChevronRight, Calendar,
  Gamepad2, FileText, Loader2, AlertCircle, Plus,
  CheckCircle2, Clock, XCircle,
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
  COMPLETED: { label: "분석 완료", Icon: CheckCircle2, bg: "#56D0A0", color: "#166534" },
  PENDING:   { label: "진행 중",   Icon: Clock,        bg: "#FFD600", color: "#1A1A1A" },
  FAILED:    { label: "실패",      Icon: XCircle,      bg: "#FF6B6B", color: "#FFFFFF" },
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
      <div className="max-w-3xl mx-auto px-4 py-10">

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
            <Plus size={15} /> 새 분석
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
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-20 rounded-2xl animate-pulse border-2"
                style={{ backgroundColor: "#F0EFEC", borderColor: "#E2E8F0" }} />
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
          /* 리포트 목록 */
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
            {reports.map((report, idx) => {
              const cfg = STATUS_CONFIG[report.status] ?? STATUS_CONFIG.PENDING;
              const Icon = cfg.Icon;
              return (
                <motion.div key={report.uuid}
                  initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.04 }}>
                  <Link href={`/history/${report.uuid}`}
                    className="group neo-card flex items-center justify-between px-5 py-4 block"
                    style={{ textDecoration: "none" }}>
                    <div className="flex items-center gap-4 min-w-0">
                      {/* 상태 배지 */}
                      <span className="shrink-0 flex items-center gap-1 text-[11px] font-bold px-3 py-1.5 rounded-full border-2"
                        style={{ backgroundColor: cfg.bg, borderColor: "#1A1A1A", color: cfg.color }}>
                        {report.status === "PENDING"
                          ? <Loader2 size={10} className="animate-spin" />
                          : <Icon size={10} />}
                        {cfg.label}
                      </span>
                      <div className="min-w-0">
                        <p className="font-black text-sm truncate transition-colors group-hover:underline"
                          style={{ color: "#1A1A1A" }}>
                          {report.gameName || t["history.loading_game"]}
                        </p>
                        {(report as any).oneLiner ? (
                          <p className="text-xs mt-0.5 line-clamp-1" style={{ color: "#4A4A4A" }}>
                            {(report as any).oneLiner}
                          </p>
                        ) : (
                          <p className="text-sm flex items-center gap-1 mt-0.5 truncate"
                            style={{ color: "#9CA3AF" }}>
                            <Gamepad2 size={12} />
                            {report.galleryName || t["history.loading_gallery"]}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-3 shrink-0 ml-4">
                      <span className="hidden sm:flex items-center gap-1 text-xs"
                        style={{ color: "#9CA3AF" }}>
                        <Calendar size={11} />
                        {report.requestedAt
                          ? new Date(report.requestedAt).toLocaleString("ko-KR", {
                              month: "2-digit", day: "2-digit",
                              hour: "2-digit", minute: "2-digit",
                            })
                          : "-"}
                      </span>
                      <ChevronRight size={16} className="transition-transform group-hover:translate-x-1"
                        style={{ color: "#9CA3AF" }} />
                    </div>
                  </Link>
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </div>
    </main>
  );
}
