"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Search, History, ArrowRight, Loader2, Info } from "lucide-react";
import axios from "axios";

export default function Home() {
  const router = useRouter();
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [statusMsg, setStatusMsg] = useState("");

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setStatusMsg("");

    if (!url.trim()) {
      setError("디시인사이드 갤러리 URL을 입력해주세요.");
      return;
    }
    
    if (!url.includes("gall.dcinside.com")) {
      setError("올바른 디시인사이드 갤러리 URL이 아닙니다.");
      return;
    }

    try {
      setLoading(true);
      setStatusMsg("서버에 분석 요청을 보내는 중...");
      
      const res = await axios.post("/api/analyze", { url });
      
      setStatusMsg("요청 성공! 백그라운드 분석이 시작되었습니다.");
      
      // Delay briefly to show success, then route to the history item (or a pending view)
      setTimeout(() => {
        router.push(`/history/${res.data.uuid}`);
      }, 1500);

    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { message?: string } } };
      setError(axiosError.response?.data?.message || "분석 요청에 실패했습니다. 관리자에게 문의하세요.");
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-blue-50 flex flex-col items-center justify-center p-4">
      <div className="max-w-3xl w-full">
        {/* Header Section */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-blue-600 text-white shadow-xl mb-6">
            <Search size={40} />
          </div>
          <h1 className="text-4xl font-extrabold text-gray-900 mb-4 tracking-tight">
            DC-Thresher <span className="text-blue-600">AI Report</span>
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            디시인사이드 갤러리 URL을 입력하면, 최근 게시글을 스크래핑하여 Gemini AI가 갤러리의 여론과 주요 키워드를 심층 분석한 리포트를 발행해 드립니다.
          </p>
        </div>

        {/* Action Card */}
        <div className="bg-white rounded-3xl shadow-2xl p-8 md:p-10 border border-gray-100">
          <form onSubmit={handleAnalyze} className="space-y-6">
            <div>
              <label htmlFor="url" className="block text-sm font-semibold text-gray-700 mb-2">
                갤러리 URL 입력
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                  <Search className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="url"
                  id="url"
                  className="block w-full pl-12 pr-4 py-4 border-2 border-gray-200 rounded-2xl text-gray-900 focus:ring-0 focus:border-blue-500 transition-colors bg-gray-50 text-lg outline-none"
                  placeholder="https://gall.dcinside.com/mgallery/board/lists?id=example"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  disabled={loading}
                  required
                />
              </div>
              <p className="mt-3 text-sm text-gray-500 flex items-center gap-1.5">
                <Info size={16} /> 
                마이너, 정식, 미니 갤러리 모두 지원합니다.
              </p>
            </div>

            {error && (
              <div className="bg-red-50 text-red-600 p-4 rounded-xl text-sm border border-red-100 font-medium">
                {error}
              </div>
            )}

            {statusMsg && !error && (
              <div className="bg-blue-50 text-blue-700 p-4 rounded-xl text-sm border border-blue-100 font-medium flex items-center gap-2">
                {loading && <Loader2 className="animate-spin" size={18} />}
                {statusMsg}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white py-4 px-8 rounded-2xl font-bold text-lg transition-all shadow-lg hover:shadow-xl disabled:opacity-70 disabled:cursor-not-allowed flex justify-center items-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="animate-spin" /> 분석 준비 중...
                </>
              ) : (
                <>
                  리포트 발행 시작하기 <ArrowRight />
                </>
              )}
            </button>
          </form>

          <div className="mt-8 pt-8 border-t border-gray-100 text-center">
            <button 
              onClick={() => router.push('/history')}
              className="inline-flex items-center gap-2 text-gray-600 hover:text-blue-600 font-medium transition-colors"
            >
              <History size={18} />
              과거 분석 리포트 열람하기
            </button>
          </div>
        </div>
        
        {/* Notice Section */}
        <div className="mt-12 space-y-4 max-w-2xl mx-auto">
          <div className="bg-white/60 backdrop-blur-sm rounded-2xl p-6 border border-gray-200">
            <h3 className="font-bold text-gray-800 mb-3 flex items-center gap-2">
              <span className="bg-blue-100 text-blue-700 p-1.5 rounded-lg text-xs">안내</span>
              알아두세요
            </h3>
            <ul className="text-sm text-gray-600 space-y-2 list-disc pl-5">
              <li>실시간 스크래핑 방식으로 동작하므로 갤러리 글 리젠 속도에 따라 <span className="font-bold">분석에 1~3분 가량 소요</span>될 수 있습니다.</li>
              <li>생성된 리포트는 누구나 열람할 수 있도록 고유 링크가 제공되며 구글 스프레드시트에 영구 저장됩니다.</li>
            </ul>
          </div>
        </div>

      </div>
    </main>
  );
}
