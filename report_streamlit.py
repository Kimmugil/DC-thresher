"""
report_streamlit.py v9
- 현황 탭 긍정/부정 위로 이동 및 관련 게시글 링크 추가
- 이슈 리스트 점수 툴팁 하단 박스로 분리
- 불만 분석 토글 제목을 요약으로, '관련 여론' 및 링크 적용
- 마크다운 (**, ~) 완전 제거 함수 적용
- 기간/글수 안내 문구 적용
"""
import streamlit as st
import plotly.graph_objects as go
import re
from collections import defaultdict
from config import COMPLAINT_CATEGORIES, GALLERY_SUBTYPES
from ui_texts import (
    TAB_LABELS, COMPLAINT_TITLE, COMPLAINT_NO_DATA, COMPLAINT_RADAR_NAME,
    COMPLAINT_NO_SUMMARY, COMPLAINT_SUMMARY_LABEL, COMPLAINT_EXAMPLE_LABEL,
    RAW_TITLE_TMPL, RAW_ALL_TITLE, RAW_DATE_GROUP_TMPL, RAW_BADGE_CONCEPT, RAW_BADGE_NORMAL, RAW_POST_META_TMPL, RAW_NO_DATE_LABEL,
    ACTIONBAR_TITLE, PUBLISH_BTN, NEW_ANALYSIS_BTN, PROFILE_KEYWORD_TMPL, PROFILE_ONELINER_PREFIX,
    TIMELINE_CHART_TITLE, TIMELINE_NO_DATA, ISSUE_TITLE, ISSUE_NO_DATA, SCORE_BASED_ON_FREQ, COMPLAINT_SCORE_BOX, ISSUE_SCORE_BOX,
    ANALYSIS_SPEC_TMPL
)

def _strip_md(t):
    """마크다운 기호를 완전히 삭제하여 노출 오류를 막습니다."""
    s = str(t)
    s = s.replace("**", "").replace("*", "").replace("~~", "").replace("~", "")
    return s

def _clean(t): 
    return _strip_md(re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", str(t)))

def _extract_url(t):
    m = re.search(r"\[([^\]]+)\]\((https?://[^)]+)\)", str(t))
    return (m.group(1), m.group(2)) if m else (_clean(t), "")

def _link(url, label, color="#3b4890"):
    if not url or not url.startswith("http"): return ""
    return f"<a href='{url}' target='_blank' style='font-size:0.78rem;color:{color};text-decoration:none;border:1px solid {color};border-radius:4px;padding:2px 6px;margin-left:6px;'>{label}</a>"

def _badge(score):
    score = max(0, min(100, int(score))) 
    bg, fc = ("#fde8e8", "#c0392b") if score >= 80 else ("#fef3cd", "#e67e22") if score >= 50 else ("#e8f4fd", "#2980b9")
    return f"<span style='background:{bg};color:{fc};font-weight:700;padding:3px 10px;border-radius:12px;font-size:0.9rem;'>{score}점</span>"

def render_gallery_profile(ins, scrape_result, game_name, subtype_id):
    sub = GALLERY_SUBTYPES.get(subtype_id, GALLERY_SUBTYPES["stable"])
    dr  = scrape_result.get("date_range_str","")
    tot = scrape_result.get("total_posts",0)
    core = scrape_result.get("core_posts", scrape_result.get("analysis_count",0))
    sc = sub["color"]

    st.markdown(
        f"<div style='display:flex;align-items:center;gap:12px;margin-bottom:6px;'>"
        f"<h2 style='margin:0;font-size:1.5rem;'>{sub['emoji']} {game_name} 분석 리포트</h2>"
        f"<span style='padding:4px 12px;border-radius:20px;background:{sc}22;border:1px solid {sc};font-size:0.82rem;font-weight:700;color:{sc};white-space:nowrap;'>{sub['label']}</span>"
        f"</div>", unsafe_allow_html=True)
    
    spec_text = ANALYSIS_SPEC_TMPL.format(date_range=dr, total=tot, analysis=core)
    st.markdown(
        f"<div style='background:#eef0fa;border-left:4px solid #3b4890;border-radius:6px;padding:8px 14px;margin-bottom:10px;'>"
        f"<span style='font-size:0.9rem;color:#1e2129;'>{spec_text}</span></div>", unsafe_allow_html=True)

    one_liner = _clean(ins.get("critic_one_liner",""))
    if one_liner:
        st.markdown(f"<div style='padding:14px 18px;border-radius:10px;background:#f0f2f6;border-left:5px solid #3b4890;margin-bottom:10px;font-size:1.05rem;font-weight:bold;'>{PROFILE_ONELINER_PREFIX} {one_liner}</div>", unsafe_allow_html=True)
    kws = ins.get("top_keywords",[])
    if kws: st.info(PROFILE_KEYWORD_TMPL.format(keywords=" · ".join(kws[:5])))

# ── 탭 1: 갤러리 현황 (긍정/부정 먼저) ──
def render_tab_overview(ins, scrape_result):
    st.markdown("### 💬 긍정 및 부정 여론 요약")
    sent = ins.get("sentiment_summary", {})
    pos = sent.get("positive", [])
    neg = sent.get("negative", [])

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### 🟢 주요 긍정 여론")
        if pos:
            for p in pos: 
                summ = _clean(p.get("summary", ""))
                url = p.get("ref_url", "")
                lk = _link(url, "📎 관련 게시글 보기", "#2980b9") if url else ""
                st.markdown(f"- {summ} {lk}", unsafe_allow_html=True)
        else: st.info("긍정 여론이 없습니다.")
    with c2:
        st.markdown("##### 🔴 주요 부정 여론")
        if neg:
            for n in neg: 
                summ = _clean(n.get("summary", ""))
                url = n.get("ref_url", "")
                lk = _link(url, "📎 관련 게시글 보기", "#2980b9") if url else ""
                st.markdown(f"- {summ} {lk}", unsafe_allow_html=True)
        else: st.info("부정 여론이 없습니다.")

    st.divider()

    st.markdown(f"### 📊 {TIMELINE_CHART_TITLE}")
    dc14 = scrape_result.get("date_counts_14") or scrape_result.get("date_counts", {})
    if dc14:
        dates14 = sorted(dc14.keys())
        counts14 = [dc14[d] for d in dates14]
        fig = go.Figure(go.Bar(
            x=dates14, y=counts14, marker=dict(color="#3b4890", line=dict(width=0)),
            hovertemplate="<b>%{x}</b><br>%{y}개<extra></extra>"
        ))
        n = len(dates14); tick_step = max(1, n // 7)
        fig.update_layout(
            height=280, margin=dict(l=0,r=0,t=20,b=20),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, tickangle=-45, tickmode="array", tickvals=dates14[::tick_step], ticktext=dates14[::tick_step], tickfont=dict(size=11), fixedrange=True),
            yaxis=dict(title="게시글 수", gridcolor="#f1f3f5", fixedrange=True, tickfont=dict(size=11)),
            dragmode=False, showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False,"scrollZoom":False})
    else: st.info(TIMELINE_NO_DATA)

# ── 탭 2: 주요 이슈 (안내박스 적용) ──
def render_tab_issues(ins):
    st.markdown(ISSUE_TITLE)
    issues = ins.get("major_issues", [])
    if issues:
        issues = sorted(issues, key=lambda x: int(x.get("mention_score", 0)), reverse=True)
        for i in issues:
            score = i.get("mention_score", 0)
            text, url = _extract_url(i.get("issue",""))
            if not url: url = i.get("ref_url", "")
            lk = _link(url, "📎 관련 게시글 보기", "#2980b9") if url else ""
            st.markdown(
                f"<div style='background:#f8f9fa;border:1px solid #dee2e6;border-radius:8px;padding:12px 16px;margin-bottom:10px;'>"
                f"<div style='margin-bottom:6px;'>{_badge(score)} <span style='font-size:0.8rem;color:#888;'>{SCORE_BASED_ON_FREQ}</span></div>"
                f"<div style='font-size:0.95rem;color:#1e2129;font-weight:500;line-height:1.5;'>{text}{lk}</div></div>",
                unsafe_allow_html=True)
        st.markdown(ISSUE_SCORE_BOX, unsafe_allow_html=True)
    else: st.info(ISSUE_NO_DATA)

# ── 탭 3: 불만 분석 (요약 토글화 및 관련여론 적용) ──
def render_tab_complaints(ins):
    st.markdown(f"### ⚠️ {COMPLAINT_TITLE}")
    st.markdown(COMPLAINT_SCORE_BOX, unsafe_allow_html=True)

    comp = ins.get("complaint_analysis",{})
    if not comp: st.info(COMPLAINT_NO_DATA); return

    labels = [COMPLAINT_CATEGORIES[k]["label"] for k in COMPLAINT_CATEGORIES]
    scores = [max(0, min(10, int(comp.get(k,{}).get("score",0)))) for k in COMPLAINT_CATEGORIES]

    fig = go.Figure(go.Scatterpolar(
        r=scores+[scores[0]], theta=labels+[labels[0]], fill="toself", fillcolor="rgba(59,72,144,0.15)",
        line=dict(color="#3b4890",width=2), name=COMPLAINT_RADAR_NAME))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10], tickvals=[0,2,4,6,8,10], tickfont=dict(size=10))),
        height=280, margin=dict(l=40,r=40,t=20,b=20), paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    for ck, ci in COMPLAINT_CATEGORIES.items():
        d = comp.get(ck,{})
        score = max(0, min(10, int(d.get("score",0))))
        summ = _clean(d.get("summary",COMPLAINT_NO_SUMMARY))
        ex = _clean(d.get("example",""))
        bg, fc = ("#fde8e8", "#c0392b") if score >= 7 else ("#fef3cd", "#e67e22") if score >= 4 else ("#e8f4fd", "#2980b9")
        
        hc, sc_col = st.columns([4,1])
        with hc: st.markdown(f"**{ci['emoji']} {ci['label']}**")
        with sc_col: st.markdown(f"<span style='background:{bg};color:{fc};font-weight:700;padding:3px 10px;border-radius:12px;font-size:0.9rem;'>{score}/10</span>", unsafe_allow_html=True)
        
        # 요약을 토글 제목으로 사용
        with st.expander(summ, expanded=(score>=5)):
            if ex:
                ex_url = d.get("example_url","")
                lk = _link(ex_url, "📎 관련 게시글 보기", "#2980b9") if ex_url else ""
                st.markdown(f"<div style='background:#f8f9fa;border-left:3px solid #dee2e6;padding:8px 12px;border-radius:4px;margin-top:6px;'>{COMPLAINT_EXAMPLE_LABEL} {ex} {lk}</div>", unsafe_allow_html=True)
        st.write("")

# ── 탭 4: 원본 데이터 ──
def render_tab_raw(scrape_result):
    total = scrape_result.get("total_posts",0); analysis = scrape_result.get("core_posts",scrape_result.get("analysis_count",0))
    all_m = scrape_result.get("all_metas",[])
    st.markdown(RAW_TITLE_TMPL.format(total=total,analysis=analysis))
    st.markdown(RAW_ALL_TITLE)
    groups = defaultdict(list)
    for m in all_m: groups[m.get("date",RAW_NO_DATE_LABEL)].append(m)
    for date in sorted(groups.keys(),reverse=True):
        with st.expander(RAW_DATE_GROUP_TMPL.format(date=date,count=len(groups[date])),expanded=False):
            for p in groups[date]:
                badge = RAW_BADGE_CONCEPT if p.get("is_concept") else RAW_BADGE_NORMAL
                meta = RAW_POST_META_TMPL.format(count=p.get("comment_count",0),utype=p.get("user_type",""))
                url = p.get("post_url",""); title = p.get("title","")
                tp = f"[{title}]({url})" if url and url.startswith("http") else title
                st.markdown(f"- {badge} {tp} {meta}")

def render_action_bar():
    st.divider()
    with st.container(border=True):
        st.markdown(ACTIONBAR_TITLE)
        c1, c2 = st.columns(2)
        with c1: btn_new = st.button(NEW_ANALYSIS_BTN, use_container_width=True)
        with c2: btn_pub = st.button(PUBLISH_BTN, use_container_width=True, type="primary")
        return btn_new, btn_pub