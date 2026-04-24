import { NextResponse } from 'next/server';
import { v4 as uuidv4 } from 'uuid';
import axios from 'axios';

export async function POST(request: Request) {
  try {
    const { url } = await request.json();

    if (!url || !url.includes("gall.dcinside.com")) {
      return NextResponse.json({ message: "유효하지 않은 URL입니다." }, { status: 400 });
    }

    const uuid = uuidv4();
    
    // GitHub API token check
    const githubToken = process.env.GITHUB_PAT;
    const repoOwner = process.env.GITHUB_REPO_OWNER;
    const repoName = process.env.GITHUB_REPO_NAME;

    if (!githubToken || !repoOwner || !repoName) {
      console.error("GitHub credentials are not set in environment variables.");
      return NextResponse.json({ 
        message: "서버 설정 오류: GitHub API 인증 정보가 누락되었습니다." 
      }, { status: 500 });
    }

    // Trigger GitHub Actions workflow via repository dispatch or workflow_dispatch
    const githubApiUrl = `https://api.github.com/repos/${repoOwner}/${repoName}/actions/workflows/analyze.yml/dispatches`;

    try {
      await axios.post(
        githubApiUrl,
        {
          ref: "main", // Assuming the action is on main branch
          inputs: {
            gallery_url: url,
            uuid: uuid
          }
        },
        {
          headers: {
            Authorization: `token ${githubToken}`,
            Accept: "application/vnd.github.v3+json"
          }
        }
      );
    } catch (ghError: unknown) {
      const axiosError = ghError as { response?: { data?: unknown }, message?: string };
      console.error("GitHub Action trigger failed:", axiosError.response?.data || axiosError.message);
      return NextResponse.json({ 
        message: "분석 워크플로우를 시작하지 못했습니다. 서버 로그를 확인해주세요." 
      }, { status: 500 });
    }

    return NextResponse.json({ 
      success: true, 
      message: "분석 워크플로우 트리거 성공",
      uuid 
    });

  } catch (error: unknown) {
    console.error("API /analyze Error:", error);
    return NextResponse.json({ message: "서버 오류가 발생했습니다." }, { status: 500 });
  }
}
