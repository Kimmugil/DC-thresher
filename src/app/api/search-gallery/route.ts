import { NextRequest, NextResponse } from 'next/server';

export interface GalleryResult {
  name: string;
  id:   string;
  type: 'regular' | 'minor' | 'mini';
  url:  string;
}

// 실제 브라우저와 동일한 헤더 세트 (WAF 우회)
const WEB_HEADERS: HeadersInit = {
  "User-Agent":                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
  "Accept":                    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
  "Accept-Language":           "ko-KR,ko;q=0.9,en-US;q=0.8",
  "Accept-Encoding":           "gzip, deflate, br",
  "Referer":                   "https://www.dcinside.com/",
  "Connection":                "keep-alive",
  "Upgrade-Insecure-Requests": "1",
  "Sec-Fetch-Dest":            "document",
  "Sec-Fetch-Mode":            "navigate",
  "Sec-Fetch-Site":            "same-origin",
  "Sec-Fetch-User":            "?1",
};

// DC Inside 앱 API 헤더
const APP_HEADERS: HeadersInit = {
  "User-Agent":      "dcinside.app",
  "Referer":         "http://www.dcinside.com",
  "Accept":          "application/json, text/plain, */*",
  "Accept-Language": "ko-KR,ko;q=0.9",
  "Connection":      "Keep-Alive",
};

export async function GET(request: NextRequest) {
  const q = request.nextUrl.searchParams.get('q')?.trim();
  if (!q || q.length < 1) return NextResponse.json({ galleries: [] });

  // 시도 1: DC Inside suggest JSON API
  try {
    const suggestRes = await fetch(
      `https://suggest.dcinside.com/galley/?query=${encodeURIComponent(q)}`,
      { headers: APP_HEADERS, signal: AbortSignal.timeout(5000) }
    );
    if (suggestRes.ok) {
      const text = await suggestRes.text();
      const parsed = parseSuggestResponse(text);
      if (parsed.length > 0) {
        console.log(`[search-gallery] suggest API: ${parsed.length}건`);
        return NextResponse.json({ galleries: parsed });
      }
    }
  } catch (e) {
    console.warn('[search-gallery] suggest API 실패:', e);
  }

  // 시도 2: DC Inside 웹 검색 HTML 스크래핑
  try {
    const searchRes = await fetch(
      `https://search.dcinside.com/galley/q/${encodeURIComponent(q)}/`,
      { headers: WEB_HEADERS, signal: AbortSignal.timeout(7000) }
    );
    if (searchRes.ok) {
      const html = await searchRes.text();
      const parsed = parseGalleries(html);
      if (parsed.length > 0) {
        console.log(`[search-gallery] HTML 파싱: ${parsed.length}건`);
        return NextResponse.json({ galleries: parsed });
      }
      console.log('[search-gallery] HTML 파싱 결과 없음, 응답 앞 500자:', html.slice(0, 500));
    }
  } catch (e) {
    console.warn('[search-gallery] HTML 검색 실패:', e);
  }

  return NextResponse.json({ galleries: [] });
}

// ── suggest API 응답 파싱 ──────────────────────────────────────────
// 예상 형식: [{"id":"maple_worlds","name":"메이플 키우기","type":"minor"}, ...]
// 또는: {"galleries": [...]} 등 다양할 수 있음
function parseSuggestResponse(text: string): GalleryResult[] {
  try {
    let data = JSON.parse(text);
    // 배열이 아닌 경우 배열을 꺼냄
    if (!Array.isArray(data)) {
      data = data.galleries || data.result || data.list || data.data || [];
    }
    if (!Array.isArray(data)) return [];

    const results: GalleryResult[] = [];
    const seen = new Set<string>();

    for (const item of data) {
      if (!item || typeof item !== 'object') continue;
      const id   = String(item.id || item.gallery_id || item.gall_id || '').trim();
      const name = String(item.name || item.gallery_name || item.gall_name || item.title || '').trim();
      if (!id || !name || seen.has(id)) continue;
      if (name.length < 2 || name.length > 60) continue;
      seen.add(id);

      const rawType = String(item.type || item.gallery_type || '').toLowerCase();
      const type: GalleryResult['type'] =
        rawType.includes('minor') || rawType === 'm' ? 'minor' :
        rawType.includes('mini')                     ? 'mini'  : 'regular';
      const prefix = type === 'minor' ? 'mgallery/' : type === 'mini' ? 'mini/' : '';

      results.push({
        name,
        id,
        type,
        url: `https://gall.dcinside.com/${prefix}board/lists/?id=${id}`,
      });
      if (results.length >= 8) break;
    }
    return results;
  } catch {
    return [];
  }
}

// ── HTML 스크래핑 파서 ────────────────────────────────────────────
function parseGalleries(html: string): GalleryResult[] {
  const results: GalleryResult[] = [];
  const seen = new Set<string>();

  // 갤러리 목록 링크 추출 — 내부 중첩 태그 허용
  const linkRe = /href="https?:\/\/gall\.dcinside\.com\/(mgallery\/|mini\/)?board\/lists\/?\?(?:[^"]*[?&])?id=([a-zA-Z0-9_]+)[^"]*"[^>]*>([\s\S]*?)<\/a>/g;

  let m: RegExpExecArray | null;
  while ((m = linkRe.exec(html)) !== null) {
    const prefix   = m[1] ?? '';
    const id       = m[2];
    const rawName  = m[3].replace(/<[^>]+>/g, '').trim().replace(/\s+/g, ' ');

    if (!id || !rawName || seen.has(id)) continue;
    if (rawName.length < 2 || rawName.length > 60) continue;
    if (/^[\s\d]+$/.test(rawName)) continue;
    if (/전체글|더보기|목록|검색|바로가기|로그인|회원가입/.test(rawName)) continue;

    seen.add(id);
    const type: GalleryResult['type'] =
      prefix === 'mgallery/' ? 'minor' :
      prefix === 'mini/'     ? 'mini'  : 'regular';

    results.push({
      name: rawName,
      id,
      type,
      url: `https://gall.dcinside.com/${prefix}board/lists/?id=${id}`,
    });
    if (results.length >= 8) break;
  }
  return results;
}
