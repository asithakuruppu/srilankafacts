# W05: Downloads and static API

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 1 | Backend (static) / Developer experience | 1 | 2026-11-07 | active |

## When to use
To publish release data as downloads and a documented, file-based JSON API.

## Read first
- `AGENTS.md`
- `docs/architecture/architecture-overview.md` §5.3
- `docs/architecture/data-model.md` §5, §7
- D04 release layout

## Inputs (fill in)
```
RELEASE:  version
BASE_URL: e.g. https://data.<domain>/ (CDN in front of R2)
```

## Task
1. Generate static API files from the release: `/api/v1/places/{geoId}.json`, `/api/v1/indicators.json`, `/api/v1/indicators/{id}.json`, `/api/v1/indicators/{id}/{level}.json`, `/api/v1/geographies/{scheme}.json`, `/api/v1/releases/latest.json`. Versioned paths under `/releases/{version}/` plus `latest` aliases. Every response includes `release`, `licence`, `citation` and source references.
2. JSON Schemas for each response type; contract tests validating every generated file.
3. An OpenAPI 3.1 document describing the static endpoints (GET only), plus examples in curl, Python, R and JavaScript.
4. A `/data` page: downloads per dataset (CSV, Parquet), boundaries (GeoPackage, GeoParquet), the full bundle, sizes, checksums, licence and attribution text, and how to cite.
5. CDN and storage configuration notes: CORS `*` for GET on API and tiles, long cache lifetimes for versioned paths, short ones for `latest`.
6. A link checker over all download links.

## Constraints
- No dynamic server code. Everything is generated files.
- File sizes stay reasonable: split large level files if needed and document it.

## Verify (show real output)
Contract-test results; file counts and total size; a sample curl of three endpoints from a local static server; link-checker output.

## Deliverables
Generator, schemas, OpenAPI, `/data` page, tests and docs.

## Done when
A developer can fetch any place or indicator with one GET, and every response says where the number came from and how to cite it.

Report using the format in `AGENTS.md`.
