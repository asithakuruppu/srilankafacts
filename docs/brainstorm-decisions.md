# Sri Lanka Facts — Brainstorm notes: ideas and decisions

> **Historical input (2026-11-07).** Current decisions live in [decisions/decision-log.md](decisions/decision-log.md), which overrides this file where they differ. The recommended direction is in [vision/vision-and-strategy.md](vision/vision-and-strategy.md). Start at [00-start-here.md](00-start-here.md).

Source: user's ChatGPT brainstorming session (pasted 2026-11-07) plus the user's own direction. **Part 2 (§11–20)** adds a second pasted blueprint covering institution, products, business model, launch scope and plan, read through the map-first direction. Items are labelled **Decided** (user stated), **Recommended** (ChatGPT proposed, not yet confirmed by the user) or **Open**. Claims from the chat I have not checked are marked ⚠️.

## 1. Product direction

- **Decided:** The website is **very visual, with an interactive map as the base layer** and a **fluid, animated, high-tech looking UI**. (User, latest message.)
- Sri Lanka Facts is a national data platform, partly inspired by USAFacts.
- **Recommended:** Treat the map as the **geographic foundation** for everything else (education, health, agriculture, transport, economy, demographics). Selecting any area should eventually show all indicators for it.
- **Recommended first project ("Project 001"): Sri Lanka Administrative Atlas.** Scope: country, 9 provinces, 25 districts, all DS divisions, GN divisions, roads and railways, rivers and water bodies, population by area. Build the complete atlas first, not a single thematic map.

## 2. Source inventory (starting register)

Critical: Dept of Census and Statistics (statistics.gov.lk, incl. LankaStatMAP, NADA, digital library, route to request unpublished data/microdata), Central Bank of Sri Lanka, Sri Lanka Open Data Portal (data.gov.lk), Treasury / Ministry of Finance, Government portal, National Spatial Data Infrastructure (NSDI).
High: Parliament, Auditor General, Government Printing Dept (gazettes), National Archives.

- **Decided approach (recommended by chat):** keep a master register that records, per source, whether it offers downloadable datasets, PDF-only reports, an API, or data only on request. Do not treat every website as an accessible dataset.
- Much data is buried in annual reports, statistical abstracts and departmental PDFs.

## 3. Geographic data sources

- **NSDI geoportal** (WMS services and a catalogue). **ArcGIS REST boundaries service:** `gisapps.nsdi.gov.lk/server/rest/services/Srilanka/Boundaries/MapServer` — GN, DS, district, province, forest and country layers; supports JSON/GeoJSON queries. It is a live service, not a download package. ⚠️ not verified by me.
- **Survey Department:** authoritative base maps and finer boundaries (1:50,000 topographic data).
- **OpenStreetMap** via Geofabrik for roads, rail, buildings, POIs. **ODbL attribution and share-alike must be checked before redistribution.**
- **UN SALB:** cross-check and historical admin units (GeoJSON, Shapefile, REST). Licence noted as CC BY-IGO.
- Population statistics from DCS, joined to boundaries via stable IDs.
- **Rule:** record source, licence, collection date, scale, CRS and accuracy for every geographic dataset. Reusing code does not grant rights to the underlying data.

## 4. Data design decisions (recommended)

- Every geographic feature gets a **stable identifier plus metadata**: `geography_id` (e.g. `LK-DIST-07`), `name_en`, `name_si`, `name_ta`, `geography_type`, `parent_id`, `valid_from`, `valid_to`, `source`, `geometry`.
- **Preserve historical versions** of boundaries and names; never overwrite.
- Keep original source files untouched and make separate cleaned copies.
- Never fabricate missing data or silently replace authoritative statistics with estimates.
- Eventual registries: geographic entity, statistical indicator, geographic dataset; plus provenance and historical versioning.

## 5. Technology (recommended, not yet locked)

- **Core:** QGIS (inspect data first), PostgreSQL + PostGIS, MapLibre GL JS, Python + GeoPandas, FastAPI, Next.js + TypeScript, Docker.
- **Supporting:** GDAL/OGR, Tippecanoe + **PMTiles** (static vector tiles, simple hosting), GeoServer (optional OGC services), Apache ECharts for charts, Redis for caching, Git/GitHub.
- **Pipeline:** sources → QGIS/GDAL/GeoPandas cleaning → PostGIS → FastAPI → Next.js + MapLibre.
- **Open:** for a read-heavy national map, precomputed tiles plus static data (SQLite/PMTiles) may beat PostGIS; PostGIS is better for complex queries. Decide after the architecture prompt.
- Install order: QGIS, PostgreSQL/PostGIS, Python/GeoPandas, VS Code, Node/Next.js, MapLibre, FastAPI, Docker.
- **Implication of the new visual direction (my note, to be decided):** a map-as-background, animated UI favours MapLibre GL (WebGL) with PMTiles vector tiles, plus a motion layer (e.g. Framer Motion / GSAP) and dark, glass-style panels. Performance on low-end phones and slow connections in Sri Lanka needs an explicit budget, and animation should respect reduced-motion settings.

## 6. Prototype UI concept (from chat)

Full-screen map; left layer selector; search for districts/DS/GN; clickable areas with an info panel; legend and colour scale; date selector for historical data. Example: clicking Kurunegala shows population, density, age mix, schools, hospitals, roads. First layers: boundaries, roads, railways, rivers, population.

## 7. Competitor findings and corrections

- Chat's view: LankaData.net is a serious strategic competitor at the data-infrastructure level.
- **Corrections from my audit** ([lankadata-audit.md](lankadata-audit.md)): the chat says LankaData advertises "100+ endpoints" and has a "data-mapping section". I verified that `api.lankadata.net` does not resolve and has no docs, and that its "Lanka Data Map" page is a conceptual diagram, not a GIS map. It is document and registry search, not statistics or geography. So the **map-first, number-first angle is open ground**.
- **Lanka Data Layer** (`github.com/prabhavalabs/lanka-data-layer`): per the chat, an MIT-licensed open-source project with 25 districts, 9 provinces, about 330 DS and about 14,000 GN divisions, population, reverse geocoding, postal codes, election data, PMTiles, and a SQLite + TypeScript + MapLibre stack; underlying datasets under ODbL and CC BY-IGO. ⚠️ **I have not inspected this repo.** The chat itself says it is not shown to be affiliated with LankaData.net.
- **Recommended decision:** don't rebuild boundaries, geocoding and basic population lookups from scratch; evaluate reusing or integrating Lanka Data Layer. Differentiate on:
  1. National infrastructure atlas (schools, hospitals, police, offices, roads, rail, bridges, utilities)
  2. District intelligence (economy, demographics, education, health)
  3. Historical geography (boundaries, settlements, population over time)
  4. Spatial research (infrastructure vs poverty, employment, development)
  5. A national data API tied to the wider statistics repository

## 8. Working method (recommended)

- One assignment at a time; require evidence; review before proceeding. Don't build the whole platform in one prompt.
- Standing rule for coding agents: inspect existing code first, smallest change, run tests and show real results, never fabricate counts/responses/deployments, update docs, wait for approval before the next milestone. Prioritise correctness, reproducibility, provenance and maintainability.
- Tools: ChatGPT for research/architecture; Claude Code for repo work and implementation; Cursor optional; QGIS for data inspection.

## 9. Planned sequence (ten prompts, five phases)

1. **Understand competition:** LankaData.net audit (**done**, see audit file); audit the Lanka Data Layer repo (**next**).
2. **Run and test:** set up Lanka Data Layer locally; test its geographic data quality against NSDI/Survey/DCS (feature counts, invalid or duplicate geometries, IDs, CRS, gaps/overlaps, licences, update dates).
3. **Gap analysis and architecture:** missing layers ranked by public value, availability and difficulty; full architecture and cost estimates (prototype, beta, national).
4. **Build:** administrative atlas (repo structure, schema, then one milestone at a time); add national datasets (population, schools, universities, hospitals, police, rail, roads, rivers, protected forests) each with provenance and a quality report.
5. **National scale:** historical geographic database with validity periods, confidence levels and citations (separate fact from reconstruction); integrate with statistics (unified geography IDs, search, comparison, export). Keep basic statistics public while allowing future commercial API services.

Seven-day starter plan from the chat: set up QGIS and inspect NSDI layers; extract districts/DS and check IDs; build the base map; join DCS population and make a density map; thematic maps; PostGIS + MapLibre prototype; publish with layer controls, district selection, info panels and search.

## 10. Open questions

- Lock the architecture: PostGIS vs precomputed SQLite/PMTiles (or both).
- Reuse/integrate Lanka Data Layer, or build independently?
- English-first, with Sinhala/Tamil names in the data model from day one (chat's suggestion): confirm.
- Visual identity: colour theme, motion language, performance budget for mobile.
- Licence for what Sri Lanka Facts publishes (open licence vs restrictive).
- Verify NSDI REST service access terms and which boundary layers are shareable.
- Institutional model: single entity first, or non-profit foundation plus commercial company from the start (see §11)?
- Which "Priority 1" launch section anchors the map: Population (blueprint) vs the Administrative Atlas (§1)? They overlap; see §14.
- Pricing, tier boundaries and the domain/trademark check for "Sri Lanka Facts" and the four sub-brands.
- Legal review: PDPA obligations, per-dataset reuse rights, commercial redistribution (see §17).

---

# Part 2 — National platform blueprint (pasted 2026-11-07)

Source: a second ChatGPT blueprint, pasted by the user. Everything below is **Recommended** unless marked, and was **not yet confirmed by the user**. Standing user direction still applies to all of it: **the platform is visual and map-first**, so each product below is read through the map. ⚠️ marks claims I have not checked (legal dates, data-portal licence terms, DCS microdata rules, RTI Act details).

## 11. Institutional model and governance

- Position it as a **national data and research institution with a commercial services division**, not just a statistics website. The defensible assets are the trusted database, historical archive, methodology and reputation, not the front end.
- Working identity: **SRI LANKA FACTS** — "Understand the country through data." — *Independent national data platform*. Subject to name, trademark and domain checks.
- Proposed structure: **Sri Lanka Facts** (public platform), **Research** (analysis services), **Data** (datasets, APIs, data products), **Observatory** (long-term indicator monitoring). Shared engineering, research, QA and documentation underneath.
- Start as one legal entity, with the public platform and commercial work kept separate in practice. Consider a **non-profit foundation plus commercial company** as it grows (needs legal advice).
- **Governance principles** (adopt from day one):
  - No political party ownership or editorial control.
  - No sale of favourable rankings or manipulated statistics.
  - Every published figure has a traceable source.
  - Commercial customers cannot buy changes to public findings.
  - Corrections are documented publicly.
  - Methodologies are open to independent scrutiny.
  - Sponsored research is disclosed, and funders do not control findings.
- Keep publicly funded/open data clearly separated from commercially commissioned work.

## 12. Products, each as a map experience

The blueprint lists five products. Under the map-first decision, each is a mode of the same map shell rather than a separate site.

| Product | Blueprint purpose | Map-first reading (my note) |
|---|---|---|
| National Statistics | Topic landing pages: latest figure, trends, district/province comparison, charts, indicator explainers, source links, downloads | Every topic opens on the map (choropleth by district/DS) with the trend chart and explainer in a side panel |
| Data Explorer | Search/filter datasets, multi-indicator, compare, export CSV/JSON/Excel, view methodology | Pick indicators, brush a region or period on the map, export what is selected |
| Observatory | Monitor inflation, FX, debt, unemployment, tourism, electricity, population, revenue at set frequencies | A national dashboard layer over the map; geographic indicators (e.g. electricity by district) animate on it, national ones sit in a HUD strip |
| Research & Insights | Published reports with dataset and reproducible method | Scroll-driven stories where the map moves as the narrative advances |
| Data Services | API, custom analysis, enterprise dashboards | Embeddable/white-label map views plus the API |

- **District Explorer** (Recommended flagship): every one of the 25 districts is a navigable profile (population, density, age, household income, poverty, education, employment, agriculture, health, roads, local-government spending, history). Same structure for all districts, reached by clicking the map. Reuses the §6 info-panel concept.
- Topic pages should explain, not just display. Example: GDP page covers nominal vs real, growth, sector shares, per capita, revisions and history.
- Initial research topics: population since independence; education spending; where revenue comes from; cost of living over 25 years; inequality between districts; government employment over time; debt servicing; urban/rural shift. Each with dataset and reproducible method.
- **Language:** English first. Schema carries `name_si` / `name_ta` and Sinhala/Tamil metadata from day one (matches §4 and the §10 question; still to be confirmed).

## 13. Business model

- **Freemium. Never paywall basic national statistics.** Charge for added value: processing, cleaning, linking, analysis, visualisation, convenience, service guarantees. Never charge simply for access to government information that is legally free.
- Proposed tiers (not prices):
  - **Public (Rs. 0):** published statistics, interactive charts and maps, history, public reports, basic CSV, source documentation.
  - **Professional (paid):** advanced comparisons, bulk downloads, saved dashboards/map views, advanced filters, higher API quotas, custom chart and map exports.
  - **Enterprise (custom):** dedicated API, commercial dashboards, custom datasets, research and consultancy, integrations, SLAs.
- Customers: banks, insurers, universities, NGOs, research firms, investors, media, government, international organisations. Services: custom economic research, **district-level market analysis**, BI, forecasting, bespoke integrations.
- Revenue streams: enterprise subscriptions, research contracts, data consultancy, custom dashboards, sponsored research (disclosed), grants, education/training. **No advertising and no sale of personal data.**
- Keep infrastructure spend low early; spend on people, research, data acquisition and development.
- ⚠️ The blueprint says the government Open Data Portal permits commercial and non-commercial reuse. I have not checked it, and the blueprint itself warns this may not cover every institution's datasets. **Record reuse rights per dataset.**

## 14. Launch scope

Blueprint: launch with three well-built sections, not twelve thin ones.

1. **Population & Demographics:** national history, by district, age/sex, urban/rural, births/deaths/migration, density maps.
2. **Economy & Public Finance:** GDP and sectors, GDP per capita, inflation, debt, revenue/expenditure, trade, reserves.
3. **Government & Institutions:** directory of ministries, departments, statutory bodies, government employment, spending by institution, responsibilities.

- **Recommended first dataset and dashboard:** population, because it has historical depth, geographic comparison and public interest. It demonstrates the full chain from source document to interactive visualisation.
- **Reconciling with Part 1 (my note, to decide):** the Administrative Atlas (§1) is the geographic spine the population dashboard needs. Sensible order: Atlas boundaries → population join → density map and dashboard → Economy → Institutions. Institutions and public finance are less naturally geographic, so decide how they appear on the map (office locations, spending by district where it exists).
- **Launch targets (targets, not facts):** 100 verified datasets; 20 institutional sources; 30 historical indicators; 25 district-level indicators; 15 dashboards; 5 research publications; 10 API endpoints; 100 downloadable datasets.
- **12-month targets:** 500 datasets; 40 sources; 20 publications; 25 district profiles; 5,000 registered users; 100 API users; 5 institutional partnerships; 3–5 paying institutional customers. To be revised after the first month of source discovery.
- Measure credibility (sources, partnerships, citations), not only traffic.

## 15. Data model and quality

- **Every observation carries provenance:** indicator, geography, period, value, unit, source, source document, publication date, methodology, status (e.g. official), revision/version, last-verified date. Also keep the original source file, extraction date, transformations and revisions. This answers: where did it come from, was it revised, what was the original, how was it calculated, do two conflicting figures measure different things?
- **Historical and reconstructed data** also need `estimate_type`, `confidence`, `notes`, `boundary_definition`, `methodology`. Archaeological estimates, reconstructions and census counts must never be confused (matters for the historical city population project).
- This complements §4: geography gets stable IDs and validity periods; statistics get provenance and revisions; the two join on `geography_id` plus period.
- **Public data-quality grade, shown on each dataset and on the map legend, not buried in docs:**
  - **A — Verified:** checked directly against an authoritative primary source.
  - **B — Reconciled:** cross-checked against several credible sources.
  - **C — Estimated:** derived or modelled with documented method.
  - **D — Historical:** reconstructed from incomplete evidence.
- Prefer Sri Lankan primary sources as the authority; use World Bank, IMF, UN, ADB, ILO and FAO for international comparison.
- Automated freshness monitoring for outdated data; human verification of important indicators extracted automatically.

## 16. Architecture and technology (delta from §5)

- Blueprint pipeline: source connectors (automated APIs/downloads/scraping plus manual PDF/Excel/CSV/OCR) → validation and transformation (quality checks, standardisation, reconciliation, provenance) → canonical platform (PostgreSQL + PostGIS, object storage, versioned datasets, metadata catalogue) → FastAPI public API (auth, queries, downloads, rate limits) → Next.js public site and business portal.
- Additional stack choices not in §5: **Pandas/Polars** for processing, **Prefect** for orchestration, **Celery + Redis** for background jobs, **S3-compatible object storage**.
- **Modular monolith, no microservices at the start.** Separate modules: ingestion, data, API, authentication, publishing.
- Still open (§5/§10): PostGIS as the canonical store with PMTiles/static exports generated for the read-heavy map. These can coexist: PostGIS as source of truth, precomputed tiles for serving.
- Map-first implication (my note): the API must serve both tile-friendly data (indicator values keyed by `geography_id`, joined client-side to boundary tiles) and the provenance and grade of each value, so the info panel can always show source and quality.

## 17. Data acquisition and legal

- **Tier 1, public datasets.** Priority institutions and data: DCS (population, census, household income, employment, poverty); CBSL (GDP, inflation, debt, reserves, banking, trade); Ministry of Finance (budget, revenue, expenditure); Election Commission (results, electorate); Tourism Development Authority (arrivals, revenue, accommodation); Department of Motor Traffic (vehicle registrations); Sri Lanka Railways (statistics, timetables); Ceylon Electricity Board (generation, consumption). Add these to the §2 register; several are geographic (electorates, rail, tourism sites).
- **Tier 2, formal partnerships:** approach DCS, CBSL and selected ministries with a proposal (who we are, what we publish, attribution, confidentiality, how we help them, machine-readable feeds/APIs). Aim for MoUs and regular data feeds rather than manual downloads.
- **Tier 3, Right to Information:** run an RTI programme for data that exists but is unpublished (public-sector headcount by institution, district expenditure, historical vehicle registrations, school infrastructure, hospital capacity, local-authority finances, project completion). **Keep a public register of requests, responses, refusals and outstanding items.** ⚠️ Act No. 12 of 2016 as cited by the chat; not verified.
- **Tier 4, international datasets** for comparison (World Bank, IMF, UN, ADB, ILO, FAO).
- DCS microdata: public-use files differ from licensed microdata, which need an application. Treat as a separate access class. ⚠️ per the chat, not verified.
- **Privacy and legal defaults:** prefer aggregates; never publish identifiable personal records; respect licensed/confidential data; track source-specific reuse permissions; get legal review of commercial redistribution rights.
- ⚠️ **Personal Data Protection Act:** the chat says a Data Protection Authority notice (July 2026) gives **1 January 2027** as commencement for core provisions. I have not verified this and it is close to today's date (2026-11-07). Verify before launch; build safeguards now.

## 18. Team and plan

- **Team (can combine or outsource):** project director; lead software engineer; data engineer; research analyst; data journalist / visualisation specialist; UI/UX designer. **Hire data engineer and research analyst first.** For this project, the designer/visualisation role carries the map-first, animated experience, so it is more central than the blueprint implies (my note).
- **90-day plan:**
  - **Days 1–30:** settle identity, institutional data inventory, source register, metadata standards, database design, GitHub organisation and repos, wireframes, pick first 20 datasets. *Milestone: architecture and initial catalogue approved.*
  - **Days 31–60:** deploy PostgreSQL/PostGIS, FastAPI, ingestion pipelines, validation, import 50 datasets, dataset catalogue, charts and geographic components, source attribution pages. *Milestone: working internal platform.*
  - **Days 61–90:** finish three subject areas, 15 dashboards, downloads, initial API, first reports, test with researchers and journalists, accuracy and security audits, public beta. *Milestone: public beta.*
  - Allow 1–3 more months for a polished first release.
- The ten-prompt sequence in §9 is the working-level route into Days 1–30 and should feed this plan rather than compete with it.

## 19. Risks

| Risk | Mitigation |
|---|---|
| Inconsistent government statistics | Keep original figures; document reconciliation |
| Missing historical data | Explicit confidence classes (grade D) |
| Political pressure | Editorial and governance policy independent of funders/parties |
| Licensing disputes | Rights recorded per dataset |
| Outdated information | Automated freshness monitoring |
| Wrong automated extraction | Human verification for key indicators |
| Commercial conflicts | Keep commissioned work separate from public findings |
| Poor institutional cooperation | Combine open sources, partnerships and RTI |
| *(my addition)* Map performance and cost on low-end devices | Performance budget, tiles over live queries, reduced-motion support |
| *(my addition)* Boundary/statistic mismatches across years | Validity periods on geography; never silently join across boundary changes |

## 20. Immediate next steps (blueprint order)

1. Project charter (mission, structure, governance, scope, principles).
2. National data inventory (master research spreadsheet; extends the §2 register).
3. Technical repository (GitHub org, schema, backend and frontend repos).
4. First working dataset: population.
5. First public dashboard: population on the map, source to visualisation.
6. Institutional engagement: introductory letters and partnership proposals for DCS, CBSL and others.

**Sequencing note:** these overlap with §9. Suggested merge: audit Lanka Data Layer (§9 step 1) and write the charter/inventory in parallel, then build the Atlas and population dashboard as items 4–5.
