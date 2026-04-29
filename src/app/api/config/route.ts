import { NextResponse } from "next/server";
import { fetchSiteConfig } from "@/lib/site-config";

/**
 * GET /api/config
 * 클라이언트 컴포넌트에서 사용 가능한 사이트 설정 값 반환.
 * 민감 정보 없음. 5분 캐시.
 */
export async function GET() {
  const config = await fetchSiteConfig();
  return NextResponse.json(
    { marqueeSpeedPerCard: config.marqueeSpeedPerCard },
    { headers: { "Cache-Control": "public, max-age=300, stale-while-revalidate=60" } }
  );
}
