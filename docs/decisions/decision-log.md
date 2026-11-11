# Decision log

The single place where project decisions are recorded. AI agents must read this before working and **must not contradict an Accepted decision**. If a task seems to need that, they stop and raise it.

**Statuses:** `Proposed` (awaiting the lead's confirmation) · `Accepted` (D-001 to D-028 accepted by the lead, 2026-11-07 to 2026-11-08) · `Superseded by D-NNN` · `Rejected`.
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

## D-022: Provisional units for divisions missing from COD-AB; first one is Kalmunai North Sub
- **Status:** Accepted · 2026-11-08 (decided by the lead) · Applies data-model §3.2
- **Context:** DCS Census 2024 publishes 340 DS divisions; COD-AB v03 has 339. The difference is Kalmunai: COD-AB has one unit (`LK5221`, 58 GNs), while DCS publishes **Kalmunai North Sub** (DS 5221) and **Kalmunai** (DS 5224) separately, 29 GNs each. The 29 named COD-AB GNs in `LK5221` are exactly DCS 5221's GNs; the other 29 COD-AB GNs have no names. Without a unit for Kalmunai North Sub, DCS figures for it cannot be joined.
- **Decision:** Add **`LK-ADM3-P0001` Kalmunai North Sub** as a provisional DS unit under Ampara (`LK52`), defined by `composed_of` relations to its 29 GNs (`catalog/geographies/provisional.csv`, `relations/provisional.csv`); its geometry is derived as their union. General rule: units missing from COD-AB get `LK-ADM{level}-P{nnnn}` ids, never reused, defined by composition, `status: provisional` until an official boundary source settles them. Provisional units overlap COD-AB units, so they are excluded from area roll-ups, the contiguity graph and geometry QA. Person-made crosswalk decisions live in `catalog/geographies/manual-matches.csv`. The naming follows the DCS publication and implies no position on any administrative question (AGENTS rule 12).
- **Alternatives:** keep COD-AB only (rejected: loses published census figures); split `LK5221` into two units by inference (rejected: the remaining 29 GNs are unnamed, so their match to DCS 5224 is unverified).
- **Consequences:** DCS 5221 → `LK-ADM3-P0001` (manual match). DCS 5224 Kalmunai is **not** equivalent to `LK5221` and stays in review; whether to add a second provisional unit for it depends on matching the 29 unnamed GNs (needs a GN list with names, or geometry). Sinhala and Tamil names are to be recorded from an official source.
- **Revisit when:** the Survey Department or DCS supplies an official DS list or boundaries; or the 29 unnamed GNs are identified.

## D-023: Stage 1A stays private; the DCS reuse-terms letter is approved for sending
- **Status:** Accepted · 2026-11-08 (decided by the lead)
- **Context:** DCS has published no licence or reuse terms for the CPH 2024 tables, so `rights.status` stays `unclear`. Stage 1A is technically complete, but Stage 0's "rights letters sent" exit criterion is unmet because the letter at `docs/outreach/2026-11-07-dcs-reuse-terms.md` has not been sent. AGENTS rule 9 forbids agents from sending it.
- **Decision:** Stage 1A remains a private preview: `publishable: false`, no public mirror, no redistribution of DCS source files, and no public beta until DCS replies or the lead records a different rights position in this log. The DCS reuse-terms letter is approved for the lead to send; the agent must not send it. The send date and any reply are recorded in `docs/outreach/log.md` and, if rights change, in the dataset catalogue entry.
- **Alternatives:** publish now with attribution and a notice (rejected: the terms are unclear and the public-beta gate is not met); wait without sending (rejected: the blocker would not move).
- **Consequences:** 1A can be reviewed internally; 1B stays blocked. Non-commercial publication with attribution is **not** authorised by this entry; it would need a new decision, with legal advice if DCS does not reply. The Survey Department/NSDI boundary letter is also still unsent, so Stage 0's "rights letters sent" criterion stays open until both letters are sent.
- **Revisit when:** DCS replies, or the lead records a rights position with a legal basis.

## D-024: Stage 1 is split into 1A and 1B; Stage 1 work uses branch + PR + Q05
- **Status:** Accepted · 2026-11-08 (decided by the lead)
- **Context:** The Stage 0 retrospective found that all work landed on `main`, no pull requests or Q05 reviews ran, and the original 10–14 week Stage 1 estimate mixed engineering with rights and verification. Stage 1 is now two tracks.
- **Decision:** Approve the split in [development-strategy](../roadmap/development-strategy.md): **1A** is a 3–4 week private preview built from the two held workbooks; **1B** is a 5–6 week public beta that starts only after 1A and a recorded rights position. From Stage 1, every task uses a branch, a pull request and a Q05 review, including agent work. The current uncommitted work moves to a task branch when it is committed; history on `main` is not rewritten. 1A uses the English UI with the Sinhala names already in the spine; Tamil stays marked "not yet available" until a translator reviews it (D-012). DCS 5224 Kalmunai stays in review under D-022.
- **Alternatives:** keep the single 10–14 week track (rejected: hides the rights blocker); keep committing directly to `main` (rejected: no review or rework measure).
- **Consequences:** 1A is approved to proceed; 1B remains gated. The retrospective's review-process metric becomes measurable.
- **Revisit when:** the lead decides the review overhead is disproportionate, or Stage 1B closes.

## D-025: Approve the `profile` space v0.1 (two blocks, nine indicators)
- **Status:** Accepted · 2026-11-08 (decided by the lead)
- **Context:** A03 proposed a joint place–indicator space in `catalog/spaces/profile.yaml`, limited to the two DCS workbooks actually held. No profile vectors have been computed.
- **Decision:** Approve `profile` v0.1 as written: nine non-sensitive inputs in two blocks (demography: population total, four age shares, sex ratio; housing: occupied housing units, persons per occupied unit, population density); log and share transforms; z-standardisation by level; ±5 SD winsorising; equal block weights; PCA by SVD with the eigenvalue/loading rule; no imputation; places with population below 100 or a missing input are listed with a reason. Ethnicity and religion stay excluded (D-015). A03 steps 2–7 may now build the vectors, similar places, unusualness, contrasts and sensitivity check.
- **Alternatives:** wait for the missing amenity and education/work tables (rejected: blocks 1A for no gain); include ethnicity or religion (rejected: D-015).
- **Consequences:** vectors, axes and neighbour lists are machine-derived; axis labels stay AI-generated drafts until the lead approves them. Amenities and education/work are deferred until those tables are held and catalogued.
- **Revisit when:** the missing tables arrive, or user testing shows the axes are unreadable.

## D-026: The small-denominator threshold is 100
- **Status:** Accepted · 2026-11-08 (decided by the lead)
- **Context:** D06 used 100 as a provisional threshold; the preview release and its smoothed values were built with it, and the methods note marked it as an assumption.
- **Decision:** Confirm **100**. The flag applies to population for shares, age shares and density; to females for the sex ratio; and to occupied housing units for persons per occupied unit. The code constant in `pipeline/slf/enrich.py` stays 100; changing it requires a new decision and a rebuild because flags and smoothed values change. Published census values are never changed.
- **Alternatives:** another threshold (no evidence yet that it improves the flags); no flag (rejected: small bases produce unstable rates).
- **Consequences:** the threshold changes from `❓ assumption` to `✅ confirmed` in the methods note; preview.1 already used 100, so no rebuild is needed for this decision.
- **Revisit when:** a sensitivity check shows a different threshold materially changes GN flags, or DCS publishes a rule.

## D-027: `/explore` must server-render an initial table before Stage 1B
- **Status:** Accepted · 2026-11-08 (decided by the lead)
- **Context:** Place, indicator, data and methods pages render server-side, but `/explore` builds its table in the browser, so it needs JavaScript. The map is optional everywhere; the table is the accessible alternative.
- **Decision:** Stage 1A may keep the current client-rendered explorer table, with the limitation stated in the QA report. Before the 1B public beta, `/explore` must server-render an initial table from the URL state or the default indicator and level, so the page is readable without JavaScript. The map remains an enhancement. This becomes a 1B exit requirement.
- **Alternatives:** leave the table client-only (rejected: the main exploration page would fail without JavaScript); server-render it now (not required for the private preview, but may be done earlier).
- **Consequences:** W02/W05 work before 1B; the accessibility check includes a JavaScript-disabled pass.
- **Revisit when:** the explorer is replaced by a different interaction.
- **Implemented (2026-11-12):** the prerendered `/explore` HTML now contains a server-rendered table for the default view (population density by district), not just "Loading explorer…". Every indicator and level pair also has a static table page, `/explore/table/<indicator>/<level>`, linked from that view and from the interactive explorer. The interactive explorer and these pages share one table component. Browser smoke tests with JavaScript disabled check the default table and the links between table pages. Remaining limit: without JavaScript, `/explore?indicator=…&level=…` still shows the default table, because the URL is read in the browser; the static table pages are the no-JavaScript path to other views.

## D-028: Null-name GN divisions keep p-code labels for 1A; names resolved by crosswalk review before 1B
- **Status:** Accepted · 2026-11-08 (decided by the lead)
- **Context:** 65 COD-AB GN divisions have no English, Sinhala or Tamil name in the spine. Seven have a DCS `external_name` in the crosswalk, but it has not been checked or promoted.
- **Decision:** For 1A, the website shows a level label plus p-code (for example "Grama Niladhari division LK5104002") and does not promote `external_name` values ad hoc. Before 1B, resolve the names through the crosswalk review, record the name source and licence, and update the spine/crosswalk together. Sinhala and Tamil names follow D-012.
- **Alternatives:** promote the seven DCS names now (rejected: incomplete and unverified); invent or transliterate names (rejected: AGENTS rules 1 and 12).
- **Consequences:** some 1A place pages show p-codes; the seven candidates stay in the review queue.
- **Revisit when:** the crosswalk review resolves the names, or an official GN list arrives.
- **Evidence (2026-11-12):** `docs/research/geography/null-name-gns.md`. Of the 65 null-name GNs, 8 have the same English name in DCS 2024 and NSDI 2017 (with an NSDI Sinhala gazetted name), 4 have a DCS name only, 29 are Kalmunai (D-022), 7 are disputed Eravur Pattu units, and 17 have no candidate in any held source. The review also found and corrected a Kandalama/Kiralessa swap. Promotion waits for the lead's decision.
- **Implemented (2026-11-12):** the lead accepted the 12 names. `overrides/cod-ab-lka.csv` holds 12 English and 8 Sinhala names, each with its source and a note that rights are unclear. The spine build applies them and refuses stale rows. 53 GNs keep p-code labels: 29 Kalmunai, 7 Eravur Pattu, 17 with no candidate. D-028's 1B requirement is met for the names current sources can resolve. The rest wait for an official GN list.

## D-029: Profile space v0.2 keeps axes by a variance-share threshold, because the eigenvalue > 1 rule keeps none
- **Status:** Proposed · 2026-11-12 (agent; awaiting the lead) · Would amend D-025 (the retention rule only)
- **Context:** D-025 approved PCA "with the eigenvalue/loading rule": keep axes with eigenvalue > 1. With equal block weights (each block scaled to total variance 1), the eigenvalues sum to 2, not 9. On the real data the largest eigenvalue is 0.715 at GN level and 0.874 at DS level, so v0.1 keeps **zero axes** and cannot be built ✅ (`docs/qa/profile-space-v0.2.md` §2). The build also shows two exact redundancies: the age shares sum to 100, and persons per housing unit is population ÷ housing units, so settlement size enters through both log population (demography) and log housing units (housing) ✅.
- **Decision (proposed):** v0.2 keeps the D-025 recipe but retains a component when its eigenvalue exceeds total weighted variance ÷ 9 (the same "above-average axis" idea as Kaiser's rule; 0.222 at DS, 0.213 at GN after winsorising) and it has at least 3 loadings with |loading| ≥ 0.3; cap 6. This keeps 3 axes at each level, explaining 74% (GN) and 81% (DS) of the weighted variance.
- **Alternatives:** (a) drop block weighting and use Kaiser on 9 standardised inputs (demography's six inputs then dominate housing's three, which D-025 rejected); (b) a fixed number of axes, e.g. 3 (simple, but not tied to the data); (c) also drop occupied housing units, which is redundant given population and persons per unit, so the housing block stops counting size a second time (changes the inputs, so it is a v0.3 question).
- **Consequences:** `slf profile build` produces vectors, similar places with exact reasons, distance from the centre, bordering-unit contrasts and a sensitivity check (A03 steps 2–6). Nothing is in a release or on the website. **GN neighbour lists are unstable:** removing either block leaves about 2% of each GN's top-20 unchanged (DS: 27–38%), so GN "similar places" should not be published as robust without a further check. Axis labels are machine drafts until the lead writes them.
- **Revisit when:** the lead decides; the amenity or education/work tables arrive; or user testing shows the axes are unreadable.

## D-030: Census 2024 tables may be published non-commercially, with attribution and a notice, while DCS has not replied
- **Status:** Accepted · 2026-11-12 (decided by the lead) · Amends D-023 (the "stays private" part)
- **Context:** DCS publishes no licence or reuse terms for the CPH 2024 tables (rights memo E1–E5). The reuse-terms letter and the other outreach drafts have been sent, as the lead reported on 2026-11-12; no reply yet. D-023 kept Stage 1A private and said non-commercial publication would need a new decision. Sri Lankan copyright law on government statistical tables has not been checked (memo E6).
- **Decision:** The lead's position: Census 2024 GN tables and values derived from them may be shown and redistributed **non-commercially**, with attribution and a notice, before DCS replies. Conditions:
  1. **Attribution** on every page, download and API response that carries census values: "Source: Department of Census and Statistics, Sri Lanka, Census of Population and Housing 2024 (provisional GN-level tables)."
  2. **Notice:** DCS has not published reuse terms; Sri Lanka Facts publishes these figures non-commercially for public information, has asked DCS for terms, and will correct or remove them on DCS's request.
  3. **Non-commercial only:** no paid product, paid API tier or client work uses these values until `commercial_reuse: yes` is recorded (data-model §2.4). Downloads carry the same notice.
  4. **No redistribution of the DCS source files**; link to the DCS page instead.
  5. **Takedown:** if DCS objects or sets terms that forbid this, census values come down or change to match within 7 days (confirmed by the lead 2026-11-12), and the outreach log records it.
- **What does not change:** the catalogue keeps `rights.status: unclear` and `commercial_reuse: unknown`, because no source text grants permission. This decision is a recorded risk position by the lead, not a licence. Values stay `machine_extracted` until checked (AGENTS rule 7).
- **Alternatives:** wait for DCS (rejected by the lead: replies may never come, and the blocker would not move); get legal advice first (recommended in D-023, not taken: cost; the risk is accepted with the takedown commitment above).
- **Consequences:** the rights blocker on Stage 1B is lifted for non-commercial publication. The release builder still refuses a public release when rights are `unclear`, so a code change must let a recorded lead decision (this entry) authorise a non-commercial public release that carries the notice. Until then, releases stay `publishable: false`. Public hosting is not set up yet (R2 and Vercel are deferred by the lead), so nothing is public today. The 1B exit requirements (D-027, D-028) still apply.
- **Revisit when:** DCS replies; a lawyer reviews the position; or any commercial use is planned.
- **Implemented (2026-11-12):** the dataset's catalogue entry has a `publication` block (decision D-030, non-commercial, attribution, notice, 7-day takedown). The release builder allows a public build of an `unclear`-rights dataset only when that block names a decision marked Accepted in this log. Such a build has `use: non_commercial` and the attribution and notice in every API response, in `datapackage.json`, `CITATION.md` and `NOTICE.md`, and in the website header and footer. `rights.status` stays `unclear`. No public release has been built for hosting.
- **Related (2026-11-12):** the lead also accepted 22 low-risk DCS crosswalk matches (`catalog/geographies/manual-matches.csv`; analysis in `docs/research/geography/dcs-review-items-dating.md`).

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
