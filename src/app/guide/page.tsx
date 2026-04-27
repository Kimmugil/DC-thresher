import { BookOpen, Search, Database, Bot, Sparkles, CheckCircle } from "lucide-react";

export default function GuidePage() {
  return (
    <main className="min-h-screen py-10 px-5" style={{ backgroundColor: "var(--bg-base)" }}>
      <div className="max-w-4xl mx-auto space-y-10">
        
        <header className="text-center border-b pb-10" style={{ borderColor: "var(--border)" }}>
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-6 bg-indigo-500/10">
            <BookOpen size={32} className="text-indigo-400" />
          </div>
          <h1 className="text-3xl md:text-4xl font-black mb-4" style={{ color: "var(--text-primary)" }}>
            DC-Thresher 분석 가이드
          </h1>
          <p className="text-lg" style={{ color: "var(--text-secondary)" }}>
            AI가 디시인사이드 갤러리 여론을 어떻게 분석하는지 투명하게 공개합니다.
          </p>
        </header>

        <section className="space-y-6">
          <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
            <Search className="text-emerald-400" /> 1. 데이터 수집 단계
          </h2>
          <div className="p-6 rounded-2xl border leading-relaxed space-y-4" style={{ backgroundColor: "var(--bg-surface)", borderColor: "var(--border)", color: "var(--text-secondary)" }}>
            <p>
              유저가 갤러리 URL을 입력하면, 시스템은 즉시 해당 갤러리의 최근 게시글들을 수집하기 시작합니다. 
              단순히 최신 글을 몇 개 긁어오는 것이 아니라, <strong>가장 화제성이 높은 핵심 데이터</strong>를 선별하기 위해 특별한 과정을 거칩니다.
            </p>
            <ul className="list-disc pl-5 space-y-2">
              <li>초기 수집기로 갤러리의 최신 글 리젠율을 분석하여 적절한 수집 기간을 자동 산출합니다. (최대 7일)</li>
              <li>해당 기간 내의 수많은 게시글(많게는 수만 개)의 메타데이터(제목, 댓글 수, 조회수 등)를 빠르게 스캔합니다.</li>
              <li>스캔된 전체 게시글 중 <strong>댓글 수가 가장 많은 상위 100개</strong>의 게시글을 최종 '분석 표본'으로 확정하고 본문 내용까지 깊게 파싱합니다.</li>
            </ul>
            <p className="text-sm mt-4 p-3 rounded-lg bg-emerald-400/10 text-emerald-400/90">
              💡 <strong>왜 댓글 수 기준 상위 100개인가요?</strong> <br />
              갤러리 특성상 의미 없는 뻘글이나 단순 질문글이 대다수를 차지합니다. 댓글이 많이 달린 글(일명 떡밥글)이야말로 현재 유저들이 가장 주목하고 격렬하게 논의 중인 진짜 '여론'이기 때문입니다.
            </p>
          </div>
        </section>

        <section className="space-y-6">
          <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
            <Bot className="text-indigo-400" /> 2. AI 분석 단계
          </h2>
          <div className="p-6 rounded-2xl border leading-relaxed space-y-4" style={{ backgroundColor: "var(--bg-surface)", borderColor: "var(--border)", color: "var(--text-secondary)" }}>
            <p>
              수집된 100개의 핵심 게시글(제목, 본문, 댓글 반응 포함)은 고성능 AI 모델인 <strong>Google Gemini 1.5 Pro</strong>에게 전달됩니다.
              단순한 감정 분석(긍/부정 단어 개수 세기)이 아닌, 문맥을 이해하는 심층 분석이 진행됩니다.
            </p>
            <ul className="list-disc pl-5 space-y-2">
              <li><strong>게임 및 운영진에 대한 유저의 평가</strong>를 기준으로 긍정과 부정 여론을 엄격하게 분리합니다. (예: 유저들끼리 뭉쳐서 트럭 시위를 준비하는 '단합력'은 긍정이 아니라 분노에서 비롯된 '부정적 이슈'로 정확히 분류합니다.)</li>
              <li>단순한 불평불만이 아닌, 구체적으로 어떤 콘텐츠(BM, 밸런스, 이벤트 등)에서 불타오르고 있는지 카테고리화합니다.</li>
              <li>각 여론과 이슈가 사실임을 증명하기 위해, AI가 <strong>직접 원본 게시글의 제목과 URL을 매칭</strong>하여 레퍼런스로 첨부합니다.</li>
            </ul>
          </div>
        </section>

        <section className="space-y-6">
          <h2 className="text-2xl font-bold flex items-center gap-2" style={{ color: "var(--text-primary)" }}>
            <Sparkles className="text-amber-400" /> 3. 리포트 발행 및 확인
          </h2>
          <div className="p-6 rounded-2xl border leading-relaxed space-y-4" style={{ backgroundColor: "var(--bg-surface)", borderColor: "var(--border)", color: "var(--text-secondary)" }}>
            <p>
              모든 분석이 완료되면 JSON 형태의 결과물을 시각적인 리포트 대시보드로 변환하여 제공합니다.
            </p>
            <ul className="space-y-3 mt-4">
              <li className="flex items-start gap-2">
                <CheckCircle className="text-amber-400 shrink-0 mt-1" size={16} />
                <span><strong>투명성 지표:</strong> 리포트 상단에서 전체 데이터가 몇 개였고, 그중 1등 댓글 글과 100등(커트라인) 댓글 글이 무엇이었는지 가감 없이 공개합니다.</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="text-amber-400 shrink-0 mt-1" size={16} />
                <span><strong>주요 여론 & 이슈:</strong> 한눈에 들어오는 카드 형태로 정리되며, 카드 하단의 레퍼런스 링크를 눌러 실제 디시인사이드 원문으로 바로 이동해 팩트 체크를 할 수 있습니다.</span>
              </li>
            </ul>
          </div>
        </section>

      </div>
    </main>
  );
}
