/**
 * daily-usage.ts (서버 전용)
 *
 * Google Sheets Config 탭에서 일 최대 분석 횟수를 관리합니다.
 *
 * Config 탭 필요 행 (Key | Value):
 *   daily.limit     | 30   ← 관리자가 설정
 *   daily.used      | 0    ← 자동 업데이트, 수정 금지
 *   daily.used_date |      ← 자동 업데이트, 수정 금지
 */

import "server-only";
import { JWT } from "google-auth-library";
import { GoogleSpreadsheet, GoogleSpreadsheetWorksheet } from "google-spreadsheet";

const DEFAULT_LIMIT = 30;

/** KST 기준 오늘 날짜 (YYYY-MM-DD) */
function todayKST(): string {
  const kst = new Date(Date.now() + 9 * 3600 * 1000);
  return kst.toISOString().slice(0, 10);
}

async function getConfigSheet(): Promise<GoogleSpreadsheetWorksheet> {
  const cred    = process.env.GOOGLE_SHEETS_CREDENTIALS;
  const sheetId = process.env.GOOGLE_SPREADSHEET_ID;
  if (!cred || !sheetId) throw new Error("Google Sheets credentials not set");

  const auth = new JWT({
    email:  JSON.parse(cred).client_email,
    key:    JSON.parse(cred).private_key,
    scopes: ["https://www.googleapis.com/auth/spreadsheets"],
  });
  const doc = new GoogleSpreadsheet(sheetId, auth);
  await doc.loadInfo();
  const sheet = doc.sheetsByTitle["config"];
  if (!sheet) throw new Error("Config sheet not found");
  return sheet;
}

interface RowInfo { value: string; rowNumber: number; valColIdx: number }

async function readConfigMap(sheet: GoogleSpreadsheetWorksheet): Promise<Record<string, RowInfo>> {
  await sheet.loadHeaderRow();
  const headers  = sheet.headerValues;
  const keyIdx   = headers.indexOf("Key");
  const valIdx   = headers.indexOf("Value");
  if (keyIdx === -1 || valIdx === -1) throw new Error("Config sheet: Key/Value columns not found");

  const rows = await sheet.getRows();
  const map: Record<string, RowInfo> = {};
  for (const row of rows) {
    const k = row.get("Key");
    if (k) map[k] = { value: row.get("Value") || "", rowNumber: row.rowNumber, valColIdx: valIdx };
  }
  return map;
}

/** 여러 셀을 한 번에 업데이트 */
async function patchCells(
  sheet: GoogleSpreadsheetWorksheet,
  updates: { rowNumber: number; colIdx: number; value: string }[]
) {
  if (!updates.length) return;
  const minR = Math.min(...updates.map(u => u.rowNumber));
  const maxR = Math.max(...updates.map(u => u.rowNumber));
  const minC = Math.min(...updates.map(u => u.colIdx));
  const maxC = Math.max(...updates.map(u => u.colIdx));

  await sheet.loadCells({
    startRowIndex: minR - 1, endRowIndex: maxR,
    startColumnIndex: minC,  endColumnIndex: maxC + 1,
  });
  for (const u of updates) {
    sheet.getCell(u.rowNumber - 1, u.colIdx).value = u.value;
  }
  await sheet.saveUpdatedCells();
}

export interface DailyUsage {
  count:   number;
  limit:   number;
  date:    string;  // YYYY-MM-DD KST
  allowed: boolean;
}

/** 현재 사용량만 조회 (카운트 증가 없음) */
export async function getDailyUsage(): Promise<DailyUsage> {
  const sheet  = await getConfigSheet();
  const config = await readConfigMap(sheet);
  const today  = todayKST();

  const limit = parseInt(config["daily.limit"]?.value || "") || DEFAULT_LIMIT;
  const count = config["daily.used_date"]?.value === today
    ? parseInt(config["daily.used"]?.value || "0") || 0
    : 0;

  return { count, limit, date: today, allowed: count < limit };
}

/** 요청 수락 전 호출 — 한도 초과 시 allowed:false, 허용 시 카운트 +1 */
export async function checkAndIncrement(): Promise<DailyUsage> {
  const sheet  = await getConfigSheet();
  const config = await readConfigMap(sheet);
  const today  = todayKST();

  const limit    = parseInt(config["daily.limit"]?.value || "") || DEFAULT_LIMIT;
  const dateMatch = config["daily.used_date"]?.value === today;
  const count    = dateMatch ? parseInt(config["daily.used"]?.value || "0") || 0 : 0;

  if (count >= limit) return { count, limit, date: today, allowed: false };

  // 카운트 증가
  const newCount = count + 1;
  const patches: { rowNumber: number; colIdx: number; value: string }[] = [];

  const usedRow = config["daily.used"];
  const dateRow = config["daily.used_date"];
  if (usedRow) patches.push({ rowNumber: usedRow.rowNumber, colIdx: usedRow.valColIdx, value: String(newCount) });
  if (!dateMatch && dateRow) patches.push({ rowNumber: dateRow.rowNumber, colIdx: dateRow.valColIdx, value: today });

  await patchCells(sheet, patches);
  return { count: newCount, limit, date: today, allowed: true };
}

/** 오늘 카운트 초기화 */
export async function resetDailyCount(): Promise<void> {
  const sheet  = await getConfigSheet();
  const config = await readConfigMap(sheet);
  const today  = todayKST();

  const patches: { rowNumber: number; colIdx: number; value: string }[] = [];
  const usedRow = config["daily.used"];
  const dateRow = config["daily.used_date"];
  if (usedRow) patches.push({ rowNumber: usedRow.rowNumber, colIdx: usedRow.valColIdx, value: "0" });
  if (dateRow) patches.push({ rowNumber: dateRow.rowNumber, colIdx: dateRow.valColIdx, value: today });

  await patchCells(sheet, patches);
}

/** 일 최대 한도 변경 */
export async function setDailyLimit(newLimit: number): Promise<void> {
  const sheet  = await getConfigSheet();
  const config = await readConfigMap(sheet);
  const row    = config["daily.limit"];
  if (!row) throw new Error("daily.limit key not found in Config sheet");
  await patchCells(sheet, [{ rowNumber: row.rowNumber, colIdx: row.valColIdx, value: String(newLimit) }]);
}
