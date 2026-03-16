import requests
from bs4 import BeautifulSoup
import re
import time
import random
import urllib3
from datetime import datetime, timedelta

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def parse_dc_url(url):
    url = url.strip()
    match = re.search(r'gall\.dcinside\.com/(?:(mgallery|mini)/)?board/(?:lists|view).*?[\?&]id=([a-zA-Z0-9_]+)', url)
    if match:
        gal_type_str = match.group(1)
        gal_id = match.group(2)
        if gal_type_str == 'mgallery': gal_type = 'minor'
        elif gal_type_str == 'mini': gal_type = 'mini'
        else: gal_type = 'regular'
        return gal_type, gal_id
    return None, None

def get_api_urls(gal_type):
    comment_url = "https://gall.dcinside.com/board/comment/"
    if gal_type == 'minor': return "https://gall.dcinside.com/mgallery/board/lists/", "https://gall.dcinside.com/mgallery/board/view/", comment_url
    elif gal_type == 'mini': return "https://gall.dcinside.com/mini/board/lists/", "https://gall.dcinside.com/mini/board/view/", comment_url
    else: return "https://gall.dcinside.com/board/lists/", "https://gall.dcinside.com/board/view/", comment_url

def get_post_url(gal_type, gal_id, post_no):
    if gal_type == 'minor': return f"https://gall.dcinside.com/mgallery/board/view/?id={gal_id}&no={post_no}"
    elif gal_type == 'mini': return f"https://gall.dcinside.com/mini/board/view/?id={gal_id}&no={post_no}"
    else: return f"https://gall.dcinside.com/board/view/?id={gal_id}&no={post_no}"

def fetch_post_detail(session, gal_type, gal_id, post_no):
    _, view_url, comment_url = get_api_urls(gal_type)
    params = {'id': gal_id, 'no': post_no}
    try:
        res = session.get(view_url, params=params, headers=HEADERS, verify=False, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        body_div = soup.select_one('.write_div')
        body_text = body_div.text.strip() if body_div else "본문 누락"
        
        e_spt_elem = soup.select_one('#e_spt')
        e_spt = e_spt_elem['value'] if e_spt_elem else ""
        comments = []
        if e_spt:
            comment_headers = HEADERS.copy()
            comment_headers.update({"X-Requested-With": "XMLHttpRequest", "Accept": "application/json", "Referer": res.url})
            payload = {"id": gal_id, "no": post_no, "cmt_id": gal_id, "cmt_no": post_no, "e_spt": e_spt, "comment_page": 1, "sort": "D", "_v": "2b3133"}
            c_res = session.post(comment_url, data=payload, headers=comment_headers, verify=False, timeout=5)
            if c_res.status_code == 200:
                try:
                    c_data = c_res.json()
                    if c_data and isinstance(c_data, dict) and c_data.get('comments'):
                        for cmt in c_data['comments']:
                            if isinstance(cmt, dict) and cmt.get('memo'):
                                clean_memo = BeautifulSoup(cmt['memo'], 'html.parser').text.strip()
                                if clean_memo: comments.append(clean_memo)
                except:
                    c_soup = BeautifulSoup(c_res.text, 'html.parser')
                    comments = [cmt.text.strip() for cmt in c_soup.select('.us-txt') if cmt.text.strip()]
        return {"body": body_text, "comments": comments}
    except Exception as e:
        return {"body": f"에러: {e}", "comments": []}

def run_dc_scraper(url, max_posts=500, days_limit=30, progress_cb=None):
    gal_type, gal_id = parse_dc_url(url)
    if not gal_type: raise ValueError("유효하지 않은 URL 형식입니다.")
    
    session = requests.Session()
    list_url, _, _ = get_api_urls(gal_type)

    try:
        res_init = session.get(list_url, params={'id': gal_id}, headers=HEADERS, verify=False, timeout=5)
        soup_init = BeautifulSoup(res_init.text, 'html.parser')
        raw_name = soup_init.select_one('.title_main').text.strip()
        gallery_name = re.sub(r'\s*(갤러리|마이너 갤러리|미니 갤러리)$', '', raw_name)
    except:
        gallery_name = gal_id

    if progress_cb: progress_cb(f"[{gallery_name}] 데이터 분석 시작...", 5)
    
    cutoff_date = datetime.now() - timedelta(days=days_limit)
    collected_posts = []
    
    for is_concept in [True, False]:
        page = 1
        stop_scraping = False
        target_limit = max_posts // 2
        mode_count = 0
        old_post_streak = 0
        
        while not stop_scraping and mode_count < target_limit:
            params = {'id': gal_id, 'page': page}
            if is_concept: params['exception_mode'] = 'recommend'
            
            res = session.get(list_url, params=params, headers=HEADERS, verify=False, timeout=5)
            if res.status_code != 200: raise Exception(f"접근 차단됨 (상태 코드: {res.status_code})")
                
            soup = BeautifulSoup(res.text, 'html.parser')
            rows = soup.select('tr.ub-content.us-post')
            if not rows: break 
            
            added_on_page = 0
            
            for row in rows:
                subject_elem = row.select_one('.gall_subject')
                if subject_elem:
                    subject_text = subject_elem.text.strip()
                    if subject_text in ['공지', '설문', 'AD', '이슈']:
                        continue
                
                if 'notice' in row.get('class', []): continue
                if mode_count >= target_limit or len(collected_posts) >= max_posts:
                    stop_scraping = True; break
                    
                post_no_elem = row.select_one('.gall_num')
                if not post_no_elem or not post_no_elem.text.strip().isdigit(): continue
                post_no = post_no_elem.text.strip()
                
                if any(p['post_no'] == post_no for p in collected_posts): continue
                
                date_elem = row.select_one('.gall_date')
                date_str = date_elem.get('title') if date_elem and date_elem.has_attr('title') else date_elem.text.strip()
                try:
                    if len(date_str) > 10: post_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    elif ':' in date_str: post_date = datetime.now()
                    elif len(date_str) == 5: 
                        parsed = datetime.strptime(date_str, '%m.%d')
                        post_date = parsed.replace(year=datetime.now().year)
                    else: post_date = datetime.strptime(date_str, '%y.%m.%d')
                except: post_date = datetime.now()
                
                if post_date < cutoff_date:
                    old_post_streak += 1
                    if old_post_streak >= 5:
                        stop_scraping = True; break 
                    continue
                else:
                    old_post_streak = 0
                    
                title_elem = row.select_one('.gall_tit a')
                title = title_elem.text.strip() if title_elem else "제목 누락"
                reply_elem = row.select_one('.reply_num')
                comment_count = int(re.sub(r'[^0-9]', '', reply_elem.text)) if reply_elem and re.sub(r'[^0-9]', '', reply_elem.text) else 0
                
                author_elem = row.select_one('.gall_writer')
                ip_elem = author_elem.select_one('.ip') if author_elem else None
                author_name = author_elem.select_one('.nickname').text.strip() if author_elem and author_elem.select_one('.nickname') else "알 수 없음"
                
                collected_posts.append({
                    "post_no": post_no, "title": title, "date": post_date.strftime('%Y-%m-%d'),
                    "post_url": get_post_url(gal_type, gal_id, post_no), "is_concept": is_concept,
                    "comment_count": comment_count, "author": f"{author_name} ({ip_elem.text.strip()})" if ip_elem else author_name,
                    "user_type": "유동" if ip_elem else "고닉"
                })
                mode_count += 1
                added_on_page += 1
                
                if len(collected_posts) % 10 == 0 and progress_cb:
                    p_ratio = min(30, 5 + int((len(collected_posts)/max_posts) * 25))
                    mode_str = "개념글" if is_concept else "일반글"
                    progress_cb(f"[{mode_str}] 목록 탐색 중... (현재 {len(collected_posts)}개 완료 ⏳)", p_ratio)

            if added_on_page == 0 and old_post_streak >= 5:
                break

            page += 1
            time.sleep(random.uniform(0.3, 0.7))
            
    if not collected_posts:
        raise Exception("최근 30일 이내에 작성된 유효한 게시글이 전혀 없습니다.")

    if progress_cb: progress_cb(f"목록 수집 완료: 총 {len(collected_posts)}개. 본문 병합 시작...", 35)
    
    results = []
    total = len(collected_posts)
    for idx, post in enumerate(collected_posts):
        if progress_cb and idx % 5 == 0: 
            progress_ratio = 35 + int((idx / total) * 60)
            progress_cb(f"게시물 내용 추출 및 병합 중... ({idx+1}/{total}) ⚙️", progress_ratio)
            
        detail = fetch_post_detail(session, gal_type, gal_id, post['post_no'])
        results.append({**post, **detail})
        time.sleep(random.uniform(0.5, 1.0))
        
    return {"gallery_id": gal_id, "gallery_name": gallery_name, "data": results}