import os
import sys
import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

def main():
    if len(sys.argv) < 2:
        print("Usage: python save_to_sheets.py <uuid>")
        sys.exit(1)

    uuid = sys.argv[1]

    # Load credentials
    creds_json_str = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    sheet_id = os.environ.get("GOOGLE_SPREADSHEET_ID")

    if not creds_json_str or not sheet_id:
        print("ERROR: GOOGLE_SHEETS_CREDENTIALS or GOOGLE_SPREADSHEET_ID not set.")
        sys.exit(1)

    # Parse JSON string to dict
    try:
        creds_dict = json.loads(creds_json_str)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in GOOGLE_SHEETS_CREDENTIALS: {e}")
        sys.exit(1)

    # Scope for Google Sheets API
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(credentials)

    try:
        # Open spreadsheet
        sh = gc.open_by_key(sheet_id)
        
        # Select first sheet or create 'Reports' if it doesn't exist
        try:
            worksheet = sh.worksheet("Reports")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title="Reports", rows="100", cols="20")
            # Set headers
            headers = ["UUID", "Status", "GameName", "GalleryName", "RequestedAt", "CompletedAt", "AI_Insights", "Raw_Data"]
            worksheet.append_row(headers)

        # Load result from files
        insights = {}
        if os.path.exists("insights.json"):
            with open("insights.json", "r", encoding="utf-8") as f:
                insights = json.load(f)

        raw_data = {}
        if os.path.exists("scrape_result.json"):
            with open("scrape_result.json", "r", encoding="utf-8") as f:
                raw_data = json.load(f)

        # Basic Info
        status = "COMPLETED" if insights else "FAILED"
        game_name = insights.get("game_name", "Unknown")
        gallery_name = insights.get("gallery_name", "Unknown")
        
        # Load requested time from workflow inputs or use current time
        requested_at = datetime.utcnow().isoformat() + "Z"
        completed_at = datetime.utcnow().isoformat() + "Z"

        # Append row to Google Sheets
        row_data = [
            uuid,
            status,
            game_name,
            gallery_name,
            requested_at,
            completed_at,
            json.dumps(insights, ensure_ascii=False) if insights else "",
            json.dumps(raw_data, ensure_ascii=False) if raw_data else ""
        ]
        
        worksheet.append_row(row_data)
        print(f"Successfully saved to Google Sheets. UUID: {uuid}")

    except Exception as e:
        print(f"ERROR: Failed to save to Google Sheets: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
