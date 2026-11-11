# QA report: Census 2024 GN population and occupied housing units

First dataset release, private preview `v2026.11.4-preview.1`, built 2026-11-08 by
`slf build census-2024-gnd-tables` and `slf release` (prompt D01, Stage 1A).

**Result:** PASS for a private preview: 0 errors, 3 recorded warnings, 0 unresolved
arithmetic or anchor mismatches. **Not publishable:** DCS rights are `unclear`.

## 1. Dataset scope

Only two DCS workbooks are held. The other CPH 2024 topic tables are **not** part of this
release and no placeholder values exist.

| Workbook | Contents | Rows | Raw snapshot | sha256 |
|---|---|---|---|---|
| GN population by sex and age group | 6 columns: total, male, female, 0–14, 15–59, 60–64, 65+ | 14,008 GN + 340 DS rows | `raw/dcs/census-2024-gnd-tables/20261107T165036Z/GN_population.xlsx` | `2e0168c5daa43af4c4f61a55389768d5c86508ad47252a2d8c89a52986215425` |
| Occupied housing units by GN | occupied housing units | 14,008 GN rows | `raw/dcs/census-2024-gnd-tables/20261107T165040Z/GN_housing.xlsx` | `db5a9af593316cfce8ac72282ebc0aba4edc91443d0afce233db09cd53d8c62a` |

Both were retrieved on 2026-11-07:
`https://www.statistics.gov.lk/Population/StaticalInformation/CPH2024/GN_population_excel`
and `.../GN_housing_excel`. The final report PDF
(`.../CPH2024_Final_Eng.pdf`, sha256
`a6dea9388d05bbb8c9f08d32f562a258838b737938275ed4a2f6ee34ecd670ca`) is used only for
anchors, never for cell values. Reference date: **19 December 2024**.

`information_count: 14008` in the catalogue records the source information unit: GN-level
DCS rows. The published release has values at GN, DS, district, province and country level,
all derived from those rows.

## 2. What was built

`slf build census-2024-gnd-tables`:

| Check | Result |
|---|---|
| Observations written | **200,466** (14 indicators × 14,319 places with values) |
| Validation errors | **0** |
| Validation warnings | **3** (listed in §5) |
| GN rows read from each workbook | 14,008 |
| DCS DS rows | 340 (338 matched to COD-AB, 1 provisional `LK-ADM3-P0001`, 1 unmatched DS 5224) |
| Indicators | 14 (9 counts, 3 shares, 2 ratios; see `docs/methods/census-2024.md`) |

Release `v2026.11.4-preview.1`:

| Artifact | Count |
|---|---|
| Files in release | 14,586 |
| Checksums in `CHECKSUMS.sha256` | 14,585 (the checksum file itself is excluded) |
| Place JSON files | 14,418 (all spine geographies, including 99 with no values) |
| Geographies with values | 14,319 |
| Geography level counts | 1 country, 9 province, 25 district, 339 DS, 1 provisional DS, 14,043 GN |
| `publishable` | `false` (every API payload) |

## 3. Anchors and arithmetic (✅ verified)

National values match the DCS final report:

| Indicator | Value |
|---|---|
| Total population | 21,781,800 |
| Male | 10,512,344 |
| Female | 11,269,456 |
| Aged 0–14 | 4,506,839 |
| Aged 15–59 | 13,353,837 |
| Aged 60–64 | 1,183,310 |
| Aged 65+ | 2,737,814 |
| Aged 60+ (derived) | 3,921,124 |
| Occupied housing units | 6,030,541 |

Arithmetic checks on all 14,008 DCS GN rows:

| Check | Rows passing |
|---|---|
| Total = male + female | 14,008 / 14,008 |
| 0–14 + 15–59 + 60–64 + 65+ = total | 14,008 / 14,008 |

All 25 district population and housing anchors match the DCS final report tables:

- Table 3.1, printed p.67: district population.
- Table 3.2, printed p.51 / PDF p.68: district population by sex and age.
- Table 11.1, p.201: occupied housing units.
- Table 11.2, printed p.185 / PDF p.202: housing units by district.

Independent comparison, used only as a check and never as a source:

- `nuuuwan/lk_census_2024`, snapshot
  `raw/nuuuwan/nuuuwan-lk-census-2024/20261107T165224Z/Person-Sex_gnd_data.json`:
  **14,008 / 14,008** DCS GNs matched, **0** mismatches for total, male and female.

## 4. Derived indicators

- Sex ratio = 100 × male ÷ female. `LK5315010` has 1 male and 0 female, so its sex ratio is
  `not_available`, not zero and not infinity.
- Age shares = 100 × age group ÷ total population.
- Persons per occupied housing unit = population ÷ occupied housing units. The numerator
  and denominator come from **two different snapshots**; `snapshot_sha256` records the
  population workbook and `source_locator` names both files.
- Density = population ÷ land area. Area is computed in EPSG:5235 from the COD-AB v03
  boundary, not from the census workbook.
- All higher-level counts are sums of GN rows, including the 63 unmatched DCS GNs.
  Rates are recomputed from summed numerators and denominators, never averaged from child
  rates.
- A zero denominator produces `not_available` for the affected ratio. Five GNs have zero
  population (`LK4112185`, `LK4112220`, `LK4112225`, `LK5110025`, `LK7210065`); their sex
  ratio is `not_available` and their density is 0.0.

## 5. Known gaps (recorded, not hidden)

1. **63 DCS GN units are unmatched** in the G02 crosswalk. They are included in their DS,
   district, province and country totals (population 97,681; occupied housing 25,760) but
   have no GN-level rows. Their codes and DCS names are in the G02 review queue.
2. **DCS DS 5224 Kalmunai** has no COD-AB equivalent (decision D-022). Its 29 GNs
   (population 52,798; occupied housing 13,481) enter the Ampara district total
   (`LK52` = 744,551), but no DS-level row is published. Ampara DS rows sum to 691,753;
   the 52,798 difference is exactly DS 5224.
3. **DCS DS 5221** maps to provisional `LK-ADM3-P0001` (29 GNs, population 31,556,
   occupied housing 8,675, area 12.699301 km²). It is excluded from the DS contiguity graph
   and is an island, so its spatial context is `no_neighbours` rather than an invented
   neighbour list.
4. **98 spine GN divisions** have no DCS row in the two held workbooks. They have no
   GN-level observations and are published as `no_data`, not as zero.
5. **65 COD-AB GN divisions have no English name** (and no Sinhala/Tamil name) in the
   spine. The website falls back to a level label and the p-code, for example
   “Grama Niladhari division LK5104002”. This is a name gap in the boundary source, not an
   invented name. Seven of the 65 have a DCS `external_name` in the crosswalk; that name
   is not yet promoted to the published name field. D-028 keeps the p-code for 1A and
   requires the names to be resolved through the crosswalk review before 1B.
6. **Every value is `machine_extracted`.** No human has spot-checked a GN cell against the
   workbook, and no QGIS visual check of GN boundaries against DCS names has been done.
7. **Rights are unclear.** No copyright notice, licence or reuse terms were found on the
   DCS page, homepage, workbook or final report. The release is `publishable: false` and
   `robots.txt` disallows crawling. Stage 1A stays private and no public release is
   authorised (D-023); the reuse-terms letter is approved for the lead to send. See
   `docs/research/rights/census-2024-gnd-tables.md`.
8. **No basemap.** The preview draws COD-AB boundaries on a plain background; PMTiles
   tooling was unavailable. This is a recorded deviation, not a finished map.
9. **Small-denominator threshold is 100 (confirmed).** The lead confirmed 100 on
   2026-11-08 (D-026). Preview.1 already used it, so no rebuild was needed. Smoothed
   values are stored separately and labelled `modelled_estimate`; they never replace
   published values.

## 6. Release integrity (✅ verified)

- Two consecutive builds produced identical `CHECKSUMS.sha256` values; the release has no
  wall-clock timestamp in its metadata, so the version is its identity.
- All JSON in `api/v1` is strict JSON: `grep -rl "NaN" api/v1` returned 0 files.
  Non-finite values (including `NaT` and missing names) are written as `null`.
- `shasum -a 256 -c CHECKSUMS.sha256` passes from the release root.
- The GeoPackage has five layers (`admin0`–`admin4`) and is deterministic; its metadata
  date is derived from the release version, not the clock.
- The release builder refuses to write a public release while any dataset rights are
  `unclear` or `restricted`.

## 7. Website and API checks (✅ verified)

- Production build against the full preview release: passed (`next build`, 375 static
  admin place pages; GN pages render on demand). A second build with
  `SLF_RELEASE_DIR=fixtures/preview` also passed, which is the CI path when the full
  release is absent.
- Unit tests: 13 passed. Browser smoke tests: 8 passed (home, search, explore table, place
  provenance, indicator, data, methods, API).
- Static API: `/api/v1/places/LK11.json` returns `publishable: false`,
  `release: v2026.11.4-preview.1`, 14 values and per-value `snapshot_sha256`.
- The map is an enhancement on every page, and the table is its accessible alternative.
  Place, indicator, data and methods pages render their content server-side, so they remain
  readable without JavaScript. `/explore` builds its table in the browser, so it needs
  JavaScript; the map is still optional there. D-027 requires a server-rendered initial
  table before 1B, so this is a known 1A limitation, not the public-beta design.
- The map uses the release worker copied to `/release/maplibre-gl-worker.mjs`; a local
  production smoke run showed no map error.
- `web/fixtures/preview` is a 1.25 MB committed subset (71 geographies, 980 observations,
  release `v2026.11.4-preview.1`) so CI can build without the 459 MB release.

## 8. Outputs

Release root: `pipeline/data/build/releases-preview/v2026.11.4-preview.1`.

Key files: `observations/census-2024-gnd-tables.parquet` (1.7 MB),
`observations/census-2024-gnd-tables.csv` (98.3 MB), `boundaries/admin0–4.geojson`,
`geographies.gpkg`, `geographies.parquet`, `geography_versions.geoparquet`,
`api/v1/`, `stats/local_*.parquet`, `stats/spatial_summary.json`,
`qa/summary.md`, `qa/spatial-context.md`, `CHECKSUMS.sha256`, `datapackage.json`.

QA summary: `qa/summary.md` (0 errors, 3 warnings). Spatial QA:
`qa/spatial-context.md` and `docs/methods/spatial-context.md`.
