"""
ui_texts.py v3 — 모든 UI 문구, 툴팁, AI 프롬프트 중앙 관리
"""

# ─────────────────────────────────────────────
# 앱 기본
# ─────────────────────────────────────────────
APP_PAGE_TITLE = "DC 게임 갤러리 탈곡기"
APP_PAGE_ICON  = "🚜"
APP_VERSION_DISPLAY = "v2.0.0 — 현황 중심 리포트 전면 개편"

# ─────────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────────
SIDEBAR_TOOL_NAME        = "🚜 DC 탈곡기"
SIDEBAR_TOOL_CAPTION     = "게임 갤러리 민심 분석 툴"
SIDEBAR_STEP_TITLE       = "진행 단계"
SIDEBAR_CURRENT_TARGET   = "현재 분석 대상"
SIDEBAR_VERSION_EXPANDER = "ℹ️ 버전 및 환경 정보"
SIDEBAR_VERSION_LABEL    = "버전:"
SIDEBAR_HISTORY_TITLE    = "업데이트 이력"
SIDEBAR_HISTORY = [
    "v2.0.0 — 현황 중심 리포트 전면 개편",
    "v2.0.0 — 게임 갤러리 특화 전면 개편",
    "v1.0.0 — 최초 출시",
]
SIDEBAR_RESET_BTN      = "🔄 처음부터 다시"
SIDEBAR_DAILY_AVG_TMPL = "일평균 {avg}개 글"

STEP_INFO = [
    ("🔍", "갤러리 진단"),
    ("✅", "게임 확인"),
    ("🌾", "수집 & AI 분석"),
    ("📊", "리포트 검수"),
    ("🎉", "발행 완료"),
]

STEP_GUIDE_MESSAGES = {
    0: "갤러리 URL을 입력하고 진단 시작",
    1: "게임명을 확인하고 분석 시작",
    2: "수집 & AI 분석 진행 중 — 브라우저를 닫지 마세요",
    3: "분석 결과를 검토하고 노션으로 발행하세요",
    4: "발행 완료! 노션 리포트를 확인하세요",
}

# ─────────────────────────────────────────────
# Step 0 — URL 입력
# ─────────────────────────────────────────────
STEP0_TITLE        = "🚜 DC 게임 갤러리 탈곡기"
STEP0_SUBTITLE     = "게임 유저 민심을 빠르게 파악하는 PM 전용 분석 툴"
STEP0_INPUT_HEADER = "분석할 게임 갤러리 URL을 입력하세요"
STEP0_PLACEHOLDER  = "https://gall.dcinside.com/mgallery/board/lists/?id=projectnakwon"
STEP0_CAPTION      = "마이너 갤러리(mgallery), 일반 갤러리 모두 지원합니다."
STEP0_BTN          = "🔍  갤러리 진단 시작"
STEP0_WARN_EMPTY   = "URL을 입력해 주세요."
STEP0_WARN_INVALID = "유효한 디씨인사이드 갤러리 URL을 입력해 주세요."

# ─────────────────────────────────────────────
# Step 1 — 진단 결과
# ─────────────────────────────────────────────
DIAG_STATUS_MSG       = "🔍 갤러리 진단 중..."
DIAG_DONE_MSG         = "✅ 진단 완료!"
DIAG_ERROR_LABEL      = "진단 오류"
DIAG_SECTION_TITLE    = "## 📊 갤러리 진단 결과"
DIAG_SECTION_SUBTITLE = "아래 진단 결과를 확인하세요. AI가 분석 방향을 제안합니다."

METRIC_GALLERY_NAME       = "갤러리"
METRIC_TOTAL_ROWS         = "수집 글 수"
METRIC_DAILY_AVG          = "일평균 글 수"
METRIC_CONCEPT_COUNT      = "개념글 수"
METRIC_CONCEPT_COUNT_UNIT = "개"
METRIC_GONIK_RATIO        = "고닉 비율"
METRIC_DIAG_PERIOD        = "진단 기간"

TOOLTIP_TOTAL_ROWS = (
    "진단 기간 동안 수집된 일반 게시글 총 수입니다.\n"
    "공지·설문·광고 글은 제외됩니다."
)
TOOLTIP_DAILY_AVG = (
    "수집된 글 수 ÷ 실제 데이터가 있는 날수.\n"
    "갤러리 활성도 지표이며, 분석 기간 추천에 사용됩니다."
)
TOOLTIP_CONCEPT_COUNT = (
    "디씨인사이드 추천 수 기준으로 선정된 '개념글' 수입니다.\n"
    "일반 목록 내 아이콘(.icon_recom)으로 감지합니다.\n\n"
    "개념글은 AI 분석의 주요 표본으로 사용됩니다."
)
TOOLTIP_GONIK_RATIO = (
    "'고닉' = 고정 닉네임 코어 유저\n"
    "'유동' = IP만 표시되는 비고정 작성자\n\n"
    "고닉 비율이 높을수록 단골 유저 중심 갤러리입니다.\n"
    "AI 분석의 세그먼트 분류에 활용됩니다."
)
TOOLTIP_CHART = (
    "진단 기간 내 날짜별 게시글 수입니다.\n"
    "🔴 빨간 막대: 평균 대비 1.8배 이상 급증(스파이크)\n"
    "→ 주요 이슈·패치·운영 이벤트가 있었을 가능성이 높습니다."
)
TOOLTIP_SPIKE = (
    "스파이크: 해당 날짜 게시글 수가 평균보다 1.8배 이상 높은 경우.\n"
    "다음 단계 AI 분석에서 해당 시점의 원인을 집중 분석합니다."
)
TOOLTIP_SUBTYPE = (
    "게시글 제목 키워드 패턴과 리젠 속도로 자동 감지한 갤러리 상태입니다.\n"
    "AI 분석 방향에 영향을 줍니다."
)
GALLERY_NAME_TOOLTIP = (
    "갤러리명이 실제 다루는 주제와 다를 수 있습니다.\n\n"
    "예) '특이점이 온다 갤러리': 원래 책 제목이지만\n"
    "실제로는 AGI·ASI 등 AI 관련 논의가 주를 이룹니다.\n\n"
    "다음 단계에서 게임명을 직접 수정할 수 있습니다."
)
GALLERY_NAME_EDIT_HINT  = "✏️ 다음 단계에서 게임명 수정 가능"
GALLERY_NAME_ANCHOR_ID  = "game-name-input"

DIAG_CHART_TITLE       = "진단 기간 내 날짜별 게시글 수"
DIAG_CHART_SPIKE_LABEL = "🔴 = 평균 대비 1.8배 이상 급증"
CHART_HOVER_TMPL       = "<b>%{x}</b><br>%{y}개<extra></extra>"
SPIKE_WARNING_TMPL     = "🔥 스파이크 감지: {dates}"
SPIKE_NEXT_STEP_MSG    = "📌 위 날짜에 게시글이 급증했습니다. AI가 다음 단계에서 해당 시점의 원인을 집중 분석합니다."

# 갤러리 유형 팝업
SUBTYPE_MODAL_BTN   = "📖 갤러리 유형 분류 기준 보기"
SUBTYPE_MODAL_TITLE = "갤러리 유형 분류 기준"
SUBTYPE_MODAL_DESC  = (
    "탈곡기는 게시글 제목 키워드 패턴과 리젠 속도를 분석해 "
    "갤러리를 5가지 유형으로 자동 분류합니다."
)
SUBTYPE_DEFINITIONS = [
    {"id":"pre_launch", "emoji":"🌱","label":"출시 전 기대형",
     "desc":"게임 출시 전, 기대·정보 공유 중심",
     "criteria":"일평균 30개 미만 + 기대/출시/CBT 키워드 35% 이상",
     "focus":"기대 포인트, 우려 사항 중심 분석"},
    {"id":"early_launch","emoji":"🚀","label":"출시 초기형",
     "desc":"출시 직후, 버그 제보·초기 반응 중심",
     "criteria":"출시/버그/뉴비 키워드 25% 이상 + 리젠 상승 중",
     "focus":"첫인상, 초기 버그, 온보딩 반응 분석"},
    {"id":"stable","emoji":"📚","label":"안정기형",
     "desc":"공략·빌드·정보 글 비중이 높은 성숙한 갤러리",
     "criteria":"공략/빌드/메타 키워드 비중 가장 높음 + 안정적 리젠",
     "focus":"게임 완성도, 장기 만족도, 메타 변화 분석"},
    {"id":"issue_burst","emoji":"🔥","label":"이슈 폭발형",
     "desc":"패치·운영 논란으로 부정 여론 급등 중",
     "criteria":"환불/패치/운영 키워드 35% 이상 OR 리젠 급증 1.4배",
     "focus":"이슈 원인, 이탈 위험, 긴급 대응 항목 분석"},
    {"id":"decline","emoji":"📉","label":"쇠퇴기형",
     "desc":"리젠 감소, 이탈 논의가 늘어나는 갤러리",
     "criteria":"이탈 키워드 30% 이상 + 최근 리젠 70% 미만",
     "focus":"이탈 원인, 잔류 유저 심리, 부활 가능성 분석"},
]
SUBTYPE_CRITERIA_PREFIX = "**판별 기준:**"
SUBTYPE_FOCUS_PREFIX    = "**분석 포커스:**"

# ─────────────────────────────────────────────
# Step 2 — 분석 방향 설정 (AI 인터랙션 + 기간 설정)
# ─────────────────────────────────────────────
STEP2_TITLE    = "## 🤖 분석 방향 설정"
STEP2_AI_STATUS = "🤖 갤러리 특성 파악 중..."
STEP2_AI_DONE  = "✅ 특성 파악 완료!"

AI_TOPIC_CONFIRM_TITLE  = "이 갤러리의 분석 대상 게임이 맞나요?"
AI_TOPIC_CONFIRM_DESC   = "AI가 게시글 제목 키워드를 분석해 추정한 결과입니다. 틀렸다면 직접 수정하세요."
AI_TOPIC_CONFIDENCE_TMPL = "추정 신뢰도: {pct}%"
AI_TOPIC_REASON_LABEL   = "추정 근거:"
COND_GAME_INPUT_LABEL   = "게임명 확인"
COND_GAME_PLACEHOLDER   = "예: 프로젝트 낙원, 던전앤파이터, 로스트아크"

AI_FOCUS_CONFIRM_TITLE  = "이 방향으로 분석을 진행할까요?"
AI_FOCUS_CONFIRM_DESC   = "AI가 갤러리 특성에 맞는 분석 방향을 추천했습니다. 변경하려면 선택하세요."
AI_FOCUS_REASON_LABEL   = "추천 이유:"
AI_WARNING_LABEL        = "⚠️ 참고:"

COND_PERIOD_TITLE   = "**📅 분석 기간 선택**"
COND_PERIOD_CAPTION = "선택 시 해당 기간의 게시글 수를 바로 보여드립니다."
PERIOD_OPTIONS = {
    7:  ("최근 7일",  "이슈 직후 빠른 파악"),
    14: ("최근 14일", "2주 트렌드 파악"),
    30: ("최근 30일", "월간 동향 리포트"),
}
PERIOD_BTN_SELECTED = "✓ 선택됨"
PERIOD_BTN_DEFAULT  = "선택"

# 기간별 게시글 수 카운팅 표시
PERIOD_COUNT_LOADING   = "게시글 수 확인 중..."
PERIOD_COUNT_TMPL      = "총 {total}개 게시글 분석 예정 (개념글 {concept}개 + 일반글 {normal}개)"
PERIOD_COUNT_CONCEPT_NOTE = "ℹ️ AI 분석은 개념글 위주로 진행하며, 개념글이 부족할 경우 고댓글 일반글로 보충합니다."

START_BTN = "🚀  수집 & AI 분석 시작"


# ─────────────────────────────────────────────
# Step 1 — 게임명 확인 (v4 1클릭 구조)
# ─────────────────────────────────────────────
STEP1_GAME_CONFIRM_TITLE = "이 갤러리에서 다루는 게임이 맞나요?"
STEP1_GAME_CONFIRM_DESC  = "AI가 게시글 제목 키워드를 분석해 추정한 결과입니다."
STEP1_GAME_REASON_LABEL  = "추정 근거:"
STEP1_GAME_WRONG_HINT    = "틀렸다면 아래 입력창에서 직접 수정하세요. 게임명은 AI 분석 품질에 직접 영향을 줍니다."

# Step 2 — 수집 & 분석 (자동)
STEP2_SUBTITLE = "잠시 기다려 주세요. 브라우저를 닫지 마세요."

# ─────────────────────────────────────────────
# Step 3 — 수집 & AI 분석
# ─────────────────────────────────────────────
STEP3_TITLE       = "## 🌾 데이터 수집 & AI 분석"
STEP3_SUBTITLE    = "잠시 기다려 주세요. 브라우저를 닫지 마세요."
SCRAPE_STATUS_MSG = "🌾 게시글 수집 중..."
AI_STATUS_MSG     = "🧠 AI 민심 분석 중..."
PATCH_STATUS_MSG  = "🔎 공식 패치/업데이트 정보 확인 중..."
SCRAPE_DONE_TMPL  = "✅ 수집 완료 — 전체 {total}개 (분석용 본문 {analysis}개)"
SCRAPE_ERROR_TMPL = "수집 실패: {error}"
AI_ERROR_TMPL     = "AI 분석 실패: {error}"
BTN_BACK_TO_COND  = "← 조건 설정으로 돌아가기"
BTN_BACK          = "← 돌아가기"

TICKER_MESSAGES = [
    "갤러리 떡밥을 탈곡하는 중... 🌾",
    "개념글에서 민심의 핵심을 추출하는 중... 🧐",
    "이슈 발생 원인을 추적하는 중... 🔍",
    "불만 카테고리를 분류하는 중... 📂",
    "이탈 신호를 감지하는 중... 🚨",
    "PM 액션 아이템을 도출하는 중... 📝",
    "민심 온도계를 측정하는 중... 🌡️",
    "코어 유저와 라이트 유저의 온도 차를 비교하는 중... ⚖️",
]

# ─────────────────────────────────────────────
# Step 4 — 리포트 탭
# ─────────────────────────────────────────────
TAB_LABELS = [
    "📊 핵심 요약",
    "🌡️ 민심 & 이슈",
    "⚠️ 불만 분석",
    "🔍 주목할 동향",
    "📋 원본 데이터",
]

REANALYZE_BTN             = "🔄 피드백 반영 재분석"
REANALYZE_PLACEHOLDER     = "특정 항목을 더 자세히 분석해줘, 이탈 원인에 집중해줘 등..."
PUBLISH_BTN               = "📤 노션 리포트 최종 발행"
REANALYZE_STATUS_MSG      = "재분석 중..."
PUBLISH_STATUS_MSG        = "노션 페이지 생성 중..."
PUBLISH_ERROR_TMPL        = "노션 발행 실패: {error}"

# 갤러리 프로필
PROFILE_TITLE_TMPL        = "### {emoji} {game_name} 게임 갤러리 민심 리포트"
PROFILE_PERIOD_LABEL      = "🗓️ 분석 기간:"
PROFILE_TEMP_LABEL        = "민심 온도 / 100"
PROFILE_KEYWORD_TMPL      = "🏷️ **핵심 키워드 TOP 5:** {keywords}"
PROFILE_ONELINER_PREFIX   = "💬"
PROFILE_PERIOD_DETAIL_TMPL = (
    "총 {days}일간 · 전체 {total}개 (개념글 {concept}개 + 일반글 {normal}개) · 분석 표본 {analysis}개"
)

# ─────────────────────────────────────────────
# 민심 온도 (9번 반영 — 측정 기준 상세)
# ─────────────────────────────────────────────
TOOLTIP_SENTIMENT_SCORE = (
    "민심 온도 측정 기준 (0~100점)\n\n"
    "[AI가 종합하는 5가지 요소]\n"
    "① 긍정·부정 표현의 언급 빈도\n"
    "② 감정 강도 (분노·실망 vs 기대·만족)\n"
    "③ 이탈 신호 키워드 빈도 (환불·삭제·탈겜 등)\n"
    "④ 개념글(추천받은 고품질 글)의 여론 방향\n"
    "⑤ 갤러리 상태(이슈폭발/안정기 등) 맥락 보정\n\n"
    "[점수 기준]\n"
    "80~100 : 매우 긍정적 — 전반적 만족\n"
    "65~79  : 긍정적 — 대체로 긍정 반응\n"
    "50~64  : 보통 — 긍부정 혼재\n"
    "35~49  : 부정적 — 불만 글 많음\n"
    "0~34   : 매우 부정적 — 강한 이탈 신호\n\n"
    "※ AI 판단이므로 참고 지표로 활용하세요."
)
TOOLTIP_SENTIMENT_PERIOD = (
    "분석 기간을 2등분해 전반부/후반부 온도를 별도 측정합니다.\n"
    "두 점수 차이로 여론 추세(상승/하락/유지)를 판단합니다.\n\n"
    "예) 전반부 30 → 후반부 55 = 상승 추세"
)

# 탭 내부 문자열
SUMMARY_TEMP_TITLE     = "### 🌡️ 민심 온도 변화"
SUMMARY_TEMP_EARLY     = "기간 전반부"
SUMMARY_TEMP_LATE      = "기간 후반부"
SUMMARY_TEMP_OVERALL   = "전체 평균"
SUMMARY_TREND_TMPL     = "기간 내 민심 추세: **{trend}**"
SUMMARY_POSITIVE_TITLE = "##### 🟢 긍정 여론"
SUMMARY_NEGATIVE_TITLE = "##### 🔴 부정 여론"
TREND_UP   = "상승"
TREND_DOWN = "하락"
TREND_FLAT = "유지"

TIMELINE_CHART_TITLE    = "날짜별 게시글 수 추이 (전체 기준)"
TIMELINE_CHART_ALL      = "전체 게시글"
TIMELINE_NO_DATA        = "날짜 데이터가 부족하여 차트를 생성할 수 없습니다."
TIMELINE_PERIOD_TMPL    = "분석 기간: {start} ~ {end}"
TIMELINE_ISSUE_TITLE    = "### 🗓️ 이슈 타임라인"
TIMELINE_NO_ISSUE       = "분석 기간 내 뚜렷한 이슈 타임라인이 감지되지 않았습니다."
TIMELINE_ISSUE_DEFAULT  = "이슈 감지"
TIMELINE_PATCH_TITLE    = "### 🛠️ 공식 패치/업데이트 타임라인"
TIMELINE_PATCH_CAPTION  = "AI가 알고 있는 공식 업데이트 정보입니다. 외부 링크가 있으면 연결됩니다."
TIMELINE_PATCH_EXPANDER = "📋 패치노트 타임라인 펼쳐보기"
TIMELINE_EXT_LINK_LABEL = "🔗 링크"
TIMELINE_ORIG_LINK_LABEL = "→ 원문"

SENTIMENT_ICON           = {"긍정": "🟢", "부정": "🔴", "혼재": "🟡"}
SENTIMENT_CHANGE_DEFAULT = "혼재"
SENTIMENT_ICON_DEFAULT   = "🟡"

# ─────────────────────────────────────────────
# 불만 카테고리 (강도 점수 시각화 방식 변경)
# ─────────────────────────────────────────────
COMPLAINT_TITLE         = "### ⚠️ 불만 카테고리별 분석"
COMPLAINT_NO_DATA       = "불만 카테고리 데이터가 없습니다."
COMPLAINT_RADAR_NAME    = "불만 강도"
COMPLAINT_NO_SUMMARY    = "데이터 없음"
COMPLAINT_REF_LINK_LABEL = "📎 관련 게시글"
COMPLAINT_EXPANDER_TMPL  = "{emoji} {label}"
COMPLAINT_SUMMARY_LABEL  = "**요약:**"
COMPLAINT_EXAMPLE_LABEL  = "**대표 발언:**"

TOOLTIP_COMPLAINT_SCORE = (
    "불만 강도 점수 (0~10점)\n\n"
    "[계산 논리]\n"
    "강도 = 키워드 등장 비율 × 감정 강도 가중치\n\n"
    "① 해당 카테고리 키워드가 등장한 게시글 수 / 전체 분석 게시글 수\n"
    "② 단순 언급이 아닌 강한 부정 감정이 동반된 경우 가중치 1.5배\n"
    "③ 최종 점수를 0~10 구간으로 정규화\n\n"
    "[점수 기준]\n"
    "0~2  : 거의 없음\n"
    "3~4  : 낮음 (소수 언급)\n"
    "5~6  : 중간 (주의 필요)\n"
    "7~8  : 높음 (유저 불만 상당)\n"
    "9~10 : 심각 (긴급 대응 필요)"
)

# ─────────────────────────────────────────────
# 유저 세그먼트 (별도 탭)
# ─────────────────────────────────────────────
SEGMENT_TAB_TITLE    = "### 👥 유저 세그먼트별 반응"
SEGMENT_CORE_LABEL   = "🛡️ 코어 유저 (고닉)"
SEGMENT_CASUAL_LABEL = "🌊 라이트 유저 (유동)"
SEGMENT_INSIGHT_TITLE = "### 💡 세그먼트 인사이트"
SEGMENT_POSTS_TITLE_TMPL = "#### {label} 주요 게시글"
SEGMENT_POSTS_EMPTY  = "해당 세그먼트의 대표 게시글이 없습니다."

CHURN_TITLE         = "### 🚨 이탈 위험 신호"
CHURN_COUNT_TMPL    = "**강한 이탈 신호 언급:** {count}회"
CHURN_SUMMARY_LABEL = "**종합 분석:**"
CHURN_REASON_LABEL  = "**주요 이탈 원인:**"
CHURN_RISK_LABELS   = {"high": "🚨 높음", "medium": "👀 주의", "low": "✅ 낮음"}
CHURN_RISK_TITLE    = "이탈 위험도"

SEGMENT_TEMP_TMPL = "{temp}점"
SEGMENT_GAP_PREFIX = "💡 **인사이트:**"

TEMP_LABELS = {80: "매우 긍정적", 65: "긍정적", 50: "보통", 35: "부정적", 0: "매우 부정적"}

# ─────────────────────────────────────────────
# PM 체크리스트
# ─────────────────────────────────────────────
CHECKLIST_TITLE   = "### 🚨 PM 액션 체크리스트"
CHECKLIST_CAPTION = "AI가 커뮤니티 동향을 기반으로 도출한 대응 우선순위입니다."
CHECKLIST_NO_DATA = "체크리스트 데이터가 없습니다."
CHECKLIST_REF_LINK_LABEL = "📎 관련 게시글"

# ─────────────────────────────────────────────
# 원본 데이터
# ─────────────────────────────────────────────
RAW_TITLE_TMPL      = "**전체 {total}개 게시글 · 분석 표본 {analysis}개 (개념글 위주)**"
RAW_ALL_TITLE       = "#### 전체 수집 목록 (날짜별)"
RAW_ANALYSIS_TITLE  = "#### AI 분석 표본 (본문 수집 완료)"
RAW_DATE_GROUP_TMPL = "📅 {date} — {count}개"
RAW_BADGE_CONCEPT   = "🔥[개념]"
RAW_BADGE_NORMAL    = "💬[일반]"
RAW_POST_META_TMPL  = "(댓글: {count}개 / {utype})"
RAW_NO_DATE_LABEL   = "날짜 없음"

# 액션바
ACTIONBAR_TITLE                = "### 📝 검수 및 발행"
ACTIONBAR_FEEDBACK_LABEL       = "피드백"
ACTIONBAR_FEEDBACK_PLACEHOLDER = "특정 항목을 더 자세히 분석해줘, 이탈 원인에 집중해줘 등..."

# Step 5
NOTION_SUCCESS_MSG = "🎉 노션 리포트 발행 완료!"
NOTION_LINK_LABEL  = "🔗 생성된 노션 리포트 확인하기"

# ─────────────────────────────────────────────
# 유틸
# ─────────────────────────────────────────────
def sanitize_for_display(text: str) -> str:
    """취소선(~~) 방지 — 물결표 → 유사 문자."""
    return str(text).replace("~", "∼")

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
TAB_STYLE_CSS = """
<style>
div[data-testid="stTabs"] button[data-baseweb="tab"] {
    background:#f8f9fa; border:1.5px solid #dee2e6;
    border-radius:8px; margin:0 3px 0 0;
    padding:7px 16px; font-weight:600; font-size:0.85rem; color:#495057;
    transition:all 0.15s;
}
div[data-testid="stTabs"] button[data-baseweb="tab"]:hover {
    background:#e9ecef; border-color:#adb5bd; color:#212529;
}
div[data-testid="stTabs"] button[aria-selected="true"][data-baseweb="tab"] {
    background:#3b4890; border-color:#3b4890; color:white;
}
div[data-testid="stTabs"] div[data-baseweb="tab-border"] { display:none; }

/* 사이드바 진행 단계 */
.step-done    { color:#adb5bd !important; }
.step-current { background:#3b4890; color:white !important; border-radius:8px; }
.step-wait    { color:#dee2e6 !important; }
</style>
"""

TOOLTIP_CSS = """
<style>
.tt-wrap { position:relative; display:inline-block; cursor:help; }
.tt-wrap .tt-box {
    visibility:hidden; opacity:0;
    background:#1e2129; color:#f8f9fa;
    border-radius:8px; padding:12px 16px;
    font-size:0.78rem; line-height:1.65; white-space:pre-line;
    position:absolute; z-index:99999; bottom:130%; left:0;
    transform:none;
    box-shadow:0 4px 20px rgba(0,0,0,0.3);
    transition:opacity 0.15s; pointer-events:none;
    min-width:280px; max-width:420px; word-break:keep-all;
}
.tt-wrap .tt-box.tt-wide { max-width:520px; }
.tt-wrap:hover .tt-box { visibility:visible; opacity:1; }
.tt-wrap .tt-box::after {
    content:""; position:absolute; top:100%; left:20px;
    border:6px solid transparent; border-top-color:#1e2129;
}
.floating-guide {
    position:fixed; top:64px; right:12px; z-index:9998;
    background:#3b4890; color:white;
    padding:8px 20px; border-radius:20px;
    font-size:0.85rem; font-weight:700;
    white-space:nowrap;
    box-shadow:0 4px 16px rgba(59,72,144,0.4);
    pointer-events:none;
}
</style>
"""

# ─────────────────────────────────────────────
# AI 프롬프트 — Step 2 경량 진단
# ─────────────────────────────────────────────
def build_diagnosis_ai_prompt(gallery_name, top_words, subtype_id, daily_avg):
    from config import GALLERY_SUBTYPES, ANALYSIS_FOCUS_OPTIONS
    subtype = GALLERY_SUBTYPES.get(subtype_id, GALLERY_SUBTYPES["stable"])
    focus_ids = list(ANALYSIS_FOCUS_OPTIONS.keys())
    return f"""
당신은 게임 커뮤니티 분석 전문가입니다.
아래 정보를 바탕으로 이 갤러리가 어떤 게임/주제에 관한 갤러리인지 파악하고,
최적의 분석 방향을 추천하세요.

[갤러리 정보]
- 갤러리명: {gallery_name}
- 자주 등장한 제목 키워드: {', '.join(top_words[:10])}
- 자동 감지된 갤러리 상태: {subtype['label']} ({subtype['desc']})
- 일평균 게시글 수: {daily_avg}개

[분석 방향 옵션]: {', '.join(focus_ids)}

[출력 JSON 스키마 — 반드시 이 구조만 출력]:
{{
  "topic_guess": "추정되는 게임명 또는 주제",
  "topic_reason": "추정 근거 (2~3가지 키워드 근거, 개조식 나열)",
  "suggested_focus": ["권장 분석 방향 ID 1개 이상 — 위 옵션에서 선택"],
  "suggested_focus_reason": "이 방향을 추천하는 이유 (1~2문장, 개조식)",
  "warning": "주의 사항이 있으면 1문장, 없으면 빈 문자열"
}}
"""


# ─────────────────────────────────────────────
# AI 프롬프트 — Step 3 메인 분석
# ─────────────────────────────────────────────
def build_main_analysis_prompt(gallery_id, game_name, subtype_label, subtype_desc,
                                subtype_focus, analysis_focus_label,
                                post_data_text, analysis_days, total_posts,
                                concept_posts, date_summary, user_feedback=""):
    bt = chr(96) * 3
    fb = f"\n\n[사용자 추가 지시]:\n{user_feedback}\n" if user_feedback else ""
    return f"""
당신은 게임사업 PM의 관점에서 커뮤니티 데이터를 분석하는 전문 애널리스트입니다.
팩트 중심의 간결한 개조식으로, PM이 회의에서 바로 사용할 수 있는 수준의 리포트를 작성하세요.{fb}

[분석 대상]
- 갤러리 ID: {gallery_id}
- 게임명: {game_name}
- 갤러리 상태: {subtype_label} — {subtype_desc}
- 분석 포커스: {subtype_focus}
- 요청된 분석 방향: {analysis_focus_label}
- 분석 기간: 최근 {analysis_days}일
- 전체 게시글 수: {total_posts}개 (개념글 {concept_posts}개)
- 날짜별 전체 게시글 수: {date_summary}

[데이터 구성 안내]
- 아래 게시글은 AI 분석용 표본입니다 (개념글 위주, 부족 시 고댓글 일반글 보충)
- 날짜별 게시글 수 통계는 전체 수집 기준이며 위 [날짜별 전체 게시글 수]를 참고하세요

[작성 규칙 — 위반 시 시스템 파싱 오류]:
1. {bt} 기호 절대 사용 금지. 순수 JSON만 출력.
2. 큰따옴표(")·줄바꿈 문자 사용 금지. 강조는 작은따옴표(').
3. 마크다운 볼드(**), 물결표(~) 기호 사용 금지.
4. 서술형 대신 명사형 종결/개조식.
5. URL 인용 시 "[글 제목](URL)" 형식.
6. 수치 항상 포함.

[출력 JSON 스키마]:
{{
  "game_name_detected": "AI가 추론한 실제 게임명",
  "critic_one_liner": "게임 PM 관점 한줄 민심 요약 (이모지 포함)",
  "top_keywords": ["키워드1","키워드2","키워드3","키워드4","키워드5"],
  "sentiment_score": {{
    "overall": 0~100,
    "early_period": 0~100,
    "late_period": 0~100,
    "trend": "상승 또는 하락 또는 유지"
  }},
  "issue_timeline": [
    {{"date":"YYYY-MM-DD","event":"이슈 한줄 요약",
      "impact":"high/medium/low","sentiment_change":"긍정/부정/혼재",
      "ref_url":"대표 게시글 URL 또는 빈 문자열"}}
  ],
  "complaint_analysis": {{
    "balance":   {{"score":0~10,"summary":"요약","example":"대표 발언","example_url":"URL 또는 빈 문자열"}},
    "operation": {{"score":0~10,"summary":"요약","example":"대표 발언","example_url":"URL 또는 빈 문자열"}},
    "bug":       {{"score":0~10,"summary":"요약","example":"대표 발언","example_url":"URL 또는 빈 문자열"}},
    "payment":   {{"score":0~10,"summary":"요약","example":"대표 발언","example_url":"URL 또는 빈 문자열"}},
    "content":   {{"score":0~10,"summary":"요약","example":"대표 발언","example_url":"URL 또는 빈 문자열"}}
  }},
  "churn_analysis": {{
    "risk_level":"high/medium/low",
    "strong_signal_count":숫자,
    "main_reasons":["원인1","원인2"],
    "summary":"종합 요약"
  }},
  "segment_analysis": {{
    "core_user_temp":0~100,
    "casual_user_temp":0~100,
    "core_main_concern":"코어 유저 주요 관심사",
    "casual_main_concern":"라이트 유저 주요 관심사",
    "gap_insight":"두 그룹 온도 차 인사이트",
    "core_key_posts":[
      {{"summary":"게시글 핵심 요약","url":"URL 또는 빈 문자열"}}
    ],
    "casual_key_posts":[
      {{"summary":"게시글 핵심 요약","url":"URL 또는 빈 문자열"}}
    ]
  }},
  "sentiment_summary": {{
    "positive":["긍정 요약1","긍정 요약2"],
    "negative":["부정 요약1","부정 요약2"]
  }},
  "pm_checklist": [
    {{"priority":"high/medium/low",
      "action":"관찰된 동향이나 상황 팩트 기술 (지시형 금지, 상황 기술형)",
      "reason":"근거",
      "ref_url":"URL 또는 빈 문자열"}}
  ],
  "patch_search_query": "패치노트 검색 최적 검색어"
}}

[AI 분석 표본 게시글]:
{post_data_text}
"""


# ─────────────────────────────────────────────
# AI 프롬프트 — 패치 타임라인
# ─────────────────────────────────────────────
def build_patch_search_prompt(game_name, analysis_days, spike_dates):
    spike_info = ", ".join(spike_dates) if spike_dates else "없음"
    return f"""
당신은 게임 정보 전문가입니다.
게임명: {game_name}
요청 기간: 최근 {analysis_days}일
커뮤니티 글 급증 날짜: {spike_info}

위 게임의 최근 {analysis_days}일 내 주요 업데이트, 패치노트, 공식 이벤트 중
알고 있는 내용을 아래 형식으로 정리하세요.
글 급증 날짜({spike_info})와 연관 이벤트가 있으면 반드시 포함하세요.
공식 URL이 있으면 함께 명시하세요.

출력 형식:
- [날짜] 이벤트 제목 / 주요 내용 (URL: 공식 링크 또는 생략)

정보가 없거나 확실하지 않으면 포함하지 마세요.
아무것도 모르면 "확인된 공식 패치 정보 없음" 한 줄만 출력하세요.
"""
# ─────────────────────────────────────────────
# v4 추가
# ─────────────────────────────────────────────
TREND_TITLE   = "### 🔍 주목할 동향"
TREND_NO_DATA = "특이 동향이 감지되지 않았습니다."

CHART_14D_TITLE = "최근 14일간 날짜별 게시글 수"
CHART_14D_SPIKE = "빨간 막대 = 평균 대비 1.8배 이상 급증"

ANALYSIS_SPEC_TMPL = (
    "**분석 기간** {days}일 ({date_range})  ·  "
    "**전체 게시글** {total}개  ·  "
    "**개념글** {concept}개  ·  "
    "**분석 표본** {analysis}개 (개념글 위주)  ·  "
    "**갤러리 유형** {subtype}"
)
ANALYSIS_SPEC_REANALYZE = "결과가 마음에 안들면 아래 피드백 입력 후 재분석할 수 있습니다."

SEGMENT_INSIGHT_TITLE = "### 💡 세그먼트 인사이트"

# ─────────────────────────────────────────────
# v5 신규: 토스 UX 카드/CSS/팝업
# ─────────────────────────────────────────────
DIAG_CARDS = [
    {"emoji":"🔍","label":"먼저 갤러리를 파악해요","desc":"게시글 패턴과 리젠 속도를 분석해\n갤러리 상태를 진단합니다"},
    {"emoji":"🚀","label":"출시 초기 갤러리라면","desc":"버그 제보, 초기 반응, 온보딩 경험\n중심으로 분석을 집중합니다"},
    {"emoji":"🔥","label":"이슈가 터진 갤러리라면","desc":"논란 원인과 여론 변화 흐름을\n집중 추적합니다"},
    {"emoji":"📚","label":"안정기 갤러리라면","desc":"장기 유저 만족도와 메타 변화,\n밸런스 이슈를 깊게 들여다봅니다"},
    {"emoji":"📉","label":"갤러리가 조용해졌다면","desc":"이탈 원인과 잔류 유저 심리를\n파악해 현황을 정리합니다"},
    {"emoji":"💬","label":"반응 많은 글이 진짜 민심","desc":"개념글 대신 댓글 상위 게시글을\n핵심 분석 표본으로 선정합니다"},
]

GLOBAL_CSS = '''
<style>
section[data-testid="stSidebar"] { background:#f8f9fa; border-right:1px solid #e9ecef; }
section[data-testid="stSidebar"] > div { padding-top:1.5rem; }
.main .block-container { padding:1.5rem 2.5rem 2rem 2.5rem; max-width:1100px; }
div[data-testid="stTabPanel"] hr:last-of-type { display:none !important; }
button[data-testid="collapsedControl"],
button[data-testid="baseButton-headerNoPadding"] { display:none !important; }
section[data-testid="stSidebarCollapseButton"] { display:none !important; }
div[data-testid="stButton"] > button { border-radius:10px; font-weight:600; }
.step-done { padding:6px 10px; border-radius:8px; color:#1d7a3a; font-size:0.85rem; }
.step-cur  { padding:8px 12px; border-radius:8px; background:#3b4890; color:white; font-size:0.85rem; font-weight:700; }
.step-wait { padding:6px 10px; border-radius:8px; color:#adb5bd; font-size:0.85rem; }
.toss-h1 { text-align:center; font-size:2.2rem; font-weight:800; color:#1e2129; }
.toss-sub { text-align:center; color:#6c757d; margin-bottom:2rem; }
.toss-card {
  background:linear-gradient(135deg,#3b4890 0%,#5b6fb5 100%);
  border-radius:20px; padding:40px 32px 28px; text-align:center;
  margin:16px 0; min-height:220px;
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  box-shadow:0 8px 32px rgba(59,72,144,0.25);
}
.toss-card-emoji { font-size:3.5rem; margin-bottom:16px; }
.toss-card-label { font-size:1.4rem; font-weight:800; color:white; margin-bottom:10px; }
.toss-card-desc  { font-size:0.95rem; color:rgba(255,255,255,0.82); line-height:1.6; white-space:pre-line; }
.toss-card-dots  { margin-top:20px; display:flex; gap:6px; justify-content:center; }
.toss-dot     { font-size:0.5rem; color:rgba(255,255,255,0.35); }
.toss-dot-on  { color:white; }
.diag-msg { text-align:center; color:#3b4890; font-size:0.9rem; font-weight:600; padding:8px; margin-top:4px; }
.phase-card { background:#f8f9fa; border:1.5px solid #dee2e6; border-radius:12px; padding:18px 22px; margin:8px 0; }
.phase-card.phase-ai { background:#eef0fa; border-color:#3b4890; }
.phase-title { font-size:1rem; font-weight:700; color:#1e2129; }
.game-confirm-card { background:#fffbeb; border:1.5px solid #fbbf24; border-radius:16px; padding:22px 26px; margin-bottom:16px; }
.game-confirm-label { font-size:0.82rem; color:#92400e; font-weight:600; margin-bottom:10px; }
.game-confirm-name  { font-size:2.2rem; font-weight:800; color:#1e2129; margin-bottom:8px; }
.game-confirm-reason { font-size:0.82rem; color:#6c757d; margin-bottom:6px; }
.game-confirm-hint  { font-size:0.82rem; color:#e74c3c; font-weight:600; }
.info-card { background:#fff; border:1px solid #e9ecef; border-radius:12px; padding:1rem 1.2rem; }
.info-card-label { font-size:0.78rem; color:#6c757d; margin-bottom:4px; }
.info-card-val   { font-size:1.05rem; font-weight:700; color:#1e2129; }
.info-card-hint  { font-size:0.72rem; color:#3b4890; margin-top:4px; }
.subtype-badge { display:inline-flex; align-items:center; gap:10px; padding:10px 16px; border-radius:10px; border:1.5px solid; }
.dim-overlay { position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:9990; cursor:pointer; }
.dim-modal { position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); background:white; border-radius:16px; padding:28px 32px; z-index:9999; width:min(580px,90vw); max-height:80vh; overflow-y:auto; box-shadow:0 20px 60px rgba(0,0,0,0.25); }
.dim-modal-title { font-size:1.1rem; font-weight:800; color:#1e2129; margin-bottom:16px; }
.dim-modal-body  { font-size:0.88rem; color:#495057; line-height:1.75; }
.floating-guide { position:fixed; top:64px; right:12px; z-index:9998; background:#3b4890; color:white; padding:8px 20px; border-radius:20px; font-size:0.85rem; font-weight:700; white-space:nowrap; box-shadow:0 4px 16px rgba(59,72,144,0.4); pointer-events:none; }
</style>
'''

SENTIMENT_SCORE_DETAIL = (
    "<b>AI가 종합하는 5가지 요소</b><br><br>"
    "① <b>긍정·부정 표현 빈도</b><br>게시글 본문에서 긍정/부정 표현의 비율을 계산합니다.<br><br>"
    "② <b>감정 강도</b><br>단순 불만 vs 강한 분노·실망 표현인지를 가중합니다.<br><br>"
    "③ <b>이탈 신호 키워드 빈도</b><br>'환불', '삭제', '탈겜' 등 이탈 의도 단어를 감지합니다.<br><br>"
    "④ <b>고관여 게시글 여론 방향</b><br>댓글 수 상위 게시글의 전반적 톤을 반영합니다.<br><br>"
    "⑤ <b>갤러리 상태 맥락 보정</b><br>이슈폭발형/안정기형 등 상태에 따라 점수를 보정합니다.<br><br>"
    "<hr style='border:none;border-top:1px solid #eee;margin:12px 0;'>"
    "<b>점수 기준</b><br>"
    "80~100 : 매우 긍정적<br>65~79 : 긍정적<br>50~64 : 보통<br>35~49 : 부정적<br>0~34 : 매우 부정적<br><br>"
    "<i style='color:#888;'>AI 판단이므로 참고 지표로 활용하세요.</i>"
)

COMPLAINT_SCORE_DETAIL = (
    "<b>점수 의미 (0~10점, 높을수록 불만 심각)</b><br><br>"
    "<b style='color:#888;'>0~2점</b> — 거의 없음<br>"
    "<b style='color:#2980b9;'>3~4점</b> — 낮음: 소수 언급<br>"
    "<b style='color:#e67e22;'>5~6점</b> — 주의: 반복 언급<br>"
    "<b style='color:#c0392b;'>7~8점</b> — 높음: 유저 불만 상당<br>"
    "<b style='color:#c0392b;font-weight:900;'>9~10점</b> — 심각: 커뮤니티 주요 이슈<br><br>"
    "<hr style='border:none;border-top:1px solid #eee;margin:12px 0;'>"
    "<b>계산 방식</b><br>"
    "키워드 등장 게시글 비율 × 감정 강도 가중치 → 0~10 정규화<br>"
    "<i style='color:#888;'>단순 언급(×1.0) vs 강한 부정 표현(×1.5)</i>"
)

ISSUE_IMPACT_LEGEND = "🔴 높은 임팩트  🟡 중간 임팩트  🔵 낮은 임팩트"
TREND_PRIORITY_LEGEND = "■ 집중도 높음  ■ 주의 필요  ■ 참고 수준"