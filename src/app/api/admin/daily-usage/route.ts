import { NextResponse } from "next/server";
import { getDailyUsage, resetDailyCount, setDailyLimit } from "@/lib/daily-usage";

/** GET /api/admin/daily-usage — 현재 사용량 조회 */
export async function GET() {
  try {
    const usage = await getDailyUsage();
    return NextResponse.json(usage);
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ message: msg }, { status: 500 });
  }
}

/** POST /api/admin/daily-usage
 *  { action: "RESET" }               — 오늘 카운트 0으로 초기화
 *  { action: "SET_LIMIT", value: 50 } — 일 한도 변경
 */
export async function POST(req: Request) {
  try {
    const { action, value } = await req.json();

    if (action === "RESET") {
      await resetDailyCount();
      return NextResponse.json({ ok: true });
    }

    if (action === "SET_LIMIT") {
      const n = parseInt(value);
      if (!n || n < 1) return NextResponse.json({ message: "1 이상의 숫자를 입력하세요." }, { status: 400 });
      await setDailyLimit(n);
      return NextResponse.json({ ok: true });
    }

    return NextResponse.json({ message: "알 수 없는 액션" }, { status: 400 });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    console.error("[daily-usage POST]", msg);
    return NextResponse.json({ message: msg }, { status: 500 });
  }
}
