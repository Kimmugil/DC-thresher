import "./globals.css";
import { Inter } from "next/font/google";
import { Noto_Sans_KR } from "next/font/google";
import { fetchUITexts } from "@/lib/ui-texts";
import { fetchSiteConfig } from "@/lib/site-config";
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

// Config / UI_Texts를 구글 시트에서 매 요청마다 읽어야 하므로 정적 캐시 비활성화
export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function generateMetadata() {
  const config = await fetchSiteConfig();
  return {
    title:       config.title,
    description: config.description,
  };
}

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
