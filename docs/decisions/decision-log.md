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
- **Open for the lead:** may users include ethnicity and religion in *custom* similarity recipes? Recommendation: no in Stage 1–2; revisit with advisers. *(Amended by D-037: ethnicity and religion are now in the default DS-level profile.)*
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
- **Status:** Accepted · 2026-11-12 (decided by the lead) · Amends D-025 (the retention rule only)
- **Context:** D-025 approved PCA "with the eigenvalue/loading rule": keep axes with eigenvalue > 1. With equal block weights (each block scaled to total variance 1), the eigenvalues sum to 2, not 9. On the real data the largest eigenvalue is 0.715 at GN level and 0.874 at DS level, so v0.1 keeps **zero axes** and cannot be built ✅ (`docs/qa/profile-space-v0.2.md` §2). The build also shows two exact redundancies: the age shares sum to 100, and persons per housing unit is population ÷ housing units, so settlement size enters through both log population (demography) and log housing units (housing) ✅.
- **Decision:** v0.2 keeps the D-025 recipe but retains a component when its eigenvalue exceeds total weighted variance ÷ 9 (the same "above-average axis" idea as Kaiser's rule; 0.222 at DS, 0.213 at GN after winsorising) and it has at least 3 loadings with |loading| ≥ 0.3; cap 6. This keeps 3 axes at each level, explaining 74% (GN) and 81% (DS) of the weighted variance.
- **Alternatives:** (a) drop block weighting and use Kaiser on 9 standardised inputs (demography's six inputs then dominate housing's three, which D-025 rejected); (b) a fixed number of axes, e.g. 3 (simple, but not tied to the data); (c) also drop occupied housing units, which is redundant given population and persons per unit, so the housing block stops counting size a second time (changes the inputs, so it is a v0.3 question).
- **Consequences:** `slf profile build` produces vectors, similar places with exact reasons, distance from the centre, bordering-unit contrasts and a sensitivity check (A03 steps 2–6). Nothing is in a release or on the website. **GN neighbour lists are unstable:** removing either block leaves about 2% of each GN's top-20 unchanged (DS: 27–38%), so GN "similar places" should not be published as robust without a further check. Axis labels are machine drafts until the lead writes them.
- **Revisit when:** the amenity or education/work tables arrive; or user testing shows the axes are unreadable.

## D-030: Census 2024 tables may be published non-commercially, with attribution and a notice, while DCS has not replied
- **Status:** Accepted · 2026-11-12 (decided by the lead) · Amends D-023 (the "stays private" part) · Amended by D-032 (scope)
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


## D-031: Publish similar places for DS divisions, not for GN divisions, until GN lists are stable
- **Status:** Accepted · 2026-11-12 (decided by the lead)
- **Context:** The profile space v0.2 (D-029) gives every GN and DS a top-20 list of similar places. The stability checks (`docs/qa/profile-space-v0.2.md` §4b) show:
  - The axes are stable ✅: refitting on resampled places leaves 89% of GN lists and 93% of DS lists unchanged.
  - DS lists are robust to ordinary small-number variation ✅: 84% unchanged when every count is redrawn from a Poisson distribution with the published count as its mean.
  - GN lists are not ✅: 13% unchanged. A typical GN moves 0.32 in the space under that variation, while its 20th-nearest neighbour is 0.16 away. GNs with 5,000+ people keep 61% (346 GNs); GNs under 2,000 people keep 7–9%.
- **Decision:** For 1B, the website and API show:
  - similar places, with reasons, for DS divisions;
  - for GN divisions: the GN's position on the profile axes and its distance from the national centre, plus a link to its DS division's similar places. No GN similar-places list.
  - The GN vectors stay in the build for analysis. They are not shown as a list.
- **Alternatives:** (a) show GN lists with a "low stability" label (rejected: most of each list would change under ordinary variation, and a label rarely survives a screenshot); (b) show GN lists only for GNs with 5,000+ people (possible, but covers only 346 of 13,934 GNs); (c) build GN lists from smoothed values, such as the empirical Bayes rates the census build already computes, then re-test (worth trying; a separate change); (d) group GNs into broad types (A03 step 7, Stage 2) and show "GNs of the same type" rather than a ranked list.
- **Consequences:** GN pages carry the stable parts of the profile and point to DS comparisons. GN lists can return when a version passes the same stability test, for example option (c) or (d).
- **Revisit when:** a smoothed or typology-based GN comparison is tested, or user testing shows people need GN-to-GN comparisons.

## D-032: D-030 also covers the Census 2024 topic tables; households and amenities are ingested first
- **Status:** Accepted · 2026-11-12 (decided by the lead) · Amends D-030 (scope only)
- **Context:** D-030 lets the Census 2024 "GN tables" be published non-commercially with attribution, a notice and a 7-day takedown. The other CPH 2024 tables on the same DCS page are now snapshotted and checked ✅ (`docs/research/sources/dcs-census-2024-topic-tables.md`): GN tables for households and amenities, ethnicity, religion, five-year age, sector and local authority type, and DS and district tables (A-series, OHU_DS, HH_DS). They come from the same source, under the same missing terms ❌.
- **Decision:**
  1. D-030's position and all five of its conditions apply to dataset `census-2024-topic-tables`, at GN, DS and district level. The notice text is unchanged. The attribution names the tables used, not only "GN-level tables".
  2. Ingest order: (a) households and the four amenity groups (drinking water, cooking fuel, lighting, toilet) at GN level; (b) five-year age, sector and local authority type at GN level; (c) DS and district housing unit structure and wall, roof and floor materials; (d) ethnicity and religion, under D-033. Each step is its own branch and PR, with a QA report.
- **Alternatives:** a separate decision with its own terms (rejected: same source, same risk); keep these tables private until DCS replies (rejected for the same reasons as in D-030).
- **Consequences:** the catalogue entry gets a `publication` block naming D-030 and this entry. `rights.status` stays `unclear` and `commercial_reuse` stays `unknown`. Nothing is published until hosting exists and each topic is ingested, checked and in a release.
- **Revisit when:** DCS replies, or with D-030.

## D-033: Ethnicity and religion are shown at DS and district level only, from DCS's own tables, neutrally
- **Status:** Superseded by D-036 · 2026-11-15 (was Accepted 2026-11-12, decided by the lead)
- **Context:** DCS's GN files for ethnicity and religion move any group with fewer than 10 people in a GN into "Other" and show `-` in its cell ✅ (101,464 such cells for ethnicity, 39,241 for religion). Summing GNs therefore under-counts small groups: Burgher is 25,159 from GN sums against 31,721 in DCS's district table A2 ✅. D-015 keeps ethnicity and religion out of the profile space but says nothing about showing them as indicators. They are sensitive (AGENTS rule 12).
- **Decision:** For 1B:
  - Ethnicity and religion are shown for DS divisions, districts, provinces and the country, using DCS's own DS and district tables (A2, A3, A6, A7), never sums of GN values.
  - Labels follow DCS's category names. Values are counts and shares, with the source table named.
  - No rankings, "most/least" lists, maps coloured by a single group's share, or similarity or profile use.
  - GN-level ethnicity and religion are not shown. They may be ingested for QA, but stay out of releases until the lead agrees how to show `-` ("fewer than 10, counted in Other").
- **Alternatives:** (a) show GN values with `-` labelled (rejected for now: the folding hides small communities in exactly the places where they are few, and a label rarely survives a screenshot); (b) leave ethnicity and religion out of 1B entirely (possible, but DS and district values are standard, published DCS figures); (c) derive DS values by summing GNs (rejected: wrong, as shown above).
- **Consequences:** the ethnicity and religion ingest (D-032 step d) reads the A-series tables, which are DS and district level only. The website needs a neutral presentation for these two topics, separate from the ranked indicator views. No thematic map for these two topics in 1B.
- **Revisit when:** there is a proposed way to show folded GN cells; DCS publishes unfolded GN tables; or user testing asks for it.

## D-034: Downloads are served from Cloudflare R2 (r2.dev for now); the website is deployed to Vercel as a prebuilt build
- **Status:** Accepted · 2026-11-14 (proposed); accepted by the lead 2026-11-16 (builds on D-007, D-030, D-032)
- **Context:** The first public release `v2026.11.14` (2.1 GB, 15,922 files, non-commercial per D-030 and D-032) is being uploaded with `slf upload`. The lead needs a place for the files and a way to show the website. The site reads the release from local files at build time (`SLF_RELEASE_DIR`), so a Vercel build from Git alone has no data.
- **Decision:**
  - Release files live in the R2 bucket `srilankafacts-data` under `releases/<version>/`, public read through the bucket's `r2.dev` address for now. A custom domain comes later.
  - R2 clients use region `auto` and the account endpoint **without** the bucket in the path. Keys are never overwritten.
  - `slf upload` puts a release there; `slf verify-upload` (read-only) proves the bucket matches the local release: file count, sizes, MD5 for single-part ETags, and a sampled SHA-256 download against `CHECKSUMS.sha256`.
  - The website is deployed to Vercel as a prebuilt deploy: `vercel build` then `vercel deploy --prebuilt`, run locally with `SLF_RELEASE_DIR` pointing at the release folder.
- **Alternatives:** build on Vercel from Git (rejected: no release data in the repository); serve everything from Vercel (rejected: size); put the release in Git (rejected: 2.1 GB).
- **Consequences:** r2.dev is rate-limited and meant for testing, so it is acceptable for a non-commercial preview but not for launch. ❓ Open risk, not verified: the 857 MB `api/` folder may exceed Vercel's deployment size or file-count limits. If it does, the site must fetch `api/` from R2 instead of bundling it, which is a code change.
- **Revisit when:** the Vercel prebuilt deploy is tried and passes or fails on size; before launch (custom domain for R2, rate limits); or D-030 changes.
- **Superseded 2026-11-19 by D-053** (free static hosting on Cloudflare Workers; no R2, no Vercel).

## D-035: Indicator drill-down charts are hand-written SVG; the hierarchy ships as a compact `hierarchy.json`
- **Status:** Accepted · 2026-11-15 (proposed); accepted by the lead 2026-11-16 (builds on D-007, D-027, D-033)
- **Context:** `/indicators` was a text list. The lead wants charts that drill from the country to the GN division with dropdowns. D-007 leaves the chart library "pending spike"; no spike has run.
- **Decision:**
  - `/indicators` gets a client-side explorer: indicator select, cascading province / district / DS / GN selects, a ranked bar chart and histogram of the next level down, and a "Show as table" under the charts. Bars are clickable to drill in. The server-rendered topic list stays on the page as the no-JS fallback (D-027).
  - Charts are plain SVG components in `web/src/components/charts/`; no chart dependency is added.
  - `web/scripts/prepare-release.mjs` writes `public/release/hierarchy.json` (id, name, parent, level; about 0.6 MB for 14,418 areas) so the browser does not load the 2.5 MB spine.
  - Values come from the existing `api/v1/indicators/{id}/{level}.json` files, fetched on demand. GN files are about 1.4 MB per indicator, loaded only when the GN level is reached.
- **Alternatives:** Observable Plot (deferred until the W01 spike; revisit if more chart types are needed); per-DS GN shards (a pipeline and API change, not needed at this size).
- **Consequences:** Only `api` indicators appear (D-033 exclusions unchanged). 37 indicators have no GN level and stop at DS. The GN files are not sharded, so the first GN view of an indicator downloads its whole GN file.
- **Revisit when:** the W01 chart spike runs, or GN loading proves too slow on mobile.

---

## D-036: Ethnicity and religion are ordinary indicators, at the levels DCS publishes them (supersedes D-033)
- **Status:** Accepted · 2026-11-15 (decided by the lead)
- **Context:** D-033 showed ethnicity and religion on place pages only, with no indicator pages, rankings, maps, charts or neighbour comparisons. The lead decided they should not be excluded: they are published DCS census figures and readers expect to explore them like any other topic.
- **Decision:**
  - The 32 ethnicity and religion indicators (`distribution: api`) get indicator pages, rankings, maps, drill-down charts and pies, downloads, and spatial-context statistics, like every other indicator.
  - Unchanged from D-033, because it is a data limit, not a presentation policy: values come from DCS's own DS and district tables (A2, A3, A6, A7), never from sums of GN values, and use DCS's category names. They exist for DS divisions, districts, provinces and the country. There is no GN level, because DCS's GN files fold groups of fewer than 10 people into "Other" (101,464 ethnicity cells and 39,241 religion cells ✅ per D-033). Showing GN values needs the folded cells ingested and labelled; that is a separate piece of work and decision.
  - Wording stays neutral (AGENTS rule 12): counts and shares with the source table named, no judgement. Ranking by a single group's share is allowed; the pages carry the standard "counts reflect population size" caution.
  - Not changed here: D-015 keeps ethnicity and religion out of the profile vector space and similar-place lists. Distances are still never used to infer relations (rule 13). If the lead wants them in the profile space, that needs its own decision.
- **Alternatives:** keep D-033's restrictions (rejected by the lead); also show folded GN values now (not done: needs a labelling design, see D-033 alternative (a)).
- **Consequences:** `distribution: places_only` stays a valid mode but no indicator uses it. The release must be rebuilt for the change to appear; the already-published `v2026.11.14` still carries the D-033 behaviour. The place page keeps its own ethnic group and religion section in DCS's order, now with links to indicator pages.
- **Revisit when:** DCS publishes unfolded GN tables, or a labelled way to show folded GN cells is agreed, or the lead decides on D-015 for these topics.

---

## D-037: Ethnicity and religion enter the DS-level profile space (amends D-015, D-025; profile v0.3)
- **Status:** Accepted · 2026-11-15 (the lead decided that ethnicity and religion go into the profile space; the recipe details below are the agent's proposal for the lead to review)
- **Context:** D-015 excluded ethnicity and religion from default profiles. D-036 made them ordinary indicators. The lead then decided they should also be in the profile space. DCS publishes them for DS divisions and larger areas only (D-033, D-036), so a GN-level input does not exist.
- **Decision:**
  - Profile v0.3 adds a third block, `identity`, at **DS level only**: the 10 ethnic-group and 6 religion categories (DCS's names). Each count becomes its share of its own topic's total, then the square root of the percentage (variance-stabilising; keeps zero counts defined). The block has equal weight with demography and housing (the existing rule, D-025), so each block carries one third of the variance.
  - The **GN space is unchanged** (v0.2's nine inputs). GN similar-place lists are still not published (D-031).
  - DS similar-place lists and "most alike / most different" reasons may now name identity inputs, labelled with DCS's category names. Wording stays neutral (AGENTS rule 12); a distance is never a ranking or a fact about people (rule 13).
  - `catalog/spaces/profile.yaml` v0.3 has `excludes: []`; the schema guard now refuses an input only if the recipe also lists its group in `excludes`.
- **Alternatives:** a separate DS-only identity space (more machinery; two spaces to explain); a lower weight for the identity block (a judgement the lead has not made; equal weight is the existing rule); log-ratio transform (breaks on zero counts, which occur for small groups).
- **Consequences:** ✅ measured on the real data (DS, 339 places, 5 retained axes against 3 in v0.2; GN 13,934 places and 3 axes, unchanged):
  - Removing the identity block keeps on average 62% of each DS top-20 list (the block matters a lot: about 38% of neighbours change). Removing demography keeps 55%, housing 49%.
  - Refitting on resampled places keeps on average 73% of a DS top-20 list (minimum run 47%), against 93% (minimum 84%) in v0.2: **DS lists are less stable under refitting with the identity block.**
  - Redrawing counts from a Poisson distribution keeps 88% (v0.2: 84%).
  - The 16 identity inputs spread over axes 4 and 6; axis labels are still machine drafts needing the lead's wording.
  - The default DS similar-place lists on the website change, so compare before publishing.
  - Not built: custom user recipes (Stage 2), a GN identity input.
- **Revisit when:** the lead reviews the weight and transformation; user testing shows the identity block dominates similar-place lists; DCS publishes unfolded GN tables.

## D-038: Census history: the 2012 GN file is used from a mirror; retired 2012 DS units get vintage ids; comparisons carry exact/approximate
- **Status:** Accepted · 2026-11-15 (proposed); accepted by the lead 2026-11-16 (G06 v2; builds on D-008, D-019, D-021, D-022, data-model §3.3)
- **Context:** Comparing the 2012 and 2024 censuses by DS needs DCS's 2012 list of GNs in each DS. DCS publishes 2012 DS totals (Statistical Abstract 2024 Table 2.7), but the GN-level file ("Population by GN division and sex 2012", authored by DCS in 2015) could not be found on any DCS address, live or archived. The only copy found is in `nuuuwan/lk_census_2012`. D-008 makes nuuuwan a cross-check, not an authority. The 2012 file has no DS or GN codes, only names and DCS GN numbers, and 9 DS divisions were created between the censuses (331 → 340).
- **Decision:**
  - Use the mirrored PDF as a copy of a **DCS document** (not as nuuuwan's data): snapshot it from a pinned commit, parse it ourselves, record the mirror in provenance, and accept it because every one of its 331 DS totals equals DCS's own Table 2.7 and every district total equals the 2024 Final Report. Its GN-level values are used only to classify DS changes and to rebuild 2012 populations on 2024 DS boundaries; they are **not published** at GN level. nuuuwan's own parse and ids are not used.
  - Match 2012 GNs to 2024 GNs only inside the same district, on DCS GN number and name (four layers, each requiring a unique key on both sides). Unmatched GNs are listed, never forced.
  - A 2012 DS that was **split** (or merged) is retired and gets a vintage id `LK-ADM3-V2012-<district code>-<order in the DCS 2012 table>`, never reused; every other 2012 DS continues under its 2024 spine id (renames and GN transfers keep identity). Retired units get `succeeded_by`/`preceded_by` edges weighted by 2012 GN population (`catalog/geographies/relations/succession_ds_2012-2024.csv`, vintage `2012-2024`).
  - Every 2012↔2024 DS comparison is labelled: `exact` only when the GN lists are identical (a rename alone stays exact); otherwise `approximate` with its method (`gn_reaggregation` or `same_ds_total_gns_unverified`). Closed groups of units (for example Kothmale → Kothmale West + East) are compared `exact` at group level.
  - The district series labels every year before 2001 `approximate` against 2024 districts, because DCS records districts being created and abolished; 2001 estimates are `approximate`; where two DCS tables disagree (1981, 2001), both are kept (D-019).
- **Alternatives:** wait for DCS to supply the 2012 GN file (rejected for analysis; kept as the route to publication); compare only districts (rejected: loses the DS view the roadmap asks for); use nuuuwan's region ids (rejected: assigned by name matching to a later list); area-weighted crosswalk from COD-AB geometry (rejected: no 2012 boundaries; G06 forbids drawing).
- **Consequences:** The 2012↔2024 DS comparison exists privately; nothing is published until the lead extends D-030 to `census-2012-tables` and `census-district-series` (or DCS replies). If DCS supplies the original 2012 file, its sha256 is compared with the mirror and provenance switches to DCS. The question is in the draft `docs/outreach/2026-11-15-dcs-census-history-queries.md`.
- **Revisit when:** DCS publishes or sends the 2012 GN file or a 2012↔2024 concordance; the lead decides on publication; a later census adds a vintage.

---

## D-039: Election Commission results may be published non-commercially, with attribution and a notice (as D-030 for DCS)
- **Status:** Accepted · 2026-11-15 (proposed); accepted by the lead 2026-11-16 (agent proposal) · Builds on D-030
- **Context:** The 2024 presidential results by polling division (PD) and electoral district (ED) are ingested and checked ([QA](../qa/election-results-pre-2024.md)). 7,593 of 7,644 sheet values are read; all agree with nuuuwan's extraction, and our ED and national sums match the Commission's own district and all-island sheets (879 of 879). The Commission publishes no terms of use ✅ ([rights memo](../research/rights/election-results.md) E1–E3). A letter asking for terms is drafted, not sent. Rights stay `unclear`, so the catalogue refuses publication.
- **Decision (proposed):** the same position the lead took for DCS in D-030, applied to `election-results`:
  1. Attribution on every page, download and API response: "Source: Election Commission of Sri Lanka, Presidential Election 2024, official results by polling division and postal votes by electoral district (elections.gov.lk)."
  2. Notice: the Commission has not published reuse terms; Sri Lanka Facts publishes these results non-commercially for public information, has asked for terms, and will correct or remove them on the Commission's request.
  3. Non-commercial only. No redistribution of the Commission's PDFs (link to its page).
  4. Takedown within 7 days on objection.
  5. Values stay `machine_extracted`. The 51 unread or withheld cells stay `not_available` until the lead's verification sheet fills them.
  6. Neutral presentation (AGENTS rule 12; [live-events §3](../architecture/live-events-and-sources.md#3-election-results)): no party-favourable colours, no inference about how groups voted.
- **Alternatives:** wait for the Commission (results stay private); publish ED and national totals only (smaller exposure, less use).
- **Consequences:** if Accepted, the dataset gets a `publication` block naming this entry, and the release builder can include it. The website still needs a neutral results view (not built).
- **Revisit when:** the Commission replies; a lawyer reviews whether official results are protected at all ([memo](../research/rights/election-results.md) E7).

## D-040: Polling divisions have ids and results but no GN composition until an official list exists; nuuuwan's GN→PD list is internal QA only
- **Status:** Accepted · 2026-11-15 (proposed); accepted by the lead 2026-11-16 (agent proposal)
- **Context:** G05 needs each non-admin unit composed of GNs with weights. For the 22 EDs this is exact: each is one or more whole districts (Jaffna = Jaffna + Kilinochchi; Vanni = Mannar + Vavuniya + Mullaitivu; 🟡 secondary source, consistent with the register ✅ and with nuuuwan for 13,620 of 13,620 GNs ✅). For the 160 PDs:
  - no official GN list or PD boundary file with known rights is public ([rights memo](../research/rights/election-results.md));
  - nuuuwan's `gig-data` has a GN→PD list, but no licence and no stated origin;
  - our checks show the list is unreliable: 423 spine GNs have no PD; for 21 PDs, nuuuwan's own shape and GN list overlap with IoU below 0.9; electors per 100 adults range from 40 to 655 ([QA](../qa/electoral-geography-ec-2024.md)).
- **Decision (proposed):**
  - ED and PD ids (`LK-ED-NN`, `LK-PD-NNX`), Commission codes and PD→ED `parent` edges go in the catalogue.
  - ED `composed_of` districts (weight 1). ED denominators are the districts' census totals (exact).
  - **No PD `composed_of` relations and no PD denominators are published.** nuuuwan's list stays in the local build for QA only.
  - PD results (counts, shares, turnout) remain usable without denominators.
  - Ask the Commission for its GN list per PD (letter drafted).
- **Alternatives:** use nuuuwan's list with a "modelled" label (rejected: no licence, and the checks show errors); overlay nuuuwan's PD shapes (same rights problem, and the shapes disagree with the list); digitise PD maps ourselves (large effort, unknown source rights).
- **Consequences:** there are no per-capita PD figures or PD-to-census-profile links yet, so the "results linked to census profiles" part of the election atlas works at ED level only for now.
- **Revisit when:** the Commission (or Survey Department) provides a GN list or boundaries with terms.

## D-041: Scanned PDFs may be read with on-device Vision OCR (macOS), with arithmetic checks, instead of a new Python dependency
- **Status:** Accepted · 2026-11-15 (proposed); accepted by the lead 2026-11-16 (agent proposal; AGENTS rule 8)
- **Context:** Many 2024 result sheets are scans; some have no text layer at all. The pipeline has no PDF or OCR library. The repo already uses `scripts/pdf_pages.swift` (PDFKit, macOS) for audits.
- **Decision (proposed):** `pipeline/scripts/pdf_ocr.swift` (PDFKit text plus Apple Vision OCR: whole page, right half and votes column) produces page text in the build folder, compiled once by the pipeline. Nothing leaves the machine. Values are accepted only through checks on the sheet itself (printed percentages, totals, sum rules); anything unconfirmed is `not_available` and goes to a verification sheet. No new Python dependency. Extraction runs on macOS only; CI and tests use fixtures.
- **Alternatives:** Tesseract or a Python OCR stack (new system and Python dependencies, unknown accuracy on these sheets); an external AI service (D02 allows it for statistical tables, but it adds cost and data transfer, and is not needed at 99.3% read with checks); manual entry (7,644 values).
- **Consequences:** building `election-results` from scratch needs a Mac; the page text is cached by snapshot sha256. If accuracy on other PDF sources is worse, revisit.
- **Revisit when:** a Linux build of this dataset is needed, or another PDF source fails these checks.

---

## D-042: The home page is the map-first atlas, fed by a derived "atlas bundle" outside the release
- **Status:** Accepted · 2026-11-17 (agent proposal; the lead said on 2026-11-17 to follow the recommended decisions; builds on D-002, D-003, D-013 to D-016, D-031, D-035)
- **Context:** The lead asked for the site to open on an immersive map with four lenses (Geography, Profile, Change, Landscape), contextual comparisons and clean shared borders. The release boundaries are simplified per polygon, which leaves 130 km² of overlaps and about 84 km² of false gaps in the DS layer ([QA](../qa/atlas-2026-11-17.md)). The website also had no neighbour graph or profile vectors in a browser-readable form.
- **Decision (proposed):**
  - `/` is the atlas. The former home page moves to `/about`. Place, indicator, table, data and methods pages keep their URLs and server rendering (D-002); `/` has a readable no-JavaScript summary.
  - A new pipeline command, `slf atlas export`, writes a **derived bundle** (display geometry simplified as a coverage with a ranked border mesh, the spine's neighbour graph, significant cluster lists, the DS profile space, census change) to `pipeline/data/build/atlas/<release>/`. It is not part of the release, changes no release file or checksum, and is copied into the site only when it names the same release.
  - Similarity in the browser is distance in the pipeline's `profile` space, nothing else. Similar-place lists stay DS-only (D-031).
  - The Change lens reads the local history build and says so. **It must not ship in a public build until the lead extends D-030 to the history datasets** (D-038 covers local use only).
  - The Landscape lens states that no dataset exists; it shows no estimate.
  - No new runtime dependency: MapLibre and hand-written SVG as before (D-035).
- **Alternatives:** fix simplification in the release builder (better long term, but it changes every release's boundary files and checksums; proposed as a follow-up); PMTiles for geometry (needs Tippecanoe and a tile reader; revisit if GN detail files prove too heavy); keep the hero home page and put the atlas at `/explore` (does not meet the map-first brief).
- **Consequences:** the atlas needs the bundle; CI's fixture has none and shows the summary. The bundle is 44 MB uncompressed, which matters for the hosting decision. `/explore`, indicator and place-page maps still use the release boundaries.
- **Revisit when:** hosting is chosen (bundle size, compression); the release builder adopts coverage simplification; a landscape or feature dataset is admitted; the lead reviews the axis names and the Change lens rights.

---

## D-043: Release boundaries are simplified as a coverage, so neighbours share identical edges
- **Status:** Proposed · 2026-11-17 (agent proposal, acted on under the lead's instruction of 2026-11-17 to follow recommended decisions; follows D-042)
- **Context:** The release builder simplified each polygon on its own. In `v2026.11.17-preview.2` that left overlaps between neighbours of 100 km² (provinces), 61 km² (districts), 130 km² (DS) and 458 km² (GN), and false gaps of similar size. D-042 fixed this for the atlas only.
- **Decision:** `slf release` simplifies the GN divisions as one coverage (60 m, EPSG:5235) and the DS divisions as one coverage (150 m); districts, provinces and the country are dissolved from the simplified DS divisions. Coordinates are rounded to 6 decimals. Units outside the GN coverage (today only the provisional `LK-ADM3-P0001`) keep per-polygon simplification and are listed in the release warnings. Areas, adjacency and every statistic still come from the full-resolution spine.
- **Alternatives:** keep per-polygon simplification (rejected: visible seams, wrong point-in-polygon answers near borders); publish full-resolution boundaries (rejected: about 60 MB for the web).
- **Consequences:** every `boundaries/*.geojson` and `geographies.gpkg` checksum changes from `v2026.11.17-preview.3`. Measured there: 0 km² overlap at levels 0, 1, 2 and 4; 12.75 km² at level 3, all of it the provisional unit lying over its parent, as designed (D-022); remaining holes are the 83.7 km² already in COD-AB. `admin4` grows from 11.8 MB to 16.1 MB. Higher levels are now built from GN polygons, not from COD-AB's own higher-level polygons.
- **Revisit when:** boundary vintages are added; PMTiles replace GeoJSON; the lead or a GIS reviewer objects to dissolved higher levels.

---

## D-044: Open spatial layers are rolled up onto GN divisions as modelled estimates; raw files may live on an external root
- **Status:** Proposed · 2026-11-17 (agent proposal; builds on D-013, D-016, D-017, D-018)
- **Context:** The brief asked for the open spatial layers (terrain, land cover, tree cover, surface water, built-up history, buildings, schools, health sites, places) to become indicators without a new backend.
- **Decision (proposed):** `slf spatial build` computes zonal statistics on each source's own grid and stores only additive components per GN division (areas, counts, sums); shares and means are recomputed at every level. Rows are `data_nature: modelled_estimate`, `verification: machine_extracted`, and carry their information floor. ODbL-derived outputs (Overture buildings, OSM) stay apart from CC BY outputs (D-005). Raw snapshots may be held on an external root (`SLF_DATA_DIR`, `--data-root`); the layout and immutability rules are unchanged. Sources with restricted redistribution (HydroSHEDS, WDPA, Ookla, Meta RWI, DHS on HDX) are held or listed but not republished.
- **Alternatives:** publish raster tiles (needs hosting and a tile stack); sample points instead of zones (loses area-weighting).
- **Consequences:** 69 new indicator definitions; builds need the external drive for Overture extracts.
- **Revisit when:** the lead reviews the indicator list and licences, or hosting is chosen.

---

## D-045: Landscape space v0.1 recipe (profile method, 85% variance retention)
- **Status:** Proposed · 2026-11-17 (agent proposal; builds on D-014, D-029)
- **Context:** The landscape space reuses `slf.profile.fit`. D-029's retention rule kept one axis at DS level, giving nonsense neighbours (for example Kaduwela similar to Kuchchaweli).
- **Decision (proposed):** nine inputs in three blocks (terrain, cover, change), transformed as in `docs/methods/landscape.md`; keep the fewest axes that explain 85% of the variance, at most 6. Axis labels are machine-generated drafts until the lead names them.
- **Alternatives:** keep D-029's rule (collapses the space); fixed number of axes (arbitrary).
- **Consequences:** landscape neighbours and the cross-space comparison with profile v0.3 are available locally; nothing is published.
- **Revisit when:** the lead approves or changes the inputs, or more layers join the space.

---

## D-046: Elections in the atlas at electoral-district level; local authorities and MOH areas wait for an official GN list
- **Status:** Proposed · 2026-11-17 (agent proposal, acted on under the lead's autonomous instruction of 2026-11-17; builds on D-004, D-021, D-039, D-040, D-042)
- **Context:** Stage 2 asks for election pages and an atlas view, and for local authorities (LA) and MOH areas as GN compositions with denominators (G05). The 2024 presidential results are in the release (D-039). No LA or MOH unit list, GN list or boundary with recorded rights is held; the only source with per-GN LA and MOH ids is nuuuwan `gig-data`, which has no licence.
- **Decision (proposed):**
  - The atlas gets an **Elections lens** at electoral-district (ED) level and pages at `/elections`. ED geometry is dissolved from the districts (EDs are whole districts). The map shows only whole-election measures (turnout, rejected ballots, electors, valid votes), never a candidate's share; candidates keep ballot order; unread values say "not read". Polling divisions stay in tables (D-040).
  - A generic `slf composition build` composes any GN-based scheme from a unit list and a membership list, with G05's checks, and writes to `catalog/` **only** when the membership dataset's rights allow publication. Until then LA and MOH are built internally from gig-data for QA, nothing is committed, and the atlas shows LA and MOH as unavailable with the reason.
- **Alternatives:** map candidate shares (rejected: invites a partisan reading and adds nothing a table does not give); publish gig-data LA/MOH (rejected: no licence, and the QA finds gaps and mismatches); area overlays from an unlicensed shape (rejected: same rights problem).
- **Consequences:** the atlas bundle grows by about 2.4 MB (ED mesh, outlines, results). LA- and MOH-level indicators (for example dengue by MOH) cannot be published until an official list is obtained.
- **Revisit when:** an official GN list per local authority or MOH area is held with rights recorded; more elections are ingested; the lead reviews whether turnout maps are acceptable under D-039.

---

## D-047: Vector spaces v2: typology, trajectory (private), composite weights, text search, and the two-map explorer
- **Status:** Proposed · 2026-11-17 (agent proposal, acted on under the lead's autonomous instruction of 2026-11-17; builds on D-015, D-016, D-031, D-037, D-038, D-042)
- **Context:** Stage 2 asks for more vector spaces next to `profile` (vector-space-model.md) and the W08 two-map explorer. Inputs held: the DS profile v0.3, the history build (2012 DS population by sex, D-038) and the release's place names. No GN-level similar lists may be published (D-031).
- **Decision (proposed):**
  - `typology` v1.0: k-means on the DS profile vectors, k from 3 to 10, chosen as the highest silhouette among k with bootstrap stability (mean ARI) ≥ 0.75; result k = 5. Names are machine drafts from each type's back-projected inputs, tagged and awaiting review. Numbered by size, never ranked.
  - `trajectory` v0.1: DS change vectors (annual growth, change in the sex ratio) on the 320 divisions with a one-to-one 2012 predecessor, carrying exact/approximate. **Private under D-038**: local build and local bundle only, counts only in public docs.
  - `composite` v0.1: the profile space with a weight per block, applied in the browser to exact per-block contributions to each axis score, so equal weights are profile v0.3 and every distance still splits exactly by axis and by block.
  - `text` v0.1: character 2/3-gram TF-IDF vectors of English, Sinhala and Tamil names, cosine, used to order search results within the existing tiers and to let misspellings match (cosine ≥ 0.45). No model.
  - `/explore/space` (W08): the map beside a 2-D view of the first two axes, linked selection both ways, drag to select a group, four preset questions, sliders, exact explanations and a table that works without WebGL.
  - No new dependency: k-means, silhouette and ARI are plain NumPy.
- **Alternatives:** UMAP layout for the 2-D view (needs a new dependency and distorts distances; PCA axes are what the space is); hierarchical clustering (no stability advantage at this size); an embedding model for search (download, cost, opaque); GN-level types (D-031).
- **Consequences:** the atlas bundle grows by about 150 KB (`spaces/`). Three of the five type names lead with ethnic group or religion, because those inputs separate the groups most (D-037); this is sensitive and is the main item for review.
- **Amended 2026-11-19 (D-054):** type names no longer use ethnic group or religion.
- **Revisit when:** the lead reviews the type names; more 2012 DS topics are held (a richer trajectory); D-030 is extended to the history datasets; aliases are added to the spine.

---

## D-048: Analytic grid v1 is H3 resolution 9 with equal-share GN weights; drawn areas and the point resolver use it
- **Status:** Proposed · 2026-11-18 (agent proposal, acted on under the lead's instruction of 2026-11-17 to follow recommended decisions; implements D-014, G07 in part)
- **Context:** Stage 2 asks for drawn, radius and multi-unit areas and a point resolver. G07 asks for a weight source chosen on evidence (buildings or a population grid) and the lead's approval of it; that comparison is not done yet.
- **Decision:**
  - `slf grid build` makes H3 resolution 9 cells (about 0.105 km²) and assigns each to the GN division containing its centre; a GN too small to hold a cell centre gets the cell under its label point (63 GNs). Weights are **equal shares by area** (`weight_source: area_equal_share`). Adds the `h3` Python package (named in D-014 and G07).
  - The `/area` page estimates GN counts inside a circle or a drawn shape from these weights. Every estimate is labelled `modelled estimate` with its information floor (GN division), lists the divisions it cut and the share of each, and names divisions with no value instead of counting them as zero.
  - `slf resolve` answers point → GN, DS, district, province, electoral district from the full-resolution spine; the browser answers from the 30 m display geometry and says so.
  - Resolution 10 (the D-017 atom) is deferred: about 4 million cells, too heavy for the browser bundle; resolution 9 is a derived view and can be rebuilt.
- **Alternatives:** population-weighted cells from WorldPop, Kontur or buildings (better inside mixed GNs; waits for the G07 completeness report and rights checks); area-weighted polygon intersection (exact by area, but needs full polygons in the browser).
- **Consequences:** inside GNs where people cluster (a town beside paddy), equal shares misplace people; totals for whole GNs are exact. The grid files add 13.2 MB to the atlas bundle. Measured: weights sum to 1 for all 14,043 GNs (max error 7e-14); browser and exact lookups give the same GN for 1,998 of 2,000 random land points.
- **Revisit when:** a population or building weight source passes G07 steps 1 to 4; resolution 10 is needed; drawn areas move server-side.

---

## D-049: The Landscape lens shows the landscape roll-ups; named public features are drawn in the local preview only
- **Status:** Proposed · 2026-11-18 (agent proposal, acted on under the lead's instruction of 2026-11-17 to follow recommended decisions; builds on D-042, D-044, D-045)
- **Context:** D-042 left the Landscape lens empty because no landscape dataset existed. `slf spatial build` (D-044) now gives 69 indicators for every place, and its feature tables hold schools, health facilities, Wikidata and GeoNames points.
- **Decision:**
  - `slf atlas export --landscape-dir` copies 30 display indicators (terrain, land cover, trees, water, built-up and settlement, facilities and mapped places), each at its latest period, with its information floor, data nature, verification, dataset, snapshot hash, source locator and the catalogue's licence. Component rows (measured areas, class areas) are not shown. Nothing is recomputed.
  - The Landscape lens maps the chosen layer at the level in view and shows it against neighbours, parent, the 10 most similar landscapes (landscape space v0.1, D-045) and the country, always labelled "modelled estimate" with its floor.
  - Named features are drawn from zoom 11 for the selected district, and a GN or DS lists "what is here". Only schools (Giga), health facilities (healthsites.io/OSM), Wikidata places and GeoNames names; name and category only. Wikidata events, organisations and administrative units and GeoNames administrative entries are left out (counted in the manifest). Overture business listings stay counts. **Individual features are not part of any release** (D-044); this is a local preview feature until the lead decides.
- **Alternatives:** keep the lens empty until review (rejected: the data exists and is labelled); show Overture places by name (rejected: business names and uneven quality; counts suffice).
- **Consequences:** the atlas bundle grows by 7.6 MB (landscape) and 4.2 MB (features). Feature lists are incomplete and uneven by source; the panel says so.
- **Revisit when:** the lead reviews D-044/D-045 and the licences (ODbL for health facilities, Copernicus DEM licence recorded as "public licence", commercial use unconfirmed); a release admits landscape data.

---

## D-050: Stage 3 build-out: p-coded open indicators in the Geography lens, a local freshness monitor, and opt-in draft translations
- **Status:** Proposed · 2026-11-18 (agent proposal, acted on under the lead's instruction of 2026-11-17 to follow recommended decisions; builds on D-012, D-015, D-019, D-042)
- **Context:** Stage 3 asks for curated sub-national indicators, a freshness monitor and release calendar (D05), a national context strip and Sinhala and Tamil core pages (W07). Several sources are already held with rights recorded in the catalogue.
- **Decision:**
  - `slf subnational build` adds 12 indicators from tables that carry the spine's own p-codes: OPHI MPI 2016 (province, survey estimate, CC0), WFP/CHIRPS rainfall and WFP/MODIS NDVI for the latest complete year against their long-term averages (district and province, CC BY), and HeiGIT's Rural Access Index (district, CC BY-SA). The country rainfall and NDVI figures are pixel-weighted means of the district values; everything else is copied. They appear in the Geography lens under their own groups, each marked "not from the census" with its nature, period, floor and licence.
  - Not built: DesInventar (place names only; joining needs a crosswalk), HeiGIT travel-time tables (ISO 3166-2 codes; needs a code list with evidence), WFP market prices (points, not areas), the national context strip (no CBSL series is held).
  - `slf freshness` writes a release calendar from catalogue schedules and held snapshots; `--probe` adds polite HEAD checks of landing pages with a generic user agent. No scheduled workflow and no automatic issues: both are outward-facing and CI runs only by hand.
  - Interface strings move to a catalogue with machine drafts in Sinhala and Tamil, shown only when a visitor chooses them and always under a banner. No `/si` or `/ta` routes yet.
- **Alternatives:** a GitHub Actions schedule that opens issues (rejected for now: cost and outward action); an i18n routing library (deferred: new dependency, and nothing is reviewed to route to).
- **Consequences:** survey and modelled indicators sit next to census ones; the labels must keep them apart. Translations stay drafts until a reviewer is recorded in `docs/translation/README.md`.
- **Revisit when:** a translator reviews a locale; the lead wants automatic release alerts; CBSL or HIES tables are snapshotted; a crosswalk for DesInventar names exists.

---

## D-051: Distribution: a local MCP server, an evaluation set kept private, embeddable maps and SQL in the browser
- **Status:** Proposed · 2026-11-18 (agent proposal, acted on under the lead's instruction of 2026-11-17 to follow recommended decisions; builds on D-011, D-030, D-034)
- **Context:** Stage 2 asks for an MCP server and `llms.txt` (A01), a public AI evaluation set (A02), embeddable maps and charts, and a DuckDB-WASM or Datasette explorer.
- **Decision:**
  - `mcp/` is a read-only MCP server over the static API, run locally over stdio (`@modelcontextprotocol/sdk` 1.32.2, `zod` 3.25.76). Six tools; every value comes with unit, period, verification, dataset, source locator and citation; missing data is answered "not available". No hosted endpoint (hosting is undecided).
  - `slf evalset` generates questions with expected answers copied from a release; `mcp/eval/run.mjs` scores the server. **The generated set stays in `pipeline/data/build/evals/`, not in Git**: A02 asks for CC BY 4.0, but its answers are DCS values that D-030 allows only non-commercially. Only the generator, harness and results are committed.
  - `/embed/map` is a chrome-free map of one indicator with a credit line naming the source, the release and non-commercial use. Embeddable charts are not built.
  - `/query` runs SQL over the release's Parquet files with `@duckdb/duckdb-wasm` 1.32.0 in the browser; the engine (33 MB) and the Parquet files (13 MB) are copied into the site, not loaded from a third-party host.
- **Alternatives:** a hosted MCP endpoint (waits for hosting); Datasette (needs a server); loading DuckDB from a CDN (smaller site, but a third-party request on every use).
- **Consequences:** three new runtime dependencies. The site grows by about 46 MB, which matters for the hosting decision. The 150 of 150 score measures the tools, not an assistant.
- **Revisit when:** hosting is chosen; DCS publishes reuse terms (the evaluation set could then be published); outlets ask for chart embeds.

---

## D-052: Events layer v1 from held datasets; no live feeds and no Movement layer yet
- **Status:** Proposed · 2026-11-18 (agent proposal, acted on under the lead's instruction of 2026-11-17 to follow recommended decisions; builds on D-020, D-044)
- **Context:** The Stage 3 "Living Sri Lanka" track asks for an events layer and place timelines; the Stage 4 "Movement" track asks for estimated train positions from timetables. Held: UNOSAT's 2025 flood extent, NASA FIRMS fire detections, IBTrACS storm tracks. No train timetable or other movement data is held.
- **Decision:**
  - `slf events` builds three event layers by place: area and share flooded in Cyclone Ditwah (26 Nov to 2 Dec 2025, UNOSAT, every level down to GN), VIIRS fire detections per complete year 2013 to 2025 (DS and above), and storm tracks within 50 km of each district (IBTrACS). Flood and fire layers join the Geography lens under "Events"; the Change lens shows a fire series and recent storm passes for the selected place.
  - Every event value is labelled: floods are a lower bound (cloud and tree cover), a fire detection is a hot pixel, not a fire, and a storm passing within 50 km is not damage.
  - No scheduled or live feeds are set up: the freshness monitor (D-050) detects new editions, and snapshots stay manual. **No Movement layer is built**: there is no timetable data, and an empty layer would suggest a feature that does not exist.
- **Alternatives:** an hourly FIRMS feed (needs an API key and a scheduler; deferred); a placeholder Movement layer (rejected: it would mislead).
- **Consequences:** events are historical snapshots, not live. The landslide points and cloud-obstruction mask in the UNOSAT file are not used yet.
- **Revisit when:** a timetable source with clear rights is found (Sri Lanka Railways GTFS or similar); the lead wants near-real-time feeds and accepts a scheduler.

## D-053: Free hosting: the website and the data site as Cloudflare Workers static assets; large files on a GitHub release
- **Status:** Accepted · 2026-11-19 (lead: "prepare the deploy. check free usage limitations. don't make it cost me anything"; the design is the agent's) · Supersedes D-034's hosting choice; amends D-007 (Vercel Pro) and D-051 (DuckDB engine source on the static host)
- **Context:** D-034 chose Vercel (prebuilt deploys) for the site and R2 for files. Measured on 2026-11-19 ✅: the server build is about 840 MB of prerendered pages plus 140 MB of public files, and the release is 16,158 files and 2.2 GB, of which three files are over 100 MB. Vendor limits read the same day (🟡 from the vendors' pages): Vercel Hobby caps uploads at 100 MB and 15,000 files and allows non-commercial use only; R2's free tier (10 GB) sits behind an R2 subscription checkout; Cloudflare Workers static assets on the free plan allow 20,000 files per site and 25 MiB per file, with "requests to static assets free and unlimited"; GitHub Pages caps a site at 1 GB.
- **Decision:**
  - **Website:** a static export of `web/` (`pnpm build:static`): pages from country to DS division are prebuilt (6,840 files, 962 MB, largest 16.1 MB on `v2026.11.17-preview.3` ✅). GN pages (14,043) are not prebuilt: `/place/<GN id>` is served by `/place/gn`, which renders the same place view in the browser from the API. `_redirects` lists each prebuilt place page before the GN rule (Cloudflare applies rules before files). Deployed as an assets-only Worker `srilankafacts-site` (no Worker script).
  - **Data site:** the public release itself, hard-linked by `deploy/stage-data-site.mjs`, served as the assets-only Worker `srilankafacts-data` with `Access-Control-Allow-Origin: *`. The website reads the API from `NEXT_PUBLIC_DATA_BASE`.
  - **Large files:** files over 25 MiB (topic-tables CSV 1.03 GB, GN-tables CSV 103 MB, `geography_versions.geoparquet` 126 MB) go on a GitHub release of this public repository, linked from `/data` via `NEXT_PUBLIC_LARGE_FILES_BASE`. The Parquet copies of both tables stay on the data site.
  - **SQL engine:** the static site loads DuckDB-WASM 1.32.0 (33 MB, over the per-file limit) from jsDelivr's copy of the npm package (`NEXT_PUBLIC_DUCKDB_BASE`), only when a reader opens `/query`.
  - **Addresses:** the free `*.workers.dev` addresses first; a custom domain is optional and free if its DNS moves to Cloudflare.
  - **Tooling:** `wrangler` 4.156.0 run with `npx` at deploy time; not a project dependency.
  - Cache Components are switched off in the web app (static export cannot use partial prerendering); pages are unchanged.
- **Alternatives:** Vercel Hobby (100 MB upload limit; site alone is about 1 GB); Vercel Pro and R2 (cost money); GitHub Pages (1 GB site cap, release would not fit); Cloudflare Pages (same free limits: 20,000 files, 25 MiB per file); prebuilding GN pages (about 3 files each: over the file limit); serving DuckDB from the data site (over the per-file limit).
- **Consequences:** no running cost and no payment method needed for Workers or GitHub (🟡 not verified by signing up). GN pages need JavaScript (D-027's no-JavaScript rule now holds from country to DS level; GN pages are `noindex` and link their API file for readers without JavaScript). `/query` makes a request to jsDelivr. The data site's 16,156 files are under the 20,000 limit but could not be run in full in the local emulator (it fails above a few thousand files; a 3,003-file subset served correctly); the real upload is the first full check. If Cloudflare's free terms change, the same static folders can move to any static host.
- **Revisit when:** a release passes 20,000 files or the site passes 20,000 files; traffic or terms change; the lead wants a custom domain; a server becomes necessary (S01).

## D-054: The four launch decisions, as recommended by the agent
- **Status:** Accepted · 2026-11-19 (lead: "follow your recommendations on the four decisions") · Amends D-047; confirms D-038 and D-049 for public builds
- **Context:** The 2026-11-18 review queue listed four items blocking a public site: typology names, the 2012 census comparison, share-alike layers, and a public release.
- **Decision:**
  1. **Typology names (D-047):** names never use ethnic group or religion. They are drafted from age, sex, size and housing inputs only; the identity inputs still shape the types and stay listed in each type's input profile. Same partition as before (339 of 339 assignments unchanged ✅); the five names are in `docs/qa/typology-v1.0.md`. Still machine drafts awaiting review.
  2. **2012 census comparison (D-038):** stays private; D-030 is not extended. `slf atlas export --public` refuses a release that is not publishable and leaves out `change.json`, the `trajectory` space and named features (D-049).
  3. **Share-alike layers** (healthsites.io ODbL, HeiGIT CC BY-SA, UNOSAT CC BY-SA): allowed in public builds, each in its own file under its own licence and attribution (the atlas index and the place panel already carry both), never relicensed under the census's non-commercial terms.
  4. **Public release:** built with `slf release` without `--preview` once disk space allows (see the deploy guide); the website and data site are built from it.
- **Alternatives:** approve the original names (rejected: leads with ethnic group or religion); extend D-030 to the 2012 data (rejected for now: no reply from DCS); drop share-alike layers (loses the health access, risk and flood layers for no rights gain).
- **Consequences:** the public atlas has no Change lens history and no named features; the typology legend reads neutrally.
- **Revisit when:** DCS replies on reuse terms; a reviewer renames the types.

---

## D-055: Local-authority and MOH profile pages render only from a publishable composition
- **Status:** Accepted · 2026-11-21 (proposed by the agent; accepted by the lead 2026-11-21; builds on D-046, D-030, D-040)
- **Context:** `slf composition profile` now writes per-unit profiles (population, age, households, housing, rates recomputed from counts) from a composition build. The only membership source held, nuuuwan `gig-data`, has no licence. The internal run shows 423 spine GNs with no local authority and 986 with no MOH area, 97 local authorities and 88 MOH areas whose own shape overlaps their GN union poorly (IoU < 0.9), and 16 local authorities whose population DCS places mostly under another local-authority type.
- **Decision (proposed):** (1) the website route `/units/la` and `/units/moh` renders profiles only from a file marked `publishable: true`, which is written only when the membership dataset passes the rights gate (D-046); otherwise it says unavailable and why. (2) `gig-data` stays internal. (3) The profiles of a source that passes the gate must show the flags (coverage gaps, shape disagreement, DCS type mismatch) beside each unit.
- **Alternatives:** publish gig-data profiles under D-030-style terms (rejected: no stated origin, so no one to notify or credit, and the QA gaps above); hide flagged units (rejected: rule 6, show with the reason).
- **Consequences:** nothing public changes now. Publishing needs an official GN list per unit with rights recorded, plus copying `units-<scheme>.json` into `web/public/release/atlas/` (atlas export wiring is not done).
- **Revisit when:** an official GN list per local authority or MOH area is held with rights recorded.

---

## D-056: LA and MOH memberships from gig-data are published in the non-commercial preview, flagged
- **Status:** Accepted · 2026-11-21 (decided by the lead: "build the preview with no restrictions" until broader permissions are obtained; amends D-046 and D-055 on the rights gate only)
- **Context:** No official GN list per local authority or MOH area is held (D-046). The only membership source, nuuuwan `gig-data`, has no licence and no stated origin. The lead wants the preview to carry LA and MOH profiles now and to stay a preview until permissions are obtained.
- **Decision:** (1) A new catalogue entry `nuuuwan-gig-data-lg-moh` (`lg_id` and `moh_id` only) gets a `publication` block under this decision, as for D-030/D-032: non-commercial, attribution, notice, 7-day takedown; `rights.status` stays `unclear`. (2) LA and MOH compositions and profiles built from it are committed to `catalog/` and shown at `/units/la` and `/units/moh` with their known gaps and per-unit flags. (3) gig-data's polling-division columns stay local (D-040) and its shapes are not published. (4) The preview is non-commercial only; nothing is a commercial release.
- **Alternatives:** wait for an official list (rejected by the lead for the preview); also publish gig-data shapes (rejected: not needed for tables, and the IoU shows many disagree).
- **Consequences:** units show coverage gaps (423 GNs in no LA, 986 in no MOH area), flagged shape and type disagreements, and the notice. The site header/footer notice for D-030 is unchanged; the unit pages carry their own notice. An official list replaces this when obtained.
- **Revisit when:** an official GN list per local authority or MOH area is held; permissions are obtained; nuuuwan states a licence.

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
