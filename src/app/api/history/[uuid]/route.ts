import { NextResponse } from 'next/server';
import { JWT } from 'google-auth-library';
import { GoogleSpreadsheet } from 'google-spreadsheet';

export async function GET(request: Request, { params }: { params: Promise<{ uuid: string }> }) {
  try {
    const { uuid } = await params;
    
    if (!uuid) {
      return NextResponse.json({ message: "UUID is required" }, { status: 400 });
    }

    const credentialsEnv = process.env.GOOGLE_SHEETS_CREDENTIALS;
    const sheetId = process.env.GOOGLE_SPREADSHEET_ID;

    if (!credentialsEnv || !sheetId) {
       console.warn("Google Sheets credentials not set.");
       return NextResponse.json({ message: "Server misconfigured" }, { status: 500 });
    }

    const credentials = JSON.parse(credentialsEnv);
    const auth = new JWT({
      email: credentials.client_email,
      key: credentials.private_key,
      scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'],
    });

    const doc = new GoogleSpreadsheet(sheetId, auth);
    await doc.loadInfo();

    const sheet = doc.sheetsByTitle['Reports'] || doc.sheetsByIndex[0];
    
    if (!sheet) {
        return NextResponse.json({ message: "No data found" }, { status: 404 });
    }

    const rows = await sheet.getRows();
    
    // Find the row with matching UUID
    const targetRow = rows.find(row => row.get('UUID') === uuid);

    if (!targetRow) {
       // It's possible the GitHub action hasn't populated it yet, or it's invalid.
       // Return a pending state if not found.
       return NextResponse.json({ 
         report: {
           uuid,
           status: "PENDING",
         }
       });
    }

    const report = {
      uuid: targetRow.get('UUID'),
      status: targetRow.get('Status') || 'COMPLETED',
      gameName: targetRow.get('GameName'),
      galleryName: targetRow.get('GalleryName'),
      requestedAt: targetRow.get('RequestedAt'),
      completedAt: targetRow.get('CompletedAt'),
      aiInsights: targetRow.get('AI_Insights'),
      // rawData: targetRow.get('Raw_Data') // Omit raw data from API response unless needed to save bandwidth
    };

    return NextResponse.json({ report });
  } catch (error: unknown) {
    console.error(`API /history/[uuid] Error:`, error);
    return NextResponse.json({ message: "Internal Server Error" }, { status: 500 });
  }
}
