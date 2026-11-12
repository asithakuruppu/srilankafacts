import Link from "next/link";

import { getLatest } from "@/lib/release";

export default function SiteFooter() {
  const latest = getLatest();
  return (
    <footer className="site-footer">
      <div className="shell footer-grid">
        <div>
          <p className="footer-brand">Sri Lanka Facts</p>
          <p className="muted">
            A place-based data platform. Every published value traces to a dataset, a raw
            snapshot and a source locator.
          </p>
        </div>
        <div>
          <p className="footer-heading">The atlas</p>
          <ul>
            <li>
              <Link href="/explore">Explore the map</Link>
            </li>
            <li>
              <Link href="/indicators">Indicators</Link>
            </li>
            <li>
              <Link href="/data">Data and API</Link>
            </li>
            <li>
              <Link href="/methods">Methods and limits</Link>
            </li>
            <li>
              <Link href="/corrections">Corrections</Link>
            </li>
          </ul>
        </div>
        <div>
          <p className="footer-heading">This release</p>
          <ul>
            <li>
              <code>{latest.release}</code>
            </li>
            <li>{latest.publishable ? "Public release" : "Private preview"}</li>
            {latest.use === "non_commercial" ? <li>Non-commercial use only</li> : null}
            <li>{latest.observation_count.toLocaleString("en-LK")} observations</li>
            <li>{latest.geography_count.toLocaleString("en-LK")} geographies</li>
          </ul>
        </div>
      </div>
      <div className="shell footer-note">
        <p>{latest.citation}</p>
        <p>
          Census data: Department of Census and Statistics, Census of Population and Housing
          2024. Boundaries: OCHA COD-AB v03. This is not an official DCS publication.
        </p>
        {(latest.notices ?? []).map((n) => (
          <p key={n.dataset_id}>
            {n.attribution} {n.notice} ({n.decision}; not a licence from the source.)
          </p>
        ))}
      </div>
    </footer>
  );
}
