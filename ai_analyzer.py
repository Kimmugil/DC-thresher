"""
ai_analyzer.py v3 — Gemini API 호출 전담

[v3 변경]
  - diagnose_gallery_ai(): 경량 AI 호출 — 갤러리 주제·특성 파악 (Step 2)
  - analyze_gallery():     메인 분석 (Step 3, 개념글 위주 데이터)
  - fetch_patch_timeline(): 패치 타임라인 (보조)
"""

import requests, json, re
from config import GEMINI_API_KEY
from ui_texts import (
    build_diagnosis_ai_prompt,
    build_main_analysis_prompt,
    build_patch_search_prompt,
)

GEMINI_BASE  = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_MODEL = "gemini-2.5-flash"


def _call_gemini(prompt: str, json_mode: bool = True, timeout: int = 60) -> tuple:
    """공통 Gemini 호출. (result, error) 반환."""
    url = f"{GEMINI_BASE}/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}".strip()
    cfg = {"temperature": 0.1}
    if json_mode:
        cfg["responseMimeType"] = "application/json"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": cfg,
    }
    try:
        res = requests.post(
            url, headers={"Content-Type": "application/json"},
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=timeout,
        )
        res.raise_for_status()
        raw = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

        if json_mode:
            bt = chr(96) * 3
            raw = re.sub(r"^" + bt + r"(?:json)?\s*", "", raw, flags=re.MULTILINE | re.IGNORECASE)
            raw = re.sub(r"\s*" + bt + r"$", "", raw, flags=re.MULTILINE)
            raw = re.sub(r",\s*([\]}])", r"\1", raw)
            return json.loads(raw, strict=False), None
        return raw, None

    except json.JSONDecodeError as je:
        snippet = raw[max(0, je.pos-40):min(len(raw), je.pos+40)] if 'raw' in dir() else ""
        return None, f"JSON 파싱 오류: [... {snippet} ...]\n재분석 버튼을 눌러 다시 시도해 주세요."
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code
        if code == 429: return None, "API 호출 한도 초과(429). 잠시 후 다시 시도해 주세요."
        return None, f"Gemini API 오류 (HTTP {code})"
    except Exception as e:
        return None, str(e).replace(GEMINI_API_KEY or "", "***")


def diagnose_gallery_ai(gallery_name: str, top_words: list,
                         subtype_id: str, daily_avg: float) -> tuple:
    """
    Step 2 경량 AI 호출.
    갤러리가 어떤 주제인지 파악하고, 분석 방향을 제안.
    반환: (result_dict, error)
    result_dict = {
        "topic_guess": "추정 주제",
        "topic_confidence": 0~100,
        "topic_reason": "추정 근거",
        "suggested_focus": "분석 방향 추천 ID",
        "suggested_focus_reason": "추천 이유",
        "warning": "주의 사항 (없으면 빈 문자열)",
    }
    """
    prompt = build_diagnosis_ai_prompt(
        gallery_name=gallery_name,
        top_words=top_words,
        subtype_id=subtype_id,
        daily_avg=daily_avg,
    )
    return _call_gemini(prompt, json_mode=True, timeout=30)


def _format_posts(post_data: list) -> str:
    lines = []
    for idx, post in enumerate(post_data):
        badge = "🔥[개념글]" if post.get("is_concept") else "💬[일반글(보충)]"
        body  = (post.get("body","")
                 .replace('"',"'").replace("\n"," ").replace("\\"," "))
        lines.append(
            f"\n=== {badge} [{idx+1}] ===\n"
            f"제목: {post.get('title','')}\n"
            f"작성일: {post.get('date','')}\n"
            f"URL: {post.get('post_url','')}\n"
            f"유형: {post.get('user_type','')} / 댓글: {post.get('comment_count',0)}개\n"
            f"본문: {body[:600]}\n"
        )
    return "".join(lines)


def analyze_gallery(gallery_id: str, game_name: str, subtype_id: str,
                    analysis_data: list, all_metas: list,
                    analysis_days: int, analysis_focus: str = "default",
                    user_feedback: str = "") -> tuple:
    """
    메인 분석.
    analysis_data: 본문 포함 (개념글 위주)
    all_metas: 전체 목록 메타 (날짜 분포, 수 통계용)
    """
    from config import GALLERY_SUBTYPES, ANALYSIS_FOCUS_OPTIONS
    subtype   = GALLERY_SUBTYPES.get(subtype_id, GALLERY_SUBTYPES["stable"])
    sl        = f"{subtype['emoji']} {subtype['label']}"
    sd        = subtype["desc"]
    sf        = subtype.get("analysis_focus", "")
    focus_lbl = ANALYSIS_FOCUS_OPTIONS.get(analysis_focus, ANALYSIS_FOCUS_OPTIONS["default"])

    # 전체 목록 통계 요약 (날짜별 글 수 — AI 컨텍스트용)
    from collections import Counter
    date_cnt     = Counter(m["date"] for m in all_metas)
    total_count  = len(all_metas)
    concept_cnt  = sum(1 for m in all_metas if m.get("is_concept"))
    sorted_dates = sorted(date_cnt.items())
    date_summary = "  ".join(f"{d}:{c}개" for d, c in sorted_dates)

    post_text = _format_posts(analysis_data)
    prompt    = build_main_analysis_prompt(
        gallery_id=gallery_id,
        game_name=game_name,
        subtype_label=sl,
        subtype_desc=sd,
        subtype_focus=sf,
        analysis_focus_label=focus_lbl,
        post_data_text=post_text,
        analysis_days=analysis_days,
        total_posts=total_count,
        concept_posts=concept_cnt,
        date_summary=date_summary,
        user_feedback=user_feedback,
    )
    return _call_gemini(prompt, json_mode=True, timeout=120)


def fetch_patch_timeline(game_name: str, analysis_days: int, spike_dates: list) -> str:
    if not game_name or not game_name.strip(): return ""
    prompt = build_patch_search_prompt(game_name, analysis_days, spike_dates)
    result, _ = _call_gemini(prompt, json_mode=False, timeout=30)
    return result or ""