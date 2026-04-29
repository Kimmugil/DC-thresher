import { NextResponse } from 'next/server';
import { JWT } from 'google-auth-library';
import { GoogleSpreadsheet } from 'google-spreadsheet';

export async function GET(req: Request) {
  // 간단한 비밀번호 검증은 생략하거나 헤더/토큰으로 구현해야 하지만, 이 예제에서는 단순화합니다.
  const credentialsEnv = process.env.GOOGLE_SHEETS_CREDENTIALS;
  const sheetId        = process.env.GOOGLE_SPREADSHEET_ID;

  if (!credentialsEnv || !sheetId) return NextResponse.json({ message: "서버 설정 오류" }, { status: 500 });

  try {
    const credentials = JSON.parse(credentialsEnv);
    const auth = new JWT({
      email:  credentials.client_email,
      key:    credentials.private_key,
      scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });

    const doc = new GoogleSpreadsheet(sheetId, auth);
    await doc.loadInfo();

    const sheet = doc.sheetsByTitle['Reports'] || doc.sheetsByIndex[0];
    if (!sheet) return NextResponse.json({ reports: [] });

    const rows = await sheet.getRows();
    const reports = rows.map((row, index) => {
      let oneLiner = '';
      const rawInsights = row.get('AI_Insights');
      if (rawInsights) {
        try { oneLiner = JSON.parse(rawInsights)?.critic_one_liner || ''; } catch { /* ignore */ }
      }
      return {
        index:       index,
        uuid:        row.get('UUID')        || '',
        status:      row.get('Status')      || 'PENDING',
        gameName:    row.get('GameName')    || '',
        galleryName: row.get('GalleryName') || '',
        requestedAt: row.get('RequestedAt') || '',
        hidden:      row.get('Hidden') === 'TRUE' || row.get('Hidden') === 'true',
        oneLiner,
      };
    }).reverse();

    return NextResponse.json({ reports });
  } catch (error: unknown) {
    console.error("Admin API Error:", error);
    return NextResponse.json({ message: "리포트 목록을 불러오는 데 실패했습니다." }, { status: 500 });
  }
}

export async function POST(req: Request) {
  const { action, rowIndex } = await req.json();
  const credentialsEnv = process.env.GOOGLE_SHEETS_CREDENTIALS;
  const sheetId        = process.env.GOOGLE_SPREADSHEET_ID;

  if (!credentialsEnv || !sheetId) {
    return NextResponse.json({ ok: false, message: "서버 설정 오류" }, { status: 500 });
  }

  try {
    const credentials = JSON.parse(credentialsEnv);
    const auth = new JWT({
      email:  credentials.client_email,
      key:    credentials.private_key,
      scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });

    const doc = new GoogleSpreadsheet(sheetId, auth);
    await doc.loadInfo();
    const sheet = doc.sheetsByTitle['Reports'] || doc.sheetsByIndex[0];
    const rows  = await sheet.getRows();

    const row = rows[rowIndex];
    if (!row) {
      return NextResponse.json(
        { ok: false, message: `Row ${rowIndex} not found (total: ${rows.length})` },
        { status: 404 }
      );
    }

    if (action === 'DELETE') {
      await row.delete();
      return NextResponse.json({ ok: true });
    }

    if (action === 'HIDE' || action === 'SHOW') {
      // Hidden 컬럼이 없으면 자동으로 추가
      await sheet.loadHeaderRow();
      const headers: string[] = [...sheet.headerValues];
      let hiddenColIdx = headers.indexOf('Hidden');

      if (hiddenColIdx === -1) {
        hiddenColIdx = headers.length;
        await sheet.setHeaderRow([...headers, 'Hidden']);
      }

      // row.set + save 대신 셀 직접 업데이트 (컬럼 인식 문제 우회)
      const rowNum = row.rowNumber; // 1-based 시트 행 번호
      await sheet.loadCells({
        startRowIndex:    rowNum - 1,
        endRowIndex:      rowNum,
        startColumnIndex: hiddenColIdx,
        endColumnIndex:   hiddenColIdx + 1,
      });

      const cell = sheet.getCell(rowNum - 1, hiddenColIdx);
      cell.value  = action === 'HIDE' ? 'TRUE' : 'FALSE';
      await sheet.saveUpdatedCells();

      return NextResponse.json({ ok: true });
    }

    return NextResponse.json({ ok: false, message: "알 수 없는 액션" }, { status: 400 });

  } catch (error: unknown) {
    const msg = error instanceof Error ? error.message : String(error);
    console.error("Admin Action Error:", msg);
    return NextResponse.json({ ok: false, message: msg }, { status: 500 });
  }
}
