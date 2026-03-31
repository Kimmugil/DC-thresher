"""
report_notion.py v4
- 타임라인 테이블: 컬럼 헤더를 '추이' 대신 '분석기간 여부'로 변경
  + 범례 callout 추가 (진한 파랑=분석 기간 / 회색=14일 참고 기간)
"""
import requests, json, re, time
from datetime import datetime, timedelta, timezone
from config import NOTION_TOKEN, NOTION_DATABASE_ID, APP_VERSION, COMPLAINT_CATEGORIES
from utils import strip_md, clean
from ui_texts import (
    NOTION_BOT_INFO_TITLE, NOTION_BOT_INFO_DESC, NOTION_SUMMARY_TITLE,
    NOTION_POS_TITLE, NOTION_NEG_TITLE, NOTION_ISSUE_TITLE,
    NOTION_COMPLAINT_TITLE, NOTION_TIMELINE_TITLE, NOTION_RAW_TITLE,
    NOTION_SCORE_CRITERIA, NOTION_ISSUE_CRITERIA,
)

# 노션 타임라인 범례 텍스트
_TIMELINE_LEGEND = (
    "색상 기준: 진한 파랑(■) = 실제 분석 기간 / 회색(■) = 추이 파악용 참고 기간(최대 14일)\n"
    "막대 길이는 해당 날짜 게시글 수를 최대값 대비 10단계로 표시합니다."
)


# ── 노션 블록 헬퍼 ───────────────────────────────────────────────
def _bullet(text: str, color: str = "default") -> dict:
    txt = clean(str(text))[:1900]
    ann = {"color": color} if color != "default" else {}
    return {
        "object": "block", "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": [{"text": {"content": txt}, "annotations": ann}]},
    }


def _bullet_with_url(text: str, url: str = "", color: str = "default") -> dict:
    txt  = clean(str(text))[:1900]
    ann  = {"color": color} if color != "default" else {}
    rich = [{"text": {"content": txt}, "annotations": ann}]
    if url and url.startswith("http"):
        rich.append({
            "text":        {"content": " [관련 게시글 보기]", "link": {"url": url}},
            "annotations": {"color": "blue"},
        })
    return {
        "object": "block", "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": rich},
    }


def _heading(text: str, level: int = 2) -> dict:
    ht = f"heading_{level}"
    return {"object": "block", "type": ht, ht: {"rich_text": [{"text": {"content": text}}]}}


def _divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def _callout(text: str, emoji: str = "💡", color: str = "blue_background") -> dict:
    return {
        "object": "block", "type": "callout",
        "callout": {
            "icon":      {"emoji": emoji},
            "color":     color,
            "rich_text": [{"text": {"content": strip_md(str(text))[:1900]}}],
        },
    }


def _toggle(title: str, children: list) -> dict:
    return {
        "object": "block", "type": "toggle",
        "toggle": {
            "rich_text": [{"text": {"content": title}, "annotations": {"bold": True, "color": "gray"}}],
            "children":  children[:99],
        },
    }


def _patch_append(page_id: str, blocks: list, headers: dict):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    for i in range(0, len(blocks), 100):
        res = requests.patch(url, headers=headers, data=json.dumps({"children": blocks[i:i + 100]}))
        if not res.ok:
            raise Exception(f"노션 블록 추가 실패 ({res.status_code}): {res.text[:300]}")
        time.sleep(0.5)


# ── 섹션 블록 생성 함수 ───────────────────────────────────────────
def _bot_info_blocks(game_name: str, date_range_str: str, subtype_label: str) -> list:
    desc = NOTION_BOT_INFO_DESC.format(
        version=APP_VERSION, game_name=game_name,
        subtype_label=subtype_label, date_range_str=date_range_str,
    )
    return [_toggle(NOTION_BOT_INFO_TITLE, [_callout(desc, emoji="🚜")]), _divider()]


def _summary_blocks(ins: dict) -> list:
    blocks = [_heading(NOTION_SUMMARY_TITLE, 2)]

    one_liner = clean(ins.get("critic_one_liner", ""))
    if one_liner:
        blocks.append({
            "object": "block", "type": "heading_3",
            "heading_3": {"rich_text": [
                {"text": {"content": f"❝ {one_liner} ❞"}, "annotations": {"color": "blue"}},
            ]},
        })

    kws = " / ".join(ins.get("top_keywords", [])[:5])
    if kws:
        blocks.append(_callout(f"핵심 키워드 TOP 5:\n{kws}", emoji="🏷️", color="gray_background"))

    sent = ins.get("sentiment_summary", {})
    pos  = sent.get("positive", [])
    neg  = sent.get("negative", [])

    if pos:
        blocks.append(_heading(NOTION_POS_TITLE, 3))
        for p in pos:
            blocks.append(_bullet_with_url(p.get("summary", ""), p.get("ref_url", ""), color="blue"))
    if neg:
        blocks.append(_heading(NOTION_NEG_TITLE, 3))
        for n in neg:
            blocks.append(_bullet_with_url(n.get("summary", ""), n.get("ref_url", ""), color="red"))

    blocks.append(_divider())
    return blocks


def _timeline_table_blocks(scrape_result: dict) -> list:
    """날짜별 게시글 수 테이블 — 컬럼명 명확화 + 범례 callout."""
    dc14 = scrape_result.get("date_counts_14") or scrape_result.get("date_counts", {})
    if not dc14:
        return []

    blocks         = [_heading(NOTION_TIMELINE_TITLE, 2)]
    max_cnt        = max(dc14.values(), default=1)
    analysis_dates = set(scrape_result.get("date_counts", {}).keys())

    # 범례 callout
    blocks.append(_callout(_TIMELINE_LEGEND, emoji="📊", color="gray_background"))

    rows = [{
        "object": "block", "type": "table_row",
        "table_row": {"cells": [
            [{"text": {"content": "날짜"},      "annotations": {"bold": True}}],
            [{"text": {"content": "게시글 수"}, "annotations": {"bold": True}}],
            [{"text": {"content": "분포"},      "annotations": {"bold": True}}],
        ]},
    }]
    for d in sorted(dc14.keys()):
        cnt         = dc14[d]
        in_analysis = d in analysis_dates
        bar         = "█" * max(1, round(cnt / max_cnt * 10))
        rows.append({
            "object": "block", "type": "table_row",
            "table_row": {"cells": [
                [{"text": {"content": d},
                  "annotations": {"bold": in_analysis, "color": "default" if in_analysis else "gray"}}],
                [{"text": {"content": f"{cnt}개"}}],
                [{"text": {"content": bar},
                  "annotations": {"color": "blue" if in_analysis else "gray"}}],
            ]},
        })

    blocks.append({
        "object": "block", "type": "table",
        "table": {
            "table_width":       3,
            "has_column_header": True,
            "has_row_header":    False,
            "children":          rows,
        },
    })
    blocks.append(_divider())
    return blocks


def _issue_blocks(ins: dict) -> list:
    blocks = [
        _heading(NOTION_ISSUE_TITLE, 2),
        _callout(NOTION_ISSUE_CRITERIA, emoji="ℹ️", color="gray_background"),
    ]
    issues = sorted(
        ins.get("major_issues", []),
        key=lambda x: int(x.get("mention_score", 0)),
        reverse=True,
    )
    if issues:
        for i in issues:
            score = i.get("mention_score", 0)
            url   = i.get("ref_url", "")
            
            # 신규 스키마 대응 (issue_title, issue_detail) 및 구버전(issue) 폴백
            if "issue_title" in i:
                title_text  = clean(i.get("issue_title", ""))
                detail_text = clean(i.get("issue_detail", ""))
                issue_tx = f"{title_text} — {detail_text}" if detail_text else title_text
            else:
                issue_tx = clean(i.get("issue", ""))
                
            blocks.append(_bullet_with_url(f"[{score}점] {issue_tx}", url, color="orange"))
    else:
        blocks.append(_bullet("감지된 주요 이슈 없음"))
    blocks.append(_divider())
    return blocks


def _complaint_blocks(ins: dict) -> list:
    complaint = ins.get("complaint_analysis", {})
    blocks    = [
        _heading(NOTION_COMPLAINT_TITLE, 2),
        _callout(NOTION_SCORE_CRITERIA, emoji="ℹ️", color="gray_background"),
    ]
    for cat_key, cat_info in COMPLAINT_CATEGORIES.items():
        data    = complaint.get(cat_key, {})
        score   = max(0, min(10, int(data.get("score", 0))))
        summary = clean(data.get("summary", ""))
        example = clean(data.get("example", ""))
        ex_url  = data.get("example_url", "")
        color   = "red" if score >= 7 else ("orange" if score >= 4 else "blue")

        children = [_bullet(f"요약: {summary}", color=color)]
        if example:
            children.append(_bullet_with_url(f"관련 여론: {example}", ex_url))

        blocks.append(_toggle(
            f"{cat_info['emoji']} {cat_info['label']} — 강도: {score}/10",
            children,
        ))
    blocks.append(_divider())
    return blocks


def _raw_data_blocks(scrape_result: dict) -> list:
    blocks = [_heading(NOTION_RAW_TITLE, 2)]
    all_m  = scrape_result.get("all_metas", [])

    list_children = []
    for m in sorted(all_m, key=lambda x: x.get("date", ""), reverse=True)[:50]:
        title = strip_md(m.get("title", ""))
        url   = m.get("post_url", "")
        meta  = f"(댓글: {m.get('comment_count', 0)}개)"
        text  = f"{title} {meta}"
        rich  = ([{"text": {"content": text, "link": {"url": url}}}]
                 if url else [{"text": {"content": text}}])
        list_children.append({
            "object": "block", "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": rich},
        })

    blocks.append(_toggle("클릭하여 원본 데이터 보기 (최근 50개)", list_children))
    blocks.append(_divider())
    return blocks


# ── 메인 발행 함수 ────────────────────────────────────────────────
def upload_to_notion(game_name: str, gallery_name: str, subtype_id: str,
                     scrape_result: dict, insights: dict) -> str:
    from config import GALLERY_SUBTYPES

    post_data      = scrape_result.get("all_metas", [])
    date_range_str = scrape_result.get("date_range_str", "")
    subtype        = GALLERY_SUBTYPES.get(subtype_id, GALLERY_SUBTYPES["stable"])
    subtype_label  = f"{subtype['emoji']} {subtype['label']}"

    headers = {
        "Authorization":  f"Bearer {NOTION_TOKEN}",
        "Content-Type":   "application/json",
        "Notion-Version": "2022-06-28",
    }
    iso_ts = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%dT%H:%M:%S+09:00")

    create_data = {
        "parent":     {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "이름":          {"title":     [{"text": {"content": f"[{game_name}] DC 게임 민심 리포트 ({date_range_str})"}}]},
            "수집 시점":      {"date":      {"start": iso_ts}},
            "DC탈곡기 버전":  {"rich_text": [{"text": {"content": APP_VERSION}}]},
            "수집 게시글 수": {"number":    len(post_data)},
        },
    }

    res = requests.post("https://api.notion.com/v1/pages", headers=headers, data=json.dumps(create_data))
    if not res.ok:
        raise Exception(f"노션 페이지 생성 실패: {res.text[:300]}")
    page_id = res.json()["id"]

    blocks  = _bot_info_blocks(game_name, date_range_str, subtype_label)
    blocks += _summary_blocks(insights)
    blocks += _timeline_table_blocks(scrape_result)
    blocks += _issue_blocks(insights)
    blocks += _complaint_blocks(insights)
    blocks += _raw_data_blocks(scrape_result)

    _patch_append(page_id, blocks, headers)
    return page_id