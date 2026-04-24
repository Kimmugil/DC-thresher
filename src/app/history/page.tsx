"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { History, ArrowLeft, ExternalLink, Calendar, Gamepad2, FileText } from "lucide-react";
import axios from "axios";
import Link from "next/link";

interface Report {
  uuid: string;
  gameName: string;
  galleryName: string;
  requestedAt: string;
  status: "PENDING" | "COMPLETED" | "FAILED";
}

export default function HistoryPage() {
  const router = useRouter();
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        // This endpoint will be implemented later to fetch from Google Sheets
        const res = await axios.get("/api/history");
        setReports(res.data.reports);
      } catch (err) {
        console.error(err);
        // Fallback for development/UI design until API is ready
        setError("리포트 목록을 불러오지 못했습니다. 임시 데이터를 표시합니다.");
        setReports([
          { uuid: "123e4567-e89b-12d3-a456-426614174000", gameName: "로스트아크", galleryName: "로스트아크 갤러리", requestedAt: "2024-05-20T10:30:00Z", status: "COMPLETED" },
          { uuid: "223e4567-e89b-12d3-a456-426614174001", gameName: "메이플스토리", galleryName: "메이플스토리 갤러리", requestedAt: "2024-05-19T14:20:00Z", status: "COMPLETED" },
          { uuid: "323e4567-e89b-12d3-a456-426614174002", gameName: "명조", galleryName: "명조 마이너 갤러리", requestedAt: "2024-05-18T09:15:00Z", status: "PENDING" },
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  return (
    <main className="min-h-screen bg-gray-50 p-4 md:p-8">
      <div className="max-w-5xl mx-auto">
        <button 
          onClick={() => router.push('/')}
          className="flex items-center gap-2 text-gray-500 hover:text-blue-600 font-medium mb-8 transition-colors"
        >
          <ArrowLeft size={20} />
          새로운 분석 요청하기
        </button>

        <div className="flex items-end justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
              <History className="text-blue-600" /> 분석 리포트 보관함
            </h1>
            <p className="text-gray-600">지금까지 발행된 DC-Thresher AI 리포트 목록입니다.</p>
          </div>
        </div>

        {error && (
          <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-xl mb-6">
            {error}
          </div>
        )}

        {loading ? (
          <div className="grid gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 animate-pulse flex h-32" />
            ))}
          </div>
        ) : reports.length === 0 ? (
          <div className="bg-white rounded-3xl border border-dashed border-gray-300 p-16 text-center">
            <FileText className="mx-auto text-gray-300 mb-4" size={48} />
            <h3 className="text-xl font-bold text-gray-700 mb-2">아직 발행된 리포트가 없습니다</h3>
            <p className="text-gray-500">첫 번째 갤러리 분석을 요청해보세요.</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {reports.map((report) => (
              <Link 
                href={`/history/${report.uuid}`} 
                key={report.uuid}
                className="group bg-white p-6 rounded-2xl shadow-sm border border-gray-100 hover:border-blue-200 hover:shadow-md transition-all flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 cursor-pointer"
              >
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <span className="bg-gray-100 text-gray-600 text-xs font-bold px-2.5 py-1 rounded-md uppercase tracking-wider">
                      {report.status}
                    </span>
                    <span className="flex items-center gap-1.5 text-sm text-gray-500 font-medium">
                      <Calendar size={14} /> 
                      {new Date(report.requestedAt).toLocaleString('ko-KR')}
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2 group-hover:text-blue-600 transition-colors">
                    {report.gameName || '알 수 없는 게임'}
                  </h3>
                  <p className="text-gray-500 text-sm flex items-center gap-1 mt-1">
                    <Gamepad2 size={14} /> {report.galleryName || '갤러리명 수집중...'}
                  </p>
                </div>
                
                <div className="flex items-center gap-2 text-blue-600 font-semibold bg-blue-50 px-4 py-2 rounded-xl group-hover:bg-blue-600 group-hover:text-white transition-colors w-full sm:w-auto justify-center">
                  리포트 보기 <ExternalLink size={16} />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
