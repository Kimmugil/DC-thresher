import { NextResponse } from 'next/server';
import { v4 as uuidv4 } from 'uuid';
import axios from 'axios';
import { checkAndIncrement } from '@/lib/daily-usage';

// DC Inside 갤러리 URL 패턴 검증 (단순 문자열 포함 검사 대신 정규식 적용)
const DC_GALLERY_URL_PATTERN =
  /^https?:\/\/gall\.dcinside\.com\/(mgallery\/|mini\/)?board\/(lists|view)\/?\?(?:[^"'<>]*[?&])?id=[a-zA-Z0-9_]+/;

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const url: string = typeof body?.url === 'string' ? body.url.trim() : '';

    if (!url || !DC_GALLERY_URL_PATTERN.test(url)) {
      return NextResponse.json(
        { message: "유효하지 않은 디시인사이드 갤러리 URL입니다. 주소창의 URL을 그대로 붙여넣어 주세요." },
        { status: 400 }
      );
    }

    const githubToken = process.env.GITHUB_PAT;
    const repoOwner   = process.env.GITHUB_REPO_OWNER;
    const repoName    = process.env.GITHUB_REPO_NAME;

    if (!githubToken || !repoOwner || !repoName) {
      console.error("GitHub credentials are not set in environment variables.");
      return NextResponse.json(
        { message: "서버 설정 오류: GitHub API 인증 정보가 누락되었습니다." },
        { status: 500 }
      );
    }

    // 일 사용량 체크 & 증가
    try {
      const usage = await checkAndIncrement();
      if (!usage.allowed) {
        return NextResponse.json(
          { message: `오늘의 분석 한도(${usage.limit}회)에 도달했습니다. 내일 자정(KST)에 초기화됩니다.` },
          { status: 429 }
        );
      }
    } catch (usageErr) {
      // Config 탭 읽기 실패 시 분석은 허용 (서비스 중단 방지)
      console.warn("[daily-usage] 한도 체크 실패 (스킵):", usageErr);
    }

    const uuid        = uuidv4();
    const requestedAt = new Date().toISOString(); // 실제 요청 시각 — save_to_sheets.py에 전달

    const githubApiUrl = `https://api.github.com/repos/${repoOwner}/${repoName}/actions/workflows/analyze.yml/dispatches`;

    try {
      await axios.post(
        githubApiUrl,
        {
          ref: "main",
          inputs: {
            gallery_url:  url,
            uuid:         uuid,
            requested_at: requestedAt,
          },
        },
        {
          headers: {
            Authorization: `token ${githubToken}`,
            Accept: "application/vnd.github.v3+json",
          },
        }
      );
    } catch (ghError: unknown) {
      const axiosError = ghError as { response?: { data?: unknown }; message?: string };
      console.error("GitHub Action trigger failed:", axiosError.response?.data || axiosError.message);
      return NextResponse.json(
        { message: "분석 워크플로우를 시작하지 못했습니다. 서버 로그를 확인해주세요." },
        { status: 500 }
      );
    }

    return NextResponse.json({ success: true, uuid, requestedAt });

  } catch (error: unknown) {
    console.error("API /analyze Error:", error);
    return NextResponse.json({ message: "서버 오류가 발생했습니다." }, { status: 500 });
  }
}
