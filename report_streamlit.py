"""
report_streamlit.py v5

[변경]
- render_tab_segment 제거 (유저 세그먼트 탭 삭제)
- render_tab_timeline: 패치 타임라인 제거, 이슈 색상 범례 추가
- render_tab_complaints: 이탈 위험 신호 제거, 점수 설명 모달 팝업
- render_tab_summary: 민심 온도 측정 기준 모달 팝업
- render_tab_trend: 색상 의미 범례 추가
- 프로필: 분석 방법 표시 (개념글/고관여 구분)
- _strip_md: 완전 강화
"""

import streamlit as st
import plotly.graph_objects as go
import re
from collections import defaultdict
from config import COMPLAINT_CATEGORIES, GALLERY_SUBTYPES
from ui_texts import (
    TAB_LABELS,
    SUMMARY_TEMP_TITLE, SUMMARY_TEMP_EARLY, SUMMARY_TEMP_LATE, SUMMARY_TEMP_OVERALL,
    SUMMARY_TREND_TMPL, SUMMARY_POSITIVE_TITLE, SUMMARY_NEGATIVE_TITLE,
    TREND_UP, TREND_DOWN, TREND_FLAT,
    TIMELINE_ISSUE_TITLE, TIMELINE_NO_ISSUE, TIMELINE_ISSUE_DEFAULT,
    TIMELINE_ORIG_LINK_LABEL,
    SENTIMENT_ICON, SENTIMENT_CHANGE_DEFAULT, SENTIMENT_ICON_DEFAULT,
    COMPLAINT_TITLE, COMPLAINT_NO_DATA, COMPLAINT_RADAR_NAME,
    COMPLAINT_NO_SUMMARY, COMPLAINT_REF_LINK_LABEL,
    COMPLAINT_SUMMARY_LABEL, COMPLAINT_EXAMPLE_LABEL,
    TREND_TITLE, TREND_NO_DATA,
    RAW_TITLE_TMPL, RAW_ALL_TITLE, RAW_DATE_GROUP_TMPL,
    RAW_BADGE_CONCEPT, RAW_BADGE_NORMAL, RAW_POST_META_TMPL, RAW_NO_DATE_LABEL,
    TEMP_LABELS,
    ACTIONBAR_TITLE, ACTIONBAR_FEEDBACK_LABEL, ACTIONBAR_FEEDBACK_PLACEHOLDER,
    REANALYZE_BTN, PUBLISH_BTN,
    PROFILE_TITLE_TMPL, PROFILE_TEMP_LABEL,
    PROFILE_KEYWORD_TMPL, PROFILE_ONELINER_PREFIX,
    TOOLTIP_SENTIMENT_SCORE, TOOLTIP_SENTIMENT_PERIOD,
    CHART_HOVER_TMPL, CHART_14D_TITLE, CHART_14D_SPIKE,
    ANALYSIS_SPEC_TMPL, ANALYSIS_SPEC_REANALYZE,
    SENTIMENT_SCORE_DETAIL, COMPLAINT_SCORE_DETAIL,
    ISSUE_IMPACT_LEGEND, TREND_PRIORITY_LEGEND,
    sanitize_for_display,
)


def _strip_md(t: str) -> str:
    s = str(t)
    s = re.sub(r"~~(.+?)~~", r"\1", s, flags=re.DOTALL)
    s = re.sub(r"__(.+?)__", r"\1", s, flags=re.DOTALL)
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s, flags=re.DOTALL)
    s = re.sub(r"\*(.+?)\*",   r"\1", s, flags=re.DOTALL)
    s = re.sub(r"\*+", "", s)
    s = sanitize_for_display(s)
    return s

def _clean(t: str) -> str:
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", str(t))
    return _strip_md(s)

def _safe(d) -> list:
    if isinstance(d, list): return [str(i) for i in d]
    if isinstance(d, dict): return [str(v) for v in d.values()]
    if isinstance(d, str):  return [d]
    return []

def _tc(s: int) -> str:
    if s >= 70: return "#1d7a3a"
    if s >= 50: return "#2980b9"
    if s >= 30: return "#e67e22"
    return "#c0392b"

def _tl(s: int) -> str:
    for t, l in sorted(TEMP_LABELS.items(), reverse=True):
        if s >= t: return l
    return list(TEMP_LABELS.values())[-1]

def _link(url: str, label: str, color="#3b4890") -> str:
    if not url or not url.startswith("http"): return ""
    return (f"<a href='{url}' target='_blank' "
            f"style='font-size:0.78rem;color:{color};text-decoration:none;"
            f"border:1px solid {color};border-radius:4px;padding:2px 6px;'>{label}</a>")

def _badge(score: int) -> str:
    if score >= 8:   bg, fc = "#fde8e8", "#c0392b"
    elif score >= 5: bg, fc = "#fef3cd", "#e67e22"
    elif score >= 3: bg, fc = "#e8f4fd", "#2980b9"
    else:            bg, fc = "#f0f0f0", "#888"
    return f"<span style='background:{bg};color:{fc};font-weight:700;padding:3px 10px;border-radius:12px;font-size:1rem;'>{score}/10</span>"


# ── 딤드 팝업 모달 ────────────────────────────────────────────────
def _modal_btn(label: str, key: str, content_html: str, title: str):
    """버튼 클릭 시 딤드 배경 모달 표시"""
    if st.button(label, key=key, type="secondary"):
        st.session_state[f"_modal_{key}"] = True
    if st.session_state.get(f"_modal_{key}"):
        st.markdown(f"""
        <div class='dim-overlay' onclick="this.parentElement.querySelector('.dim-modal').style.display='none';this.style.display='none';">
        </div>
        <div class='dim-modal'>
          <div class='dim-modal-title'>{title}</div>
          <div class='dim-modal-body'>{content_html}</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("✕ 닫기", key=f"_close_{key}"):
            st.session_state[f"_modal_{key}"] = False
            st.rerun()


# ── 프로필 카드 ────────────────────────────────────────────────────
def render_gallery_profile(ins, scrape_result, game_name, subtype_id):
    sub  = GALLERY_SUBTYPES.get(subtype_id, GALLERY_SUBTYPES["stable"])
    dr   = scrape_result.get("date_range_str", "")
    tot  = scrape_result.get("total_posts", 0)
    con  = scrape_result.get("concept_posts", 0)
    ana  = scrape_result.get("analysis_count", 0)
    method = scrape_result.get("analysis_method", "high_engagement")
    core   = scrape_result.get("core_posts", ana)

    try:
        from datetime import datetime as _d
        d1, d2 = [_d.strptime(x.strip(), "%Y-%m-%d") for x in dr.split("~")]
        days = (d2 - d1).days + 1
    except Exception:
        days = "?"

    method_label = "🔥 개념글 위주" if method == "concept" else "💬 고관여 게시글 위주 (댓글 상위 20%)"

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        st.markdown(PROFILE_TITLE_TMPL.format(emoji=sub["emoji"], game_name=game_name))
        st.markdown(
            f"<div style='background:#eef0fa;border-left:4px solid #3b4890;border-radius:6px;padding:8px 14px;margin:4px 0 8px;'>"
            f"<span style='font-weight:700;color:#3b4890;'>📅 {dr}</span>"
            f"<span style='font-size:0.8rem;color:#6c757d;margin-left:10px;'>총 {days}일간 · 전체 {tot}개 · 개념글 {con}개 · 분석 표본 {core}개</span><br>"
            f"<span style='font-size:0.78rem;color:#6c757d;'>분석 방식: {method_label}</span>"
            f"</div>",
            unsafe_allow_html=True)
    with c2:
        sc = sub["color"]
        st.markdown(
            f"<div style='padding:10px;border-radius:8px;background:{sc}22;border-left:4px solid {sc};'>"
            f"<b>{sub['emoji']} {sub['label']}</b><br><small style='color:#666;'>{sub['desc']}</small></div>",
            unsafe_allow_html=True)
    with c3:
        ov    = ins.get("sentiment_score", {}).get("overall", 50)
        color = _tc(ov)
        st.markdown(
            f"<div style='padding:10px;border-radius:8px;background:{color}22;border-left:4px solid {color};text-align:center;'>"
            f"<div style='font-size:1.6rem;font-weight:bold;color:{color};'>{ov}</div>"
            f"<div style='font-size:0.8rem;color:#666;'>{PROFILE_TEMP_LABEL}</div>"
            f"<div style='font-weight:bold;color:{color};'>{_tl(ov)}</div></div>",
            unsafe_allow_html=True)

    st.markdown(
        f"<div style='padding:14px 18px;border-radius:10px;background:#f0f2f6;border-left:5px solid #3b4890;margin:10px 0;font-size:1.05rem;font-weight:bold;'>"
        f"{PROFILE_ONELINER_PREFIX} {_clean(ins.get('critic_one_liner',''))}</div>",
        unsafe_allow_html=True)

    kws = ins.get("top_keywords", [])
    if kws: st.info(PROFILE_KEYWORD_TMPL.format(keywords=" · ".join(kws)))

    with st.expander("📋 분석 조건 상세 보기", expanded=False):
        st.markdown(ANALYSIS_SPEC_TMPL.format(
            days=days, date_range=dr, total=tot, concept=con, analysis=core,
            subtype=f"{sub['emoji']} {sub['label']}"))
        st.caption(ANALYSIS_SPEC_REANALYZE)


# ── 탭 1: 핵심 요약 ───────────────────────────────────────────────
def render_tab_summary(ins, post_data):
    # 민심 온도 측정 기준 팝업 버튼
    col_t, col_btn = st.columns([5, 1])
    with col_t:
        st.markdown(f"### 🌡️ {SUMMARY_TEMP_TITLE}")
    with col_btn:
        _modal_btn("측정 기준 ⓘ", "sentiment_info",
                   SENTIMENT_SCORE_DETAIL.replace("\n","<br>"),
                   "민심 온도 측정 기준")

    sc = ins.get("sentiment_score", {})
    c1, c2, c3 = st.columns(3)
    for col, label, key in [
        (c1, SUMMARY_TEMP_EARLY,   "early_period"),
        (c2, SUMMARY_TEMP_LATE,    "late_period"),
        (c3, SUMMARY_TEMP_OVERALL, "overall"),
    ]:
        v = sc.get(key, 50); c = _tc(v)
        with col:
            st.markdown(
                f"<div style='text-align:center;padding:12px;border-radius:8px;background:{c}18;border:1px solid {c}55;'>"
                f"<div style='font-size:2rem;font-weight:bold;color:{c};'>{v}</div>"
                f"<div style='color:#666;font-size:0.85rem;'>{label}</div>"
                f"<div style='color:{c};font-weight:bold;'>{_tl(v)}</div></div>",
                unsafe_allow_html=True)

    tr = sc.get("trend", TREND_FLAT)
    ti = "📈" if tr == TREND_UP else ("📉" if tr == TREND_DOWN else "➡️")
    st.caption(f"{ti} {SUMMARY_TREND_TMPL.format(trend=tr)}")
    st.divider()

    sm = ins.get("sentiment_summary", {})
    cp, cn = st.columns(2)
    with cp:
        st.markdown(SUMMARY_POSITIVE_TITLE)
        for line in _safe(sm.get("positive")): st.markdown(f"- {_clean(line)}")
    with cn:
        st.markdown(SUMMARY_NEGATIVE_TITLE)
        for line in _safe(sm.get("negative")): st.markdown(f"- {_clean(line)}")


# ── 탭 2: 민심 & 이슈 ────────────────────────────────────────────
def render_tab_timeline(ins, scrape_result):
    # 14일 차트
    dc14 = scrape_result.get("date_counts_14") or {}
    if not dc14:
        from datetime import datetime as _dt, timedelta as _td
        cutoff14 = (_dt.now() - _td(days=14)).strftime("%Y-%m-%d")
        dc14 = {k: v for k, v in scrape_result.get("date_counts", {}).items() if k >= cutoff14}

    if dc14:
        st.markdown(f"#### 📅 {CHART_14D_TITLE}")

        from gallery_analyzer import detect_spike_dates
        tl_events = ins.get("issue_timeline", [])
        # impact 색상 맵
        ic_bar = {"high": "#c0392b", "medium": "#e67e22", "low": "#3b4890"}
        # 날짜→이벤트 맵 (이슈 타임라인 차트 반영)
        ev_map    = {e.get("date",""): (e.get("event",""), e.get("impact","low")) for e in tl_events}

        dates14  = sorted(dc14.keys())
        counts14 = [dc14[d] for d in dates14]
        spikes14 = detect_spike_dates(dc14)

        # 색상: 이슈 있는 날은 이슈 색상, 스파이크면 빨강, 나머지는 기본 파랑
        bar_colors = []
        for d in dates14:
            if d in ev_map:
                _, impact = ev_map[d]
                bar_colors.append(ic_bar.get(impact, "#e67e22"))
            elif d in spikes14:
                bar_colors.append("#e74c3c")
            else:
                bar_colors.append("#3b4890")

        # 어노테이션
        avg14 = sum(counts14) / max(len(counts14), 1)
        annots = []
        for i, d in enumerate(dates14):
            if d in ev_map:
                ev_text, impact = ev_map[d]
                annots.append(dict(
                    x=d, y=counts14[i],
                    text=f"{'🔴' if impact=='high' else '🟡' if impact=='medium' else '🔵'} {_clean(ev_text)[:20]}",
                    showarrow=True, arrowhead=2, ax=0, ay=-36,
                    font=dict(size=10, color=ic_bar.get(impact,"#e67e22"))))
            elif counts14[i] >= avg14 * 1.8 and counts14[i] > 2:
                annots.append(dict(
                    x=d, y=counts14[i], text="급증",
                    showarrow=True, arrowhead=2, ax=0, ay=-28,
                    font=dict(size=10, color="#e74c3c")))

        fig = go.Figure(go.Bar(
            x=dates14, y=counts14,
            marker=dict(color=bar_colors, line=dict(width=0)),
            hovertemplate=CHART_HOVER_TMPL))
        fig.update_layout(
            annotations=annots, height=260,
            margin=dict(l=0,r=0,t=16,b=0),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, tickfont=dict(size=10), tickangle=-30, fixedrange=True),
            yaxis=dict(gridcolor="#f1f3f5", fixedrange=True),
            dragmode=False, showlegend=False)
        st.plotly_chart(fig, use_container_width=True,
                        config={"displayModeBar": False, "scrollZoom": False})

        # 범례
        st.markdown(
            "<div style='display:flex;gap:16px;font-size:0.78rem;color:#6c757d;margin-bottom:4px;'>"
            "<span><b style='color:#c0392b;'>■</b> 높은 임팩트 이슈</span>"
            "<span><b style='color:#e67e22;'>■</b> 중간 임팩트 이슈</span>"
            "<span><b style='color:#3b4890;'>■</b> 낮은 임팩트 이슈 / 일반</span>"
            "<span><b style='color:#e74c3c;'>■</b> 글 급증(이슈 미연동)</span>"
            "</div>",
            unsafe_allow_html=True)
        st.caption(f"분석 기간: {scrape_result.get('date_range_str','')}")
        st.divider()

    # 이슈 타임라인
    col_t, col_btn = st.columns([5, 1])
    with col_t:
        st.markdown(TIMELINE_ISSUE_TITLE)
    with col_btn:
        st.markdown(
            "<div style='font-size:0.75rem;color:#6c757d;margin-top:14px;'>"
            "<b style='color:#c0392b;'>●</b> 높음 "
            "<b style='color:#e67e22;'>●</b> 중간 "
            "<b style='color:#2980b9;'>●</b> 낮음</div>",
            unsafe_allow_html=True)

    timeline = ins.get("issue_timeline", [])
    if timeline:
        ic = {"high":"#c0392b","medium":"#e67e22","low":"#2980b9"}
        for ev in timeline:
            color = ic.get(ev.get("impact","low"), "#999")
            icon  = SENTIMENT_ICON.get(ev.get("sentiment_change", SENTIMENT_CHANGE_DEFAULT), SENTIMENT_ICON_DEFAULT)
            date  = ev.get("date","")
            event = _clean(ev.get("event",""))
            ref   = ev.get("ref_url","")
            lk    = f" {_link(ref, TIMELINE_ORIG_LINK_LABEL, color)}" if ref else ""
            st.markdown(
                f"<div style='padding:8px 14px;margin:6px 0;border-radius:6px;"
                f"border-left:4px solid {color};background:{color}11;'>"
                f"<b style='color:{color};'>{date}</b> {icon} {event}{lk}</div>",
                unsafe_allow_html=True)
    else:
        st.info(TIMELINE_NO_ISSUE)


# ── 탭 3: 불만 분석 (이탈 위험 신호 제거) ───────────────────────
def render_tab_complaints(ins):
    col_t, col_btn = st.columns([5, 1])
    with col_t:
        st.markdown(f"### {COMPLAINT_TITLE}")
    with col_btn:
        _modal_btn("점수 기준 ⓘ", "complaint_info",
                   COMPLAINT_SCORE_DETAIL.replace("\n","<br>"),
                   "불만 강도 점수 기준")

    comp = ins.get("complaint_analysis", {})
    if not comp: st.info(COMPLAINT_NO_DATA); return

    # 레이더 차트
    labels = [COMPLAINT_CATEGORIES[k]["label"] for k in COMPLAINT_CATEGORIES]
    scores = [comp.get(k, {}).get("score", 0) for k in COMPLAINT_CATEGORIES]
    fig = go.Figure(go.Scatterpolar(
        r=scores+[scores[0]], theta=labels+[labels[0]],
        fill="toself", fillcolor="rgba(59,72,144,0.15)",
        line=dict(color="#3b4890", width=2), name=COMPLAINT_RADAR_NAME))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0,10], tickfont=dict(size=10))),
        height=280, margin=dict(l=40,r=40,t=20,b=20),
        paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # 점수 설명 범례 (한 줄)
    st.markdown(
        "<div style='font-size:0.78rem;color:#6c757d;margin-bottom:12px;'>"
        "점수 의미: "
        "<b style='color:#888;'>0~2</b> 거의 없음 · "
        "<b style='color:#2980b9;'>3~4</b> 낮음 · "
        "<b style='color:#e67e22;'>5~6</b> 주의 · "
        "<b style='color:#c0392b;'>7~10</b> 심각 &nbsp;|&nbsp; "
        "10점에 가까울수록 유저 불만이 높음</div>",
        unsafe_allow_html=True)

    st.markdown("---")
    for ck, ci in COMPLAINT_CATEGORIES.items():
        d     = comp.get(ck, {})
        score = d.get("score", 0)
        summ  = _clean(d.get("summary", COMPLAINT_NO_SUMMARY))
        ex    = _clean(d.get("example", ""))
        exurl = d.get("example_url", "")

        hc, sc_col = st.columns([4,1])
        with hc:
            st.markdown(
                f"**{ci['emoji']} {ci['label']}**",
                unsafe_allow_html=True)
        with sc_col:
            st.markdown(_badge(score), unsafe_allow_html=True)

        with st.expander("상세 보기", expanded=(score >= 5)):
            st.markdown(f"{COMPLAINT_SUMMARY_LABEL} {summ}")
            if ex:
                lk = _link(exurl, COMPLAINT_REF_LINK_LABEL)
                st.markdown(
                    f"<div style='background:#f8f9fa;border-left:3px solid #dee2e6;padding:8px 12px;border-radius:4px;margin-top:6px;'>"
                    f"{COMPLAINT_EXAMPLE_LABEL} {ex}{'  '+lk if lk else ''}</div>",
                    unsafe_allow_html=True)
        st.write("")


# ── 탭 4: 주목할 동향 ─────────────────────────────────────────────
def render_tab_trend(ins):
    col_t, _ = st.columns([5,1])
    with col_t:
        st.markdown(TREND_TITLE)

    # 색상 범례
    st.markdown(
        "<div style='display:flex;gap:16px;font-size:0.78rem;color:#6c757d;margin-bottom:12px;'>"
        "<span><b style='color:#c0392b;'>■</b> 집중도 높음</span>"
        "<span><b style='color:#e67e22;'>■</b> 주의 필요</span>"
        "<span><b style='color:#2980b9;'>■</b> 참고 수준</span>"
        "</div>",
        unsafe_allow_html=True)

    checklist = ins.get("pm_checklist", [])
    if not checklist: st.info(TREND_NO_DATA); return

    priority_color = {
        "urgent":"#c0392b","high":"#c0392b",
        "monitor":"#e67e22","medium":"#e67e22",
        "note":"#2980b9","low":"#2980b9",
    }
    for item in checklist:
        action  = _clean(item.get("action",""))
        reason  = _clean(item.get("reason",""))
        ref_url = item.get("ref_url","")
        pkey    = item.get("priority","note")
        color   = priority_color.get(pkey,"#adb5bd")
        lk      = _link(ref_url, "관련 게시글", color)
        st.markdown(
            f"<div style='padding:10px 16px;margin:6px 0;border-radius:8px;"
            f"border-left:4px solid {color};background:{color}11;'>"
            f"{action}"
            f"{'<br><small style=\"color:#888;\">'+reason+'</small>' if reason else ''}"
            f"{'<br>'+lk if lk else ''}</div>",
            unsafe_allow_html=True)


# ── 탭 5: 원본 데이터 ────────────────────────────────────────────
def render_tab_raw(scrape_result):
    total    = scrape_result.get("total_posts", 0)
    analysis = scrape_result.get("core_posts", scrape_result.get("analysis_count", 0))
    all_m    = scrape_result.get("all_metas", [])

    st.markdown(RAW_TITLE_TMPL.format(total=total, analysis=analysis))
    st.markdown(RAW_ALL_TITLE)

    groups = defaultdict(list)
    for m in all_m:
        groups[m.get("date", RAW_NO_DATE_LABEL)].append(m)

    for date in sorted(groups.keys(), reverse=True):
        posts = groups[date]
        with st.expander(RAW_DATE_GROUP_TMPL.format(date=date, count=len(posts)), expanded=False):
            for p in posts:
                badge = RAW_BADGE_CONCEPT if p.get("is_concept") else RAW_BADGE_NORMAL
                meta  = RAW_POST_META_TMPL.format(count=p.get("comment_count",0), utype=p.get("user_type",""))
                url   = p.get("post_url","")
                title = p.get("title","")
                tp    = f"[{title}]({url})" if url and url.startswith("http") else title
                st.markdown(f"- {badge} {tp} {meta}")


# ── 액션바 ────────────────────────────────────────────────────────
def render_action_bar():
    st.divider()
    with st.container(border=True):
        st.markdown(ACTIONBAR_TITLE)
        feedback = st.text_area(ACTIONBAR_FEEDBACK_LABEL,
                                placeholder=ACTIONBAR_FEEDBACK_PLACEHOLDER,
                                label_visibility="collapsed", key="feedback_input")
        c1, c2 = st.columns(2)
        with c1: rea = st.button(REANALYZE_BTN, use_container_width=True, key="btn_reanalyze")
        with c2: pub = st.button(PUBLISH_BTN, use_container_width=True, type="primary", key="btn_publish")
        return feedback, rea, pub