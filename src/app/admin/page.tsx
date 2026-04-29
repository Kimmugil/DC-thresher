"use client";

import { useState, useEffect } from "react";
import { Lock, EyeOff, Eye, Trash2, ShieldCheck, Loader2 } from "lucide-react";
import axios from "axios";

export default function AdminPage() {
  const [password, setPassword] = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [error, setError] = useState("");

  const [reports, setReports] = useState<any[]>([]);
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
      setError(err.response?.data?.message || "비밀번호가 틀렸거나 서버 오류가 발생했습니다.");
    } finally {
      setAuthLoading(false);
    }
  };

  const fetchReports = async () => {
    setReportsLoading(true);
    try {
      const res = await axios.get("/api/admin/reports");
      setReports(res.data.reports || []);
    } catch (e) {
      setError("리포트 목록을 불러오지 못했습니다.");
    } finally {
      setReportsLoading(false);
    }
  };

  const handleAction = async (rowIndex: number, action: "HIDE" | "SHOW" | "DELETE") => {
    if (action === "DELETE" && !confirm("이 리포트를 마스터 시트에서 완전히 삭제하시겠습니까? (복구 불가)")) return;
    
    try {
      await axios.post("/api/admin/reports", { rowIndex, action });
      fetchReports(); // Refresh
    } catch (e) {
      alert("작업에 실패했습니다.");
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4" style={{ backgroundColor: "var(--bg-base)" }}>
        <form onSubmit={handleAuth} className="max-w-sm w-full p-8 rounded-2xl border" style={{ backgroundColor: "var(--bg-surface)", borderColor: "var(--border)" }}>
          <ShieldCheck size={40} className="mx-auto mb-4 text-indigo-400" />
          <h2 className="text-xl font-bold text-center mb-6" style={{ color: "var(--text-primary)" }}>관리자 패널</h2>
          
          <div className="mb-4 relative">
            <Lock size={16} className="absolute left-3 top-3 text-gray-400" />
            <input type="password" placeholder="비밀번호 입력"
              value={password} onChange={(e) => setPassword(e.target.value)}
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border text-sm"
              style={{ backgroundColor: "var(--bg-base)", borderColor: "var(--border)", color: "var(--text-primary)" }}
            />
          </div>

          {error && <p className="text-red-400 text-xs mb-4 text-center">{error}</p>}

          <button type="submit" disabled={authLoading}
            className="w-full py-2.5 rounded-xl text-sm font-bold transition-colors flex items-center justify-center gap-2"
            style={{ backgroundColor: "#18181B", color: "#FFFFFF" }}>
            {authLoading ? <Loader2 size={16} className="animate-spin" /> : "로그인"}
          </button>
        </form>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8" style={{ backgroundColor: "var(--bg-base)" }}>
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
            <ShieldCheck className="text-indigo-400" /> 관리자 대시보드
          </h1>
          <button onClick={fetchReports} className="text-sm font-semibold px-4 py-2 rounded-lg border hover:bg-white/5 transition-colors"
            style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}>
            새로고침
          </button>
        </div>

        {reportsLoading ? (
          <div className="py-20 flex justify-center"><Loader2 className="animate-spin text-indigo-400" /></div>
        ) : (
          <div className="rounded-xl border overflow-hidden" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-surface)" }}>
            <table className="w-full text-left text-sm">
              <thead className="border-b" style={{ borderColor: "var(--border)", backgroundColor: "var(--bg-raised)" }}>
                <tr>
                  <th className="px-4 py-3 font-semibold" style={{ color: "var(--text-secondary)" }}>상태/게임명</th>
                  <th className="px-4 py-3 font-semibold" style={{ color: "var(--text-secondary)" }}>요청일</th>
                  <th className="px-4 py-3 font-semibold text-right" style={{ color: "var(--text-secondary)" }}>관리</th>
                </tr>
              </thead>
              <tbody className="divide-y" style={{ borderColor: "var(--border)" }}>
                {reports.map((r) => (
                  <tr key={r.uuid} className={r.hidden ? "opacity-50" : ""}>
                    <td className="px-4 py-3">
                      <div className="font-bold mb-1 flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
                        {r.gameName || r.galleryName || "알 수 없음"}
                        {r.hidden && <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-500/20 text-gray-400">숨김처리됨</span>}
                      </div>
                      <div className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>{r.uuid} | {r.status}</div>
                    </td>
                    <td className="px-4 py-3 text-xs" style={{ color: "var(--text-secondary)" }}>
                      {new Date(r.requestedAt).toLocaleString("ko-KR")}
                    </td>
                    <td className="px-4 py-3 text-right space-x-2">
                      <button onClick={() => handleAction(r.index, r.hidden ? "SHOW" : "HIDE")}
                        className="p-1.5 rounded-md border hover:bg-white/5 transition-colors"
                        style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
                        title={r.hidden ? "숨김 해제" : "숨기기"}>
                        {r.hidden ? <Eye size={14} /> : <EyeOff size={14} />}
                      </button>
                      <button onClick={() => handleAction(r.index, "DELETE")}
                        className="p-1.5 rounded-md border hover:bg-red-500/10 transition-colors text-red-400"
                        style={{ borderColor: "var(--border)" }}
                        title="영구 삭제">
                        <Trash2 size={14} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
