import type { Metadata } from "next";
import Link from "next/link";

import MapView from "@/components/map-view";
import { formatNumber, formatValue } from "@/lib/format";
import {
  getChildren,
  getGeographyIndex,
  getIndicators,
  getLatest,
  getPlace,
  placeValue,
} from "@/lib/release";

export const metadata: Metadata = {
  title: "Sri Lanka Facts",
  description:
    "Every place in Sri Lanka, every number about it, with its source. Census Atlas 2024 private preview.",
  alternates: { canonical: "/" },
};

export default function HomePage() {
  const latest = getLatest();
  const country = getPlace("LK");
  const indicators = getIndicators();
  const provinces = getChildren("LK");
  const index = getGeographyIndex();

  return (
    <>
      <section className="hero">
        <div className="shell hero-grid">
          <div className="hero-copy">
            <p className="eyebrow">Census Atlas 2024 · private preview</p>
            <h1>Every place in Sri Lanka, every number about it, with its source.</h1>
            <p className="lede">
              A place-based atlas built on a geography spine. Start with the country, move
              down through provinces, districts and DS divisions to GN divisions, and open any
              number to see the workbook, row and snapshot it came from.
            </p>
            <div className="button-row">
              <Link className="button" href="/explore">
                Explore the map
              </Link>
              <Link className="button button-quiet" href="/data">
                Data and API
              </Link>
            </div>
            <p className="hero-note">
              This is a review build. The Department of Census and Statistics’ reuse terms
              are unresolved, so nothing here is published or citable as final.
            </p>
          </div>
          <div className="hero-panel">
            <p className="panel-kicker">Sri Lanka · Census 2024</p>
            <p className="hero-number">
              {formatValue(placeValue(country, "population_total"), "persons")}
            </p>
            <p className="muted">persons enumerated on 19 December 2024</p>
            <dl className="hero-facts">
              <div>
                <dt>Occupied housing units</dt>
                <dd>
                  {formatValue(
                    placeValue(country, "occupied_housing_units"),
                    "housing_units",
                  )}
                </dd>
              </div>
              <div>
                <dt>Persons per occupied unit</dt>
                <dd>
                  {formatValue(
                    placeValue(country, "persons_per_occupied_housing_unit"),
                    "persons per housing unit",
                  )}
                </dd>
              </div>
              <div>
                <dt>Population density</dt>
                <dd>
                  {formatValue(
                    placeValue(country, "population_density"),
                    "persons per km2",
                  )}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </section>

      <section className="section shell">
        <div className="section-head">
          <div>
            <p className="eyebrow">The map</p>
            <h2>Population by district</h2>
          </div>
          <p className="section-note">
            The map is an enhancement. Every value is also in the tables and on each place
            page. Colours are quantile classes, not a judgement about places.
          </p>
        </div>
        <MapView
          indicatorId="population_total"
          levelName="district"
          boundaryLevel={2}
          unit="persons"
          className="home-map"
        />
        <div className="province-strip">
          {provinces.map((province) => {
            const place = getPlace(province.geography_id);
            return (
              <Link key={province.geography_id} href={`/place/${province.geography_id}`}>
                <span>{province.name_en}</span>
                <strong>
                  {formatValue(placeValue(place, "population_total"), "persons")}
                </strong>
              </Link>
            );
          })}
        </div>
      </section>

      <section className="section shell" id="indicators">
        <div className="section-head">
          <div>
            <p className="eyebrow">What is measured</p>
            <h2>{indicators.length} indicators in this preview</h2>
          </div>
          <p className="section-note">
            From DCS Census 2024 workbooks and tables: population by sex and age, occupied
            housing units, households and their amenities, age group, sector and local authority
            type, and, for DS divisions and larger areas, housing structure and materials. Shares
            and ratios are computed from the published counts, never copied. Ethnic group and
            religion appear only on place pages, never ranked or mapped.
          </p>
        </div>
        <div className="indicator-grid">
          {indicators.map((indicator) => (
            <Link
              key={indicator.id}
              className="indicator-card"
              href={`/indicator/${indicator.id}`}
            >
              <span className="indicator-name">{indicator.name}</span>
              <span className="indicator-meta">
                {indicator.unit} · {indicator.measure_type}
              </span>
            </Link>
          ))}
        </div>
      </section>

      <section className="section shell">
        <div className="section-head">
          <div>
            <p className="eyebrow">Levels</p>
            <h2>From the country to the GN division</h2>
          </div>
        </div>
        <div className="level-grid">
          {[
            { level: 0, label: "Country", count: 1, href: "/place/LK" },
            {
              level: 1,
              label: "Provinces",
              count: 9,
              href: "/place/LK1",
            },
            {
              level: 2,
              label: "Districts",
              count: 25,
              href: "/place/LK11",
            },
            {
              level: 3,
              label: "DS divisions",
              count: 340,
              href: "/place/LK1103",
            },
            {
              level: 4,
              label: "GN divisions",
              count: 14043,
              href: "/place/LK1103005",
            },
          ].map((item) => (
            <Link key={item.level} className="level-card" href={item.href}>
              <span className="level-count">{formatNumber(item.count)}</span>
              <span className="level-label">{item.label}</span>
              <span className="level-arrow" aria-hidden="true">
                →
              </span>
            </Link>
          ))}
        </div>
        <p className="muted small">
          {index.size.toLocaleString("en-LK")} geographies in the spine. {formatNumber(13945)}{" "}
          GN divisions have census values; 98 spine GNs have no row in the two held workbooks.
        </p>
      </section>

      <section className="section shell">
        <div className="section-head">
          <div>
            <p className="eyebrow">Limits</p>
            <h2>What this preview does not claim</h2>
          </div>
        </div>
        <div className="limits-grid">
          <div className="limit">
            <h3>Not the full census</h3>
            <p>
              Education, employment, housing amenities, water, sanitation and cooking fuel
              are not in this build. They are not shown as empty charts.
            </p>
          </div>
          <div className="limit">
            <h3>Not yet human-verified</h3>
            <p>
              All values are tagged <code>machine_extracted</code>. No sample of GN values
              has been checked against the workbook by a person.
            </p>
          </div>
          {latest.publishable ? (
            <div className="limit">
              <h3>Non-commercial use only</h3>
              <p>
                DCS has published no reuse terms. These figures are published
                non-commercially by decision D-030, with attribution and a notice in every
                download and API response. That is not a licence from DCS.
              </p>
            </div>
          ) : (
            <div className="limit">
              <h3>Not publishable</h3>
              <p>
                This build is a private preview. The release is marked{" "}
                <code>publishable: false</code> and every API response repeats that.
              </p>
            </div>
          )}
          <div className="limit">
            <h3>Not a ranking of people</h3>
            <p>
              No indicator here is broken down by ethnicity or religion. Spatial clusters are
              descriptions of the data, not causal findings.
            </p>
          </div>
        </div>
        <p className="muted">
          Read the <Link href="/methods">methods and known gaps</Link>, or the{" "}
          <Link href="/data">release contents and API</Link>. Full release:{" "}
          <code>{latest.release}</code>.
        </p>
      </section>
    </>
  );
}
