"""
report_notion.py
역할: 분석 결과를 노션 데이터베이스에 발행합니다.
"""

import requests, json, re, time
from datetime import datetime, timedelta, timezone
from config import NOTION_TOKEN, NOTION_DATABASE_ID, APP_VERSION, COMPLAINT_CATEGORIES
from ui_texts import (
    NOTION_BOT_INFO_TITLE, NOTION_BOT_INFO_DESC, NOTION_SUMMARY_TITLE,
    NOTION_POS_TITLE, NOTION_NEG_TITLE, NOTION_ISSUE_TITLE, NOTION_COMPLAINT_TITLE,
    NOTION_TIMELINE_TITLE, NOTION_RAW_TITLE
)

def _sanitize(text: str) -> str: return str(text).replace('~', '∼')
def _strip_md(text: str) -> str: 
    # 마크다운 ** 와 * 등을 완전히 제거
    return _sanitize(str(text).replace("**", "").replace("*", "").replace("~~", "").replace("~", ""))

def _bullet(text: str, color: str = "default") -> dict:
    clean = _strip_md(re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", str(text)))[:1900]
    return {
        "object": "block", "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": [{"text": {"content": clean}, "annotations": {"color": color} if color != "default" else {}}]}
    }

def _bullet_with_url(text: str, url: str = "", color: str = "default") -> dict:
    clean = _strip_md(re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", str(text)))[:1900]
    rich_text = []
    rich_text.append({"text": {"content": clean}, "annotations": {"color": color} if color != "default" else {}})
    if url and url.startswith("http"):
        rich_text.append({"text": {"content": " [관련 게시글 보기]", "link": {"url": url}}, "annotations": {"color": "blue"}})
    return {
        "object": "block", "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": rich_text}
    }

def _heading(text: str, level: int = 2) -> dict:
    htype = f"heading_{level}"
    return {"object": "block", "type": htype, htype: {"rich_text": [{"text": {"content": text}}]}}

def _divider() -> dict: return {"object": "block", "type": "divider", "divider": {}}

def _callout(text: str, emoji: str = "💡", color: str = "blue_background") -> dict:
    return {"object": "block", "type": "callout", "callout": {"icon": {"emoji": emoji}, "color": color, "rich_text": [{"text": {"content": _strip_md(str(text))[:1900]}}]}}

def _toggle(title: str, children: list) -> dict:
    return {"object": "block", "type": "toggle", "toggle": {"rich_text": [{"text": {"content": title}, "annotations": {"bold": True, "color": "gray"}}], "children": children[:99]}}

def _patch_append(page_id: str, blocks: list, headers: dict):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    for i in range(0, len(blocks), 100):
        res = requests.patch(url, headers=headers, data=json.dumps({"children": blocks[i:i + 100]}))
        if not res.ok: raise Exception(f"노션 블록 추가 실패 ({res.status_code}): {res.text[:300]}")
        time.sleep(0.5)

def _bot_info_blocks(game_name: str, date_range_str: str, subtype_label: str) -> list:
    desc = NOTION_BOT_INFO_DESC.format(version=APP_VERSION, game_name=game_name, subtype_label=subtype_label, date_range_str=date_range_str)
    return [_toggle(NOTION_BOT_INFO_TITLE, [_callout(desc, emoji="🚜")]), _divider()]

def _summary_blocks(ins: dict) -> list:
    blocks = [_heading(NOTION_SUMMARY_TITLE, 2)]
    blocks.append({"object": "block", "type": "heading_3", "heading_3": {"rich_text": [{"text": {"content": f"❝ {_strip_md(ins.get('critic_one_liner', ''))} ❞"}, "annotations": {"color": "blue"}}]}})
    blocks.append(_callout(f"핵심 키워드 TOP 5:\n{' / '.join(ins.get('top_keywords', [])[:5])}", emoji="🏷️", color="gray_background"))
    
    # 긍정 부정 여론 추가 (링크 포함)
    sent = ins.get("sentiment_summary", {})
    pos = sent.get("positive", [])
    neg = sent.get("negative", [])
    if pos:
        blocks.append(_heading(NOTION_POS_TITLE, 3))
        for p in pos: blocks.append(_bullet_with_url(p.get("summary", ""), p.get("ref_url", ""), color="blue"))
    if neg:
        blocks.append(_heading(NOTION_NEG_TITLE, 3))
        for n in neg: blocks.append(_bullet_with_url(n.get("summary", ""), n.get("ref_url", ""), color="red"))
        
    blocks.append(_divider())
    return blocks

def _timeline_table_blocks(scrape_result: dict) -> list:
    dc14 = scrape_result.get("date_counts_14") or scrape_result.get("date_counts", {})
    if not dc14: return []
    blocks = [_heading(NOTION_TIMELINE_TITLE, 2)]
    
    rows = []
    # 헤더
    rows.append({"type": "table_row", "table_row": {"cells": [[{"text": {"content": "날짜"}}], [{"text": {"content": "게시글 수"}}]]}})
    # 데이터
    for d in sorted(dc14.keys()):
        rows.append({"type": "table_row", "table_row": {"cells": [[{"text": {"content": d}}], [{"text": {"content": f"{dc14[d]}개"}}]]}})
        
    blocks.append({
        "object": "block", "type": "table",
        "table": {"table_width": 2, "has_column_header": True, "has_row_header": False, "children": rows}
    })
    blocks.append(_divider())
    return blocks

def _issue_blocks(ins: dict) -> list:
    blocks = [_heading(NOTION_ISSUE_TITLE, 2)]
    issues = sorted(ins.get("major_issues", []), key=lambda x: int(x.get("mention_score", 0)), reverse=True)
    if issues:
        for i in issues: blocks.append(_bullet(f"[점수 {i.get('mention_score', 0)}] {_strip_md(i.get('issue',''))}", color="orange"))
    else: blocks.append(_bullet("주요 이슈 없음"))
    blocks.append(_divider())
    return blocks

def _complaint_blocks(ins: dict) -> list:
    complaint = ins.get("complaint_analysis", {})
    blocks = [_heading(NOTION_COMPLAINT_TITLE, 2)]
    for cat_key, cat_info in COMPLAINT_CATEGORIES.items():
        data = complaint.get(cat_key, {}); score = data.get("score", 0); summary = _strip_md(data.get("summary", "")); example = _strip_md(data.get("example", ""))
        ex_url = data.get("example_url", "")
        color = "red" if score >= 7 else ("orange" if score >= 4 else "blue")
        
        children_list = [_bullet(f"요약: {summary}", color=color)]
        if example: children_list.append(_bullet_with_url(f"관련 여론: {example}", ex_url))
            
        blocks.append(_toggle(f"{cat_info['emoji']} {cat_info['label']} — 강도: {score}/10", children_list))
    blocks.append(_divider())
    return blocks

def _raw_data_blocks(scrape_result: dict) -> list:
    blocks = [_heading(NOTION_RAW_TITLE, 2)]
    all_m = scrape_result.get("all_metas", [])
    
    list_children = []
    # 노션 블록 제한을 막기 위해 최근 50개만 원본 데이터에 삽입
    for m in sorted(all_m, key=lambda x: x.get("date", ""), reverse=True)[:50]:
        badge = "[개념]" if m.get("is_concept") else "[일반]"
        title = _strip_md(m.get("title", ""))
        url = m.get("post_url", "")
        meta = f"(댓글: {m.get('comment_count', 0)}개)"
        
        text_content = f"{badge} {title} {meta}"
        rich_text = [{"text": {"content": text_content}}]
        if url:
            rich_text = [{"text": {"content": text_content, "link": {"url": url}}}]
        
        list_children.append({
            "object": "block", "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": rich_text}
        })
        
    blocks.append(_toggle("클릭하여 원본 데이터 보기 (최근 50개)", list_children))
    blocks.append(_divider())
    return blocks

def upload_to_notion(game_name: str, gallery_name: str, subtype_id: str, scrape_result: dict, insights: dict) -> str:
    from config import GALLERY_SUBTYPES
    post_data = scrape_result.get("all_metas", []); date_range_str = scrape_result.get("date_range_str", "")
    subtype = GALLERY_SUBTYPES.get(subtype_id, GALLERY_SUBTYPES["stable"])
    
    headers = {"Authorization": f"Bearer {NOTION_TOKEN}", "Content-Type": "application/json", "Notion-Version": "2022-06-28"}
    iso_ts = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%dT%H:%M:%S+09:00")
    
    # 1번 피드백 반영: '분석 게시글 수' -> '수집 게시글 수'
    create_data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {"이름": {"title": [{"text": {"content": f"[{game_name}] DC 게임 민심 리포트 ({date_range_str})"}}] },
                       "수집 시점": {"date": {"start": iso_ts}}, "DC탈곡기 버전": {"rich_text": [{"text": {"content": APP_VERSION}}]}, "수집 게시글 수": {"number": len(post_data)}}
    }
    res = requests.post("https://api.notion.com/v1/pages", headers=headers, data=json.dumps(create_data))
    if not res.ok: raise Exception(f"노션 페이지 생성 실패: {res.text[:300]}")
    page_id = res.json()["id"]

    blocks = _bot_info_blocks(game_name, date_range_str, f"{subtype['emoji']} {subtype['label']}")
    blocks += _summary_blocks(insights)
    blocks += _timeline_table_blocks(scrape_result) # 7번 표 데이터 반영
    blocks += _issue_blocks(insights)
    blocks += _complaint_blocks(insights)
    blocks += _raw_data_blocks(scrape_result) # 7번 원본 데이터 반영
    
    _patch_append(page_id, blocks, headers)
    return page_id