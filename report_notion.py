"""
report_notion.py
역할: 분석 결과를 노션 데이터베이스에 발행합니다.
"""

import requests
import json
import re
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from config import NOTION_TOKEN, NOTION_DATABASE_ID, APP_VERSION, COMPLAINT_CATEGORIES, ACTION_PRIORITY


def _sanitize(text: str) -> str:
    return str(text).replace('~', '∼')


def _safe_list(data) -> list:
    if isinstance(data, list):
        return [str(i) for i in data]
    if isinstance(data, dict):
        return [str(v) for v in data.values()]
    if isinstance(data, str) and data:
        return [data]
    return []


def _strip_md(text: str) -> str:
    return _sanitize(re.sub(r"\*+", "", str(text)))


def _bullet(text: str, color: str = "default") -> dict:
    """단순 불릿 블록 생성"""
    clean = _strip_md(re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", str(text)))[:1900]
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{"text": {"content": clean},
                           "annotations": {"color": color} if color != "default" else {}}],
        },
    }


def _heading(text: str, level: int = 2) -> dict:
    htype = f"heading_{level}"
    return {"object": "block", "type": htype, htype: {"rich_text": [{"text": {"content": text}}]}}


def _divider() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}


def _callout(text: str, emoji: str = "💡", color: str = "blue_background") -> dict:
    return {
        "object": "block", "type": "callout",
        "callout": {
            "icon": {"emoji": emoji},
            "color": color,
            "rich_text": [{"text": {"content": _strip_md(str(text))[:1900]}}],
        },
    }


def _toggle(title: str, children: list) -> dict:
    return {
        "object": "block", "type": "toggle",
        "toggle": {
            "rich_text": [{"text": {"content": title}, "annotations": {"bold": True, "color": "gray"}}],
            "children": children[:99],
        },
    }


def _patch_append(page_id: str, blocks: list, headers: dict):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    for i in range(0, len(blocks), 100):
        chunk = blocks[i:i + 100]
        res   = requests.patch(url, headers=headers, data=json.dumps({"children": chunk}))
        if not res.ok:
            raise Exception(f"노션 블록 추가 실패 ({res.status_code}): {res.text[:300]}")
        time.sleep(0.5)


# ─────────────────────────────────────────────
# 섹션 블록 생성 함수들
# ─────────────────────────────────────────────
def _bot_info_blocks(game_name: str, date_range_str: str, subtype_label: str) -> list:
    return [
        _toggle(
            "ℹ️ 봇 안내 및 데이터 출처 (클릭해서 펼치기)",
            [_callout(
                f"[{APP_VERSION}] 디씨인사이드 게임 갤러리 탈곡기\n"
                f"분석 대상: {game_name} / {subtype_label}\n"
                f"분석 기간: {date_range_str}",
                emoji="🚜", color="blue_background",
            )],
        ),
        _divider(),
    ]


def _summary_blocks(ins: dict) -> list:
    blocks = [_heading("🤖 AI 민심 한줄평", 2)]
    blocks.append({
        "object": "block", "type": "heading_3",
        "heading_3": {"rich_text": [
            {"text": {"content": f"❝ {_strip_md(ins.get('critic_one_liner', ''))} ❞"},
             "annotations": {"color": "blue"}},
        ]},
    })
    kws = " / ".join(ins.get("top_keywords", []))
    blocks.append(_callout(f"핵심 키워드 TOP 5:\n{kws}", emoji="🏷️", color="gray_background"))
    blocks.append(_divider())
    return blocks


def _sentiment_blocks(ins: dict) -> list:
    sc    = ins.get("sentiment_score", {})
    trend = sc.get("trend", "유지")
    blocks = [
        _heading("🌡️ 민심 온도 분석", 2),
        _callout(
            f"전체 민심 온도: {sc.get('overall', 'N/A')} / 100  ({trend})\n"
            f"기간 전반부: {sc.get('early_period', 'N/A')} / 100\n"
            f"기간 후반부: {sc.get('late_period', 'N/A')} / 100\n\n"
            f"[측정 기준] 5가지 요소 종합: 긍부정 빈도 / 감정 강도 / 이탈 신호 / 개념글 여론 / 갤러리 상태\n"
            f"점수: 80~100=매우긍정 / 65~79=긍정 / 50~64=보통 / 35~49=부정 / 0~34=매우부정",
            emoji="🌡️", color="gray_background",
        ),
    ]
    summary = ins.get("sentiment_summary", {})
    blocks.append(_heading("🟢 긍정 여론", 3))
    for line in _safe_list(summary.get("positive")):
        blocks.append(_bullet(line, color="blue"))
    blocks.append(_heading("🔴 부정 여론", 3))
    for line in _safe_list(summary.get("negative")):
        blocks.append(_bullet(line, color="red"))
    blocks.append(_divider())
    return blocks


def _timeline_blocks(ins: dict, post_data: list) -> list:
    # 날짜별 글 수 테이블
    from collections import Counter
    date_cnt = Counter(p.get("date", "") for p in post_data if p.get("date"))
    sorted_dates = sorted(date_cnt.items())
    max_cnt = max((v for _, v in sorted_dates), default=1)

    concept_cnt = Counter(p.get("date","") for p in post_data if p.get("is_concept") and p.get("date"))
    normal_cnt  = Counter(p.get("date","") for p in post_data if not p.get("is_concept") and p.get("date"))
    table_rows = [{
        "object": "block", "type": "table_row",
        "table_row": {"cells": [
            [{"text": {"content": "날짜"}, "annotations": {"bold": True}}],
            [{"text": {"content": "전체"}, "annotations": {"bold": True}}],
            [{"text": {"content": "개념글"}, "annotations": {"bold": True, "color": "blue"}}],
            [{"text": {"content": "일반글"}, "annotations": {"bold": True}}],
            [{"text": {"content": "추이"}, "annotations": {"bold": True}}],
        ]},
    }]
    for d, cnt in sorted_dates:
        bar = "█" * max(1, int(cnt / max_cnt * 10))
        table_rows.append({
            "object": "block", "type": "table_row",
            "table_row": {"cells": [
                [{"text": {"content": d}}],
                [{"text": {"content": str(cnt)}}],
                [{"text": {"content": str(concept_cnt.get(d,0))}, "annotations": {"color": "blue"}}],
                [{"text": {"content": str(normal_cnt.get(d,0))}}],
                [{"text": {"content": bar}, "annotations": {"color": "gray"}}],
            ]},
        })

    blocks = [
        _heading("📈 이슈 타임라인", 2),
        {"object": "block", "type": "table",
         "table": {"table_width": 5, "has_column_header": True, "has_row_header": False,
                   "children": table_rows}},
    ]

    # AI 이슈 타임라인
    timeline = ins.get("issue_timeline", [])
    for ev in timeline:
        impact_map = {"high": "red", "medium": "orange", "low": "blue"}
        color = impact_map.get(ev.get("impact", "low"), "gray")
        text  = f"[{ev.get('date', '')}] {_strip_md(ev.get('event', ''))}"
        url   = ev.get("ref_url", "")
        if url and url.startswith("http"):
            text += f"  →  {url}"
        blocks.append(_bullet(text, color=color))

    blocks.append(_divider())
    return blocks


def _complaint_blocks(ins: dict) -> list:
    complaint = ins.get("complaint_analysis", {})
    blocks    = [_heading("⚠️ 불만 카테고리 분석", 2)]
    for cat_key, cat_info in COMPLAINT_CATEGORIES.items():
        data    = complaint.get(cat_key, {})
        score   = data.get("score", 0)
        summary = _strip_md(data.get("summary", ""))
        example = _strip_md(data.get("example", ""))
        color   = "red" if score >= 7 else ("orange" if score >= 4 else "blue")
        blocks.append(_toggle(
            f"{cat_info['emoji']} {cat_info['label']} — 강도: {score}/10",
            [
                _bullet(f"요약: {summary}", color=color),
                *([_bullet(f"대표 발언: {example}")] if example else []),
            ],
        ))
    blocks.append(_divider())
    return blocks


def _churn_blocks(ins: dict) -> list:
    churn   = ins.get("churn_analysis", {})
    risk    = churn.get("risk_level", "low")
    labels  = {"high": "🚨 높음", "medium": "👀 주의", "low": "✅ 낮음"}
    colors  = {"high": "red_background", "medium": "orange_background", "low": "blue_background"}
    blocks  = [
        _heading("🚨 이탈 위험 신호 분석", 2),
        _callout(
            f"이탈 위험도: {labels.get(risk, risk)}\n"
            f"강한 이탈 신호 언급: {churn.get('strong_signal_count', 0)}회\n"
            f"종합: {_strip_md(churn.get('summary', ''))}",
            emoji="⚠️",
            color=colors.get(risk, "gray_background"),
        ),
    ]
    for r in _safe_list(churn.get("main_reasons")):
        blocks.append(_bullet(f"이탈 원인: {_strip_md(r)}", color="red"))
    blocks.append(_divider())
    return blocks


def _segment_blocks(ins: dict) -> list:
    seg    = ins.get("segment_analysis", {})
    if not seg:
        return []
    blocks = [
        _heading("👥 유저 세그먼트 분석 (고닉 vs 유동)", 2),
        _callout(
            f"코어 유저 (고닉) 민심 온도: {seg.get('core_user_temp', 'N/A')} / 100\n"
            f"  → {_strip_md(seg.get('core_main_concern', ''))}\n\n"
            f"라이트 유저 (유동) 민심 온도: {seg.get('casual_user_temp', 'N/A')} / 100\n"
            f"  → {_strip_md(seg.get('casual_main_concern', ''))}\n\n"
            f"인사이트: {_strip_md(seg.get('gap_insight', ''))}",
            emoji="👥", color="gray_background",
        ),
        _divider(),
    ]
    return blocks


def _checklist_blocks(ins: dict) -> list:
    checklist = ins.get("pm_checklist", [])
    blocks    = [_heading("🚨 PM 액션 체크리스트", 2)]
    color_map = {"urgent": "red", "monitor": "orange", "note": "blue"}
    for item in checklist:
        pkey   = item.get("priority", "note")
        pinfo  = ACTION_PRIORITY.get(pkey, ACTION_PRIORITY["note"])
        action = _strip_md(item.get("action", ""))
        reason = _strip_md(item.get("reason", ""))
        color  = color_map.get(pkey, "default")
        blocks.append(_bullet(f"{pinfo['emoji']} [{pinfo['label']}] {action}", color=color))
        if reason:
            blocks.append(_bullet(f"   근거: {reason}"))
        ref_url = item.get("ref_url","")
        if ref_url and ref_url.startswith("http"):
            blocks.append(_bullet(f"   관련 게시글: {ref_url}", color=color))
    blocks.append(_divider())
    return blocks


def _patch_timeline_blocks(patch_text: str) -> list:
    if not patch_text:
        return []
    lines  = [l.strip() for l in patch_text.split("\n") if l.strip()]
    blocks = [_heading("🛠️ 공식 패치/업데이트 타임라인", 2)]
    for line in lines:
        blocks.append(_bullet(line[:1900]))
    blocks.append(_divider())
    return blocks


def _raw_data_blocks(post_data: list) -> list:
    blocks    = [_heading("🔍 수집 데이터 원본", 2)]
    chunk_sz  = 90
    for i in range(0, len(post_data), chunk_sz):
        chunk = post_data[i:i + chunk_sz]
        items = []
        for p in chunk:
            badge = "🔥[개념]" if p.get("is_concept") else "💬[일반]"
            title = f"[{p.get('date', '')}] {badge} {p['title']} (댓글: {p.get('comment_count', 0)}개)"
            url   = p.get("post_url", "#")
            items.append({
                "object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {"text": {"content": title[:1800]}},
                        {"text": {"content": " 원문", "link": {"url": url}},
                         "annotations": {"color": "blue", "underline": True}},
                    ],
                },
            })
        blocks.append(_toggle(
            f"▶ 원본 링크 {i + 1}~{i + len(chunk)}번째",
            items,
        ))
    return blocks


# ─────────────────────────────────────────────
# 메인 발행 함수
# ─────────────────────────────────────────────
def upload_to_notion(game_name: str, gallery_name: str, subtype_id: str,
                     scrape_result: dict, insights: dict,
                     patch_timeline: str = "") -> str:
    from config import GALLERY_SUBTYPES
    post_data     = scrape_result.get("all_metas", [])
    date_range_str = scrape_result.get("date_range_str", "")
    subtype       = GALLERY_SUBTYPES.get(subtype_id, GALLERY_SUBTYPES["stable"])
    subtype_label = f"{subtype['emoji']} {subtype['label']}"

    headers  = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    kst      = timezone(timedelta(hours=9))
    iso_ts   = datetime.now(kst).strftime("%Y-%m-%dT%H:%M:%S+09:00")
    page_title = f"[{game_name}] DC 게임 민심 리포트 ({date_range_str})"

    create_data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "이름":           {"title": [{"text": {"content": page_title}}]},
            "수집 시점":       {"date": {"start": iso_ts}},
            "DC탈곡기 버전":   {"rich_text": [{"text": {"content": APP_VERSION}}]},
            "분석 게시글 수":  {"number": len(post_data)},
        },
    }

    res = requests.post("https://api.notion.com/v1/pages", headers=headers,
                        data=json.dumps(create_data))
    if not res.ok:
        raise Exception(f"노션 페이지 생성 실패: {res.text[:300]}")

    page_id = res.json()["id"]

    blocks = []
    blocks += _bot_info_blocks(game_name, date_range_str, subtype_label)
    blocks += _summary_blocks(insights)
    blocks += _sentiment_blocks(insights)
    blocks += _timeline_blocks(insights, post_data)
    blocks += _complaint_blocks(insights)
    blocks += _churn_blocks(insights)
    blocks += _segment_blocks(insights)
    blocks += _checklist_blocks(insights)
    if patch_timeline:
        blocks += _patch_timeline_blocks(patch_timeline)
    blocks += _raw_data_blocks(post_data)

    _patch_append(page_id, blocks, headers)
    return page_id