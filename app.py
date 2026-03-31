"""
app.py v10
- 사이드바: 진행단계·현재대상·분석기록 상시 고정 표시
  (펼치고 닫는 토글 없이 항상 보임, 환경/버전정보만 expander 유지)
- Step1: 진단기간 + 갤러리유형 → 2열 나란히 배치 (스크롤 단축)
- Step0: 이미지 200px, 담백한 문구 적용
- 전체: 사이드바 collapsed 버튼 숨김 CSS 유지
"""
import streamlit as st
import random, time, threading
from datetime import datetime
from pathlib import Path
from config import APP_VERSION, ENV_NAME, TICKER_INTERVAL
from ui_texts import (
    APP_PAGE_TITLE, APP_PAGE_ICON, GLOBAL_CSS,
    SIDEBAR_TOOL_NAME, SIDEBAR_TOOL_CAPTION, SIDEBAR_STEP_TITLE,
    SIDEBAR_CURRENT_TARGET, SIDEBAR_VERSION_EXPANDER, SIDEBAR_VERSION_LABEL,
    SIDEBAR_HISTORY, SIDEBAR_DAILY_AVG_TMPL,
    STEP_INFO, STEP_GUIDE_MESSAGES,
    STEP0_TITLE, STEP0_SUBTITLE, STEP0_INPUT_HEADER, STEP0_PLACEHOLDER,
    STEP0_CAPTION, STEP0_BTN, STEP0_WARN_EMPTY, STEP0_WARN_INVALID,
    STEP0_NOTICE_TITLE, STEP0_NOTICE_ITEMS,
    DIAG_ERROR_LABEL, DIAG_SECTION_SUBTITLE,
    TOOLTIP_SUBTYPE, GALLERY_NAME_ANCHOR_ID,
    SUBTYPE_MODAL_BTN, SUBTYPE_MODAL_TITLE,
    DIAG_PERIOD_CRITERIA,
    STEP1_GAME_REASON_LABEL, STEP1_GAME_WRONG_HINT,
    COND_GAME_INPUT_LABEL, COND_GAME_PLACEHOLDER, STEP1_START_BTN,
    STEP2_TITLE, STEP2_SUBTITLE, STEP2_INFO_TMPL,
    SCRAPE_ERROR_TMPL, AI_ERROR_TMPL, BTN_BACK,
    TICKER_MESSAGES, TAB_LABELS,
    PUBLISH_STATUS_MSG, PUBLISH_ERROR_TMPL,
    NOTION_SUCCESS_MSG, NOTION_LINK_LABEL, STEP4_RESET_BTN,
    HISTORY_BACK_BTN, HISTORY_VIEW_LABEL,
    DIAG_CARDS,
)
from dc_scraper import parse_dc_url, diagnose_gallery, run_dc_scraper
from gallery_analyzer import detect_subtype, get_subtype_info, guess_game_name
from ai_analyzer import diagnose_gallery_ai, analyze_gallery
from report_streamlit import (
    render_gallery_profile, render_tab_overview,
    render_tab_issues, render_tab_complaints, render_tab_raw,
    render_action_bar, render_subtype_modal_content,
)
from report_notion import upload_to_notion

MAX_HISTORY = 10


def _auto_days(daily_avg):
    if daily_avg >= 200: return 7
    if daily_avg >= 50:  return 14
    return 30


st.set_page_config(
    page_title=APP_PAGE_TITLE, page_icon=APP_PAGE_ICON,
    layout="wide", initial_sidebar_state="expanded",
)
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ── 세션 초기화 ───────────────────────────────────────────────────
def _init():
    defaults = {
        "step": 0, "raw_url": "", "diag": None, "diag_ai": None,
        "subtype_id": None, "game_name": "", "gallery_id": None,
        "gallery_name": None, "auto_days": 14, "auto_focus": "default",
        "scrape_result": None, "insights": None, "notion_page_id": None,
        "history": [], "viewing_history": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _save_history():
    if not st.session_state.insights: return
    entry = {
        "game_name":     st.session_state.game_name,
        "date_range":    st.session_state.scrape_result.get("date_range_str", ""),
        "saved_at":      datetime.now().strftime("%m/%d %H:%M"),
        "insights":      st.session_state.insights,
        "scrape_result": st.session_state.scrape_result,
        "subtype_id":    st.session_state.subtype_id,
    }
    hist = st.session_state.history
    hist = [h for h in hist if not (
        h["game_name"] == entry["game_name"] and h["date_range"] == entry["date_range"]
    )]
    hist.insert(0, entry)
    st.session_state.history = hist[:MAX_HISTORY]


def _reset():
    history = st.session_state.history
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    st.session_state.history         = history
    st.session_state.viewing_history = None


# ── 사이드바 ─────────────────────────────────────────────────────
def _sidebar():
    with st.sidebar:
        st.markdown(f"### {SIDEBAR_TOOL_NAME}")
        st.caption(f"{SIDEBAR_TOOL_CAPTION}  |  {APP_VERSION}")
        st.divider()

        # 진행 단계 — 항상 표시
        cur = st.session_state.step
        st.markdown(f"**{SIDEBAR_STEP_TITLE}**")
        for i, (icon, label) in enumerate(STEP_INFO):
            if i < cur:
                st.markdown(f"<div class='step-done'>✔ {label}</div>", unsafe_allow_html=True)
            elif i == cur:
                st.markdown(f"<div class='step-cur'>{icon} {label}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='step-wait'>○ {label}</div>", unsafe_allow_html=True)
            if i < len(STEP_INFO) - 1:
                c = "#1d7a3a" if i < cur else "#dee2e6"
                st.markdown(
                    f"<div style='margin:2px 0 2px 20px;width:2px;height:12px;background:{c};'></div>",
                    unsafe_allow_html=True,
                )

        # 현재 분석 대상 — 항상 표시 (값이 있을 때만)
        if st.session_state.game_name:
            st.divider()
            st.markdown(f"**{SIDEBAR_CURRENT_TARGET}**")
            st.markdown(f"🎮 **{st.session_state.game_name}**")
            if st.session_state.diag:
                st.caption(SIDEBAR_DAILY_AVG_TMPL.format(avg=st.session_state.diag["daily_avg"]))

        # 분석 기록 — 항상 표시 (기록이 있을 때만)
        hist = st.session_state.get("history", [])
        if hist:
            st.divider()
            st.markdown("**📁 분석 기록**")
            for i, h in enumerate(hist):
                if st.button(
                    f"{h['game_name']} ({h['saved_at']})",
                    key=f"hist_{i}",
                    use_container_width=True,
                ):
                    st.session_state.viewing_history = i
                    st.rerun()

        # 버전/환경 — expander 유지
        st.divider()
        with st.expander(SIDEBAR_VERSION_EXPANDER):
            ec = "#e74c3c" if ENV_NAME == "DEV" else "#2ecc71"
            st.markdown(
                f"<span style='background:{ec};color:#fff;padding:2px 8px;"
                f"border-radius:6px;font-size:0.75rem;font-weight:700;'>{ENV_NAME}</span>",
                unsafe_allow_html=True,
            )
            st.markdown(f"**{SIDEBAR_VERSION_LABEL}** {APP_VERSION}")
            for item in SIDEBAR_HISTORY:
                st.markdown(f"- {item}")


# ── 갤러리 유형 모달 ─────────────────────────────────────────────
_HAS_DIALOG = hasattr(st, "dialog")
if _HAS_DIALOG:
    @st.dialog(SUBTYPE_MODAL_TITLE, width="large")
    def _show_modal():
        render_subtype_modal_content()
else:
    def _show_modal():
        st.session_state["_show_modal"] = not st.session_state.get("_show_modal", False)
        st.rerun()


# ── 헬퍼 ─────────────────────────────────────────────────────────
def _tip(text):
    return (
        f"<span class='tt-wrap' style='color:#3b4890;cursor:help;font-size:0.82rem;'>"
        f"ⓘ<span class='tt-box'>{text}</span></span>"
    )


def _diag_card(idx):
    card = DIAG_CARDS[idx % len(DIAG_CARDS)]
    dots = "".join(
        f"<span class='toss-dot {'toss-dot-on' if i == idx % len(DIAG_CARDS) else ''}'>●</span>"
        for i in range(len(DIAG_CARDS))
    )
    st.markdown(
        f"<div class='toss-card'>"
        f"<div class='toss-card-emoji'>{card['emoji']}</div>"
        f"<div class='toss-card-label'>{card['label']}</div>"
        f"<div class='toss-card-desc'>{card['desc']}</div>"
        f"<div class='toss-card-dots'>{dots}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


def _load_welcome_image():
    import base64
    img_path = Path(__file__).parent / "image" / "dctractor.png"
    if img_path.exists():
        with open(img_path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{data}"
    return None


# ── 리포트 렌더링 ─────────────────────────────────────────────────
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
                    pid = upload_to_notion(
                        game_name, st.session_state.gallery_name,
                        subtype_id, scrape_result, ins,
                    )
                    st.session_state.notion_page_id = pid
                    _save_history()
                    st.session_state.step = 4
                    st.rerun()
                except Exception as e:
                    st.error(PUBLISH_ERROR_TMPL.format(error=e))
    else:
        st.write("")
        if st.button(HISTORY_BACK_BTN, use_container_width=True):
            st.session_state.viewing_history = None
            st.rerun()


# ── 메인 ─────────────────────────────────────────────────────────
def main():
    _init()
    _sidebar()

    guide = STEP_GUIDE_MESSAGES.get(st.session_state.step, "")
    if guide and st.session_state.viewing_history is None:
        st.markdown(f"<div class='floating-guide'>💡 {guide}</div>", unsafe_allow_html=True)

    if not _HAS_DIALOG and st.session_state.get("_show_modal"):
        with st.expander(SUBTYPE_MODAL_TITLE, expanded=True):
            render_subtype_modal_content()
            if st.button("✕ 닫기", key="modal_close"):
                st.session_state["_show_modal"] = False
                st.rerun()

    # ── 기록 열람 ────────────────────────────────────────────────
    if st.session_state.viewing_history is not None:
        idx  = st.session_state.viewing_history
        hist = st.session_state.history
        if 0 <= idx < len(hist):
            h = hist[idx]
            st.info(HISTORY_VIEW_LABEL.format(
                game_name=h["game_name"],
                date_range=h["date_range"],
                saved_at=h["saved_at"],
            ))
            _render_report(h["insights"], h["scrape_result"], h["game_name"], h["subtype_id"], is_history=True)
        else:
            st.session_state.viewing_history = None
            st.rerun()
        return

    # ── Step 0: URL 입력 ─────────────────────────────────────────
    if st.session_state.step == 0:
        _, col, _ = st.columns([1, 3, 1])
        with col:
            st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)

            img_src = _load_welcome_image()
            if img_src:
                st.markdown(
                    f"<div style='text-align:center;margin-bottom:10px;'>"
                    f"<img src='{img_src}' style='max-height:200px;width:auto;object-fit:contain;'>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            st.markdown(f"<h1 class='toss-h1'>{STEP0_TITLE}</h1>", unsafe_allow_html=True)
            st.markdown(f"<p class='toss-sub'>{STEP0_SUBTITLE}</p>", unsafe_allow_html=True)

            with st.expander(STEP0_NOTICE_TITLE, expanded=False):
                for item in STEP0_NOTICE_ITEMS:
                    st.markdown(
                        f"<div style='padding:8px 0 8px 12px;border-left:3px solid #e67e22;"
                        f"margin-bottom:8px;font-size:0.88rem;color:#444;line-height:1.6;'>"
                        f"{item}</div>",
                        unsafe_allow_html=True,
                    )

            st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)

            with st.container(border=True):
                st.markdown(
                    f"<div style='padding:4px 2px 8px 2px;'>"
                    f"<p style='font-weight:700;font-size:1rem;margin-bottom:8px;'>{STEP0_INPUT_HEADER}</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                raw_url = st.text_input("URL", placeholder=STEP0_PLACEHOLDER, label_visibility="collapsed")
                st.caption(STEP0_CAPTION)
                st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)

                if st.button(STEP0_BTN, type="primary", use_container_width=True):
                    if not raw_url.strip():
                        st.warning(STEP0_WARN_EMPTY); return
                    _, gal_id = parse_dc_url(raw_url)
                    if not gal_id:
                        st.warning(STEP0_WARN_INVALID); return

                    st.session_state.raw_url = raw_url
                    card_slot = st.empty(); prog_slot = st.empty(); msg_slot = st.empty()
                    card_idx  = [0]

                    def show_card():
                        with card_slot.container(): _diag_card(card_idx[0])
                        card_idx[0] += 1

                    show_card()
                    prog    = prog_slot.progress(0)
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
                    msg_slot.markdown("<div class='diag-msg'>🤖 AI가 갤러리 유형 파악 중...</div>", unsafe_allow_html=True)

                    base_game_name = guess_game_name(diag["gallery_name"], diag["top_title_words"])
                    st.session_state.update({
                        "diag":         diag,
                        "subtype_id":   detect_subtype(diag),
                        "game_name":    base_game_name,
                        "gallery_id":   diag["gallery_id"],
                        "gallery_name": diag["gallery_name"],
                        "auto_days":    _auto_days(diag["daily_avg"]),
                    })

                    ai_result, ai_err = diagnose_gallery_ai(
                        diag["gallery_name"], diag["top_title_words"],
                        st.session_state.subtype_id, diag["daily_avg"],
                    )
                    if not ai_err and ai_result:
                        st.session_state.diag_ai = ai_result
                        ai_guess = ai_result.get("topic_guess", "").strip()
                        # AI 추정값이 갤러리명 정제값과 길이 차이가 크지 않을 때만 반영
                        if ai_guess and len(ai_guess) >= len(base_game_name) * 0.5:
                            st.session_state.game_name = ai_guess

                    prog.progress(100)
                    card_slot.empty(); prog_slot.empty(); msg_slot.empty()
                    st.session_state.step = 1
                    st.rerun()

    # ── Step 1: 게임 확인 ───────────────────────────────────────
    elif st.session_state.step == 1:
        diag    = st.session_state.diag
        ai      = st.session_state.diag_ai or {}
        subtype = get_subtype_info(st.session_state.subtype_id)

        st.markdown("## ✅ 게임 확인")
        st.markdown(
            f"<p style='color:#6c757d;margin-top:-0.5rem;margin-bottom:1.5rem;'>"
            f"{DIAG_SECTION_SUBTITLE}</p>",
            unsafe_allow_html=True,
        )

        # ① AI 주제 + 게임명 입력 (먼저 표시)
        with st.container(border=True):
            st.markdown("<div style='padding:4px 2px;'>", unsafe_allow_html=True)
            st.markdown("#### 🤖 AI가 진단한 갤러리 주제")
            game_name_display = st.session_state.game_name
            topic_reason      = ai.get("topic_reason", "갤러리 타이틀 기반 자동 추출")
            st.markdown(
                f"<div style='font-size:2rem;font-weight:800;color:#1e2129;margin:8px 0 4px;'>"
                f"{game_name_display}</div>"
                f"<div style='font-size:0.82rem;color:#6c757d;margin-bottom:10px;'>"
                f"{STEP1_GAME_REASON_LABEL} {topic_reason}</div>"
                f"<div style='font-size:0.82rem;color:#e74c3c;font-weight:600;margin-bottom:12px;'>"
                f"{STEP1_GAME_WRONG_HINT}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(f"<div id='{GALLERY_NAME_ANCHOR_ID}'></div>", unsafe_allow_html=True)

            inp          = st.text_input(
                COND_GAME_INPUT_LABEL,
                value=game_name_display,
                placeholder=COND_GAME_PLACEHOLDER,
                label_visibility="collapsed",
            )
            current_game = inp.strip() or game_name_display

            if current_game != game_name_display:
                st.info(f"💡 '{current_game}' 주제로 분석을 진행합니다.")

            if ai.get("warning"):
                st.warning(f"⚠️ 참고: {ai['warning']}")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)

        # ② 진단기간 + 갤러리유형 → 2열 나란히 (아래에 배치)
        # min-height로 두 박스 높이를 동일하게 고정
        BOX_MIN_H = "210px"
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown(
                f"<div style='border:1px solid #e0e3e8;border-radius:10px;"
                f"padding:16px 18px;min-height:{BOX_MIN_H};box-sizing:border-box;'>"
                f"<div style='font-size:1rem;font-weight:700;margin-bottom:12px;'>📅 진단 기간</div>"
                f"<div style='font-size:1.05rem;font-weight:700;color:#1e2129;margin-bottom:4px;'>"
                f"{diag.get('diag_start','')} ~ {diag.get('diag_end','')}</div>"
                f"<div style='font-size:0.85rem;color:#6c757d;margin-bottom:12px;'>"
                f"일평균 <b>{diag['daily_avg']}개 게시글</b> · 자동 분석 기간: <b>{st.session_state.auto_days}일</b></div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            with st.expander("ℹ️ 분석 기간 자동 결정 기준", expanded=False):
                for line in DIAG_PERIOD_CRITERIA.strip().split("\n"):
                    st.markdown(
                        f"<div style='font-size:0.85rem;color:#555;padding:3px 0;'>{line}</div>",
                        unsafe_allow_html=True,
                    )

        with col_right:
            sc = subtype["color"]
            st.markdown(
                f"<div style='border:1px solid #e0e3e8;border-radius:10px;"
                f"padding:16px 18px;min-height:{BOX_MIN_H};box-sizing:border-box;'>"
                f"<div style='font-size:1rem;font-weight:700;margin-bottom:12px;'>🏷️ 갤러리 유형</div>"
                f"<div style='display:inline-flex;align-items:center;gap:10px;"
                f"padding:10px 14px;border-radius:10px;"
                f"border:1.5px solid {sc};background:{sc}0d;margin-bottom:12px;'>"
                f"<span style='font-size:1.3rem;'>{subtype['emoji']}</span>"
                f"<div><b style='color:{sc};font-size:1rem;'>{subtype['label']}</b>"
                f"<div style='font-size:0.82rem;color:#6c757d;margin-top:2px;'>{subtype['desc']}</div></div>"
                f"{_tip(TOOLTIP_SUBTYPE)}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            if st.button(SUBTYPE_MODAL_BTN, use_container_width=True):
                _show_modal()

        st.markdown("<div style='margin-top:18px;'></div>", unsafe_allow_html=True)

        if st.button(STEP1_START_BTN, type="primary", use_container_width=True):
            st.session_state.game_name = current_game
            focus = ai.get("suggested_focus", "default")
            if isinstance(focus, list):
                focus = focus[0] if focus else "default"
            st.session_state.auto_focus = focus
            st.session_state.step       = 2
            st.rerun()

    # ── Step 2: 수집 & AI 분석 ──────────────────────────────────
    elif st.session_state.step == 2:
        raw_url       = st.session_state.raw_url
        analysis_days = st.session_state.auto_days
        gallery_id    = st.session_state.gallery_id
        game_name     = st.session_state.game_name
        subtype_id    = st.session_state.subtype_id

        st.markdown(STEP2_TITLE)
        st.markdown(f"<p style='color:#6c757d;'>{STEP2_SUBTITLE}</p>", unsafe_allow_html=True)
        st.info(STEP2_INFO_TMPL.format(days=analysis_days))

        phase = st.empty(); pbar = st.progress(0); ticker_slot = st.empty()

        def show_phase(title, pct, is_ai=False):
            cls = "phase-card phase-card-ai" if is_ai else "phase-card"
            phase.markdown(
                f"<div class='{cls}'><div class='phase-title'>{title}</div></div>",
                unsafe_allow_html=True,
            )
            pbar.progress(int(pct))

        show_phase("갤러리에 접속 중...", 2)

        ticker_running = threading.Event(); ticker_running.set()
        def _ticker_loop():
            while ticker_running.is_set():
                ticker_slot.info(f"⏳ {random.choice(TICKER_MESSAGES)}")
                time.sleep(TICKER_INTERVAL)
        threading.Thread(target=_ticker_loop, daemon=True).start()

        def scb(msg, val): show_phase(f"🌾 {msg}", val)

        try:
            scrape_result = run_dc_scraper(raw_url, days_limit=analysis_days, progress_cb=scb)
        except Exception as e:
            ticker_running.clear(); ticker_slot.empty(); phase.empty(); pbar.empty()
            st.error(SCRAPE_ERROR_TMPL.format(error=e))
            if st.button(BTN_BACK): st.session_state.step = 1; st.rerun()
            return

        ticker_running.clear(); ticker_slot.empty()
        tot = scrape_result["total_posts"]; ana = scrape_result["analysis_count"]
        show_phase(f"수집 완료 — 전체 {tot}개 · 본문 수집 {ana}개", 100)

        ai_phase = st.empty(); ai_pbar = st.progress(0); ai_log = st.empty()
        ai_phase.markdown(
            "<div class='phase-card phase-card-ai'>"
            "<div class='phase-title'>AI 분석 시작...</div></div>",
            unsafe_allow_html=True,
        )

        res_box = [None, None]; ev = threading.Event()

        def run_ai():
            try:
                res_box[0], res_box[1] = analyze_gallery(
                    gallery_id=gallery_id, game_name=game_name,
                    subtype_id=subtype_id,
                    analysis_data=scrape_result["analysis_data"],
                    all_metas=scrape_result["all_metas"],
                    analysis_days=analysis_days,
                )
            except Exception as ex:
                res_box[1] = str(ex)
            finally:
                ev.set()

        threading.Thread(target=run_ai, daemon=True).start()

        tick = 0
        while not ev.is_set():
            ai_pbar.progress(min(95, 10 + tick * 3))
            ai_log.info(f"⏳ {random.choice(TICKER_MESSAGES)}")
            time.sleep(TICKER_INTERVAL); tick += 1
        ai_pbar.progress(100); ai_log.empty()

        if res_box[1]:
            ai_phase.empty(); ai_pbar.empty()
            st.error(AI_ERROR_TMPL.format(error=res_box[1]))
            if st.button(BTN_BACK): st.session_state.step = 1; st.rerun()
            return

        ai_phase.markdown(
            "<div class='phase-card phase-card-ai'>"
            "<div class='phase-title'>✅ AI 분석 완료</div></div>",
            unsafe_allow_html=True,
        )
        st.session_state.scrape_result = scrape_result
        st.session_state.insights      = res_box[0]
        _save_history()
        st.session_state.step = 3
        time.sleep(0.6); st.rerun()

    # ── Step 3: 리포트 검수 ─────────────────────────────────────
    elif st.session_state.step == 3:
        _render_report(
            st.session_state.insights,
            st.session_state.scrape_result,
            st.session_state.game_name,
            st.session_state.subtype_id,
            is_history=False,
        )

    # ── Step 4: 발행 완료 ───────────────────────────────────────
    elif st.session_state.step == 4:
        st.balloons()
        _, cc, _ = st.columns([1, 2, 1])
        with cc:
            st.markdown("<div style='height:2rem;'></div>", unsafe_allow_html=True)
            st.success(NOTION_SUCCESS_MSG)
            pid   = st.session_state.notion_page_id
            p_url = f"https://notion.so/{pid.replace('-', '')}"
            st.markdown(
                f"<a href='{p_url}' target='_blank'>"
                f"<div style='padding:20px;border-radius:12px;border:2px solid #3b4890;"
                f"text-align:center;font-size:1.1rem;font-weight:700;color:#3b4890;"
                f"margin:1rem 0;cursor:pointer;'>{NOTION_LINK_LABEL}</div></a>",
                unsafe_allow_html=True,
            )
            st.write("")
            if st.button(STEP4_RESET_BTN, use_container_width=True):
                _reset(); st.rerun()


if __name__ == "__main__":
    main()