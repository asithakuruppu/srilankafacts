# Technology choices

Status: **proposed** · 2026-11-07 · Criteria applied to every choice: (1) fits small data and high trust, (2) low operational burden for a solo, non-coding lead, (3) well known to AI coding agents, (4) open formats and no lock-in, (5) cost.

Versions are deliberately not pinned here. The repository bootstrap (prompt F01) pins current stable versions and records them.

---

## 1. Summary of recommendations

| Layer | Recommendation | Instead of | Revisit when |
|---|---|---|---|
| Data processing | **Python + DuckDB (spatial extension) + GeoPandas/GDAL**, managed with `uv` | PostGIS-centred ETL; Spark | Never needed at this scale |
| Orchestration | **Python CLI + GitHub Actions** (scheduled and manual workflows) | Prefect, Airflow, Celery | More than 30 independently scheduled datasets → evaluate Dagster |
| Validation | **pytest + Pandera** + custom geo checks; **Frictionless Data Package** for release metadata | Great Expectations (heavy) | — |
| Source of truth | **Versioned release files** (Parquet/GeoParquet/CSV) + Git catalogue | PostGIS as master | — |
| Object storage | **Cloudflare R2** (no egress fees) | S3 (egress costs for tiles) | — |
| Serving database | *None until Stage 3*; then **managed Postgres + PostGIS** | Self-hosted DB on a VPS | Paying users need queries, or accounts are needed |
| Web framework | **Next.js (App Router, TypeScript)** with a persistent map layout | Astro, SvelteKit | — |
| Web hosting | **Vercel Pro** to start (simplest for agents); keep portable to Cloudflare | VPS + nginx | Cost or vendor concerns |
| Map renderer | **MapLibre GL JS** (+ **deck.gl** later for heavy overlays) | Leaflet, Mapbox GL (licensed) | — |
| Tiles | **PMTiles** built with **Tippecanoe**; values joined via `feature-state` | GeoServer, live PostGIS tiles | Dynamic tiles needed → Martin |
| Basemap | **Protomaps basemap extract** self-hosted on R2 | OpenFreeMap (no SLA), MapTiler (paid) | — |
| Charts | **Observable Plot** for standard charts; D3/visx for bespoke (decide in W01 spike) | ECharts (heavy), Recharts (limited) | — |
| Motion | CSS transitions + **Motion** (Framer Motion) + View Transitions; reduced-motion respected | GSAP everywhere | — |
| Search | Client-side trilingual place index + **Pagefind** for content | Elasticsearch | Content > ~5k pages → Typesense/Postgres FTS |
| API (Stage 1) | **Static JSON files** + OpenAPI description | FastAPI from day one | — |
| API (Stage 3) | **FastAPI** over Postgres/DuckDB | Node API (second backend language) | — |
| AI extraction | Deterministic parsers first (openpyxl, pdfplumber, camelot, **Docling**); **Claude** with structured outputs as fallback; human verification sheet | LLM-only extraction | — |
| AI distribution | **MCP server** + `llms.txt` | Public chatbot | Demand and evaluation results justify one |
| Analytics | Cloudflare Web Analytics or Umami | Google Analytics (privacy, PDPA) | — |
| Testing (web) | Vitest + Playwright + Lighthouse CI + axe | — | — |
| Tooling | Python: uv, ruff, pyright, pytest · JS: pnpm, TypeScript strict, ESLint/Biome | — | — |

---

## 1a. Pinned versions (from lockfiles, 2026-11-07)

Installed by the F01 bootstrap; read from `pipeline/uv.lock` and `web/node_modules`. Update this list when upgrading.

| Area | Package | Version |
|---|---|---|
| Python runtime | CPython (`pipeline/.python-version`) | 3.12 |
| Pipeline | typer | 0.28.0 |
| Pipeline | pyyaml | 6.0.3 |
| Pipeline | pydantic (catalogue schemas, F02) | 2.14.3 |
| Pipeline | geopandas · pyogrio (GDAL 3.12.4 bundled) · shapely · pyproj (G01) | 1.2.0 · 0.13.0 · 2.2.0 · 3.8.0 |
| Pipeline | pandas · numpy · pyarrow | 3.1.1 · 2.5.4 · 26.0.1 |
| Pipeline | openpyxl (DCS workbooks, G02) · matplotlib (QA thumbnails, G03) | see `pipeline/uv.lock` |
| Pipeline dev | ruff | 0.17.4 |
| Pipeline dev | pyright | 1.1.414 |
| Pipeline dev | pytest | 9.2.0 |
| Web | next | 16.4.5 |
| Web | react / react-dom | 19.3.0 |
| Web | typescript | 5.9.3 |
| Web dev | eslint | 9.39.5 |
| Web dev | vitest | 5.1.0 |
| Web dev | @testing-library/react | 16.3.3 |
| Web dev | jsdom | 31.0.0 |
| Web dev | @playwright/test | 1.65.0 |
| Package manager | pnpm (`packageManager` in `web/package.json`) | 12.18.0 |
| CI | actions/checkout · setup-node · astral-sh/setup-uv · pnpm/action-setup | v7.0.1 · v7.1.0 · v10.3.3 · v6.1.1 (pinned by SHA) |

GDAL comes bundled inside pyogrio, so no system GDAL install is needed. DuckDB is not installed yet: G01 did not need it, so it arrives with the first task that does (G02 or D01). MapLibre arrives with W02.

---

## 2. Key comparisons

### 2.1 Where should the "truth" live? Files vs PostGIS

| | Versioned files + Git catalogue | PostGIS as master |
|---|---|---|
| Provenance | Each release is immutable, hashed and citable. A diff between releases is easy. | Needs extra versioning tables. Updates in place erase history unless guarded. |
| Review by a non-coder | YAML/CSV diffs in PRs | DB migrations and SQL, harder to review |
| Reproducibility | Rebuild from snapshots anywhere | Depends on DB state and backups |
| Spatial queries | DuckDB spatial for builds. PostGIS added later for serving. | Excellent |
| Operations | None | Hosting, backups, upgrades, connections |
| AI agent safety | Changes in branches; nothing live until release | Agents with DB credentials can break production |

**Choice: files as truth, PostGIS as a later cache.** This is the pattern OWID uses at much larger scale 🟡. The brainstorm's "both can coexist" is right; the difference is *which one is the master*.

### 2.2 Orchestration

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| Python CLI + GitHub Actions | Zero infrastructure, logs and history in GitHub, free for public repos, agents know it | No asset lineage UI; job limits around 6 h | **Start here** |
| Dagster | Asset lineage, good for data products, local UI | Another service to run or pay for | Revisit at scale |
| Prefect | Flexible | Same overhead, weaker asset model | Not now |
| Airflow | Industry standard | Heavy for one person | No |
| Celery + Redis | For app background jobs | Not a data orchestrator; we have no app jobs | No |

### 2.3 Web framework

| | Next.js | Astro | SvelteKit |
|---|---|---|---|
| Persistent map across page navigations, each page server-rendered | **Natural** (shared layout keeps client component mounted) | Possible (`transition:persist`) but less natural | Possible |
| JS shipped on content pages | More by default; manageable with server components | **Least** | Low |
| App-like features later (accounts, dashboards) | **Strong** | Adequate | Strong |
| Agent familiarity, ecosystem (react-map-gl, visx, deck.gl) | **Highest** | Good | Lower |
| Pitfalls | App Router caching semantics confuse agents; keep to SSG/ISR and simple fetches | — | Smaller ecosystem |

**Choice: Next.js.** The deciding factor is the persistent, animated map *around* real, citable pages, which is the synthesis of your visual ambition with search and citation needs. Mitigate complexity with rules in AGENTS.md: static generation by default, no exotic caching, a strict performance budget.

### 2.4 Hosting the web app

| | Vercel Pro | Cloudflare (Workers + OpenNext) | VPS |
|---|---|---|---|
| Ops burden | Lowest | Low, more config | High |
| Next.js support | Native | Via adapter, occasional gaps | Manual |
| Cost at our scale ❓ | ~USD 20/month | ~0–5 | ~5–20 + your time |
| Commercial use | Pro required (Hobby is non-commercial) | Allowed on free tier | Yes |

**Choice: Vercel Pro to start; data and tiles on R2 regardless.** Moving to Cloudflare later is a contained task if cost matters.

### 2.5 Maps

- **MapLibre GL JS:** open-source WebGL renderer, the de facto open choice, supports PMTiles via protocol, `feature-state`, globe and terrain. Mapbox GL v2+ is proprietary-licensed, and Leaflet has no vector-tile WebGL performance.
- **PMTiles** (single-file tile archives over HTTP range requests): no tile server, cheap on R2, simple versioning per release. Lanka Data Layer already serves a 38.7 MB admin PMTiles this way ✅.
- **Tippecanoe** for boundary tiles (fine control over simplification and zoom levels). Basemap: extract Sri Lanka from a Protomaps daily build 🟡 rather than building from OSM ourselves.
- **Data join on the client via `feature-state`:** one tileset per boundary vintage, many indicators. A new indicator is a small JSON file, not a tile rebuild.

### 2.6 Processing engine

| | DuckDB + spatial | GeoPandas only | PostGIS |
|---|---|---|---|
| Speed on 14k polygons × hundreds of indicators | Excellent | Fine | Excellent |
| Reads/writes Parquet, GeoParquet, CSV, Excel | Native | Via libraries | Import/export |
| Runs in CI with no service | **Yes** | Yes | Needs a container |
| SQL for transformations (reviewable) | Yes | No (Python) | Yes |
| Geometry repair, projections | Good (GEOS-based) | **Best** (Shapely, pyproj) | Best |

**Choice: DuckDB for tabular and most spatial work; GeoPandas/Shapely/GDAL for geometry QA and repair.** Work in EPSG:4326 for publication and SLD99 / Sri Lanka Grid 1999 (EPSG:5235) for area and distance calculations (confirm the CRS of each source).

### 2.7 AI-assisted extraction

1. **Deterministic first:** Excel via openpyxl; text PDFs via pdfplumber/camelot; complex layouts via Docling (open source).
2. **LLM fallback:** send page images and text to Claude with a strict output schema (structured outputs), and ask for cell-level source locators.
3. **Automatic cross-checks:** row and column totals, hierarchy sums, comparison with nuuuwan or LDF extractions where they exist.
4. **Human verification sheet** for key indicators (D02). Unverified values are labelled `machine_extracted` in the UI.

---

## 3. Reuse, integrate or build: existing projects

| Project | What it offers | Decision | Why |
|---|---|---|---|
| **Lanka Data Layer** (MIT) | Admin boundaries, p-codes, reverse-geocode grid, PMTiles, manifest pattern ✅ | **Borrow ideas and selected code (with attribution); cross-check; don't fork, don't depend on hosted API** | Mixed boundary sources, hierarchy bug, no history, Node pipeline with seed-file dependency ✅. Our spine needs vintages and crosswalks from the start. |
| **nuuuwan repositories** (MIT code) | Parsed census 1971–2024, DCS, CBSL, dengue, DMC, elections, geometries ✅ | **Integrate as upstream for discovery and cross-check**; primary sources stay authoritative | Saves extraction effort. Bus factor of one. Geometry licences unknown. |
| **LDF OpenGIN** (Apache-2.0) | Temporal entity graph of government structure ✅ | **Don't adopt; link to their products** | Different problem (organisations over time). Polyglot stack (Go/Ballerina, MongoDB, Neo4j, PostgreSQL) is heavy for us. Data is CC BY-NC-SA. |
| **OWID ETL / grapher** | Proven pipeline pattern; grapher code no longer MIT 🟡 | **Copy the pattern, not the code** | Licence and fit |
| **Data Commons** | Knowledge graph, place pages, MCP 🟡 | **Contribute to it later as a channel; don't build on it** | GCP and Spanner dependency, limited UI control |
| CKAN | Data portal software | **No** | Built for catalogues of files, not indicators on maps |
| .Stat Suite / PxWeb | SDMX dissemination for statistics offices | **No** (borrow SDMX ideas for the observation model) | Built for NSO infrastructure, heavy |
| GeoNode / GeoServer | OGC GIS portal / services | **No** (until a client needs WMS/WFS) | Heavy operations |
| Datasette | Instant browsable SQL over SQLite | **Maybe (Stage 2)** as a cheap power-user explorer, alongside DuckDB-WASM | Low cost; test demand |
| Protomaps / PMTiles | Basemap and tile format | **Adopt** | Fits static-first |
| HDX COD-AB | Boundaries | **Adopt as primary geometry input**, verified | Survey Department source, CC BY-IGO |

---

## 4. Choices deliberately left open

| Question | Options | How to decide | When |
|---|---|---|---|
| Chart library | Observable Plot vs visx vs a thin D3 layer | W01 spike: build the same three charts; compare bundle size, SSR, accessibility | Stage 1 |
| GN pages: prerender or on demand | SSG for all ~14k vs ISR | Measure build time in W03 | Stage 1 |
| Serving DB provider | Supabase, Neon or Crunchy (all managed Postgres with PostGIS ❓ verify) | Price, PostGIS version, region latency to Sri Lanka | Stage 3 |
| Reverse-geocoding method | Client-side point-in-polygon on tiles vs precomputed grid (LDL-style) vs serverless function | Accuracy test against known points | Stage 2 |
| Code licence | Apache-2.0 vs MIT | Apache-2.0 has an explicit patent grant; both are fine | Stage 0 |
