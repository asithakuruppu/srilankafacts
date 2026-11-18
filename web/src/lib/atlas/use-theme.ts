"use client";

import { useEffect, useState } from "react";

/** The page theme: the visitor's choice (`data-theme` on <html>), else the system setting. */
export function useTheme(): "light" | "dark" {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const read = () => {
      const chosen = document.documentElement.dataset.theme;
      setTheme(chosen === "dark" || chosen === "light" ? chosen : media.matches ? "dark" : "light");
    };
    read();
    media.addEventListener("change", read);
    const observer = new MutationObserver(read);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => {
      media.removeEventListener("change", read);
      observer.disconnect();
    };
  }, []);
  return theme;
}
