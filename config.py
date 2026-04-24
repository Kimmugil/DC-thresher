import os

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

# ─────────────────────────────────────────────
# 환경 스위치
# ─────────────────────────────────────────────
ENV = "dev"

APP_VERSION     = "v2.0.0"
ENV_NAME        = ENV.upper()
TICKER_INTERVAL = 2.5

# API 키
if HAS_STREAMLIT:
    try:
        GEMINI_API_KEY     = st.secrets[ENV]["GEMINI_API_KEY"]
        NOTION_TOKEN       = st.secrets[ENV]["NOTION_TOKEN"]
        NOTION_DATABASE_ID = st.secrets[ENV]["NOTION_DATABASE_ID"]
    except Exception:
        GEMINI_API_KEY     = os.environ.get("GEMINI_API_KEY", "")
        NOTION_TOKEN       = os.environ.get("NOTION_TOKEN", "")
        NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "")
else:
    GEMINI_API_KEY     = os.environ.get("GEMINI_API_KEY", "")
    NOTION_TOKEN       = os.environ.get("NOTION_TOKEN", "")
    NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "")

# ─────────────────────────────────────────────
# 스크래핑 설정
# ─────────────────────────────────────────────
SCRAPE_DELAY_MIN  = 0.4
SCRAPE_DELAY_MAX  = 0.8
DETAIL_DELAY_MIN  = 0.5
DETAIL_DELAY_MAX  = 1.0
REQUEST_TIMEOUT   = 6
BODY_MAX_CHARS    = 800

# ─────────────────────────────────────────────
# [v3 신규] 진단 전략 설정
# ─────────────────────────────────────────────
# "최소 DIAG_MIN_POSTS개 이상 AND 최소 DIAG_MIN_DAYS일 이상" 조건 충족 시
# 해당 날짜 경계(00:00)에서 진단 종료. 단, DIAG_MAX_DAYS 일치를 초과하지 않음.
DIAG_MIN_POSTS = 200   # 최소 수집 게시글 수
DIAG_MIN_DAYS  = 3     # 최소 수집 기간(일)
DIAG_MAX_DAYS  = 14    # 최대 수집 기간(일)

# [v3 신규] 분석용 개념글 최소 표본 수. 부족 시 고댓글 일반글로 보충.
ANALYSIS_MIN_CONCEPT_POSTS = 50

# ─────────────────────────────────────────────
# 갤러리 서브타입 정의
# ─────────────────────────────────────────────
GALLERY_SUBTYPES = {
    "pre_launch": {
        "label": "출시 전 기대형", "emoji": "🌱", "color": "#2d9e6b",
        "desc": "게임 출시 전, 기대·정보 공유 중심 갤러리",
        "analysis_focus": "기대 포인트, 우려 사항, 유저들이 주목하는 요소 중심",
    },
    "early_launch": {
        "label": "출시 초기형", "emoji": "🚀", "color": "#3b4890",
        "desc": "출시 직후, 버그 제보·초기 반응·감상 중심",
        "analysis_focus": "첫인상, 초기 버그 현황, 온보딩 경험 중심",
    },
    "stable": {
        "label": "안정기형", "emoji": "📚", "color": "#1d7a3a",
        "desc": "공략·빌드·정보 글 비중이 높은 성숙한 갤러리",
        "analysis_focus": "게임 완성도, 장기 유저 만족도, 메타 변화 중심",
    },
    "issue_burst": {
        "label": "이슈 폭발형", "emoji": "🔥", "color": "#c0392b",
        "desc": "패치·운영 논란으로 부정 여론이 급등 중인 갤러리",
        "analysis_focus": "이슈 원인 추적, 이탈 위험, 긴급 대응 항목 중심",
    },
    "decline": {
        "label": "쇠퇴기형", "emoji": "📉", "color": "#7f8c8d",
        "desc": "리젠 감소, 이탈 논의가 늘어나는 갤러리",
        "analysis_focus": "이탈 원인, 잔류 유저 심리, 부활 가능성 요소 중심",
    },
}

# [v3 신규] 분석 방향 옵션 (Step 2에서 유저가 선택 가능)
ANALYSIS_FOCUS_OPTIONS = {
    "default":    "AI 자동 판단 (권장)",
    "complaint":  "불만/이슈 집중 분석",
    "positive":   "긍정 여론 및 강점 발굴",
    "churn":      "이탈 위험 신호 집중 분석",
    "balance":    "밸런스/게임성 집중 분석",
    "operation":  "운영/소통 집중 분석",
}

SUBTYPE_KEYWORDS = {
    "pre_launch":   ["출시", "오픈", "cbt", "사전예약", "기다린다", "언제나와", "기대", "런칭", "오픈베타", "얼리액세스"],
    "early_launch": ["버그", "오류", "출시", "첫날", "시작했", "다운로드", "설치", "입문", "뉴비"],
    "stable":       ["공략", "빌드", "덱", "tier", "티어", "메타", "가이드", "추천", "세팅", "조합"],
    "issue_burst":  ["환불", "패치", "운영", "너프", "상향", "하향", "논란", "사과", "공지", "망함", "최악", "실망"],
    "decline":      ["접종", "탈겜", "삭제", "손절", "갈아탐", "예전엔", "옛날엔", "망겜", "폐겜", "추억"],
}

COMPLAINT_CATEGORIES = {
    "balance":   {"label": "밸런스/게임성",   "emoji": "⚖️",
                  "keywords": ["사기", "너프", "상향", "메타", "밸런스", "OP", "tier"],
                  "score_logic": "해당 키워드 등장 게시글 수 × 감정 강도 가중치"},
    "operation": {"label": "운영/소통",        "emoji": "📢",
                  "keywords": ["운영", "공지", "답변", "소통", "CS", "고객센터"],
                  "score_logic": "운영 관련 키워드 빈도 × 부정 감정 강도"},
    "bug":       {"label": "버그/최적화",      "emoji": "🐛",
                  "keywords": ["버그", "렉", "팅김", "오류", "크래시", "최적화"],
                  "score_logic": "버그 보고 게시글 수 × 심각도 가중치"},
    "payment":   {"label": "과금/BM",          "emoji": "💳",
                  "keywords": ["뽑기", "현질", "과금", "가챠", "BM", "현금", "스킨"],
                  "score_logic": "과금 관련 부정 언급 빈도 × 확산도"},
    "content":   {"label": "콘텐츠/업데이트",  "emoji": "🎮",
                  "keywords": ["업데이트", "할게없", "노잼", "루틴", "콘텐츠", "반복"],
                  "score_logic": "콘텐츠 부족 키워드 빈도 × 이탈 신호 연관도"},
}

CHURN_SIGNALS = {
    "strong":  ["환불", "삭제", "접종", "탈겜", "손절", "갈아탄", "언인스톨"],
    "medium":  ["쉬어야", "잠깐 쉬", "지쳐서", "재미없어졌", "질렸"],
    "migrate": ["로 갈아", "시작했", "이거 말고", "대신"],
}

ACTION_PRIORITY = {
    "urgent":  {"label": "긴급",         "emoji": "🚨", "color": "#c0392b"},
    "monitor": {"label": "모니터링 필요", "emoji": "👀", "color": "#e67e22"},
    "note":    {"label": "참고",          "emoji": "📝", "color": "#2980b9"},
}

NOTION_SECTION_ORDER = [
    "bot_info", "ai_one_liner", "gallery_profile", "sentiment_gauge",
    "issue_timeline", "complaint_categories", "churn_signals",
    "segment_analysis", "pm_checklist", "patch_timeline", "raw_data",
]