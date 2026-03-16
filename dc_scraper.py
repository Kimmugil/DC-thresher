import requests
from bs4 import BeautifulSoup
import re
import time
import random
import urllib3

# SSL 인증서 경고 무시 (로컬 테스트 환경용)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# HTTP 헤더 설정
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def parse_dc_url(url):
    """URL 분석 및 갤러리 속성(타입, ID) 추출"""
    url = url.strip()
    match = re.search(r'gall\.dcinside\.com/(?:(mgallery|mini)/)?board/lists/\??(?:.*&)?id=([a-zA-Z0-9_]+)', url)
    
    if match:
        gal_type_str = match.group(1)
        gal_id = match.group(2)
        if gal_type_str == 'mgallery': gal_type = 'minor'
        elif gal_type_str == 'mini': gal_type = 'mini'
        else: gal_type = 'regular'
        return gal_type, gal_id
    return None, None

def get_api_urls(gal_type):
    """갤러리 타입에 따른 엔드포인트 URL 반환 (댓글 API는 공통 URL)"""
    comment_url = "https://gall.dcinside.com/board/comment/"
    
    if gal_type == 'minor':
        return "https://gall.dcinside.com/mgallery/board/lists/", "https://gall.dcinside.com/mgallery/board/view/", comment_url
    elif gal_type == 'mini':
        return "https://gall.dcinside.com/mini/board/lists/", "https://gall.dcinside.com/mini/board/view/", comment_url
    else:
        return "https://gall.dcinside.com/board/lists/", "https://gall.dcinside.com/board/view/", comment_url

def fetch_post_list(session, gal_type, gal_id, page=1):
    """특정 갤러리의 게시글 목록 수집 (댓글 수 포함)"""
    list_url, _, _ = get_api_urls(gal_type)
    params = {'id': gal_id, 'page': page}
    
    try:
        res = session.get(list_url, params=params, headers=HEADERS, verify=False, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        posts = []
        
        for row in soup.select('tr.ub-content.us-post'):
            post_no_elem = row.select_one('.gall_num')
            if not post_no_elem: continue
            
            post_no = post_no_elem.text.strip()
            if not post_no.isdigit(): continue # 공지사항 및 설문 제외
            
            title_elem = row.select_one('.gall_tit a')
            title = title_elem.text.strip() if title_elem else "제목 누락"
            
            # 💡 [핵심 추가] 댓글 수 추출
            reply_elem = row.select_one('.reply_num')
            comment_count = 0
            if reply_elem:
                num_str = re.sub(r'[^0-9]', '', reply_elem.text)
                if num_str:
                    comment_count = int(num_str)
            
            author_elem = row.select_one('.gall_writer')
            ip_elem = author_elem.select_one('.ip') if author_elem else None
            author_name_elem = author_elem.select_one('.nickname') if author_elem else None
            author_name = author_name_elem.text.strip() if author_name_elem else "알 수 없음"
            
            posts.append({
                "post_no": post_no,
                "title": title,
                "comment_count": comment_count, # 👈 추출한 댓글 수 저장
                "author": f"{author_name} ({ip_elem.text.strip()})" if ip_elem else author_name,
                "user_type": "유동" if ip_elem else "고닉/반고닉"
            })
        return posts
    except Exception as e:
        print(f"[Error] 목록 수집 중 예외 발생: {e}")
        return []

def fetch_post_detail(session, gal_type, gal_id, post_no):
    """게시글 본문 및 비동기 댓글 수집 (보안 토큰 우회 적용)"""
    _, view_url, comment_url = get_api_urls(gal_type)
    params = {'id': gal_id, 'no': post_no}
    
    try:
        # 1. 본문 페이지 접속 및 세션 유지
        res = session.get(view_url, params=params, headers=HEADERS, verify=False, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        body_div = soup.select_one('.write_div')
        body_text = body_div.text.strip() if body_div else "본문 누락"
        
        # 2. 댓글 수집을 위한 보안 토큰(e_spt) 추출
        e_spt_elem = soup.select_one('#e_spt')
        e_spt = e_spt_elem['value'] if e_spt_elem else ""
        
        comments = []
        if e_spt:
            comment_headers = HEADERS.copy()
            comment_headers.update({
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Referer": res.url
            })
            
            payload = {
                "id": gal_id,
                "no": post_no,
                "cmt_id": gal_id,
                "cmt_no": post_no,
                "e_spt": e_spt,
                "comment_page": 1,
                "sort": "D",
                "_v": "2b3133"
            }
            
            # 3. 추출한 토큰을 포함하여 비동기 댓글 API 호출
            c_res = session.post(comment_url, data=payload, headers=comment_headers, verify=False, timeout=5)
            
            if c_res.status_code == 200:
                # JSON/HTML 다중 파싱 로직
                try:
                    c_data = c_res.json()
                    if c_data and isinstance(c_data, dict) and c_data.get('comments'):
                        for cmt in c_data['comments']:
                            if isinstance(cmt, dict) and cmt.get('memo'):
                                clean_memo = BeautifulSoup(cmt['memo'], 'html.parser').text.strip()
                                if clean_memo:
                                    comments.append(clean_memo)
                except:
                    c_soup = BeautifulSoup(c_res.text, 'html.parser')
                    comments = [cmt.text.strip() for cmt in c_soup.select('.us-txt') if cmt.text.strip()]
                
        return {"body": body_text, "comments": comments}
    except Exception as e:
        return {"body": f"수집 에러: {e}", "comments": []}

def run_dc_scraper(url, max_posts=5):
    """스크래퍼 메인 파이프라인 (app.py에서 호출하는 메인 함수)"""
    gal_type, gal_id = parse_dc_url(url)
    if not gal_type: 
        raise ValueError("유효하지 않은 URL 형식입니다.")
    
    print(f"[{gal_id}] 대상 데이터 수집 프로세스 시작...")
    
    # 세션 객체를 생성하여 쿠키(Cookie) 상태 유지
    session = requests.Session()
    post_list = fetch_post_list(session, gal_type, gal_id)
    
    results = []
    target_posts = post_list[:max_posts]
    
    for idx, post in enumerate(target_posts):
        print(f"진행 상황 ({idx+1}/{len(target_posts)}) - 문서 번호: {post['post_no']} 수집 중...")
        detail = fetch_post_detail(session, gal_type, gal_id, post['post_no'])
        results.append({**post, **detail})
        
        # 서버 부하 방지를 위한 임의 지연
        time.sleep(random.uniform(1.0, 2.5))
        
    return {"gallery_id": gal_id, "data": results}
