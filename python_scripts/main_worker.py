"""
main_worker.py
- Coordinates dc_scraper and ai_analyzer
"""
import os
import sys
import json
from dc_scraper import parse_dc_url, diagnose_gallery, run_dc_scraper
from gallery_analyzer import guess_game_name, detect_subtype
from ai_analyzer import diagnose_gallery_ai, analyze_gallery

def main():
    if len(sys.argv) < 3:
        print("Usage: python main_worker.py <gallery_url> <uuid>")
        sys.exit(1)

    url = sys.argv[1]
    uuid = sys.argv[2]
    
    print(f"Starting analysis for URL: {url} (UUID: {uuid})")

    # Step 1: Diagnose
    _, gal_id = parse_dc_url(url)
    if not gal_id:
        print("Invalid URL")
        sys.exit(1)

    diag = diagnose_gallery(url)
    if diag.get("error"):
        print(f"Diagnosis Error: {diag['error']}")
        sys.exit(1)

    gallery_name = diag["gallery_name"]
    gallery_id = diag["gallery_id"]
    top_words = diag["top_title_words"]
    daily_avg = diag["daily_avg"]
    
    base_game_name = guess_game_name(gallery_name, top_words)
    subtype_id = detect_subtype(diag)

    # Calculate auto_days based on activity
    auto_days = 7 if daily_avg >= 200 else (14 if daily_avg >= 50 else 30)
    
    print(f"Gallery Name: {gallery_name}")
    print(f"Base Game Name: {base_game_name}")
    print(f"Auto Days: {auto_days}")

    # AI Diagnosis
    ai_result, ai_err = diagnose_gallery_ai(gallery_name, top_words, subtype_id, daily_avg)
    
    game_name = base_game_name
    if not ai_err and ai_result:
        ai_guess = ai_result.get("topic_guess", "").strip()
        if ai_guess and len(ai_guess) >= len(base_game_name) * 0.5:
            game_name = ai_guess

    print(f"Final Game Name: {game_name}")

    # Step 2: Scrape
    try:
        scrape_result = run_dc_scraper(url, days_limit=auto_days)
    except Exception as e:
        print(f"Scraping Error: {e}")
        sys.exit(1)

    # Save scrape result
    with open("scrape_result.json", "w", encoding="utf-8") as f:
        json.dump(scrape_result, f, ensure_ascii=False)
        
    print(f"Scraping complete. Analysis count: {scrape_result['analysis_count']}")

    # Step 3: AI Analysis
    insights, error = analyze_gallery(
        gallery_id=gallery_id,
        game_name=game_name,
        subtype_id=subtype_id,
        analysis_data=scrape_result["analysis_data"],
        all_metas=scrape_result["all_metas"],
        analysis_days=auto_days,
    )

    if error:
        print(f"AI Analysis Error: {error}")
        sys.exit(1)

    # Attach names for save_to_sheets.py
    insights["game_name"] = game_name
    insights["gallery_name"] = gallery_name
    
    # Attach scrape metadata for frontend display
    ana_data = scrape_result.get("analysis_data", [])
    if ana_data:
        s_data = sorted(ana_data, key=lambda x: x.get("comment_count", 0), reverse=True)
        insights["scrape_meta"] = {
            "total_posts":  scrape_result.get("total_posts", 0),
            "core_posts":   len(ana_data),
            "date_range":   scrape_result.get("date_range_str", ""),
            # 일별 게시글 추이 차트용 (전체 수집 범위)
            "date_counts":  scrape_result.get("date_counts", {}),
            # 표본 상·하단 게시글 (URL 포함)
            "max_comment_post": {
                "title":         s_data[0].get("title", ""),
                "comment_count": s_data[0].get("comment_count", 0),
                "url":           s_data[0].get("post_url", ""),
            },
            "min_comment_post": {
                "title":         s_data[-1].get("title", ""),
                "comment_count": s_data[-1].get("comment_count", 0),
                "url":           s_data[-1].get("post_url", ""),
            },
        }

    # Save insights
    with open("insights.json", "w", encoding="utf-8") as f:
        json.dump(insights, f, ensure_ascii=False)

    print("AI Analysis complete. Results saved.")

if __name__ == "__main__":
    main()
