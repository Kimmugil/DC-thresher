"""
app.py v5 — 토스 스타일 UX 전면 개편

[변경]
- Step 0: 갤러리 진단 중 토스식 슬라이딩 카드 (분석 방식 설명)
- Step 1: 게임 확인 — 깔끔한 확인 카드
- Step 2: 수집&분석 — 토글 없이 단계별 진행 상황 실시간 표시
- 리포트: 이탈 위험 탭 제거, 유저 세그먼트 탭 제거, 패치 타임라인 제거
"""

import streamlit as st
import random, time, threading
from datetime import datetime

from config import APP_VERSION, ENV_NAME, TICKER_INTERVAL
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
    METRIC_GALLERY_NAME, METRIC_DIAG_PERIOD,
    TOOLTIP_CHART, GALLERY_NAME_TOOLTIP, GALLERY_NAME_EDIT_HINT,
    GALLERY_NAME_ANCHOR_ID, TOOLTIP_SUBTYPE,
    SUBTYPE_MODAL_BTN, SUBTYPE_MODAL_TITLE, SUBTYPE_MODAL_DESC,
    SUBTYPE_DEFINITIONS, SUBTYPE_CRITERIA_PREFIX, SUBTYPE_FOCUS_PREFIX,
    STEP1_GAME_CONFIRM_TITLE, STEP1_GAME_CONFIRM_DESC,
    STEP1_GAME_REASON_LABEL, STEP1_GAME_WRONG_HINT,
    COND_GAME_INPUT_LABEL, COND_GAME_PLACEHOLDER,
    STEP2_TITLE, STEP2_SUBTITLE,
    SCRAPE_STATUS_MSG, AI_STATUS_MSG, PATCH_STATUS_MSG,
    SCRAPE_DONE_TMPL, SCRAPE_ERROR_TMPL, AI_ERROR_TMPL,
    BTN_BACK, TICKER_MESSAGES, TAB_LABELS,
    REANALYZE_STATUS_MSG, PUBLISH_STATUS_MSG, PUBLISH_ERROR_TMPL,
    NOTION_SUCCESS_MSG, NOTION_LINK_LABEL,
    TAB_STYLE_CSS, TOOLTIP_CSS, GLOBAL_CSS,
    CHART_HOVER_TMPL,
    DIAG_CARDS,
    sanitize_for_display,
)
from dc_scraper import parse_dc_url, diagnose_gallery, run_dc_scraper
from gallery_analyzer import detect_subtype, get_subtype_info, detect_spike_dates, guess_game_name
from ai_analyzer import diagnose_gallery_ai, analyze_gallery
from report_streamlit import (
    render_gallery_profile,
    render_tab_summary, render_tab_timeline,
    render_tab_complaints,
    render_tab_trend,
    render_tab_raw, render_action_bar,
)
from report_notion import upload_to_notion


def _auto_days(daily_avg: float) -> int:
    if daily_avg >= 200: return 7
    if daily_avg >= 50:  return 14
    return 30


st.set_page_config(page_title=APP_PAGE_TITLE, page_icon=APP_PAGE_ICON,
                   layout="wide", initial_sidebar_state="expanded")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
st.markdown(TAB_STYLE_CSS, unsafe_allow_html=True)
st.markdown(TOOLTIP_CSS, unsafe_allow_html=True)


def _init():
    defs = {
        "step": 0, "raw_url": "", "diag": None, "diag_ai": None,
        "subtype_id": None, "game_name": "", "gallery_id": None,
        "gallery_name": None, "auto_days": 14, "auto_focus": "default",
        "scrape_result": None, "insights": None, "notion_page_id": None,
        "_card_idx": 0, "_card_ts": 0.0,
    }
    for k, v in defs.items():
        if k not in st.session_state: st.session_state[k] = v


def _sidebar():
    with st.sidebar:
        st.markdown(f"### {SIDEBAR_TOOL_NAME}")
        st.caption(f"{SIDEBAR_TOOL_CAPTION}  |  {APP_VERSION}")
        st.divider()
        cur = st.session_state.step
        st.markdown(f"**{SIDEBAR_STEP_TITLE}**")
        for i, (icon, label) in enumerate(STEP_INFO):
            if i < cur:
                st.markdown(f"<div class='step-done'>✔ {label}</div>", unsafe_allow_html=True)
            elif i == cur:
                st.markdown(f"<div class='step-cur'>{icon} {label}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='step-wait'>○ {label}</div>", unsafe_allow_html=True)
            if i < len(STEP_INFO)-1:
                c = "#1d7a3a" if i < cur else "#dee2e6"
                st.markdown(f"<div style='margin:2px 0 2px 20px;width:2px;height:12px;background:{c};'></div>", unsafe_allow_html=True)

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
    return f"<span class='tt-wrap' style='color:#3b4890;cursor:help;'>ⓘ<span class='{cls}'>{text}</span></span>"


def _render_diag_card(idx: int):
    """토스 스타일 분석 방식 설명 카드"""
    cards = DIAG_CARDS
    card  = cards[idx % len(cards)]
    st.markdown(f"""
    <div class='toss-card'>
      <div class='toss-card-emoji'>{card['emoji']}</div>
      <div class='toss-card-label'>{card['label']}</div>
      <div class='toss-card-desc'>{card['desc']}</div>
      <div class='toss-card-dots'>{''.join(
        f"<span class='toss-dot {'toss-dot-on' if i==idx%len(cards) else ''}'>●</span>"
        for i in range(len(cards))
      )}</div>
    </div>
    """, unsafe_allow_html=True)


def main():
    _init()
    _sidebar()

    guide = STEP_GUIDE_MESSAGES.get(st.session_state.step, "")
    if guide:
        st.markdown(f"<div class='floating-guide'>💡 {guide}</div>", unsafe_allow_html=True)

    if not _HAS_DIALOG and st.session_state.get("_show_modal"):
        with st.expander(SUBTYPE_MODAL_TITLE, expanded=True):
            _subtype_modal_content()
            if st.button("✕ 닫기", key="modal_close"):
                st.session_state["_show_modal"] = False; st.rerun()

    # ── Step 0: URL 입력 + 진단 ──────────────────────────────────
    if st.session_state.step == 0:
        _, col, _ = st.columns([1, 3, 1])
        with col:
            st.markdown("<div style='height:2rem;'></div>", unsafe_allow_html=True)
            st.markdown(f"<h1 class='toss-h1'>{STEP0_TITLE}</h1>", unsafe_allow_html=True)
            st.markdown(f"<p class='toss-sub'>{STEP0_SUBTITLE}</p>", unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown(f"#### {STEP0_INPUT_HEADER}")
                raw_url = st.text_input("URL", placeholder=STEP0_PLACEHOLDER, label_visibility="collapsed")
                st.caption(STEP0_CAPTION)
                st.write("")

                if st.button(STEP0_BTN, type="primary", use_container_width=True):
                    if not raw_url.strip(): st.warning(STEP0_WARN_EMPTY); return
                    _, gal_id = parse_dc_url(raw_url)
                    if not gal_id: st.warning(STEP0_WARN_INVALID); return

                    st.session_state.raw_url = raw_url

                    # 카드 영역
                    card_slot = st.empty()
                    prog_slot = st.empty()
                    msg_slot  = st.empty()

                    card_idx = 0
                    def show_card():
                        nonlocal card_idx
                        with card_slot.container():
                            _render_diag_card(card_idx)
                        card_idx = (card_idx + 1) % len(DIAG_CARDS)

                    show_card()
                    prog = prog_slot.progress(0)

                    def _cb(msg, val):
                        prog.progress(int(val))
                        msg_slot.markdown(f"<div class='diag-msg'>🔍 {msg}</div>", unsafe_allow_html=True)

                    # 카드 자동 전환 스레드
                    stop_card = threading.Event()
                    def _card_runner():
                        while not stop_card.is_set():
                            time.sleep(2.5)
                            if not stop_card.is_set():
                                show_card()
                    ct = threading.Thread(target=_card_runner, daemon=True)
                    ct.start()

                    diag = diagnose_gallery(raw_url, progress_cb=_cb)
                    stop_card.set()

                    if diag.get("error"):
                        card_slot.empty(); prog_slot.empty(); msg_slot.empty()
                        st.error(diag["error"]); return

                    prog.progress(90)
                    msg_slot.markdown("<div class='diag-msg'>🤖 AI가 갤러리 특성 파악 중...</div>", unsafe_allow_html=True)

                    st.session_state.diag         = diag
                    st.session_state.subtype_id   = detect_subtype(diag)
                    st.session_state.game_name    = guess_game_name(diag["gallery_name"], diag["top_title_words"])
                    st.session_state.gallery_id   = diag["gallery_id"]
                    st.session_state.gallery_name = diag["gallery_name"]
                    st.session_state.auto_days    = _auto_days(diag["daily_avg"])

                    ai_result, ai_err = diagnose_gallery_ai(
                        gallery_name=diag["gallery_name"],
                        top_words=diag["top_title_words"],
                        subtype_id=st.session_state.subtype_id,
                        daily_avg=diag["daily_avg"],
                    )
                    if not ai_err and ai_result:
                        st.session_state.diag_ai  = ai_result
                        st.session_state.game_name = ai_result.get("topic_guess", st.session_state.game_name)

                    prog.progress(100)
                    card_slot.empty(); prog_slot.empty(); msg_slot.empty()
                    st.session_state.step = 1
                    st.rerun()

    # ── Step 1: 게임 확인 ────────────────────────────────────────
    elif st.session_state.step == 1:
        diag    = st.session_state.diag
        ai      = st.session_state.diag_ai or {}
        subtype = get_subtype_info(st.session_state.subtype_id)

        st.markdown(DIAG_SECTION_TITLE)
        st.markdown(f"<p class='toss-sub'>{DIAG_SECTION_SUBTITLE}</p>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                f"<div class='info-card'>"
                f"<div class='info-card-label'>{METRIC_GALLERY_NAME} {_tip(GALLERY_NAME_TOOLTIP, wide=True)}</div>"
                f"<div class='info-card-val'>{diag['gallery_name']}</div>"
                f"<div class='info-card-hint'>{GALLERY_NAME_EDIT_HINT}</div>"
                f"</div>", unsafe_allow_html=True)
        with c2:
            st.markdown(
                f"<div class='info-card'>"
                f"<div class='info-card-label'>{METRIC_DIAG_PERIOD} {_tip(TOOLTIP_CHART)}</div>"
                f"<div class='info-card-val' style='font-size:0.95rem;'>{diag.get('diag_start','')} ~ {diag.get('diag_end','')}</div>"
                f"<div class='info-card-hint'>일평균 {diag['daily_avg']}개 · 자동 분석 기간: {st.session_state.auto_days}일</div>"
                f"</div>", unsafe_allow_html=True)

        st.write("")
        sc = subtype["color"]
        col_b, col_btn = st.columns([3, 1])
        with col_b:
            st.markdown(
                f"<div class='subtype-badge' style='border-color:{sc};background:{sc}0d;'>"
                f"<span style='font-size:1.2rem;'>{subtype['emoji']}</span>"
                f"<div><b style='color:{sc};'>{subtype['label']}</b>"
                f"<div style='font-size:0.8rem;color:#6c757d;'>{subtype['desc']}</div></div>"
                f"{_tip(TOOLTIP_SUBTYPE)}</div>", unsafe_allow_html=True)
        with col_btn:
            if st.button(SUBTYPE_MODAL_BTN, use_container_width=True): _show_subtype_modal()

        st.divider()

        # 게임명 확인 카드 (토스 스타일)
        game_name_display = ai.get("topic_guess", st.session_state.game_name)
        topic_reason      = ai.get("topic_reason", "")

        st.markdown(
            f"<div class='game-confirm-card'>"
            f"<div class='game-confirm-label'>{STEP1_GAME_CONFIRM_TITLE}</div>"
            f"<div class='game-confirm-name'>{game_name_display}</div>"
            f"<div class='game-confirm-reason'>{STEP1_GAME_REASON_LABEL} {topic_reason}</div>"
            f"<div class='game-confirm-hint'>{STEP1_GAME_WRONG_HINT}</div>"
            f"</div>", unsafe_allow_html=True)

        st.markdown(f"<div id='{GALLERY_NAME_ANCHOR_ID}'></div>", unsafe_allow_html=True)
        game_name_input = st.text_input(
            COND_GAME_INPUT_LABEL,
            value=game_name_display,
            placeholder=COND_GAME_PLACEHOLDER,
            label_visibility="collapsed")

        if ai.get("warning"):
            st.warning(f"⚠️ 참고: {ai['warning']}")

        st.write("")
        if st.button("🚀  분석 시작", type="primary", use_container_width=True):
            st.session_state.game_name  = game_name_input.strip() or game_name_display
            st.session_state.auto_focus = ai.get("suggested_focus", "default")
            if isinstance(st.session_state.auto_focus, list):
                st.session_state.auto_focus = st.session_state.auto_focus[0]
            st.session_state.step = 2
            st.rerun()

    # ── Step 2: 수집 & AI 분석 (토글 없이 실시간 표시) ──────────
    elif st.session_state.step == 2:
        raw_url        = st.session_state.raw_url
        analysis_days  = st.session_state.auto_days
        gallery_id     = st.session_state.gallery_id
        game_name      = st.session_state.game_name
        subtype_id     = st.session_state.subtype_id
        analysis_focus = st.session_state.auto_focus

        st.markdown(STEP2_TITLE)
        st.markdown(f"<p class='toss-sub'>{STEP2_SUBTITLE}</p>", unsafe_allow_html=True)
        st.info(f"📅 분석 기간: 최근 **{analysis_days}일** · 고관여 게시글 위주 자동 수집")

        # ── 수집 단계: 상태를 카드로 실시간 표시 ────────────────
        phase_slot = st.empty()   # 현재 단계 표시
        pbar       = st.progress(0)
        log_slot   = st.empty()   # 세부 로그

        def _phase(title, pct):
            phase_slot.markdown(
                f"<div class='phase-card'>"
                f"<div class='phase-title'>{title}</div>"
                f"</div>", unsafe_allow_html=True)
            pbar.progress(int(pct))

        def scb(msg, val):
            _phase(f"🌾 {msg}", val)
            log_slot.caption(msg)

        _phase("🔍 갤러리 접속 중...", 2)
        try:
            scrape_result = run_dc_scraper(raw_url, days_limit=analysis_days, progress_cb=scb)
        except Exception as e:
            phase_slot.empty(); pbar.empty(); log_slot.empty()
            st.error(SCRAPE_ERROR_TMPL.format(error=e))
            if st.button(BTN_BACK): st.session_state.step=1; st.rerun()
            return

        tot = scrape_result["total_posts"]
        ana = scrape_result["analysis_count"]
        method = scrape_result.get("analysis_method", "high_engagement")
        method_label = "개념글 위주" if method == "concept" else "고관여 게시글 위주 (댓글 상위 20%)"
        _phase(f"✅ 수집 완료 — 전체 {tot}개 · 분석 표본 {ana}개 ({method_label})", 100)
        log_slot.empty()

        # ── AI 분석 단계 ─────────────────────────────────────────
        ai_phase = st.empty()
        ai_pbar  = st.progress(0)
        ai_log   = st.empty()

        ai_phase.markdown(
            f"<div class='phase-card phase-ai'>"
            f"<div class='phase-title'>🧠 AI 민심 분석 시작...</div>"
            f"</div>", unsafe_allow_html=True)

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

        tick = 0
        while not ev.is_set():
            pct = min(95, 10 + tick * 3)
            ai_pbar.progress(pct)
            ai_log.info(f"💡 {random.choice(TICKER_MESSAGES)}")
            time.sleep(TICKER_INTERVAL)
            tick += 1
        ai_pbar.progress(100)
        ai_log.empty()

        if res_box[1]:
            ai_phase.empty(); ai_pbar.empty()
            st.error(AI_ERROR_TMPL.format(error=res_box[1]))
            if st.button(BTN_BACK): st.session_state.step=1; st.rerun()
            return

        ai_phase.markdown(
            f"<div class='phase-card phase-ai'>"
            f"<div class='phase-title'>✅ AI 분석 완료</div>"
            f"</div>", unsafe_allow_html=True)

        st.session_state.scrape_result  = scrape_result
        st.session_state.insights       = res_box[0]
        st.session_state.step = 3
        time.sleep(0.8)
        st.rerun()

    # ── Step 3: 리포트 ────────────────────────────────────────────
    elif st.session_state.step == 3:
        ins           = st.session_state.insights
        scrape_result = st.session_state.scrape_result
        game_name     = st.session_state.game_name
        subtype_id    = st.session_state.subtype_id

        render_gallery_profile(ins, scrape_result, game_name, subtype_id)

        # 탭: 유저세그먼트 제거, 이탈위험 제거
        tabs = st.tabs(TAB_LABELS)
        with tabs[0]: render_tab_summary(ins, scrape_result.get("analysis_data",[]))
        with tabs[1]: render_tab_timeline(ins, scrape_result)
        with tabs[2]: render_tab_complaints(ins)
        with tabs[3]: render_tab_trend(ins)
        with tabs[4]: render_tab_raw(scrape_result)

        feedback, do_reanalyze, do_publish = render_action_bar()

        if do_reanalyze:
            with st.status(REANALYZE_STATUS_MSG, expanded=True):
                new_ins, err = analyze_gallery(
                    gallery_id=st.session_state.gallery_id,
                    game_name=game_name, subtype_id=subtype_id,
                    analysis_data=scrape_result["analysis_data"],
                    all_metas=scrape_result["all_metas"],
                    analysis_days=st.session_state.auto_days,
                    analysis_focus=st.session_state.auto_focus,
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
                        patch_timeline="",
                    )
                    st.session_state.notion_page_id=pid; st.session_state.step=4; st.rerun()
                except Exception as e: st.error(PUBLISH_ERROR_TMPL.format(error=e))

    # ── Step 4: 완료 ──────────────────────────────────────────────
    elif st.session_state.step == 4:
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