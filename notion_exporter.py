import requests
import json
import time
from datetime import datetime, timedelta, timezone
from config import NOTION_TOKEN, NOTION_DATABASE_ID, APP_VERSION

def format_sentiment_line(line):
    """[긍정], [부정] 키워드에 따라 노션 텍스트 색상을 입혀주는 포맷터"""
    if line.startswith("[긍정]"):
        return [{"text": {"content": "[긍정] "}, "annotations": {"color": "blue", "bold": True}}, {"text": {"content": line[4:].strip()}}]
    elif line.startswith("[부정]"):
        return [{"text": {"content": "[부정] "}, "annotations": {"color": "red", "bold": True}}, {"text": {"content": line[4:].strip()}}]
    return [{"text": {"content": line}}]

def get_bot_info_block(gallery_id):
    """봇 안내 및 출처 링크 블록"""
    return [
        {"object": "block", "type": "toggle", "toggle": {"rich_text": [{"text": {"content": "ℹ️ 봇 안내 및 데이터 출처 (클릭해서 펼치기)"}, "annotations": {"color": "gray", "bold": True}}], "children": [
            {"object": "block", "type": "callout", "callout": {"icon": {"emoji": "🚜"}, "color": "blue_background", "rich_text": [
                {"text": {"content": f"[{APP_VERSION}] 디시인사이드 갤러리 탈곡기\n"}, "annotations": {"bold": True, "color": "blue"}}, 
                {"text": {"content": "해당 리포트는 AI가 커뮤니티 민심을 객관적으로 요약한 결과입니다.\n"}}, 
                {"text": {"content": f"👉 {gallery_id} 갤러리 바로가기", "link": {"url": f"https://gall.dcinside.com/mgallery/board/lists/?id={gallery_id}"}}, "annotations": {"bold": True, "color": "blue", "underline": True}}
            ]}}
        ]}}, 
        {"object": "block", "type": "divider", "divider": {}}
    ]

def get_ai_one_liner_block(ai_data):
    """AI 한줄평 및 전체 여론 요약 블록"""
    return [
        {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "🤖 AI 갤러리 민심 한줄평"}}]}}, 
        {"object": "block", "type": "heading_3", "heading_3": {"rich_text": [{"text": {"content": f"❝ {ai_data.get('critic_one_liner', '')} ❞"}, "annotations": {"color": "blue"}}]}}, 
        {"object": "block", "type": "callout", "callout": {"icon": {"emoji": "💬"}, "color": "gray_background", "rich_text": [{"text": {"content": ai_data.get('sentiment_analysis', '')}}]}},
        {"object": "block", "type": "divider", "divider": {}}
    ]

def get_sentiment_summary_block(ai_data):
    """긍정/부정 핵심 여론 요약 블록"""
    blocks = [
        {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "📊 주요 여론 동향"}}]}}, 
    ]
    for line in ai_data.get('final_summary_all', []): 
        blocks.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": format_sentiment_line(line)}})
    blocks.append({"object": "block", "type": "divider", "divider": {}})
    return blocks

def get_user_type_block(ai_data):
    """유동 vs 고닉 여론 차이 분석 블록"""
    user_data = ai_data.get('user_type_analysis', {})
    if not user_data: return []
    
    blocks = [{"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "👥 작성자 유형별 교차 분석 (고닉 vs 유동)"}}]}}]
    
    # 핵심 인사이트 (비교)
    comparison = user_data.get('comparison_insights', [])
    if comparison:
        list_items = [{"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"text": {"content": line}}]}} for line in comparison if isinstance(line, str)]
        blocks.append({"object": "block", "type": "callout", "callout": {"icon": {"emoji": "⚖️"}, "color": "gray_background", "rich_text": [{"text": {"content": "핵심 인사이트"}, "annotations": {"bold": True}}], "children": list_items}})
        
    # 고닉 여론
    blocks.append({"object": "block", "type": "heading_3", "heading_3": {"rich_text": [{"text": {"content": "🛡️ 정보/개념글 위주 (고닉/반고닉 주류)"}, "annotations": {"color": "purple", "bold": True}}]}})
    for line in user_data.get('high_quality_posts', []): 
        blocks.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"text": {"content": line}}]}})
        
    # 유동 여론
    blocks.append({"object": "block", "type": "heading_3", "heading_3": {"rich_text": [{"text": {"content": "🌪️ 일반 갤러들 분위기 (유동 주류)"}, "annotations": {"color": "green", "bold": True}}]}})
    for line in user_data.get('general_opinion', []): 
        blocks.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"text": {"content": line}}]}})
        
    blocks.append({"object": "block", "type": "divider", "divider": {}})
    return blocks

def get_issue_pick_block(ai_data):
    """갤러리 내 주요 논란 및 떡밥 블록"""
    blocks = [{"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "🚨 [AI 떡밥 픽] 갤러리 핫이슈"}}]}}]
    for issue in ai_data.get('ai_issue_pick', []): 
        blocks.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"text": {"content": issue}}]}})
    blocks.append({"object": "block", "type": "divider", "divider": {}})
    return blocks

def upload_to_notion(gallery_id, post_data, ai_data):
    """생성된 데이터를 노션 페이지로 업로드합니다."""
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}", 
        "Content-Type": "application/json", 
        "Notion-Version": "2022-06-28"
    }
    
    # 💡 [핵심] KST (한국 시간) 보정 및 노션 Date 포맷 (년-월-일T시:분:초+09:00)
    kst = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst)
    iso_timestamp = now_kst.strftime('%Y-%m-%dT%H:%M:%S+09:00')
    
    # 노션 페이지 제목
    page_title = f"[{gallery_id}] 갤러리 민심 요약 리포트"
    
    # 무길이가 세팅한 DB 컬럼에 맞춘 메타데이터
    create_data = {
        "parent": {"database_id": NOTION_DATABASE_ID}, 
        "properties": {
            "이름": {"title": [{"text": {"content": page_title}}]},
            "수집 시점": {"date": {"start": iso_timestamp}},
            "DC탈곡기 버전": {"rich_text": [{"text": {"content": APP_VERSION}}]}
        }
    }
    
    try:
        res = requests.post("https://api.notion.com/v1/pages", headers=headers, data=json.dumps(create_data))
        res.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise Exception(f"노션 DB 연동 실패 (컬럼명/타입 불일치 의심): {e.response.text}")
        
    page_id = res.json()['id']
    
    # 본문 블록 조립
    children_blocks = []
    children_blocks.extend(get_bot_info_block(gallery_id))
    children_blocks.extend(get_ai_one_liner_block(ai_data))
    children_blocks.extend(get_sentiment_summary_block(ai_data))
    children_blocks.extend(get_issue_pick_block(ai_data))
    children_blocks.extend(get_user_type_block(ai_data))
    
    # 블록을 100개 단위로 쪼개서 노션에 이어붙이기 (노션 API 제한 우회)
    append_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    for i in range(0, len(children_blocks), 100):
        try:
            patch_res = requests.patch(append_url, headers=headers, data=json.dumps({"children": children_blocks[i:i+100]}))
            patch_res.raise_for_status() 
        except requests.exceptions.HTTPError as e:
            raise Exception(f"노션 블록 추가 실패: {e.response.text}")
        time.sleep(0.5)
        
    return page_id
