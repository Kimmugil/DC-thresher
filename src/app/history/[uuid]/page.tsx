"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Loader2, Calendar, AlertTriangle, MessageSquare, Flame, CheckCircle2, RefreshCw } from "lucide-react";
import axios from "axios";

interface ReportData {
  uuid: string;
  status: "PENDING" | "COMPLETED" | "FAILED";
  galleryName?: string;
  gameName?: string;
  requestedAt?: string;
  completedAt?: string;
  aiInsights?: string; // Stored as JSON string in sheets
  rawData?: string;    // Stored as JSON string in sheets
}

export default function ReportPage() {
  const { uuid } = useParams();
  const router = useRouter();
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [insights, setInsights] = useState<{
    gallery_summary?: string;
    key_topics?: { topic: string; details: string }[];
    complaints?: { issue: string; severity: string; context: string; suggestion: string }[];
    action_plans?: string[];
  } | null>(null);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        const res = await axios.get(`/api/history/${uuid}`);
        const data = res.data.report;
        setReport(data);

        if (data.status === "COMPLETED" && data.aiInsights) {
          try {
            setInsights(JSON.parse(data.aiInsights));
          } catch (e) {
            console.error("Failed to parse AI Insights JSON", e);
          }
        }
      } catch (err: unknown) {
        const axiosError = err as { response?: { status?: number } };
        if (axiosError.response?.status === 404) {
          setError("해당 리포트를 찾을 수 없습니다.");
        } else {
          setError("리포트를 불러오는 중 오류가 발생했습니다.");
        }
      } finally {
        setLoading(false);
      }
    };

    fetchReport();
    
    // Auto refresh if pending
    let interval: NodeJS.Timeout;
    if (report?.status === "PENDING") {
      interval = setInterval(() => {
        fetchReport();
      }, 10000); // Check every 10 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [uuid, report?.status]);

  if (loading && !report) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
        <Loader2 className="animate-spin text-blue-600 mb-4" size={48} />
        <p className="text-gray-600 font-medium text-lg">리포트 데이터를 불러오는 중...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 p-4">
        <div className="bg-white p-8 rounded-3xl shadow-lg text-center max-w-md w-full">
          <AlertTriangle className="text-red-500 mx-auto mb-4" size={48} />
          <h2 className="text-2xl font-bold text-gray-800 mb-2">오류 발생</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button 
            onClick={() => router.push('/history')}
            className="bg-blue-600 text-white px-6 py-3 rounded-xl font-medium hover:bg-blue-700 transition w-full"
          >
            목록으로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  if (report?.status === "PENDING") {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 p-4">
        <div className="bg-white p-10 rounded-3xl shadow-xl text-center max-w-lg w-full border border-blue-100 relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-400 to-indigo-500 animate-pulse" />
          
          <RefreshCw className="text-blue-500 mx-auto mb-6 animate-spin" size={56} />
          <h2 className="text-2xl font-extrabold text-gray-900 mb-3">AI가 갤러리를 분석 중입니다</h2>
          <p className="text-gray-600 mb-6">
            스크래핑 및 AI 분석에는 갤러리 규모에 따라 약 1~3분이 소요됩니다.<br/>
            이 페이지를 켜두시면 분석 완료 시 자동으로 화면이 갱신됩니다.
          </p>
          
          <div className="bg-gray-50 p-4 rounded-xl text-left border border-gray-100">
            <p className="text-sm text-gray-500 flex justify-between mb-1">
              <span>요청 ID</span> <span className="font-mono">{uuid?.slice(0,8)}...</span>
            </p>
            <p className="text-sm text-gray-500 flex justify-between">
              <span>요청 시간</span> <span>{report.requestedAt ? new Date(report.requestedAt).toLocaleTimeString() : '-'}</span>
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-[#f8fafc]">
      {/* Navbar */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <button 
            onClick={() => router.push('/history')}
            className="flex items-center gap-2 text-gray-600 hover:text-blue-600 font-medium transition-colors"
          >
            <ArrowLeft size={20} />
            목록으로
          </button>
          <div className="font-bold text-gray-800 hidden sm:block">
            {report?.gameName || 'AI 분석 리포트'}
          </div>
          <div className="text-sm text-gray-500 font-mono">
            {uuid?.slice(0,8)}
          </div>
        </div>
      </nav>

      {/* Header Profile */}
      <header className="bg-white border-b border-gray-200 pt-10 pb-12 mb-8">
        <div className="max-w-5xl mx-auto px-4">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="bg-blue-100 text-blue-800 text-xs font-bold px-2.5 py-1 rounded-md">
                  분석 완료
                </span>
                <span className="text-sm text-gray-500 flex items-center gap-1">
                  <Calendar size={14} /> 
                  {report?.completedAt ? new Date(report.completedAt).toLocaleString('ko-KR') : '-'}
                </span>
              </div>
              <h1 className="text-4xl md:text-5xl font-black text-gray-900 tracking-tight mb-2">
                {report?.gameName || '게임명 확인 불가'}
              </h1>
              <p className="text-xl text-gray-600 font-medium">
                {report?.galleryName || '갤러리명'}
              </p>
            </div>
            
            {insights?.gallery_summary && (
              <div className="bg-indigo-50 border border-indigo-100 p-5 rounded-2xl max-w-sm">
                <p className="text-sm font-bold text-indigo-900 mb-1">한줄 요약</p>
                <p className="text-indigo-800 font-medium">&quot;{insights.gallery_summary}&quot;</p>
              </div>
            )}
          </div>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-4 pb-20 space-y-8">
        
        {/* Core Insights Grid */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* Main Topics */}
          <section className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100">
            <h2 className="text-2xl font-bold flex items-center gap-2 mb-6 text-gray-900 border-b pb-4">
              <MessageSquare className="text-blue-500" /> 핵심 여론 및 주요 주제
            </h2>
            <div className="space-y-4">
              {insights?.key_topics ? insights.key_topics.map((topic: { topic: string, details: string }, idx: number) => (
                <div key={idx} className="bg-gray-50 rounded-xl p-4 border border-gray-100">
                  <h3 className="font-bold text-lg text-gray-800 mb-1">{idx + 1}. {topic.topic}</h3>
                  <p className="text-gray-600 text-sm">{topic.details}</p>
                </div>
              )) : (
                <p className="text-gray-500">데이터를 분석할 수 없습니다.</p>
              )}
            </div>
          </section>

          {/* Issues / Fire */}
          <section className="bg-white rounded-3xl p-8 shadow-sm border border-gray-100">
            <h2 className="text-2xl font-bold flex items-center gap-2 mb-6 text-gray-900 border-b pb-4">
              <Flame className="text-red-500" /> 불만 및 민심 (이슈)
            </h2>
            <div className="space-y-4">
              {insights?.complaints ? insights.complaints.map((comp: { issue: string, severity: string, context: string, suggestion: string }, idx: number) => (
                <div key={idx} className="bg-red-50 rounded-xl p-4 border border-red-100">
                  <div className="flex justify-between items-start mb-1">
                    <h3 className="font-bold text-lg text-red-900">{comp.issue}</h3>
                    <span className="text-xs font-bold px-2 py-1 bg-red-100 text-red-800 rounded-lg">
                      심각도: {comp.severity}
                    </span>
                  </div>
                  <p className="text-red-800/80 text-sm mb-2">{comp.context}</p>
                  <div className="bg-white/60 p-2 rounded-lg text-sm text-red-900/90 font-medium">
                    💡 제언: {comp.suggestion}
                  </div>
                </div>
              )) : (
                <p className="text-gray-500">분석된 불만 사항이 없습니다.</p>
              )}
            </div>
          </section>
        </div>

        {/* Actionable Advice */}
        <section className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-3xl p-8 shadow-lg text-white">
          <h2 className="text-2xl font-bold flex items-center gap-2 mb-6 border-b border-gray-700 pb-4">
            <CheckCircle2 className="text-green-400" /> 운영진/개발자를 위한 액션 플랜
          </h2>
          <div className="grid sm:grid-cols-2 gap-4">
            {insights?.action_plans ? insights.action_plans.map((plan: string, idx: number) => (
              <div key={idx} className="bg-white/10 rounded-xl p-4 backdrop-blur-sm">
                <p className="font-medium text-blue-100 leading-relaxed">
                  <span className="text-blue-400 font-black mr-2">{idx + 1}.</span>
                  {plan}
                </p>
              </div>
            )) : (
              <p className="text-gray-400">제공된 액션 플랜이 없습니다.</p>
            )}
          </div>
        </section>

      </div>
    </main>
  );
}
