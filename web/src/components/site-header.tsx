import Link from "next/link";

import SearchBox from "@/components/search-box";
import { getLatest } from "@/lib/release";

export default function SiteHeader() {
  const latest = getLatest();
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
          <nav className="site-nav" aria-label="Main">
            <Link href="/explore">Explore</Link>
            <Link href="/indicators">Indicators</Link>
            <Link href="/data">Data</Link>
            <Link href="/methods">Methods</Link>
          </nav>
          <SearchBox compact />
        </div>
      </header>
      {!latest.publishable ? (
        <div className="preview-banner" role="note">
          <div className="shell">
            <strong>Private preview, not for publication.</strong> The Department of Census
            and Statistics’ reuse terms are unclear, so these figures are shown for review
            only. Release <code>{latest.release}</code>.
          </div>
        </div>
      ) : null}
    </>
  );
}
