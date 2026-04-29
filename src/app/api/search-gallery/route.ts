import { NextRequest, NextResponse } from 'next/server';

const WEB_HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
  "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
  "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
  "Referer": "https://www.dcinside.com/",
};

export interface GalleryResult {
  name: string;
  id: string;
  type: 'regular' | 'minor' | 'mini';
  url: string;
}

export async function GET(request: NextRequest) {
  const q = request.nextUrl.searchParams.get('q')?.trim();
  if (!q || q.length < 1) return NextResponse.json({ galleries: [] });

  try {
    const res = await fetch(
      `https://search.dcinside.com/galley/q/${encodeURIComponent(q)}/`,
      { headers: WEB_HEADERS, signal: AbortSignal.timeout(7000) }
    );

    if (!res.ok) return NextResponse.json({ galleries: [] });

    const html = await res.text();
    const galleries = parseGalleries(html);
    return NextResponse.json({ galleries });

  } catch (e) {
    console.error('[search-gallery]', e);
    return NextResponse.json({ galleries: [] });
  }
}

function parseGalleries(html: string): GalleryResult[] {
  const results: GalleryResult[] = [];
  const seen = new Set<string>();

  // DC Inside 갤러리 검색 결과 페이지에서 갤러리 링크+이름 추출
  // 패턴: href="...dcinside.com/(mgallery/|mini/)?board/lists/?id=<ID>..." 와 인접 텍스트
  // 내부에 <span> 등 중첩 태그가 있을 수 있으므로 [\s\S]*? 로 캡처 후 태그 제거
  const linkRe = /href="https?:\/\/gall\.dcinside\.com\/(mgallery\/|mini\/)?board\/lists\/?\?(?:[^"]*[?&])?id=([a-zA-Z0-9_]+)[^"]*"[^>]*>([\s\S]*?)<\/a>/g;

  let m: RegExpExecArray | null;
  while ((m = linkRe.exec(html)) !== null) {
    const prefix = m[1] ?? '';
    const id     = m[2];
    // 중첩 태그 제거 후 텍스트만 추출
    const rawName = m[3].replace(/<[^>]+>/g, '').trim().replace(/\s+/g, ' ');

    // 노이즈 필터
    if (!id || !rawName || seen.has(id)) continue;
    if (rawName.length < 2 || rawName.length > 60 || /^[\s\d]+$/.test(rawName)) continue;
    if (/전체글|더보기|목록|검색|바로가기|로그인|회원가입/.test(rawName)) continue;

    seen.add(id);
    const type: GalleryResult['type'] = prefix === 'mgallery/' ? 'minor'
      : prefix === 'mini/' ? 'mini' : 'regular';

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
