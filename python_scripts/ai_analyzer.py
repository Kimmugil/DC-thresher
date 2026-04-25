"""
ai_analyzer.py v6

[v6 변경]
- GEMINI_MODEL을 환경변수(GEMINI_MODEL)로 오버라이드 가능
- _call_gemini: timeout/5xx 오류 시 1회 재시도 (지수 백오프)
"""
import os, requests, json, re, time
from config import GEMINI_API_KEY
from ui_texts import build_diagnosis_ai_prompt, build_main_analysis_prompt

GEMINI_BASE  = "https://generativelanguage.googleapis.com/v1beta/models"
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def _call_gemini(prompt: str, json_mode: bool = True, timeout: int = 60, retries: int = 1) -> tuple:
    """공통 Gemini 호출. (result, error) 반환. timeout/5xx 발생 시 최대 retries회 재시도."""
    url = f"{GEMINI_BASE}/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}".strip()
    cfg = {"temperature": 0.1}
    if json_mode:
        cfg["responseMimeType"] = "application/json"

    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": cfg}
    raw = ""

    for attempt in range(retries + 1):
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
            snippet = raw[max(0, je.pos - 40):min(len(raw), je.pos + 40)] if raw else ""
            return None, f"JSON 파싱 오류: [... {snippet} ...]\n재분석 버튼을 눌러 다시 시도해 주세요."

        except requests.exceptions.Timeout:
            if attempt < retries:
                time.sleep(5 * (attempt + 1))
                continue
            return None, "요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."

        except requests.exceptions.HTTPError as e:
            code = e.response.status_code
            if code == 429:
                return None, "API 호출 한도 초과(429). 잠시 후 다시 시도해 주세요."
            if code >= 500 and attempt < retries:
                time.sleep(5)
                continue
            return None, f"Gemini API 오류 (HTTP {code})"

        except Exception as e:
            if attempt < retries:
                time.sleep(3)
                continue
            return None, str(e).replace(GEMINI_API_KEY or "", "***")

    return None, "알 수 없는 오류로 분석에 실패했습니다."


def diagnose_gallery_ai(gallery_name: str, top_words: list,
                         subtype_id: str, daily_avg: float) -> tuple:
    prompt = build_diagnosis_ai_prompt(gallery_name, top_words, subtype_id, daily_avg)
    result, err = _call_gemini(prompt, json_mode=True, timeout=30)
    if result and isinstance(result.get("suggested_focus"), list):
        result["suggested_focus"] = result["suggested_focus"][0] if result["suggested_focus"] else "default"
    return result, err


def _format_posts(post_data: list) -> str:
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
