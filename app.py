import streamlit as st
import random, time, threading
from datetime import datetime
from config import APP_VERSION, ENV_NAME, TICKER_INTERVAL
from ui_texts import (
    APP_PAGE_TITLE, APP_PAGE_ICON, GLOBAL_CSS,
    SIDEBAR_TOOL_NAME, SIDEBAR_TOOL_CAPTION, SIDEBAR_STEP_TITLE,
    SIDEBAR_CURRENT_TARGET, SIDEBAR_VERSION_EXPANDER, SIDEBAR_VERSION_LABEL,
    SIDEBAR_HISTORY_TITLE, SIDEBAR_HISTORY, SIDEBAR_RESET_BTN, SIDEBAR_DAILY_AVG_TMPL,
    STEP_INFO, STEP_GUIDE_MESSAGES,
    STEP0_TITLE, STEP0_SUBTITLE, STEP0_INPUT_HEADER, STEP0_PLACEHOLDER,
    STEP0_CAPTION, STEP0_BTN, STEP0_WARN_EMPTY, STEP0_WARN_INVALID,
    DIAG_ERROR_LABEL, DIAG_SECTION_SUBTITLE, METRIC_DIAG_PERIOD, TOOLTIP_CHART, TOOLTIP_SUBTYPE,
    GALLERY_NAME_ANCHOR_ID, SUBTYPE_MODAL_BTN, SUBTYPE_MODAL_TITLE, SUBTYPE_MODAL_DESC,
    SUBTYPE_DEFINITIONS, SUBTYPE_CRITERIA_PREFIX, SUBTYPE_FOCUS_PREFIX,
    STEP1_GAME_CONFIRM_TITLE, STEP1_GAME_REASON_LABEL,
    STEP1_GAME_WRONG_HINT, COND_GAME_INPUT_LABEL, COND_GAME_PLACEHOLDER,
    STEP1_GAME_CHANGED_TMPL, STEP2_TITLE, STEP2_SUBTITLE,
    SCRAPE_ERROR_TMPL, AI_ERROR_TMPL, BTN_BACK,
    TICKER_MESSAGES, TAB_LABELS, PUBLISH_STATUS_MSG, PUBLISH_ERROR_TMPL,
    NOTION_SUCCESS_MSG, NOTION_LINK_LABEL, DIAG_CARDS
)
from dc_scraper import parse_dc_url, diagnose_gallery, run_dc_scraper
from gallery_analyzer import detect_subtype, get_subtype_info, guess_game_name
from ai_analyzer import diagnose_gallery_ai, analyze_gallery
from report_streamlit import (
    render_gallery_profile, render_tab_overview,
    render_tab_issues, render_tab_complaints, render_tab_raw, render_action_bar,
)
from report_notion import upload_to_notion

MAX_HISTORY = 10

def _auto_days(daily_avg):
    if daily_avg >= 200: return 7
    if daily_avg >= 50:  return 14
    return 30

st.set_page_config(page_title=APP_PAGE_TITLE, page_icon=APP_PAGE_ICON, layout="wide", initial_sidebar_state="expanded")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

def _init():
    for k, v in {
        "step": 0, "raw_url": "", "diag": None, "diag_ai": None,
        "subtype_id": None, "game_name": "", "gallery_id": None,
        "gallery_name": None, "auto_days": 14, "auto_focus": "default",
        "scrape_result": None, "insights": None, "notion_page_id": None,
        "history": [], "viewing_history": None,
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v

def _save_history():
    if not st.session_state.insights: return
    entry = {
        "game_name":     st.session_state.game_name,
        "date_range":    st.session_state.scrape_result.get("date_range_str",""),
        "saved_at":      datetime.now().strftime("%m/%d %H:%M"),
        "insights":      st.session_state.insights,
        "scrape_result": st.session_state.scrape_result,
        "subtype_id":    st.session_state.subtype_id,
    }
    hist = st.session_state.history
    hist = [h for h in hist if not (h["game_name"]==entry["game_name"] and h["date_range"]==entry["date_range"])]
    hist.insert(0, entry)
    st.session_state.history = hist[:MAX_HISTORY]

def _reset():
    history = st.session_state.history
    for k in list(st.session_state.keys()): del st.session_state[k]
    st.session_state.history = history
    st.session_state.viewing_history = None

def _sidebar():
    with st.sidebar:
        st.markdown(f"### {SIDEBAR_TOOL_NAME}")
        st.caption(f"{SIDEBAR_TOOL_CAPTION}  |  {APP_VERSION}")
        st.divider()
        cur = st.session_state.step
        st.markdown(f"**{SIDEBAR_STEP_TITLE}**")
        for i, (icon, label) in enumerate(STEP_INFO):
            if i < cur: st.markdown(f"<div class='step-done'>✔ {label}</div>", unsafe_allow_html=True)
            elif i == cur: st.markdown(f"<div class='step-cur'>{icon} {label}</div>", unsafe_allow_html=True)
            else: st.markdown(f"<div class='step-wait'>○ {label}</div>", unsafe_allow_html=True)
            if i < len(STEP_INFO)-1:
                c = "#1d7a3a" if i < cur else "#dee2e6"
                st.markdown(f"<div style='margin:2px 0 2px 20px;width:2px;height:12px;background:{c};'></div>", unsafe_allow_html=True)

        if cur >= 1 and st.session_state.gallery_name:
            st.divider()
            st.markdown(f"**{SIDEBAR_CURRENT_TARGET}**")
            st.markdown(f"🎮 **{st.session_state.game_name or st.session_state.gallery_name}**")
            if st.session_state.diag:
                st.caption(SIDEBAR_DAILY_AVG_TMPL.format(avg=st.session_state.diag["daily_avg"]))

        hist = st.session_state.get("history", [])
        if hist:
            st.divider()
            st.markdown("**📁 분석 기록**")
            for i, h in enumerate(hist):
                if st.button(f"{h['game_name']} ({h['saved_at']})", key=f"hist_{i}", use_container_width=True):
                    st.session_state.viewing_history = i
                    st.rerun()
        st.divider()
        with st.expander(SIDEBAR_VERSION_EXPANDER):
            ec = "#e74c3c" if ENV_NAME == "DEV" else "#2ecc71"
            st.markdown(f"<span style='background:{ec};color:#fff;padding:2px 8px;border-radius:6px;font-size:0.75rem;font-weight:700;'>{ENV_NAME}</span>", unsafe_allow_html=True)
            st.markdown(f"**{SIDEBAR_VERSION_LABEL}** {APP_VERSION}")
            for item in SIDEBAR_HISTORY: st.markdown(f"- {item}")

def _modal_content():
    st.markdown(SUBTYPE_MODAL_DESC); st.write("")
    for s in SUBTYPE_DEFINITIONS:
        with st.expander(f"{s['emoji']} **{s['label']}** — {s['desc']}", expanded=False):
            st.markdown(f"{SUBTYPE_CRITERIA_PREFIX} {s['criteria']}")
            st.markdown(f"{SUBTYPE_FOCUS_PREFIX} {s['focus']}")

_HAS_DIALOG = hasattr(st, "dialog")
if _HAS_DIALOG:
    @st.dialog(SUBTYPE_MODAL_TITLE, width="large")
    def _show_modal(): _modal_content()
else:
    def _show_modal():
        st.session_state["_show_modal"] = not st.session_state.get("_show_modal", False)
        st.rerun()

def _tip(text): return f"<span class='tt-wrap' style='color:#3b4890;cursor:help;font-size:0.82rem;'>ⓘ<span class='tt-box'>{text}</span></span>"

def _diag_card(idx):
    card = DIAG_CARDS[idx % len(DIAG_CARDS)]
    dots = "".join(f"<span class='toss-dot {'toss-dot-on' if i==idx%len(DIAG_CARDS) else ''}'>●</span>" for i in range(len(DIAG_CARDS)))
    st.markdown(
        f"<div class='toss-card'><div class='toss-card-emoji'>{card['emoji']}</div>"
        f"<div class='toss-card-label'>{card['label']}</div>"
        f"<div class='toss-card-desc'>{card['desc']}</div>"
        f"<div class='toss-card-dots'>{dots}</div></div>", unsafe_allow_html=True)

def _render_report(ins, scrape_result, game_name, subtype_id, is_history=False):
    render_gallery_profile(ins, scrape_result, game_name, subtype_id)
    tabs = st.tabs(TAB_LABELS)
    with tabs[0]: render_tab_overview(ins, scrape_result)
    with tabs[1]: render_tab_issues(ins)
    with tabs[2]: render_tab_complaints(ins)
    with tabs[3]: render_tab_raw(scrape_result)

    if not is_history:
        btn_new, do_publish = render_action_bar()

        if btn_new:
            _reset(); st.rerun()

        if do_publish:
            with st.status(PUBLISH_STATUS_MSG, expanded=True):
                try:
                    pid = upload_to_notion(game_name, st.session_state.gallery_name, subtype_id, scrape_result, ins)
                    st.session_state.notion_page_id=pid
                    _save_history()
                    st.session_state.step=4; st.rerun()
                except Exception as e: st.error(PUBLISH_ERROR_TMPL.format(error=e))
    else:
        st.write("")
        if st.button("← 현재 분석으로 돌아가기", use_container_width=True):
            st.session_state.viewing_history = None; st.rerun()

def main():
    _init()
    _sidebar()

    guide = STEP_GUIDE_MESSAGES.get(st.session_state.step, "")
    if guide and st.session_state.viewing_history is None:
        st.markdown(f"<div class='floating-guide'>💡 {guide}</div>", unsafe_allow_html=True)

    if not _HAS_DIALOG and st.session_state.get("_show_modal"):
        with st.expander(SUBTYPE_MODAL_TITLE, expanded=True):
            _modal_content()
            if st.button("✕ 닫기", key="modal_close"):
                st.session_state["_show_modal"] = False; st.rerun()

    if st.session_state.viewing_history is not None:
        idx = st.session_state.viewing_history
        hist = st.session_state.history
        if 0 <= idx < len(hist):
            h = hist[idx]
            st.info(f"📁 기록 열람 중 — {h['game_name']} ({h['date_range']}) | 저장: {h['saved_at']}")
            _render_report(h["insights"], h["scrape_result"], h["game_name"], h["subtype_id"], is_history=True)
        else: st.session_state.viewing_history = None; st.rerun()
        return

    if st.session_state.step == 0:
        _, col, _ = st.columns([1,3,1])
        with col:
            st.markdown("<div style='height:2rem;'></div>", unsafe_allow_html=True)
            st.markdown(f"<h1 class='toss-h1'>{STEP0_TITLE}</h1>", unsafe_allow_html=True)
            st.markdown(f"<p class='toss-sub'>{STEP0_SUBTITLE}</p>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown(f"#### {STEP0_INPUT_HEADER}")
                raw_url = st.text_input("URL", placeholder=STEP0_PLACEHOLDER, label_visibility="collapsed")
                st.caption(STEP0_CAPTION); st.write("")
                if st.button(STEP0_BTN, type="primary", use_container_width=True):
                    if not raw_url.strip(): st.warning(STEP0_WARN_EMPTY); return
                    _, gal_id = parse_dc_url(raw_url)
                    if not gal_id: st.warning(STEP0_WARN_INVALID); return
                    st.session_state.raw_url = raw_url

                    card_slot = st.empty(); prog_slot = st.empty(); msg_slot = st.empty()
                    card_idx = [0]
                    def show_card():
                        with card_slot.container(): _diag_card(card_idx[0])
                        card_idx[0] += 1
                    show_card(); prog = prog_slot.progress(0)
                    stop_ev = threading.Event()
                    def _card_loop():
                        while not stop_ev.is_set():
                            time.sleep(2.5)
                            if not stop_ev.is_set(): show_card()
                    threading.Thread(target=_card_loop, daemon=True).start()

                    def _cb(msg, val):
                        prog.progress(int(val))
                        msg_slot.markdown(f"<div class='diag-msg'>🔍 {msg}</div>", unsafe_allow_html=True)

                    diag = diagnose_gallery(raw_url, progress_cb=_cb)
                    stop_ev.set()
                    if diag.get("error"):
                        card_slot.empty(); prog_slot.empty(); msg_slot.empty()
                        st.error(diag["error"]); return

                    prog.progress(90)
                    msg_slot.markdown("<div class='diag-msg'>🤖 AI가 갤러리 특성 파악 중...</div>", unsafe_allow_html=True)
                    st.session_state.update({
                        "diag": diag, "subtype_id": detect_subtype(diag),
                        "game_name":  guess_game_name(diag["gallery_name"], diag["top_title_words"]),
                        "gallery_id": diag["gallery_id"], "gallery_name": diag["gallery_name"],
                        "auto_days": _auto_days(diag["daily_avg"]),
                    })
                    ai_result, ai_err = diagnose_gallery_ai(
                        diag["gallery_name"], diag["top_title_words"], st.session_state.subtype_id, diag["daily_avg"]
                    )
                    if not ai_err and ai_result:
                        st.session_state.diag_ai = ai_result
                        st.session_state.game_name = ai_result.get("topic_guess", st.session_state.game_name)
                    prog.progress(100); card_slot.empty(); prog_slot.empty(); msg_slot.empty()
                    st.session_state.step = 1; st.rerun()

    elif st.session_state.step == 1:
        diag = st.session_state.diag
        ai = st.session_state.diag_ai or {}
        subtype = get_subtype_info(st.session_state.subtype_id)

        st.markdown("## ✅ 게임 확인")
        st.markdown(f"<p style='color:#6c757d;margin-top:-0.5rem;margin-bottom:1.5rem;'>{DIAG_SECTION_SUBTITLE}</p>", unsafe_allow_html=True)

        with st.container(border=True):
            st.markdown("#### 📅 진단 기간")
            st.markdown(
                f"<div style='font-size:1rem;font-weight:700;color:#1e2129;'>"
                f"{diag.get('diag_start','')} ~ {diag.get('diag_end','')}</div>"
                f"<div style='font-size:0.82rem;color:#6c757d;margin-top:4px;'>"
                f"일평균 {diag['daily_avg']}개 · 자동 분석 기간: {st.session_state.auto_days}일</div>",
                unsafe_allow_html=True)
        st.write("")

        with st.container(border=True):
            st.markdown("#### 🏷️ 갤러리 유형")
            sc = subtype["color"]
            col_b, col_btn = st.columns([3,1])
            with col_b:
                st.markdown(
                    f"<div style='display:inline-flex;align-items:center;gap:10px;"
                    f"padding:10px 14px;border-radius:10px;border:1.5px solid {sc};background:{sc}0d;'>"
                    f"<span style='font-size:1.3rem;'>{subtype['emoji']}</span>"
                    f"<div><b style='color:{sc};font-size:1rem;'>{subtype['label']}</b>"
                    f"<div style='font-size:0.82rem;color:#6c757d;'>{subtype['desc']}</div></div>"
                    f"{_tip(TOOLTIP_SUBTYPE)}</div>", unsafe_allow_html=True)
            with col_btn:
                if st.button(SUBTYPE_MODAL_BTN, use_container_width=True): _show_modal()
        st.write("")

        with st.container(border=True):
            st.markdown("#### 🤖 AI가 진단한 갤러리 주제")
            game_name_display = ai.get("topic_guess", st.session_state.game_name)
            topic_reason      = ai.get("topic_reason", "")
            st.markdown(
                f"<div style='font-size:2rem;font-weight:800;color:#1e2129;margin-bottom:6px;'>{game_name_display}</div>"
                f"<div style='font-size:0.82rem;color:#6c757d;margin-bottom:10px;'>{STEP1_GAME_REASON_LABEL} {topic_reason}</div>"
                f"<div style='font-size:0.82rem;color:#e74c3c;font-weight:600;'>{STEP1_GAME_WRONG_HINT}</div>",
                unsafe_allow_html=True)
            st.markdown(f"<div id='{GALLERY_NAME_ANCHOR_ID}'></div>", unsafe_allow_html=True)
            
            inp = st.text_input(
                COND_GAME_INPUT_LABEL,
                value=game_name_display,
                placeholder=COND_GAME_PLACEHOLDER,
                label_visibility="collapsed"
            )
            current_game = inp.strip() or game_name_display
            st.info(STEP1_GAME_CHANGED_TMPL.format(game_name=current_game))

            if ai.get("warning"): st.warning(f"⚠️ 참고: {ai['warning']}")

        st.write("")
        if st.button("🚀  분석 시작", type="primary", use_container_width=True):
            st.session_state.game_name  = current_game
            st.session_state.auto_focus = ai.get("suggested_focus", "default")
            if isinstance(st.session_state.auto_focus, list):
                st.session_state.auto_focus = st.session_state.auto_focus[0]
            st.session_state.step = 2; st.rerun()

    elif st.session_state.step == 2:
        raw_url = st.session_state.raw_url
        analysis_days = st.session_state.auto_days
        gallery_id = st.session_state.gallery_id
        game_name = st.session_state.game_name
        subtype_id = st.session_state.subtype_id
        analysis_focus = st.session_state.auto_focus

        st.markdown(STEP2_TITLE)
        st.markdown(f"<p style='color:#6c757d;'>{STEP2_SUBTITLE}</p>", unsafe_allow_html=True)
        st.info(f"📅 분석 기간: 최근 **{analysis_days}일** · 댓글 상위 핵심 게시글 본문 수집")

        phase = st.empty(); pbar = st.progress(0); ticker_slot = st.empty()
        def show_phase(title, pct, is_ai=False):
            cls = "phase-card phase-card-ai" if is_ai else "phase-card"
            phase.markdown(f"<div class='{cls}'><div class='phase-title'>{title}</div></div>", unsafe_allow_html=True)
            pbar.progress(int(pct))
        show_phase("🔍 갤러리 접속 중...", 2)

        ticker_running = threading.Event(); ticker_running.set()
        def _ticker_loop():
            while ticker_running.is_set():
                ticker_slot.info(f"🌾 {random.choice(TICKER_MESSAGES)}")
                time.sleep(TICKER_INTERVAL)
        threading.Thread(target=_ticker_loop, daemon=True).start()
        def scb(msg, val): show_phase(f"🌾 {msg}", val)

        try:
            scrape_result = run_dc_scraper(raw_url, days_limit=analysis_days, progress_cb=scb)
        except Exception as e:
            ticker_running.clear(); ticker_slot.empty(); phase.empty(); pbar.empty()
            st.error(SCRAPE_ERROR_TMPL.format(error=e))
            if st.button(BTN_BACK): st.session_state.step=1; st.rerun()
            return

        ticker_running.clear(); ticker_slot.empty()
        tot = scrape_result["total_posts"]; ana = scrape_result["analysis_count"]
        show_phase(f"✅ 수집 완료 — 전체 {tot}개 · 분석 표본 {ana}개", 100)

        ai_phase = st.empty(); ai_pbar = st.progress(0); ai_log = st.empty()
        ai_phase.markdown("<div class='phase-card phase-card-ai'><div class='phase-title'>🧠 AI 민심 분석 시작...</div></div>", unsafe_allow_html=True)

        res_box = [None, None]; ev = threading.Event()
        def run_ai():
            try:
                res_box[0], res_box[1] = analyze_gallery(
                    gallery_id=gallery_id, game_name=game_name, subtype_id=subtype_id,
                    analysis_data=scrape_result["analysis_data"],
                    all_metas=scrape_result["all_metas"],
                    analysis_days=analysis_days
                )
            except Exception as ex: res_box[1] = str(ex)
            finally: ev.set()
        threading.Thread(target=run_ai, daemon=True).start()

        tick = 0
        while not ev.is_set():
            ai_pbar.progress(min(95, 10+tick*3))
            ai_log.info(f"💡 {random.choice(TICKER_MESSAGES)}")
            time.sleep(TICKER_INTERVAL); tick += 1
        ai_pbar.progress(100); ai_log.empty()

        if res_box[1]:
            ai_phase.empty(); ai_pbar.empty()
            st.error(AI_ERROR_TMPL.format(error=res_box[1]))
            if st.button(BTN_BACK): st.session_state.step=1; st.rerun()
            return

        ai_phase.markdown("<div class='phase-card phase-card-ai'><div class='phase-title'>✅ AI 분석 완료</div></div>", unsafe_allow_html=True)
        st.session_state.scrape_result = scrape_result
        st.session_state.insights      = res_box[0]
        _save_history()
        st.session_state.step = 3
        time.sleep(0.6); st.rerun()

    elif st.session_state.step == 3:
        _render_report(st.session_state.insights, st.session_state.scrape_result, st.session_state.game_name, st.session_state.subtype_id, is_history=False)

    elif st.session_state.step == 4:
        st.balloons()
        _, cc, _ = st.columns([1,2,1])
        with cc:
            st.markdown("<div style='height:2rem;'></div>", unsafe_allow_html=True)
            st.success(NOTION_SUCCESS_MSG)
            pid = st.session_state.notion_page_id
            p_url = f"https://notion.so/{pid.replace('-','')}"
            st.markdown(
                f"<a href='{p_url}' target='_blank'><div style='padding:20px;border-radius:12px;border:2px solid #3b4890;"
                f"text-align:center;font-size:1.1rem;font-weight:700;color:#3b4890;margin:1rem 0;cursor:pointer;'>"
                f"{NOTION_LINK_LABEL}</div></a>", unsafe_allow_html=True)
            st.write("")
            if st.button("🔄 다른 게임 분석하기", use_container_width=True):
                _reset(); st.rerun()

if __name__ == "__main__": main()