"""
gallery_analyzer.py
역할: 진단 데이터를 받아 갤러리 서브타입을 판별하고
      분석에 필요한 메타 정보를 정리합니다.

[v2 변경]
- guess_game_name: 갤러리 페이지 제목(HTML h1)을 최우선으로 사용,
  정제 후에도 남는 텍스트를 그대로 반환해 AI 추정 오류를 최소화
"""

import re
from config import GALLERY_SUBTYPES, SUBTYPE_KEYWORDS
from collections import Counter

# 제거할 불필요 접미사 패턴 (갤러리명에서 게임명만 남기기)
_STRIP_PATTERN = re.compile(
    r"\s*(마이너\s*갤러리|미니\s*갤러리|갤러리|마갤|갤|공식|팬|fan\s*cafe|community|DC)\s*$",
    re.IGNORECASE,
)


def detect_subtype(diag: dict) -> str:
    """
    진단 결과(diag)를 받아 가장 적합한 서브타입 ID를 반환합니다.
    """
    scores        = diag.get("subtype_scores", {})
    daily_avg     = diag.get("daily_avg", 0)
    date_counts   = diag.get("date_counts", {})

    sorted_dates = sorted(date_counts.keys())
    if len(sorted_dates) >= 14:
        recent_7    = sum(date_counts.get(d, 0) for d in sorted_dates[-7:])
        prev_7      = sum(date_counts.get(d, 0) for d in sorted_dates[-14:-7])
        trend_ratio = recent_7 / max(prev_7, 1)
    else:
        trend_ratio = 1.0

    pre_score     = scores.get("pre_launch", 0)
    early_score   = scores.get("early_launch", 0)
    issue_score   = scores.get("issue_burst", 0)
    decline_score = scores.get("decline", 0)
    stable_score  = scores.get("stable", 0)
    total_score   = max(sum(scores.values()), 1)

    play_based = issue_score + early_score
    if pre_score / total_score > 0.35 and play_based < pre_score and daily_avg < 30:
        return "pre_launch"
    if decline_score / total_score > 0.3 and trend_ratio < 0.7:
        return "decline"
    if issue_score / total_score > 0.35 or (issue_score > stable_score and trend_ratio > 1.4):
        return "issue_burst"
    if early_score / total_score > 0.25 and trend_ratio > 1.2:
        return "early_launch"
    return "stable"


def get_subtype_info(subtype_id: str) -> dict:
    return GALLERY_SUBTYPES.get(subtype_id, GALLERY_SUBTYPES["stable"])


def detect_spike_dates(date_counts: dict, threshold: float = 1.8) -> list:
    if not date_counts:
        return []
    values = list(date_counts.values())
    avg    = sum(values) / len(values)
    return [d for d, cnt in sorted(date_counts.items()) if cnt >= avg * threshold and cnt > 2]


def guess_game_name(gallery_name: str, top_words: list) -> str:
    """
    갤러리명에서 불필요한 접미사를 제거한 이름을 우선 반환합니다.
    갤러리명이 ID 수준(영문 슬러그)이거나 너무 짧을 때만 top_words를 보조로 사용합니다.
    AI가 topic_guess를 제시하더라도, 이 함수 반환값을 초기값으로 쓰고
    AI 결과로 덮어쓰는 방식은 app.py에서 제어합니다.
    """
    # 1순위: 갤러리명에서 접미사 제거
    cleaned = _STRIP_PATTERN.sub("", gallery_name).strip()

    # 정제 후 2자 이상이면 그대로 사용
    if len(cleaned) >= 2:
        return cleaned

    # 2순위: 영문 슬러그처럼 의미 파악이 어려운 경우 — 빈도 상위 한글/영문 단어 사용
    candidates = [w for w in top_words if len(w) >= 2]
    if candidates:
        return candidates[0]

    return gallery_name