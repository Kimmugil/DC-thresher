"""
ai_analyzer.py v5
- suggested_focus: 배열 반환 시 첫 원소 추출 (프롬프트에서 단일 문자열 보장)
- analyze_gallery: user_feedback 파라미터 완전 제거
- _format_posts: 배지 구분 제거 (개념글 구분 불필요)
"""
import requests, json, re
from config import GEMINI_API_KEY
from ui_texts import build_diagnosis_ai_prompt, build_main_analysis_prompt

GEMINI_BASE  = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_MODEL = "gemini-2.5-flash"


def _call_gemini(prompt: str, json_mode: bool = True, timeout: int = 60) -> tuple:
    """공통 Gemini 호출. (result, error) 반환."""
    url = f"{GEMINI_BASE}/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}".strip()
    cfg = {"temperature": 0.1}
    if json_mode:
        cfg["responseMimeType"] = "application/json"

    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": cfg}
    try:
        res = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=timeout,
        )
        res.raise_for_status()
        raw = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

        if json_mode:
            bt  = chr(96) * 3
            raw = re.sub(r"^" + bt + r"(?:json)?\s*", "", raw, flags=re.MULTILINE | re.IGNORECASE)
            raw = re.sub(r"\s*" + bt + r"$",           "", raw, flags=re.MULTILINE)
            raw = re.sub(r",\s*([\]}])",               r"\1", raw)
            return json.loads(raw, strict=False), None
        return raw, None

    except json.JSONDecodeError as je:
        snippet = raw[max(0, je.pos - 40):min(len(raw), je.pos + 40)] if "raw" in dir() else ""
        return None, f"JSON 파싱 오류: [... {snippet} ...]\n재분석 버튼을 눌러 다시 시도해 주세요."
    except requests.exceptions.HTTPError as e:
        code = e.response.status_code
        if code == 429:
            return None, "API 호출 한도 초과(429). 잠시 후 다시 시도해 주세요."
        return None, f"Gemini API 오류 (HTTP {code})"
    except Exception as e:
        return None, str(e).replace(GEMINI_API_KEY or "", "***")


def diagnose_gallery_ai(gallery_name: str, top_words: list,
                         subtype_id: str, daily_avg: float) -> tuple:
    """
    Step 0 경량 AI 호출 — 갤러리 주제 파악 및 분석 방향 추천.
    suggested_focus를 단일 문자열로 보장 (구버전 배열 반환 대응).
    """
    prompt = build_diagnosis_ai_prompt(gallery_name, top_words, subtype_id, daily_avg)
    result, err = _call_gemini(prompt, json_mode=True, timeout=30)
    if result and isinstance(result.get("suggested_focus"), list):
        result["suggested_focus"] = result["suggested_focus"][0] if result["suggested_focus"] else "default"
    return result, err


def _format_posts(post_data: list) -> str:
    """분석용 게시글 텍스트 포맷."""
    lines = []
    for idx, post in enumerate(post_data):
        body = (
            post.get("body", "")
            .replace('"', "'")
            .replace("\n", " ")
            .replace("\\", " ")
        )
        lines.append(
            f"[{idx + 1}] "
            f"제목: {post.get('title', '')} | "
            f"작성일: {post.get('date', '')} | "
            f"댓글: {post.get('comment_count', 0)}개 | "
            f"URL: {post.get('post_url', '')} | "
            f"본문: {body[:600]}\n"
        )
    return "".join(lines)


def analyze_gallery(gallery_id: str, game_name: str, subtype_id: str,
                    analysis_data: list, all_metas: list,
                    analysis_days: int, analysis_focus: str = "default") -> tuple:
    """
    메인 분석.
    analysis_data : 본문 포함 고관여 게시글
    all_metas     : 전체 목록 메타 (날짜 분포 통계용)
    """
    from config import GALLERY_SUBTYPES, ANALYSIS_FOCUS_OPTIONS
    from collections import Counter

    subtype   = GALLERY_SUBTYPES.get(subtype_id, GALLERY_SUBTYPES["stable"])
    sl        = f"{subtype['emoji']} {subtype['label']}"
    sd        = subtype["desc"]
    sf        = subtype.get("analysis_focus", "")
    focus_lbl = ANALYSIS_FOCUS_OPTIONS.get(analysis_focus, ANALYSIS_FOCUS_OPTIONS["default"])

    date_cnt     = Counter(m["date"] for m in all_metas)
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
        total_posts=len(all_metas),
        concept_posts=sum(1 for m in all_metas if m.get("is_concept")),
        date_summary=date_summary,
    )
    return _call_gemini(prompt, json_mode=True, timeout=120)