import requests
import json
import time
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from config import NOTION_TOKEN, NOTION_DATABASE_ID, APP_VERSION

def get_safe_list(data):
    if isinstance(data, list): return [str(i) for i in data]
    if isinstance(data, dict): return [str(v) for v in data.values()]
    if isinstance(data, str): return [data]
    if data is None: return []
    return [str(data)]

def create_nested_bullet_block(line, prefix=None, prefix_color="default"):
    if not isinstance(line, str): line = str(line)
    
    links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', line)
    main_text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', '', line).strip()
    
    rich_text = []
    if prefix and main_text.startswith(prefix):
        main_text = main_text.replace(prefix, "").strip()
        rich_text.append({"text": {"content": prefix + " "}, "annotations": {"color": prefix_color, "bold": True}})
    
    if main_text:
        rich_text.append({"text": {"content": main_text[:1900]}}) 
    elif not rich_text:
        rich_text.append({"text": {"content": "내용 없음 (AI 응답 누락)"}})
    
    block = {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": rich_text
        }
    }
    
    if links:
        children = []
        for title, url in links:
            url = url.strip()
            if not url.startswith("http"): url = "https://" + url.lstrip(":/")
            if len(url) < 10 or "://" not in url: url = "https://gall.dcinside.com" 
            
            children.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {"text": {"content": "🔗 참조: "}, "annotations": {"color": "gray"}},
                        {"text": {"content": f"[{title[:50]}]", "link": {"url": url}}, "annotations": {"color": "blue", "underline": True}}
                    ]
                }
            })
        block["bulleted_list_item"]["children"] = children
        
    return block

# 💡 [핵심 버그 수정] 링크 구조 걷어내고 텍스트로 깔끔하게 처리!
def get_bot_info_block(gallery_name, date_range_str):
    return [{"object": "block", "type": "toggle", "toggle": {"rich_text": [{"text": {"content": "ℹ️ 봇 안내 및 데이터 출처 (클릭해서 펼치기)"}, "annotations": {"color": "gray", "bold": True}}], "children": [{"object": "block", "type": "callout", "callout": {"icon": {"emoji": "🚜"}, "color": "blue_background", "rich_text": [{"text": {"content": f"[{APP_VERSION}] 디시인사이드 갤러리 탈곡기\n"}, "annotations": {"bold": True, "color": "blue"}}, {"text": {"content": f"👉 {gallery_name} 데이터 기반 리포트\n"}, "annotations": {"bold": True, "color": "blue"}}, {"text": {"content": f"🗓️ 분석 대상 기간: {date_range_str}"}, "annotations": {"color": "gray"}}]}}]}}, {"object": "block", "type": "divider", "divider": {}}]

def get_ai_one_liner_block(ai_data):
    critic = str(ai_data.get('critic_one_liner', ''))[:1900]
    return [{"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "🤖 AI 갤러리 민심 한줄평"}}]}}, {"object": "block", "type": "heading_3", "heading_3": {"rich_text": [{"text": {"content": f"❝ {critic} ❞"}, "annotations": {"color": "blue"}}]}}]

def get_top_keywords_block(ai_data):
    keywords_str = "  /  ".join(get_safe_list(ai_data.get('top_keywords')))
    return [{"object": "block", "type": "callout", "callout": {"icon": {"emoji": "🏷️"}, "color": "gray_background", "rich_text": [{"text": {"content": "핵심 키워드 TOP 5: \n"}, "annotations": {"bold": True}}, {"text": {"content": keywords_str}}]}}, {"object": "block", "type": "divider", "divider": {}}]

def get_trend_table_block(post_data):
    blocks = [{"object": "block", "type": "heading_3", "heading_3": {"rich_text": [{"text": {"content": "📊 분석 기간 내 개념글 수 추이"}, "annotations": {"color": "blue", "bold": True}}]}}]
    
    concept_posts = [p for p in post_data if p.get('is_concept')]
    date_counts = Counter(p.get('date', '알수없음') for p in concept_posts)
    sorted_dates = sorted(date_counts.items(), key=lambda x: x[0])
    
    if not sorted_dates: 
        blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "수집된 개념글 데이터가 없습니다.", "annotations": {"color": "gray"}}}]}})
        return blocks

    table_rows = []
    table_rows.append({
        "object": "block", "type": "table_row", "table_row": {"cells": [
            [{"text": {"content": "날짜"}, "annotations": {"bold": True}}],
            [{"text": {"content": "개념글 수"}, "annotations": {"bold": True}}]
        ]}
    })
    
    max_count = max(count for _, count in sorted_dates) if sorted_dates else 1
    for date_str, count in sorted_dates:
        bar_length = int((count / max_count) * 15)
        visual_bar = "█" * bar_length if bar_length > 0 else "▏"
        table_rows.append({
            "object": "block", "type": "table_row", "table_row": {"cells": [
                [{"text": {"content": date_str}}],
                [{"text": {"content": f"{count}개  {visual_bar}"}, "annotations": {"color": "gray"}}]
            ]}
        })

    blocks.append({
        "object": "block", "type": "table", "table": {
            "table_width": 2, "has_column_header": True, "has_row_header": False,
            "children": table_rows
        }
    })
    return blocks

def get_trend_analysis_block(ai_data, post_data):
    blocks = [{"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "📈 트렌드 및 여론 온도 변화"}}]}}]
    blocks.extend(get_trend_table_block(post_data))
    
    blocks.append({"object": "block", "type": "heading_3", "heading_3": {"rich_text": [{"text": {"content": "🌡️ 여론 온도 변화 (Before & After)"}, "annotations": {"color": "purple", "bold": True}}]}})
    for line in get_safe_list(ai_data.get('sentiment_tracker')): 
        blocks.append(create_nested_bullet_block(line))
        
    blocks.append({"object": "block", "type": "heading_3", "heading_3": {"rich_text": [{"text": {"content": "🔥 주요 트렌드 스파이크 원인"}, "annotations": {"color": "orange", "bold": True}}]}})
    for line in get_safe_list(ai_data.get('trend_spike_analysis')): 
        blocks.append(create_nested_bullet_block(line))
        
    blocks.append({"object": "block", "type": "divider", "divider": {}})
    return blocks

def get_sentiment_summary_block(ai_data):
    blocks = [{"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "📊 주요 긍/부정 여론 요약"}}]}}]
    for line in get_safe_list(ai_data.get('final_summary_all')): 
        if line.startswith("[긍정]"):
            blocks.append(create_nested_bullet_block(line, prefix="[긍정]", prefix_color="blue"))
        elif line.startswith("[부정]"):
            blocks.append(create_nested_bullet_block(line, prefix="[부정]", prefix_color="red"))
        else:
            blocks.append(create_nested_bullet_block(line))
    blocks.append({"object": "block", "type": "divider", "divider": {}})
    return blocks

def get_checklist_block(ai_data):
    blocks = [{"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "🚨 [AI픽 체크리스트] 주요 동향 기반 대응 제안"}}]}}]
    for issue in get_safe_list(ai_data.get('ai_pick_checklist')): 
        blocks.append(create_nested_bullet_block(issue))
    blocks.append({"object": "block", "type": "divider", "divider": {}})
    return blocks

def get_user_type_block(ai_data):
    user_data = ai_data.get('user_type_analysis', {})
    if not user_data: return []
    blocks = [{"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "👥 세부 민심 분석 (정보글 vs 일반반응)"}}]}}]
    blocks.append({"object": "block", "type": "heading_3", "heading_3": {"rich_text": [{"text": {"content": "🛡️ 주요 정보성/분석글"}, "annotations": {"color": "blue", "bold": True}}]}})
    for line in get_safe_list(user_data.get('high_quality_posts')): 
        blocks.append(create_nested_bullet_block(line))
    blocks.append({"object": "block", "type": "heading_3", "heading_3": {"rich_text": [{"text": {"content": "🌪️ 유저들의 일반적인 반응"}, "annotations": {"color": "green", "bold": True}}]}})
    for line in get_safe_list(user_data.get('general_opinion')): 
        blocks.append(create_nested_bullet_block(line))
    blocks.append({"object": "block", "type": "divider", "divider": {}})
    return blocks

def get_raw_data_block(post_data):
    blocks = [{"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "🔍 수집 데이터 원본 리스트"}}]}}]
    
    chunk_size = 90
    for i in range(0, len(post_data), chunk_size):
        chunk = post_data[i:i + chunk_size]
        list_items = []
        for p in chunk:
            badge = "🔥[개념]" if p.get('is_concept') else "💬[일반]"
            title_text = f"[{p.get('date', '')}] {badge} {p['title']} (댓글: {p.get('comment_count', 0)}개) - "
            url = p.get('post_url', '#')
            if not url.startswith("http"): url = "https://" + url.lstrip(":/")
            list_items.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"text": {"content": title_text[:1900]}}, {"text": {"content": "원문 링크", "link": {"url": url}}, "annotations": {"color": "blue", "underline": True}}]}})
        
        toggle_title = f"▶ 원본 링크 펼쳐보기 ({i+1} ~ {i+len(chunk)}번째 글)"
        blocks.append({"object": "block", "type": "toggle", "toggle": {"rich_text": [{"text": {"content": toggle_title}, "annotations": {"color": "gray", "bold": True}}], "children": list_items}})
        
    return blocks

def upload_to_notion(gallery_name, post_data, ai_data, date_range_str):
    headers = {"Authorization": f"Bearer {NOTION_TOKEN}", "Content-Type": "application/json", "Notion-Version": "2022-06-28"}
    kst = timezone(timedelta(hours=9))
    iso_timestamp = datetime.now(kst).strftime('%Y-%m-%dT%H:%M:%S+09:00')
    
    page_title = f"[{gallery_name}] DC 주요 동향 리포트 ({date_range_str})"
    create_data = {
        "parent": {"database_id": NOTION_DATABASE_ID}, 
        "properties": {
            "이름": {"title": [{"text": {"content": page_title}}]}, 
            "수집 시점": {"date": {"start": iso_timestamp}}, 
            "DC탈곡기 버전": {"rich_text": [{"text": {"content": APP_VERSION}}]},
            "분석 게시글 수": {"number": len(post_data)}
        }
    }
    
    try:
        res = requests.post("https://api.notion.com/v1/pages", headers=headers, data=json.dumps(create_data))
        res.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise Exception(f"노션 페이지 생성 실패: {e.response.text}")
        
    page_id = res.json()['id']
    children_blocks = []
    
    children_blocks.extend(get_bot_info_block(gallery_name, date_range_str))
    children_blocks.extend(get_ai_one_liner_block(ai_data))
    children_blocks.extend(get_top_keywords_block(ai_data))
    children_blocks.extend(get_trend_analysis_block(ai_data, post_data))
    children_blocks.extend(get_sentiment_summary_block(ai_data))
    children_blocks.extend(get_checklist_block(ai_data))
    children_blocks.extend(get_user_type_block(ai_data))
    children_blocks.extend(get_raw_data_block(post_data))
    
    append_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    for i in range(0, len(children_blocks), 100):
        try:
            requests.patch(append_url, headers=headers, data=json.dumps({"children": children_blocks[i:i+100]})).raise_for_status() 
        except requests.exceptions.HTTPError as e:
            raise Exception(f"노션 블록 추가 실패 (상태코드 {e.response.status_code}): {e.response.text}")
        except Exception as e:
            raise Exception(f"노션 블록 추가 실패: {e}")
        time.sleep(0.5)
    return page_id