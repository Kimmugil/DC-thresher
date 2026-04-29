/**
 * 사이트 설정 (서버 전용)
 *
 * Google Sheets "Config" 탭에서 app.title / app.description 을 읽어
 * layout.tsx의 generateMetadata()에 제공합니다.
 *
 * Config 탭 컬럼: Key | Value | Description
 *   app.title       | DC-Thresher | AI 갤러리 분석 | ...
 *   app.description | 디시인사이드 갤러리 ... | ...
 *
 * ⚠️ 서버 컴포넌트에서만 호출하세요.
 */

import "server-only";
import { JWT } from "google-auth-library";
import { GoogleSpreadsheet } from "google-spreadsheet";

export interface SiteConfig {
  title:       string;
  description: string;
}

const DEFAULT_CONFIG: SiteConfig = {
  title:       "DC-Thresher | AI 갤러리 분석",
  description: "디시인사이드 갤러리 여론을 Gemini AI가 심층 분석합니다",
};

let _cache: { config: SiteConfig; expiresAt: number } | null = null;

export async function fetchSiteConfig(): Promise<SiteConfig> {
  if (_cache && Date.now() < _cache.expiresAt) return _cache.config;

  const credentialsEnv = process.env.GOOGLE_SHEETS_CREDENTIALS;
  const sheetId        = process.env.GOOGLE_SPREADSHEET_ID;
  if (!credentialsEnv || !sheetId) return DEFAULT_CONFIG;

  try {
    const credentials = JSON.parse(credentialsEnv);
    const auth = new JWT({
      email:  credentials.client_email,
      key:    credentials.private_key,
      scopes: ["https://www.googleapis.com/auth/spreadsheets.readonly"],
    });

    const doc = new GoogleSpreadsheet(sheetId, auth);
    await doc.loadInfo();

    const sheet = doc.sheetsByTitle["Config"];
    if (!sheet) return DEFAULT_CONFIG;

    const rows = await sheet.getRows();
    const map: Record<string, string> = {};
    for (const row of rows) {
      const key   = row.get("Key");
      const value = row.get("Value");
      if (key && value) map[key] = value;
    }

    const config: SiteConfig = {
      title:       map["app.title"]       || DEFAULT_CONFIG.title,
      description: map["app.description"] || DEFAULT_CONFIG.description,
    };

    _cache = { config, expiresAt: Date.now() + 5 * 60 * 1000 };
    return config;
  } catch (err) {
    console.error("[site-config] Config 탭 읽기 실패:", err);
    return DEFAULT_CONFIG;
  }
}
