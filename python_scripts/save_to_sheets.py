import os
import sys
import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

MAX_CELL = 49000   # Google Sheets 단일 셀 한계(50,000자) 안전 여유


def main():
    if len(sys.argv) < 2:
        print("Usage: python save_to_sheets.py <uuid> [requested_at]")
        sys.exit(1)

    uuid         = sys.argv[1]
    requested_at = sys.argv[2] if len(sys.argv) > 2 else datetime.utcnow().isoformat() + "Z"

    creds_json_str = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    sheet_id       = os.environ.get("GOOGLE_SPREADSHEET_ID")

    if not creds_json_str or not sheet_id:
        print("ERROR: GOOGLE_SHEETS_CREDENTIALS or GOOGLE_SPREADSHEET_ID not set.")
        sys.exit(1)

    try:
        creds_dict = json.loads(creds_json_str)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in GOOGLE_SHEETS_CREDENTIALS: {e}")
        sys.exit(1)

    scopes      = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc          = gspread.authorize(credentials)

    try:
        sh = gc.open_by_key(sheet_id)

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

        # ── AI_Insights ─────────────────────────────────────────────
        # 프롬프트가 15,000자 이내 출력을 강제하므로 정상적으로는 한도를 넘지 않음.
        # 안전망: 초과 시 최소 필드만 저장하고 경고 로그 출력.
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

        # ── Raw_Data ─────────────────────────────────────────────────
        # 게시글 배열(all_metas, analysis_data)은 수십~수백 KB → 통계 수치만 저장
        BULKY_KEYS   = {"all_metas", "analysis_data"}
        slim_raw     = {k: v for k, v in raw_data.items() if k not in BULKY_KEYS} if raw_data else {}
        raw_data_str = json.dumps(slim_raw, ensure_ascii=False) if slim_raw else ""
        if len(raw_data_str) > MAX_CELL:
            raw_data_str = ""
            print("[WARN] slim raw_data_str still too large, saving empty string")

        print(f"[INFO] insights={len(insights_str)}chars  raw_data={len(raw_data_str)}chars")

        worksheet.append_row([
            uuid, status, game_name, gallery_name,
            requested_at, completed_at,
            insights_str, raw_data_str,
        ])
        print(f"Successfully saved to Google Sheets. UUID: {uuid}, Status: {status}")

    except Exception as e:
        print(f"ERROR: Failed to save to Google Sheets: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
