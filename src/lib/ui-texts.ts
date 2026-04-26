/**
 * UI Texts CMS  (서버 전용 — Node.js 환경에서만 실행)
 *
 * 런타임에 Google Sheets "UI_Texts" 탭에서 텍스트를 읽어
 * 하드코딩 없이 UI 문구를 관리합니다.
 *
 * - 최초 실행 시 시트가 없으면 DEFAULT_TEXTS로 탭을 자동 생성합니다.
 * - 서버 사이드에서만 호출됩니다 (layout.tsx 등).
 * - 결과는 프로세스 메모리에 5분 TTL로 캐싱됩니다.
 *
 * ⚠️  클라이언트 컴포넌트에서 이 파일을 직접 import하지 마세요.
 *     DEFAULT_TEXTS 가 필요하면 ui-texts-defaults.ts 를 import하세요.
 */

import "server-only";
import { JWT } from "google-auth-library";
import { GoogleSpreadsheet } from "google-spreadsheet";
import { DEFAULT_TEXTS } from "./ui-texts-defaults";

// DEFAULT_TEXTS 를 이 파일에서도 re-export (layout.tsx 등 서버 측 편의)
export { DEFAULT_TEXTS } from "./ui-texts-defaults";

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
