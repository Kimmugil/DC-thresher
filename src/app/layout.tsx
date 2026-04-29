import "./globals.css";
import { Inter } from "next/font/google";
import { Noto_Sans_KR } from "next/font/google";
import { fetchUITexts } from "@/lib/ui-texts";
import { UITextsProvider } from "@/components/UITextsProvider";
import Navigation from "@/components/Navigation";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

const notoSansKR = Noto_Sans_KR({
  subsets: ["latin"],
  weight: ["400", "500", "700", "900"],
  variable: "--font-korean",
  display: "swap",
});

export const metadata = {
  title: "DC-Thresher | AI 갤러리 분석",
  description: "디시인사이드 갤러리 여론을 Gemini AI가 심층 분석합니다",
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const texts = await fetchUITexts();

  return (
    <html lang="ko" className={`${inter.variable} ${notoSansKR.variable}`}>
      <head>
        {/* Pretendard — 네오 브루탈리즘 한국어 폰트 */}
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css"
        />
      </head>
      <body>
        <UITextsProvider texts={texts}>
          <Navigation />
          {children}
        </UITextsProvider>
      </body>
    </html>
  );
}
