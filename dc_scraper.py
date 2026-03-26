"""
dc_scraper.py v3 — 3단계 파이프라인

[데이터 흐름 설계 원칙 (탈곡기 개발 가이드 준수)]
  통계 집계 → 대상 선정 → 원문 수집

[3가지 함수]
  1. diagnose_gallery()     : Step1 — 빠른 진단 (목록만, 3~14일치 adaptive)
  2. count_posts_in_period(): Step2 — 기간별 게시글 수 실시간 체크 (목록만)
  3. run_dc_scraper()        : Step3 — 전체 목록 수집 후 개념글 본문 수집
"""

import requests
from bs4 import BeautifulSoup
import re, time, random, urllib3
from datetime import datetime, timedelta, date
from collections import Counter, defaultdict
from config import (
    SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX,
    DETAIL_DELAY_MIN, DETAIL_DELAY_MAX,
    REQUEST_TIMEOUT, BODY_MAX_CHARS,
    SUBTYPE_KEYWORDS,
    DIAG_MIN_POSTS, DIAG_MIN_DAYS, DIAG_MAX_DAYS,
    ANALYSIS_MIN_CONCEPT_POSTS,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


# ─────────────────────────────────────────────
# 공통 유틸
# ─────────────────────────────────────────────
def parse_dc_url(url: str):
    url = url.strip()
    match = re.search(
        r'gall\.dcinside\.com/(?:(mgallery|mini)/)?board/(?:lists|view).*?[\?&]id=([a-zA-Z0-9_]+)',
        url
    )
    if not match:
        return None, None
    s = match.group(1)
    if s == "mgallery": gal_type = "minor"
    elif s == "mini":   gal_type = "mini"
    else:               gal_type = "regular"
    return gal_type, match.group(2)


def _get_api_urls(gal_type: str):
    if gal_type == "minor":
        return ("https://gall.dcinside.com/mgallery/board/lists/",
                "https://gall.dcinside.com/mgallery/board/view/")
    elif gal_type == "mini":
        return ("https://gall.dcinside.com/mini/board/lists/",
                "https://gall.dcinside.com/mini/board/view/")
    return ("https://gall.dcinside.com/board/lists/",
            "https://gall.dcinside.com/board/view/")


def _get_post_url(gal_type, gal_id, post_no):
    if gal_type == "minor":
        return f"https://gall.dcinside.com/mgallery/board/view/?id={gal_id}&no={post_no}"
    if gal_type == "mini":
        return f"https://gall.dcinside.com/mini/board/view/?id={gal_id}&no={post_no}"
    return f"https://gall.dcinside.com/board/view/?id={gal_id}&no={post_no}"


def _parse_date(s: str) -> datetime:
    s = (s or "").strip()
    try:
        if not s:                                    return datetime.now()
        if re.match(r'^\d{2}:\d{2}$', s):           return datetime.now()
        if re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', s):
            return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        if re.match(r'^\d{2}\.\d{2}$', s):
            return datetime.strptime(s, "%m.%d").replace(year=datetime.now().year)
        if re.match(r'^\d{2}\.\d{2}\.\d{2}$', s):  return datetime.strptime(s, "%y.%m.%d")
        if re.match(r'^\d{4}\.\d{2}\.\d{2}$', s):  return datetime.strptime(s, "%Y.%m.%d")
    except Exception:
        pass
    return datetime.now()


def _get_date_str(row) -> str:
    e = row.select_one(".gall_date")
    if not e: return ""
    if e.has_attr("title") and e["title"].strip(): return e["title"].strip()
    return e.text.strip()


def _is_skip_row(row) -> bool:
    if "notice" in row.get("class", []): return True
    sub = row.select_one(".gall_subject")
    if sub and sub.text.strip() in {"공지","설문","AD","이슈"}: return True
    num = row.select_one(".gall_num")
    if not num or not num.text.strip().isdigit(): return True
    return False


def _is_concept_row(row) -> bool:
    if "recommend" in " ".join(row.get("class", [])): return True
    if row.select_one(".icon_recom, .icon_recomsmall, .bg_recomsmall"): return True
    return False


def _get_gallery_name(soup) -> str:
    try:
        raw = soup.select_one(".title_main").text.strip()
        return re.sub(r"\s*(갤러리|마이너 갤러리|미니 갤러리)$", "", raw)
    except Exception:
        return ""


def _get_soup(session, url, params):
    try:
        r = session.get(url, params=params, headers=HEADERS, verify=False, timeout=REQUEST_TIMEOUT)
        return BeautifulSoup(r.text, "html.parser")
    except Exception:
        return None


def _parse_row_meta(row) -> dict | None:
    """목록 행에서 메타 정보만 파싱 (본문 없음)."""
    num_e = row.select_one(".gall_num")
    if not num_e: return None
    post_no   = num_e.text.strip()
    post_date = _parse_date(_get_date_str(row))
    title_e   = row.select_one(".gall_tit a")
    title     = title_e.text.strip() if title_e else ""
    reply_e   = row.select_one(".reply_num")
    cc = int(re.sub(r"[^0-9]","",reply_e.text)) if reply_e and re.sub(r"[^0-9]","",reply_e.text) else 0
    auth_e    = row.select_one(".gall_writer")
    ip_e      = auth_e.select_one(".ip") if auth_e else None
    nk_e      = auth_e.select_one(".nickname") if auth_e else None
    author    = nk_e.text.strip() if nk_e else "알 수 없음"
    return {
        "post_no":       post_no,
        "title":         title,
        "date":          post_date.strftime("%Y-%m-%d"),
        "_dt":           post_date,
        "is_concept":    _is_concept_row(row),
        "comment_count": cc,
        "author":        f"{author} ({ip_e.text.strip()})" if ip_e else author,
        "user_type":     "유동" if ip_e else "고닉",
        "post_url":      "",  # 호출측에서 채움
    }


# ─────────────────────────────────────────────
# Step 1: 빠른 갤러리 진단
# 목표: "이 갤러리가 어떤 곳인가" 파악
# 전략: 최신 글부터 읽다가 DIAG_MIN_POSTS 초과 AND DIAG_MIN_DAYS 이상 되는
#       날 경계(00:00)에서 종료. 최대 DIAG_MAX_DAYS 일치.
# ─────────────────────────────────────────────
def diagnose_gallery(url: str, progress_cb=None) -> dict:
    gal_type, gal_id = parse_dc_url(url)
    if not gal_id:
        return {"error": "유효하지 않은 URL 형식입니다.", "gallery_id": None}

    session  = requests.Session()
    list_url, _ = _get_api_urls(gal_type)

    soup_init = _get_soup(session, list_url, {"id": gal_id})
    gallery_name = (_get_gallery_name(soup_init) if soup_init else "") or gal_id

    if progress_cb: progress_cb(f"[{gallery_name}] 진단 시작...", 5)

    hard_cutoff = datetime.now() - timedelta(days=DIAG_MAX_DAYS)
    all_rows    = []   # {"date", "_dt", "is_concept", "title", "user_type", ...}
    seen_nos    = set()
    old_streak  = 0

    done = False
    for page in range(1, 300):
        if done: break
        soup = _get_soup(session, list_url, {"id": gal_id, "page": page})
        if not soup: break
        rows = soup.select("tr.ub-content.us-post")
        if not rows: break

        page_added = 0
        for row in rows:
            if _is_skip_row(row): continue
            meta = _parse_row_meta(row)
            if not meta: continue
            if meta["post_no"] in seen_nos: continue

            if meta["_dt"] < hard_cutoff:
                old_streak += 1
                if old_streak >= 5: old_streak = 9999; break
                continue
            old_streak = 0

            seen_nos.add(meta["post_no"])
            all_rows.append(meta)
            page_added += 1

            # ── 실시간 종료 체크 ─────────────────────────────────────
            # 조건 A: DIAG_MIN_POSTS개 이상 수집 (글 수 기준 상한)
            # 조건 B: 날짜 span >= DIAG_MIN_DAYS 이상 AND 최소 50개 수집
            # A OR B 중 먼저 충족되는 시점의 날짜 경계(00:00)에서 종료
            # → 메이플(일 500개): A가 200개 시점에서 먼저 발동
            # → 소형(일 5개):   B가 3일치 시점에서 먼저 발동
            if len(all_rows) >= 2:
                newest_dt = all_rows[0]["_dt"]
                oldest_dt = meta["_dt"]
                span_days = (newest_dt - oldest_dt).days

                cond_a = len(all_rows) >= DIAG_MIN_POSTS
                cond_b = span_days >= DIAG_MIN_DAYS and len(all_rows) >= 50

                if cond_a or cond_b:
                    done = True
                    break

        if progress_cb:
            progress_cb(f"진단 중... ({len(all_rows)}개 수집)", min(80, 5 + len(all_rows)//10))

        if old_streak >= 9999: break
        if page_added == 0: break
        time.sleep(random.uniform(SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX))

    if not all_rows:
        return {"error": "게시글을 찾을 수 없습니다.", "gallery_id": gal_id}

    # ── 종료 경계 결정: "N개 이상 AND M일 이상"이 되는 날 경계 찾기 ──
    all_rows.sort(key=lambda x: x["_dt"], reverse=True)  # 최신순 정렬
    cutoff_dt = _find_day_boundary(all_rows)

    # cutoff_dt 이후 글만 사용
    diag_rows = [r for r in all_rows if r["_dt"] >= cutoff_dt]

    # ── 집계 ──
    date_counts = Counter(r["date"] for r in diag_rows)
    concept_cnt = sum(1 for r in diag_rows if r["is_concept"])
    gonik_count = sum(1 for r in diag_rows if r["user_type"] == "고닉")
    total       = len(diag_rows)
    daily_avg   = total / max(len(date_counts), 1)
    gonik_ratio = gonik_count / max(total, 1)

    title_words = []
    for r in diag_rows:
        if r["title"]:
            title_words.extend(
                w.lower() for w in re.findall(r"[가-힣a-zA-Z]{2,}", r["title"]))

    SW = {"이","그","저","이거","ㅋㅋ","ㅠㅠ","진짜","뭔","왜","좀","다","하는","합니다","이거"}
    wf = Counter(w for w in title_words if w not in SW)
    top_words = [w for w, _ in wf.most_common(15)]

    all_t = " ".join(title_words)
    subtype_scores = {
        s: sum(all_t.count(k.lower()) for k in ks)
        for s, ks in SUBTYPE_KEYWORDS.items()
    }

    # 수집된 실제 날짜 범위
    diag_dates = sorted(date_counts.keys())
    diag_start = diag_dates[0] if diag_dates else ""
    diag_end   = diag_dates[-1] if diag_dates else ""

    if progress_cb: progress_cb("진단 완료!", 100)

    return {
        "gallery_id":       gal_id,
        "gallery_name":     gallery_name,
        "gal_type":         gal_type,
        "total_rows":       total,
        "concept_total":    concept_cnt,
        "date_counts":      dict(date_counts),
        "daily_avg":        round(daily_avg, 1),
        "gonik_ratio":      round(gonik_ratio, 3),
        "top_title_words":  top_words,
        "subtype_scores":   subtype_scores,
        "diag_start":       diag_start,
        "diag_end":         diag_end,
        "error":            None,
    }


def _find_day_boundary(rows_newest_first: list) -> datetime:
    """
    rows를 최신순으로 읽다가 DIAG_MIN_POSTS 초과 & DIAG_MIN_DAYS 이상이 되는
    날짜 경계(해당일 00:00:00)를 반환.
    DIAG_MAX_DAYS 초과 시 hard cutoff 반환.
    """
    if not rows_newest_first:
        return datetime.now() - timedelta(days=1)

    newest_dt = rows_newest_first[0]["_dt"]
    for i, row in enumerate(rows_newest_first):
        days_span = (newest_dt - row["_dt"]).days
        count     = i + 1
        if count >= DIAG_MIN_POSTS and days_span >= DIAG_MIN_DAYS:
            # 해당 날짜의 00:00으로 내림
            boundary_date = row["_dt"].date()
            return datetime.combine(boundary_date, datetime.min.time())

    # 조건을 못 채우면 전체 사용
    return datetime.combine(rows_newest_first[-1]["_dt"].date(), datetime.min.time())


# ─────────────────────────────────────────────
# Step 2: 기간별 게시글 수 실시간 체크 (목록만)
# 분석 기간 선택 시 "총 n개 게시글을 분석합니다" 표시용
# ─────────────────────────────────────────────
def count_posts_in_period(url: str, days_limit: int, progress_cb=None) -> dict:
    """
    빠른 게시글 수 집계. 본문 수집 없음.
    반환: {"total": n, "concept": n, "normal": n, "date_counts": {...}}
    """
    gal_type, gal_id = parse_dc_url(url)
    if not gal_id:
        return {"error": "URL 오류", "total": 0}

    session  = requests.Session()
    list_url, _ = _get_api_urls(gal_type)
    cutoff   = datetime.now() - timedelta(days=days_limit)
    total    = 0
    concept  = 0
    date_counts = Counter()
    seen_nos = set()
    old_str  = 0

    for page in range(1, 300):
        soup = _get_soup(session, list_url, {"id": gal_id, "page": page})
        if not soup: break
        rows = soup.select("tr.ub-content.us-post")
        if not rows: break

        page_added = 0
        for row in rows:
            if _is_skip_row(row): continue
            meta = _parse_row_meta(row)
            if not meta: continue
            if meta["post_no"] in seen_nos: continue

            if meta["_dt"] < cutoff:
                old_str += 1
                if old_str >= 5: old_str = 9999; break
                continue
            old_str = 0
            seen_nos.add(meta["post_no"])
            total += 1
            date_counts[meta["date"]] += 1
            if meta["is_concept"]: concept += 1
            page_added += 1

        if progress_cb: progress_cb(total)
        if old_str >= 9999: break
        if page_added == 0: break
        time.sleep(random.uniform(SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX))

    return {
        "total":       total,
        "concept":     concept,
        "normal":      total - concept,
        "date_counts": dict(date_counts),
    }


# ─────────────────────────────────────────────
# Step 3: 수집 + 본문 추출
# 전략:
#   1) 기간 내 전체 목록 수집 (날짜별 분포 확정)
#   2) 개념글 본문 우선 수집 (AI 분석용)
#   3) 개념글 < ANALYSIS_MIN_CONCEPT_POSTS 이면 고댓글 일반글 보충
# ─────────────────────────────────────────────
def run_dc_scraper(url: str, days_limit: int, progress_cb=None) -> dict:
    """
    max_posts 파라미터 제거 — 기간 내 모든 글의 날짜/수 통계는 전수 수집,
    AI 분석용 본문은 개념글 우선으로 자동 결정 (설정값: config.py).
    """
    gal_type, gal_id = parse_dc_url(url)
    if not gal_id: raise ValueError("유효하지 않은 URL 형식입니다.")

    session  = requests.Session()
    list_url, view_url = _get_api_urls(gal_type)

    soup_init = _get_soup(session, list_url, {"id": gal_id})
    gallery_name = (_get_gallery_name(soup_init) if soup_init else "") or gal_id

    if progress_cb: progress_cb("목록 수집 시작...", 5)

    cutoff     = datetime.now() - timedelta(days=days_limit)
    all_metas  = []
    seen_nos   = set()
    old_streak = 0

    # ── Phase 1: 전체 목록 수집 ────────────────────────────────────
    for page in range(1, 500):
        soup = _get_soup(session, list_url, {"id": gal_id, "page": page})
        if not soup: break
        rows = soup.select("tr.ub-content.us-post")
        if not rows: break

        page_added = 0
        for row in rows:
            if _is_skip_row(row): continue
            meta = _parse_row_meta(row)
            if not meta: continue
            if meta["post_no"] in seen_nos: continue

            if meta["_dt"] < cutoff:
                old_streak += 1
                if old_streak >= 5: old_streak = 9999; break
                continue
            old_streak = 0
            seen_nos.add(meta["post_no"])
            meta["post_url"] = _get_post_url(gal_type, gal_id, meta["post_no"])
            all_metas.append(meta)
            page_added += 1

        if progress_cb and len(all_metas) % 50 == 0:
            progress_cb(f"목록 수집 중... ({len(all_metas)}개)", min(30, 5 + len(all_metas)//20))

        if old_streak >= 9999: break
        if page_added == 0: break
        time.sleep(random.uniform(SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX))

    if not all_metas:
        raise Exception(f"최근 {days_limit}일 이내 게시글이 없습니다.")

    if progress_cb: progress_cb(f"목록 완료 ({len(all_metas)}개). 분석용 본문 수집 시작...", 32)

    # ── Phase 2: 날짜별 분포 (전체 목록 기반 — 정확한 분포) ──────
    date_counts = Counter(m["date"] for m in all_metas)
    concept_metas = [m for m in all_metas if m["is_concept"]]
    normal_metas  = [m for m in all_metas if not m["is_concept"]]

    # ── Phase 3: AI 분석용 본문 수집 대상 결정 ──────────────────
    # 개념글 우선. 부족하면 고댓글 일반글 보충.
    analysis_targets = list(concept_metas)  # 개념글 전체

    if len(analysis_targets) < ANALYSIS_MIN_CONCEPT_POSTS:
        # 고댓글 순 일반글 보충
        need    = ANALYSIS_MIN_CONCEPT_POSTS - len(analysis_targets)
        extras  = sorted(normal_metas, key=lambda x: -x["comment_count"])[:need]
        analysis_targets.extend(extras)

    # 날짜순 정렬
    analysis_targets.sort(key=lambda x: x["_dt"])

    # ── Phase 4: 본문 수집 ───────────────────────────────────────
    results = []
    total   = len(analysis_targets)
    for idx, meta in enumerate(analysis_targets):
        if progress_cb and idx % 5 == 0:
            progress_cb(f"본문 추출 중... ({idx+1}/{total})", 32 + int(idx/total*63))
        body = _fetch_body(session, view_url, gal_id, meta["post_no"])
        clean = {k: v for k, v in meta.items() if k != "_dt"}
        results.append({**clean, "body": body})
        time.sleep(random.uniform(DETAIL_DELAY_MIN, DETAIL_DELAY_MAX))

    dates = sorted(m["date"] for m in all_metas)
    return {
        "gallery_id":        gal_id,
        "gallery_name":      gallery_name,
        "gal_type":          gal_type,
        "all_metas":         [{k:v for k,v in m.items() if k!="_dt"} for m in all_metas],
        "analysis_data":     results,  # 본문 포함 (개념글 위주)
        "date_counts":       dict(date_counts),
        "total_posts":       len(all_metas),
        "concept_posts":     len(concept_metas),
        "normal_posts":      len(normal_metas),
        "analysis_count":    len(results),
        "date_range_str":    f"{dates[0]} ~ {dates[-1]}" if dates else "기간 알 수 없음",
    }


def _fetch_body(session, view_url, gal_id, post_no) -> str:
    try:
        r    = session.get(view_url, params={"id": gal_id, "no": post_no},
                           headers=HEADERS, verify=False, timeout=REQUEST_TIMEOUT)
        soup = BeautifulSoup(r.text, "html.parser")
        bd   = soup.select_one(".write_div")
        if not bd: return "본문 누락"
        return re.sub(r"\s+", " ", bd.get_text(separator=" ").strip())[:BODY_MAX_CHARS]
    except Exception as e:
        return f"본문 수집 오류: {e}"