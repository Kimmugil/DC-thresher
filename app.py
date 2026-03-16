import streamlit as st
import pandas as pd
import random
import time
import threading
import re
from config import APP_VERSION, TICKER_INTERVAL, ENV_NAME
from dc_scraper import run_dc_scraper, parse_dc_url
from ai_analyzer import analyze_with_gemini
from notion_exporter import upload_to_notion

st.set_page_config(page_title="디시인사이드 갤러리 탈곡기", page_icon="🚜", layout="wide")

st.markdown("""
    <style>
        .fixed-banner { position: fixed; top: 0; left: 0; width: 100%; background-color: #3b4890; color: white; text-align: center; padding: 8px; font-weight: bold; z-index: 9999; }
        .main .block-container { padding-top: 50px; }
        .stats-card { background-color: #f0f2f6; color: #1e2129; padding: 20px; border-radius: 12px; border-left: 5px solid #3b4890; margin-bottom: 15px; }
        [data-theme="light"] .stats-card { background-color: #ffffff; border: 1px solid #ddd; color: #1e2129; }
        .ai-one-liner { font-size: 1.25rem; font-weight: bold; color: #3b4890 !important; }
        .stMarkdown p { line-height: 1.6; }
    </style>
""", unsafe_allow_html=True)

if ENV_NAME == "DEV":
    st.markdown('<div class="fixed-banner">🚧 개발 환경 (DEV MODE) - 로컬 테스트 환경입니다.</div>', unsafe_allow_html=True)

def render_step_indicator(current_step):
    st.progress(int((current_step + 1) * 33.3))
    cols = st.columns(3)
    steps = ["1️⃣ 갤러리 입력", "2️⃣ 리포트 검수", "3️⃣ 노션 발행"]
    for i, col in enumerate(cols):
        color = "#3b4890" if (i == current_step) else ("#888" if i < current_step else "#444")
        weight = "bold" if (i == current_step) else "normal"
        col.markdown(f"<div style='text-align: center; color: {color}; font-weight: {weight};'> {steps[i]} </div>", unsafe_allow_html=True)
    st.write("")

def main():
    if "step" not in st.session_state:
        st.session_state.step = 0
        st.session_state.update({"gallery_id": None, "gallery_name": None, "insights": None, "post_data": None, "date_range_str": ""})

    st.title("🚜 디시인사이드 갤러리 탈곡기")
    st.write("")
    render_step_indicator(st.session_state.step)

    if st.session_state.step == 0:
        with st.container(border=True):
            st.subheader("🎯 Step 1. 분석 대상 입력")
            st.markdown("**동향이 궁금한 갤러리의 URL을 입력하세요!**")
            raw_input = st.text_input("디시인사이드 갤러리 URL 입력", placeholder="https://gall.dcinside.com/mgallery/board/lists/?id=projectnakwon", label_visibility="collapsed")
            
            st.markdown("<br>**수집할 게시글 수량을 선택하세요.**", unsafe_allow_html=True)
            post_options = {
                50: "50개 (초소형 갤러리 추천 / 예상 소요시간: 약 1~2분)",
                100: "100개 (소형 갤러리 추천 / 예상 소요시간: 약 2~3분)",
                200: "200개 (중형 갤러리 추천 / 예상 소요시간: 약 4~5분)",
                300: "300개 (중대형 갤러리 추천 / 예상 소요시간: 약 6~8분)",
                400: "400개 (대형 갤러리 추천 / 예상 소요시간: 약 8~10분)",
                500: "500개 (초대형 흥한갤 추천 / 예상 소요시간: 약 10~15분)"
            }
            selected_max_posts = st.selectbox(
                "수집 수량",
                options=list(post_options.keys()),
                format_func=lambda x: post_options[x],
                index=1,
                label_visibility="collapsed"
            )
            st.caption("* 참고: 최근 30일 내 작성된 글 수가 선택한 수량보다 적을 경우, 수집 가능한 만큼의 데이터만으로 분석을 진행합니다.")
            st.write("")

            if st.button("🚀 데이터 수집 및 분석 시작", use_container_width=True, type="primary"):
                gal_type, gal_id = parse_dc_url(raw_input)
                if not gal_id: st.warning("유효한 디시인사이드 갤러리 URL을 입력해 주세요."); return
                
                with st.status("데이터 탈곡 진행 중... 🌾", expanded=True) as status:
                    p_bar = st.progress(0); info_txt = st.empty()
                    
                    def scraper_progress(msg, p_val=None):
                        info_txt.markdown(f"**🔍 1/3:** {msg}")
                        if p_val is not None: p_bar.progress(p_val)
                    
                    try:
                        scraper_result = run_dc_scraper(raw_input, max_posts=selected_max_posts, days_limit=30, progress_cb=scraper_progress)
                        post_data = scraper_result['data']
                        
                        # 💡 [핵심] 수집된 데이터에서 실제 날짜 범위(시작일~종료일) 계산
                        dates = [p.get('date') for p in post_data if p.get('date')]
                        if dates:
                            dates.sort()
                            date_range_str = f"{dates[0]} ~ {dates[-1]}"
                        else:
                            date_range_str = "기간 알 수 없음"
                            
                    except Exception as e:
                        status.update(label="수집 에러", state="error"); st.error(f"스크래핑 실패: {e}"); return
                        
                    p_bar.progress(95)
                    info_txt.markdown("**🧠 2/3:** AI 트렌드 및 체크포인트 다차원 분석 중...")
                    ticker = st.empty(); res_box = [None, None]; event = threading.Event()
                    
                    def run_ai():
                        try: res_box[0], res_box[1] = analyze_with_gemini(gal_id, post_data)
                        except Exception as ex: res_box[1] = str(ex)
                        finally: event.set()
                    threading.Thread(target=run_ai).start()
                    
                    msgs = ["키워드 연관성 분석 중...", "게시물 급증 원인(스파이크) 파악 중...", "이슈 전후 여론 비교 중...", "PM을 위한 제안 도출 중..."]
                    while not event.is_set():
                        ticker.info(f"💡 {random.choice(msgs)}"); time.sleep(TICKER_INTERVAL)
                        
                    if res_box[1]: status.update(label="분석 에러", state="error"); st.error(f"AI 분석 실패: {res_box[1]}"); return

                    st.session_state.update({"gallery_id": gal_id, "gallery_name": scraper_result['gallery_name'], "insights": res_box[0], "post_data": post_data, "date_range_str": date_range_str})
                    ticker.empty(); info_txt.markdown(f"**✅ 3/3:** 분석 완료! (수집된 글: {len(post_data)}개)"); p_bar.progress(100)
                    st.session_state.step = 1; status.update(label="✅ 분석 완료", state="complete"); st.rerun()

    elif st.session_state.step == 1:
        st.subheader(f"Step 2. [{st.session_state.gallery_name}] 주요 동향 리포트")
        st.markdown(f"**🗓️ 분석 대상 기간:** `{st.session_state.date_range_str}`")
        ins = st.session_state.insights
        tab1, tab2, tab3 = st.tabs(["📊 핵심 요약 및 트렌드", "✅ AI픽 체크리스트", "🔍 수집 데이터 원본"])
        
        with tab1:
            st.markdown(f'<div class="stats-card"><b>💬 AI 한줄평:</b><br><span class="ai-one-liner">{ins.get("critic_one_liner", "")}</span></div>', unsafe_allow_html=True)
            st.info(f"🏷️ **핵심 키워드 TOP 5:** {', '.join(ins.get('top_keywords', []))}")
            st.markdown("---")
            
            st.markdown("### 📊 수집 기간 내 개념글 수 추이")
            if st.session_state.post_data:
                concept_posts = [p for p in st.session_state.post_data if p.get('is_concept')]
                df = pd.DataFrame(concept_posts)
                if 'date' in df.columns and not df.empty:
                    trend_df = df.groupby('date').size().reset_index(name='개념글 수')
                    st.bar_chart(trend_df.set_index('date'), color="#ff6b6b")
                else:
                    st.write("수집된 개념글 데이터가 부족하여 차트를 생성할 수 없습니다.")
            
            st.markdown("### 📈 트렌드 스파이크 및 여론 온도 변화")
            st.markdown("**🌡️ 여론 온도 변화:**")
            
            # 여기서도 세로쓰기 에러 나지 않도록 방어
            def get_safe_list(data):
                if isinstance(data, list): return data
                if isinstance(data, dict): return list(data.values())
                if isinstance(data, str): return [data]
                return []

            for line in get_safe_list(ins.get('sentiment_tracker')): 
                st.markdown(f"- {re.sub(r'\[([^\]]+)\]\(([^)]+)\)', '', line).strip()}")
                
            st.markdown("**🔥 스파이크 원인:**")
            for line in get_safe_list(ins.get('trend_spike_analysis')): 
                st.markdown(f"- {re.sub(r'\[([^\]]+)\]\(([^)]+)\)', '', line).strip()}")
            st.divider()
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("##### 🟢 긍정적 여론")
                for line in get_safe_list(ins.get('final_summary_all')): 
                    if "[긍정]" in line: st.markdown(f"- {re.sub(r'\[([^\]]+)\]\(([^)]+)\)', '', line).replace('[긍정]', '').strip()}")
            with c2:
                st.markdown("##### 🔴 부정적/불만 여론")
                for line in get_safe_list(ins.get('final_summary_all')): 
                    if "[부정]" in line: st.markdown(f"- {re.sub(r'\[([^\]]+)\]\(([^)]+)\)', '', line).replace('[부정]', '').strip()}")

        with tab2:
            st.markdown("### 🚨 [AI픽 체크리스트] 주요 동향 기반 대응 제안")
            for issue in get_safe_list(ins.get('ai_pick_checklist')): 
                clean_issue = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', '', issue).strip()
                st.markdown(f"✅ {clean_issue}")
            st.divider()
            st.markdown("### 👥 세부 민심 요약")
            user_analysis = ins.get('user_type_analysis', {})
            st.markdown("**🛡️ 주요 정보성/분석글**")
            for l in get_safe_list(user_analysis.get('high_quality_posts')): 
                st.markdown(f"- {re.sub(r'\[([^\]]+)\]\(([^)]+)\)', '', l).strip()}")
            st.markdown("**🌪️ 일반 갤러들 분위기**")
            for l in get_safe_list(user_analysis.get('general_opinion')): 
                st.markdown(f"- {re.sub(r'\[([^\]]+)\]\(([^)]+)\)', '', l).strip()}")

        with tab3:
            st.markdown(f"**해당 기간 기준 총 {len(st.session_state.post_data)}개의 유용한 데이터를 수집했습니다.**")
            for p in st.session_state.post_data:
                badge = "🔥[개념글]" if p.get('is_concept') else "💬[일반글]"
                st.markdown(f"- **[{p.get('date','')}] {badge} [{p['title']}]({p.get('post_url', '#')})** (댓글: {p.get('comment_count', 0)}개)")

        st.divider()
        with st.container(border=True):
            st.markdown("### 📝 최종 검수 및 노션 전송")
            feedback = st.text_area("수정 요청 사항 (선택)", placeholder="특정 날짜의 데이터만 다시 분석해 줘 등 추가 지시...", label_visibility="collapsed")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 피드백 반영 재분석", use_container_width=True):
                    with st.status("분석 업데이트 중..."):
                        res, err = analyze_with_gemini(st.session_state.gallery_id, st.session_state.post_data, feedback)
                        if err: st.error(err); st.stop()
                        st.session_state.insights = res; st.rerun()
            with col2:
                if st.button("📤 노션 리포트 최종 발행", type="primary", use_container_width=True):
                    with st.status("노션 페이지 생성 중..."):
                        pid = upload_to_notion(st.session_state.gallery_name, st.session_state.post_data, st.session_state.insights, st.session_state.date_range_str)
                        st.session_state.page_id = pid; st.session_state.step = 2; st.rerun()

    elif st.session_state.step == 2:
        st.balloons(); st.success("🎉 노션 주요 동향 리포트 발행 완료!")
        p_url = f"https://notion.so/{st.session_state.page_id.replace('-', '')}"
        st.markdown(f'<div style="padding:30px; border-radius:15px; background-color:#1e2129; text-align:center;"><a href="{p_url}" target="_blank" style="font-size:1.5em; color:#3b4890; font-weight:bold; text-decoration:none;">🔗 생성된 노션 리포트 확인</a></div>', unsafe_allow_html=True)
        if st.button("🔄 다른 갤러리 분석하기", use_container_width=True):
            for k in [k for k in st.session_state.keys() if k != 'history']: del st.session_state[k]
            st.rerun()

if __name__ == "__main__": main()