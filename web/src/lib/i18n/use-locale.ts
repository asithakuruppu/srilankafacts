"use client";

import { useCallback, useEffect, useState } from "react";

import { translate, type Locale, type MessageKey } from "@/lib/i18n/messages";

const KEY = "slf-lang";
const EVENT = "slf-lang-change";

function read(): Locale {
  try {
    const stored = window.localStorage.getItem(KEY);
    return stored === "si" || stored === "ta" ? stored : "en";
  } catch {
    return "en";
  }
}

/** The interface language the visitor opted into (English unless they chose a draft). */
export function useLocale(): { locale: Locale; t: (key: MessageKey) => string; setLocale: (next: Locale) => void } {
  const [locale, setState] = useState<Locale>("en");
  useEffect(() => {
    const update = () => {
      const current = read();
      // Screen readers pick the voice from <html lang>: keep it in step with the text.
      document.documentElement.lang = current;
      setState(current);
    };
    update();
    window.addEventListener(EVENT, update);
    window.addEventListener("storage", update);
    return () => {
      window.removeEventListener(EVENT, update);
      window.removeEventListener("storage", update);
    };
  }, []);
  const setLocale = useCallback((next: Locale) => {
    try {
      window.localStorage.setItem(KEY, next);
    } catch {
      // Without storage the choice lasts for this page only.
    }
    document.documentElement.lang = next;
    window.dispatchEvent(new Event(EVENT));
  }, []);
  const t = useCallback((key: MessageKey) => translate(locale, key), [locale]);
  return { locale, t, setLocale };
}
