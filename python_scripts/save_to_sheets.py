import os
import sys
import json
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

MAX_CELL = 49000   # Google Sheets 단일 셀 한계(50,000자) 안전 여유

# ── 갤러리 전용 시트 컬럼 정의 ────────────────────────────────────
GALLERY_SHEET_HEADERS = [
    "AnalyzedAt", "UUID", "GameName", "DateRange",
    "TotalPosts", "ConceptPosts", "AnalysisMethod",
    "CriticOneLiner", "Keywords",
    "Pos1", "Pos2", "Pos3",
    "Neg1", "Neg2", "Neg3",
    "Balance", "Operation", "Bug", "Payment", "Content",
    "MajorIssues",
]


def _get_or_create_gallery_sheet(spreadsheet, tab_name):
    """갤러리 전용 탭이 없으면 헤더와 함께 생성, 있으면 그대로 반환."""
    try:
        return spreadsheet.worksheet(tab_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(
            title=tab_name,
            rows="500",
            cols=str(len(GALLERY_SHEET_HEADERS)),
        )
        ws.append_row(GALLERY_SHEET_HEADERS)
        return ws


def save_to_gallery_sheet(spreadsheet, slim_raw, insights, uuid, analyzed_at):
    """
    갤러리 ID별 전용 탭(gall_{id})에 분석 결과를 누적 저장합니다.
    gallery_id 를 찾을 수 없으면 조용히 건너뜁니다.
    """
    gallery_id = slim_raw.get("gallery_id") or insights.get("gallery_id")
    if not gallery_id:
        print("[WARN] gallery_id를 찾을 수 없어 갤러리 전용 시트 저장을 건너뜁니다.")
        return

    tab_name = f"gall_{gallery_id}"
    ws = _get_or_create_gallery_sheet(spreadsheet, tab_name)

    # ── 값 추출 ──────────────────────────────────────────────────
    game_name       = insights.get("game_name", slim_raw.get("gallery_name", ""))
    date_range      = slim_raw.get("date_range_str", "")
    total_posts     = slim_raw.get("total_posts", "")
    concept_posts   = slim_raw.get("concept_posts", "")
    analysis_method = slim_raw.get("analysis_method", "")

    critic        = insights.get("critic_one_liner", "")
    keywords_list = insights.get("top_keywords", [])
    keywords_str  = ", ".join(keywords_list) if isinstance(keywords_list, list) else str(keywords_list)

    # 긍정/부정 여론 요약 (최대 3개씩)
    sentiment  = insights.get("sentiment_summary") or {}
    pos_items  = sentiment.get("positive") or []
    neg_items  = sentiment.get("negative") or []
    pos_cols   = [(item.get("summary", "") if isinstance(item, dict) else "") for item in pos_items[:3]]
    neg_cols   = [(item.get("summary", "") if isinstance(item, dict) else "") for item in neg_items[:3]]
    while len(pos_cols) < 3: pos_cols.append("")
    while len(neg_cols) < 3: neg_cols.append("")

    # 불만 카테고리 점수
    ca = insights.get("complaint_analysis") or {}
    def _score(key):
        cat = ca.get(key)
        return cat.get("score", "") if isinstance(cat, dict) else ""

    # 주요 이슈 (제목만 콤마 구분, 500자 이하)
    issues_list      = insights.get("major_issues") or []
    major_issues_str = ", ".join(
        issue.get("issue_title", "") for issue in issues_list if isinstance(issue, dict)
    )
    if len(major_issues_str) > 500:
        major_issues_str = major_issues_str[:497] + "..."

    row = [
        analyzed_at, uuid, game_name, date_range,
        total_posts, concept_posts, analysis_method,
        critic, keywords_str,
        pos_cols[0], pos_cols[1], pos_cols[2],
        neg_cols[0], neg_cols[1], neg_cols[2],
        _score("balance"), _score("operation"), _score("bug"),
        _score("payment"), _score("content"),
        major_issues_str,
    ]
    ws.append_row(row)
    print(f"[INFO] 갤러리 전용 시트 '{tab_name}' 에 저장 완료.")


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

        # ── Reports 탭 (메인 기록) ───────────────────────────────
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

        # ── Raw_Data ─────────────────────────────────────────────
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
        print(f"Successfully saved to Google Sheets (Reports). UUID: {uuid}, Status: {status}")

        # ── 갤러리 전용 탭 누적 저장 (분석 성공 시에만) ──────────
        if status == "COMPLETED":
            save_to_gallery_sheet(sh, slim_raw, insights, uuid, completed_at)

    except Exception as e:
        print(f"ERROR: Failed to save to Google Sheets: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
