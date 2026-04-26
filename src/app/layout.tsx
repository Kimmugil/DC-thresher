import "./globals.css";
import { Inter } from "next/font/google";
import { Noto_Sans_KR } from "next/font/google";
import { fetchUITexts } from "@/lib/ui-texts";
import { UITextsProvider } from "@/components/UITextsProvider";

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
  // 서버에서 UI 텍스트를 미리 가져와 클라이언트 컴포넌트에 주입
  const texts = await fetchUITexts();

  return (
    <html lang="ko" className={`${inter.variable} ${notoSansKR.variable}`}>
      <body>
        <UITextsProvider texts={texts}>{children}</UITextsProvider>
      </body>
    </html>
  );
}
