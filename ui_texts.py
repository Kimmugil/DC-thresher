"""
ui_texts.py v7 — 모든 UI 문구·CSS·프롬프트 중앙 관리
"""

# ── 앱 기본 ──────────────────────────────────────────────────────
APP_PAGE_TITLE = "DC 게임 갤러리 탈곡기"
APP_PAGE_ICON  = "🚜"

# ── 사이드바 ──────────────────────────────────────────────────────
SIDEBAR_TOOL_NAME        = "🚜 DC 탈곡기"
SIDEBAR_TOOL_CAPTION     = "게임 갤러리 민심 분석 툴"
SIDEBAR_STEP_TITLE       = "진행 단계"
SIDEBAR_CURRENT_TARGET   = "현재 분석 대상"
SIDEBAR_VERSION_EXPANDER = "ℹ️ 버전 및 환경 정보"
SIDEBAR_VERSION_LABEL    = "버전:"
SIDEBAR_HISTORY_TITLE    = "업데이트 이력"
SIDEBAR_HISTORY          = ["v2.0.0 — 현황 중심 리포트 전면 개편", "v1.0.0 — 최초 출시"]
SIDEBAR_RESET_BTN        = "🔄 처음부터 다시"
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
STEP0_TITLE        = "🚜 DC 게임 갤러리 탈곡기"
STEP0_SUBTITLE     = "게임 유저 민심을 빠르게 파악하는 PM 전용 분석 툴"
STEP0_INPUT_HEADER = "분석할 게임 갤러리 URL을 입력하세요"
STEP0_PLACEHOLDER  = "https://gall.dcinside.com/mgallery/board/lists/?id=projectnakwon"
STEP0_CAPTION      = "마이너 갤러리(mgallery), 일반 갤러리 모두 지원합니다."
STEP0_BTN          = "🔍  갤러리 진단 시작"
STEP0_WARN_EMPTY   = "URL을 입력해 주세요."
STEP0_WARN_INVALID = "유효한 디씨인사이드 갤러리 URL을 입력해 주세요."

# ── Step 0 진단 카드 ───────────────────────────────
DIAG_CARDS = [
    {"emoji": "🔍", "label": "먼저 갤러리를 파악해요", "desc": "게시글 패턴과 리젠 속도를 분석해\n갤러리 상태를 진단합니다"},
    {"emoji": "🚀", "label": "출시 초기 갤러리라면", "desc": "버그 제보, 초기 반응, 온보딩 경험\n중심으로 분석을 집중합니다"},
    {"emoji": "🔥", "label": "이슈가 터진 갤러리라면", "desc": "논란 원인과 여론 변화 흐름을\n집중 추적합니다"},
    {"emoji": "📚", "label": "안정기 갤러리라면", "desc": "장기 유저 만족도, 메타 변화,\n밸런스 이슈를 깊게 파악합니다"},
    {"emoji": "📉", "label": "갤러리가 조용해졌다면", "desc": "이탈 원인과 잔류 유저 심리를\n파악해 현황을 정리합니다"},
    {"emoji": "💬", "label": "반응 많은 글이 진짜 민심", "desc": "댓글이 많이 달린 게시글을\n핵심 분석 표본으로 선정합니다"},
]

# ── Step 1 ────────────────────────────────────────────────────────
DIAG_STATUS_MSG       = "🔍 갤러리 진단 중..."
DIAG_DONE_MSG         = "✅ 진단 완료!"
DIAG_ERROR_LABEL      = "진단 오류"
DIAG_SECTION_TITLE    = "## 📊 갤러리 진단 결과"
DIAG_SECTION_SUBTITLE = "아래 결과를 확인하세요."

METRIC_GALLERY_NAME = "갤러리"
METRIC_DIAG_PERIOD  = "진단 기간"

TOOLTIP_CHART = "진단 기간 내 일자별 게시글 수 추이입니다."
TOOLTIP_SUBTYPE = "게시글 제목 키워드 패턴과 리젠 속도로\n자동 감지한 갤러리 상태입니다.\nAI 분석 방향에 영향을 줍니다."
GALLERY_NAME_TOOLTIP = "갤러리명이 실제 다루는 주제와 다를 수 있습니다.\n\n다음 단계에서 게임명을 직접 수정할 수 있습니다."
GALLERY_NAME_EDIT_HINT = "✏️ 다음 단계에서 수정 가능"
GALLERY_NAME_ANCHOR_ID = "game-name-input"

SUBTYPE_MODAL_BTN   = "갤러리 유형 기준 보기"
SUBTYPE_MODAL_TITLE = "갤러리 유형 분류 기준"
SUBTYPE_MODAL_DESC  = "게시글 제목 키워드 패턴과 리젠 속도를 분석해 5가지 유형으로 자동 분류합니다."
SUBTYPE_DEFINITIONS = [
    {"id":"pre_launch",  "emoji":"🌱","label":"출시 전 기대형", "desc":"게임 출시 전, 기대·정보 공유 중심", "criteria":"일평균 30개 미만 + 기대/출시/CBT 키워드 35% 이상", "focus":"기대 포인트, 우려 사항 중심 분석"},
    {"id":"early_launch","emoji":"🚀","label":"출시 초기형", "desc":"출시 직후, 버그 제보·초기 반응 중심", "criteria":"출시/버그/뉴비 키워드 25% 이상 + 리젠 상승 중", "focus":"첫인상, 초기 버그, 온보딩 반응 분석"},
    {"id":"stable",      "emoji":"📚","label":"안정기형", "desc":"공략·빌드·정보 글 비중이 높은 갤러리", "criteria":"공략/빌드/메타 키워드 비중 가장 높음 + 안정적 리젠", "focus":"게임 완성도, 장기 만족도, 메타 변화 분석"},
    {"id":"issue_burst", "emoji":"🔥","label":"이슈 폭발형", "desc":"패치·운영 논란으로 부정 여론 급등 중", "criteria":"환불/패치/운영 키워드 35% 이상 OR 리젠 급증 1.4배", "focus":"이슈 원인, 이탈 위험 분석"},
    {"id":"decline",     "emoji":"📉","label":"쇠퇴기형", "desc":"리젠 감소, 이탈 논의가 늘어나는 갤러리", "criteria":"이탈 키워드 30% 이상 + 최근 리젠 70% 미만", "focus":"이탈 원인, 잔류 유저 심리 분석"},
]
SUBTYPE_CRITERIA_PREFIX = "**판별 기준:**"
SUBTYPE_FOCUS_PREFIX    = "**분석 포커스:**"

STEP1_GAME_CONFIRM_TITLE = "이 갤러리에서 다루는 게임이 맞나요?"
STEP1_GAME_CONFIRM_DESC  = "AI가 게시글 제목 키워드를 분석해 추정한 결과입니다."
STEP1_GAME_REASON_LABEL  = "추정 근거:"
STEP1_GAME_WRONG_HINT    = "틀렸다면 아래 입력창에서 직접 수정하세요. (갤러리 주제는 AI 분석에 도움을 줍니다.)"
COND_GAME_INPUT_LABEL    = "게임명 확인"
COND_GAME_PLACEHOLDER    = "예: 메이플스토리 키우기, 로스트아크, 던전앤파이터"
STEP1_GAME_CHANGED_TMPL  = "💡 **'{game_name}'** 주제로 분석을 진행합니다."

# ── Step 2 ────────────────────────────────────────────────────────
STEP2_TITLE    = "## 🌾 데이터 수집 & AI 분석"
STEP2_SUBTITLE = "잠시 기다려 주세요. 브라우저를 닫지 마세요."

SCRAPE_STATUS_MSG = "🌾 게시글 수집 중..."
AI_STATUS_MSG     = "🧠 AI 민심 분석 중..."
SCRAPE_DONE_TMPL  = "✅ 수집 완료 — 전체 {total}개 · 분석 표본 {analysis}개"
SCRAPE_ERROR_TMPL = "수집 실패: {error}"
AI_ERROR_TMPL     = "AI 분석 실패: {error}"
BTN_BACK          = "← 돌아가기"
BTN_CLOSE         = "✕ 닫기"

TICKER_MESSAGES = [
    "갤러리 떡밥을 탈곡하는 중... 🌾",
    "댓글 많은 글에서 민심을 추출하는 중... 🧐",
    "이슈 발생 원인을 추적하는 중... 🔍",
    "불만 카테고리를 분류하는 중... 📂",
    "팩트 중심의 데이터를 수집하는 중... 📝",
]

# ── Step 3 (리포트) ───────────────────────────────────────────────
TAB_LABELS = [
    "📈 갤러리 현황",
    "🔥 주요 이슈",
    "⚠️ 불만 분석",
    "📋 원본 데이터",
]

PUBLISH_BTN          = "📤 노션으로 발행하기"
NEW_ANALYSIS_BTN     = "🔄 다른 게임 분석하기"
PUBLISH_STATUS_MSG   = "노션 페이지 생성 중..."
PUBLISH_ERROR_TMPL   = "노션 발행 실패: {error}"

PROFILE_TITLE_TMPL      = "### {emoji} {game_name} 게임 갤러리 분석 리포트"
PROFILE_KEYWORD_TMPL    = "🏷️ **핵심 키워드 TOP 5:** {keywords}"
PROFILE_ONELINER_PREFIX = "💬"

ANALYSIS_SPEC_TMPL = (
    "📅 **{date_range}** · "
    "기간 내 게시글 {total}개 중 고관여 게시글 {analysis}개 집중 분석"
)

COMPLAINT_SCORE_BOX = """
<div style="background:#f8f9fa; border:1px solid #dee2e6; border-radius:8px; padding:12px; font-size:0.85rem; margin-bottom:1.5rem;">
    <b style="color:#1e2129;">ℹ️ 불만 강도 점수 기준 (0-10점)</b><br>
    <span style="color:#888;font-weight:700;">0-2점</span> (거의 없음) · 
    <span style="color:#2980b9;font-weight:700;">3-4점</span> (소수 언급) · 
    <span style="color:#e67e22;font-weight:700;">5-6점</span> (반복 언급 주의) · 
    <span style="color:#c0392b;font-weight:700;">7-8점</span> (유저 불만 상당) · 
    <span style="color:#c0392b;font-weight:900;">9-10점</span> (커뮤니티 주요 이슈)
</div>
"""

ISSUE_SCORE_BOX = """
<div style="background:#f8f9fa; border:1px solid #dee2e6; border-radius:8px; padding:12px; font-size:0.85rem; margin-top:1.5rem;">
    <b style="color:#1e2129;">ℹ️ 언급 빈도 점수 기준 (0-100점)</b><br>
    해당 이슈와 관련된 키워드가 전체 수집된 게시글 내에서 언급된 빈도를 기반으로 산출된 객관적 점수입니다. 점수가 높을수록 현재 갤러리 내 화제성이 높음을 의미합니다.
</div>
"""

# 현황
TIMELINE_CHART_TITLE = "일자별 게시글 수 추이"
TIMELINE_NO_DATA     = "날짜 데이터가 없습니다."

# 주요 이슈
ISSUE_TITLE         = "### 🔥 주요 이슈 리스트"
ISSUE_NO_DATA       = "감지된 주요 이슈가 없습니다."
SCORE_BASED_ON_FREQ = "언급 빈도 점수"

# 불만 분석
COMPLAINT_TITLE          = "불만 카테고리별 분석"
COMPLAINT_NO_DATA        = "불만 카테고리 데이터가 없습니다."
COMPLAINT_RADAR_NAME     = "불만 강도"
COMPLAINT_NO_SUMMARY     = "데이터 없음"
COMPLAINT_SUMMARY_LABEL  = "**요약:**"
COMPLAINT_EXAMPLE_LABEL  = "**관련 여론:**"

# 원본 데이터
RAW_TITLE_TMPL      = "**수집된 전체 {total}개 게시글 · 집중 분석 표본 {analysis}개**"
RAW_ALL_TITLE       = "#### 전체 수집 목록 (날짜별)"
RAW_DATE_GROUP_TMPL = "📅 {date} — {count}개"
RAW_BADGE_CONCEPT   = "🔥[개념]"
RAW_BADGE_NORMAL    = "💬[일반]"
RAW_POST_META_TMPL  = "(댓글: {count}개 / {utype})"
RAW_NO_DATE_LABEL   = "날짜 없음"

ACTIONBAR_TITLE = "### 📝 리포트 발행"

NOTION_SUCCESS_MSG = "🎉 노션 리포트 발행 완료!"
NOTION_LINK_LABEL  = "🔗 생성된 노션 리포트 확인하기"

# ── 노션 전용 텍스트 (하드코딩 제거용) ───────────────────────────
NOTION_BOT_INFO_TITLE  = "ℹ️ 봇 안내 및 데이터 출처 (클릭해서 펼치기)"
NOTION_BOT_INFO_DESC   = "[{version}] DC 게임 갤러리 분석 리포트\n분석 대상: {game_name} / {subtype_label}\n분석 기간: {date_range_str}"
NOTION_SUMMARY_TITLE   = "🤖 AI 객관적 현황 요약"
NOTION_POS_TITLE       = "🟢 주요 긍정 여론"
NOTION_NEG_TITLE       = "🔴 주요 부정 여론"
NOTION_ISSUE_TITLE     = "🔥 주요 이슈 리스트"
NOTION_COMPLAINT_TITLE = "⚠️ 불만 카테고리 분석"
NOTION_TIMELINE_TITLE  = "📊 일자별 수집 게시글 수 추이"
NOTION_RAW_TITLE       = "📋 원본 데이터 (최근 수집순)"

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
.step-cur  { padding:8px 12px; border-radius:8px; background:#3b4890; color:white;  font-size:0.85rem; font-weight:700; }
.step-wait { padding:6px 10px; border-radius:8px; color:#adb5bd;  font-size:0.85rem; }
div[data-testid="stTabs"] button[data-baseweb="tab"] { background:#f8f9fa; border:1.5px solid #dee2e6; border-radius:8px; margin:0 3px 0 0; padding:7px 16px; font-weight:600; font-size:0.85rem; color:#495057; transition:all 0.15s; }
div[data-testid="stTabs"] button[data-baseweb="tab"]:hover { background:#e9ecef; color:#212529; }
div[data-testid="stTabs"] button[aria-selected="true"][data-baseweb="tab"] { background:#3b4890; border-color:#3b4890; color:white; }
div[data-testid="stTabs"] div[data-baseweb="tab-border"] { display:none; }
.toss-h1  { text-align:center; font-size:2.2rem; font-weight:800; color:#1e2129; margin-bottom:0.5rem; }
.toss-sub { text-align:center; color:#6c757d; margin-bottom:2rem; }
.toss-card { background:linear-gradient(135deg,#3b4890 0%,#5b6fb5 100%); border-radius:20px; padding:36px 28px 24px; text-align:center; margin:12px 0; min-height:200px; display:flex; flex-direction:column; align-items:center; justify-content:center; box-shadow:0 8px 28px rgba(59,72,144,0.22); }
.toss-card-emoji { font-size:3rem; margin-bottom:14px; }
.toss-card-label { font-size:1.3rem; font-weight:800; color:white; margin-bottom:10px; }
.toss-card-desc  { font-size:0.9rem; color:rgba(255,255,255,0.82); line-height:1.65; white-space:pre-line; }
.toss-card-dots  { margin-top:18px; display:flex; gap:6px; justify-content:center; }
.toss-dot        { font-size:0.45rem; color:rgba(255,255,255,0.3); }
.toss-dot-on     { color:white; }
.diag-msg { text-align:center; color:#3b4890; font-size:0.88rem; font-weight:600; padding:6px; }
.phase-card    { background:#f8f9fa; border:1.5px solid #dee2e6; border-radius:12px; padding:16px 20px; margin:6px 0; }
.phase-card-ai { background:#eef0fa; border-color:#3b4890; }
.phase-title   { font-size:0.98rem; font-weight:700; color:#1e2129; }
.tt-wrap { position:relative; display:inline-block; cursor:help; }
.tt-box  { visibility:hidden; opacity:0; background:#1e2129; color:#f8f9fa; border-radius:8px; padding:10px 14px; font-size:0.78rem; line-height:1.6; white-space:pre-line; position:absolute; z-index:9999; top:120%; left:0; min-width:220px; max-width:360px; word-break:keep-all; box-shadow:0 4px 18px rgba(0,0,0,0.28); transition:opacity 0.15s; pointer-events:none; }
.tt-box::before { content:""; position:absolute; bottom:100%; left:14px; border:6px solid transparent; border-bottom-color:#1e2129; }
.tt-wrap:hover .tt-box { visibility:visible; opacity:1; }
.floating-guide { position:fixed; top:64px; right:14px; z-index:9998; background:#3b4890; color:white; padding:8px 18px; border-radius:20px; font-size:0.84rem; font-weight:700; white-space:nowrap; box-shadow:0 4px 14px rgba(59,72,144,0.38); pointer-events:none; }
</style>
"""

# ── AI 프롬프트 ──────────────────────────────────────────────────
def build_diagnosis_ai_prompt(gallery_name, top_words, subtype_id, daily_avg):
    from config import GALLERY_SUBTYPES, ANALYSIS_FOCUS_OPTIONS
    subtype   = GALLERY_SUBTYPES.get(subtype_id, GALLERY_SUBTYPES["stable"])
    focus_ids = list(ANALYSIS_FOCUS_OPTIONS.keys())
    return f"""
당신은 게임 커뮤니티 분석 전문가입니다.
아래 정보를 바탕으로 이 갤러리가 어떤 게임/주제에 관한 갤러리인지 파악하고, 최적의 분석 방향을 추천하세요.

[갤러리 정보]
- 갤러리명: {gallery_name}
- 자주 등장한 제목 키워드: {', '.join(top_words[:10])}
- 자동 감지된 갤러리 상태: {subtype['label']}
- 일평균 게시글 수: {daily_avg}개

[출력 JSON — 반드시 이 구조만 출력]:
{{
  "topic_guess": "추정되는 게임명 또는 주제",
  "topic_reason": "추정 근거",
  "suggested_focus": ["권장 분석 방향 ID"],
  "suggested_focus_reason": "추천 이유",
  "warning": ""
}}
"""

def build_main_analysis_prompt(gallery_id, game_name, subtype_label, subtype_desc,
                                subtype_focus, analysis_focus_label,
                                post_data_text, analysis_days, total_posts,
                                concept_posts, date_summary):
    bt = chr(96) * 3
    return f"""
당신은 커뮤니티 데이터 분석 전문가이자 전략 PM입니다.
다음은 '{gallery_id}' ({game_name}) 갤러리에서 수집된 게시글 데이터입니다.
오직 주어진 데이터에 근거하여 팩트 중심으로 분석하십시오.

[분석 대상]
- 게임/주제: {game_name}
- 갤러리 상태: {subtype_label}
- 전체 게시글 수: {total_posts}개 (일자별: {date_summary})

[작성 가이드라인 — 위반 시 시스템 오류 발생]:
1. 결과물에 마크다운 코드 블록 기호({bt})를 절대 포함하지 마십시오. 순수 JSON 데이터만 출력.
2. 🚨 [매우 중요: JSON 문법 엄수] 모든 텍스트/요약 내용 내부에 **큰따옴표(")**나 제어 문자(줄바꿈 등)를 절대 사용하지 마십시오. 이스케이프(Escape) 처리를 철저히 하십시오. 강조가 필요하면 **작은따옴표(')**를 사용하십시오.
3. 모든 텍스트에서 마크다운 볼드체(**), 물결표(~) 기호를 절대 사용하지 마십시오.
4. [객관성 유지] 주관적 판단, 추측을 배제하고 게시글에서 확인 가능한 '팩트'만 명사형 종결 개조식으로 나열하십시오.
5. 핵심 키워드는 반드시 정확히 5개만 추출하십시오.
6. 출처 표기 의무: 분석 내용 중 특정 떡밥이나 글을 언급할 때는 문장 끝에 원문 링크를 "[글 제목](URL)" 형식으로 달아주십시오.

[출력 JSON 스키마 (반드시 이 구조를 지킬 것)]:
{{
  "critic_one_liner": "갤러리 유형(예: 안정기형, 폭발형 등)에 대한 언급은 철저히 배제하고, 오직 분석 기간 내 발생한 주요 동향과 핵심 민심만을 중심으로 한줄 요약 (이모지 포함)",
  "top_keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"],
  "sentiment_summary": {{
    "positive": [{{"summary": "긍정 요약 팩트 1", "ref_url": "관련 게시글 URL"}}],
    "negative": [{{"summary": "부정 요약 팩트 1", "ref_url": "관련 게시글 URL"}}]
  }},
  "major_issues": [
    {{"issue": "이슈 명칭 및 주요 팩트 내용 요약", "mention_score": 0~100 (관련 키워드 언급 빈도를 기반으로 한 객관적 점수. 가장 빈도가 높으면 100), "ref_url": "관련 게시글 URL (있는 경우)"}}
  ],
  "complaint_analysis": {{
    "balance":   {{"score":0~10,"summary":"팩트 요약","example":"대표 팩트 발언","example_url":"관련 URL"}},
    "operation": {{"score":0~10,"summary":"팩트 요약","example":"대표 팩트 발언","example_url":""}},
    "bug":       {{"score":0~10,"summary":"팩트 요약","example":"대표 팩트 발언","example_url":""}},
    "payment":   {{"score":0~10,"summary":"팩트 요약","example":"대표 팩트 발언","example_url":""}},
    "content":   {{"score":0~10,"summary":"팩트 요약","example":"대표 팩트 발언","example_url":""}}
  }}
}}

[AI 분석 표본 게시글 (최근 고관여 게시글)]:
{post_data_text}
"""