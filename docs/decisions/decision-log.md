# Decision log

The single place where project decisions are recorded. AI agents must read this before working and **must not contradict an Accepted decision**. If a task seems to need that, they stop and raise it.

**Statuses:** `Proposed` (awaiting the lead's confirmation) · `Accepted` (D-001 to D-020 accepted by the lead on 2026-11-07) · `Superseded by D-NNN` · `Rejected`.
**To change a decision:** add a new entry that supersedes the old one. Don't edit history. Change only the old entry's status line.

---

## Carried forward from the brainstorm (Accepted)

These were stated by you or are standing rules in [brainstorm-decisions.md](../brainstorm-decisions.md).

| ID | Decision | Source |
|---|---|---|
| C-01 | Never fabricate data. Never silently replace authoritative statistics with estimates. | Brainstorm §4, §8 |
| C-02 | Keep original source files untouched; work on separate cleaned copies. | Brainstorm §4 |
| C-03 | Every observation carries provenance (source, document, dates, method, revision). | Brainstorm §15 |
| C-04 | Preserve historical versions of boundaries and names; never overwrite. | Brainstorm §4 |
| C-05 | Never paywall basic public statistics. No advertising, no sale of personal data. | Brainstorm §13 |
| C-06 | Governance principles (§11) apply from day one. | Brainstorm §11 |
| C-07 | The product is very visual, with an interactive map and a fluid, animated UI. **Amended by D-002 if you accept it.** | User direction, brainstorm §1 |
| C-08 | One assignment at a time; evidence required; review before the next milestone. | Brainstorm §8 |
| C-09 | Record reuse rights per dataset. | Brainstorm §13, §17 |

---

## D-001: Positioning: the place-based data layer for Sri Lanka
- **Status:** Accepted · 2026-11-07 (accepted by the lead 2026-11-07; proposed the same day)
- **Context:** A comprehensive, topic-based national statistics portal (USAFacts-style) needs a large funded team, and its national layer is partly served by CBSL, Advocata, Verité and commercial aggregators ([landscape](../research/ecosystem-landscape.md)). Sub-national data is the least served and most map-appropriate.
- **Decision:** Sri Lanka Facts' core identity is "every place in Sri Lanka, every number about it, with its source". National series appear as context for places, not as the main product.
- **Alternatives:** comprehensive topic portal (rejected: infeasible solo, overlaps); geography-only infrastructure like LDL (rejected: too narrow, little audience).
- **Consequences:** the roadmap prioritises the spine and sub-national indicators. Public finance and institutions come later or through partners.
- **Revisit when:** funding allows a larger team, or users clearly ask for national topics.

## D-002: Map-first, not map-only
- **Status:** Accepted · 2026-11-07 (accepted by the lead 2026-11-07; proposed the same day) · Amends C-07
- **Context:** A full-screen map as the only container hurts search visibility, citation, accessibility, low-end phones and national-level figures.
- **Decision:** Every place and indicator has a server-rendered page with a stable URL, readable text, a table and sources. A **persistent map shell** stays mounted across those pages and animates between places. `/explore` offers the full-screen immersive mode. Lite mode without WebGL.
- **Alternatives:** map-only SPA (rejected); no map on content pages (rejected: loses the visual identity).
- **Consequences:** Next.js layout architecture (D-007); performance budget enforced in CI.

## D-003: Releases are the source of truth; static-first serving
- **Status:** Accepted · 2026-11-07 (accepted by the lead 2026-11-07; proposed the same day)
- **Context:** Small data, high trust, one non-coding lead. The brainstorm's stack (PostGIS master, Prefect, Celery, Redis, GeoServer, FastAPI) has many moving parts.
- **Decision:** Immutable, versioned releases built from hashed snapshots by a Python/DuckDB pipeline on GitHub Actions are the source of truth. The site, tiles, downloads and API (Stage 1) are static files on a CDN. Postgres/PostGIS and FastAPI are added later as rebuildable serving layers when a concrete need appears (triggers in [architecture §6](../architecture/architecture-overview.md#6-how-the-architecture-evolves)).
- **Alternatives:** PostGIS as master (rejected for now: operations, review difficulty, mutable history).
- **Consequences:** No dynamic queries in Stage 1. Every value is citable by release.

## D-004: Geography identifiers and the GN-atom model
- **Status:** Accepted · 2026-11-07 (accepted by the lead 2026-11-07; proposed the same day)
- **Context:** Codes differ across DCS, NSDI, OCHA and LDL; DS/GN counts disagree; non-admin geographies don't nest ([audit §11](../lanka-data-layer-audit.md)).
- **Decision:** Admin units use OCHA p-codes. Other schemes use prefixed IDs (`LK-LA-`, `LK-ED-`, `LK-PD-`, `LK-MOH-`). Units missing from COD-AB get provisional IDs. External codes live in a crosswalk with match method and confidence. Hierarchy comes from relations, never from parsing codes. Non-admin units are composed of GN divisions with weights. Identity changes create new IDs; minor boundary edits create new versions.
- **Alternatives:** `LK-DIST-07`-style IDs from the brainstorm (rejected: reinvents an existing standard); DCS codes as IDs (rejected: drift across sources ✅).
- **Consequences:** G01/G02 build the crosswalk first; any dataset join goes through it.

## D-005: Licensing of outputs and code
- **Status:** Accepted · 2026-11-07 (accepted by the lead 2026-11-07; proposed the same day)
- **Decision:** CC BY 4.0 for our text, charts and derived tables where input rights allow. ODbL for OSM-derived databases. Unclear-rights data is displayed with attribution but not redistributed until clarified. Code under Apache-2.0, public from Stage 1.
- **Alternatives:** non-commercial or restrictive licences (rejected: weakens citation and reuse; contradicts the open positioning); closed code (rejected: loses credibility and contributors).
- **Consequences:** Revenue comes from services and guarantees, not data sales (D-010).

## D-006: First public release is the Census Atlas 2024
- **Status:** Accepted · 2026-11-07 (accepted by the lead 2026-11-07; proposed the same day)
- **Context:** The brainstorm proposed three launch sections and large launch targets, sized for a team.
- **Decision:** Stage 1 ships one flagship: 2024 Census at every admin level to GN, with place pages, explorer, downloads, static API, methodology and corrections log ([vision §6](../vision/vision-and-strategy.md#6-the-flagship-census-atlas-2024)).
- **Alternatives:** Population + Economy + Institutions (rejected: thin, overlapping); boundaries-only atlas (rejected: no audience hook).
- **Consequences:** Rights clearance with DCS is on the critical path.

## D-007: Core technology stack
- **Status:** Accepted · 2026-11-07 (accepted by the lead 2026-11-07; proposed the same day)
- **Decision:** Python (uv) + DuckDB + GeoPandas/GDAL; pytest + Pandera; GitHub Actions; Cloudflare R2; Next.js (App Router, TypeScript) on Vercel Pro; MapLibre GL JS + PMTiles (Tippecanoe) + Protomaps basemap extract; Observable Plot (pending spike); Pagefind. Details in [technology-choices.md](../architecture/technology-choices.md).
- **Revisit when:** the triggers in the architecture document fire.

## D-008: Reuse policy for ecosystem projects
- **Status:** Accepted · 2026-11-07 (accepted by the lead 2026-11-07; proposed the same day) · Amends the LDL audit's recommendation (option C, fork the foundry)
- **Decision:**
  - *Lanka Data Layer:* don't fork or depend on its hosted API. Borrow ideas and selected MIT code with attribution. Use it as a cross-check. Report the Ampara bug.
  - *nuuuwan repositories:* use as discovery and cross-check upstreams. Primary sources remain authoritative. Credit them. Ask about geometry provenance before using `gig-data`.
  - *LDF:* link to their products. Don't reuse CC BY-NC-SA data in anything commercial. Explore a division of labour.
  - *LankaData.net:* no reuse of its archive or endpoints.
- **Consequences:** We build our own spine from COD-AB/Survey Department and DCS, which takes more work up front but leaves us in control of history and quality.

## D-009: Quality model: data nature and verification
- **Status:** Accepted · 2026-11-07 (accepted by the lead 2026-11-07; proposed the same day) · Supersedes the A–D grade (brainstorm §15)
- **Decision:** Each observation carries `data_nature` (census_count, administrative_count, survey_estimate, official_estimate, modelled_estimate, reconstruction) and `verification` (machine_extracted, spot_checked, human_verified, reconciled, disputed). A display badge is derived from them ([data-model §6](../architecture/data-model.md#6-quality-two-dimensions-one-badge)).
- **Why:** the single grade mixed how a number was produced with how well it was checked.

## D-010: Organisation and revenue
- **Status:** Accepted · 2026-11-07 (accepted by the lead 2026-11-07; proposed the same day)
- **Decision:** One small legal entity and one brand. Services-funded open platform: commissioned analysis, sampling frames and catchment work first; API service levels and tools later; grants when there is a track record. No subscription tier before demand is proven. Governance principles published at launch ([business model](../vision/organisation-and-business-model.md)).
- **Revisit when:** recurring revenue covers running costs, or a grant or partner requires a non-profit structure.

## D-011: AI policy
- **Status:** Accepted · 2026-11-07 (accepted by the lead 2026-11-07; proposed the same day)
- **Decision:** AI is used internally for extraction, QA and drafting, always with human verification for key values and human editing for published text. Externally: MCP server and `llms.txt` (Stage 2); no public chatbot until an evaluation set shows reliable, cited answers. AI-generated text is labelled. No AI-generated values in published fields without verification status.

## D-012: Languages
- **Status:** Accepted · 2026-11-07 (accepted by the lead 2026-11-07; proposed the same day) · Refines brainstorm §10/§12
- **Decision:** English UI first. Trilingual place names (si/ta/en) in the data from day one, never machine-transliterated into published fields. Sinhala and Tamil core pages in Stage 3, with human review.

## D-013: Spatial-first data contract
- **Status:** Accepted · 2026-11-07 (accepted by the lead 2026-11-07; proposed the same day)
- **Context:** The lead wants all data to be location-based and modelled spatial-first. Some data is genuinely national, and some is measured in one place but used nationally (for example the CCPI 🟡).
- **Decision:** Every dataset declares a `spatial` block (support: area, point, line, grid or national; scheme, level, vintage, coverage, where measured, positional accuracy, source CRS, derivation method). The pipeline refuses datasets without it. National figures attach to `LK` and are never pushed down. Geometry is stored once per place version, not on observation rows. Details: [spatial-first-analytics.md §3](../architecture/spatial-first-analytics.md#3-the-spatial-contract-every-dataset).
- **Alternatives:** geometry on every row in a spatial database (rejected: duplication, harder review, conflicts with D-003); location as an optional filter (rejected: not spatial-first).
- **Consequences:** F02 and G01 updated; a contiguity graph ships with every spine vintage; point and line features become a first-class entity (`FEATURE`).
- **Revisit when:** a data type appears that doesn't fit the five supports.

## D-014: Three spatial fabrics, with H3 as a derived analytic grid
- **Status:** Accepted · 2026-11-07 (accepted by the lead 2026-11-07; proposed the same day) · Extends D-004
- **Context:** Reporting units don't nest, change between vintages, and can't directly hold rasters, points or user-drawn areas.
- **Decision:** Reporting units (with GN atoms) stay authoritative. **H3** resolution 10 (~100 m, the atom per D-017), 8 (analysis) and 6 (display) is a derived grid, fed only through named, versioned bridge methods (aggregate, apportion, point-in-polygon, zonal statistics, network distance). Anything apportioned is `modelled_estimate` and never the default map of an official indicator.
- **Alternatives:** square grids (acceptable; H3 preferred for neighbours, hierarchy and tooling; reversible because derived); grid as source of truth (rejected: invents precision).
- **Consequences:** GN-to-hex weights in Stage 2 (G07); building or population weight source chosen by measured completeness, not assumption.
- **Revisit when:** official grid statistics are published for Sri Lanka.

## D-015: Spatial context and place vectors as the default analytics
- **Status:** Accepted · 2026-11-07 (accepted by the lead 2026-11-07; proposed the same day) · Amends D-006 (flagship scope)
- **Context:** The lead wants a new way of doing analytics, with spatiality at the core and exploration through vectors. Raw census tables already exist elsewhere (nuuuwan); spatial context does not.
- **Decision:** Every value is shown against neighbours, parent, similar places and the country. Local cluster and outlier statistics (with false-discovery control) and small-number handling are computed in a new pipeline stage, *enrich*. Every place gets a **profile vector** from standardised indicator blocks, used for "places like this" (always with reasons), a typology (Stage 2), change vectors and custom recipes. All are precomputed static files plus in-browser computation: **no vector database, no server**. **Ethnicity and religion are excluded from default profiles.** Satellite embeddings (AlphaEarth) are a Stage 3 experiment, subject to a licence check.
- **Alternatives:** classic indicator-by-indicator portal (rejected: not differentiated); vector database or embedding service (rejected: unnecessary at about 14,000 places).
- **Consequences:** Census Atlas gains neighbour context, clusters/outliers and "places like this"; drawn areas, typology and scale check in Stage 2. New prompts D06, G07, A03.
- **Open for the lead:** may users include ethnicity and religion in *custom* similarity recipes? Recommendation: no in Stage 1–2; revisit with advisers.
- **Revisit when:** user research shows the spatial context confuses rather than helps.

## D-016: Vector-native, fact-anchored core
- **Status:** Accepted · 2026-11-07 (accepted by the lead 2026-11-07; proposed the same day) · Extends D-013 to D-015
- **Context:** The lead wants the core to be conceptually vector-based: every entity a point in a multi-dimensional space, with relationships measured by distance.
- **Decision:** Two layers. The **ledger** holds exact, cited facts (observations, places, hierarchy, borders, features) and stays the source of truth. Every entity also has coordinates in **named, versioned spaces** (`geo`, `profile`, `trajectory`, `text`, later `landscape`, `access`, and a user-weighted `composite`), computed deterministically from a release. Degree relations (alike, near, changed, unusual) are distances in a stated space; exact relations (inside, borders, measured by) stay in the ledger. The first joint space puts places and indicators together by PCA or correspondence analysis, so every distance decomposes exactly into named indicators. Details: [vector-space-model.md](../architecture/vector-space-model.md).
- **Alternatives:** vector-only core where hierarchy and adjacency are inferred from embeddings (rejected: not citable, not stable, wrong for exact relations); one undifferentiated space for all entities (rejected: meaningless cross-type distances, distance concentration, hidden metric choices); learned neural embeddings first (rejected for now: not reproducible or explainable enough for the flagship).
- **Consequences:** catalogue gains `VECTOR_SPACE`, releases gain `EMBEDDING` and `AXIS` files; every published relationship records its space and version; A03 builds the profile space; a two-map explorer (W08) in Stage 2. Still no vector database or server.
- **Revisit when:** vectors reach millions of rows, or users show the space metaphor confuses more than it helps.

## D-017: Multi-scale entities: a ~100 m cell as the atom, features below it, and an information floor on every value
- **Status:** Accepted · 2026-11-07 (accepted by the lead 2026-11-07; proposed the same day) (revised the same day) · Extends D-004, D-014, D-016
- **Context:** The lead wants to zoom below GN level to buildings, land, individual trees, landmarks and every mapped detail. Official statistics stop at GN level; maps go much finer.
- **Revision:** the lead pointed to 100 m population and land-cover grids. The atom is now an **H3 resolution 10 cell (~100 m)**, the finest common unit for every layer. The GN becomes the **information floor** for census data, not the atom: every dataset records the unit its information really comes from (WorldPop's Sri Lanka population grid draws on 13,938 GN units of the 2012 Census ✅), and maps show an effective-resolution note.
- **Decision (as refined by D-018):** The **cell** is the common index and finest analytic unit; the true atom is the observation with its footprint. The **individual feature** (building, parcel, tree, landmark, road segment, water body) is the physical object below and across the cell, an entity in the vector-native core with `geo`, `form` and `context` coordinates, exact links to every geography it falls in, and roll-ups into place profiles. Feature layers come from open sources (OSM, Overture, Wikidata, canopy and land-cover products), reusing Overture's conflation and GERS IDs, each class admitted only after a use, rights and completeness test. **Statistics about people are never attributed to individual buildings or parcels, and no owner or occupant data is published.** OSM-derived feature layers are ODbL. Details: [multi-scale-features.md](../architecture/multi-scale-features.md).
- **Alternatives:** GN as the only atom (rejected: loses the physical detail the lead wants and the real information in fine grids); treating 100 m population grids as if they were observed at 100 m (rejected: their people information comes from GN totals); building our own map database (rejected: duplicates OSM, impossible solo); downscaling census data to buildings (rejected: privacy and ethics).
- **Consequences:** feature GeoParquet and PMTiles in releases; `FEATURE_CODE` crosswalk; heavy builds may need a larger machine than CI; feature-level similarity moves to the Stage 3 serving layer; legal checklist gains map-publication approval and ODbL aggregate questions. New prompt G08.
- **Revisit when:** sub-metre imagery rights or parcel data become available through a partnership.

## D-018: Footprint model: every value has a where, a when and a what
- **Status:** Accepted · 2026-11-07 (accepted by the lead 2026-11-07; proposed the same day) · Refines D-013, D-014, D-017
- **Context:** The lead proposed storing every value as a point plus a polygon showing the resolution of the data, and asked whether that beats a grid. They then added that every data point should carry time and geographic space as well as other dimensions.
- **Decision:** **Footprint-first, grid-indexed.** Every value has a representative point, a spatial footprint (its true shape: GN polygon, pixel square, building outline, or an uncertainty circle), a `support_type` (`area_total`, `area_mean`, `location_uncertain`, `object_extent`, `field_sample`), an information footprint, and a time footprint (`time_start`, `time_end`, `time_support`, boundary vintage), plus its meaning dimensions and provenance. The ~100 m H3 cell is the **common index** (every footprint has a cell cover with fractions), not the source of truth. Combined results take the coarser footprint in space and time. Details: [footprint-model.md](../architecture/footprint-model.md).
- **Alternatives:** grid as truth (rejected: loses or invents precision); circles for everything (rejected: area totals and uncertain locations need different maths); footprints without a grid index (rejected: too slow to combine at scale).
- **Consequences:** observation schema gains footprint and time-footprint fields; footprints stored by reference, not copied; "what do we know here?" point query (Stage 2); uncertain locations handled as probabilities (Stage 3); scale and time become explicit dimensions in the vector spaces.
- **Revisit when:** a source type appears that none of the five support types describes.

## D-019: Every value is a claim; conflicting sources are shown, not hidden
- **Status:** Accepted · 2026-11-07 (accepted by the lead 2026-11-07; proposed the same day) · Extends D-009, D-018
- **Context:** Sri Lankan sources often disagree (DS counts of 331, 332, 339 or 340; GN counts; population figures; boundaries). The lead wants users to be able to compare multiple conflicting sources.
- **Decision:** Each observation is a **claim** by one source about one footprint, time footprint and indicator; several claims can coexist. One may be marked `preferred` for default display, always with a written reason. Disagreement (spread, relative spread, source count, overlap within uncertainty) is computed and stored as a dimension. The UI shows a "sources disagree" badge, a side-by-side panel and a disagreement map. Reconciliation is a documented override, never a silent edit. Details: [live-events-and-sources.md §2](../architecture/live-events-and-sources.md#2-comparing-multiple-conflicting-sources-core-d-019).
- **Alternatives:** pick one source silently (rejected: hides uncertainty, erodes trust); show only reconciled values (rejected: reconciliation is often impossible).
- **Consequences:** observation schema gains `claim_id`, `preferred`, `preferred_reason`; validation compares claims; Stage 1 shows disagreement for unit counts and census totals.
- **Revisit when:** never in principle; the UI may be simplified after user testing.

## D-020: Live data as scheduled near-real-time files; streaming deferred
- **Status:** Accepted · 2026-11-07 (accepted by the lead 2026-11-07; proposed the same day) · Amends D-003
- **Context:** The lead wants as much live and historical free data as possible (weather, disasters, prices) and moving objects (trains, buses, aircraft).
- **Decision:** Live feeds run as **scheduled jobs** (15–60 minutes for weather, daily or weekly for others) writing immutable time partitions plus a small "latest" file, inside the release model with per-fetch provenance. **True streaming** (positions every few seconds) is deferred to Stage 4 and will be the first server component. Every feed needs a rights entry first; free-of-charge APIs that forbid commercial use are flagged, because the services model is commercial. Social media mood is parked pending lawful access and an ethics review.
- **Alternatives:** streaming platform from the start (rejected: cost and operations for a solo founder); no live data (rejected: loses a major use case).
- **Consequences:** a rolling-partition pattern in the pipeline; new Stage 3 "Living Sri Lanka" and Stage 4 "Movement" in the roadmap.
- **Revisit when:** a feed or customer genuinely needs sub-minute updates.

## D-021: Relationships are a graph in the data model, not a graph database
- **Status:** Accepted · 2026-11-07 (accepted by the lead 2026-11-07; proposed the same day) · Extends D-004, D-013, D-016
- **Context:** The lead asked why not use a graph database. Much of the data is graph-shaped: the admin hierarchy, contiguity, weighted crosswalks between schemes and vintages, lineage (splits and merges), claim → snapshot → source provenance, and features inside places.
- **Decision:** Model exact relationships as **node and edge tables** (Parquet in each release; `GEO_RELATION`, `GEO_ADJACENCY`, crosswalks, lineage, provenance), each edge with a source and a time footprint like any fact. Query them with DuckDB (recursive SQL) or networkx in the pipeline. **No graph database server.** Three views of one truth: the ledger says what is true, the graph says what is connected (exact), vector spaces say what is similar (derived, D-016). Exact relations are never inferred from vectors (AGENTS rule 13).
- **Alternatives:** Neo4j or another graph database (rejected for now: a server to host and pay for, breaks static-first, weak polygon support, columnar analytics are slower, GPL/commercial licensing for the free edition 🟡, agents less fluent in graph query languages, downloads harder to use).
- **Consequences:** edge tables are published as downloads, which also eases a later linked-data export (JSON-LD, Wikidata links). F02 defines the relation schema; G01 builds the hierarchy and contiguity edges.
- **Revisit when:** users need interactive multi-hop queries over millions of edges, or road-network analysis (travel time to services) becomes a core product. First try a graph extension inside DuckDB (DuckPGQ, community extension 🟡) or Postgres before adding a separate database.

---

## Template

```markdown
## D-NNN: Title
- **Status:** Proposed · YYYY-MM-DD [· Supersedes / Amends …]
- **Context:**
- **Decision:**
- **Alternatives:**
- **Consequences:**
- **Revisit when:**
```
