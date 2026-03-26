"""
report_streamlit.py v3 — 리포트 화면 렌더링 전담.
[v3 변경]
  - 날짜별 차트: 전체 게시글 기준(단일 막대), 분석 표본과 혼용 없음
  - 불만 카테고리: 프로그레스 바 → 점수 배지 + 히트맵 색상
  - 유저 세그먼트: 별도 탭, 주요 게시글 링크 포함
  - PM 체크리스트: 관련 게시글 링크 연결
"""

import streamlit as st
import plotly.graph_objects as go
import re
from collections import defaultdict
from config import COMPLAINT_CATEGORIES, ACTION_PRIORITY, GALLERY_SUBTYPES
from ui_texts import (
    TAB_LABELS,
    SUMMARY_TEMP_TITLE, SUMMARY_TEMP_EARLY, SUMMARY_TEMP_LATE, SUMMARY_TEMP_OVERALL,
    SUMMARY_TREND_TMPL, SUMMARY_POSITIVE_TITLE, SUMMARY_NEGATIVE_TITLE,
    TREND_UP, TREND_DOWN, TREND_FLAT,
    TIMELINE_CHART_TITLE, TIMELINE_CHART_ALL,
    TIMELINE_NO_DATA, TIMELINE_ISSUE_TITLE, TIMELINE_NO_ISSUE,
    TIMELINE_ISSUE_DEFAULT, TIMELINE_PATCH_TITLE, TIMELINE_PATCH_CAPTION,
    TIMELINE_PATCH_EXPANDER, TIMELINE_EXT_LINK_LABEL, TIMELINE_ORIG_LINK_LABEL,
    TIMELINE_PERIOD_TMPL,
    SENTIMENT_ICON, SENTIMENT_CHANGE_DEFAULT, SENTIMENT_ICON_DEFAULT,
    COMPLAINT_TITLE, COMPLAINT_NO_DATA, COMPLAINT_RADAR_NAME,
    COMPLAINT_NO_SUMMARY, COMPLAINT_REF_LINK_LABEL,
    COMPLAINT_EXPANDER_TMPL, COMPLAINT_SUMMARY_LABEL, COMPLAINT_EXAMPLE_LABEL,
    TOOLTIP_COMPLAINT_SCORE,
    CHURN_TITLE, CHURN_COUNT_TMPL, CHURN_SUMMARY_LABEL, CHURN_REASON_LABEL,
    CHURN_RISK_LABELS, CHURN_RISK_TITLE,
    SEGMENT_TAB_TITLE, SEGMENT_CORE_LABEL, SEGMENT_CASUAL_LABEL,
    SEGMENT_INSIGHT_TITLE, SEGMENT_POSTS_TITLE_TMPL, SEGMENT_POSTS_EMPTY,
    SEGMENT_TEMP_TMPL, SEGMENT_GAP_PREFIX,
    CHECKLIST_TITLE, CHECKLIST_CAPTION, CHECKLIST_NO_DATA, CHECKLIST_REF_LINK_LABEL,
    RAW_TITLE_TMPL, RAW_ALL_TITLE, RAW_DATE_GROUP_TMPL,
    RAW_BADGE_CONCEPT, RAW_BADGE_NORMAL, RAW_POST_META_TMPL, RAW_NO_DATE_LABEL,
    TEMP_LABELS,
    ACTIONBAR_TITLE, ACTIONBAR_FEEDBACK_LABEL, ACTIONBAR_FEEDBACK_PLACEHOLDER,
    REANALYZE_BTN, PUBLISH_BTN,
    PROFILE_TITLE_TMPL, PROFILE_PERIOD_LABEL, PROFILE_TEMP_LABEL,
    PROFILE_KEYWORD_TMPL, PROFILE_ONELINER_PREFIX, PROFILE_PERIOD_DETAIL_TMPL,
    TOOLTIP_SENTIMENT_SCORE, TOOLTIP_SENTIMENT_PERIOD,
    CHART_HOVER_TMPL,
    sanitize_for_display,
)


def _strip_md(t: str) -> str:
    return sanitize_for_display(re.sub(r"\*+", "", str(t)))

def _strip_links(t: str) -> str:
    return re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", str(t))

def _safe_list(d) -> list:
    if isinstance(d, list): return [str(i) for i in d]
    if isinstance(d, dict): return [str(v) for v in d.values()]
    if isinstance(d, str):  return [d]
    return []

def _temp_color(s: int) -> str:
    if s >= 70: return "#1d7a3a"
    if s >= 50: return "#2980b9"
    if s >= 30: return "#e67e22"
    return "#c0392b"

def _temp_label(s: int) -> str:
    for t, l in sorted(TEMP_LABELS.items(), reverse=True):
        if s >= t: return l
    return list(TEMP_LABELS.values())[-1]

def _tip(text: str, wide: bool = False) -> str:
    cls = "tt-box tt-wide" if wide else "tt-box"
    return (f"<span class='tt-wrap' style='color:#3b4890;cursor:help;font-size:0.8rem;'>ⓘ"
            f"<span class='{cls}'>{text}</span></span>")

def _link_btn(url: str, label: str, color: str = "#3b4890") -> str:
    if not url or not url.startswith("http"): return ""
    return (f"<a href='{url}' target='_blank' "
            f"style='font-size:0.78rem;color:{color};text-decoration:none;"
            f"border:1px solid {color};border-radius:4px;padding:2px 6px;'>"
            f"{label}</a>")

def _score_badge(score: int) -> str:
    """점수를 색상 배지로 표시 (프로그레스 바 대체)."""
    if score >= 8:   bg, fc = "#fde8e8", "#c0392b"
    elif score >= 5: bg, fc = "#fef3cd", "#e67e22"
    elif score >= 3: bg, fc = "#e8f4fd", "#2980b9"
    else:            bg, fc = "#f0f0f0", "#888"
    return (f"<span style='background:{bg};color:{fc};font-weight:700;"
            f"padding:3px 10px;border-radius:12px;font-size:1rem;'>{score}/10</span>")


# ─────────────────────────────────────────────
# 갤러리 프로필 카드
# ─────────────────────────────────────────────
def render_gallery_profile(ins, scrape_result, game_name, subtype_id):
    subtype = GALLERY_SUBTYPES.get(subtype_id, GALLERY_SUBTYPES["stable"])
    c1, c2, c3 = st.columns([2, 1, 1])

    with c1:
        st.markdown(PROFILE_TITLE_TMPL.format(emoji=subtype["emoji"], game_name=game_name))
        dr  = scrape_result.get("date_range_str","")
        tot = scrape_result.get("total_posts", 0)
        con = scrape_result.get("concept_posts", 0)
        nor = scrape_result.get("normal_posts", 0)
        ana = scrape_result.get("analysis_count", 0)

        # 분석 기간 날짜 수 계산
        dates_str = dr.split(" ~ ")
        try:
            from datetime import datetime as _dt
            d1 = _dt.strptime(dates_str[0], "%Y-%m-%d")
            d2 = _dt.strptime(dates_str[1], "%Y-%m-%d")
            days = (d2 - d1).days + 1
        except Exception:
            days = "?"

        detail = PROFILE_PERIOD_DETAIL_TMPL.format(
            days=days, total=tot, concept=con, normal=nor, analysis=ana)
        st.markdown(
            f"<div style='background:#eef0fa;border-left:4px solid #3b4890;"
            f"border-radius:6px;padding:8px 14px;margin:4px 0 8px;'>"
            f"<span style='font-size:0.9rem;font-weight:700;color:#3b4890;'>📅 {dr}</span>"
            f"<span style='font-size:0.8rem;color:#6c757d;margin-left:10px;'>{detail}</span></div>",
            unsafe_allow_html=True)

    with c2:
        sc = subtype["color"]
        st.markdown(
            f"<div style='padding:10px;border-radius:8px;background:{sc}22;border-left:4px solid {sc};'>"
            f"<b>{subtype['emoji']} {subtype['label']}</b><br>"
            f"<small style='color:#666;'>{subtype['desc']}</small></div>",
            unsafe_allow_html=True)

    with c3:
        overall = ins.get("sentiment_score", {}).get("overall", 50)
        color   = _temp_color(overall)
        st.markdown(
            f"<div style='padding:10px;border-radius:8px;background:{color}22;"
            f"border-left:4px solid {color};text-align:center;'>"
            f"<div style='font-size:1.6rem;font-weight:bold;color:{color};'>{overall}</div>"
            f"<div style='font-size:0.8rem;color:#666;'>{PROFILE_TEMP_LABEL} "
            f"{_tip(TOOLTIP_SENTIMENT_SCORE, wide=True)}</div>"
            f"<div style='font-weight:bold;color:{color};'>{_temp_label(overall)}</div>"
            f"</div>", unsafe_allow_html=True)

    st.markdown(
        f"<div style='padding:14px 18px;border-radius:10px;background:#f0f2f6;"
        f"border-left:5px solid #3b4890;margin:10px 0;font-size:1.1rem;font-weight:bold;'>"
        f"{PROFILE_ONELINER_PREFIX} {_strip_md(ins.get('critic_one_liner',''))}</div>",
        unsafe_allow_html=True)

    kws = ins.get("top_keywords", [])
    if kws: st.info(PROFILE_KEYWORD_TMPL.format(keywords=" · ".join(kws)))


# ─────────────────────────────────────────────
# 탭 1 — 핵심 요약
# ─────────────────────────────────────────────
def render_tab_summary(ins, post_data):
    st.markdown(f"{SUMMARY_TEMP_TITLE} {_tip(TOOLTIP_SENTIMENT_SCORE, wide=True)}",
                unsafe_allow_html=True)

    sc = ins.get("sentiment_score", {})
    c1, c2, c3 = st.columns(3)
    for col, label, key, tip in [
        (c1, SUMMARY_TEMP_EARLY,   "early_period", TOOLTIP_SENTIMENT_PERIOD),
        (c2, SUMMARY_TEMP_LATE,    "late_period",  TOOLTIP_SENTIMENT_PERIOD),
        (c3, SUMMARY_TEMP_OVERALL, "overall",      TOOLTIP_SENTIMENT_SCORE),
    ]:
        v = sc.get(key, 50); c = _temp_color(v)
        with col:
            st.markdown(
                f"<div style='text-align:center;padding:12px;border-radius:8px;"
                f"background:{c}18;border:1px solid {c}55;'>"
                f"<div style='font-size:2rem;font-weight:bold;color:{c};'>{v}</div>"
                f"<div style='color:#666;font-size:0.85rem;'>{label} {_tip(tip, wide=True)}</div>"
                f"<div style='color:{c};font-weight:bold;'>{_temp_label(v)}</div>"
                f"</div>", unsafe_allow_html=True)

    tr = sc.get("trend", TREND_FLAT)
    ti = "📈" if tr == TREND_UP else ("📉" if tr == TREND_DOWN else "➡️")
    st.caption(f"{ti} {SUMMARY_TREND_TMPL.format(trend=tr)}")
    st.divider()

    sm = ins.get("sentiment_summary", {})
    cp, cn = st.columns(2)
    with cp:
        st.markdown(SUMMARY_POSITIVE_TITLE)
        for line in _safe_list(sm.get("positive")):
            st.markdown(f"- {_strip_links(_strip_md(line))}")
    with cn:
        st.markdown(SUMMARY_NEGATIVE_TITLE)
        for line in _safe_list(sm.get("negative")):
            st.markdown(f"- {_strip_links(_strip_md(line))}")


# ─────────────────────────────────────────────
# 탭 2 — 민심 & 이슈 (날짜별 차트: 전체 기준 단일 막대)
# ─────────────────────────────────────────────
def render_tab_timeline(ins, scrape_result, patch_timeline):
    st.markdown(f"### 📈 {TIMELINE_CHART_TITLE}")
    date_counts = scrape_result.get("date_counts", {})
    dr          = scrape_result.get("date_range_str", "")

    if date_counts:
        dates  = sorted(date_counts.keys())
        counts = [date_counts[d] for d in dates]
        avg    = sum(counts) / max(len(counts), 1)

        timeline_events = ins.get("issue_timeline", [])
        event_map = {ev.get("date",""): ev.get("event","") for ev in timeline_events}
        annotations = []
        for i, d in enumerate(dates):
            if counts[i] >= avg * 1.8 and counts[i] > 2:
                annotations.append(dict(
                    x=d, y=counts[i],
                    text=f"🔥 {event_map.get(d, TIMELINE_ISSUE_DEFAULT)[:20]}",
                    showarrow=True, arrowhead=2, ax=0, ay=-35,
                    font=dict(size=11, color="#c0392b")))

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=dates, y=counts, name=TIMELINE_CHART_ALL,
            marker_color="#3b4890", opacity=0.85,
            hovertemplate=CHART_HOVER_TMPL))
        fig.update_layout(
            barmode="stack", annotations=annotations,
            height=300, margin=dict(l=0, r=0, t=20, b=40),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, fixedrange=True),
            yaxis=dict(gridcolor="#eee", fixedrange=True),
            dragmode=False, showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True,
                        config={"displayModeBar": False, "scrollZoom": False})
        if dr:
            st.caption(TIMELINE_PERIOD_TMPL.format(
                start=dr.split(" ~ ")[0] if " ~ " in dr else dr,
                end=dr.split(" ~ ")[1] if " ~ " in dr else ""))
    else:
        st.info(TIMELINE_NO_DATA)

    st.divider()
    st.markdown(TIMELINE_ISSUE_TITLE)
    timeline = ins.get("issue_timeline", [])
    if timeline:
        ic = {"high":"#c0392b","medium":"#e67e22","low":"#2980b9"}
        for ev in timeline:
            color   = ic.get(ev.get("impact","low"), "#999")
            icon    = SENTIMENT_ICON.get(ev.get("sentiment_change", SENTIMENT_CHANGE_DEFAULT),
                                         SENTIMENT_ICON_DEFAULT)
            date    = ev.get("date","")
            event   = _strip_md(ev.get("event",""))
            ref_url = ev.get("ref_url","")
            link    = _link_btn(ref_url, TIMELINE_ORIG_LINK_LABEL, color)
            link_part = f" {link}" if link else ""
            st.markdown(
                f"<div style='padding:8px 14px;margin:6px 0;border-radius:6px;"
                f"border-left:4px solid {color};background:{color}11;'>"
                f"<b style='color:{color};'>{date}</b> {icon} {event}{link_part}"
                f"</div>", unsafe_allow_html=True)
    else:
        st.info(TIMELINE_NO_ISSUE)

    # 패치 타임라인
    if patch_timeline and patch_timeline.strip():
        st.divider()
        st.markdown(TIMELINE_PATCH_TITLE)
        st.caption(TIMELINE_PATCH_CAPTION)
        with st.expander(TIMELINE_PATCH_EXPANDER, expanded=False):
            for line in patch_timeline.split("\n"):
                if not line.strip(): continue
                url_m = re.search(r'\(URL:\s*(https?://[^\s)]+)\)', line)
                if url_m:
                    url = url_m.group(1)
                    text = line[:url_m.start()].strip()
                    st.markdown(f"{text} [{TIMELINE_EXT_LINK_LABEL}]({url})")
                else:
                    url_m2 = re.search(r'https?://[^\s)]+', line)
                    if url_m2:
                        url  = url_m2.group(0)
                        text = line[:url_m2.start()].strip().rstrip("(").strip()
                        st.markdown(f"{text} [{TIMELINE_EXT_LINK_LABEL}]({url})")
                    else:
                        st.markdown(line)


# ─────────────────────────────────────────────
# 탭 3 — 불만 분석 (점수 배지 방식)
# ─────────────────────────────────────────────
def render_tab_complaints(ins):
    st.markdown(f"{COMPLAINT_TITLE} {_tip(TOOLTIP_COMPLAINT_SCORE, wide=True)}",
                unsafe_allow_html=True)

    complaint = ins.get("complaint_analysis", {})
    if not complaint: st.info(COMPLAINT_NO_DATA); return

    # 레이더 차트
    cat_labels = [COMPLAINT_CATEGORIES[k]["label"] for k in COMPLAINT_CATEGORIES]
    cat_scores = [complaint.get(k, {}).get("score", 0) for k in COMPLAINT_CATEGORIES]
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=cat_scores + [cat_scores[0]], theta=cat_labels + [cat_labels[0]],
        fill="toself", fillcolor="rgba(59,72,144,0.15)",
        line=dict(color="#3b4890", width=2), name=COMPLAINT_RADAR_NAME))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0,10], tickfont=dict(size=10))),
        height=300, margin=dict(l=40, r=40, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    # 카테고리별 — 점수 배지 + 상세
    for cat_key, cat_info in COMPLAINT_CATEGORIES.items():
        data    = complaint.get(cat_key, {})
        score   = data.get("score", 0)
        summary = _strip_md(data.get("summary", COMPLAINT_NO_SUMMARY))
        example = _strip_md(data.get("example", ""))
        ex_url  = data.get("example_url", "")

        # 카테고리 헤더 행 (점수 배지 포함)
        h_col, s_col = st.columns([4, 1])
        with h_col:
            st.markdown(
                f"**{cat_info['emoji']} {cat_info['label']}** "
                f"<span style='color:#888;font-size:0.85rem;'>— {cat_info['score_logic']}</span>",
                unsafe_allow_html=True)
        with s_col:
            st.markdown(_score_badge(score), unsafe_allow_html=True)

        with st.expander(f"{COMPLAINT_EXPANDER_TMPL.format(emoji='', label='상세 보기')}",
                         expanded=(score >= 5)):
            st.markdown(f"{COMPLAINT_SUMMARY_LABEL} {summary}")
            if example:
                link = _link_btn(ex_url, COMPLAINT_REF_LINK_LABEL)
                st.markdown(
                    f"<div style='background:#f8f9fa;border-left:3px solid #dee2e6;"
                    f"padding:8px 12px;border-radius:4px;margin-top:6px;'>"
                    f"{COMPLAINT_EXAMPLE_LABEL} {example}"
                    f"{'  ' + link if link else ''}</div>",
                    unsafe_allow_html=True)
        st.write("")

    # 이탈 신호
    st.divider()
    st.markdown(CHURN_TITLE)
    churn = ins.get("churn_analysis", {})
    risk  = churn.get("risk_level","low")
    rc    = {"high":"#c0392b","medium":"#e67e22","low":"#2980b9"}
    color = rc.get(risk, "#999")
    c1, c2 = st.columns([1,3])
    with c1:
        st.markdown(
            f"<div style='padding:18px;border-radius:10px;background:{color}22;"
            f"border:2px solid {color};text-align:center;font-size:1.2rem;"
            f"font-weight:bold;color:{color};'>{CHURN_RISK_LABELS.get(risk,risk)}<br>"
            f"<span style='font-size:0.85rem;'>{CHURN_RISK_TITLE}</span></div>",
            unsafe_allow_html=True)
    with c2:
        st.markdown(CHURN_COUNT_TMPL.format(count=churn.get("strong_signal_count",0)))
        st.markdown(f"{CHURN_SUMMARY_LABEL} {_strip_md(churn.get('summary',''))}")
        for r in _safe_list(churn.get("main_reasons")):
            st.markdown(f"- {_strip_md(r)}")


# ─────────────────────────────────────────────
# 탭 4 — 유저 세그먼트 (별도 탭, 주요 게시글 링크)
# ─────────────────────────────────────────────
def render_tab_segment(ins):
    st.markdown(SEGMENT_TAB_TITLE)
    seg = ins.get("segment_analysis", {})
    if not seg: st.info("세그먼트 분석 데이터가 없습니다."); return

    ct, xt = seg.get("core_user_temp",50), seg.get("casual_user_temp",50)
    ca, cb = st.columns(2)
    for col, temp, label, key in [
        (ca, ct, SEGMENT_CORE_LABEL,   "core_main_concern"),
        (cb, xt, SEGMENT_CASUAL_LABEL, "casual_main_concern"),
    ]:
        c = _temp_color(temp)
        with col:
            st.markdown(
                f"<div style='padding:14px 16px;border-radius:10px;background:{c}18;"
                f"border-left:4px solid {c};margin:4px 6px;'>"
                f"<b>{label}</b><br>"
                f"<span style='font-size:1.4rem;color:{c};font-weight:bold;'>"
                f"{SEGMENT_TEMP_TMPL.format(temp=temp)}</span> "
                f"<span style='color:{c};'>{_temp_label(temp)}</span><br>"
                f"<small>{_strip_md(seg.get(key,''))}</small>"
                f"</div>", unsafe_allow_html=True)

    gap = _strip_md(seg.get("gap_insight",""))
    if gap:
        st.info(f"{SEGMENT_GAP_PREFIX} {gap}")

    st.divider()

    # 코어 유저 주요 게시글
    for label, posts_key in [
        (SEGMENT_CORE_LABEL,   "core_key_posts"),
        (SEGMENT_CASUAL_LABEL, "casual_key_posts"),
    ]:
        st.markdown(SEGMENT_POSTS_TITLE_TMPL.format(label=label))
        posts = seg.get(posts_key, [])
        if not posts:
            st.caption(SEGMENT_POSTS_EMPTY)
        else:
            for p in posts:
                summary = _strip_md(p.get("summary",""))
                url     = p.get("url","")
                link    = _link_btn(url, "원문", "#3b4890")
                st.markdown(
                    f"<div style='padding:8px 14px;margin:4px 0;border-radius:6px;"
                    f"background:#f8f9fa;border-left:3px solid #dee2e6;'>"
                    f"{summary} {link}</div>",
                    unsafe_allow_html=True)
        st.write("")


# ─────────────────────────────────────────────
# 탭 5 — PM 체크리스트 (링크 연결)
# ─────────────────────────────────────────────
def render_tab_checklist(ins):
    st.markdown(CHECKLIST_TITLE)
    st.caption(CHECKLIST_CAPTION)
    checklist = ins.get("pm_checklist",[])
    if not checklist: st.info(CHECKLIST_NO_DATA); return

    order   = ["urgent","monitor","note"]
    grouped = {p: [] for p in order}
    for item in checklist:
        grouped.get(item.get("priority","note"), grouped["note"]).append(item)

    for pkey in order:
        items = grouped[pkey]
        if not items: continue
        pinfo = ACTION_PRIORITY[pkey]
        st.markdown(f"#### {pinfo['emoji']} {pinfo['label']}")
        for item in items:
            action  = _strip_md(item.get("action",""))
            reason  = _strip_md(item.get("reason",""))
            ref_url = item.get("ref_url","")
            color   = pinfo["color"]
            link    = _link_btn(ref_url, CHECKLIST_REF_LINK_LABEL, color)
            link_part = f"<br>{link}" if link else ""
            st.markdown(
                f"<div style='padding:10px 14px;margin:6px 0;border-radius:8px;"
                f"border-left:4px solid {color};background:{color}11;'>"
                f"<b>{action}</b>"
                f"{'<br><small style=color:#666;>'+reason+'</small>' if reason else ''}"
                f"{link_part}</div>",
                unsafe_allow_html=True)
        st.write("")


# ─────────────────────────────────────────────
# 탭 6 — 원본 데이터
# ─────────────────────────────────────────────
def render_tab_raw(scrape_result):
    total    = scrape_result.get("total_posts", 0)
    analysis = scrape_result.get("analysis_count", 0)
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
                meta  = RAW_POST_META_TMPL.format(
                    count=p.get("comment_count",0), utype=p.get("user_type",""))
                url   = p.get("post_url","")
                title = p.get("title","")
                tp    = f"[{title}]({url})" if url and url.startswith("http") else title
                st.markdown(f"- {badge} {tp} {meta}")


# ─────────────────────────────────────────────
# 액션바
# ─────────────────────────────────────────────
def render_action_bar():
    st.divider()
    with st.container(border=True):
        st.markdown(ACTIONBAR_TITLE)
        feedback = st.text_area(ACTIONBAR_FEEDBACK_LABEL,
                                placeholder=ACTIONBAR_FEEDBACK_PLACEHOLDER,
                                label_visibility="collapsed", key="feedback_input")
        c1, c2 = st.columns(2)
        with c1: reanalyze = st.button(REANALYZE_BTN, use_container_width=True, key="btn_reanalyze")
        with c2: publish   = st.button(PUBLISH_BTN, use_container_width=True,
                                        type="primary", key="btn_publish")
        return feedback, reanalyze, publish