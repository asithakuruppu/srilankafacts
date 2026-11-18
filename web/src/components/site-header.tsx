import Link from "next/link";

import SearchBox from "@/components/search-box";
import { LanguageBanner, LanguageSwitch, SiteNav } from "@/components/site-nav";
import ThemeToggle from "@/components/theme-toggle";
import { getLatest } from "@/lib/release";

export default function SiteHeader() {
  const latest = getLatest();
  const notices = latest.notices ?? [];
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="site-header">
        <div className="shell header-inner">
          <Link className="brand" href="/">
            <span className="brand-mark" aria-hidden="true" />
            <span>
              Sri Lanka Facts
              <small>Every place, every number, with its source</small>
            </span>
          </Link>
          <SiteNav />
          <SearchBox compact />
          <LanguageSwitch />
          <ThemeToggle />
        </div>
      </header>
      <LanguageBanner />
      {!latest.publishable ? (
        <div className="preview-banner" role="note">
          <div className="shell">
            <strong>Private preview, not for publication.</strong> The Department of Census
            and Statistics’ reuse terms are unclear, so these figures are shown for review
            only. Release <code>{latest.release}</code>.
          </div>
        </div>
      ) : notices.length > 0 ? (
        <div className="preview-banner" role="note">
          <div className="shell">
            <strong>Non-commercial use only.</strong>{" "}
            {notices.map((n) => (
              <span key={n.dataset_id}>
                {n.attribution} {n.notice}{" "}
              </span>
            ))}
            Release <code>{latest.release}</code>.
          </div>
        </div>
      ) : null}
    </>
  );
}
