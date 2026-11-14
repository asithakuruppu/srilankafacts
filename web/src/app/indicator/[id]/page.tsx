import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import MapView from "@/components/map-view";
import { UNMATCHED_DCS_GN } from "@/lib/coverage";
import { formatNumber, formatValue, levelLabel } from "@/lib/format";
import { groupIndicators } from "@/lib/indicator-groups";
import {
  getGeographyIndex,
  getIndicator,
  getIndicatorLevel,
  getIndicators,
  getNationalValues,
  geographyLabel,
} from "@/lib/release";

export function generateStaticParams() {
  return getIndicators().map((indicator) => ({ id: indicator.id }));
}

export async function generateMetadata({
  params,
}: PageProps<"/indicator/[id]">): Promise<Metadata> {
  const { id } = await params;
  const indicator = getIndicator(id);
  if (!indicator) {
    return { title: "Indicator not found" };
  }
  return {
    title: indicator.name,
    description: `${indicator.definition} Census Atlas 2024 private preview.`,
    alternates: { canonical: `/indicator/${indicator.id}` },
    openGraph: { title: `${indicator.name} · Sri Lanka Facts` },
  };
}

// Read params at the top, not inside <Suspense>: Suspense would stream the content into a hidden
// block that needs JavaScript to show (D-027: pages must read without JavaScript). The route may
// therefore block on navigation, which instant = false allows.
export const instant = false;

export default async function IndicatorPage({ params }: PageProps<"/indicator/[id]">) {
  const { id } = await params;
  const indicator = getIndicator(id);
  if (!indicator) {
    notFound();
  }
  const districts = getIndicatorLevel(indicator.id, "district");
  const national = getNationalValues();
  const index = getGeographyIndex();
  const nationalValue = national.get(indicator.id) ?? null;
  const rows = (districts?.values ?? [])
    .filter((row) => row.value !== null)
    .map((row) => ({
      ...row,
      name: geographyLabel(index.get(row.geography_id)),
    }))
    .sort((a, b) => (b.value ?? 0) - (a.value ?? 0));
  const max = rows[0]?.value ?? 0;
  const min = rows.at(-1)?.value ?? 0;
  // Same reader-facing group only; the home page lists every group.
  const group = groupIndicators(getIndicators()).find((g) =>
    g.indicators.some((item) => item.id === indicator.id),
  );
  const related = (group?.indicators ?? []).filter((item) => item.id !== indicator.id);
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Dataset",
    name: `${indicator.name}, Census of Population and Housing 2024`,
    description: indicator.definition,
    creator: {
      "@type": "Organization",
      name: "Department of Census and Statistics, Sri Lanka",
      url: "https://www.statistics.gov.lk/",
    },
    spatialCoverage: { "@type": "Country", name: "Sri Lanka" },
    temporalCoverage: "2024-12-19",
    variableMeasured: indicator.name,
    isAccessibleForFree: false,
  };

  return (
    <article className="shell section indicator-page">
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link href="/indicators">Indicators</Link>
        <span aria-hidden="true"> / </span>
        <span aria-current="page">{indicator.name}</span>
      </nav>

      <header className="place-head">
        <p className="eyebrow">Indicator · {indicator.measure_type}</p>
        <h1>{indicator.name}</h1>
        <p className="lede">{indicator.definition}</p>
        <p className="muted">
          Unit: <strong>{indicator.unit}</strong> · Reference date: 19 December 2024 ·
          Geography: GN divisions, aggregated to DS, district, province and country
        </p>
      </header>

      <section className="stat-grid" aria-label="National value">
        <div className="stat stat-wide">
          <span className="stat-label">Sri Lanka</span>
          <span className="stat-value">
            {formatValue(nationalValue, indicator.unit, indicator.decimals)}
          </span>
          <span className="stat-note">
            computed from the {indicator.value_count.toLocaleString("en-LK")} published
            place values
          </span>
        </div>
        <div className="stat">
          <span className="stat-label">Districts covered</span>
          <span className="stat-value">{formatNumber(rows.length)}</span>
          <span className="stat-note">of 25</span>
        </div>
        <div className="stat">
          <span className="stat-label">National range</span>
          <span className="stat-value">
            {formatValue(min, indicator.unit, indicator.decimals)} –{" "}
            {formatValue(max, indicator.unit, indicator.decimals)}
          </span>
          <span className="stat-note">lowest to highest district</span>
        </div>
      </section>

      <section className="section section-tight" aria-labelledby="indicator-map">
        <div className="section-head">
          <div>
            <p className="eyebrow">Across the country</p>
            <h2 id="indicator-map">By district</h2>
          </div>
          <p className="section-note">
            Switch to DS or GN in <Link href={`/explore?indicator=${indicator.id}`}>Explore</Link>.
            Colours are quantile classes; no value is hidden by the map.
          </p>
        </div>
        <MapView
          indicatorId={indicator.id}
          levelName="district"
          boundaryLevel={2}
          unit={indicator.unit}
          decimals={indicator.decimals}
          nationalValue={nationalValue}
        />
      </section>

      <div className="place-grid">
        <section className="panel" aria-labelledby="distribution-heading">
          <h2 id="distribution-heading">District distribution</h2>
          <p className="muted small">
            Ranked from highest to lowest. A longer bar means a larger value, not a better
            place.
          </p>
          <div className="rank-bars">
            {rows.map((row) => (
              <div className="rank-row" key={row.geography_id}>
                <Link href={`/place/${row.geography_id}`} className="rank-name">
                  {row.name}
                </Link>
                <span className="rank-track">
                  <span
                    className="rank-fill"
                    style={{ width: `${max > 0 ? (100 * (row.value ?? 0)) / max : 0}%` }}
                  />
                </span>
                <span className="rank-value">
                  {formatValue(row.value, indicator.unit, indicator.decimals)}
                </span>
              </div>
            ))}
          </div>
          <details className="table-details">
            <summary>Show as table</summary>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th scope="col">District</th>
                    <th scope="col">Value</th>
                    <th scope="col">National</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => (
                    <tr key={row.geography_id}>
                      <th scope="row">
                        <Link href={`/place/${row.geography_id}`}>{row.name}</Link>
                      </th>
                      <td className="numeric">
                        {formatValue(row.value, indicator.unit, indicator.decimals)}
                      </td>
                      <td className="numeric">
                        {formatValue(nationalValue, indicator.unit, indicator.decimals)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </section>

        <aside className="panel">
          <h2>Reading this indicator</h2>
          <ul className="notes-list">
            <li>
              <strong>Source definition.</strong>{" "}
              {indicator.definition}
            </li>
            <li>
              <strong>Aggregation.</strong>{" "}
              {indicator.measure_type === "count"
                ? `Counts are summed from GN rows, including ${UNMATCHED_DCS_GN} unmatched DCS GNs that have no GN-level row.`
                : "Rates and shares are recomputed from summed counts, never averaged from GN rates."}
            </li>
            <li>
              <strong>Small places.</strong> A rate in a place with a small denominator can
              move a lot for a handful of people. The release carries a small-denominator
              flag and empirical-Bayes smoothed values, stored separately from the published
              values.
            </li>
            <li>
              <strong>Not causal.</strong> Spatial clusters describe where similar values sit
              together. They do not explain why, and they are sensitive to how boundaries are
              drawn.
            </li>
          </ul>
          <p className="small">
            <Link href="/methods">Methods, MAUP and the ecological fallacy</Link>
          </p>
        </aside>
      </div>

      <section className="section" aria-labelledby="related-heading">
        <div className="section-head">
          <div>
            <p className="eyebrow">Related</p>
            <h2 id="related-heading">
              {group && group.label !== "Other" ? `More in ${group.label}` : "Other indicators"}
            </h2>
          </div>
          <p className="section-note">
            <Link href="/#indicators">All indicators</Link>
          </p>
        </div>
        <div className="indicator-grid">
          {related.map((item) => (
            <Link key={item.id} className="indicator-card" href={`/indicator/${item.id}`}>
              <span className="indicator-name">{item.name}</span>
              <span className="indicator-meta">
                {item.unit} · {levelLabel(item.levels.includes("gn") ? "gn" : "district")}
              </span>
            </Link>
          ))}
        </div>
      </section>

      <section className="section citation-block">
        <h2>How to cite and download</h2>
        <p>
          Cite the census table for the number and this page for the derived presentation.
          The static API file for this indicator is{" "}
          <code>/api/v1/indicators/{indicator.id}.json</code>; district values are at{" "}
          <code>/api/v1/indicators/{indicator.id}/district.json</code>.
        </p>
        <p>
          <Link href="/data">Release contents, checksums and citation</Link>
        </p>
      </section>

      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
    </article>
  );
}
