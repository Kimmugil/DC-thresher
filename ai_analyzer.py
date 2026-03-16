import requests
import json
from config import GEMINI_API_KEY
from prompts import build_dc_prompt

def analyze_with_gemini(gallery_id, post_data, user_feedback=""):
    """
    수집된 디시인사이드 게시글 데이터를 바탕으로 AI 분석 리포트를 생성합니다.
    """
    
    # AI 토큰 절약 및 프롬프트 구성을 위해 수집된 데이터를 문자열로 포맷팅
    formatted_posts = ""
    for idx, post in enumerate(post_data):
        # AI에게 댓글 수를 강조해서 전달 (화제성 판단 근거)
        formatted_posts += f"\n=== [게시글 {idx+1}] ===\n"
        formatted_posts += f"제목: {post.get('title', '')} (💬 댓글 수: {post.get('comment_count', 0)}개)\n"
        formatted_posts += f"작성자: {post.get('author', '')} ({post.get('user_type', '')})\n"
        # 텍스트가 너무 길면 잘리므로 최대 1000자까지만 자르기
        body_text = post.get('body', '')[:1000]
        formatted_posts += f"본문: {body_text}\n"

    # 프롬프트 빌드 (이전에 만든 build_dc_prompt 사용)
    prompt = build_dc_prompt(gallery_id, formatted_posts, user_feedback)
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}".strip()
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}], 
        "generationConfig": {
            "responseMimeType": "application/json", 
            "temperature": 0.1 # 환각 방지
        }
    }
    
    try:
        res = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'))
        res.raise_for_status()
        raw_text = res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        
        # 마크다운 백틱 우회 제거 로직 (안정성)
        bt = "`" * 3
        if raw_text.startswith(f"{bt}json"): raw_text = raw_text[7:]
        if raw_text.startswith(bt): raw_text = raw_text[3:]
        if raw_text.endswith(bt): raw_text = raw_text[:-3]
        raw_text = raw_text.strip()
        
        return json.loads(raw_text), None
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429: return None, "429 Client Error (API 호출량 초과)"
        return None, f"API 에러 ({e.response.status_code})"
    except json.JSONDecodeError as e:
        return None, f"JSON_DECODE_ERROR: {str(e)}"
    except Exception as e: 
        error_msg = str(e)
        if GEMINI_API_KEY and GEMINI_API_KEY in error_msg:
            error_msg = error_msg.replace(GEMINI_API_KEY, "********")
        return None, error_msg
