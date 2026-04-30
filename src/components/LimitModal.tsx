"use client";

import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import { useTexts } from "@/components/UITextsProvider";

interface Props {
  open:    boolean;
  limit?:  number;       // API가 내려준 한도 수치 (없으면 텍스트 그대로)
  onClose: () => void;
}

export default function LimitModal({ open, limit, onClose }: Props) {
  const t = useTexts();

  // ESC 키 닫기
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  // body 스크롤 잠금
  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  const desc = (t["limit.modal_desc"] || "")
    .replace("{limit}", String(limit ?? "?"))
    .split("\n");

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* 딤 배경 */}
          <motion.div
            key="dim"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 flex items-center justify-center px-4"
            style={{ backgroundColor: "rgba(0,0,0,0.55)" }}
            onClick={onClose}
          >
            {/* 모달 카드 — 클릭 이벤트 막기 */}
            <motion.div
              key="card"
              initial={{ opacity: 0, scale: 0.92, y: 16 }}
              animate={{ opacity: 1, scale: 1,    y: 0  }}
              exit={{    opacity: 0, scale: 0.92, y: 16 }}
              transition={{ type: "spring", stiffness: 320, damping: 26 }}
              className="neo-card w-full max-w-sm p-8 relative"
              style={{ backgroundColor: "#FFFFFF" }}
              onClick={e => e.stopPropagation()}
            >
              {/* 닫기 버튼 */}
              <button
                onClick={onClose}
                className="absolute top-4 right-4 rounded-lg p-1 transition-opacity hover:opacity-50"
                style={{ color: "#9CA3AF" }}
                aria-label="닫기"
              >
                <X size={18} />
              </button>

              {/* 배지 */}
              <span
                className="inline-block text-[11px] font-black px-3 py-1 rounded-full border-2 mb-4"
                style={{ backgroundColor: "#FF6B6B", borderColor: "#1A1A1A", color: "#FFFFFF" }}
              >
                {t["limit.modal_badge"]}
              </span>

              {/* 타이틀 */}
              <h2 className="text-xl font-black leading-snug mb-3" style={{ color: "#1A1A1A" }}>
                {t["limit.modal_title"]}
              </h2>

              {/* 설명 (줄바꿈 \n 지원) */}
              <div className="text-sm leading-relaxed mb-2" style={{ color: "#4A4A4A" }}>
                {desc.map((line, i) => (
                  <p key={i}>{line}</p>
                ))}
              </div>

              {/* 서브 텍스트 */}
              <p className="text-xs mb-6" style={{ color: "#9CA3AF" }}>
                {t["limit.modal_sub"]}
              </p>

              {/* 확인 버튼 */}
              <button
                onClick={onClose}
                className="neo-button w-full py-3 text-sm font-black"
                style={{ backgroundColor: "#1A1A1A", color: "#FFFFFF" }}
              >
                {t["limit.modal_close"]}
              </button>
            </motion.div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
