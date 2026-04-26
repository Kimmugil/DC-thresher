/**
 * UI Texts CMS
 *
 * 런타임에 Google Sheets "UI_Texts" 탭에서 텍스트를 읽어
 * 하드코딩 없이 UI 문구를 관리합니다.
 *
 * - 최초 실행 시 시트가 없으면 DEFAULT_TEXTS로 탭을 자동 생성합니다.
 * - 서버 사이드에서만 호출됩니다 (layout.tsx 등).
 * - 결과는 프로세스 메모리에 5분 TTL로 캐싱됩니다.
 */

import { JWT } from "google-auth-library";
import { GoogleSpreadsheet } from "google-spreadsheet";

// ── 기본값 ─────────────────────────────────────────────────────────
export const DEFAULT_TEXTS: Record<string, string> = {
  /* ── 홈 페이지 ─────────────────────────────────────── */
  "home.nav_history":        "보관함",
  "home.badge":              "Powered by Gemini 2.5 Flash",
  "home.title_line1":        "갤러리 민심,",
  "home.title_accent":       "AI가 읽다",
  "home.subtitle":           "DC Inside 갤러리 URL 하나로 게시글을 자동 수집하고, Gemini AI가 여론·불만·이슈를 심층 분석한 리포트를 발행합니다.",
  "home.url_label":          "갤러리 URL",
  "home.url_placeholder":    "https://gall.dcinside.com/mgallery/board/lists?id=...",
  "home.submit_btn":         "리포트 발행 시작하기",
  "home.submit_loading":     "분석 준비 중...",
  "home.status_sending":     "분석 요청을 전송하는 중...",
  "home.status_redirecting": "요청 완료! 분석 페이지로 이동합니다...",
  "home.step1_label":        "URL 입력",
  "home.step1_desc":         "갤러리 주소 붙여넣기",
  "home.step2_label":        "자동 수집",
  "home.step2_desc":         "최신 게시글 스크래핑",
  "home.step3_label":        "AI 분석",
  "home.step3_desc":         "Gemini 여론 심층 분석",
  "home.step4_label":        "리포트",
  "home.step4_desc":         "결과 즉시 열람 가능",
  "home.footer_note":        "마이너·정식·미니 갤러리 지원 · 분석 소요 약 1~3분 · 리포트는 고유 링크로 영구 보관",
  "home.error_empty_url":    "디시인사이드 갤러리 URL을 입력해주세요.",
  "home.error_invalid_url":  "올바른 디시인사이드 갤러리 URL이 아닙니다. 주소창 URL을 그대로 붙여넣어 주세요.",
  "home.error_generic":      "분석 요청에 실패했습니다. 잠시 후 다시 시도해주세요.",

  /* ── 보관함 페이지 ─────────────────────────────────── */
  "history.back_btn":        "새 분석 요청",
  "history.header_label":    "분석 리포트 보관함",
  "history.title":           "분석 리포트 보관함",
  "history.subtitle":        "지금까지 발행된 DC-Thresher AI 리포트 전체 목록입니다.",
  "history.empty_title":     "아직 발행된 리포트가 없습니다",
  "history.empty_desc":      "첫 번째 갤러리 분석을 요청해보세요.",
  "history.empty_btn":       "새 분석 시작",
  "history.error_load":      "리포트 목록을 불러오지 못했습니다.",
  "history.loading_game":    "게임명 수집 중...",
  "history.loading_gallery": "갤러리명 수집 중...",
  "history.status_completed":"완료",
  "history.status_pending":  "분석 중",
  "history.status_failed":   "실패",

  /* ── 리포트 상세 페이지 ────────────────────────────── */
  "report.back_btn":         "목록",
  "report.default_title":    "AI 분석 리포트",
  "report.loading_text":     "리포트 데이터를 불러오는 중...",
  "report.error_title":      "오류 발생",
  "report.error_not_found":  "해당 리포트를 찾을 수 없습니다.",
  "report.error_generic":    "리포트를 불러오는 중 오류가 발생했습니다.",
  "report.back_to_list":     "목록으로 돌아가기",
  "report.analyzing_title":  "AI가 갤러리를 분석 중입니다",
  "report.analyzing_desc":   "게시글 스크래핑 및 Gemini AI 분석에는 갤러리 규모에 따라 약 1~3분이 소요됩니다.",
  "report.timeout_msg":      "분석 시간이 초과되었습니다 (10분). 페이지를 새로고침하거나 다시 요청해주세요.",
  "report.status_completed": "분석 완료",
  "report.ai_summary_label": "AI 한줄 요약",
  "report.section_positive": "긍정 여론",
  "report.section_negative": "부정 여론",
  "report.section_issues":   "주요 이슈 리스트",
  "report.section_complaints":"불만 카테고리 분석",
  "report.mention_freq":     "언급 빈도",
  "report.read_original":    "원문 보기",
  "report.no_positive":      "수집된 긍정 여론이 없습니다.",
  "report.no_negative":      "수집된 부정 여론이 없습니다.",
  "report.req_time":         "요청",
  "report.done_time":        "완료",
  "report.game_unknown":     "게임명 확인 불가",
  "report.polling_label":    "폴링",
  "report.req_id_label":     "요청 ID",
  "report.complaint_balance":   "밸런스/게임성",
  "report.complaint_operation": "운영/소통",
  "report.complaint_bug":       "버그/최적화",
  "report.complaint_payment":   "과금/BM",
  "report.complaint_content":   "콘텐츠/업데이트",
  "report.complaint_example_label": "대표 발언",
};

// ── 캐시 (프로세스 메모리, 5분 TTL) ────────────────────────────────
let _cache: { texts: Record<string, string>; expiresAt: number } | null = null;

// ── Sheet 초기화 & 읽기 ────────────────────────────────────────────
async function _fetchFromSheets(): Promise<Record<string, string>> {
  const credentialsEnv = process.env.GOOGLE_SHEETS_CREDENTIALS;
  const sheetId        = process.env.GOOGLE_SPREADSHEET_ID;
  if (!credentialsEnv || !sheetId) return {};

  try {
    const credentials = JSON.parse(credentialsEnv);
    const auth = new JWT({
      email:  credentials.client_email,
      key:    credentials.private_key,
      scopes: ["https://www.googleapis.com/auth/spreadsheets"],
    });

    const doc = new GoogleSpreadsheet(sheetId, auth);
    await doc.loadInfo();

    // UI_Texts 탭이 없으면 기본값으로 자동 생성
    let sheet = doc.sheetsByTitle["UI_Texts"];
    if (!sheet) {
      console.info("[ui-texts] UI_Texts 탭 없음 → 기본값으로 자동 생성");
      sheet = await doc.addSheet({
        title:        "UI_Texts",
        headerValues: ["Key", "Value", "Description"],
      });
      const seedRows = Object.entries(DEFAULT_TEXTS).map(([key, value]) => ({
        Key:         key,
        Value:       value,
        Description: "",
      }));
      await sheet.addRows(seedRows);
      // 방금 DEFAULT_TEXTS로 초기화했으니 캐시는 빈 맵 반환 (defaults 사용)
      return {};
    }

    const rows = await sheet.getRows();
    const texts: Record<string, string> = {};
    for (const row of rows) {
      const key   = row.get("Key");
      const value = row.get("Value");
      if (key && value !== undefined && value !== "") {
        texts[key] = value;
      }
    }
    return texts;
  } catch (err) {
    console.error("[ui-texts] Sheets 읽기 실패:", err);
    return {};
  }
}

// ── 공개 API ───────────────────────────────────────────────────────
export async function fetchUITexts(): Promise<Record<string, string>> {
  if (_cache && Date.now() < _cache.expiresAt) {
    return _cache.texts;
  }
  const sheetTexts = await _fetchFromSheets();
  const texts      = { ...DEFAULT_TEXTS, ...sheetTexts };
  _cache = { texts, expiresAt: Date.now() + 5 * 60 * 1000 };
  return texts;
}
