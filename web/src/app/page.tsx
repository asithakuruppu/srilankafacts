import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import Atlas from "@/components/atlas/atlas";
import MapView from "@/components/map-view";
import type { AtlasIndicator, AtlasMeta } from "@/lib/atlas/types";
import { formatValue } from "@/lib/format";
import { groupIndicators } from "@/lib/indicator-groups";
import {
  getAtlasMeta,
  getChildren,
  getIndicators,
  getLatest,
  getObservationFor,
  getPlace,
  placeValue,
} from "@/lib/release";

import "./atlas.css";

export const metadata: Metadata = {
  title: "Sri Lanka Facts",
  description:
    "Every place in Sri Lanka, every number about it, with its source. A map-first atlas of the Census 2024; private preview.",
  alternates: { canonical: "/" },
};

/** Readable without JavaScript or WebGL (D-002): the national figures and the way in. */
function Summary({ withMap }: { withMap: boolean }) {
  const country = getPlace("LK");
  const observation = country ? getObservationFor(country, "population_total") : null;
  return (
    <section className="atlas-summary shell">
      <p className="eyebrow">Census Atlas 2024 · private preview</p>
      <h1>Every place in Sri Lanka, every number about it, with its source.</h1>
      <p className="hero-number">{formatValue(placeValue(country, "population_total"), "persons")}</p>
      <p className="muted">persons enumerated on 19 December 2024</p>
      {observation ? (
        <p className="source-line">
          {observation.dataset_id} · sha256 {observation.snapshot_sha256.slice(0, 8)} ·{" "}
          {observation.source_locator}
        </p>
      ) : null}
      {withMap ? (
        <MapView
          indicatorId="population_total"
          levelName="district"
          boundaryLevel={2}
          unit="persons"
          className="home-map"
        />
      ) : null}
      <ul className="atlas-summary-links">
        {getChildren("LK").map((province) => (
          <li key={province.geography_id}>
            <Link href={`/place/${province.geography_id}`}>{province.name_en}</Link>
          </li>
        ))}
      </ul>
      <p>
        <Link href="/explore">Tables for every indicator and level</Link> ·{" "}
        <Link href="/about">About this preview</Link>
      </p>
    </section>
  );
}

export default function HomePage() {
  const latest = getLatest();
  const meta: AtlasMeta | null = getAtlasMeta();
  if (!meta) {
    // No atlas bundle for this release (for example the CI fixture): the plain boundary map.
    return (
      <>
        <Summary withMap />
        <p className="shell muted small">
          The map-first atlas needs the atlas bundle for release <code>{latest.release}</code>.
          Build it with <code>uv run slf atlas export</code> in <code>pipeline/</code>.
        </p>
      </>
    );
  }
  const indicators: AtlasIndicator[] = groupIndicators(getIndicators()).flatMap((group) =>
    group.indicators.map((indicator) => ({
      id: indicator.id,
      name: indicator.name,
      short: indicator.short_name ?? indicator.name,
      unit: indicator.unit,
      decimals: indicator.decimals,
      measureType: indicator.measure_type,
      higherIs: indicator.higher_is,
      definition: indicator.definition,
      levels: indicator.levels.map((level) => (level === "ds-provisional" ? "ds" : level)),
      group: group.label,
    })),
  );
  return (
    <>
      <h1 className="visually-hidden">Sri Lanka Facts: the atlas</h1>
      <Suspense fallback={<Summary withMap={false} />}>
        <Atlas indicators={indicators} meta={meta} release={latest.release} />
      </Suspense>
      <noscript>
        <Summary withMap={false} />
      </noscript>
    </>
  );
}
