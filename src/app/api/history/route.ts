import { NextResponse } from 'next/server';
import { JWT } from 'google-auth-library';
import { GoogleSpreadsheet } from 'google-spreadsheet';

export async function GET() {
  const credentialsEnv = process.env.GOOGLE_SHEETS_CREDENTIALS;
  const sheetId        = process.env.GOOGLE_SPREADSHEET_ID;

  if (!credentialsEnv || !sheetId) {
    console.error("Google Sheets credentials not set.");
    return NextResponse.json(
      { message: "서버 설정 오류: Google Sheets 인증 정보가 누락되었습니다." },
      { status: 500 }
    );
  }

  try {
    const credentials = JSON.parse(credentialsEnv);
    const auth = new JWT({
      email:  credentials.client_email,
      key:    credentials.private_key,
      scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
    });

    const doc = new GoogleSpreadsheet(sheetId, auth);
    await doc.loadInfo();

    const sheet = doc.sheetsByTitle['Reports'] || doc.sheetsByIndex[0];
    if (!sheet) {
      return NextResponse.json({ reports: [] });
    }

    const rows = await sheet.getRows();

    const reports = rows
      .filter(row => row.get('Hidden') !== 'TRUE' && row.get('Hidden') !== 'true')
      .map((row) => {
        // AI_Insights JSON에서 카드 표시용 필드 추출
        let oneLiner  = '';
        let dateRange = '';
        let top3Posts: { title: string; comment_count: number }[] = [];

        const rawInsights = row.get('AI_Insights');
        if (rawInsights) {
          try {
            const parsed = JSON.parse(rawInsights);
            oneLiner  = parsed?.critic_one_liner || '';
            dateRange = parsed?.scrape_meta?.date_range || '';
            const tp  = parsed?.scrape_meta?.top_posts || [];
            top3Posts = (tp as { title?: string; comment_count?: number }[])
              .slice(0, 3)
              .map(p => ({ title: p.title || '', comment_count: p.comment_count || 0 }));
          } catch { /* ignore */ }
        }
        return {
          uuid:        row.get('UUID')        || '',
          status:      row.get('Status')      || 'PENDING',
          gameName:    row.get('GameName')    || '',
          galleryName: row.get('GalleryName') || '',
          requestedAt: row.get('RequestedAt') || '',
          oneLiner,
          dateRange,
          top3Posts,
        };
      })
      .reverse(); // 최신순

    return NextResponse.json({ reports });

  } catch (error: unknown) {
    console.error("API /history Error:", error);
    return NextResponse.json(
      { message: "리포트 목록을 불러오는 데 실패했습니다." },
      { status: 500 }
    );
  }
}
