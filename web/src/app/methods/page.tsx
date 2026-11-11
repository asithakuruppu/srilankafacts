import type { Metadata } from "next";
import Link from "next/link";

import { getLatest, getPlace, placeValue } from "@/lib/release";

export const metadata: Metadata = {
  title: "Methods and known gaps",
  description:
    "How the Census Atlas 2024 preview is built, what was checked, and what it does not claim.",
  alternates: { canonical: "/methods" },
};

export default function MethodsPage() {
  const latest = getLatest();
  const country = getPlace("LK");
  const population = placeValue(country, "population_total");

  return (
    <div className="shell section methods">
      <header className="place-head">
        <p className="eyebrow">Methods</p>
        <h1>How this atlas is built — and what it does not claim</h1>
        <p className="lede">
          This page explains the first Census Atlas dataset in plain language. The full
          methodology is in <code>docs/methods/census-2024.md</code>; the spatial-context note
          is in <code>docs/methods/spatial-context.md</code>.
        </p>
      </header>

      <div className="method-grid">
        <section>
          <h2>1. Source and scope</h2>
          <p>
            The only census values in this release come from two workbooks published by the
            Department of Census and Statistics (DCS) for the Census of Population and Housing
            2024: GN population by sex and age group, and occupied housing units. Both are
            held as immutable raw snapshots.
          </p>
          <p>
            The release does <strong>not</strong> contain the other census topics — education,
            employment, housing amenities, water, sanitation, cooking fuel and so on. They are
            not shown as empty charts, and no placeholder values exist.
          </p>
          <p className="muted small">
            Source page:{" "}
            <a href="https://www.statistics.gov.lk/Population/StaticalInformation/CPH2024">
              statistics.gov.lk · CPH 2024
            </a>
            . Reference date: 19 December 2024.
          </p>
        </section>

        <section>
          <h2>2. Geography joins</h2>
          <p>
            DCS GN codes are joined to the geography spine only through the recorded crosswalk{" "}
            <code>catalog/geographies/codes/dcs-census2024.csv</code>. Nothing is joined by
            name. The spine uses OCHA p-codes for admin units.
          </p>
          <ul>
            <li>
              14,008 DCS GN rows. 13,945 match a current COD-AB v03 GN division; 63 unmatched
              GNs enter their DS, district, province and country totals but have no GN-level
              row.
            </li>
            <li>
              98 spine GNs have no DCS row in the two workbooks and are marked{" "}
              <code>no_data</code>;
            </li>
            <li>
              DCS DS 5224 Kalmunai has no spine equivalent (decision D-022). Its 52,798 people
              enter the Ampara district total, but no DS-level row is published for it.
            </li>
            <li>
              DCS DS 5221 maps to the provisional unit <code>LK-ADM3-P0001</code>. It has no
              neighbours in the contiguity graph, so its spatial context is{" "}
              <code>no_neighbours</code> rather than an invented list.
            </li>
          </ul>
        </section>

        <section>
          <h2>3. Counts, rates and aggregation</h2>
          <p>
            Counts are integers copied from the workbooks. Derived shares and ratios are
            computed from those counts:
          </p>
          <ul>
            <li>sex ratio = 100 × male ÷ female;</li>
            <li>age shares = 100 × age group ÷ total population;</li>
            <li>persons per occupied unit = population ÷ occupied housing units;</li>
            <li>density = population ÷ land area, with area computed in EPSG:5235.</li>
          </ul>
          <p>
            DS, district, province and country counts are sums of GN rows, including the 63
            unmatched GNs. Rates are recomputed from the summed components, never averaged from
            GN rates. A zero denominator yields <code>not_available</code>, never zero.
          </p>
          <p className="muted small">
            National population in this release: {population?.toLocaleString("en-LK")}. The
            national anchors and all 25 district anchors match the DCS final report.
          </p>
        </section>

        <section>
          <h2>4. Spatial context</h2>
          <p>
            For every indicator and level the release computes neighbour median, minimum,
            maximum and mean, a spatial lag, parent and national values, a rank, and a local
            Moran’s I class. Local Moran uses the spine contiguity graph, 999 conditional
            permutations, a fixed seed (20241108) and Benjamini–Hochberg false-discovery-rate
            control at 0.05. The four classes are high–high, low–low, high–low and low–high.
          </p>
          <p>
            A class is a description of spatial association, not a cause and not a score.
            Counts cluster partly because settlements are large. Rates in small places are
            unstable; the release flags denominators below 100 (a provisional threshold) and
            stores empirical-Bayes smoothed values separately, labelled{" "}
            <code>modelled_estimate</code>. Published values are never replaced by smoothed
            values.
          </p>
        </section>

        <section>
          <h2>5. Two traps: MAUP and the ecological fallacy</h2>
          <p>
            <strong>The modifiable areal unit problem (MAUP).</strong> A pattern can change when
            the same people are grouped into different boundaries. A GN division is not a
            neighbourhood, and a DS division is not a community. Comparisons across levels are
            comparisons of different units, not of the same population.
          </p>
          <p>
            <strong>The ecological fallacy.</strong> A rate for an area does not describe every
            person in it. A district with a high share of older residents is not evidence that
            any particular person is older. Aggregates only: this release never attributes a
            statistic to a building, a household or a named person.
          </p>
        </section>

        <section>
          <h2>6. What was checked</h2>
          <ul>
            <li>National anchors for population, sex, age groups and housing units.</li>
            <li>All 25 district population and housing anchors against DCS final-report tables.</li>
            <li>Total = male + female and age components = total for all 14,008 GN rows.</li>
            <li>
              An independent comparison against <code>nuuuwan/lk_census_2024</code> for total,
              male and female: 0 mismatches across 14,008 GNs. The comparison is not an
              authority and supplies no published value.
            </li>
            <li>Two release builds produced identical checksums.</li>
          </ul>
        </section>

        <section>
          <h2>7. What was not checked</h2>
          <ul>
            <li>
              No human has spot-checked GN cells against the workbook. Every value remains{" "}
              <code>machine_extracted</code>.
            </li>
            <li>
              The lead looked at the boundaries in QGIS on 2026-11-12 and reported nothing to
              correct; which checks were covered is not recorded.
            </li>
            <li>
              Unmatched DCS GNs (listed in the release QA report) and DS 5224 are unresolved.
            </li>
            <li>
              DCS rights are unclear. The release is{" "}
              <code>{latest.publishable ? "public, non-commercial (D-030)" : "publishable: false"}</code>.
            </li>
            <li>
              No basemap is shown: the preview has no PMTiles build, so boundaries are drawn on
              a plain background. That is a deliberate, recorded deviation, not a finished map.
            </li>
            <li>
              Sinhala and Tamil place names come from COD-AB and are displayed, but the
              interface is English-only until reviewed translations exist.
            </li>
          </ul>
        </section>
      </div>

      <section className="section citation-block">
        <h2>Verification tags used in reports</h2>
        <p>
          ✅ verified by running or reading the source · 🟡 claimed by a source, not
          independently checked · ❌ not found or failed · ❓ assumption. The release QA files
          are <code>qa/summary.md</code> and <code>qa/spatial-context.md</code>.
        </p>
        <p>
          <Link href="/data">Release contents</Link> ·{" "}
          <Link href="/explore">Explore the map</Link>
        </p>
      </section>
    </div>
  );
}
