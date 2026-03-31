"""
utils.py
역할: report_streamlit / report_notion 양쪽에서 공통으로 사용하는
      마크다운 정제·링크 추출·HTML 헬퍼 함수를 제공합니다.
"""
import re


# ── 텍스트 정제 ──────────────────────────────────────────────────
def strip_md(text: str) -> str:
    """마크다운 볼드(**), 이탤릭(*), 취소선(~~) 기호를 제거합니다."""
    s = str(text)
    s = s.replace("**", "").replace("~~", "").replace("~", "")
    # 단독 * (이탤릭) 만 제거 — URL 안의 * 는 놔둠
    s = re.sub(r"(?<!\*)\*(?!\*)", "", s)
    return s


def clean(text: str) -> str:
    """마크다운 링크 [label](url) → label 로 바꾸고 strip_md 적용."""
    return strip_md(re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", str(text)))


def extract_url(text: str) -> tuple[str, str]:
    """
    텍스트에서 첫 번째 마크다운 링크를 추출합니다.
    반환: (clean_label, url) — 링크가 없으면 (clean_text, "")
    """
    m = re.search(r"\[([^\]]+)\]\((https?://[^)]+)\)", str(text))
    return (m.group(1), m.group(2)) if m else (clean(text), "")


# ── HTML 헬퍼 ────────────────────────────────────────────────────
def link_btn(url: str, label: str = "📎 관련 게시글 보기",
             color: str = "#2980b9") -> str:
    """작은 링크 버튼 HTML. url이 없거나 http 아니면 빈 문자열 반환."""
    if not url or not url.startswith("http"):
        return ""
    return (
        f"<a href='{url}' target='_blank' style='"
        f"font-size:0.78rem;color:{color};text-decoration:none;"
        f"border:1px solid {color};border-radius:4px;"
        f"padding:2px 6px;margin-left:6px;white-space:nowrap;'>{label}</a>"
    )


def score_badge_html(score: int, suffix: str = "") -> str:
    """언급 빈도 점수(0-100) 컬러 배지 HTML."""
    score = max(0, min(100, int(score)))
    if score >= 80:
        bg, fc = "#fde8e8", "#c0392b"
    elif score >= 50:
        bg, fc = "#fef3cd", "#e67e22"
    else:
        bg, fc = "#e8f4fd", "#2980b9"
    return (
        f"<span style='background:{bg};color:{fc};"
        f"font-weight:700;padding:3px 10px;border-radius:12px;"
        f"font-size:0.9rem;'>{score}{suffix}</span>"
    )


def complaint_badge_html(score: int) -> str:
    """불만 점수(0-10) 컬러 배지 HTML."""
    score = max(0, min(10, int(score)))
    if score >= 7:
        bg, fc = "#fde8e8", "#c0392b"
    elif score >= 4:
        bg, fc = "#fef3cd", "#e67e22"
    else:
        bg, fc = "#e8f4fd", "#2980b9"
    return (
        f"<span style='background:{bg};color:{fc};"
        f"font-weight:700;padding:3px 10px;border-radius:12px;"
        f"font-size:0.9rem;'>{score}/10</span>"
    )