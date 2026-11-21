"use client";

import Link from "next/link";

import { LOCALES, type Locale } from "@/lib/i18n/messages";
import { useLocale } from "@/lib/i18n/use-locale";

const LINKS = [
  ["/", "nav.atlas"],
  ["/explore", "nav.tables"],
  ["/indicators", "nav.indicators"],
  ["/elections", "nav.elections"],
  ["/area", "nav.areas"],
  ["/resolution", "nav.resolution"],
  ["/data", "nav.data"],
  ["/methods", "nav.methods"],
  ["/about", "nav.about"],
] as const;

export function SiteNav() {
  const { t } = useLocale();
  return (
    <nav className="site-nav" aria-label="Main">
      {LINKS.map(([href, key]) => (
        <Link key={href} href={href}>
          {t(key)}
        </Link>
      ))}
    </nav>
  );
}

/** Opt-in switch for draft interface translations, with a banner while one is on. */
export function LanguageSwitch() {
  const { locale, t, setLocale } = useLocale();
  return (
    <label className="language-switch">
      <span className="visually-hidden">{t("language.label")}</span>
      <select
        value={locale}
        onChange={(event) => setLocale(event.target.value as Locale)}
        aria-label={t("language.label")}
      >
        {LOCALES.map((item) => (
          <option key={item.id} value={item.id}>
            {item.label}
            {item.status === "draft-machine" ? " (draft)" : ""}
          </option>
        ))}
      </select>
    </label>
  );
}

export function LanguageBanner() {
  const { locale, t } = useLocale();
  if (locale === "en") {
    return null;
  }
  return (
    <div className="language-banner" role="note" data-testid="language-banner">
      <div className="shell">
        <strong>{t("language.draft")}</strong> <span lang="en">Machine draft translation, not yet reviewed.</span>
      </div>
    </div>
  );
}
