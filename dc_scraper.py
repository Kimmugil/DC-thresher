"""
dc_scraper.py v7

[v7 변경]
- _gname(): .title_main 실패 시 <title> 태그에서 갤러리명 추출 (폴백 강화)
  → '메이플 키우기 갤러리' 같이 페이지 타이틀에 명확히 나오는 경우 정확 추출
- 그 외 로직은 v6 유지
"""

import requests
from bs4 import BeautifulSoup
import re, time, random, urllib3
from datetime import datetime, timedelta
from collections import Counter
from config import (
    SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX,
    DETAIL_DELAY_MIN, DETAIL_DELAY_MAX,
    REQUEST_TIMEOUT, BODY_MAX_CHARS, SUBTYPE_KEYWORDS,
    DIAG_MIN_POSTS, DIAG_MIN_DAYS, DIAG_MAX_DAYS,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── 상수 ──────────────────────────────────────────────────────────
MAX_BODY_POSTS   = 50
TOP_PCT          = 0.10
MIN_BODY_POSTS   = 20
SPAM_MIN_TITLE   = 4

WEB_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}
APP_HEADERS = {
    "User-Agent": "dcinside.app",
    "Referer":    "http://www.dcinside.com",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
}
APP_ID   = "aW0vNGVja05kc0hTSllkTXBqbGFyVzRQZEFvNml6cEJ2enk1VVYxSml6cz0="
APP_LIST = "http://app.dcinside.com/api/gall_list_new.php"

# 갤러리명에서 제거할 접미사 패턴
_GNAME_STRIP = re.compile(
    r"\s*(마이너\s*갤러리|미니\s*갤러리|갤러리)\s*$",
    re.IGNORECASE,
)


# ── URL 유틸 ──────────────────────────────────────────────────────
def parse_dc_url(url: str):
    m = re.search(
        r'gall\.dcinside\.com/(?:(mgallery|mini)/)?board/(?:lists|view).*?[\?&]id=([a-zA-Z0-9_]+)',
        url.strip()
    )
    if not m: return None, None
    s = m.group(1)
    gal_type = {"mgallery": "minor", "mini": "mini"}.get(s, "regular")
    return gal_type, m.group(2)


def _urls(t):
    if t == "minor": return "https://gall.dcinside.com/mgallery/board/lists/", "https://gall.dcinside.com/mgallery/board/view/"
    if t == "mini":  return "https://gall.dcinside.com/mini/board/lists/",     "https://gall.dcinside.com/mini/board/view/"
    return "https://gall.dcinside.com/board/lists/", "https://gall.dcinside.com/board/view/"


def _post_url(t, gid, no):
    if t == "minor": return f"https://gall.dcinside.com/mgallery/board/view/?id={gid}&no={no}"
    if t == "mini":  return f"https://gall.dcinside.com/mini/board/view/?id={gid}&no={no}"
    return f"https://gall.dcinside.com/board/view/?id={gid}&no={no}"


# ── 날짜 파싱 ─────────────────────────────────────────────────────
def _parse_date(s):
    s = (s or "").strip()
    now = datetime.now()
    try:
        if not s or re.match(r'^\d{2}:\d{2}$', s): return now
        for fmt in ("%Y-%m-%d %H:%M:%S", "%m.%d", "%y.%m.%d", "%Y.%m.%d"):
            try:
                d = datetime.strptime(s, fmt)
                return d.replace(year=now.year) if fmt == "%m.%d" else d
            except ValueError:
                continue
    except Exception:
        pass
    return now


# ── 웹 HTML 파싱 ──────────────────────────────────────────────────
def _gname(soup):
    """
    갤러리명 추출 우선순위:
    1) .title_main 요소 (갤러리 페이지 상단 h1)
    2) <title> 태그 (예: '메이플 키우기 갤러리 - 디씨인사이드')
    3) 둘 다 실패하면 빈 문자열
    """
    # 1순위: .title_main
    try:
        raw = soup.select_one(".title_main").text.strip()
        return _GNAME_STRIP.sub("", raw).strip()
    except Exception:
        pass

    # 2순위: <title> 태그
    try:
        title_tag = soup.select_one("title")
        if title_tag:
            raw = title_tag.text.strip()
            # 예: "메이플 키우기 갤러리 - 디씨인사이드" → "메이플 키우기 갤러리"
            raw = raw.split(" - ")[0].strip()
            raw = raw.split(" | ")[0].strip()
            return _GNAME_STRIP.sub("", raw).strip()
    except Exception:
        pass

    return ""


def _soup(sess, url, params):
    try:
        r = sess.get(url, params=params, headers=WEB_HEADERS, verify=False, timeout=REQUEST_TIMEOUT)
        return BeautifulSoup(r.text, "html.parser")
    except Exception:
        return None


def _skip(row):
    if "notice" in row.get("class", []): return True
    sub = row.select_one(".gall_subject")
    if sub and sub.text.strip() in {"공지", "설문", "AD", "이슈"}: return True
    num = row.select_one(".gall_num")
    return not num or not num.text.strip().isdigit()


def _date_str(row):
    e = row.select_one(".gall_date")
    if not e: return ""
    return e.get("title", "").strip() or e.text.strip()


def _is_spam(title: str) -> bool:
    t = title.strip()
    if len(t) < SPAM_MIN_TITLE: return True
    if re.match(r'^[ㄱ-ㅎㅏ-ㅣ\s]+$', t): return True
    return False


def _parse_row(row, gtype, gid):
    ne = row.select_one(".gall_num")
    if not ne: return None
    dt    = _parse_date(_date_str(row))
    te    = row.select_one(".gall_tit a")
    title = te.text.strip() if te else ""
    re_e  = row.select_one(".reply_num")
    cc    = int(re.sub(r"[^0-9]", "", re_e.text)) if re_e and re.sub(r"[^0-9]", "", re_e.text) else 0
    ae    = row.select_one(".gall_writer")
    ip_e  = ae.select_one(".ip") if ae else None
    nk_e  = ae.select_one(".nickname") if ae else None
    nm    = nk_e.text.strip() if nk_e else "알 수 없음"
    classes     = " ".join(row.get("class", []))
    is_concept  = "recommend" in classes or bool(row.select_one(".icon_recom, .icon_recomsmall"))
    return {
        "post_no":       ne.text.strip(),
        "title":         title,
        "date":          dt.strftime("%Y-%m-%d"),
        "_dt":           dt,
        "is_concept":    is_concept,
        "comment_count": cc,
        "author":        f"{nm} ({ip_e.text.strip()})" if ip_e and nk_e else nm,
        "user_type":     "유동" if ip_e else "고닉",
        "post_url":      _post_url(gtype, gid, ne.text.strip()),
    }


# ── 앱 API 개념글 시도 ────────────────────────────────────────────
def _try_concepts_api(gid, gtype, cutoff):
    results = []; seen = set(); sess = requests.Session()
    for page in range(1, 100):
        try:
            r = sess.get(APP_LIST,
                         params={"id": gid, "page": str(page), "app_id": APP_ID, "recommend": "1"},
                         headers=APP_HEADERS, verify=False, timeout=REQUEST_TIMEOUT)
            raw = r.json()
        except Exception:
            break
        if isinstance(raw, list):
            posts = raw
        elif isinstance(raw, dict):
            candidate = None
            for k in ("gall_list", "data", "list", "posts", "result"):
                if k in raw: candidate = raw[k]; break
            if candidate is None:
                for v in raw.values():
                    if isinstance(v, list) and v: candidate = v; break
            posts = candidate if isinstance(candidate, list) else []
        else:
            posts = []
        if not posts: break

        added = 0; old_seq = 0
        for p in posts:
            if not isinstance(p, dict): continue
            no = str(p.get("no") or p.get("gall_num") or p.get("num") or "")
            if not no or no in seen: continue
            raw_d = (p.get("date_time") or p.get("reg_date") or p.get("gall_date") or p.get("date") or "").strip()
            dt = _parse_date(raw_d)
            if dt < cutoff:
                old_seq += 1
                if old_seq >= 3: added = -1; break
                continue
            old_seq = 0
            seen.add(no)
            title = (p.get("subject") or p.get("gall_subject") or p.get("title") or "").strip()
            try: cc = int(re.sub(r"[^0-9]", "", str(p.get("reply_num") or p.get("comment_cnt") or "0")) or "0")
            except: cc = 0
            results.append({
                "post_no": no, "title": title,
                "date": dt.strftime("%Y-%m-%d"), "_dt": dt,
                "is_concept": True, "comment_count": cc,
                "author": p.get("name") or p.get("gall_writer") or "알 수 없음",
                "user_type": "고닉" if (p.get("member_id") or p.get("user_id")) else "유동",
                "post_url": _post_url(gtype, gid, no),
            })
            added += 1
        if added <= 0: break
        time.sleep(random.uniform(SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX))
    return results


# ── 핵심 게시글 선정 ──────────────────────────────────────────────
def _select_core(all_metas: list) -> list:
    filtered = [m for m in all_metas if not _is_spam(m["title"])]
    if not filtered:
        filtered = all_metas
    sorted_m = sorted(filtered, key=lambda x: -x["comment_count"])
    top_n    = max(MIN_BODY_POSTS, min(MAX_BODY_POSTS, int(len(filtered) * TOP_PCT)))
    return sorted(sorted_m[:top_n], key=lambda x: x["_dt"])


# ── 진단 ─────────────────────────────────────────────────────────
def diagnose_gallery(url, progress_cb=None):
    gtype, gid = parse_dc_url(url)
    if not gid: return {"error": "유효하지 않은 URL 형식입니다.", "gallery_id": None}

    sess = requests.Session()
    lu, _ = _urls(gtype)
    s0 = _soup(sess, lu, {"id": gid})
    gname = (_gname(s0) if s0 else "") or gid
    if progress_cb: progress_cb(f"[{gname}] 진단 중...", 5)

    cutoff = datetime.now() - timedelta(days=DIAG_MAX_DAYS)
    rows = []; seen = set(); old_s = 0; done = False

    for page in range(1, 300):
        if done: break
        s = _soup(sess, lu, {"id": gid, "page": page})
        if not s: break
        trs = s.select("tr.ub-content.us-post")
        if not trs: break
        padded = 0
        for tr in trs:
            if _skip(tr): continue
            m = _parse_row(tr, gtype, gid)
            if not m or m["post_no"] in seen: continue
            if m["_dt"] < cutoff:
                old_s += 1
                if old_s >= 5: old_s = 9999; break
                continue
            old_s = 0
            seen.add(m["post_no"]); rows.append(m); padded += 1
            if len(rows) >= 2:
                span = (rows[0]["_dt"] - m["_dt"]).days
                if len(rows) >= DIAG_MIN_POSTS or (span >= DIAG_MIN_DAYS and len(rows) >= 50):
                    done = True; break
        if progress_cb: progress_cb(f"진단 중... ({len(rows)}개)", min(85, 5 + len(rows) // 5))
        if old_s >= 9999 or padded == 0: break
        time.sleep(random.uniform(SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX))

    if not rows: return {"error": "게시글을 찾을 수 없습니다.", "gallery_id": gid}
    rows.sort(key=lambda x: x["_dt"], reverse=True)

    dc    = Counter(r["date"] for r in rows)
    daily = len(rows) / max(len(dc), 1)
    words = []
    for r in rows:
        if r["title"]: words.extend(w.lower() for w in re.findall(r"[가-힣a-zA-Z]{2,}", r["title"]))
    SW = {"이", "그", "저", "이거", "ㅋㅋ", "ㅠㅠ", "진짜", "뭔", "왜", "좀", "다", "하는", "합니다"}
    wf     = Counter(w for w in words if w not in SW)
    all_t  = " ".join(words)
    dates  = sorted(dc.keys())
    if progress_cb: progress_cb("진단 완료!", 100)
    return {
        "gallery_id": gid, "gallery_name": gname, "gal_type": gtype,
        "total_rows": len(rows), "daily_avg": round(daily, 1),
        "date_counts": dict(dc),
        "diag_start": dates[0] if dates else "",
        "diag_end":   dates[-1] if dates else "",
        "top_title_words": [w for w, _ in wf.most_common(15)],
        "subtype_scores": {s: sum(all_t.count(k.lower()) for k in ks) for s, ks in SUBTYPE_KEYWORDS.items()},
        "error": None,
    }


# ── 수집 메인 ────────────────────────────────────────────────────
def run_dc_scraper(url, days_limit, progress_cb=None):
    gtype, gid = parse_dc_url(url)
    if not gid: raise ValueError("유효하지 않은 URL 형식입니다.")

    sess = requests.Session()
    lu, vu = _urls(gtype)
    s0 = _soup(sess, lu, {"id": gid})
    gname = (_gname(s0) if s0 else "") or gid
    if progress_cb: progress_cb("목록 수집 시작...", 3)

    cutoff    = datetime.now() - timedelta(days=days_limit)
    cutoff_14 = datetime.now() - timedelta(days=14)
    collect_co = min(cutoff, cutoff_14)

    api_concepts = _try_concepts_api(gid, gtype, cutoff)
    if progress_cb:
        msg = f"개념글 {len(api_concepts)}개 수집." if api_concepts else "전체 목록 수집 중..."
        progress_cb(f"{msg}", 12)

    all_metas = []; seen = set(); old_s = 0; done = False
    for page in range(1, 500):
        if done: break
        s = _soup(sess, lu, {"id": gid, "page": page})
        if not s: break
        trs = s.select("tr.ub-content.us-post")
        if not trs: break
        padded = 0
        for tr in trs:
            if _skip(tr): continue
            m = _parse_row(tr, gtype, gid)
            if not m or m["post_no"] in seen: continue
            if m["_dt"] < collect_co:
                old_s += 1
                if old_s >= 5: done = True; break
                continue
            old_s = 0; seen.add(m["post_no"]); all_metas.append(m); padded += 1
        if padded == 0: break
        time.sleep(random.uniform(SCRAPE_DELAY_MIN * 0.4, SCRAPE_DELAY_MAX * 0.4))

    web_nos = {m["post_no"]: i for i, m in enumerate(all_metas)}
    for cp in api_concepts:
        if cp["post_no"] in web_nos:
            all_metas[web_nos[cp["post_no"]]]["is_concept"] = True
        elif cp["_dt"] >= collect_co:
            all_metas.append(cp)

    analysis_metas = [m for m in all_metas if m["_dt"] >= cutoff]
    fourteen_metas = [m for m in all_metas if m["_dt"] >= cutoff_14]

    core          = _select_core(analysis_metas)
    concept_count = sum(1 for m in analysis_metas if m.get("is_concept"))

    if not core:
        raise Exception(f"최근 {days_limit}일 이내 분석 가능한 게시글이 없습니다.")

    if progress_cb: progress_cb(f"본문 수집 시작... ({len(core)}개)", 30)

    results = []
    for idx, m in enumerate(core):
        if progress_cb:
            pct = 30 + int(idx / len(core) * 65)
            progress_cb(f"본문 수집 중... ({idx + 1}/{len(core)})", pct)
        try:
            r  = sess.get(vu, params={"id": gid, "no": m["post_no"]},
                          headers=WEB_HEADERS, verify=False, timeout=REQUEST_TIMEOUT)
            sp = BeautifulSoup(r.text, "html.parser")
            bd = sp.select_one(".write_div")
            body = re.sub(r"\s+", " ", bd.get_text(separator=" ").strip())[:BODY_MAX_CHARS] if bd else "본문 누락"
        except Exception:
            body = "본문 수집 오류"
        results.append({**{k: v for k, v in m.items() if k != "_dt"}, "body": body})
        time.sleep(random.uniform(DETAIL_DELAY_MIN, DETAIL_DELAY_MAX))

    dc_ana = Counter(m["date"] for m in analysis_metas)
    dc_14  = Counter(m["date"] for m in fourteen_metas)
    dates  = sorted(m["date"] for m in analysis_metas)
    return {
        "gallery_id":      gid,
        "gallery_name":    gname,
        "gal_type":        gtype,
        "all_metas":       [{k: v for k, v in m.items() if k != "_dt"} for m in analysis_metas],
        "analysis_data":   results,
        "date_counts":     dict(dc_ana),
        "date_counts_14":  dict(dc_14),
        "total_posts":     len(analysis_metas),
        "concept_posts":   concept_count,
        "core_posts":      len(core),
        "analysis_count":  len(results),
        "analysis_method": "concept" if concept_count >= 5 else "high_engagement",
        "date_range_str":  f"{dates[0]} ~ {dates[-1]}" if dates else "기간 알 수 없음",
    }