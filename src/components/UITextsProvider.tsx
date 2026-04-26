"use client";

import { createContext, useContext } from "react";
import { DEFAULT_TEXTS } from "@/lib/ui-texts";

type TextsMap = Record<string, string>;

const UITextsContext = createContext<TextsMap>(DEFAULT_TEXTS);

export function UITextsProvider({
  texts,
  children,
}: {
  texts: TextsMap;
  children: React.ReactNode;
}) {
  return (
    <UITextsContext.Provider value={texts}>
      {children}
    </UITextsContext.Provider>
  );
}

/** 전체 텍스트 맵 반환 — 컴포넌트 최상단에서 구조분해하여 사용 */
export function useTexts(): TextsMap {
  return useContext(UITextsContext);
}

/** 단일 키 조회 — 없으면 기본값, 기본값도 없으면 키 자체 반환 */
export function useText(key: string): string {
  const texts = useContext(UITextsContext);
  return texts[key] ?? DEFAULT_TEXTS[key] ?? key;
}
