"""
report_streamlit.py v12
- 바 차트: trace0 제거 (범례 전용 trace에 showlegend=False 처리)
- render_tab_issues: issue_title 볼드 + issue_detail 줄바꿈 렌더링
- render_tab_complaints: 점수 내림차순 정렬, expander 내부 padding 추가
- _render_sentiment: 긍/부정 각 최대 5개까지만 표시
"""
import streamlit as st
import plotly.graph_objects as go
from collections import defaultdict
from config import COMPLAINT_CATEGORIES, GALLERY_SUBTYPES
from utils import clean, extract_url, link_btn, score_badge_html, complaint_badge_html
from ui_texts import (
    TAB_LABELS, COMPLAINT_TITLE, COMPLAINT_NO_DATA, COMPLAINT_RADAR_NAME,
    COMPLAINT_NO_SUMMARY, COMPLAINT_EXAMPLE_LABEL,
    RAW_TITLE_TMPL, RAW_ALL_TITLE, RAW_DATE_GROUP_TMPL,
    RAW_BADGE_HIGH_ENG, RAW_BADGE_NORMAL, RAW_POST_META_TMPL, RAW_NO_DATE_LABEL,
    ACTIONBAR_TITLE, PUBLISH_BTN, NEW_ANALYSIS_BTN,
    PROFILE_KEYWORD_TMPL, PROFILE_ONELINER_PREFIX,
    TIMELINE_CHART_TITLE, TIMELINE_NO_DATA,
    ISSUE_TITLE, ISSUE_NO_DATA, SCORE_BASED_ON_FREQ,
    COMPLAINT_SCORE_BOX, ISSUE_SCORE_BOX, ANALYSIS_SPEC_TMPL,
    SUBTYPE_MODAL_DESC, SUBTYPE_DEFINITIONS,
    SUBTYPE_CRITERIA_PREFIX, SUBTYPE_FOCUS_PREFIX,
)


# ── 갤러리 프로필 헤더 ────────────────────────────────────────────
def render_gallery_profile(ins, scrape_result, game_name, subtype_id):
    sub  = GALLERY_SUBTYPES.get(subtype_id, GALLERY_SUBTYPES["stable"])
    dr   = scrape_result.get("date_range_str", "")
    tot  = scrape_result.get("total_posts", 0)
    core = scrape_result.get("core_posts", scrape_result.get("analysis_count", 0))
    sc   = sub["color"]

    st.markdown(
        f"<div style='display:flex;align-items:center;gap:12px;margin-bottom:8px;'>"
        f"<h2 style='margin:0;font-size:1.5rem;'>{sub['emoji']} {game_name} 분석 리포트</h2>"
        f"<span style='padding:4px 12px;border-radius:20px;background:{sc}22;"
        f"border:1px solid {sc};font-size:0.82rem;font-weight:700;color:{sc};"
        f"white-space:nowrap;'>{sub['label']}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    with st.expander(f"ℹ️ '{sub['label']}' 유형 판별 기준 및 수집 포커스 보기", expanded=False):
        render_subtype_modal_content()

    spec = ANALYSIS_SPEC_TMPL.format(date_range=dr, total=tot, analysis=core)
    st.markdown(
        f"<div style='background:#eef0fa;border-left:4px solid #3b4890;border-radius:6px;"
        f"padding:10px 16px;margin-bottom:12px;margin-top:6px;'>"
        f"<span style='font-size:0.9rem;color:#1e2129;'>{spec}</span></div>",
        unsafe_allow_html=True,
    )

    one_liner = clean(ins.get("critic_one_liner", ""))
    if one_liner:
        st.markdown(
            f"<div style='padding:14px 18px;border-radius:10px;background:#f0f2f6;"
            f"border-left:5px solid #3b4890;margin-bottom:12px;"
            f"font-size:1.05rem;font-weight:bold;line-height:1.6;'>"
            f"{PROFILE_ONELINER_PREFIX} {one_liner}</div>",
            unsafe_allow_html=True,
        )

    kws = ins.get("top_keywords", [])
    if kws:
        st.info(PROFILE_KEYWORD_TMPL.format(keywords=" · ".join(kws[:5])))


# ── 탭 1: 갤러리 현황 ────────────────────────────────────────────
def _render_sentiment(ins):
    """긍/부정 여론 — 각 최대 5개까지만 표시."""
    st.markdown("### 💬 긍정 및 부정 여론 요약")
    sent = ins.get("sentiment_summary", {})
    pos  = sent.get("positive", [])[:5]   # 최대 5개
    neg  = sent.get("negative", [])[:5]   # 최대 5개

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 🟢 주요 긍정 여론")
        if pos:
            for p in pos:
                summ = clean(p.get("summary", ""))
                lk   = link_btn(p.get("ref_url", ""))
                st.markdown(
                    f"<div style='padding:6px 0 6px 4px;'>"
                    f"- {summ} {lk}</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("긍정 여론이 없습니다.")
    with c2:
        st.markdown("##### 🔴 주요 부정 여론")
        if neg:
            for n in neg:
                summ = clean(n.get("summary", ""))
                lk   = link_btn(n.get("ref_url", ""))
                st.markdown(
                    f"<div style='padding:6px 0 6px 4px;'>"
                    f"- {summ} {lk}</div>",
                    unsafe_allow_html=True,
                )
        else:
            st.info("부정 여론이 없습니다.")


def _render_bar_chart(scrape_result):
    st.markdown(f"### 📊 {TIMELINE_CHART_TITLE}")
    dc14 = scrape_result.get("date_counts_14") or scrape_result.get("date_counts", {})
    if not dc14:
        st.info(TIMELINE_NO_DATA)
        return

    dates14        = sorted(dc14.keys())
    counts14       = [dc14[d] for d in dates14]
    n              = len(dates14)
    tick_step      = max(1, n // 7)
    analysis_dates = set(scrape_result.get("date_counts", {}).keys())
    colors         = ["#3b4890" if d in analysis_dates else "#adb5bd" for d in dates14]
    has_ref        = any(d not in analysis_dates for d in dates14)

    # 메인 바 trace
    fig = go.Figure(go.Bar(
        x=dates14, y=counts14,
        marker=dict(color=colors, line=dict(width=0)),
        hovertemplate="<b>%{x}</b><br>%{y}개<extra></extra>",
        showlegend=False,   # 메인 바는 범례 숨김
    ))

    # 범례용 더미 trace — trace0 라벨이 생기지 않도록 name 명시
    if has_ref:
        fig.add_trace(go.Bar(
            x=[None], y=[None], marker_color="#3b4890",
            name="분석 기간", showlegend=True,
        ))
        fig.add_trace(go.Bar(
            x=[None], y=[None], marker_color="#adb5bd",
            name="참고 기간", showlegend=True,
        ))

    fig.update_layout(
        height=330,
        margin=dict(l=0, r=0, t=28, b=8),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False, tickangle=-45,
            tickmode="array",
            tickvals=dates14[::tick_step],
            ticktext=dates14[::tick_step],
            tickfont=dict(size=11),
            fixedrange=True,
        ),
        yaxis=dict(
            title="게시글 수",
            gridcolor="#f1f3f5",
            fixedrange=True,
            tickfont=dict(size=11),
        ),
        dragmode=False,
        showlegend=has_ref,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "scrollZoom": False})


def render_tab_overview(ins, scrape_result):
    _render_sentiment(ins)
    st.divider()
    _render_bar_chart(scrape_result)


# ── 탭 2: 주요 이슈 ──────────────────────────────────────────────
def render_tab_issues(ins):
    st.markdown(ISSUE_TITLE)
    st.markdown(ISSUE_SCORE_BOX, unsafe_allow_html=True)

    issues = ins.get("major_issues", [])
    if not issues:
        st.info(ISSUE_NO_DATA)
        return

    issues = sorted(issues, key=lambda x: int(x.get("mention_score", 0)), reverse=True)
    for i in issues:
        score = i.get("mention_score", 0)

        # 신규 스키마: issue_title + issue_detail 분리
        # 구버전(issue 단일 필드) 폴백 처리
        if "issue_title" in i:
            title_text  = clean(i.get("issue_title", ""))
            detail_text = clean(i.get("issue_detail", ""))
            url = i.get("ref_url", "")
        else:
            title_text, url = extract_url(i.get("issue", ""))
            if not url:
                url = i.get("ref_url", "")
            detail_text = ""

        lk = link_btn(url)
        detail_html = (
            f"<div style='font-size:0.88rem;color:#555;line-height:1.6;margin-top:6px;'>"
            f"{detail_text}{lk}</div>"
        ) if detail_text else lk

        st.markdown(
            f"<div style='background:#f8f9fa;border:1px solid #dee2e6;"
            f"border-radius:8px;padding:14px 18px;margin-bottom:10px;'>"
            f"<div style='margin-bottom:6px;'>{score_badge_html(score)}"
            f"<span style='font-size:0.8rem;color:#888;margin-left:8px;'>{SCORE_BASED_ON_FREQ}</span>"
            f"</div>"
            f"<div style='font-size:0.98rem;color:#1e2129;font-weight:700;line-height:1.5;'>"
            f"{title_text}</div>"
            f"{detail_html}"
            f"</div>",
            unsafe_allow_html=True,
        )


# ── 탭 3: 불만 분석 ──────────────────────────────────────────────
def render_tab_complaints(ins):
    st.markdown(f"### ⚠️ {COMPLAINT_TITLE}")
    st.markdown(COMPLAINT_SCORE_BOX, unsafe_allow_html=True)

    comp = ins.get("complaint_analysis", {})
    if not comp:
        st.info(COMPLAINT_NO_DATA)
        return

    labels = [COMPLAINT_CATEGORIES[k]["label"] for k in COMPLAINT_CATEGORIES]
    scores = [max(0, min(10, int(comp.get(k, {}).get("score", 0)))) for k in COMPLAINT_CATEGORIES]

    fig = go.Figure(go.Scatterpolar(
        r=scores + [scores[0]],
        theta=labels + [labels[0]],
        fill="toself",
        fillcolor="rgba(59,72,144,0.15)",
        line=dict(color="#3b4890", width=2),
        name=COMPLAINT_RADAR_NAME,
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(
            visible=True, range=[0, 10],
            tickvals=[0, 2, 4, 6, 8, 10],
            tickfont=dict(size=10),
        )),
        height=320,
        margin=dict(l=48, r=48, t=24, b=24),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("---")

    # 점수 내림차순 정렬 (#11)
    sorted_categories = sorted(
        COMPLAINT_CATEGORIES.items(),
        key=lambda kv: max(0, min(10, int(comp.get(kv[0], {}).get("score", 0)))),
        reverse=True,
    )

    for ck, ci in sorted_categories:
        d     = comp.get(ck, {})
        score = max(0, min(10, int(d.get("score", 0))))
        summ  = clean(d.get("summary", COMPLAINT_NO_SUMMARY))
        ex    = clean(d.get("example", ""))

        hc, sc_col = st.columns([4, 1])
        with hc:
            st.markdown(f"**{ci['emoji']} {ci['label']}**")
        with sc_col:
            st.markdown(complaint_badge_html(score), unsafe_allow_html=True)

        # 모든 카테고리 기본 접힘 (#10), 점수 7 이상만 기본 열림
        with st.expander(summ, expanded=(score >= 7)):
            if ex:
                lk = link_btn(d.get("example_url", ""))
                st.markdown(
                    f"<div style='background:#f8f9fa;border-left:3px solid #dee2e6;"
                    f"padding:10px 14px;border-radius:4px;font-size:0.9rem;"
                    f"line-height:1.6;margin:8px 4px 4px 4px;'>"
                    f"{COMPLAINT_EXAMPLE_LABEL} {ex} {lk}</div>",
                    unsafe_allow_html=True,
                )


# ── 탭 4: 원본 데이터 ────────────────────────────────────────────
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
        with st.expander(RAW_DATE_GROUP_TMPL.format(date=date, count=len(groups[date])), expanded=False):
            for p in groups[date]:
                badge = RAW_BADGE_HIGH_ENG if p.get("comment_count", 0) >= 5 else RAW_BADGE_NORMAL
                meta  = RAW_POST_META_TMPL.format(
                    count=p.get("comment_count", 0),
                    utype=p.get("user_type", ""),
                )
                url   = p.get("post_url", "")
                title = p.get("title", "")
                tp    = f"[{title}]({url})" if url and url.startswith("http") else title
                st.markdown(f"- {badge} {tp} {meta}")


# ── 액션바 ───────────────────────────────────────────────────────
def render_action_bar():
    st.divider()
    with st.container(border=True):
        st.markdown(ACTIONBAR_TITLE)
        btn_pub = st.button(PUBLISH_BTN, use_container_width=True, type="primary")
        btn_new = st.button(NEW_ANALYSIS_BTN, use_container_width=True)
    return btn_new, btn_pub


# ── 갤러리 유형 기준 (공유 렌더러) ──────────────────────────────
def render_subtype_modal_content():
    st.markdown(SUBTYPE_MODAL_DESC)
    for s in SUBTYPE_DEFINITIONS:
        with st.expander(f"{s['emoji']} **{s['label']}** — {s['desc']}", expanded=False):
            st.markdown(f"{SUBTYPE_CRITERIA_PREFIX} {s['criteria']}")
            st.markdown(f"{SUBTYPE_FOCUS_PREFIX} {s['focus']}")