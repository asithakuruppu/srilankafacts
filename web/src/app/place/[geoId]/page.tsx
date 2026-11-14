import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";

import IdentityPanel, { IDENTITY_INDICATORS } from "@/components/identity-panel";
import MapView from "@/components/map-view";
import ProfilePanel from "@/components/profile-panel";
import Provenance from "@/components/provenance";
import SourcesPanel from "@/components/sources-panel";
import StatTile from "@/components/stat-tile";
import { formatDelta, formatNumber, formatValue, levelLabel } from "@/lib/format";
import {
  getBreadcrumb,
  getChildren,
  getGeographies,
  getGeography,
  getIndicators,
  getLatest,
  getNationalValues,
  getPlace,
  geographyLabel,
  placeValue,
} from "@/lib/release";
import type { Place } from "@/lib/types";

const HEADLINE_ORDER = [
  "population_total",
  "population_male",
  "population_female",
  "sex_ratio",
  "population_age_0_14",
  "population_age_15_59",
  "population_age_60_64",
  "population_age_65_plus",
  "population_age_60_plus",
  "population_age_0_14_share",
  "population_age_60_plus_share",
  "occupied_housing_units",
  "persons_per_occupied_housing_unit",
  "population_density",
];

export function generateStaticParams() {
  return getGeographies()
    .filter((geo) => geo.level <= 3)
    .map((geo) => ({ geoId: geo.geography_id }));
}

export async function generateMetadata({
  params,
}: PageProps<"/place/[geoId]">): Promise<Metadata> {
  const { geoId } = await params;
  const place = getPlace(geoId);
  if (!place) {
    return { title: "Place not found" };
  }
  const geography = place.geography;
  const parent = geography.parent_id ? getGeography(geography.parent_id) : null;
  const description = `${geographyLabel(geography)}${
    parent ? `, ${geographyLabel(parent)}` : ""
  } in the Sri Lanka Facts Census Atlas 2024 preview: population, age structure, housing and density, each with its source.`;
  return {
    title: `${geographyLabel(geography)} (${levelLabel(geography.level_name)})`,
    description,
    alternates: { canonical: `/place/${geography.geography_id}` },
    robots: { index: geography.level_name !== "gn", follow: true },
    openGraph: { title: `${geographyLabel(geography)} · Sri Lanka Facts`, description },
  };
}

export default function PlacePage({ params }: PageProps<"/place/[geoId]">) {
  return (
    <Suspense fallback={<PlaceSkeleton />}>
      {params.then(({ geoId }) => (
        <PlaceContent geoId={geoId} />
      ))}
    </Suspense>
  );
}

function PlaceSkeleton() {
  return (
    <div className="shell section place-skeleton" aria-busy="true">
      <p className="muted">Loading place…</p>
    </div>
  );
}

function PlaceContent({ geoId }: { geoId: string }) {
  const place = getPlace(geoId);
  if (!place) {
    notFound();
  }
  const geography = place.geography;
  const indicators = getIndicators();
  const indicatorById = new Map(indicators.map((indicator) => [indicator.id, indicator]));
  const breadcrumb = getBreadcrumb(geography.geography_id);
  const parent = geography.parent_id ? getPlace(geography.parent_id) : null;
  const nationalValues = getNationalValues();
  const children = getChildren(geography.geography_id);
  const latest = getLatest();
  // Ethnic group and religion have their own section (D-033), not the indicator table.
  const values = place.values.filter((value) => !IDENTITY_INDICATORS.has(value.indicator_id));
  values.sort((a, b) => {
    const left = HEADLINE_ORDER.indexOf(a.indicator_id);
    const right = HEADLINE_ORDER.indexOf(b.indicator_id);
    return (left === -1 ? 99 : left) - (right === -1 ? 99 : right);
  });
  const ageGroups = [
    { id: "population_age_0_14", label: "0–14" },
    { id: "population_age_15_59", label: "15–59" },
    { id: "population_age_60_64", label: "60–64" },
    { id: "population_age_65_plus", label: "65+" },
  ];
  const total = placeValue(place, "population_total");
  const male = placeValue(place, "population_male");
  const female = placeValue(place, "population_female");
  const mapLevel =
    geography.level === 0
      ? { levelName: "district", boundaryLevel: 2, selectedId: undefined }
      : geography.level <= 3
        ? {
            levelName: geography.level_name,
            boundaryLevel: geography.level,
            selectedId: geography.geography_id,
          }
        : null;

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "Place",
    name: geographyLabel(geography),
    identifier: geography.geography_id,
    containedInPlace: parent
      ? { "@type": "Place", name: geographyLabel(parent.geography) }
      : { "@type": "Country", name: "Sri Lanka" },
    additionalProperty: [
      {
        "@type": "PropertyValue",
        name: "Total population (Census 2024)",
        value: total,
        unitText: "persons",
      },
    ],
  };

  return (
    <article className="place">
      <div className="shell">
        <nav className="breadcrumb" aria-label="Breadcrumb">
          {breadcrumb.map((item, index) => (
            <span key={item.geography_id}>
              {index > 0 ? <span aria-hidden="true"> / </span> : null}
              {index === breadcrumb.length - 1 ? (
                <span aria-current="page">{geographyLabel(item)}</span>
              ) : (
                <Link href={`/place/${item.geography_id}`}>{geographyLabel(item)}</Link>
              )}
            </span>
          ))}
        </nav>

        <header className="place-head">
          <p className="eyebrow">
            {levelLabel(geography.level_name)}
            {parent ? ` · ${geographyLabel(parent.geography)}` : ""}
          </p>
          <h1>
            {geographyLabel(geography)}
            {geography.name_si ? (
              <span className="script-si" lang="si">{geography.name_si}</span>
            ) : null}
            {geography.name_ta ? (
              <span className="script-ta" lang="ta">{geography.name_ta}</span>
            ) : null}
          </h1>
          <p className="lede">
            {total !== null
              ? `${formatNumber(total)} people were enumerated here on 19 December 2024.`
              : "No population count is available for this place in the held workbooks."}{" "}
            Every number below opens to its workbook row, snapshot and claim.
          </p>
          {place.source_comparisons?.some((item) => !item.agree) ? (
            <p>
              <a className="tag" href="#sources">
                Sources disagree
              </a>{" "}
              <span className="muted small">
                on:{" "}
                {place.source_comparisons
                  .filter((item) => !item.agree)
                  .map((item) => item.label)
                  .join(", ")}
              </span>
            </p>
          ) : null}
        </header>

        <section className="stat-grid" aria-label="Key numbers">
          <StatTile
            label="Population"
            value={formatValue(total, "persons")}
            note={`Rank ${rank(place, "population_total")}`}
            href="#data"
          />
          <StatTile
            label="Population density"
            value={formatValue(placeValue(place, "population_density"), "persons per km2")}
            note="people per km² of land"
            href="#data"
          />
          <StatTile
            label="Aged 60 and over"
            value={formatValue(
              placeValue(place, "population_age_60_plus_share"),
              "percent",
            )}
            note={formatValue(placeValue(place, "population_age_60_plus"), "persons")}
            href="#data"
          />
          <StatTile
            label="Occupied housing units"
            value={formatValue(placeValue(place, "occupied_housing_units"), "housing_units")}
            note="census count"
            href="#data"
          />
          <StatTile
            label="Persons per occupied unit"
            value={formatValue(
              placeValue(place, "persons_per_occupied_housing_unit"),
              "persons per housing unit",
            )}
            note="not household size"
            href="#data"
          />
          <StatTile
            label="Sex ratio"
            value={formatValue(placeValue(place, "sex_ratio"), "males per 100 females")}
            note="100 × male ÷ female"
            href="#data"
          />
        </section>

        <div className="place-grid">
          <section className="panel" aria-labelledby="age-heading">
            <h2 id="age-heading">Age structure</h2>
            <p className="muted small">
              The held workbook gives age groups and sex separately. It does not give a
              sex-by-age cross-tabulation, so no population pyramid is shown.
            </p>
            <div className="bars">
              {ageGroups.map((group) => {
                const value = placeValue(place, group.id);
                const share =
                  value !== null && total ? (100 * value) / total : null;
                return (
                  <div className="bar-row" key={group.id}>
                    <span className="bar-label">{group.label}</span>
                    <span className="bar-track">
                      <span
                        className="bar-fill"
                        style={{ width: `${Math.min(share ?? 0, 100)}%` }}
                      />
                    </span>
                    <span className="bar-value">
                      {formatNumber(value ?? 0)}
                      <small>{share === null ? "" : `${share.toFixed(1)}%`}</small>
                    </span>
                  </div>
                );
              })}
            </div>
            <h3>Sex</h3>
            <div className="sex-bar" aria-label="Population by sex">
              {male !== null && female !== null && total ? (
                <>
                  <span
                    className="sex-male"
                    style={{ width: `${(100 * male) / total}%` }}
                    title={`Male ${formatNumber(male)}`}
                  />
                  <span
                    className="sex-female"
                    style={{ width: `${100 - (100 * male) / total}%` }}
                    title={`Female ${formatNumber(female)}`}
                  />
                </>
              ) : null}
            </div>
            <div className="sex-labels">
              <span>Male {formatValue(male, "persons")}</span>
              <span>Female {formatValue(female, "persons")}</span>
            </div>
          </section>

          <section className="panel" aria-labelledby="compare-heading">
            <h2 id="compare-heading">Compared with</h2>
            <p className="muted small">
              Parent and national values are recomputed from GN counts, never averaged from
              child rates.
            </p>
            <table className="compare-table">
              <thead>
                <tr>
                  <th scope="col">Indicator</th>
                  <th scope="col">Here</th>
                  <th scope="col">{parent ? geographyLabel(parent.geography) : "Sri Lanka"}</th>
                  <th scope="col">Sri Lanka</th>
                </tr>
              </thead>
              <tbody>
                {[
                  "population_total",
                  "population_density",
                  "population_age_60_plus_share",
                  "persons_per_occupied_housing_unit",
                ].map((id) => {
                  const indicator = indicatorById.get(id);
                  const value = placeValue(place, id);
                  const parentValue = parent ? placeValue(parent, id) : null;
                  const nationalValue = nationalValues.get(id) ?? null;
                  return (
                    <tr key={id}>
                      <th scope="row">{indicator?.short_name ?? id}</th>
                      <td className="numeric">
                        {formatValue(value, indicator?.unit ?? "")}
                        {value !== null &&
                        nationalValue !== null &&
                        indicator?.measure_type !== "count" ? (
                          <small className="delta">
                            {formatDelta(value, indicator?.unit ?? "", nationalValue)}
                          </small>
                        ) : null}
                      </td>
                      <td className="numeric">
                        {formatValue(parentValue, indicator?.unit ?? "")}
                      </td>
                      <td className="numeric">
                        {formatValue(nationalValue, indicator?.unit ?? "")}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <p className="muted small">
              Need the full method? Read{" "}
              <Link href="/methods">methods and limits</Link>.
            </p>
          </section>
        </div>

        {mapLevel ? (
          <section className="section section-tight" aria-labelledby="map-heading">
            <div className="section-head">
              <div>
                <p className="eyebrow">Where it is</p>
                <h2 id="map-heading">{geographyLabel(geography)} in {levelLabel(mapLevel.levelName)} context</h2>
              </div>
              <p className="section-note">
                The map shows population totals at this level and outlines the selected area.
                It is an enhancement; the table below is complete without it.
              </p>
            </div>
            <MapView
              indicatorId="population_total"
              levelName={mapLevel.levelName}
              boundaryLevel={mapLevel.boundaryLevel}
              unit="persons"
              selectedId={mapLevel.selectedId}
              nationalValue={nationalValues.get("population_total") ?? null}
            />
          </section>
        ) : (
          <section className="section section-tight">
            <p className="notice">
              GN pages carry a lighter template. For a map of this area, open its parent DS
              division or use <Link href="/explore">Explore</Link>.
            </p>
          </section>
        )}

        {place.profile ? (
          <ProfilePanel
            profile={place.profile}
            indicatorNames={
              new Map(
                indicators.map((indicator) => [indicator.id, indicator.short_name ?? indicator.id]),
              )
            }
            parentLabel={parent ? geographyLabel(parent.geography) : null}
          />
        ) : null}

        {place.source_comparisons && place.source_comparisons.length > 0 ? (
          <SourcesPanel comparisons={place.source_comparisons} />
        ) : null}

        <IdentityPanel place={place} />

        <section className="section" id="data" aria-labelledby="data-heading">
          <div className="section-head">
            <div>
              <p className="eyebrow">The record</p>
              <h2 id="data-heading">All indicators for {geographyLabel(geography)}</h2>
            </div>
            <p className="section-note">
              Values are Census 2024 counts or values derived from them. Open “Source” for the
              workbook, row, snapshot and verification tag.
            </p>
          </div>
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th scope="col">Indicator</th>
                  <th scope="col">Value</th>
                  <th scope="col">Unit</th>
                  <th scope="col">National</th>
                  <th scope="col">Source</th>
                </tr>
              </thead>
              <tbody>
                {values.map((observation) => {
                  const indicator = indicatorById.get(observation.indicator_id);
                  return (
                    <tr key={observation.indicator_id}>
                      <th scope="row">
                        <Link href={`/indicator/${observation.indicator_id}`}>
                          {indicator?.name ?? observation.indicator_id}
                        </Link>
                        {observation.value_status !== "normal" ? (
                          <span className="tag">{observation.value_status.replaceAll("_", " ")}</span>
                        ) : null}
                      </th>
                      <td className="numeric">
                        {formatValue(
                          observation.value,
                          observation.unit,
                          indicator?.decimals,
                        )}
                      </td>
                      <td>{observation.unit}</td>
                      <td className="numeric">
                        {formatValue(
                          nationalValues.get(observation.indicator_id) ?? null,
                          observation.unit,
                          indicator?.decimals,
                        )}
                      </td>
                      <td>
                        <Provenance value={observation} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>

        {children.length > 0 ? (
          <section className="section" aria-labelledby="children-heading">
            <div className="section-head">
              <div>
                <p className="eyebrow">Inside</p>
                <h2 id="children-heading">
                  {children.length} {levelLabel(children[0].level_name).toLowerCase()}
                  {children.length === 1 ? "" : "s"}
                </h2>
              </div>
              <p className="section-note">
                Child values are their own records, not shares of this parent.
              </p>
            </div>
            <div className="child-grid">
              {children.map((child) => {
                const childPlace = getPlace(child.geography_id);
                return (
                  <Link key={child.geography_id} href={`/place/${child.geography_id}`}>
                    <span>{geographyLabel(child)}</span>
                    <strong>
                      {formatValue(placeValue(childPlace, "population_total"), "persons")}
                    </strong>
                  </Link>
                );
              })}
            </div>
          </section>
        ) : null}

        <section className="section citation-block" aria-labelledby="cite-heading">
          <h2 id="cite-heading">How to cite</h2>
          <p>
            Department of Census and Statistics, <em>Census of Population and Housing 2024</em>
            , GN population by sex and age group and occupied housing units. Sri Lanka Facts
            release <code>{latest.release}</code>, dataset{" "}
            <code>census-2024-gnd-tables</code>, place{" "}
            <code>{geography.geography_id}</code>.
          </p>
          <p className="muted small">
            This is not an official DCS publication. Cite the underlying census table for any
            figure, and state the access date you used.{" "}
            {latest.publishable
              ? "Non-commercial use only (decision D-030): DCS has published no reuse terms."
              : "This private preview is marked publishable: false."}
          </p>
          <p>
            <Link href="/data">Downloads and static API</Link> ·{" "}
            <Link href="/methods">Methods and known gaps</Link>
          </p>
        </section>
      </div>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
    </article>
  );
}

function rank(place: Place, indicatorId: string): string {
  const value = placeValue(place, indicatorId);
  if (value === null) {
    return "not available";
  }
  const siblings =
    place.geography.parent_id === null
      ? []
      : getChildren(place.geography.parent_id).filter((child) => child.level === place.geography.level);
  if (siblings.length === 0) {
    return "national total";
  }
  const values = siblings
    .map((child) => placeValue(getPlace(child.geography_id), indicatorId))
    .filter((item): item is number => item !== null)
    .sort((a, b) => b - a);
  const position = values.indexOf(value) + 1;
  return `${position} of ${values.length} in parent`;
}
