"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { MessageSquare, Calendar } from "lucide-react";

export interface ReportCardData {
  uuid:        string;
  gameName:    string;
  galleryName: string;
  oneLiner:    string;
  top3Posts:   { title: string; comment_count: number }[];
  dateRange:   string;
  requestedAt: string;
  status:      string;
}

interface Props {
  report:  ReportCardData;
  rotate?: number;
}

export default function ReportCard({ report, rotate = 0 }: Props) {
  const name = report.gameName || report.galleryName || "-";

  return (
    <Link href={`/history/${report.uuid}`} className="block w-[360px] shrink-0">
      <motion.div
        style={{ rotate, boxShadow: "2px 2px 0px 0px #1A1A1A" }}
        whileHover={{ rotate: 0, y: -4 }}
        transition={{ type: "spring", stiffness: 300, damping: 20 }}
        className="neo-card w-[360px] flex flex-col cursor-pointer"
      >

        {/* ① 갤러리명 */}
        <div className="px-5 pt-5 pb-3.5 border-b-2" style={{ borderColor: "#E2E8F0" }}>
          <p className="font-black text-lg leading-tight line-clamp-1" style={{ color: "#1A1A1A" }}>
            {name} 갤러리
          </p>
          {report.dateRange && (
            <p className="text-xs mt-1 flex items-center gap-1" style={{ color: "#9CA3AF" }}>
              <Calendar size={10} />
              {report.dateRange}
            </p>
          )}
        </div>

        {/* ② AI 한줄평 — 노란 하이라이트, 전문 표시 */}
        <div className="px-5 py-3.5 border-b-2" style={{ borderColor: "#E2E8F0", minHeight: 82 }}>
          {report.oneLiner ? (
            <p className="text-sm font-bold leading-[1.85]">
              <span style={{
                backgroundColor: "#FFD600",
                padding: "0 4px",
                WebkitBoxDecorationBreak: "clone",
                boxDecorationBreak: "clone",
              }}>
                {report.oneLiner}
              </span>
            </p>
          ) : (
            <p className="text-sm" style={{ color: "#9CA3AF" }}>분석 중...</p>
          )}
        </div>

        {/* ③ 화제글 TOP 3 */}
        <div
          className="px-5 py-3.5 border-b-2 space-y-2"
          style={{ borderColor: "#E2E8F0", minHeight: 96 }}
        >
          {report.top3Posts.length > 0 ? (
            report.top3Posts.map((post, i) => (
              <div key={i} className="flex items-center gap-2">
                <span
                  className="shrink-0 text-xs font-black w-4 text-center tabular-nums"
                  style={{ color: i === 0 ? "#1A1A1A" : "#C8C8C8" }}
                >
                  {i + 1}
                </span>
                <span className="flex-1 text-xs truncate" style={{ color: "#4A4A4A" }}>
                  {post.title}
                </span>
                <span
                  className="shrink-0 flex items-center gap-0.5 text-xs tabular-nums font-bold"
                  style={{ color: "#9CA3AF" }}
                >
                  <MessageSquare size={9} />
                  {post.comment_count.toLocaleString("ko-KR")}
                </span>
              </div>
            ))
          ) : (
            <p className="text-xs" style={{ color: "#9CA3AF" }}>화제글 정보 없음</p>
          )}
        </div>

        {/* ④ 요청 시각 */}
        <div className="px-5 py-3">
          <p className="text-xs" style={{ color: "#9CA3AF" }}>
            {report.requestedAt
              ? new Date(report.requestedAt).toLocaleString("ko-KR", {
                  year: "numeric", month: "2-digit", day: "2-digit",
                  hour: "2-digit", minute: "2-digit",
                })
              : "-"}
          </p>
        </div>

      </motion.div>
    </Link>
  );
}
