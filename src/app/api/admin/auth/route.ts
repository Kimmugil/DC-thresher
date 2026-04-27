import { NextResponse } from 'next/server';
import { JWT } from 'google-auth-library';
import { GoogleSpreadsheet } from 'google-spreadsheet';

export async function POST(req: Request) {
  try {
    const { password } = await req.json();
    
    const credentialsEnv = process.env.GOOGLE_SHEETS_CREDENTIALS;
    const sheetId        = process.env.GOOGLE_SPREADSHEET_ID;

    if (!credentialsEnv || !sheetId) {
      return NextResponse.json({ ok: false, message: "서버 설정 오류" }, { status: 500 });
    }

    const credentials = JSON.parse(credentialsEnv);
    const auth = new JWT({
      email:  credentials.client_email,
      key:    credentials.private_key,
      scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
    });

    const doc = new GoogleSpreadsheet(sheetId, auth);
    await doc.loadInfo();

    const configSheet = doc.sheetsByTitle['config'];
    if (!configSheet) {
      return NextResponse.json({ ok: false, message: "config 시트를 찾을 수 없습니다." }, { status: 404 });
    }

    const rows = await configSheet.getRows();
    let adminPassword = "";
    
    for (const row of rows) {
      const key = row.get('Key') || row.get('key') || row.get('키');
      if (key === 'AdminPassword' || key === 'admin_password') {
        adminPassword = row.get('Value') || row.get('value') || row.get('값');
        break;
      }
    }

    if (!adminPassword) {
      return NextResponse.json({ ok: false, message: "config 시트에 AdminPassword 키가 설정되지 않았습니다." }, { status: 400 });
    }

    if (password === adminPassword) {
      return NextResponse.json({ ok: true });
    } else {
      return NextResponse.json({ ok: false, message: "비밀번호가 일치하지 않습니다." }, { status: 401 });
    }

  } catch (error: unknown) {
    console.error("Admin Auth Error:", error);
    return NextResponse.json({ ok: false, message: "서버 오류가 발생했습니다." }, { status: 500 });
  }
}
