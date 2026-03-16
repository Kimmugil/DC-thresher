import streamlit as st
import random
import time
import threading
from config import APP_VERSION, NOTION_PUBLISH_URL, GEMINI_API_KEY, NOTION_TOKEN, TICKER_INTERVAL, ENV_NAME
from dc_scraper import run_dc_scraper, parse_dc_url
from ai_analyzer import analyze_with_gemini
# from notion_exporter import upload_to_notion # 이 부분은 나중에 노션 로직 수정 후 연결

st.set_page_config(page_title="디시인사이드 갤러리 탈곡기", page_icon="🚜", layout="wide")

# CSS 주입 (기존과 동일)
st.markdown("""
    <style>
        .fixed-banner {
            position: fixed; top: 0; left: 0; width: 100%;
            background-color: #3b4890; color: white; text-align: center;
            padding: 8px; font-weight: bold; z-index: 9999;
        }
        .main .block-container { padding-top: 50px; }
        .stats-card {
            background-color: #1e2129; padding: 20px; border-radius: 12px;
            border-left: 5px solid #3b4890; margin-bottom: 15px;
        }
    </style>
""", unsafe_allow_html=True)

if ENV_NAME == "DEV":
    st.markdown('<div class="fixed-banner">🚧 개발 환경 (DEV MODE)</div>', unsafe_allow_html=True)

def render_step_indicator(current_step):
    progress_val = int((current_step + 1) * 33.3)
    st.progress(progress_val)
    cols = st.columns(3)
    steps = ["1️⃣ 갤러리 입력", "2️⃣ 리포트 검수", "3️⃣ 노션 발행"]
    for i, col in enumerate(cols):
        is_current = (i == current_step)
        color = "#3b4890" if is_current else ("#888" if i < current_step else "#444")
        weight = "bold" if is_current else "normal"
        col.markdown(f"<div style='text-align: center; color: {color}; font-weight: {weight};'> {steps[i]} </div>", unsafe_allow_html=True)
    st.write("")

def main():
    if "step" not in st.session_state:
        st.session_state.step = 0
        st.session_state.update({"gallery_id": None, "insights": None, "post_data": None})

    st.title("🚜 디시인사이드 갤러리 탈곡기")
    st.markdown("디시 갤러리 URL을 입력하면 갤러리 여론과 민심을 탈탈 털어 분석해 드립니다.")
    st.write("")
    render_step_indicator(st.session_state.step)

    # ---------------------------------------------------------
    # Step 0: URL 입력 및 크롤링/분석
    # ---------------------------------------------------------
    if st.session_state.step == 0:
        with st.container(border=True):
            st.subheader("🎯 Step 1. 분석 대상 입력")
            raw_input = st.text_input("디시인사이드 갤러리 URL 입력", placeholder="https://gall.dcinside.com/mgallery/board/lists/?id=projectnakwon", label_visibility="collapsed")
            
            if st.button("🚀 데이터 수집 및 분석 시작", use_container_width=True, type="primary"):
                gal_type, gal_id = parse_dc_url(raw_input)
                if not gal_id: 
                    st.warning("유효한 디시인사이드 갤러리 URL을 입력해 주세요."); return
                
                with st.status(f"[{gal_id}] 갤러리 민심 수집 및 분석 중... 🌾", expanded=True) as status:
                    p_bar = st.progress(0); info_txt = st.empty()
                    
                    # 1. 스크래핑 진행
                    info_txt.write("🔍 1/3: 갤러리 최신 개념글/게시글 긁어오는 중...")
                    try:
                        # 💡 일단 10개만 테스트로 수집! (원하면 늘려도 됨)
                        scraper_result = run_dc_scraper(raw_input, max_posts=10)
                        post_data = scraper_result['data']
                    except Exception as e:
                        status.update(label="수집 에러", state="error")
                        st.error(f"스크래핑 실패: {e}"); return
                        
                    p_bar.progress(40)
                    
                    # 2. AI 분석 진행
                    info_txt.write("🧠 2/3: AI 갤러리 여론 다차원 분석 중...")
                    ticker = st.empty()
                    res_box = [None, None]
                    event = threading.Event()
                    
                    def run_ai():
                        try:
                            res_box[0], res_box[1] = analyze_with_gemini(gal_id, post_data)
                        except Exception as ex: 
                            res_box[1] = str(ex)
                        finally: 
                            event.set()
                            
                    threading.Thread(target=run_ai).start()
                    
                    waiting_msgs = ["유동 형님들 의견 취합 중...", "고닉들 민심 스캔 중...", "분탕글 필터링 중...", "주요 논란거리 요약 중..."]
                    while not event.is_set():
                        ticker.info(f"💡 {random.choice(waiting_msgs)}")
                        time.sleep(TICKER_INTERVAL)
                        
                    if res_box[1]: 
                        status.update(label="분석 에러", state="error")
                        st.error(f"AI 분석 실패: {res_box[1]}"); return

                    # 3. 분석 완료
                    st.session_state.update({
                        "gallery_id": gal_id, 
                        "insights": res_box[0], 
                        "post_data": post_data
                    })
                    
                    ticker.empty(); info_txt.write("✅ 3/3: 분석 완료!"); p_bar.progress(100)
                    st.session_state.step = 1; status.update(label="✅ 분석 완료", state="complete"); st.rerun()

    # ---------------------------------------------------------
    # Step 1: 분석 리포트 화면 검수 (웹 초안)
    # ---------------------------------------------------------
    elif st.session_state.step == 1:
        st.subheader(f"Step 2. [{st.session_state.gallery_id} 갤러리] 리포트 검수")
        ins = st.session_state.insights
        
        tab1, tab2, tab3 = st.tabs(["📊 주요 민심 요약", "👥 유동 vs 고닉 분석", "🔍 수집 데이터 원본"])
        
        with tab1:
            st.markdown(f'<div class="stats-card"><b>💬 갤러리 한줄평:</b><br>{ins.get("critic_one_liner", "")}</div>', unsafe_allow_html=True)
            st.info(f"💡 **현재 여론 요약:** {ins.get('sentiment_analysis', '')}")
            st.markdown("---")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("##### 📈 긍정적 여론")
                for line in ins.get('final_summary_all', []): 
                    if "[긍정]" in line: st.write(f"🟢 {line.replace('[긍정]', '').strip()}")
            with c2:
                st.markdown("##### 📉 부정적/불만 여론")
                for line in ins.get('final_summary_all', []): 
                    if "[부정]" in line: st.write(f"🔴 {line.replace('[부정]', '').strip()}")
            
            st.divider()
            st.markdown("### 🚨 현재 갤러리 주요 떡밥 (이슈 픽)")
            for issue in ins.get('ai_issue_pick', []): st.write(f"🔥 {issue}")

        with tab2:
            st.markdown("### 👥 작성자 유형별 교차 분석")
            user_analysis = ins.get('user_type_analysis', {})
            
            st.warning("**⚖️ 핵심 인사이트 (고닉 vs 유동)**\n\n" + "\n".join([f"- {i}" for i in user_analysis.get('comparison_insights', [])]))
            
            p1, p2 = st.columns(2)
            with p1:
                st.markdown("**🛡️ 정보/개념글 위주 (고닉/반고닉 주류)**")
                for l in user_analysis.get('high_quality_posts', []): st.write(f"- {l}")
            with p2:
                st.markdown("**🌪️ 일반 갤러들 분위기 (유동 주류)**")
                for l in user_analysis.get('general_opinion', []): st.write(f"- {l}")

        with tab3:
            st.markdown(f"**총 {len(st.session_state.post_data)}개의 게시글 데이터를 기반으로 분석했습니다.**")
            for p in st.session_state.post_data:
                st.write(f"- **{p['title']}** (💬 댓글: {p['comment_count']}개 / 👤 {p['author']})")

        st.divider()
        with st.container(border=True):
            st.markdown("### 📝 최종 검수 및 노션 전송")
            feedback = st.text_area("수정 요청 사항 (선택)", placeholder="특정 논란거리에 대해 더 자세히 분석해 줘 등 추가 지시...", label_visibility="collapsed")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 피드백 반영 재분석", use_container_width=True):
                    with st.status("분석 업데이트 중..."):
                        res, err = analyze_with_gemini(st.session_state.gallery_id, st.session_state.post_data, feedback)
                        if err: st.error(err); st.stop()
                        st.session_state.insights = res; st.rerun()
            with col2:
                if st.button("📤 노션 리포트 최종 발행", type="primary", use_container_width=True):
                    # 🚀 이 부분은 다음 단계에서 노션 모듈을 고친 후 연결할게!
                    st.info("아직 노션 전송 모듈이 디시 버전에 맞게 수정되지 않았어! 다음 스텝에서 연결하자!")

if __name__ == "__main__": main()
