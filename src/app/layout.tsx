import "./globals.css";
import { Inter } from "next/font/google";
import { Noto_Sans_KR } from "next/font/google";

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

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ko" className={`${inter.variable} ${notoSansKR.variable}`}>
      <body>{children}</body>
    </html>
  );
}
