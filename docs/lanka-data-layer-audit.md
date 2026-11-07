# Lanka Data Layer — repository and live-service audit

Audited 2026-11-07. Repo: https://github.com/prabhavalabs/lanka-data-layer. Live host: https://lanka-data-layer.prabhavalabs.com.

Method: GitHub API metadata, file tree, raw README / architecture / infra docs, the bundled `admin.json`, the npm registry, and live GET requests to the hosted API. A local build, test run and integrity check were added later (section 10). NSDI attribute comparison added in section 11. **Still not done: polygon-shape comparison, Survey Department comparison, opening the web app.**

Tags: ✅ verified by me · 🟡 claimed in README/docs, not independently checked · ❌ not found.

## 1. Summary

It is a real, working project, not a placeholder. It is much closer to what we want for the Administrative Atlas than LankaData.net is (see [lankadata-audit.md](lankadata-audit.md)). It is young, though: one author, 92+ commits over about seven weeks, and v0.1.0 packages.

- ✅ MIT-licensed code. Live API returns real data for lookups, reverse geocoding, datasets, demographics and PMTiles.
- ✅ The numbers in our brainstorm file hold up: 14,417 admin units (1 country, 9 provinces, 25 districts, 339 DS, 14,043 GN), all with unique p-codes.
- ⚠️ It has **no boundary history** (no `valid_from`/`valid_to`) and mixes two boundary sources for different levels. Both matter for our "historical geography" goal.
- ⚠️ The 2024 census data has **no stated licence**. Most of the OSM layers are ODbL (share-alike).

## 2. Repository facts

| Item | Finding | Status |
|---|---|---|
| Owner / author | Prabhava Labs; all 92 commits on the first API page are by one author (Nipun Theekshana) | ✅ |
| Created / last push | 2026-08-12 / 2026-09-30 | ✅ |
| Popularity | 32 stars, 4 forks, 0 open issues | ✅ |
| Branches | `main` (production), `develop` | ✅ |
| Code licence | MIT, © 2026 Prabhava Labs | ✅ |
| Layout | pnpm monorepo: `foundry` (ETL), `api`, `web`, `shared`, `packages/*` (4 npm libs), `infra`, `docs` | ✅ |
| Tests | Test files exist in `api/`, `foundry/` and `packages/*`; **I did not run them** | ✅ exist / ❌ not run |
| npm packages | `@lanka-data-layer/admin`, `postal`, `electoral`, `census` all published at 0.1.0 (2026-08-13), MIT | ✅ |
| Affiliation with LankaData.net | None seen. Different org, host and domain | ✅ (nothing found) |
| Predecessor project | `prabhavalabs/ceylon-hub` — the build still copies some files from it | 🟡 (not inspected) |

## 3. What it serves (live catalogue, `GET /v1/datasets`)

✅ Verified live, data version `20260813.8`.

| Dataset | Features | Licence (as declared) | Source |
|---|---|---|---|
| admin-units | 14,417 | CC BY 3.0 IGO / CC BY-IGO | geoBoundaries + OCHA COD-AB |
| cell-lookup (reverse-geocode grid) | 5,467,970 | CC BY-IGO | OCHA COD-AB |
| cells (gridded population) | 5,468,498 | CC BY 4.0 | WorldPop |
| census-2024 | 9,125 | **Not stated** | Dept of Census and Statistics |
| population-2023 | 1,225 | CC BY-IGO | HDX cod-ps-lka |
| elections | 820 | "open" | Election Commission via nuuuwan/lk_elections |
| postal-codes | 1,833 | CC BY 4.0 | GeoNames |
| places / pois | 553 / 6,942 | ODbL | OpenStreetMap |
| roads / railways / waterways / protected-areas | 11,252 / 1,618 / 3,919 / 66 | ODbL | OpenStreetMap |
| country | 1 | CC BY 3.0 IGO | geoBoundaries |

## 4. API

- ✅ Base `/v1`; envelope `{ success, message, payload, meta }`; `meta` carries `data_version` and source.
- ✅ Working endpoints I called: `/v1/health`, `/v1/datasets`, `/v1/reverse`, `/v1/admin/:pcode`, `/v1/demographics/LK11`, `/v1/tiles/admin.pmtiles` (HTTP range requests, 38.7 MB).
- ✅ Caching: `ETag` carries the data version; `Cache-Control: public, max-age=300, stale-while-revalidate=86400` (tiles 3600).
- 🟡 Other routes listed in the README (`search`, `lookup`, `postal`, `population`, `elections`, geometry) — present in the source tree, not individually called.
- ❌ I saw no `Access-Control-Allow-Origin` header on `/v1/health`, so browser calls from another origin may fail. Check this before building a front end that calls it directly.
- 🟡 README says "no API keys". I found no rate-limit headers; limits live in the nginx config (`infra/nginx/lanka-data-layer-limits.conf`), which I did not read.

## 5. Architecture

- 🟡→✅ Everything spatial is precomputed offline by `foundry` into one read-only SQLite file, plus PMTiles. Reverse geocoding is a single indexed lookup on a 0.001° (~111 m) grid (`cell_id = row*2700 + col`). The API reverse call returned a correct-looking GN → DS → district → province chain for Kandy coordinates.
- ✅ Admin units use OCHA p-codes (`LK`, `LK1`, `LK11`, `LK1103`, `LK1103005`) as the stable join key, with `parent_pcode`, trilingual name fields and area/centroid.
- ✅ Foundry/API/web separation is enforced by an architecture doc that calls itself a binding contract.
- Hosting: a single VPS behind nginx, Cloudflare in front (✅ from `infra/README.md`; live host responds from nginx/1.24.0).

## 6. Fit against our brainstorm decisions

| Our decision | Lanka Data Layer | Gap |
|---|---|---|
| Stable geography IDs | ✅ OCHA p-codes, unique across 14,417 units | Our example `LK-DIST-07` style differs; we can map or adopt p-codes |
| Trilingual names | ✅ fields exist | ✅ Sinhala present on nearly all units (65 GN missing); ❌ Tamil is `null` for **all 14,043 GN divisions** (section 10); DS Tamil name for Gangawata Korale returned "கண்டி" (the district name), which looks wrong |
| `valid_from` / `valid_to`, historical versions | ❌ none in the schema; data is a single snapshot (`20260813.8`) | Must be added by us |
| Provenance + licence per dataset | ✅ catalogue and `manifest.json` carry source, licence, count | Good model to copy |
| Map-first visual UI | 🟡 README describes a MapLibre explorer with dark theme, 3D population layer, OpenFreeMap basemap; I did not open the web app | Evaluate visually |
| Source files kept untouched | 🟡 `foundry/data/raw` is kept; unverified | Check on a local build |
| Differentiators (infra atlas, district indicators, history, API) | Partial: has POIs, roads, rail, waterways, census 2024 demographics | No economy data yet (listed as planned) |

## 7. Data-quality and licence concerns

All 🟡 unless noted; most are stated by the project itself in its "Known limitations".

1. ✅ **339 DS divisions** from COD-AB, versus about 330–331 in other sources. The README says it serves COD-AB as published.
2. **Mixed boundary sources:** levels 0–2 from geoBoundaries, levels 3–4 from COD-AB; the README admits edges can disagree.
3. **Census 2024 has no licence.** Reuse of those numbers carries legal uncertainty. Ask the Department of Census and Statistics.
4. **Census 2024 matched to DS divisions by name** (hand-made alias table); one row (Kalmunai North Sub) has no counterpart.
5. **Gridded population is a model** (WorldPop), not a count.
6. **Postal-code areas are derived,** not official.
7. **OSM tables are ODbL.** Redistributing the underlying data triggers share-alike. Serving it through an API or map does not.
8. **Boundary currency:** COD-AB/geoBoundaries snapshot dated 2026-08; whether it matches the current official Survey Department boundaries is unchecked.
9. **Documentation drift:** the README says `infra/` is "planned" while the folder and a live deployment exist, so check README claims against code before relying on them.
10. **Bus factor:** one author, one VPS, public service with no stated SLA. The basemap (OpenFreeMap) also has no uptime SLA.

## 8. Reuse options

| Option | What it means | Pros | Cons |
|---|---|---|---|
| A. Use the npm packages | Embed `@lanka-data-layer/admin` etc. (zero dependencies, offline) | Fastest start; MIT; ~830 kB admin | Frozen snapshot; no history; GN reverse geocode not included |
| B. Call the hosted API | Use `/v1/*` for lookups and PMTiles | No hosting yet | Depends on a third-party single VPS; CORS and rate limits unconfirmed |
| C. Fork the foundry | Run our own pipeline, add history and our sources | Full control; keeps their p-code scheme | Needs ceylon-hub seed files and a first build; we own maintenance |
| D. Build independently, borrow ideas | Keep only the schema and grid concepts | No dependency risk | Slowest; repeats solved work |

**Recommendation:** C, with A for quick prototypes. Fork or vendor the foundry, keep OCHA p-codes as the primary key, and add the missing history layer ourselves. Do not depend on their hosted API in production. This is a recommendation, not a decision.

## 9. Not yet verified (next steps)

1. Clone into an isolated directory, run `pnpm install`, the tests, and a full foundry build (about 3 minutes claimed, needs Node ≥ 22 and tippecanoe, and a local `ceylon-hub` checkout).
2. Check the geometry for invalid/duplicate polygons, gaps/overlaps, and CRS.
3. Compare their boundaries with NSDI's ArcGIS REST service and the Survey Department.
4. Open the web app and judge it against our "fluid, animated, high-tech" direction and performance on mobile.
5. Ask the project owner about the census 2024 licence and the ceylon-hub seed files.
6. Read the nginx rate-limit config and test CORS from a browser origin.

## 10. Local build and integrity results (added 2026-11-07)

Environment: clone of `main` (shallow) plus `ceylon-hub` for seed files, in an isolated scratch directory; Node 25.9, pnpm 10.0.0 via npx. Nothing installed globally.

**Tests ✅ — 254 of 254 pass, 0 fail:** shared 8, foundry 103, api 98, admin 12, postal 13, electoral 11, census 9. (The `web` package has no test script I ran.)

**Foundry build ✅ with a gap.** It completed with exit 0 and produced `lanka.sqlite` (386.8 MB, data_version `20261107.1`) and `manifest.json`. Fetching live sources worked (GeoNames, WorldPop, OCHA, census). Differences from the README:
- Took about 10 minutes, not the "roughly 3" claimed. The GN boundary download (4 min) and cell lookup (4.5 min) dominate.
- I **skipped the vector-tile step** because `tippecanoe` is not installed, so no PMTiles were built locally. Tiles are unverified except the hosted file.
- `pnpm install` blocks the native `better-sqlite3` build script by default; I had to run `pnpm rebuild better-sqlite3 esbuild`. The README does not mention this.
- The build needs the `ceylon-hub` checkout for 20 seed files, as the README says.

**Hierarchy checks (SQLite):**
- ✅ Counts match the live API: 1 / 9 / 25 / 339 / 14,043. No orphan parents; parent levels consistent; no null or zero areas.
- ❌ **Wrong parent: Ampara District (LK52) is parented to Uva Province (LK8) instead of Eastern Province (LK5).** Reproduced on both my fresh build and the **live API** (`/v1/admin/LK52`). Its 19 DS divisions hang under that wrong district, so Eastern Province rolls up without Ampara and Uva rolls up with it. I have not found the cause; it is likely a spatial parent assignment for levels 0–2, but that is a guess.
- ❌ **Tamil names: 0 of 14,043 GN divisions** have one; 65 GN have no Sinhala name. DS divisions and above have both.
- 🟡 **17 groups of GN divisions share a name within the same parent**, so names are not unique keys (p-codes are).
- 🟡 Area totals by level: country 66,359 km²; provinces 66,359; districts 66,358; DS 66,010; GN 65,984. DS/GN are about 0.5% short of the national total, which suggests small gaps (coast/water edges), not confirmed.
- The country row has no geometry in `admin_geometry` (served as a separate layer).

**Geometry checks (shapely) — caveat:** these ran on the **simplified** geometry the project stores for map highlights (about 0.0005° tolerance), not the original COD-AB polygons. Simplification can create self-intersections and overlaps, so these numbers overstate source errors and say nothing about the raw files.
- 116 of 14,416 simplified geometries are invalid (self-intersection), including provinces LK3 and LK4 and districts LK33 and LK41.
- Overlaps above 0.01 km²: districts 4 pairs (0.13 km² total), DS 514 pairs (about 16 km²), GN 6,030 pairs (about 109 km²). The largest single overlap is about 0.18 km².
- Reverse geocoding fell back to nearest polygon (within 2 km) for 97,920 cells and found no polygon for 528 cells (out of 5,467,970 assigned).
- Census 2024: Kalmunai North Sub (Ampara, population 31,556) is unmatched and skipped, as the README says.

**Conclusion.** The pipeline is reproducible and well tested, but the data has at least one definite hierarchy error and a large Tamil-name gap. Treat it as a good starting point that needs its own validation step (we should add the checks above to our pipeline), not as an authoritative boundary source. The Ampara error is worth reporting to the project with this evidence.

Still open: comparison with NSDI / Survey Department boundaries; raw (unsimplified) polygon validation; web app review; CORS and rate-limit config.

## 11. Comparison with NSDI boundaries (added 2026-11-07)

Source: NSDI ArcGIS REST service `gisapps.nsdi.gov.lk/server/rest/services/Srilanka/Boundaries/MapServer`, queried 2026-11-07 (✅ live, public, no key; max 1,000 records per query). The service shows **no copyright or licence text**, so reuse terms are unknown. This compared **attribute tables only** (names, codes, counts, areas), not polygon shapes.

| Level | NSDI | Lanka Data Layer | Note |
|---|---|---|---|
| Provinces | 9 | 9 | match |
| Districts | 25 | 25 | match |
| DS divisions | 332 features (329 unique codes) | 339 | see below |
| GN divisions | 14,051 | 14,043 | differ by 8 |

**Ampara confirmed.** NSDI puts Ampara District (code 52) in Eastern Province (5), so the Lanka Data Layer parent (Uva) is an error in their pipeline, not a source disagreement.

**DS divisions (✅ compared by code):**
- 326 codes appear in both.
- NSDI-only: `Water Area` (code 9999, listed twice), Eravur Pattu (5112) and Kalmunai (5224). The latter two probably map to differently coded units on the other side, which I did not confirm.
- Lanka Data Layer-only: 13 units, including Ududumbara, Walapane, Mathurata, Kothmale West, Thalawakele, Norwood, Wanduramba, Madampagama, Rathgama, Kalthota, Eravur Town, Kalmunai (5221) and Town & Gravets. Most look like real recent or alternate DS divisions, which would explain the 339 vs 330-331 gap, but I did not verify which are official.
- 61 of the 326 shared codes have different names, mostly spelling variants (Pujapitiya/Poojapitiya, Dehiovita/Dehiowita, Karaitheevu/Karaitivu). One needs checking: code 2309 is "Walapane" in NSDI but "Nildandahinna" in Lanka Data Layer, which lists Walapane under 2324. So **codes are not stable across the two sources**; matching by code alone is unsafe.
- NSDI has duplicate rows (Water Area, Ganga Ihala Korale, Udubaddawa each appear twice) and 22 DS features flagged "DSD Boundary Problems".

**GN divisions (✅ compared by district + DS name):** of 340 DS groups, only 4 differ in GN count: Batticaloa "Water Area" (NSDI 5, Lanka Data Layer 0), Negombo (40 vs 39), Katana (80 vs 79), Mundel (32 vs 31). So the GN sets are nearly identical; the two sources likely share a lineage (NSDI's GN layer is all tagged year 2017, source "Satellite Images"; I did not confirm what COD-AB used).
- NSDI GN codes are **empty for all 14,051** features, and 266 carry a "dispute" flag. So NSDI cannot supply stable GN IDs; p-codes from OCHA remain the better key.

**Areas (🟡):** NSDI's `adjusted_area` field sums to 65,612 versus 66,358 for Lanka Data Layer districts. The largest district differences are Batticaloa (-8.0%), Vavuniya (+6.8%), Kilinochchi (+5.4%) and Polonnaruwa (+4.9%). I assumed km² for the NSDI field and did not check how "adjusted" is defined, so treat this as a flag, not an error.

**What this means for us:**
1. NSDI is a useful cross-check but not a drop-in replacement: it has duplicates, a water-area pseudo-division, empty GN codes and no stated licence.
2. We need a crosswalk table (NSDI code ↔ OCHA p-code ↔ name variants) and should match on name plus parent, not code.
3. The 339 vs 330-331 DS question needs an official source (Survey Department or DCS) before we publish a count.
4. Next: compare polygon shapes (area overlap per unit) and ask NSDI/Survey Department for terms of use.
