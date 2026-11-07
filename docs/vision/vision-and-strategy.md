# Sri Lanka Facts: vision and strategy

Status: **recommendation, awaiting your decisions** · Written 2026-11-07 · Evidence: [ecosystem-landscape.md](../research/ecosystem-landscape.md)

This document gives my view of what Sri Lanka Facts should become, where I think the earlier brainstorm should change, and why. The decisions it proposes are tracked in [decision-log.md](../decisions/decision-log.md). Nothing here is final until you confirm it.

Legend used throughout the docs: ✅ verified directly (primary page, API or file) · 🟡 from secondary sources (news, law-firm notes, search summaries) · ❓ assumption or unverified.

---

## 1. The short version

1. **Don't build a Sri Lankan USAFacts.** USAFacts is funded by one philanthropist: about USD 10 million to start and up to USD 5 million a year, by 2017 estimates 🟡. You are one person, self-funded, directing AI agents. Copy its values (neutral, sourced, explanatory), not its breadth.
2. **Be the trusted place-based data layer for Sri Lanka.** In short, *every place in Sri Lanka, every number about it, with its source.* Sub-national data (district, DS division, GN division, local authority, electorate, health area) is where Sri Lanka's data is most scattered, where nobody does it well, and where a map earns its place.
3. **The core asset is a geography spine, not a website.** It is one authoritative register of Sri Lanka's geographies, admin and non-admin, with stable IDs, crosswalks between schemes and population denominators for any area. Everything else hangs off it. Others can copy a website. A spine you have verified carefully is much harder to copy.
4. **Launch with one flagship: the Census Atlas 2024.** Every province, district, DS and GN division, with the 2024 Census topics on the map, as citable place pages, downloads and a simple API. The data exists (GN-level tables from the Department of Census and Statistics, DCS) 🟡, the boundaries exist (COD-AB from the Survey Department) 🟡, and it shows the whole chain from source to map. Three thin sections would not.
5. **Map-first, not map-only.** Keep the immersive, animated map, but make every place and indicator a server-rendered page with a URL that can be cited, shared, found by search and read on a cheap phone. The map persists across those pages rather than replacing them.
6. **Work with the ecosystem, don't rebuild it.** Several small, capable projects already collect raw Sri Lankan data: Nuwan Senaratna's MIT-licensed scrapers ✅, the Lanka Data Foundation ✅, Lanka Data Layer ✅, Verité Research and Advocata 🟡. The gap is not scraping. It is **harmonisation, geography, verification and explanation**.
7. **Expect services to fund the platform, at least at first.** In years 1–2, revenue will come from commissioned analysis and GIS work for NGOs, researchers and businesses, not from individual subscriptions. The public platform is the credibility engine that wins that work.
8. **Keep the architecture static-first and low-maintenance.** The data is small (gigabytes, not terabytes). Optimise for provenance and review, not scale. Versioned files are the source of truth, and a database comes later as a disposable serving layer. See [architecture-overview.md](../architecture/architecture-overview.md).
9. **Make it spatial-first and vector-native, with a new way of exploring.** Every entity is a point in named spaces (geography, profile, change, landscape), and relationships are distances in those spaces, always explained by the underlying cited facts ([vector-space-model.md](../architecture/vector-space-model.md)). Zoom runs from the country down to individual buildings, trees and landmarks ([multi-scale-features.md](../architecture/multi-scale-features.md)). Every dataset declares where it applies; every value is shown against its neighbours, its parent, similar places and the country; every place has a profile vector for "places like this" and a typology; later, users draw their own areas. All of it precomputed or run in the browser, with no extra servers. See [spatial-first-analytics.md](../architecture/spatial-first-analytics.md).

---

## 2. What the research changed

The brainstorm was written mostly before looking closely at who else is working on Sri Lankan data. Five findings change the picture.

**a. The raw-data layer is busier than assumed.** ([details](../research/ecosystem-landscape.md#3-independent-and-civil-society-data-players))
- Nuwan Senaratna (`github.com/nuuuwan`) runs dozens of MIT-licensed repositories updated daily: Census 2024, 2012, 2001 and 1971 tables, CBSL and DCS series, dengue, disaster reports, irrigation, Treasury, tourism and more ✅. One dataset, `lk_census_2024`, has 154 tables, including GN-level tables for about 14,000 units ✅. He also holds boundaries for MOH areas, local authorities and polling divisions, with no stated licence ✅.
- The **Lanka Data Foundation** (opendata.lk) is a non-profit chaired by Sanjiva Weerawarana, with 11 named current staff and board members ✅. It builds OpenGIN (a time-aware government-structure graph), a gazette archive and a datasets catalogue that includes tourism, foreign-employment and budget tables ✅. Its content licence is **CC BY-NC-SA 4.0** ✅, so its data cannot be reused commercially without permission.
- **Lanka Data Layer** already serves admin boundaries, reverse geocoding and PMTiles under MIT ✅ (see your audit).
- **Verité Research** runs PublicFinance.lk, Manthri.lk and FactCheck.lk 🟡. **Advocata** runs SOE.lk and a time-series portal at data.advocata.org 🟡.
- National macro series (GDP, inflation, debt) are already available from CBSL, Advocata, the World Bank, CEIC and Trading Economics 🟡.

*Implication:* a national-statistics site organised by topic would be the fifth or sixth place to find inflation. No one, however, offers harmonised, explained, sub-national data on a map with stable geography IDs and provenance. Lanka Data Layer comes closest on geography but has no history, no indicators beyond Census and OSM, and a hierarchy error (Ampara) ✅.

**b. The official open-data layer is weak.** data.gov.lk had about 136 datasets in 2023 against a target of 2,000, and many are marked "License Not Specified" 🟡. Sri Lanka scored 16 against a global average of 33 on the 2022 Global Data Barometer 🟡. That is an opportunity, and also a warning: you will often be the first to clean a table, and you will carry the burden of proving it is right.

**c. Licensing is the hidden constraint.** The Census 2024 tables have no stated licence ✅, the NSDI boundary service shows no terms ✅, OSM data is share-alike (ODbL), and LDF data is non-commercial ✅. Before anything is published, every dataset needs a recorded rights position. This shapes the business model more than any technology choice.

**d. Neither model you looked at fits.** USAFacts is purely philanthropic and takes no outside donations 🟡. Our World in Data is a non-profit funded by grants and donations. The closest analogues to your situation are founder-led, lean projects: Data For India (journalist-founded, CC BY 4.0, a small FOSS United infrastructure grant, a subscriber newsletter) 🟡 and Nepal in Data (run by a social business) 🟡.

**e. AI changes the cost of the bottleneck, but does not remove it.** The slow part of this work is turning PDFs and Excel sheets into verified tables. AI agents can now draft most of that extraction. A human, in this case you, still has to verify the numbers that matter. Your verification throughput, not code, is the real capacity limit, and the plan is sized to it.

---

## 3. Recommended vision

> **Sri Lanka Facts: every place in Sri Lanka, every number about it, with its source.**

**Mission:** make reliable information about Sri Lanka's places (how many people live there, how they live, what is changing, what services reach them) easy to find, understand, cite and reuse.

**What makes it distinctive**

| Pillar | What it means in practice | Why it is defensible |
|---|---|---|
| Place-based | Every unit, from country down to GN division, has a page, a profile and a place on the map. Other geographies (local authorities, polling divisions, MOH areas) work the same way. | Few others go below district level properly. |
| Geography spine | One register of all schemes, stable IDs, crosswalks, boundary history, and **population denominators for any geography**, so per-capita rates can be computed for MOH areas, local authorities or electorates. | Slow, careful work: the moat. |
| Provenance on every number | Every value shows its source document, retrieval date, method, revision and verification status, one click from the map. | LankaData, LDF and most portals don't do this per value. |
| Explanation | Short, plain-language explainers: what a number means, how it is measured, what changed. | Turns data into understanding, and drives search traffic. |
| Open and reusable | CC BY 4.0 for what we produce (where source rights allow), bulk downloads, a static API, and an MCP server so AI assistants can cite Sri Lanka Facts. | Contrasts with restrictive or non-commercial competitors. |

**What it is not:** a document search engine, a general chatbot, a news site, a national macro dashboard competing with CBSL, or a government-structure registry (LDF is building one).

---

## 4. Where I'd change the original direction

| Original idea (brainstorm) | My view | Recommendation |
|---|---|---|
| A comprehensive "USAFacts for Sri Lanka", with all topics eventually | Not feasible for one self-funded person. The topical national layer is already partly served. | Start with **place-based** data and grow outward from the geography spine. Add national context indicators only where they explain places. |
| Interactive map as the base layer for everything | Right for sub-national data. It hurts national series (inflation is one number), search visibility, citation, accessibility and low-end phones. | **Map-first, not map-only.** The persistent map shell sits around server-rendered pages. See D-002. |
| Fluid, animated, high-tech UI | Good for the explorer and stories. Too much motion undermines trust and battery life. | Motion has a purpose: transitions between places, scroll-driven stories. Restraint elsewhere, a performance budget, `prefers-reduced-motion` and a lite mode. |
| Launch with three sections (Population; Economy and Public Finance; Government and Institutions); 100 datasets, 15 dashboards and 10 API endpoints in 90 days | That assumes a 6-person team. Two of the three sections overlap with Verité, LDF and Advocata. | **One flagship: the Census Atlas 2024.** Depth beats breadth. Public finance and institutions come later, ideally through partnerships. |
| Administrative Atlas as "Project 001" (roads, rail, rivers, all layers) | Boundaries yes. Roads, rail and rivers are basemap context from OSM, not a product. | Boundaries plus Census is the product, with OSM as basemap context. Infrastructure layers come later and need a purpose. |
| Fork the Lanka Data Layer foundry (audit option C) | It is a Node/TypeScript pipeline you didn't design, mixes two boundary sources, has a confirmed hierarchy bug and no history model, and depends on `ceylon-hub` seed files. | **Build the spine from primary sources** (COD-AB/Survey Department, DCS), borrow LDL ideas and code under MIT with attribution, use LDL and NSDI as cross-checks, and report the Ampara bug upstream. See D-008. |
| PostGIS as source of truth, plus Prefect, Celery, Redis, GeoServer, FastAPI | Six services for one non-coding lead is a lot of breakage. The data fits on a laptop. | **Versioned release files are the truth.** Python and DuckDB run the pipeline on GitHub Actions. Static site, tiles and API go on a CDN. Postgres/PostGIS and FastAPI arrive when there is a real query or commercial need. See D-003. |
| Quality grade A–D (Verified / Reconciled / Estimated / Historical) | It mixes two things: *how the number was produced* and *how well we checked it*. An official estimate can be verified. A census count can be badly extracted. | Use two fields, `data_nature` and `verification`, and derive a simple display badge from them. See D-009. |
| Hybrid institution with four sub-brands (Research, Data, Observatory, Services) from the start | Brand overhead with no team behind it. | **One brand, one small legal entity**, with the public governance principles from §11 of the brainstorm (they're good). Revisit the structure when there is revenue or grant funding. |
| Freemium with a paid Professional tier for individuals | Willingness to pay for individual data subscriptions in Sri Lanka is likely low ❓, and free alternatives exist. | Free public platform. Revenue first from **commissioned analysis, GIS and sampling-frame work**, later from API service levels and data products. See [organisation-and-business-model.md](organisation-and-business-model.md). |
| Early MoUs with DCS, CBSL and ministries | No relationships yet. Institutions respond to credibility and concrete, small asks. | Earn credibility with public work first. Start with narrow asks (licence clarification, reporting errata) and build towards feeds and MoUs later. |
| AI-assisted research chat | High cost, high risk of wrong answers, and LankaData already does it. | AI is first an **internal tool** (extraction, QA, drafting). Externally, offer an **MCP server and llms.txt** so people's own assistants can cite you. A public chat comes later, if ever. |
| English first; Sinhala and Tamil later | Agree for the interface. Place names, though, must be trilingual from day one, and LDL lacks Tamil for all GN divisions ✅. | English UI first. Trilingual names in the data from day one. Sinhala and Tamil core pages in Stage 3, earlier than "later". |

**Kept as is:** never fabricate data; preserve the original sources; stable IDs with history; provenance per observation; never paywall basic public statistics; no advertising and no sale of personal data; the governance principles; keeping commissioned work separate from public findings; publishing corrections publicly; and the one-assignment-at-a-time working method with evidence.

---

## 5. Who it is for

| Audience | What they come to do | Year-1 priority |
|---|---|---|
| **Journalists and editors** | Get a reliable district or DS figure quickly, with a source to cite and a chart or map to embed | **Primary.** They spread credibility and traffic. |
| **Researchers and students** | Download clean, joinable tables at GN/DS level, with methods | **Primary.** They cite and validate. |
| **NGOs and development organisations** | Target programmes, write proposals, build baselines and sampling frames | **Primary.** They also pay for services. |
| Businesses (FMCG, banks, microfinance, insurers, research firms) | Market sizing, catchment population, site selection, survey sampling | Secondary, served through paid work. |
| Public officials (DS offices, local authorities, provincial councils) | See their area against others, find their own data cleaned | Secondary. Relationships come later. |
| Citizens | "What is my GN division? How does my area compare? Who serves my area?" | Arrive through search and place pages. |
| Developers | Look up an area from coordinates, get stable IDs, call an API | Served by the static API and downloads. |

---

## 6. The flagship: Census Atlas 2024

**What it is:** the 2024 Census of Population and Housing for every unit, from country to GN division, on a fast map, with a citable page for every place, downloads and a simple API.

**Why this, first:**
- **The data exists in machine-readable form.** DCS has published GN-level Excel tables for 12 topics: sex, ethnicity, religion and age group for people, and household structure, wall, floor and roof type, drinking water, cooking fuel, lighting and toilets for housing 🟡. Smaller tables come from the final report, presented on 6 April 2026 🟡.
- **The geometry exists.** COD-AB levels 0–4, sourced from the Survey Department, are published under CC BY-IGO on HDX 🟡, and NSDI can serve as a cross-check ✅.
- **It is visual and interesting at fine detail.** "Households cooking with firewood" or "share of homes with piped water" across 14,000 GN divisions is the kind of map people share.
- **It exercises the whole chain:** snapshot, extraction, harmonisation, validation, release, tiles, pages, API, provenance and corrections.
- **It stays relevant until the next census** (expected around 2034 ❓), and it supplies the denominators every later per-capita indicator needs.
- **Being first is not the point.** DCS's LankaStatMap showed 2012 Census data down to GN level in 2017 🟡 (it still responds ✅). The point is quality: fast, sourced, comparable, downloadable, linked to other geographies, and maintained.

**Scope for the public beta:**
- Boundaries for levels 0–4, validated, with a published quality report (the counts question, 339 vs 331 DS divisions, settled or explicitly flagged).
- 15–25 headline indicators on the map, and the full Census tables in downloads.
- Place pages: country, 9 provinces, 25 districts, all DS divisions. GN pages in a lighter template.
- Indicator pages with definitions, method notes and the source table reference.
- Downloads as CSV, Parquet and GeoPackage, plus a static JSON API, under CC BY 4.0 for our derived work **once the DCS reuse position is clarified** (see §9).
- A methodology page, a corrections log and a "report a problem" link.
- Two or three short explainers, for example ageing by district or how Sri Lankans cook.

**Deliberately out of the beta:** accounts, payments, dynamic queries, AI chat, Sinhala/Tamil UI, 2012 comparisons at GN level (boundaries changed), and infrastructure layers.

---

## 7. What not to build (for now)

- A document or PDF search engine. LankaData, nuuuwan's `lk_datasets` and LDF's archive already cover it.
- A public AI chatbot.
- Accounts, paywalls or a "Professional" tier before there is an audience that asks for them.
- National macro dashboards as a flagship.
- Microservices, Kubernetes, self-managed servers or a GeoServer stack.
- Anything copied or bulk-mirrored from LankaData or LDF, given their licence terms.
- Scrapers for sources nuuuwan already maintains, unless you need provenance he doesn't capture. Use his output as a discovery and cross-check layer, and verify against the primary source.

---

## 8. The long-term picture (3–5 years)

If the flagship works, the platform grows in layers, each one built on the spine:

```
               ┌──────────────────────────────────────────────┐
  Stories      │ Explainers · data stories · newsletter       │
               ├──────────────────────────────────────────────┤
  Products     │ Place pages · map explorer · indicator pages │
               │ downloads · API · MCP · embeds · tools       │
               ├──────────────────────────────────────────────┤
  Indicators   │ Census → poverty, labour, health, education, │
               │ agriculture, elections, prices, disasters,   │
               │ public finance by place, satellite-derived   │
               ├──────────────────────────────────────────────┤
  Spine        │ Geographies · IDs · history · crosswalks ·   │
               │ denominators · trilingual gazetteer          │
               ├──────────────────────────────────────────────┤
  Trust        │ Provenance · verification · corrections ·    │
               │ methods · licences · governance              │
               └──────────────────────────────────────────────┘
```

At national scale, Sri Lanka Facts would be the reference other people's work stands on. Newsrooms would embed its maps, NGOs would draw sampling frames from it, apps would resolve coordinates to GN, DS and MOH IDs through its API, and AI assistants would cite it. Commercial products would be built on top. The ideas that could get there are in the [opportunities register](../ideas/opportunities-register.md).

---

## 9. Key uncertainties and how to settle them

| Uncertainty | Why it matters | How to settle it | When |
|---|---|---|---|
| Can we republish DCS Census 2024 tables, including GN level, under an open licence and commercially? | It underpins the flagship and the business. | Read the DCS terms (including "Appendix D" on licensed data). Write to DCS asking for confirmation of reuse terms for published tables. Meanwhile publish with attribution and a clear note. | Stage 0 |
| Are COD-AB boundaries current against Survey Department and DCS 2024 units? | Joining census to boundaries (339 vs 331 DS; 14,043 vs 14,051 GN) | Crosswalk census unit lists to COD-AB and NSDI. List mismatches. Ask the Survey Department and DCS about specific cases. | Stage 0–1 |
| Do NGOs and businesses pay for place-based analysis? | Sustainability | 8–10 structured conversations in Stage 1 (prompt R05). One paid pilot by the end of Stage 2. | Stage 1–2 |
| Will LDF, nuuuwan and LDL see us as partners or competitors? | Reuse, reputation, duplicated work | Open, specific, generous contact: report bugs upstream, credit their work, propose a concrete division of labour. | Stage 0–1 |
| Can one person keep up with verification? | Quality is the brand | Measure verified values per hour in Stage 1. Automate checks. Verify only key figures by hand and label everything else honestly. | Stage 1 |

---

## 10. Decisions I need from you

These are yours to make. My recommendation is first in each case.

1. **Positioning:** accept "place-based data layer" as the core identity (D-001), instead of a comprehensive national statistics portal?
2. **Map-first, not map-only:** accept that every place and indicator gets its own server-rendered page, with the immersive map as a persistent shell and explorer (D-002)?
3. **Flagship:** Census Atlas 2024 as the first public release (D-006)?
4. **Openness:** CC BY 4.0 for what Sri Lanka Facts produces and open-source code (D-005)? This rules out selling the data itself, but not services.
5. **Name:** keep "Sri Lanka Facts"? `srilankafacts.com` appears to be parked with a domain-sales service ✅, so it may be for sale. `.org`, `.net` and `.lk` showed no DNS records ✅, which suggests but does not prove they are available. The name is also descriptive, which can make trademark protection harder ❓.
6. **Spatial-first analytics (D-013 to D-015):** accept the spatial contract, H3 as a derived analytic grid, and spatial context plus place vectors as the default way of exploring data? And should ethnicity and religion stay out of similarity recipes entirely, or be allowed in custom recipes? I recommend leaving them out. See [spatial-first-analytics.md](../architecture/spatial-first-analytics.md).
7. **Vector-native core (D-016):** accept the split between an exact, cited ledger and derived, versioned vector spaces, rather than making embeddings the source of truth?
8. **Multi-scale features (D-017):** accept a ~100 m cell as the atom, with individual features (building, tree, landmark) below it and the GN as the information floor for census data, with open map data integrated rather than mapped ourselves, and never attributing people's statistics to individual buildings?
9. **Footprint model (D-018):** every value stored with its real footprint in space (point, shape or uncertainty radius) and time (interval, snapshot or approximate date), indexed on ~100 m cells, rather than forced onto a grid? Plus the extra facets and context dimensions in [footprint-model.md §8](../architecture/footprint-model.md#8-dimension-catalogue-what-else-every-data-point-can-carry), in the recommended order?
10. **Claims and live data (D-019, D-020):** show conflicting sources side by side instead of picking one; add live feeds as scheduled updates in Stage 3 and movement in Stage 4; park social-media mood?
11. **Help budget:** are you willing to pay for occasional expert review, for example a few hours a month of senior-engineer code review and a GIS specialist for boundary checks? The plan works better with it (see [development-strategy.md](../roadmap/development-strategy.md#5-working-as-a-non-coding-lead-with-ai-agents)).
