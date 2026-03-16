# dc_scraper.py 내 fetch_post_list 함수 수정

def fetch_post_list(session, gal_type, gal_id, page=1):
    """
    특정 갤러리의 게시글 목록 수집 (댓글 수 포함)
    """
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
            if not post_no.isdigit(): continue
            
            title_elem = row.select_one('.gall_tit a')
            title = title_elem.text.strip() if title_elem else "제목 누락"
            
            # 💡 [핵심 추가] 댓글 수 추출 (reply_num 클래스)
            reply_elem = row.select_one('.reply_num')
            comment_count = 0
            if reply_elem:
                # '[15]' 같은 형태에서 숫자만 추출
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
                "comment_count": comment_count, # 👈 리스트에 댓글 수 추가
                "author": f"{author_name} ({ip_elem.text.strip()})" if ip_elem else author_name,
                "user_type": "유동" if ip_elem else "고닉/반고닉"
            })
        return posts
    except Exception as e:
        print(f"[Error] 목록 수집 중 예외 발생: {e}")
        return []