"use client";

import { useState } from "react";
import { Lock, Eye, EyeOff, Trash2, ShieldCheck, Loader2, RefreshCw } from "lucide-react";
import axios from "axios";

export default function AdminPage() {
  const [password,        setPassword]        = useState("");
  const [showPw,          setShowPw]          = useState(false);
  const [authLoading,     setAuthLoading]     = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [error,           setError]           = useState("");

  const [reports,        setReports]        = useState<any[]>([]);
  const [reportsLoading, setReportsLoading] = useState(false);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthLoading(true);
    setError("");
    try {
      const res = await axios.post("/api/admin/auth", { password });
      if (res.data.ok) {
        setIsAuthenticated(true);
        fetchReports();
      }
    } catch (err: any) {
      setError(err.response?.data?.message || "비밀번호가 틀렸거나 서버 오류입니다.");
    } finally {
      setAuthLoading(false);
    }
  };

  const fetchReports = async () => {
    setReportsLoading(true);
    try {
      const res = await axios.get("/api/admin/reports");
      setReports(res.data.reports || []);
    } catch {
      setError("리포트 목록을 불러오지 못했습니다.");
    } finally {
      setReportsLoading(false);
    }
  };

  const handleAction = async (rowIndex: number, action: "HIDE" | "SHOW" | "DELETE") => {
    if (action === "DELETE" && !confirm("영구 삭제합니다. 복구할 수 없습니다.")) return;
    try {
      await axios.post("/api/admin/reports", { rowIndex, action });
      fetchReports();
    } catch {
      alert("작업에 실패했습니다.");
    }
  };

  /* ── 로그인 화면 ──────────────────────────────────────── */
  if (!isAuthenticated) {
    return (
      <main className="min-h-screen flex items-center justify-center p-4"
        style={{ backgroundColor: "#FAFAFA" }}>
        <form onSubmit={handleAuth} className="neo-card w-full max-w-sm p-8">
          <div className="flex items-center gap-2 mb-6">
            <ShieldCheck size={22} style={{ color: "#1A1A1A" }} />
            <h2 className="text-xl font-black" style={{ color: "#1A1A1A" }}>관리자 패널</h2>
          </div>

          {/* 비밀번호 입력 */}
          <div className="neo-input-wrap mb-4">
            <Lock size={15} className="ml-2 shrink-0" style={{ color: "#9CA3AF" }} />
            <input
              type={showPw ? "text" : "password"}
              placeholder="비밀번호 입력"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="flex-1 py-2.5 text-sm outline-none bg-transparent"
              style={{ color: "#1A1A1A" }}
              autoComplete="current-password"
            />
            <button
              type="button"
              onClick={() => setShowPw(v => !v)}
              className="mr-2 transition-opacity hover:opacity-60"
              style={{ color: "#9CA3AF" }}
            >
              {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
            </button>
          </div>

          {error && (
            <p className="text-xs mb-4 font-bold" style={{ color: "#FF6B6B" }}>{error}</p>
          )}

          <button
            type="submit"
            disabled={authLoading}
            className="neo-button w-full flex items-center justify-center gap-2 py-3 text-sm font-black"
            style={{ backgroundColor: "#1A1A1A", color: "#FFFFFF" }}
          >
            {authLoading ? <Loader2 size={14} className="animate-spin" /> : "로그인"}
          </button>
        </form>
      </main>
    );
  }

  /* ── 대시보드 ─────────────────────────────────────────── */
  return (
    <main className="min-h-screen p-6 md:p-10" style={{ backgroundColor: "#FAFAFA" }}>
      <div className="max-w-6xl mx-auto">

        {/* 헤더 */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-2">
            <ShieldCheck size={20} style={{ color: "#1A1A1A" }} />
            <h1 className="text-2xl font-black" style={{ color: "#1A1A1A" }}>관리자 대시보드</h1>
          </div>
          <button
            onClick={fetchReports}
            disabled={reportsLoading}
            className="neo-button flex items-center gap-2 px-4 py-2 text-sm"
            style={{ backgroundColor: "#F0EFEC", color: "#1A1A1A" }}
          >
            <RefreshCw size={13} className={reportsLoading ? "animate-spin" : ""} />
            새로고침
          </button>
        </div>

        {/* 에러 */}
        {error && (
          <p className="text-sm mb-4 font-bold" style={{ color: "#FF6B6B" }}>{error}</p>
        )}

        {/* 로딩 */}
        {reportsLoading ? (
          <div className="py-24 flex justify-center">
            <Loader2 size={28} className="animate-spin" style={{ color: "#1A1A1A" }} />
          </div>
        ) : (

          /* 리포트 테이블 */
          <div className="neo-card overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="border-b-2" style={{ borderColor: "#1A1A1A", backgroundColor: "#F0EFEC" }}>
                <tr>
                  <th className="px-5 py-3 font-black text-xs" style={{ color: "#1A1A1A" }}>상태 / 게임명</th>
                  <th className="px-5 py-3 font-black text-xs" style={{ color: "#1A1A1A" }}>요청일</th>
                  <th className="px-5 py-3 font-black text-xs text-right" style={{ color: "#1A1A1A" }}>관리</th>
                </tr>
              </thead>
              <tbody>
                {reports.length === 0 ? (
                  <tr>
                    <td colSpan={3} className="px-5 py-12 text-center text-sm font-bold"
                      style={{ color: "#9CA3AF" }}>
                      리포트가 없습니다.
                    </td>
                  </tr>
                ) : reports.map((r, i) => (
                  <tr
                    key={r.uuid}
                    className={r.hidden ? "opacity-40" : ""}
                    style={{
                      borderTop: i === 0 ? "none" : "1px solid #E2E8F0",
                    }}
                  >
                    {/* 게임명 + 상태 */}
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="font-black text-sm" style={{ color: "#1A1A1A" }}>
                          {r.gameName || r.galleryName || "알 수 없음"}
                        </span>
                        {/* 상태 배지 */}
                        <span
                          className="text-[10px] font-black px-2 py-0.5 rounded-full border-2"
                          style={{
                            borderColor: "#1A1A1A",
                            backgroundColor:
                              r.status === "COMPLETED" ? "#56D0A0" :
                              r.status === "PENDING"   ? "#FFD600" : "#FF6B6B",
                            color:
                              r.status === "FAILED" ? "#FFFFFF" : "#1A1A1A",
                          }}
                        >
                          {r.status === "COMPLETED" ? "완료" : r.status === "PENDING" ? "진행 중" : "실패"}
                        </span>
                        {r.hidden && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full border"
                            style={{ borderColor: "#E2E8F0", color: "#9CA3AF" }}>
                            숨김
                          </span>
                        )}
                      </div>
                      <p className="font-mono text-[11px]" style={{ color: "#9CA3AF" }}>
                        {r.uuid}
                      </p>
                    </td>

                    {/* 요청일 */}
                    <td className="px-5 py-3.5 text-xs" style={{ color: "#4A4A4A" }}>
                      {new Date(r.requestedAt).toLocaleString("ko-KR")}
                    </td>

                    {/* 관리 버튼 */}
                    <td className="px-5 py-3.5 text-right">
                      <div className="inline-flex items-center gap-2">
                        <button
                          onClick={() => handleAction(r.index, r.hidden ? "SHOW" : "HIDE")}
                          className="neo-button flex items-center gap-1 px-3 py-1.5 text-xs"
                          style={{ backgroundColor: "#F0EFEC", color: "#1A1A1A" }}
                          title={r.hidden ? "숨김 해제" : "숨기기"}
                        >
                          {r.hidden ? <Eye size={12} /> : <EyeOff size={12} />}
                          {r.hidden ? "해제" : "숨김"}
                        </button>
                        <button
                          onClick={() => handleAction(r.index, "DELETE")}
                          className="neo-button flex items-center gap-1 px-3 py-1.5 text-xs"
                          style={{ backgroundColor: "#FF6B6B", color: "#FFFFFF", borderColor: "#1A1A1A" }}
                          title="영구 삭제"
                        >
                          <Trash2 size={12} />
                          삭제
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  );
}
