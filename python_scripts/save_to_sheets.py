import os
import sys
import json
import requests
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# config에서 가져오기
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GAS_WEBAPP_URL, GAS_FOLDER_ID, SERVICE_ACCOUNT_EMAIL

MAX_CELL = 49000

ANALYSIS_RESULTS_HEADERS = [
    "AnalyzedAt", "UUID", "GameName", "DateRange", "AnalysisCriteria",
    "CriticOneLiner", "Keywords", "PositiveSummary", "NegativeSummary",
    "MajorIssues", "TrendAnalysis"
]

RAW_POSTS_HEADERS = [
    "AnalyzedAt", "UUID", "PostNo", "Title", "Author", "UserType", 
    "Date", "CommentCount", "IsConcept", "URL", "Body"
]

def _get_or_create_tab(spreadsheet, tab_name, headers):
    try:
        return spreadsheet.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=tab_name, rows="1000", cols=str(len(headers)))
        ws.append_row(headers)
        return ws

def save_to_gallery_sheet(gc, raw_data, insights, uuid, analyzed_at):
    gallery_name = insights.get("gallery_name", raw_data.get("gallery_name", ""))
    if not gallery_name:
        print("[WARN] gallery_name을 찾을 수 없어 갤러리 전용 시트 저장을 건너뜁니다.")
        return

    # 1. GAS에 스프레드시트 생성/조회 요청
    file_name = f"DC_Thresher_{gallery_name}"
    payload = {
        "folderId": GAS_FOLDER_ID,
        "fileName": file_name,
        "serviceAccountEmail": SERVICE_ACCOUNT_EMAIL
    }
    
    print(f"[INFO] GAS 웹앱 호출 중... ({file_name})")
    try:
        res = requests.post(GAS_WEBAPP_URL, json=payload, timeout=30)
        res_data = res.json()
        if not res_data.get("ok"):
            print(f"[ERROR] GAS 요청 실패: {res_data.get('error')}")
            return
        spreadsheet_id = res_data.get("spreadsheetId")
        print(f"[INFO] 갤러리 스프레드시트 ID: {spreadsheet_id} (Reused: {res_data.get('reused')})")
    except Exception as e:
        print(f"[ERROR] GAS 웹앱 통신 오류: {e}")
        return

    # 2. 갤러리 시트 열기 및 데이터 기록
    try:
        gallery_sh = gc.open_by_key(spreadsheet_id)
        
        # --- Analysis_Results 기록 ---
        ws_results = _get_or_create_tab(gallery_sh, "Analysis_Results", ANALYSIS_RESULTS_HEADERS)
        
        game_name = insights.get("game_name", gallery_name)
        date_range = raw_data.get("date_range_str", "")
        criteria = insights.get("analysis_criteria", "")
        critic = insights.get("critic_one_liner", "")
        keywords_list = insights.get("top_keywords", [])
        keywords_str = ", ".join(keywords_list) if isinstance(keywords_list, list) else str(keywords_list)
        
        sentiment = insights.get("sentiment_summary") or {}
        pos_str = "\n".join([item.get("summary", "") for item in sentiment.get("positive", []) if isinstance(item, dict)])
        neg_str = "\n".join([item.get("summary", "") for item in sentiment.get("negative", []) if isinstance(item, dict)])
        
        issues = insights.get("major_issues") or []
        issues_str = "\n".join([f"[{i.get('issue_title','')}] {i.get('issue_detail','')}" for i in issues if isinstance(i, dict)])
        
        trends = insights.get("trend_analysis") or {}
        trends_str = "\n".join([f"[{k}] {v.get('summary','')} (Score: {v.get('score','')})" for k, v in trends.items() if isinstance(v, dict)])
        
        results_row = [
            analyzed_at, uuid, game_name, date_range, criteria,
            critic, keywords_str, pos_str, neg_str, issues_str, trends_str
        ]
        ws_results.append_row(results_row)
        
        # --- Raw_Posts 기록 ---
        ws_raw = _get_or_create_tab(gallery_sh, "Raw_Posts", RAW_POSTS_HEADERS)
        analysis_data = raw_data.get("analysis_data", [])
        raw_rows = []
        for p in analysis_data:
            if not isinstance(p, dict): continue
            body_text = p.get("body", "")
            if len(body_text) > 40000: body_text = body_text[:40000] + "..."
            
            raw_rows.append([
                analyzed_at, uuid, 
                p.get("post_no", ""), p.get("title", ""), p.get("author", ""), 
                p.get("user_type", ""), p.get("date", ""), p.get("comment_count", 0), 
                str(p.get("is_concept", False)), p.get("post_url", ""), body_text
            ])
            
        if raw_rows:
            # 여러 행을 한 번에 추가
            ws_raw.append_rows(raw_rows)
            print(f"[INFO] 갤러리 시트에 Raw Posts {len(raw_rows)}건 저장 완료.")
            
    except Exception as e:
        print(f"[ERROR] 갤러리 시트 데이터 기록 중 오류: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python save_to_sheets.py <uuid> [requested_at]")
        sys.exit(1)

    uuid         = sys.argv[1]
    requested_at = sys.argv[2] if len(sys.argv) > 2 else datetime.utcnow().isoformat() + "Z"

    creds_json_str = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    master_sheet_id = os.environ.get("GOOGLE_SPREADSHEET_ID")

    if not creds_json_str or not master_sheet_id:
        print("ERROR: GOOGLE_SHEETS_CREDENTIALS or GOOGLE_SPREADSHEET_ID not set.")
        sys.exit(1)

    try:
        creds_dict = json.loads(creds_json_str)
        scopes      = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc          = gspread.authorize(credentials)
    except Exception as e:
        print(f"ERROR: Failed to authenticate with Google Sheets: {e}")
        sys.exit(1)

    try:
        sh = gc.open_by_key(master_sheet_id)

        # ── Reports 탭 (메인 기록 - UI 히스토리용) ─────────────────
        try:
            worksheet = sh.worksheet("Reports")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title="Reports", rows="100", cols="20")
            worksheet.append_row(["UUID", "Status", "GameName", "GalleryName",
                                   "RequestedAt", "CompletedAt", "AI_Insights", "Raw_Data"])

        insights = {}
        if os.path.exists("insights.json"):
            with open("insights.json", "r", encoding="utf-8") as f:
                insights = json.load(f)

        raw_data = {}
        if os.path.exists("scrape_result.json"):
            with open("scrape_result.json", "r", encoding="utf-8") as f:
                raw_data = json.load(f)

        status       = "COMPLETED" if insights else "FAILED"
        game_name    = insights.get("game_name", "Unknown")
        gallery_name = insights.get("gallery_name", "Unknown")
        completed_at = datetime.utcnow().isoformat() + "Z"

        # ── AI_Insights ─────────────────────────────────────────
        insights_str = json.dumps(insights, ensure_ascii=False) if insights else ""
        if len(insights_str) > MAX_CELL:
            print(f"[WARN] insights_str too large ({len(insights_str)} chars). Saving minimal version.")
            minimal = {
                "critic_one_liner": insights.get("critic_one_liner", ""),
                "top_keywords":     insights.get("top_keywords", []),
                "game_name":        game_name,
                "gallery_name":     gallery_name,
            }
            insights_str = json.dumps(minimal, ensure_ascii=False)

        # ── Raw_Data (UI 로딩 최적화를 위해 메인시트에는 거의 저장안함) ─
        slim_raw = {"analysis_count": raw_data.get("analysis_count", 0)} if raw_data else {}
        raw_data_str = json.dumps(slim_raw, ensure_ascii=False) if slim_raw else ""

        worksheet.append_row([
            uuid, status, game_name, gallery_name,
            requested_at, completed_at,
            insights_str, raw_data_str,
        ])
        print(f"Successfully saved to Google Sheets (Reports). UUID: {uuid}, Status: {status}")

        # ── 갤러리 전용 파일 저장 (분석 성공 시에만) ───────────────
        if status == "COMPLETED" and raw_data:
            save_to_gallery_sheet(gc, raw_data, insights, uuid, completed_at)

    except Exception as e:
        print(f"ERROR: Failed to save to Google Sheets: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
