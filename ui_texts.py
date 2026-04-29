"""
ui_texts.py v10
- 과대 멘트 전면 담백화 (subtitle, ticker, sidebar caption 등)
- STEP1_GAME_WRONG_HINT에 "AI 분석에 영향을 줍니다" 복구
- 진단 AI 프롬프트: 갤러리명 HTML title 태그 우선 사용 명시 강화
- 메인 분석 프롬프트: positive/negative 최대 5개 제한
- major_issues: title/detail 분리 스키마로 변경 (볼드+줄바꿈용)
- STEP2_INFO_TMPL ** 완전 제거
"""

# ── 앱 기본 ──────────────────────────────────────────────────────
APP_PAGE_TITLE = "DC 게임 갤러리 탈곡기"
APP_PAGE_ICON  = "🚜"

# ── 사이드바 ──────────────────────────────────────────────────────
SIDEBAR_TOOL_NAME        = "🚜 DC 탈곡기"
SIDEBAR_TOOL_CAPTION     = "디씨인사이드 게임 갤러리 현황 파악 툴"
SIDEBAR_STEP_TITLE       = "진행 단계"
SIDEBAR_CURRENT_TARGET   = "현재 분석 대상"
SIDEBAR_VERSION_EXPANDER = "ℹ️ 버전 및 환경 정보"
SIDEBAR_VERSION_LABEL    = "버전:"
SIDEBAR_HISTORY          = ["v2.0.0 — 현황 중심 리포트 전면 개편", "v1.0.0 — 최초 출시"]
SIDEBAR_DAILY_AVG_TMPL   = "일평균 {avg}개 글"

STEP_INFO = [
    ("🔍", "갤러리 진단"),
    ("✅", "게임 확인"),
    ("🌾", "수집 & AI 분석"),
    ("📊", "리포트 검수"),
    ("🎉", "발행 완료"),
]
STEP_GUIDE_MESSAGES = {
    0: "갤러리 URL을 붙여넣고 진단을 시작하세요",
    1: "게임명을 확인하고 분석을 시작하세요",
    2: "수집 & AI 분석 중 — 브라우저를 닫지 마세요",
    3: "리포트를 검토하고 노션으로 발행하세요",
    4: "발행 완료! 노션 리포트를 확인하세요",
}

# ── Step 0 ────────────────────────────────────────────────────────
STEP0_TITLE        = "DC 게임 갤러리 탈곡기"
STEP0_SUBTITLE     = "디씨인사이드 게임 갤러리의 주요 여론과 이슈를 요약해 드립니다"
STEP0_INPUT_HEADER = "분석할 게임 갤러리 URL을 입력하세요"
STEP0_PLACEHOLDER  = "https://gall.dcinside.com/mgallery/board/lists/?id=projectnakwon"
STEP0_CAPTION      = "마이너 갤러리(mgallery), 일반 갤러리 모두 지원합니다."
STEP0_BTN          = "🔍  갤러리 진단 시작"
STEP0_WARN_EMPTY   = "URL을 입력해 주세요."
STEP0_WARN_INVALID = "유효한 디씨인사이드 갤러리 URL을 입력해 주세요."

# ── Step 0 환영 & 유의사항 ────────────────────────────────────────
STEP0_NOTICE_TITLE = "📋 리포트 해석 시 유의사항"
STEP0_NOTICE_ITEMS = [
    "디씨인사이드는 익명성이 강한 커뮤니티로, 부정적·과격한 표현이 전반적으로 많습니다. "
    "리포트 내 부정 여론은 '이런 목소리가 존재한다'는 신호로 해석하되, 전체 유저의 의견으로 일반화하지 마세요.",
    "수집 게시글은 댓글 수 상위 게시글 중심입니다. 화제성이 높은 글이 선정되므로 논란성 주제가 과대 대표될 수 있습니다.",
    "AI 분석은 수집된 데이터의 요약이며, 현실을 100% 반영하지 않을 수 있습니다. "
    "주요 판단은 반드시 원본 게시글(링크 제공)을 직접 확인한 후 내리세요.",
    "언급 빈도 점수·불만 강도 점수는 상대적 지표입니다. 수치 자체보다 항목 간 비교를 중심으로 해석하세요.",
]

# ── Step 0 진단 카드 ─────────────────────────────────────────────
DIAG_CARDS = [
    {"emoji": "🔍", "label": "갤러리 구조 파악 중",       "desc": "게시글 패턴과 리젠 속도를 확인해\n갤러리 유형을 판별합니다"},
    {"emoji": "🚀", "label": "출시 초기 갤러리라면",      "desc": "버그 제보, 초기 반응, 온보딩 이슈\n중심으로 수집을 진행합니다"},
    {"emoji": "🔥", "label": "이슈가 발생한 갤러리라면",  "desc": "논란 원인과 여론 흐름을\n확인합니다"},
    {"emoji": "📚", "label": "안정기 갤러리라면",          "desc": "장기 유저 반응, 밸런스 관련\n주제 중심으로 수집합니다"},
    {"emoji": "📉", "label": "조용한 갤러리라면",          "desc": "이탈 관련 게시글과\n잔류 유저 반응을 확인합니다"},
    {"emoji": "💬", "label": "댓글 많은 글 중심 수집",    "desc": "댓글이 많이 달린 게시글을\n핵심 표본으로 선정합니다"},
]

# ── Step 1 ────────────────────────────────────────────────────────
DIAG_ERROR_LABEL      = "진단 오류"
DIAG_SECTION_SUBTITLE = "아래 결과를 확인하고 게임명이 맞는지 확인하세요."

TOOLTIP_SUBTYPE = (
    "게시글 제목 키워드 패턴과 리젠 속도로\n"
    "자동 감지한 갤러리 유형입니다.\n"
    "AI 분석 방향에 영향을 줍니다."
)
GALLERY_NAME_ANCHOR_ID = "game-name-input"

# 진단 기간 자동 결정 기준
DIAG_PERIOD_CRITERIA = (
    "일평균 200개 이상 → 최근 7일 분석\n"
    "일평균 50~199개 → 최근 14일 분석\n"
    "일평균 49개 이하 → 최근 30일 분석\n"
    "게시글 수가 많은 갤러리일수록 짧은 기간을, 조용한 갤러리는 긴 기간을 설정해 적정 표본을 확보합니다."
)

SUBTYPE_MODAL_BTN   = "갤러리 유형 기준 보기"
SUBTYPE_MODAL_TITLE = "갤러리 유형 분류 기준"
SUBTYPE_MODAL_DESC  = "게시글 제목 키워드 패턴과 리젠 속도를 분석해 5가지 유형으로 자동 분류합니다."
SUBTYPE_DEFINITIONS = [
    {"id": "pre_launch",   "emoji": "🌱", "label": "출시 전 기대형",
     "desc": "게임 출시 전, 기대·정보 공유 중심",
     "criteria": "일평균 30개 미만 + 기대/출시/CBT 키워드 35% 이상",
     "focus": "기대 포인트, 우려 사항 중심 수집"},
    {"id": "early_launch", "emoji": "🚀", "label": "출시 초기형",
     "desc": "출시 직후, 버그 제보·초기 반응 중심",
     "criteria": "출시/버그/뉴비 키워드 25% 이상 + 리젠 상승 중",
     "focus": "첫인상, 초기 버그, 온보딩 반응 수집"},
    {"id": "stable",       "emoji": "📚", "label": "안정기형",
     "desc": "공략·빌드·정보 글 비중이 높은 갤러리",
     "criteria": "공략/빌드/메타 키워드 비중 가장 높음 + 안정적 리젠",
     "focus": "게임 완성도, 장기 유저 반응, 메타 변화 수집"},
    {"id": "issue_burst",  "emoji": "🔥", "label": "이슈 폭발형",
     "desc": "패치·운영 논란으로 부정 여론 급등 중",
     "criteria": "환불/패치/운영 키워드 35% 이상 OR 리젠 급증 1.4배",
     "focus": "이슈 원인, 이탈 관련 게시글 중심 수집"},
    {"id": "decline",      "emoji": "📉", "label": "쇠퇴기형",
     "desc": "리젠 감소, 이탈 논의가 늘어나는 갤러리",
     "criteria": "이탈 키워드 30% 이상 + 최근 리젠 70% 미만",
     "focus": "이탈 원인, 잔류 유저 반응 수집"},
]
SUBTYPE_CRITERIA_PREFIX = "**판별 기준:**"
SUBTYPE_FOCUS_PREFIX    = "**수집 포커스:**"

STEP1_GAME_REASON_LABEL = "추정 근거:"
# #5 복구: AI 분석에 영향을 준다는 안내 포함
STEP1_GAME_WRONG_HINT   = "주제가 틀렸다면 아래 입력창에서 직접 수정하세요. 입력한 주제는 AI 분석 방향에 영향을 줍니다."
COND_GAME_INPUT_LABEL   = "게임명 확인"
COND_GAME_PLACEHOLDER   = "예: 메이플스토리 키우기, 로스트아크, 던전앤파이터"
STEP1_START_BTN         = "🚀  분석 시작"

# ── Step 2 ────────────────────────────────────────────────────────
STEP2_TITLE     = "## 🌾 데이터 수집 & AI 분석"
STEP2_SUBTITLE  = "잠시 기다려 주세요. 브라우저를 닫지 마세요."
STEP2_INFO_TMPL = "📅 분석 기간: 최근 {days}일 · 댓글 수 상위 게시글 집중 수집"

SCRAPE_ERROR_TMPL = "수집 실패: {error}"
AI_ERROR_TMPL     = "AI 분석 실패: {error}"
BTN_BACK          = "← 돌아가기"

# 담백한 전광판 문구
TICKER_MESSAGES = [
    "게시글 목록을 수집하는 중입니다...",
    "댓글 수 기준으로 주요 게시글을 선별하는 중입니다...",
    "선별된 게시글 본문을 읽는 중입니다...",
    "수집된 데이터를 AI에 전달하는 중입니다...",
    "AI가 게시글 내용을 분류하는 중입니다...",
    "이슈 키워드를 집계하는 중입니다...",
    "불만 카테고리를 분류하는 중입니다...",
]

# ── Step 3 (리포트) ───────────────────────────────────────────────
TAB_LABELS = [
    "📈 갤러리 현황",
    "🔥 주요 이슈",
    "💬 주요 동향",
    "📋 원본 데이터",
]

PUBLISH_BTN        = "📤 노션으로 발행하기"
NEW_ANALYSIS_BTN   = "🔄 다른 게임 분석하기"
PUBLISH_STATUS_MSG = "노션 페이지 생성 중..."
PUBLISH_ERROR_TMPL = "노션 발행 실패: {error}"

PROFILE_KEYWORD_TMPL    = "🏷️ 핵심 키워드 TOP 5: {keywords}"
PROFILE_ONELINER_PREFIX = "💬"

ANALYSIS_SPEC_TMPL = (
    "📅 {date_range} · "
    "기간 내 게시글 {total}개 중 댓글 수 상위 {analysis}개 수집"
)

# 동향 점수 기준 박스
COMPLAINT_SCORE_BOX = """
<div style="background:#f8f9fa;border:1px solid #dee2e6;border-radius:8px;
            padding:12px 16px;font-size:0.85rem;margin-bottom:1.2rem;">
  <b style="color:#1e2129;">ℹ️ 동향 강도 점수 기준 (0–10점)</b><br>
  <span style="color:#888;font-weight:700;">0–2점</span> 거의 없음 ·
  <span style="color:#2980b9;font-weight:700;">3–4점</span> 소수 언급 ·
  <span style="color:#e67e22;font-weight:700;">5–6점</span> 반복 언급 ·
  <span style="color:#c0392b;font-weight:700;">7–8점</span> 다수 언급 ·
  <span style="color:#c0392b;font-weight:900;">9–10점</span> 주요 동향<br>
  <span style="color:#888;font-size:0.8rem;">
    분석 게시글 내 해당 카테고리 키워드 언급 비율 기준 (30% 이상→7–10점 / 10–30%→4–6점 / 10% 미만→0–3점)
  </span>
</div>
"""

# 이슈 점수 기준 박스
ISSUE_SCORE_BOX = """
<div style="background:#f8f9fa;border:1px solid #dee2e6;border-radius:8px;
            padding:12px 16px;font-size:0.85rem;margin-bottom:1.2rem;">
  <b style="color:#1e2129;">ℹ️ 언급 빈도 점수 기준 (0–100점)</b><br>
  분석 게시글 중 해당 이슈 관련 키워드가 언급된 게시글 비율을 0–100으로 표시합니다.
</div>
"""

TIMELINE_CHART_TITLE = "일자별 게시글 수 추이"
TIMELINE_NO_DATA     = "날짜 데이터가 없습니다."

ISSUE_TITLE         = "### 🔥 주요 이슈 리스트"
ISSUE_NO_DATA       = "감지된 주요 이슈가 없습니다."
SCORE_BASED_ON_FREQ = "언급 빈도 점수"

COMPLAINT_TITLE         = "주요 동향별 분석"
COMPLAINT_NO_DATA       = "주요 동향 데이터가 없습니다."
COMPLAINT_RADAR_NAME    = "동향 강도"
COMPLAINT_NO_SUMMARY    = "데이터 없음"
COMPLAINT_EXAMPLE_LABEL = "대표 게시글:"

RAW_TITLE_TMPL      = "수집된 전체 {total}개 게시글 · 집중 수집 표본 {analysis}개"
RAW_ALL_TITLE       = "#### 전체 수집 목록 (날짜별)"
RAW_DATE_GROUP_TMPL = "📅 {date} — {count}개"
RAW_BADGE_HIGH_ENG  = "💬[고관여]"
RAW_BADGE_NORMAL    = "📄[일반]"
RAW_POST_META_TMPL  = "(댓글: {count}개 / {utype})"
RAW_NO_DATE_LABEL   = "날짜 없음"

ACTIONBAR_TITLE = "### 📝 리포트 발행"

NOTION_SUCCESS_MSG = "🎉 노션 리포트 발행 완료!"
NOTION_LINK_LABEL  = "🔗 생성된 노션 리포트 확인하기"
STEP4_RESET_BTN    = "🔄 다른 게임 분석하기"

HISTORY_BACK_BTN   = "← 현재 분석으로 돌아가기"
HISTORY_VIEW_LABEL = "📁 기록 열람 중 — {game_name} ({date_range}) | 저장: {saved_at}"

# ── 노션 전용 ──────────────────────────────────────────────────────
NOTION_BOT_INFO_TITLE  = "ℹ️ 봇 안내 및 데이터 출처 (클릭해서 펼치기)"
NOTION_BOT_INFO_DESC   = "[{version}] DC 게임 갤러리 탈곡기\n분석 대상: {game_name} / {subtype_label}\n분석 기간: {date_range_str}"
NOTION_SUMMARY_TITLE   = "🤖 AI 현황 요약"
NOTION_POS_TITLE       = "🟢 주요 긍정 여론"
NOTION_NEG_TITLE       = "🔴 주요 부정 여론"
NOTION_ISSUE_TITLE     = "🔥 주요 이슈 리스트"
NOTION_COMPLAINT_TITLE = "💬 주요 동향 분석"
NOTION_TIMELINE_TITLE  = "📊 일자별 수집 게시글 수 추이"
NOTION_RAW_TITLE       = "📋 원본 데이터 (최근 수집순)"
NOTION_SCORE_CRITERIA  = (
    "동향 강도 점수 기준 (0–10점)\n"
    "0–2점: 거의 없음 / 3–4점: 소수 언급 / "
    "5–6점: 반복 언급 / 7–8점: 다수 언급 / 9–10점: 주요 동향\n"
    "산출 기준: 해당 카테고리 키워드 언급 비율 (30%↑→7–10점 / 10–30%→4–6점 / 10%↓→0–3점)"
)
NOTION_ISSUE_CRITERIA  = (
    "언급 빈도 점수 기준 (0–100점)\n"
    "분석 게시글 중 해당 이슈 관련 키워드 언급 비율을 0–100으로 표시합니다."
)

# ── CSS ──────────────────────────────────────────────────────────
GLOBAL_CSS = """
<style>
section[data-testid="stSidebar"] { background:#f8f9fa; border-right:1px solid #e9ecef; }
section[data-testid="stSidebar"] > div { padding-top:1.5rem; }
.main .block-container { padding:1.5rem 2.5rem 2rem 2.5rem; max-width:1100px; }
div[data-testid="stTabPanel"] hr:last-of-type { display:none !important; }
button[data-testid="collapsedControl"],
button[data-testid="baseButton-headerNoPadding"],
section[data-testid="stSidebarCollapseButton"] { display:none !important; }
div[data-testid="stButton"] > button { border-radius:10px; font-weight:600; }

.step-done { padding:6px 10px; border-radius:8px; color:#1d7a3a; font-size:0.85rem; }
.step-cur  { padding:8px 12px; border-radius:8px; background:#3b4890; color:white; font-size:0.85rem; font-weight:700; }
.step-wait { padding:6px 10px; border-radius:8px; color:#adb5bd; font-size:0.85rem; }

/* 탭 버튼 */
div[data-testid="stTabs"] { border-bottom: none !important; }
div[data-testid="stTabs"] > div:first-child { gap: 6px !important; }
div[data-testid="stTabs"] button[data-baseweb="tab"] {
    background: #f0f2f6; border: 1.5px solid #ced4da !important;
    border-radius: 10px !important; margin: 0 !important;
    padding: 8px 18px !important; font-weight: 600 !important;
    font-size: 0.88rem !important; color: #495057 !important;
    transition: all 0.15s ease; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
div[data-testid="stTabs"] button[data-baseweb="tab"]:hover {
    background: #e2e6ea !important; border-color: #adb5bd !important; color: #212529 !important;
}
div[data-testid="stTabs"] button[aria-selected="true"][data-baseweb="tab"] {
    background: #3b4890 !important; border-color: #3b4890 !important;
    color: white !important; box-shadow: 0 2px 8px rgba(59,72,144,0.35);
}
div[data-testid="stTabs"] div[data-baseweb="tab-border"],
div[data-testid="stTabs"] div[data-baseweb="tab-highlight"],
div[data-baseweb="tab-list"] > div:last-child { display: none !important; }

.toss-h1  { text-align:center; font-size:2.2rem; font-weight:800; color:#1e2129; margin-bottom:0.5rem; }
.toss-sub { text-align:center; color:#6c757d; margin-bottom:1.5rem; }

.toss-card       { background:linear-gradient(135deg,#3b4890 0%,#5b6fb5 100%); border-radius:20px; padding:36px 28px 24px; text-align:center; margin:12px 0; min-height:200px; display:flex; flex-direction:column; align-items:center; justify-content:center; box-shadow:0 8px 28px rgba(59,72,144,0.22); }
.toss-card-emoji { font-size:3rem; margin-bottom:14px; }
.toss-card-label { font-size:1.3rem; font-weight:800; color:white; margin-bottom:10px; }
.toss-card-desc  { font-size:0.9rem; color:rgba(255,255,255,0.82); line-height:1.65; white-space:pre-line; }
.toss-card-dots  { margin-top:18px; display:flex; gap:6px; justify-content:center; }
.toss-dot        { font-size:0.45rem; color:rgba(255,255,255,0.3); }
.toss-dot-on     { color:white; }

.diag-msg      { text-align:center; color:#3b4890; font-size:0.88rem; font-weight:600; padding:6px; }
.phase-card    { background:#f8f9fa; border:1.5px solid #dee2e6; border-radius:12px; padding:16px 20px; margin:6px 0; }
.phase-card-ai { background:#eef0fa; border-color:#3b4890; }
.phase-title   { font-size:0.98rem; font-weight:700; color:#1e2129; }

.tt-wrap { position:relative; display:inline-block; cursor:help; }
.tt-box  { visibility:hidden; opacity:0; background:#1e2129; color:#f8f9fa; border-radius:8px; padding:10px 14px; font-size:0.78rem; line-height:1.6; white-space:pre-line; position:absolute; z-index:9999; top:120%; left:0; min-width:220px; max-width:360px; word-break:keep-all; box-shadow:0 4px 18px rgba(0,0,0,0.28); transition:opacity 0.15s; pointer-events:none; }
.tt-box::before { content:""; position:absolute; bottom:100%; left:14px; border:6px solid transparent; border-bottom-color:#1e2129; }
.tt-wrap:hover .tt-box { visibility:visible; opacity:1; }

.floating-guide { position:fixed; top:64px; right:14px; z-index:9998; background:#3b4890; color:white; padding:8px 18px; border-radius:20px; font-size:0.84rem; font-weight:700; white-space:nowrap; box-shadow:0 4px 14px rgba(59,72,144,0.38); pointer-events:none; }

div[data-testid="stExpander"] { margin-bottom:8px !important; }
</style>
"""


# ── AI 프롬프트 ──────────────────────────────────────────────────
def build_diagnosis_ai_prompt(gallery_name, top_words, subtype_id, daily_avg):
    from config import GALLERY_SUBTYPES
    subtype = GALLERY_SUBTYPES.get(subtype_id, GALLERY_SUBTYPES["stable"])
    return f"""
당신은 게임 커뮤니티 분석 전문가입니다.
아래 정보를 바탕으로 이 갤러리가 어떤 게임/주제에 관한 갤러리인지 파악하세요.

[갤러리 정보]
- 갤러리 페이지 타이틀(가장 신뢰도 높음): {gallery_name}
- 자주 등장한 제목 키워드(보조 참고): {', '.join(top_words[:10])}
- 자동 감지된 갤러리 유형: {subtype['label']}
- 일평균 게시글 수: {daily_avg}개

[topic_guess 작성 규칙 — 반드시 준수]:
1. 갤러리 페이지 타이틀({gallery_name})에서 '마이너 갤러리', '미니 갤러리', '갤러리' 접미사를 제거한 결과를 topic_guess로 사용하십시오.
2. 예: '메이플 키우기 갤러리' → '메이플 키우기', '연운 마이너 갤러리' → '연운'
3. 타이틀 자체가 명확한 게임명을 담고 있으면 그대로 사용하십시오.
4. 타이틀이 영문 ID처럼 의미를 알 수 없는 경우에만 키워드를 참고해 추정하십시오.
5. 절대로 타이틀과 무관한 이름을 창작하거나 추측하지 마십시오.

[출력 JSON — 코드블록 없이 순수 JSON만 출력]:
{{
  "topic_guess": "갤러리 타이틀에서 추출한 게임명 (단일 문자열)",
  "topic_reason": "갤러리 타이틀 기반 추출임을 명시한 1문장",
  "suggested_focus": "default/complaint/positive/churn/balance/operation 중 하나 (단일 문자열)",
  "suggested_focus_reason": "추천 이유 1문장",
  "warning": "주의사항이 있으면 작성, 없으면 빈 문자열"
}}
"""


def build_main_analysis_prompt(gallery_id, game_name, subtype_label, subtype_desc,
                                subtype_focus, analysis_focus_label,
                                post_data_text, analysis_days, total_posts,
                                concept_posts, date_summary):
    return f"""당신은 커뮤니티 데이터 분석 전문가입니다.
아래 게시글 데이터를 바탕으로 '{game_name}' 갤러리의 현황을 분석하십시오.
오직 주어진 데이터에 근거한 팩트만 작성하십시오.

[분석 대상]
- 게임: {game_name} | 유형: {subtype_label} | 게시글 수: {total_posts}개
- 일자별 분포: {date_summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 출력 규칙 (위반 시 응답 전체 무효)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 순수 JSON만 출력. 코드블록(```) 절대 금지.
2. JSON 텍스트 값 내 큰따옴표(") · 줄바꿈(\\n) 절대 금지. 강조는 작은따옴표(') 사용.
3. 마크다운 기호(** ~ #) 사용 금지.
4. 전체 응답은 반드시 18,000자 이내.
5. [중요] positive_posts/negative_posts의 title과 url은 반드시 주어진 데이터 원문의 정확한 제목과 URL을 그대로 복사하세요. 절대로 가짜 URL이나 제목을 지어내지 마세요. 일치하는 글이 없다면 빈 배열([])로 두세요.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📐 필드별 길이/수량 제한 (엄수)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- critic_one_liner  : 50자 이내, 이모지 1개 포함, 현상 서술형
- issue_summary     : 80자 이내
- major_issues 배열 : 4~6개. 갤러리에서 실제 논의된 주요 이슈만.
- positive_posts    : 각 이슈당 0~2개. 해당 이슈에 긍정적인 원본 게시글.
- negative_posts    : 각 이슈당 0~2개. 해당 이슈에 부정적인 원본 게시글.
- top_keywords      : 5개 고정.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 점수 기준
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- heat_score (0-100): 전체 수집 게시글 중 해당 이슈 관련 게시글 비율 (ex: 30개면 30)
- sentiment_ratio: 해당 이슈 관련 게시글 중 긍정/부정 비중. positive+negative=100.
- overall_sentiment: 전체 수집 게시글 전반의 긍정/부정 분위기 추정 비중. positive+negative=100.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 출력 JSON 스키마
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{{
  "critic_one_liner": "이모지+현상서술 50자이내",
  "top_keywords": ["키워드1","키워드2","키워드3","키워드4","키워드5"],
  "overall_sentiment": {{"positive": 30, "negative": 70}},
  "major_issues": [
    {{
      "issue_title": "15자이내",
      "issue_category": "운영, 밸런스, BM, 콘텐츠, 커뮤니티/시스템 등",
      "issue_keywords": ["키워드1", "키워드2", "키워드3"],
      "issue_summary": "80자이내. 이슈의 핵심 내용과 유저 반응 서술.",
      "heat_score": 75,
      "sentiment_ratio": {{"positive": 20, "negative": 80}},
      "positive_posts": [
        {{"title": "실제원문제목", "url": "실제원문url"}}
      ],
      "negative_posts": [
        {{"title": "실제원문제목", "url": "실제원문url"}}
      ]
    }}
  ]
}}

[분석 표본 게시글]
{post_data_text}"""