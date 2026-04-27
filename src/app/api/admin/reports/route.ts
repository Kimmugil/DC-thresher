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
    const reports = rows.map((row, index) => ({
      index:       index, // Row index for updates
      uuid:        row.get('UUID')        || '',
      status:      row.get('Status')      || 'PENDING',
      gameName:    row.get('GameName')    || '',
      galleryName: row.get('GalleryName') || '',
      requestedAt: row.get('RequestedAt') || '',
      hidden:      row.get('Hidden') === 'TRUE' || row.get('Hidden') === 'true'
    })).reverse();

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

  if (!credentialsEnv || !sheetId) return NextResponse.json({ ok: false }, { status: 500 });

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
    const rows = await sheet.getRows();

    const row = rows[rowIndex];
    if (!row) return NextResponse.json({ ok: false, message: "Row not found" }, { status: 404 });

    if (action === 'HIDE') {
      row.set('Hidden', 'TRUE');
      await row.save();
    } else if (action === 'SHOW') {
      row.set('Hidden', 'FALSE');
      await row.save();
    } else if (action === 'DELETE') {
      await row.delete();
    }

    return NextResponse.json({ ok: true });
  } catch (error: unknown) {
    console.error("Admin Action Error:", error);
    return NextResponse.json({ ok: false, message: "작업 실패" }, { status: 500 });
  }
}
