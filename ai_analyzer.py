import requests
import json
import re
from config import GEMINI_API_KEY
from prompts import build_dc_prompt

def analyze_with_gemini(gallery_id, post_data, user_feedback=""):
    formatted_posts = ""
    for idx, post in enumerate(post_data):
        badge = "🔥[개념글]" if post.get('is_concept') else "💬[일반글]"
        formatted_posts += f"\n=== {badge} [{idx+1}] ===\n"
        formatted_posts += f"제목: {post.get('title', '')} \n"
        formatted_posts += f"작성일자: {post.get('date', '')} \n"
        formatted_posts += f"URL: {post.get('post_url', '')} \n"
        formatted_posts += f"작성자/댓글수: {post.get('author', '')} ({post.get('user_type', '')}) / {post.get('comment_count', 0)}개\n"
        
        # 큰따옴표, 줄바꿈 등 JSON 파싱을 방해하는 요소 제거 후 삽입
        clean_body = post.get('body', '').replace('"', "'").replace('\n', ' ')
        formatted_posts += f"본문: {clean_body[:600]}\n"

    prompt = build_dc_prompt(gallery_id, formatted_posts, user_feedback)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}".strip()
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}], 
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1}
    }
    
    try:
        res = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'))
        res.raise_for_status()
        raw_text = res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        
        bt = chr(96) * 3
        if raw_text.startswith(f"{bt}json"): raw_text = raw_text[7:]
        if raw_text.startswith(bt): raw_text = raw_text[3:]
        if raw_text.endswith(bt): raw_text = raw_text[:-3]
        
        return json.loads(raw_text.strip(), strict=False), None
        
    except json.JSONDecodeError as je:
        return None, f"AI 분석 실패: JSON 데이터 형식이 깨졌습니다. (상세: {je})"
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429: return None, "429 Client Error (호출 한도 초과)"
        return None, f"API 에러 ({e.response.status_code})"
    except Exception as e: 
        err = str(e).replace(GEMINI_API_KEY, "********") if GEMINI_API_KEY else str(e)
        return None, err