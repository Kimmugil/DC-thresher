import { NextResponse } from 'next/server';
import { JWT } from 'google-auth-library';
import { GoogleSpreadsheet } from 'google-spreadsheet';

export async function GET() {
  try {
    const credentialsEnv = process.env.GOOGLE_SHEETS_CREDENTIALS;
    const sheetId = process.env.GOOGLE_SPREADSHEET_ID;

    if (!credentialsEnv || !sheetId) {
      console.warn("Google Sheets credentials not set. Returning empty list.");
      return NextResponse.json({ reports: [] });
    }

    const credentials = JSON.parse(credentialsEnv);
    const auth = new JWT({
      email: credentials.client_email,
      key: credentials.private_key,
      scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
    });

    const doc = new GoogleSpreadsheet(sheetId, auth);
    await doc.loadInfo();

    // Find the sheet or use the first one
    const sheet = doc.sheetsByTitle['Reports'] || doc.sheetsByIndex[0];
    
    if (!sheet) {
       return NextResponse.json({ reports: [] });
    }

    const rows = await sheet.getRows();
    
    const reports = rows.map((row) => {
      // Map columns to fields. Assuming columns: UUID, Status, GameName, GalleryName, RequestedAt, CompletedAt, AI_Insights, Raw_Data
      return {
        uuid: row.get('UUID') || '',
        status: row.get('Status') || 'PENDING',
        gameName: row.get('GameName') || '',
        galleryName: row.get('GalleryName') || '',
        requestedAt: row.get('RequestedAt') || '',
      };
    }).reverse(); // Latest first

    return NextResponse.json({ reports });
  } catch (error: unknown) {
    console.error("API /history Error:", error);
    // If it fails, return empty list gracefully so frontend doesn't crash entirely.
    return NextResponse.json({ reports: [] }, { status: 500 });
  }
}
