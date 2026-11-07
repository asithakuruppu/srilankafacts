# Sri Lankan data ecosystem: landscape and implications

Researched 2026-11-07 · Builds on [lanka-data-layer-audit.md](../lanka-data-layer-audit.md) and [lankadata-audit.md](../lankadata-audit.md)

**Legend:** ✅ verified directly today (primary page, GitHub API, DNS, HTTP) or in the earlier audits · 🟡 from secondary sources (news, law-firm notes, search summaries), not checked at the primary source · ❓ assumption or not found.

**Method and limits:** web searches, GitHub API queries, DNS and HTTP checks, and page reads by a fetch agent. I did **not** read the Census final report PDF, the PDPA gazette, the DCS licensing appendix or any statute directly. Treat 🟡 items as leads to confirm before relying on them publicly.

---

## 1. Official producers and portals

| Institution / portal | What is there | Access class | Licence / terms | Notes |
|---|---|---|---|---|
| **Dept of Census and Statistics (DCS)**, statistics.gov.lk | Census of Population and Housing 2024: district and divisional results released 30 Oct 2025; final report presented 6 Apr 2026; population **21,781,800** 🟡 (the same total appears in a DCS-derived dataset ✅). GN-level Excel tables for 12 topics 🟡. Labour Force Survey, HIES, CCPI/NCPI, agriculture statistics. NADA microdata catalogue (nada.statistics.gov.lk) ✅ (URLs appear in results). | Excel, PDF, web tables; licensed microdata on application | **No reuse licence found.** A document titled "Terms and Conditions on the Use of Licensed Data Files" (Appendix D) exists 🟡. The Census 2024 data has no stated licence ✅ (LDL audit). | Ask for written reuse terms early (prompt R04). |
| **DCS LankaStatMap** | Launched April 2017 with 2012 Census data down to GN level 🟡 | Web map | — | Responds HTTP 200 today ✅. Whether it has 2024 data is ❓. |
| **Central Bank (CBSL)** | Economic Data Library: time-series query tool, public since 20 Feb 2017 🟡. Annual "Sri Lanka Socio-Economic Data" folder 🟡. SDDS National Summary Data Page; Sri Lanka subscribed to the IMF SDDS in Nov 2015 🟡. The Annual Report was replaced in 2023 by the Annual Economic Review plus Financial Statements 🟡 (per nuuuwan README). | Web query tool, PDF, Excel | Not checked | **No public API found** ❓ (absence in search is not proof). The NSDP is the most standardised national macro source. |
| **Open Data Portal**, data.gov.lk (ICTA) | About 136 datasets in 2023 against a 2,000 target 🟡. Many tagged "License Not Specified" 🟡. Described as poor quality by LIRNEasia 🟡. | Downloads | Per dataset, often missing | Global Data Barometer 2022: Sri Lanka 16 vs global average 33 🟡. |
| **NSDI** (ICTA with Survey Department) | Geoportal and metadata catalogue. 130+ layers from 27+ organisations 🟡. ArcGIS REST boundaries service live, max 1,000 records per query ✅. | WMS / ArcGIS REST | **No licence text** on the service ✅. A national data-sharing policy was designed, with pricing and custodianship elements 🟡; adopted text not found ❓. | Useful cross-check. GN codes are empty for all 14,051 features ✅. |
| **Survey Department** | Authoritative boundaries and 1:50k topographic data. Source of COD-AB 🟡. | On request; MOUs for government 🟡 | "Free with restrictions" 🟡 | Contact for boundary currency questions. |
| **Election Commission** | Results by electoral district (22) and polling division (160) | PDF / web | Not checked | Already parsed in nuuuwan's `elections_lk` 🟡. |
| **Local government** | 341 local authorities; 339 elected on 6 May 2025 (28 MC, 36 UC, 275 PS) 🟡 | — | — | Local authority areas don't nest within DS divisions. The crosswalk is needed. |
| **Epidemiology Unit / National Dengue Control Unit** | Weekly Epidemiological Reports; dengue by MOH area 🟡 | PDF / web | Not checked | MOH-level data is used by the academic Sri Lanka Dengue Atlas 🟡. |
| Ministry of Finance / Treasury | Budget estimates, activity budgets, fiscal reports | PDF | Not checked | LDF and nuuuwan both archive these ✅. |
| SLTDA, SLBFE, Dept of Motor Traffic, CEB, Railways | Sector statistics | Mostly PDF annual reports | Not checked | LDF has extracted some SLTDA/SLBFE tables ✅. |
| **CROPIX** (Ministry of Agriculture with FAO; Gates Foundation support) | National crop-data platform, launched Jan 2026, plans APIs and open data 🟡 | ❓ | ❓ | Watch it as an agriculture source. |

### Administrative unit counts don't agree, and that matters

| Level | Commonly cited | COD-AB (via LDL) ✅ | NSDI ✅ | Census 2024 tables, as parsed by nuuuwan ✅ | Status |
|---|---|---|---|---|---|
| Provinces | 9 | 9 | 9 | 9 | settled |
| Districts | 25 | 25 | 25 | 25 | settled (LDL has Ampara under the wrong province ✅) |
| DS divisions | 331 🟡 | 339 | 332 features / 329 codes | 340 rows | **unresolved** |
| GN divisions | 14,022 🟡 | 14,043 | 14,051 | 14,008 rows | **unresolved** |

The census-table column counts rows in nuuuwan's `Person-Sex` table (it also has 22 ED, 160 PD and 358 LG rows). I have not checked these against the DCS Excel originals, and rows may include special units.

Codes are not stable across sources. For example, DS code 2309 is Walapane in NSDI and Nildandahinna in COD-AB ✅. The geography spine must match on name **and** parent, keep a crosswalk, and publish the counts with sources rather than asserting one number.

---

## 2. Legal and policy environment

| Item | Finding | Status | Implication |
|---|---|---|---|
| Personal Data Protection Act No. 9 of 2022, amended by Act No. 22 of 2025 | A gazette of 22 July 2026 brings Parts I and III (processing; controllers and processors) into force on **1 Jan 2027**. The administrative penalties (Part VII) and data-subject rights (Part II) await a further order. The Data Protection Authority has operated since July 2023. | 🟡 (law-firm and news summaries; gazette not read) | Aggregates are low-risk. Accounts, newsletter lists and analytics are personal data. Collect the minimum and write a privacy policy before Stage 1. |
| Right to Information Act No. 12 of 2016 | Well established. Not re-read today. | 🟡 | RTI is a route to unpublished data. LDF already runs an RTI tracker ✅, so coordinate rather than duplicate. |
| Online Safety Act No. 9 of 2024 | The government has committed to amend it. A private member's repeal bill has been gazetted. No result found confirming an amendment or repeal has passed. | 🟡 | A publisher of explanatory content on contested topics should check the current status before launch (legal checklist). |
| Statistics law and DCS reuse terms | Not researched | ❓ | Part of the DCS licence question. |

---

## 3. Independent and civil-society data players

| Who | What they do | Licence | Overlap with us | Recommended relationship |
|---|---|---|---|---|
| **Nuwan I. Senaratna** (`github.com/nuuuwan`) | 60+ repositories pushed since Aug 2026, 26 of them on the day of this research ✅: `lk_census_2024` (154 tables incl. GND-level; IDs like `LK-1103015`, the same structure as OCHA p-codes), `lk_census_2012/2001/1971`, `lk_dcs` (CCPI to Oct 2026), `cbsl` (1,137 documents), `lk_dengue`, `lk_dmc`, `lk_irrigation`, `lk_treasury`, `lk_tourism`, `elections_lk`, `gig-data` (geometries for province, district, DSD, GND, ED, PD, LG and **330 MOH areas**). `lk_datasets` is a document corpus of 299,131 documents in 26 datasets, described in arXiv:2510.04124 🟡. Runs alert.lk ✅. | Code **MIT** ✅. Data follows the source. `gig-data` has **no licence** and an unknown geometry source ✅. | Raw extraction of many of our sources | **Upstream and ally.** Use as discovery and cross-check. Verify against primary sources before publishing. Credit prominently. Ask about the provenance of the MOH and LG geometries. Bus factor of one. |
| **Lanka Data Foundation (LDF)**, opendata.lk | Non-profit, "nonpartisan". Board chaired by Sanjiva Weerawarana. 5 core staff and 2 interns named ✅. Products: OpenGINXplore (government structure over time, including department moves between ministries), Archives (government publications), a datasets catalogue (statistics 2019–2025: tourism, SLBFE, ministry expenditure ✅), RTI-Tracker, WebsiteScorecard, MeetingsTracker ✅. OpenGIN: Go/Ballerina, with MongoDB, Neo4j and PostgreSQL, temporal entity graph ✅. | Code Apache-2.0 ✅. **Content CC BY-NC-SA 4.0** from 11 Nov 2025 ✅. | Government & Institutions; some statistics | **Complementary.** They do structure and documents, we do places and numbers. Link to them, don't copy their data (non-commercial). Explore a division of labour. Strong network, so treat them as a potential partner. |
| **Lanka Data Layer** (Prabhava Labs) | Admin boundaries, reverse geocoding, PMTiles, Census 2024 demographics, elections, postal codes, OSM layers ✅ | MIT code. Data per source (CC BY-IGO, ODbL, Census unlicensed) ✅ | Geography | **Borrow ideas and cross-check.** Report the Ampara bug. Don't depend on the hosted API. |
| **LankaData.net** (Chat2Find) | Document search (about 90k documents claimed), registries, AI chat. Advertised API unreachable ✅. | Restrictive, non-commercial ✅ | Document search, AI | **Different lane.** Don't copy. |
| **Verité Research** | PublicFinance.lk (debt, expenditure, revenue), Manthri.lk (parliament monitoring since 2013), FactCheck.lk, IMF Tracker 🟡 | Not checked | Public finance, parliament | **Link and cite.** A potential partner for "public finance by place". |
| **Advocata Institute** | SOE.lk and "State of State Enterprises" reports. data.advocata.org time series (population, GDP, unemployment, CCPI/NCPI, tourism) 🟡 | Not checked | National macro series | Cite. No need to compete. |
| **Sri Lanka Dengue Atlas** (academic, thiyangt.github.io) | Dengue by MOH area, from NDCU data 🟡 | Not checked | Health by place | Potential collaborator for the MOH geography. |
| OSM community / open mapping | A 2025 initiative introduced OSM to 113 civil-society organisations (Vriddhi Project, UNOPS) 🟡 | ODbL | Basemap, infrastructure | Contribute fixes upstream. Source of facility data. |

**Overall:** collecting raw data is increasingly covered, but by small teams, often one person, with differing licences. **Nobody provides a harmonised, sub-national, provenance-first layer with a geography spine.**

---

## 4. International sources covering Sri Lanka

| Source | Use for us | Licence | Notes |
|---|---|---|---|
| HDX **COD-AB** (cod-ab-lka) | Admin boundaries, levels 0–4 | CC BY-IGO ✅ (LDL catalogue) | Source: Survey Department. Version 03, file updated Aug 2022 🟡. |
| HDX COD-PS | Population statistics | CC BY-IGO ✅ | Superseded by Census 2024 for counts. |
| OpenStreetMap / Geofabrik | Roads, rail, water, POIs, basemap | ODbL ✅ | Share-alike applies to derived databases. |
| **Protomaps basemap** | Self-hostable vector basemap (PMTiles) | ODbL (OSM-derived) | Daily builds 🟡. Extract a Sri Lanka area with `pmtiles extract`. |
| **Overture Maps** | Divisions, buildings, places, transport | Per theme: ODbL (OSM-derived), CDLA-Permissive-2.0 (e.g. places) 🟡 | Monthly GeoParquet releases. The 2026-01-21 release was the latest found 🟡. |
| Google Open Buildings v3 | Building footprints, for settlement and exposure analysis | CC BY 4.0 / ODbL 🟡 (verify) | Covers South Asia. Sri Lanka coverage not confirmed ❓. |
| WorldPop | Gridded population (modelled) | CC BY 4.0 ✅ | Always label as modelled. |
| World Bank, IMF, UN, ADB, ILO, FAO | International comparison | Mostly CC BY 4.0 (WB) ❓ per source | Context only. Primary authority stays Sri Lankan. |
| **Data Commons** (Google) | National-level Sri Lanka data. A hosted MCP server for public data 🟡 | Varies | The custom-instance platform is moving to Spanner Graph on GCP 🟡, which is heavy. Treat as a distribution channel, not a foundation. |
| Earth observation (VIIRS night lights, ESA WorldCover, Sentinel, CHIRPS) | Satellite-derived indicators by area | Mostly open ❓ per product | Later stage. Label as modelled. |

---

## 5. Comparable platforms and lessons

| Platform | Model | Lesson for us |
|---|---|---|
| **USAFacts** | Privately funded solely by Steve Ballmer. Not a 501(c)(3). Takes no outside donations 🟡. About USD 10M start-up and up to USD 5M a year (2017 reporting) 🟡. | Copy the editorial values and the "explain government numbers" voice, not the budget-dependent breadth. |
| **Our World in Data** | Non-profit. Statically rendered "JAMstack" site with no public backend. Python ETL with stages snapshot → meadow → garden → grapher. A flat-file catalogue powers both site and API 🟡. The grapher code is **no longer MIT**, published for reference only 🟡. | Strong architectural precedent for our "files are the truth, static-first" design. Copy the pattern, not the code. |
| **Data For India** | Founded by data journalist Rukmini S. CC BY 4.0. FOSS United grant up to INR 5 lakh for infrastructure. A subscriber-only newsletter 🟡. | The closest analogue: founder-led, explanation-first, small and lean. A newsletter builds an audience. |
| **Nepal in Data** | Run by Bikas Udhyami, a social business. Development statistics from 1950 🟡. | Social-business model in a similar market. |
| **Data Commons** | Google-backed knowledge graph. Custom instances on GCP 🟡. | Contribute data to it for reach. Don't build on it. |
| CEIC, Trading Economics | Commercial macro aggregators 🟡 | The national macro layer is commoditised. |

---

## 6. Seed source register

A starting list for `catalog/sources/` (prompt R01 creates one YAML file per source). Access: **D** downloadable table · **P** PDF only · **A** API · **W** web query tool · **R** on request.

| Source | Key datasets | Access | Rights known? | Priority |
|---|---|---|---|---|
| DCS Census 2024 | GN-level topic tables; final report tables | D, P | ❌ ask | **Stage 0–1** |
| HDX COD-AB (Survey Dept) | Admin boundaries 0–4 | D | ✅ CC BY-IGO | **Stage 0** |
| NSDI ArcGIS REST | Boundaries (cross-check) | A | ❌ ask | Stage 0 (check only) |
| DCS Census 2012 / 2001 / 1981 / 1971 | Historical census tables | P, D | ❌ | Stage 2 |
| Election Commission | Results by ED/PD; LG 2025 | P, W | ❌ | Stage 2 |
| Local-authority boundaries | 341 LAs | ❓ | ❓ | Stage 2 |
| MOH area boundaries | ~330–350 areas | ❓ (nuuuwan holds 330) | ❓ | Stage 2 |
| DCS HIES / poverty | Poverty by district; DS-level estimates if published | P | ❌ | Stage 3 |
| DCS Labour Force Survey | District labour indicators | P | ❌ | Stage 3 |
| DCS agriculture | Paddy by district and season | P, D | ❌ | Stage 3 |
| Ministry of Education school census | Schools and students by zone | P ❓ | ❓ | Stage 3 |
| Ministry of Health Annual Health Bulletin | Facilities, services by RDHS | P | ❓ | Stage 3 |
| NDCU / Epidemiology Unit | Dengue by MOH; notifiable diseases | P, W | ❓ | Stage 3 |
| CBSL NSDP / Data Library | National context series | W | ❓ | Stage 3 (context) |
| DMC situation reports | Disaster impacts by district/DS | P | ❓ | Stage 3+ |
| OSM / Protomaps | Basemap, infrastructure | D | ✅ ODbL | Stage 1 (basemap) |
| WorldPop / GHSL | Modelled population, built-up area | D | ✅ / ❓ | Stage 3+ |

---

## 7. What this means for Sri Lanka Facts

1. **The opening is integration, not collection.** Spend effort on the spine, harmonisation, verification and explanation. Borrow raw extraction where it is reliable and licensed.
2. **Census 2024 at GN level is ready to become a flagship**, if the reuse position is confirmed.
3. **Boundaries need our own verification step.** No single source is clean (Ampara parent, DS/GN counts, unstable codes).
4. **Licensing decides what we can sell.** Record rights per dataset from day one. Open-license our own work to stand apart from NC and restrictive players.
5. **Partners exist.** nuuuwan (raw data), LDF (structure and documents), Verité (public finance), academics (dengue/MOH). A small, generous network effort costs little and avoids duplicated work.
6. **Funding precedent is thin and competitive.** Grants exist (an EU civic programme, a USD 200k Open Society grant to the RTI Commission 🟡), but a track record comes first. Plan to self-fund through services.
7. **The national macro layer is commoditised.** Show it only as context for places.

---

## 8. Open research questions

1. What does DCS permit for reuse and commercial redistribution of published Census tables? (R02, R04)
2. Which DS and GN units are current? Can the 339 vs 331 DS gap be explained unit by unit? (G02)
3. Where do the MOH and local-authority boundaries come from, and under what terms? (R01, G05)
4. Does LankaStatMap include 2024 data, and how good is it? (R03)
5. Does a DS-level poverty estimate from HIES 2019 or later exist publicly? (R01)
6. What exactly does the CBSL Data Library export, and can it be fetched reproducibly? (R01)
7. Has the Online Safety Act been amended or repealed by launch time? (legal checklist)
8. Is Sri Lanka covered by Google Open Buildings v3, and under which licence? (R01)

---

## Sources

Official and legal: [CPH 2024 Final Report (DCS)](https://www.statistics.gov.lk/Resource/en/Population/CPH_2024/CPH2024_Final_Eng.pdf) · [Ada Derana: final report presented](https://www.adaderana.lk/news.php?nid=120813) · [Daily FT: population 21.78 m](https://www.ft.lk/front-page/Population-hits-21-78-m-as-ageing-trend-deepens-Census-shows/44-790787) · [DCS Appendix D licensed data](https://www.statistics.gov.lk/Publication/Policy/Appendix_D) · [CBSL Data Library launch](https://www.cbsl.gov.lk/en/node/1125) · [CBSL SDDS page](https://www.cbsl.gov.lk/en/statistics/data/special-data-dissemination-standard) · [IMF PR 15/492](https://www.imf.org/external/np/sec/pr/2015/pr15492.htm) · [data.gov.lk](https://data.gov.lk/) · [LIRNEasia brief on the portal](https://intgovforum.org/sites/default/files/webform/igf_2023_workshop_proposal_form/243383/LIRNEasia-Sri-Lankas-Open-Data-Portal.pdf) · [Global Data Barometer SL report](https://data.opendevelopmentmekong.net/en/dataset/1b453718-7d84-421a-ad1c-b8f186c947a3/resource/82c46f54-63be-4051-86bf-8b8a0b188b0d/download/gdb-country-report-sri-lanka.pdf) · [ICTA NSDI](https://icta.lk/projects/digital-government/national-spatial-data-infrastructure-nsdi) · [UN-SPIDER NSDI listing](https://un-spider.org/links-and-resources/data-sources/sri-lanka-national-spatial-data-infrastructure-nsdi-mlld-sri-lanka) · [HDX COD-AB Sri Lanka](https://data.humdata.org/dataset/cod-ab-lka) · [PDPA commencement (Concentric)](https://concentric.ai/sri-lankas-pdpa-takes-effect-january-1-2027-what-global-enterprises-need-to-know/) · [PDPA explained (Neelakandan)](https://neelakandan.lk/insights/data-protection-in-transition-understanding-sri-lankas-new-legal-framework) · [DPA circular (Ada Derana)](https://adaderana.lk/news/cmsjsp2vt0005356q4pjfv4ih) · [OSA repeal bill (readme.lk)](https://readme.lk/a-bill-to-repeal-the-online-safety-act-has-been-gazetted/) · [ICJ on OSA](https://www.icj.org/sri-lanka-icj-calls-for-repeal-or-substantial-revision-of-online-safety-act/) · [OSA two years on (Lidings)](https://www.lidings.com/media/legalupdates/safety_act_Sri%20Lanka) · [2025 local elections](https://en.wikipedia.org/wiki/2025_Sri_Lankan_local_elections) · [Sunday Observer LG polls](https://www.sundayobserver.lk/2025/05/04/news/51449/all-set-for-lg-polls-on-may-6) · [LankaStatMap launch](https://casite-968685.cloudaccess.net/news/political-current-affairs/item/16586-dcs-launches-lanka-star-and-lankastarmap) · [CROPIX (EconomyNext)](https://economynext.com/sri-lanka-launches-tools-digital-platform-for-data-driven-agriculture-258673/)

Ecosystem: [github.com/nuuuwan](https://github.com/nuuuwan) · [lk_census_2024](https://github.com/nuuuwan/lk_census_2024) · [arXiv:2510.04124](https://arxiv.org/abs/2510.04124) · [Lanka Data Foundation](https://opendata.lk/about/) · [LDF content licence](https://opendata.lk/content-license/) · [LDF GitHub](https://github.com/LDFLK) · [OpenGIN](https://github.com/LDFLK/OpenGIN) · [Lanka Data Layer](https://github.com/prabhavalabs/lanka-data-layer) · [Verité platforms](https://www.veriteresearch.org/platforms/) · [PublicFinance.lk](https://publicfinance.lk/en/about) · [Manthri.lk](https://manthri.lk/en/about) · [SOE.lk](https://advocata.org/?p=4085) · [data.advocata.org](https://data.advocata.org/) · [Sri Lanka Dengue Atlas](https://thiyangt.github.io/DengueAtlas/) · [SotM 2025 open mapping session](https://2025.stateofthemap.org/sessions/MM8TEB) · [EU €2.6m civic grant](https://www.ft.lk/front-page/EU-grants-2-6-m-Rs-970-m-to-enhance-civic-participation-accountability-and-transparency/44-791357)

International and technology: [USAFacts AI info page](https://usafacts.org/ai-info-page/) · [Business Insider: $10m](https://www.businessinsider.nl/ex-microsoft-ceo-steve-ballmer-spent-10-million-on-usafactsorg-2017-4) · [OWID ETL architecture](https://owid-docs.readthedocs.io/projects/etl/architecture/our-journey/) · [owid-grapher](https://github.com/owid/owid-grapher) · [Data For India](https://dataforindia.com/about) · [FOSS United grant](https://fossunited.org/grants/directory/data_for_india) · [Nepal in Data launch](https://www.sharesansar.com/newsdetail/bikas-udhyami-launches-nepal-in-data-a-gateway-to-development-statistics-on-nepal) · [Data Commons on Spanner Graph](https://cloud.google.com/blog/products/databases/unify-public-and-private-data-with-data-commons-on-spanner-graph) · [Data Commons MCP](https://blog.datacommons.org/2025/10/02/announcing-the-data-commons-model-context-protocol-server/) · [Overture release notes](https://docs.overturemaps.org/blog/2026/01/21/release-notes/) · [Protomaps downloads](https://docs.protomaps.com/basemaps/downloads) · [Open Buildings v3](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_Research_open-buildings_v3_polygons)
