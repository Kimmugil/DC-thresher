"""
app.py v3 — 3단계 파이프라인 흐름 제어
  Step 0: URL 입력
  Step 1: 갤러리 진단 결과 확인
  Step 2: AI 질문 + 분석 방향 설정 + 기간별 게시글 수 실시간 표시
  Step 3: 수집 & AI 분석
  Step 4: 리포트 검수
  Step 5: 노션 발행 완료
"""

import streamlit as st
import random, time, threading
from datetime import datetime, timedelta

from config import APP_VERSION, ENV_NAME, TICKER_INTERVAL, ANALYSIS_FOCUS_OPTIONS
from ui_texts import (
    APP_PAGE_TITLE, APP_PAGE_ICON,
    SIDEBAR_TOOL_NAME, SIDEBAR_TOOL_CAPTION, SIDEBAR_STEP_TITLE,
    SIDEBAR_CURRENT_TARGET, SIDEBAR_VERSION_EXPANDER,
    SIDEBAR_VERSION_LABEL, SIDEBAR_HISTORY_TITLE, SIDEBAR_HISTORY,
    SIDEBAR_RESET_BTN, SIDEBAR_DAILY_AVG_TMPL, STEP_INFO, STEP_GUIDE_MESSAGES,
    STEP0_TITLE, STEP0_SUBTITLE, STEP0_INPUT_HEADER, STEP0_PLACEHOLDER,
    STEP0_CAPTION, STEP0_BTN, STEP0_WARN_EMPTY, STEP0_WARN_INVALID,
    DIAG_STATUS_MSG, DIAG_DONE_MSG, DIAG_ERROR_LABEL,
    DIAG_SECTION_TITLE, DIAG_SECTION_SUBTITLE,
    METRIC_GALLERY_NAME, METRIC_TOTAL_ROWS, METRIC_DAILY_AVG,
    METRIC_CONCEPT_COUNT, METRIC_CONCEPT_COUNT_UNIT, METRIC_GONIK_RATIO,
    METRIC_DIAG_PERIOD,
    TOOLTIP_TOTAL_ROWS, TOOLTIP_DAILY_AVG, TOOLTIP_CONCEPT_COUNT,
    TOOLTIP_GONIK_RATIO, TOOLTIP_CHART, TOOLTIP_SPIKE, TOOLTIP_SUBTYPE,
    GALLERY_NAME_TOOLTIP, GALLERY_NAME_EDIT_HINT, GALLERY_NAME_ANCHOR_ID,
    SUBTYPE_MODAL_BTN, SUBTYPE_MODAL_TITLE, SUBTYPE_MODAL_DESC,
    SUBTYPE_DEFINITIONS, SUBTYPE_CRITERIA_PREFIX, SUBTYPE_FOCUS_PREFIX,
    DIAG_CHART_TITLE, DIAG_CHART_SPIKE_LABEL,
    CHART_HOVER_TMPL, SPIKE_WARNING_TMPL, SPIKE_NEXT_STEP_MSG,
    STEP2_TITLE, STEP2_AI_STATUS, STEP2_AI_DONE,
    AI_TOPIC_CONFIRM_TITLE, AI_TOPIC_CONFIRM_DESC,
    AI_TOPIC_CONFIDENCE_TMPL, AI_TOPIC_REASON_LABEL,
    COND_GAME_INPUT_LABEL, COND_GAME_PLACEHOLDER,
    AI_FOCUS_CONFIRM_TITLE, AI_FOCUS_CONFIRM_DESC,
    AI_FOCUS_REASON_LABEL, AI_WARNING_LABEL,
    COND_PERIOD_TITLE, COND_PERIOD_CAPTION, PERIOD_OPTIONS,
    PERIOD_BTN_SELECTED, PERIOD_BTN_DEFAULT,
    PERIOD_COUNT_LOADING, PERIOD_COUNT_TMPL, PERIOD_COUNT_CONCEPT_NOTE,
    START_BTN,
    STEP3_TITLE, STEP3_SUBTITLE,
    SCRAPE_STATUS_MSG, AI_STATUS_MSG, PATCH_STATUS_MSG,
    SCRAPE_DONE_TMPL, SCRAPE_ERROR_TMPL, AI_ERROR_TMPL,
    BTN_BACK_TO_COND, BTN_BACK,
    TICKER_MESSAGES, TAB_LABELS,
    REANALYZE_STATUS_MSG, PUBLISH_STATUS_MSG, PUBLISH_ERROR_TMPL,
    NOTION_SUCCESS_MSG, NOTION_LINK_LABEL,
    TAB_STYLE_CSS, TOOLTIP_CSS,
    sanitize_for_display,
)
from dc_scraper import parse_dc_url, diagnose_gallery, count_posts_in_period, run_dc_scraper
from gallery_analyzer import detect_subtype, get_subtype_info, detect_spike_dates, guess_game_name
from ai_analyzer import diagnose_gallery_ai, analyze_gallery, fetch_patch_timeline
from report_streamlit import (
    render_gallery_profile,
    render_tab_summary, render_tab_timeline,
    render_tab_complaints, render_tab_segment, render_tab_checklist,
    render_tab_raw, render_action_bar,
)
from report_notion import upload_to_notion

# ─────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────
st.set_page_config(
    page_title=APP_PAGE_TITLE, page_icon=APP_PAGE_ICON,
    layout="wide", initial_sidebar_state="expanded",
)
st.markdown("""
<style>
section[data-testid="stSidebar"] { background:#f8f9fa; border-right:1px solid #e9ecef; }
section[data-testid="stSidebar"] > div { padding-top:1.5rem; }
.main .block-container { padding:1.5rem 2.5rem 2rem 2.5rem; max-width:1100px; }
div[data-testid="stTabPanel"] hr:last-of-type { display:none !important; }
button[data-testid="collapsedControl"],
button[data-testid="baseButton-headerNoPadding"] { display:none !important; }
section[data-testid="stSidebarCollapseButton"] { display:none !important; }
div[data-testid="stButton"] > button { border-radius:10px; font-weight:600; }
</style>
""", unsafe_allow_html=True)
st.markdown(TAB_STYLE_CSS, unsafe_allow_html=True)
st.markdown(TOOLTIP_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 세션 초기화
# ─────────────────────────────────────────────
def _init_session():
    defaults = {
        "step": 0, "raw_url": "",
        "diag": None, "diag_ai": None,
        "subtype_id": None, "game_name": "",
        "gallery_id": None, "gallery_name": None,
        "analysis_focus": "default",
        "analysis_days": 14, "selected_period": 14,
        "period_count": None,          # 기간별 게시글 수 캐시
        "period_count_loading": False,
        "scrape_result": None,
        "insights": None, "patch_timeline": "",
        "notion_page_id": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ─────────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────────
def _render_sidebar():
    with st.sidebar:
        st.markdown(f"### {SIDEBAR_TOOL_NAME}")
        st.caption(f"{SIDEBAR_TOOL_CAPTION}  |  {APP_VERSION}")
        st.divider()

        cur = st.session_state.step
        st.markdown(f"**{SIDEBAR_STEP_TITLE}**")
        for i, (icon, label) in enumerate(STEP_INFO):
            if i < cur:
                st.markdown(f"<div style='padding:6px 10px;border-radius:8px;color:#adb5bd;font-size:0.85rem;'>✔ {label}</div>", unsafe_allow_html=True)
            elif i == cur:
                st.markdown(f"<div style='padding:8px 12px;border-radius:8px;background:#3b4890;color:white;font-size:0.85rem;font-weight:700;'>{icon} {label}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='padding:6px 10px;border-radius:8px;color:#dee2e6;font-size:0.85rem;'>○ {label}</div>", unsafe_allow_html=True)
            if i < len(STEP_INFO)-1:
                st.markdown("<div style='margin:2px 0 2px 20px;width:2px;height:12px;background:#dee2e6;'></div>", unsafe_allow_html=True)

        if cur >= 1 and st.session_state.gallery_name:
            st.divider()
            st.markdown(f"**{SIDEBAR_CURRENT_TARGET}**")
            st.markdown(f"🎮 **{st.session_state.game_name or st.session_state.gallery_name}**")
            if st.session_state.diag:
                st.caption(SIDEBAR_DAILY_AVG_TMPL.format(avg=st.session_state.diag["daily_avg"]))

        st.divider()
        with st.expander(SIDEBAR_VERSION_EXPANDER):
            ec = "#e74c3c" if ENV_NAME == "DEV" else "#2ecc71"
            st.markdown(f"<span style='background:{ec};color:#fff;padding:2px 8px;border-radius:6px;font-size:0.75rem;font-weight:700;'>{ENV_NAME}</span>", unsafe_allow_html=True)
            st.markdown(f"**{SIDEBAR_VERSION_LABEL}** {APP_VERSION}")
            st.markdown(f"**{SIDEBAR_HISTORY_TITLE}**")
            for item in SIDEBAR_HISTORY: st.markdown(f"- {item}")

        if cur > 0:
            st.divider()
            if st.button(SIDEBAR_RESET_BTN, use_container_width=True):
                for k in list(st.session_state.keys()): del st.session_state[k]
                st.rerun()


# ─────────────────────────────────────────────
# 갤러리 유형 팝업
# ─────────────────────────────────────────────
def _subtype_modal_content():
    st.markdown(SUBTYPE_MODAL_DESC); st.write("")
    for s in SUBTYPE_DEFINITIONS:
        with st.expander(f"{s['emoji']} **{s['label']}** — {s['desc']}", expanded=False):
            st.markdown(f"{SUBTYPE_CRITERIA_PREFIX} {s['criteria']}")
            st.markdown(f"{SUBTYPE_FOCUS_PREFIX} {s['focus']}")

_HAS_DIALOG = hasattr(st, "dialog")
if _HAS_DIALOG:
    @st.dialog(SUBTYPE_MODAL_TITLE, width="large")
    def _show_subtype_modal(): _subtype_modal_content()
else:
    def _show_subtype_modal():
        st.session_state["_show_modal"] = not st.session_state.get("_show_modal", False)
        st.rerun()

def _tip(text, wide=False):
    cls = "tt-box tt-wide" if wide else "tt-box"
    return (f"<span class='tt-wrap' style='color:#3b4890;cursor:help;'>ⓘ"
            f"<span class='{cls}'>{text}</span></span>")

def _card(col, label, value, tooltip):
    with col:
        st.markdown(
            f"<div style='background:#fff;border:1px solid #e9ecef;border-radius:12px;padding:1rem 1.2rem;'>"
            f"<div style='font-size:0.78rem;color:#6c757d;margin-bottom:4px;'>{label} {_tip(tooltip)}</div>"
            f"<div style='font-size:1.5rem;font-weight:700;color:#1e2129;'>{value}</div>"
            f"</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    _init_session()
    _render_sidebar()

    guide = STEP_GUIDE_MESSAGES.get(st.session_state.step, "")
    if guide:
        st.markdown(f"<div class='floating-guide'>💡 {guide}</div>", unsafe_allow_html=True)

    if not _HAS_DIALOG and st.session_state.get("_show_modal"):
        with st.expander(SUBTYPE_MODAL_TITLE, expanded=True):
            _subtype_modal_content()
            if st.button("✕ 닫기", key="modal_close"):
                st.session_state["_show_modal"] = False; st.rerun()

    # ── Step 0: URL 입력 ──────────────────────────────────────────────
    if st.session_state.step == 0:
        _, col, _ = st.columns([1,3,1])
        with col:
            st.markdown("<div style='height:2rem;'></div>", unsafe_allow_html=True)
            st.markdown(f"<h1 style='text-align:center;font-size:2.2rem;font-weight:800;'>{STEP0_TITLE}</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align:center;color:#6c757d;margin-bottom:2rem;'>{STEP0_SUBTITLE}</p>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown(f"#### {STEP0_INPUT_HEADER}")
                raw_url = st.text_input("URL", placeholder=STEP0_PLACEHOLDER, label_visibility="collapsed")
                st.caption(STEP0_CAPTION); st.write("")
                if st.button(STEP0_BTN, type="primary", use_container_width=True):
                    if not raw_url.strip(): st.warning(STEP0_WARN_EMPTY); return
                    _, gal_id = parse_dc_url(raw_url)
                    if not gal_id: st.warning(STEP0_WARN_INVALID); return
                    st.session_state.raw_url = raw_url
                    with st.status(DIAG_STATUS_MSG, expanded=True) as status:
                        pbar = st.progress(0); info = st.empty()
                        def _cb(msg, val): info.markdown(f"🔍 {msg}"); pbar.progress(int(val))
                        diag = diagnose_gallery(raw_url, progress_cb=_cb)
                        if diag.get("error"):
                            status.update(label=DIAG_ERROR_LABEL, state="error")
                            st.error(diag["error"]); return
                        st.session_state.diag         = diag
                        st.session_state.subtype_id   = detect_subtype(diag)
                        st.session_state.game_name    = guess_game_name(
                            diag["gallery_name"], diag["top_title_words"])
                        st.session_state.gallery_id   = diag["gallery_id"]
                        st.session_state.gallery_name = diag["gallery_name"]
                        st.session_state.step = 1
                        status.update(label=DIAG_DONE_MSG, state="complete")
                        st.rerun()

    # ── Step 1: 진단 결과 ──────────────────────────────────────────────
    elif st.session_state.step == 1:
        diag    = st.session_state.diag
        subtype = get_subtype_info(st.session_state.subtype_id)

        st.markdown(DIAG_SECTION_TITLE)
        st.markdown(f"<p style='color:#6c757d;margin-top:-0.5rem;margin-bottom:1.2rem;'>{DIAG_SECTION_SUBTITLE}</p>", unsafe_allow_html=True)

        # 메트릭 카드
        c1,c2,c3,c4,c5,c6 = st.columns(6)
        with c1:  # 갤러리명
            st.markdown(
                f"<div style='background:#fff;border:1px solid #e9ecef;border-radius:12px;padding:1rem 1.2rem;'>"
                f"<div style='font-size:0.78rem;color:#6c757d;margin-bottom:4px;'>{METRIC_GALLERY_NAME} "
                f"<span class='tt-wrap' style='color:#3b4890;cursor:help;'>ⓘ<span class='tt-box tt-wide'>{GALLERY_NAME_TOOLTIP}</span></span></div>"
                f"<div style='font-size:1rem;font-weight:700;color:#1e2129;'>{diag['gallery_name']}</div>"
                f"<div style='font-size:0.72rem;color:#3b4890;margin-top:4px;'>{GALLERY_NAME_EDIT_HINT}</div>"
                f"</div>", unsafe_allow_html=True)
        _card(c2, METRIC_DIAG_PERIOD, f"{diag.get('diag_start','')}~{diag.get('diag_end','')}", TOOLTIP_CHART)
        _card(c3, METRIC_TOTAL_ROWS, f"{diag['total_rows']}개", TOOLTIP_TOTAL_ROWS)
        _card(c4, METRIC_DAILY_AVG, f"{diag['daily_avg']}개", TOOLTIP_DAILY_AVG)
        _card(c5, METRIC_CONCEPT_COUNT, f"{diag.get('concept_total',0)}{METRIC_CONCEPT_COUNT_UNIT}", TOOLTIP_CONCEPT_COUNT)
        _card(c6, METRIC_GONIK_RATIO, f"{round(diag['gonik_ratio']*100)}%", TOOLTIP_GONIK_RATIO)

        st.write("")

        # 서브타입 배지
        sc = subtype["color"]
        col_b, col_btn = st.columns([3,1])
        with col_b:
            st.markdown(
                f"<div style='display:inline-flex;align-items:center;gap:10px;"
                f"padding:10px 16px;border-radius:10px;border:1.5px solid {sc};background:{sc}0d;'>"
                f"<span style='font-size:1.2rem;'>{subtype['emoji']}</span>"
                f"<div><b style='color:{sc};'>{subtype['label']}</b>"
                f"<div style='font-size:0.8rem;color:#6c757d;'>{subtype['desc']}</div></div>"
                f"<span class='tt-wrap' style='margin-left:8px;color:#3b4890;cursor:help;'>ⓘ"
                f"<span class='tt-box'>{TOOLTIP_SUBTYPE}</span></span></div>",
                unsafe_allow_html=True)
        with col_btn:
            if st.button(SUBTYPE_MODAL_BTN, use_container_width=True): _show_subtype_modal()

        st.write("")

        # 진단 기간 차트 (수집된 날짜만 표시)
        if diag["date_counts"]:
            import plotly.graph_objects as go
            dc     = diag["date_counts"]
            dates  = sorted(dc.keys())
            counts = [dc[d] for d in dates]
            spikes = detect_spike_dates(dc)
            colors = ["#e74c3c" if d in spikes else "#3b4890" for d in dates]
            fig = go.Figure(go.Bar(
                x=dates, y=counts,
                marker=dict(color=colors, line=dict(width=0)),
                hovertemplate=CHART_HOVER_TMPL))
            fig.update_layout(
                title=dict(text=f"{DIAG_CHART_TITLE}  ({DIAG_CHART_SPIKE_LABEL})",
                           font=dict(size=13, color="#495057")),
                height=220, margin=dict(l=0, r=0, t=42, b=0),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False, tickfont=dict(size=10), tickangle=-45, fixedrange=True),
                yaxis=dict(gridcolor="#f1f3f5", tickfont=dict(size=11), fixedrange=True),
                dragmode=False, showlegend=False)
            st.plotly_chart(fig, use_container_width=True,
                            config={"displayModeBar": False, "scrollZoom": False})
            if spikes:
                st.warning(SPIKE_WARNING_TMPL.format(dates=", ".join(spikes)))
                st.info(SPIKE_NEXT_STEP_MSG)

        st.divider()
        if st.button("다음 단계 — AI 분석 방향 설정 →", type="primary", use_container_width=True):
            st.session_state.step = 2
            st.rerun()

    # ── Step 2: AI 인터랙션 + 분석 조건 설정 ────────────────────────────
    elif st.session_state.step == 2:
        diag = st.session_state.diag

        st.markdown(STEP2_TITLE)

        # 경량 AI 호출 (아직 안 됐을 때만)
        if st.session_state.diag_ai is None:
            with st.status(STEP2_AI_STATUS, expanded=True) as status:
                ai_result, ai_err = diagnose_gallery_ai(
                    gallery_name=diag["gallery_name"],
                    top_words=diag["top_title_words"],
                    subtype_id=st.session_state.subtype_id,
                    daily_avg=diag["daily_avg"],
                )
                if ai_err or not ai_result:
                    st.warning(f"AI 특성 파악 실패: {ai_err}. 기본값으로 진행합니다.")
                    ai_result = {
                        "topic_guess": st.session_state.game_name,
                        "topic_confidence": 50,
                        "topic_reason": "AI 호출 실패 — 직접 수정해 주세요",
                        "suggested_focus": "default",
                        "suggested_focus_reason": "",
                        "warning": "",
                    }
                st.session_state.diag_ai = ai_result
                status.update(label=STEP2_AI_DONE, state="complete")

        ai = st.session_state.diag_ai

        # ① 게임명 확인
        st.markdown(
            f"<div style='background:#fffbeb;border:1.5px solid #fbbf24;border-radius:10px;"
            f"padding:14px 18px;margin-bottom:1rem;'>"
            f"<div style='font-weight:700;margin-bottom:4px;'>{AI_TOPIC_CONFIRM_TITLE}</div>"
            f"<div style='font-size:0.85rem;color:#78716c;margin-bottom:8px;'>{AI_TOPIC_CONFIRM_DESC}</div>"
            f"<div style='font-size:0.82rem;color:#6c757d;'>"
            f"{AI_TOPIC_CONFIDENCE_TMPL.format(pct=ai.get('topic_confidence',50))} &nbsp;|&nbsp; "
            f"{AI_TOPIC_REASON_LABEL} {ai.get('topic_reason','')}</div></div>",
            unsafe_allow_html=True)
        st.markdown(f"<div id='{GALLERY_NAME_ANCHOR_ID}'></div>", unsafe_allow_html=True)
        game_name_input = st.text_input(
            COND_GAME_INPUT_LABEL,
            value=ai.get("topic_guess", st.session_state.game_name),
            placeholder=COND_GAME_PLACEHOLDER,
            label_visibility="collapsed")
        st.write("")

        # ② 분석 방향 선택
        st.markdown(
            f"<div style='background:#f0f4ff;border:1.5px solid #3b4890;border-radius:10px;"
            f"padding:14px 18px;margin-bottom:1rem;'>"
            f"<div style='font-weight:700;margin-bottom:4px;'>{AI_FOCUS_CONFIRM_TITLE}</div>"
            f"<div style='font-size:0.85rem;color:#495057;margin-bottom:4px;'>{AI_FOCUS_CONFIRM_DESC}</div>"
            f"<div style='font-size:0.82rem;color:#6c757d;'>"
            f"{AI_FOCUS_REASON_LABEL} {ai.get('suggested_focus_reason','')}</div></div>",
            unsafe_allow_html=True)

        focus_keys  = list(ANALYSIS_FOCUS_OPTIONS.keys())
        default_idx = focus_keys.index(ai.get("suggested_focus","default")) \
                      if ai.get("suggested_focus","default") in focus_keys else 0
        analysis_focus = st.radio(
            "분석 방향",
            options=focus_keys,
            format_func=lambda x: ANALYSIS_FOCUS_OPTIONS[x],
            index=default_idx,
            label_visibility="collapsed",
        )

        if ai.get("warning"):
            st.warning(f"{AI_WARNING_LABEL} {ai['warning']}")

        st.write("")

        # ③ 분석 기간 선택 + 실시간 게시글 수
        st.markdown(COND_PERIOD_TITLE)
        p_cols = st.columns(3)
        for idx, (days, (plabel, pdesc)) in enumerate(PERIOD_OPTIONS.items()):
            with p_cols[idx]:
                is_sel = (st.session_state.selected_period == days)
                bdr = "2px solid #3b4890" if is_sel else "1px solid #dee2e6"
                bg  = "#eef0fa" if is_sel else "#fff"
                tc  = "#3b4890" if is_sel else "#495057"
                st.markdown(
                    f"<div style='border:{bdr};border-radius:10px;padding:14px;"
                    f"background:{bg};text-align:center;margin-bottom:4px;'>"
                    f"<div style='font-weight:700;color:{tc};'>{plabel}</div>"
                    f"<div style='font-size:0.8rem;color:#6c757d;'>{pdesc}</div></div>",
                    unsafe_allow_html=True)
                bl = PERIOD_BTN_SELECTED if is_sel else PERIOD_BTN_DEFAULT
                if st.button(bl, key=f"pd_{days}", use_container_width=True,
                             type="primary" if is_sel else "secondary"):
                    st.session_state.selected_period = days
                    st.session_state.period_count    = None  # 캐시 무효화
                    st.rerun()

        st.caption(COND_PERIOD_CAPTION)

        # 기간별 게시글 수 실시간 표시
        sel_days = st.session_state.selected_period
        pc       = st.session_state.period_count

        count_box = st.empty()
        if pc is None or pc.get("_days") != sel_days:
            count_box.info(PERIOD_COUNT_LOADING)
            # 빠른 카운팅 (별도 스레드 없이 직접 호출 — 비교적 빠른 목록만 체크)
            result = count_posts_in_period(st.session_state.raw_url, sel_days)
            result["_days"] = sel_days
            st.session_state.period_count = result
            pc = result

        count_box.success(
            PERIOD_COUNT_TMPL.format(
                total=pc.get("total",0),
                concept=pc.get("concept",0),
                normal=pc.get("normal",0)))
        st.caption(PERIOD_COUNT_CONCEPT_NOTE)
        st.write("")

        if st.button(START_BTN, type="primary", use_container_width=True):
            st.session_state.game_name     = game_name_input.strip() or st.session_state.game_name
            st.session_state.analysis_days = sel_days
            st.session_state.analysis_focus = analysis_focus
            st.session_state.step = 3
            st.markdown("<script>window.scrollTo({top:0,behavior:'smooth'});</script>",
                        unsafe_allow_html=True)
            st.rerun()

    # ── Step 3: 수집 & AI 분석 ────────────────────────────────────────
    elif st.session_state.step == 3:
        raw_url       = st.session_state.raw_url
        analysis_days = st.session_state.analysis_days
        gallery_id    = st.session_state.gallery_id
        game_name     = st.session_state.game_name
        subtype_id    = st.session_state.subtype_id
        analysis_focus = st.session_state.analysis_focus
        diag_data     = st.session_state.diag

        st.markdown(STEP3_TITLE)
        st.markdown(f"<p style='color:#6c757d;'>{STEP3_SUBTITLE}</p>", unsafe_allow_html=True)

        try:
            with st.status(SCRAPE_STATUS_MSG, expanded=True) as status:
                pbar = st.progress(0); info = st.empty()
                def scb(msg, val): info.markdown(f"🔍 {msg}"); pbar.progress(int(val))
                scrape_result = run_dc_scraper(raw_url, days_limit=analysis_days, progress_cb=scb)
                tot = scrape_result["total_posts"]
                ana = scrape_result["analysis_count"]
                done_msg = SCRAPE_DONE_TMPL.format(total=tot, analysis=ana)
                info.markdown(done_msg); pbar.progress(100)
                status.update(label=done_msg, state="complete")
        except Exception as e:
            st.error(SCRAPE_ERROR_TMPL.format(error=e))
            if st.button(BTN_BACK_TO_COND): st.session_state.step=2; st.rerun()
            return

        res_box = [None, None]; ev = threading.Event()
        def run_ai():
            try:
                res_box[0], res_box[1] = analyze_gallery(
                    gallery_id=gallery_id, game_name=game_name,
                    subtype_id=subtype_id,
                    analysis_data=scrape_result["analysis_data"],
                    all_metas=scrape_result["all_metas"],
                    analysis_days=analysis_days,
                    analysis_focus=analysis_focus,
                )
            except Exception as ex: res_box[1] = str(ex)
            finally: ev.set()
        threading.Thread(target=run_ai, daemon=True).start()

        with st.status(AI_STATUS_MSG, expanded=True):
            ticker = st.empty()
            while not ev.is_set():
                ticker.info(f"💡 {random.choice(TICKER_MESSAGES)}")
                time.sleep(TICKER_INTERVAL)
            ticker.empty()

        if res_box[1]:
            st.error(AI_ERROR_TMPL.format(error=res_box[1]))
            if st.button(BTN_BACK): st.session_state.step=2; st.rerun()
            return

        spike_dates = detect_spike_dates(scrape_result.get("date_counts",{}))
        with st.status(PATCH_STATUS_MSG, expanded=False):
            patch_tl = fetch_patch_timeline(game_name, analysis_days, spike_dates)

        st.session_state.scrape_result  = scrape_result
        st.session_state.insights       = res_box[0]
        st.session_state.patch_timeline = patch_tl
        st.session_state.step = 4
        st.rerun()

    # ── Step 4: 리포트 ────────────────────────────────────────────────
    elif st.session_state.step == 4:
        ins           = st.session_state.insights
        scrape_result = st.session_state.scrape_result
        game_name     = st.session_state.game_name
        subtype_id    = st.session_state.subtype_id
        patch_tl      = st.session_state.patch_timeline

        render_gallery_profile(ins, scrape_result, game_name, subtype_id)

        tabs = st.tabs(TAB_LABELS)
        with tabs[0]: render_tab_summary(ins, scrape_result.get("analysis_data",[]))
        with tabs[1]: render_tab_timeline(ins, scrape_result, patch_tl)
        with tabs[2]: render_tab_complaints(ins)
        with tabs[3]: render_tab_segment(ins)
        with tabs[4]: render_tab_checklist(ins)
        with tabs[5]: render_tab_raw(scrape_result)

        feedback, do_reanalyze, do_publish = render_action_bar()

        if do_reanalyze:
            with st.status(REANALYZE_STATUS_MSG, expanded=True):
                new_ins, err = analyze_gallery(
                    gallery_id=st.session_state.gallery_id,
                    game_name=game_name, subtype_id=subtype_id,
                    analysis_data=scrape_result["analysis_data"],
                    all_metas=scrape_result["all_metas"],
                    analysis_days=st.session_state.analysis_days,
                    analysis_focus=st.session_state.analysis_focus,
                    user_feedback=feedback,
                )
                if err: st.error(err)
                else: st.session_state.insights=new_ins; st.rerun()

        if do_publish:
            with st.status(PUBLISH_STATUS_MSG, expanded=True):
                try:
                    pid = upload_to_notion(
                        game_name=game_name,
                        gallery_name=st.session_state.gallery_name,
                        subtype_id=subtype_id,
                        scrape_result=scrape_result,
                        insights=ins,
                        patch_timeline=patch_tl,
                    )
                    st.session_state.notion_page_id=pid; st.session_state.step=5; st.rerun()
                except Exception as e: st.error(PUBLISH_ERROR_TMPL.format(error=e))

    # ── Step 5: 완료 ──────────────────────────────────────────────────
    elif st.session_state.step == 5:
        st.balloons()
        _, cc, _ = st.columns([1,2,1])
        with cc:
            st.markdown("<div style='height:2rem;'></div>", unsafe_allow_html=True)
            st.success(NOTION_SUCCESS_MSG)
            pid   = st.session_state.notion_page_id
            p_url = f"https://notion.so/{pid.replace('-','')}"
            st.markdown(
                f"<a href='{p_url}' target='_blank'>"
                f"<div style='padding:20px;border-radius:12px;border:2px solid #3b4890;"
                f"text-align:center;font-size:1.1rem;font-weight:700;color:#3b4890;"
                f"margin:1rem 0;cursor:pointer;'>{NOTION_LINK_LABEL}</div></a>",
                unsafe_allow_html=True)


if __name__ == "__main__":
    main()