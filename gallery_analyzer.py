"""
gallery_analyzer.py
역할: 진단 데이터를 받아 갤러리 서브타입을 판별하고
      분석에 필요한 메타 정보를 정리합니다.
"""

import re
from config import GALLERY_SUBTYPES, SUBTYPE_KEYWORDS
from collections import Counter


def detect_subtype(diag: dict) -> str:
    """
    진단 결과(diag)를 받아 가장 적합한 서브타입 ID를 반환합니다.
    판별 우선순위:
      1) pre_launch  — 플레이 기반 불만 키워드 없음 + 기대 키워드 다수
      2) decline     — 일평균 글 수 적고 감소 추세 + 이탈 키워드 다수
      3) issue_burst — 이슈 키워드 점수 압도적
      4) early_launch — 출시 초기 키워드 + 리젠 급증
      5) stable      — 나머지 기본값
    """
    scores    = diag.get("subtype_scores", {})
    daily_avg = diag.get("daily_avg", 0)
    concept_ratio = diag.get("concept_ratio", 0)
    date_counts   = diag.get("date_counts", {})

    # 날짜별 글 수 추세 (최근 7일 vs 이전 7일)
    sorted_dates = sorted(date_counts.keys())
    if len(sorted_dates) >= 14:
        recent_7 = sum(date_counts.get(d, 0) for d in sorted_dates[-7:])
        prev_7   = sum(date_counts.get(d, 0) for d in sorted_dates[-14:-7])
        trend_ratio = recent_7 / max(prev_7, 1)
    else:
        trend_ratio = 1.0

    pre_score     = scores.get("pre_launch", 0)
    early_score   = scores.get("early_launch", 0)
    issue_score   = scores.get("issue_burst", 0)
    decline_score = scores.get("decline", 0)
    stable_score  = scores.get("stable", 0)
    total_score   = max(sum(scores.values()), 1)

    # --- 판별 로직 ---

    # 1. 출시 전 기대형: 전체 글이 적고, 플레이 기반 불만 거의 없음, 기대 키워드 상위
    play_based_keywords = issue_score + scores.get("early_launch", 0)
    if (pre_score / total_score > 0.35
            and play_based_keywords < pre_score
            and daily_avg < 30):
        return "pre_launch"

    # 2. 쇠퇴기형: 리젠 감소 + 이탈 키워드 높음
    if decline_score / total_score > 0.3 and trend_ratio < 0.7:
        return "decline"

    # 3. 이슈 폭발형: 이슈 키워드가 압도적이거나 트렌드 급증
    if issue_score / total_score > 0.35 or (issue_score > stable_score and trend_ratio > 1.4):
        return "issue_burst"

    # 4. 출시 초기형: 출시 키워드 높고 트렌드 상승 중
    if early_score / total_score > 0.25 and trend_ratio > 1.2:
        return "early_launch"

    # 5. 안정기형: 공략/정보 키워드가 가장 높음
    return "stable"


def get_subtype_info(subtype_id: str) -> dict:
    """서브타입 ID에 해당하는 표시 정보를 반환합니다."""
    return GALLERY_SUBTYPES.get(subtype_id, GALLERY_SUBTYPES["stable"])


def detect_spike_dates(date_counts: dict, threshold: float = 1.8) -> list:
    """
    날짜별 글 수에서 스파이크(급증) 날짜를 감지합니다.
    평균 대비 threshold 배 이상인 날짜를 반환합니다.
    """
    if not date_counts:
        return []
    values = list(date_counts.values())
    avg    = sum(values) / len(values)
    return [
        d for d, cnt in sorted(date_counts.items())
        if cnt >= avg * threshold and cnt > 2
    ]


def guess_game_name(gallery_name: str, top_words: list) -> str:
    """
    갤러리명과 자주 등장한 단어 목록을 바탕으로
    게임명 후보를 추정합니다. 실제 확정은 AI 또는 사용자가 합니다.
    """
    # 갤러리명에서 게임명 힌트 추출
    clean = re.sub(r"(갤러리|마이너|미니|공식|팬|fan|community)", "", gallery_name, flags=re.IGNORECASE).strip()

    # 빈도 높은 단어 중 게임명일 가능성 높은 것 (2글자 이상 고유명사)
    candidates = [w for w in top_words if len(w) >= 2]

    if clean:
        return clean
    elif candidates:
        return candidates[0]
    return gallery_name



