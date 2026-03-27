"""
dc_scraper.py v5

[개념글 문제 근본 해결]
디씨 앱 API (recommend=1) 는 해외 IP / 특정 환경에서 빈 배열 반환.
웹 HTML에서도 개념글 클래스(.icon_recom 등)가 환경에 따라 감지 안 됨.

→ 새로운 전략: "고관여 게시글" 선정
  - 전체 게시글 수집 후 댓글 수 상위 20% 를 핵심 분석 대상으로 선정
  - 개념글 여부 대신 "참여도(댓글 수)" 기준
  - 이는 실제로도 더 합리적: 반응 많은 글 = 민심 집약점
  - 웹 목록에서 개념글 아이콘 감지 시도는 유지 (되면 보너스)

[수집 전략]
  diagnose_gallery: 웹 목록 빠른 진단
  run_dc_scraper:
    1) 전체 목록 수집 (날짜 분포 + 댓글 수)
    2) 댓글 수 상위 20% → "핵심 게시글" (ANALYSIS_MIN_POSTS개 이상)
    3) 핵심 게시글 본문 수집
    4) 14일 차트 별도 집계 (분석 기간과 무관하게 항상)
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
    ANALYSIS_MIN_CONCEPT_POSTS,
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

# 핵심 게시글 선정 기준
CORE_POST_TOP_PERCENT = 0.20   # 댓글 수 상위 20%
CORE_POST_MIN_COUNT   = 50     # 최소 50개 보장


def parse_dc_url(url: str):
    url = url.strip()
    m = re.search(
        r'gall\.dcinside\.com/(?:(mgallery|mini)/)?board/(?:lists|view).*?[\?&]id=([a-zA-Z0-9_]+)',
        url
    )
    if not m: return None, None
    s = m.group(1)
    if s == "mgallery": gal_type = "minor"
    elif s == "mini":   gal_type = "mini"
    else:               gal_type = "regular"
    return gal_type, m.group(2)


def _web_urls(t):
    if t == "minor":
        return "https://gall.dcinside.com/mgallery/board/lists/", "https://gall.dcinside.com/mgallery/board/view/"
    if t == "mini":
        return "https://gall.dcinside.com/mini/board/lists/", "https://gall.dcinside.com/mini/board/view/"
    return "https://gall.dcinside.com/board/lists/", "https://gall.dcinside.com/board/view/"


def _post_url(t, gid, no):
    if t == "minor": return f"https://gall.dcinside.com/mgallery/board/view/?id={gid}&no={no}"
    if t == "mini":  return f"https://gall.dcinside.com/mini/board/view/?id={gid}&no={no}"
    return f"https://gall.dcinside.com/board/view/?id={gid}&no={no}"


def _parse_date(s):
    s = (s or "").strip()
    try:
        if not s: return datetime.now()
        if re.match(r'^\d{2}:\d{2}$', s): return datetime.now()
        if re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', s):
            return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        if re.match(r'^\d{2}\.\d{2}$', s):
            return datetime.strptime(s, "%m.%d").replace(year=datetime.now().year)
        if re.match(r'^\d{2}\.\d{2}\.\d{2}$', s): return datetime.strptime(s, "%y.%m.%d")
        if re.match(r'^\d{4}\.\d{2}\.\d{2}$', s): return datetime.strptime(s, "%Y.%m.%d")
    except Exception:
        pass
    return datetime.now()


def _date_str(row):
    e = row.select_one(".gall_date")
    if not e: return ""
    if e.has_attr("title") and e["title"].strip(): return e["title"].strip()
    return e.text.strip()


def _skip(row):
    if "notice" in row.get("class", []): return True
    sub = row.select_one(".gall_subject")
    if sub and sub.text.strip() in {"공지","설문","AD","이슈"}: return True
    num = row.select_one(".gall_num")
    return not num or not num.text.strip().isdigit()


def _gname(soup):
    try:
        raw = soup.select_one(".title_main").text.strip()
        return re.sub(r"\s*(갤러리|마이너 갤러리|미니 갤러리)$", "", raw)
    except Exception:
        return ""


def _soup(session, url, params):
    try:
        r = session.get(url, params=params, headers=WEB_HEADERS, verify=False, timeout=REQUEST_TIMEOUT)
        return BeautifulSoup(r.text, "html.parser")
    except Exception:
        return None


def _is_concept_html(row) -> bool:
    """웹 HTML에서 개념글 여부 감지 (되면 좋고 안 돼도 괜찮음)"""
    classes = " ".join(row.get("class", []))
    if "recommend" in classes or "bg_recommend" in classes: return True
    if row.select_one(".icon_recom, .icon_recomsmall, .bg_recomsmall"): return True
    return False


def _parse_row(row, gtype, gid):
    ne = row.select_one(".gall_num")
    if not ne: return None
    dt   = _parse_date(_date_str(row))
    te   = row.select_one(".gall_tit a")
    re_e = row.select_one(".reply_num")
    cc   = int(re.sub(r"[^0-9]","",re_e.text)) if re_e and re.sub(r"[^0-9]","",re_e.text) else 0
    ae   = row.select_one(".gall_writer")
    ip_e = ae.select_one(".ip") if ae else None
    nk_e = ae.select_one(".nickname") if ae else None
    nm   = nk_e.text.strip() if nk_e else "알 수 없음"
    return {
        "post_no":       ne.text.strip(),
        "title":         te.text.strip() if te else "",
        "date":          dt.strftime("%Y-%m-%d"),
        "_dt":           dt,
        "is_concept":    _is_concept_html(row),  # HTML 감지 시도
        "comment_count": cc,
        "author":        f"{nm} ({ip_e.text.strip()})" if ip_e and nk_e else nm,
        "user_type":     "유동" if ip_e else "고닉",
        "post_url":      _post_url(gtype, gid, ne.text.strip()),
    }


def _try_app_api_concepts(gid, gtype, cutoff):
    """앱 API 개념글 수집 시도. 실패하면 빈 리스트 반환."""
    results = []; seen = set(); sess = requests.Session()
    for page in range(1, 100):
        try:
            r = sess.get(APP_LIST,
                         params={"id": gid, "page": str(page), "app_id": APP_ID, "recommend": "1"},
                         headers=APP_HEADERS, verify=False, timeout=REQUEST_TIMEOUT)
            raw = r.json()
        except Exception:
            break

        if isinstance(raw, list):              posts = raw
        elif isinstance(raw, dict):
            candidate = None
            for k in ("gall_list","data","list","posts","result"):
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
            try:
                cc = int(re.sub(r"[^0-9]","", str(p.get("reply_num") or p.get("comment_cnt") or "0")) or "0")
            except Exception:
                cc = 0
            results.append({
                "post_no":       no,
                "title":         title,
                "date":          dt.strftime("%Y-%m-%d"),
                "_dt":           dt,
                "is_concept":    True,
                "comment_count": cc,
                "author":        p.get("name") or p.get("gall_writer") or "알 수 없음",
                "user_type":     "고닉" if (p.get("member_id") or p.get("user_id")) else "유동",
                "post_url":      _post_url(gtype, gid, no),
            })
            added += 1

        if added <= 0: break
        time.sleep(random.uniform(SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX))

    return results


def _select_core_posts(all_metas: list, min_count: int) -> list:
    """
    댓글 수 기준 핵심 게시글 선정.
    개념글(is_concept=True)이 충분하면 우선 사용,
    없으면 댓글 수 상위 20%를 핵심 게시글로 선정.
    """
    concept_posts = [m for m in all_metas if m.get("is_concept")]

    if len(concept_posts) >= min_count:
        return concept_posts

    # 개념글 부족 → 댓글 수 상위 20% 선정
    sorted_by_comments = sorted(all_metas, key=lambda x: -x["comment_count"])
    top_n = max(min_count, int(len(all_metas) * CORE_POST_TOP_PERCENT))
    core  = sorted_by_comments[:top_n]

    # 개념글도 포함 (중복 제거)
    seen_nos = {p["post_no"] for p in core}
    for cp in concept_posts:
        if cp["post_no"] not in seen_nos:
            core.append(cp)

    return sorted(core, key=lambda x: x["_dt"])


# ── 진단 ────────────────────────────────────────────────────────────
def diagnose_gallery(url, progress_cb=None):
    gtype, gid = parse_dc_url(url)
    if not gid: return {"error": "유효하지 않은 URL 형식입니다.", "gallery_id": None}

    sess = requests.Session()
    lu, _ = _web_urls(gtype)
    s0 = _soup(sess, lu, {"id": gid})
    gname = (_gname(s0) if s0 else "") or gid
    if progress_cb: progress_cb(f"[{gname}] 진단 중...", 5)

    hard_co = datetime.now() - timedelta(days=DIAG_MAX_DAYS)
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
            if m["_dt"] < hard_co:
                old_s += 1
                if old_s >= 5: old_s = 9999; break
                continue
            old_s = 0
            seen.add(m["post_no"]); rows.append(m); padded += 1
            if len(rows) >= 2:
                span = (rows[0]["_dt"] - m["_dt"]).days
                if len(rows) >= DIAG_MIN_POSTS or (span >= DIAG_MIN_DAYS and len(rows) >= 50):
                    done = True; break

        if progress_cb: progress_cb(f"진단 중... ({len(rows)}개)", min(85, 5 + len(rows)//5))
        if old_s >= 9999 or padded == 0: break
        time.sleep(random.uniform(SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX))

    if not rows: return {"error": "게시글을 찾을 수 없습니다.", "gallery_id": gid}
    rows.sort(key=lambda x: x["_dt"], reverse=True)

    dc    = Counter(r["date"] for r in rows)
    total = len(rows)
    daily = total / max(len(dc), 1)
    concept_count = sum(1 for r in rows if r["is_concept"])

    words = []
    for r in rows:
        if r["title"]:
            words.extend(w.lower() for w in re.findall(r"[가-힣a-zA-Z]{2,}", r["title"]))
    SW = {"이","그","저","이거","ㅋㅋ","ㅠㅠ","진짜","뭔","왜","좀","다","하는","합니다"}
    wf = Counter(w for w in words if w not in SW)
    top_words = [w for w, _ in wf.most_common(15)]

    all_t  = " ".join(words)
    scores = {s: sum(all_t.count(k.lower()) for k in ks) for s, ks in SUBTYPE_KEYWORDS.items()}
    dates  = sorted(dc.keys())
    if progress_cb: progress_cb("진단 완료!", 100)

    return {
        "gallery_id": gid, "gallery_name": gname, "gal_type": gtype,
        "total_rows": total, "daily_avg": round(daily, 1),
        "date_counts": dict(dc), "concept_count": concept_count,
        "diag_start": dates[0] if dates else "",
        "diag_end":   dates[-1] if dates else "",
        "top_title_words": top_words, "subtype_scores": scores,
        "error": None,
    }


# ── 수집 + 본문 ──────────────────────────────────────────────────────
def run_dc_scraper(url, days_limit, progress_cb=None):
    gtype, gid = parse_dc_url(url)
    if not gid: raise ValueError("유효하지 않은 URL 형식입니다.")

    sess = requests.Session()
    lu, vu = _web_urls(gtype)
    s0 = _soup(sess, lu, {"id": gid})
    gname = (_gname(s0) if s0 else "") or gid
    if progress_cb: progress_cb("개념글 수집 시도 중...", 3)

    cutoff    = datetime.now() - timedelta(days=days_limit)
    cutoff_14 = datetime.now() - timedelta(days=14)
    collect_cutoff = min(cutoff, cutoff_14)

    # Phase 1: 앱 API 개념글 시도 (실패해도 계속)
    app_concepts = _try_app_api_concepts(gid, gtype, cutoff)
    if progress_cb:
        if app_concepts:
            progress_cb(f"개념글 {len(app_concepts)}개 수집. 전체 목록 집계 중...", 15)
        else:
            progress_cb("고관여 게시글 선정 방식으로 전환. 전체 목록 집계 중...", 15)

    # Phase 2: 웹 전체 목록 수집 (14일 보장)
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
            if m["_dt"] < collect_cutoff:
                old_s += 1
                if old_s >= 5: done = True; break
                continue
            old_s = 0
            seen.add(m["post_no"]); all_metas.append(m); padded += 1

        if progress_cb and len(all_metas) % 200 == 0 and len(all_metas) > 0:
            progress_cb(f"목록 집계 중... ({len(all_metas)}개)", min(28, 15 + len(all_metas)//100))
        if padded == 0: break
        time.sleep(random.uniform(SCRAPE_DELAY_MIN*0.5, SCRAPE_DELAY_MAX*0.5))

    # Phase 3: 앱 API 개념글을 all_metas에 병합 (중복 제거)
    web_nos = {m["post_no"] for m in all_metas}
    for cp in app_concepts:
        if cp["post_no"] not in web_nos:
            # cutoff 범위 내인 것만
            if cp["_dt"] >= collect_cutoff:
                all_metas.append(cp)
                web_nos.add(cp["post_no"])
        else:
            # 웹에서 가져온 것을 is_concept=True로 업데이트
            for m in all_metas:
                if m["post_no"] == cp["post_no"]:
                    m["is_concept"] = True
                    break

    # Phase 4: 핵심 게시글 선정 (분석 기간 기준)
    analysis_metas = [m for m in all_metas if m["_dt"] >= cutoff]
    core_posts = _select_core_posts(analysis_metas, CORE_POST_MIN_COUNT)
    core_posts.sort(key=lambda x: x["_dt"])

    if not core_posts:
        raise Exception(f"최근 {days_limit}일 이내 분석 가능한 게시글이 없습니다.")

    concept_count = sum(1 for m in analysis_metas if m.get("is_concept"))
    core_is_concept = sum(1 for m in core_posts if m.get("is_concept"))

    if progress_cb: progress_cb(f"본문 수집 시작... ({len(core_posts)}개)", 30)

    # Phase 5: 본문 수집
    results = []
    for idx, m in enumerate(core_posts):
        if progress_cb and idx % 5 == 0:
            progress_cb(f"본문 추출 중... ({idx+1}/{len(core_posts)})", 30 + int(idx/len(core_posts)*65))
        try:
            r = sess.get(vu, params={"id": gid, "no": m["post_no"]},
                         headers=WEB_HEADERS, verify=False, timeout=REQUEST_TIMEOUT)
            sp = BeautifulSoup(r.text, "html.parser")
            bd = sp.select_one(".write_div")
            body = re.sub(r"\s+", " ", bd.get_text(separator=" ").strip())[:BODY_MAX_CHARS] if bd else "본문 누락"
        except Exception:
            body = "본문 수집 오류"
        clean = {k: v for k, v in m.items() if k != "_dt"}
        results.append({**clean, "body": body})
        time.sleep(random.uniform(DETAIL_DELAY_MIN, DETAIL_DELAY_MAX))

    # 날짜별 집계
    dc_analysis = Counter(m["date"] for m in analysis_metas)
    dc_14       = Counter(m["date"] for m in all_metas if m["_dt"] >= cutoff_14)
    dates       = sorted(m["date"] for m in analysis_metas)

    return {
        "gallery_id":      gid,
        "gallery_name":    gname,
        "gal_type":        gtype,
        "all_metas":       [{k:v for k,v in m.items() if k!="_dt"} for m in analysis_metas],
        "analysis_data":   results,
        "date_counts":     dict(dc_analysis),
        "date_counts_14":  dict(dc_14),
        "total_posts":     len(analysis_metas),
        "concept_posts":   concept_count,
        "core_posts":      len(core_posts),
        "core_is_concept": core_is_concept,
        "normal_posts":    len(analysis_metas) - concept_count,
        "analysis_count":  len(results),
        "analysis_method": "concept" if concept_count >= CORE_POST_MIN_COUNT else "high_engagement",
        "date_range_str":  f"{dates[0]} ~ {dates[-1]}" if dates else "기간 알 수 없음",
    }