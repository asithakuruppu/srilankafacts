import type { Metadata } from "next";
import Link from "next/link";

import { formatBytes } from "@/lib/format";
import { getDatapackage, getLatest, releaseName } from "@/lib/release";

export const metadata: Metadata = {
  title: "Data and API",
  description: "Release contents, checksums, static API and citation for the Census Atlas preview.",
  alternates: { canonical: "/data" },
};

const RELEASE_FILES = [
  "observations/census-2024-gnd-tables.parquet",
  "observations/census-2024-gnd-tables.csv",
  "boundaries/admin0.geojson",
  "boundaries/admin1.geojson",
  "boundaries/admin2.geojson",
  "boundaries/admin3.geojson",
  "boundaries/admin4.geojson",
  "geographies.gpkg",
  "geographies.parquet",
  "geography_versions.geoparquet",
  "stats/spatial_summary.json",
  "qa/summary.md",
  "qa/spatial-context.md",
  "CHECKSUMS.sha256",
  "datapackage.json",
];

const ENDPOINTS = [
  {
    path: "/api/v1/releases/latest.json",
    description: "Release id, status, citation, dataset rights and counts.",
    example: "curl -s https://data.example/api/v1/releases/latest.json",
  },
  {
    path: "/api/v1/places/{geoId}.json",
    description: "One place with all 14 values, each with its locator and snapshot hash.",
    example: "curl -s https://data.example/api/v1/places/LK11.json",
  },
  {
    path: "/api/v1/indicators.json",
    description: "Indicator metadata: name, definition, unit, aggregation and levels.",
    example: "curl -s https://data.example/api/v1/indicators.json",
  },
  {
    path: "/api/v1/indicators/{id}.json",
    description: "One indicator's metadata and available levels.",
    example: "curl -s https://data.example/api/v1/indicators/population_density.json",
  },
  {
    path: "/api/v1/indicators/{id}/{level}.json",
    description:
      "Values for one indicator at one level: country, province, district, ds, ds-provisional or gn.",
    example:
      "curl -s https://data.example/api/v1/indicators/population_total/district.json",
  },
  {
    path: "/api/v1/geographies/admin.json",
    description: "The admin geography index with names in English, Sinhala and Tamil.",
    example: "curl -s https://data.example/api/v1/geographies/admin.json",
  },
];

export default function DataPage() {
  const latest = getLatest();
  const datapackage = getDatapackage();
  const resources = new Map(
    (datapackage?.resources ?? []).map((resource) => [resource.path, resource]),
  );
  const listed = RELEASE_FILES.map((file) => ({
    path: file,
    size: resources.get(file)?.bytes ?? null,
    hash: resources.get(file)?.hash ?? null,
  }));
  const total = listed.reduce((sum, file) => sum + (file.size ?? 0), 0);
  const observations = resources.get("observations/census-2024-gnd-tables.parquet");

  return (
    <div className="shell section">
      <header className="place-head">
        <p className="eyebrow">Data</p>
        <h1>Release contents and static API</h1>
        <p className="lede">
          Every page on this site is built from an immutable release directory. The release
          contains the observations, boundaries, a GeoPackage, a static JSON API, spatial
          context tables, QA reports and checksums.
        </p>
      </header>

      {latest.publishable ? (
        <div className="notice notice-warn">
          <strong>Non-commercial use only.</strong> DCS has published no reuse terms. The
          census values are published non-commercially by decision D-030; every file and API
          response carries the attribution and notice (see <code>NOTICE.md</code>). The DCS
          source workbooks are not redistributed.
        </div>
      ) : (
        <div className="notice notice-warn">
          <strong>This preview is not downloadable publicly.</strong> The release is marked{" "}
          <code>publishable: false</code>. The files exist only in the private build directory
          for review. Do not mirror or redistribute them.
        </div>
      )}

      <section className="section" aria-labelledby="release-heading">
        <div className="section-head">
          <div>
            <p className="eyebrow">Release</p>
            <h2 id="release-heading">{latest.release}</h2>
          </div>
          <p className="section-note">
            {latest.publishable ? "Public release" : "Private preview"} ·{" "}
            {latest.observation_count.toLocaleString("en-LK")} observations ·{" "}
            {latest.geography_count.toLocaleString("en-LK")} geographies
          </p>
        </div>
        <div className="table-scroll">
          <table>
            <caption className="visually-hidden">Selected release files</caption>
            <thead>
              <tr>
                <th scope="col">File</th>
                <th scope="col">Size</th>
                <th scope="col">sha256</th>
              </tr>
            </thead>
            <tbody>
              {listed.map((file) => (
                <tr key={file.path}>
                  <th scope="row">
                    <code>{file.path}</code>
                  </th>
                  <td className="numeric">{file.size === null ? "—" : formatBytes(file.size)}</td>
                  <td>
                    {file.hash ? (
                      <code className="hash">{file.hash.replace("sha256:", "")}</code>
                    ) : (
                      "—"
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="muted small">
          Selected artifacts, {formatBytes(total)} in total.{" "}
          {observations
            ? "The full manifest lists every file and hash in datapackage.json."
            : "This build uses the small CI fixture, so file sizes and hashes are not shown."}{" "}
          Verify with <code>shasum -a 256 -c CHECKSUMS.sha256</code> from the release root.
        </p>
      </section>

      <section className="section" aria-labelledby="api-heading">
        <div className="section-head">
          <div>
            <p className="eyebrow">API</p>
            <h2 id="api-heading">One GET per place or indicator</h2>
          </div>
          <p className="section-note">
            Generated files only, no dynamic server. Every response carries the release,
            citation, rights status and per-value provenance.
          </p>
        </div>
        <div className="endpoint-list">
          {ENDPOINTS.map((endpoint) => (
            <div className="endpoint" key={endpoint.path}>
              <code className="endpoint-path">{endpoint.path}</code>
              <p>{endpoint.description}</p>
              <pre>
                <code>{endpoint.example}</code>
              </pre>
            </div>
          ))}
        </div>
        <p className="muted small">
          This website mirrors <code>/api/v1/places/{"{geoId}"}</code> and{" "}
          <code>/api/v1/indicators/{"{id}"}/{"{level}"}</code> from the release for the map.
          The complete generated API is the release directory itself; the examples above use a
          placeholder host because a public base URL is not yet agreed.
        </p>
      </section>

      <section className="section" aria-labelledby="rights-heading">
        <div className="section-head">
          <div>
            <p className="eyebrow">Rights</p>
            <h2 id="rights-heading">Why the downloads are blocked</h2>
          </div>
        </div>
        <table>
          <tbody>
            <tr>
              <th scope="row">Source</th>
              <td>Department of Census and Statistics, Sri Lanka</td>
            </tr>
            <tr>
              <th scope="row">Rights status</th>
              <td>
                <code>{latest.datasets[0]?.rights_status ?? "unclear"}</code>
              </td>
            </tr>
            <tr>
              <th scope="row">Licence</th>
              <td>{latest.datasets[0]?.licence ?? "None recorded"}</td>
            </tr>
            <tr>
              <th scope="row">Attribution</th>
              <td>{latest.datasets[0]?.attribution ?? "Not specified"}</td>
            </tr>
            <tr>
              <th scope="row">Boundaries</th>
              <td>
                OCHA COD-AB v03, CC BY-IGO. Boundary licence is recorded separately from the
                census values.
              </td>
            </tr>
          </tbody>
        </table>
        <p>
          Read the rights review in <code>docs/research/rights/census-2024-gnd-tables.md</code>{" "}
          and the methods in <Link href="/methods">Methods and known gaps</Link>.
        </p>
      </section>

      <section className="section" aria-labelledby="cite-heading">
        <h2 id="cite-heading">Citation</h2>
        <blockquote>{latest.citation}</blockquote>
        <p>
          Department of Census and Statistics, <em>Census of Population and Housing 2024</em>,
          GN population by sex and age group and occupied housing units. Sri Lanka Facts
          release <code>{releaseName()}</code>. Include the snapshot sha256 and source locator
          from the observation you use.
        </p>
      </section>
    </div>
  );
}
