# New source candidates (scan of 2026-11-22)

A web scan for data sources the project does not yet hold or list. It builds on the [spatial discovery catalogue](../spatial/discovery-catalogue.md) (global rasters, HDX, NSDI) and the [ecosystem landscape](../ecosystem-landscape.md) (official producers), and skips everything already in `catalog/datasets/` or assessed there. **Nothing was downloaded or ingested**; this is a shortlist for the lead.

**Legend:** ✅ read on the primary page today · 🟡 from a search result or secondary page, not opened · ❌ looked for, not found or failed · ❓ assumption or open question.

**Method and limits:** about 25 web searches, primary-page reads by a fetch agent, and JavaScript-rendered pages (CROPIX, Department of Examinations, Global Solar Atlas terms) read in the app's browser. The Epidemiology Unit site returned "509 Bandwidth Limit Exceeded" ❌; the CBSL press-release PDF and the HREA site returned HTTP 403 ❌; the EOG licence PDF and the RGD mid-year PDF could not be turned into text ❌. No API endpoint was called.

---

## 1. Shortlist, ranked

| # | Source | What it adds | Level | Rights | Effort | Recommendation |
|---|---|---|---|---|---|---|
| 1 | DCS vital statistics and mid-year population | Population **every year** between censuses; births, deaths, infant and maternal mortality | District | No terms; "All Rights Reserved" footer ✅ (same position as D-030) | S | **Do next** |
| 2 | CROPIX API gateway (Department of Agriculture) | **New geography schemes** (agrarian service centres, Mahaweli systems, agriculture zones) with GN membership; crop extents by district and season | GN to province | No terms found on the gateway ❌ | S–M | **Do next** (internal); ask for terms |
| 3 | Department of Examinations performance reports | Exam results (O/L, A/L, Grade 5) by year | Province, district, education zone 🟡; school indices 2017–2021 ✅ | "All Rights Reserved" footer ✅ | M (PDF tables) | Next, aggregates only |
| 4 | Epidemiology Unit Weekly Epidemiological Report | All notifiable diseases (leptospirosis, etc.), not only dengue | RDHS / MOH 🟡 | Not checked ❓ | S (extends `dengue-weekly-district`) | Next, when the site is reachable |
| 5 | Global Solar Atlas | Solar potential per place | ~250 m raster 🟡 | CC BY 4.0 plus a WIPO mediation clause ✅ | S | Add to landscape roll-up |
| 6 | DLR World Settlement Footprint Evolution | Settlement extent **every year** 1985–2015 at 30 m | Raster | CC-BY-4.0 ✅ | S–M | Add as a second built-up claim (D-019) |
| 7 | EOG annual VIIRS night-time lights (VNL v2.2) | A yearly activity and electrification proxy since 2012 | ~500 m raster ✅ | "Many of" the products CC BY 4.0 ✅; which ones ❓ | S | Read the licence PDF, then add |
| 8 | Impact Observatory / Esri annual land cover | 9-class land cover every year, 10 m, 2017–2023 at least 🟡 | Raster | CC BY 4.0 🟡 | M | Later; WorldCover covers one year now |
| 9 | CBSL provincial GDP | Output by province, yearly (2024 released 22 Dec 2025 🟡) | Province | Not checked ❓ | S | Later; no district GDP exists ❌ |
| 10 | SEDAC Global Gridded Relative Deprivation Index v1 | A modelled deprivation grid, 2010–2020 | ~1 km ✅ | "Openly shared, without restriction" (EOSDIS guidance) ✅ | S | Later, as a claim beside OPHI and HIES, with its information floor |

Watch list (no action yet): DCS **Economic Census 2025/26 (agricultural activities)**, preliminary report scheduled 28 Aug 2026 and final 31 Dec 2026 on the DCS release calendar 🟡 (add to the freshness calendar); Overture **Transportation** and **Divisions** themes, ODbL 🟡 (little beyond the OSM extract we hold); **GBIF** occurrences filtered to CC0/CC BY, about 859,000 records in a 2021 snapshot, most of them eBird 🟡 (strong sampling bias); Global Wind Atlas, CC BY 4.0 in a secondary catalogue 🟡.

---

## 2. Details

### 2.1 DCS vital statistics and mid-year population ✅

Page: [statistics.gov.lk › Vital Statistics](https://www.statistics.gov.lk/Population/StaticalInformation/VitalStatistics) (last update 2026-11-19 ✅). Tables found on the page ✅:

- Number of births, deaths and marriages registered **by district, 2019–2025** (PDF and Excel)
- Crude birth and death rates **by province, district and sex, 2019–2025** (PDF and Excel)
- Mid-year population estimates **by district and sex, 2014–2024 and 2025–2026**; by age group and sex
- Neonatal, infant, under-five and maternal mortality rates **by district, 2012–2021**
- Life tables by district and sex, 2011–2013; by district, 2000–2002

Why it matters: the platform's denominators are census years only. Mid-year estimates give a district population for every year, and the vital rates are the first health-outcome series by district. The sub-pages for the mid-year tables returned only the word "back" to the fetch agent ❌, so their file formats are not confirmed ❓. Rights: no reuse terms, "All Rights Reserved" in the footer ✅, the same situation as the census tables under D-030/D-032. The Registrar General's Department also publishes district birth tables (2021 seen 🟡) and a 2025 mid-year review PDF (not readable as text ❌).

### 2.2 CROPIX API gateway ✅

Page: [apiweb.doa.gov.lk](https://apiweb.doa.gov.lk), launched January 2026 🟡. The public catalogue lists **14 endpoint groups and 102 endpoints** with base URL `http://data.doa.gov.lk`, "available for broad discovery without credentials" ✅; another 140+ need registration ✅. Endpoint names include ✅:

- **Geography:** provinces, districts, DS and GN divisions; provincial director, deputy director and ADA segments; DOA divisions; **agrarian development and ASC divisions**; district commissioner divisions; **AI regions**; **Mahaweli authorities, systems, blocks and units**; "GN Divisions By Agriculture Zones" and "GN Divisions By Mahaweli System ID".
- **Crops:** crop categories and varieties; "All District Crop Cultivations By Year"; "Province-Wise Crop Cultivation Totals For All Years"; season-wise monthly cultivation; approved national progress by season.

Why it matters: the GN-membership endpoints are ready-made crosswalk material for geography schemes the spine does not have (agrarian service areas and Mahaweli systems matter for farming and irrigation questions), and crop extents go beyond the paddy series. Cautions: no licence or terms text on the gateway pages ❌; whether its GN codes match DCS codes or p-codes is unknown ❓; two endpoint groups list individual farmers ("Get All GAP Farmers", "Seed Act Registered Farmers") and must **never** be collected (rule 11).

### 2.3 Department of Examinations ✅

Page: [doenets.lk/statistics](https://www.doenets.lk/statistics) ✅. "Performance of Candidates" reports for G.C.E. O/L (2011–2025), A/L (to 2025) and the Grade 5 Scholarship (to 2026); "School Performance Indices" for O/L 2017–2021 and A/L 2019 (school level); statistical handbooks 2005–2019; 2015 gender-wise tables by province and district ✅. A secondary page says the 2024 O/L report breaks results down by province, district and education zone 🟡 (report not opened). Rights: "Copyright © 2022 … All Rights Reserved" ✅. Format: PDF ❓. Education zones are a scheme we already reference through the school census.

Care: school-level indices are about institutions, not people, but league tables are sensitive. Recommendation: publish zone and district aggregates only until the lead decides otherwise.

### 2.4 Epidemiology Unit Weekly Epidemiological Report 🟡

Each WER has a table "Selected notifiable diseases reported by Medical Officers of Health" with weekly and cumulative counts 🟡 (search snippets of 2025–2026 issues). 13,738 leptospirosis cases were notified in 2024 🟡. The site returned "509 Bandwidth Limit Exceeded" today ❌, so the table's geography (RDHS or MOH) is not confirmed ❓. It would extend `dengue-weekly-district` (on main) to other diseases. The bandwidth limit means a slow, cached schedule.

### 2.5 Spatial layers with open licences

| Layer | Licence evidence | Resolution and period | Note |
|---|---|---|---|
| [Global Solar Atlas](https://globalsolaratlas.info/support/terms-of-use) | "The Works are licensed under the Creative Commons 4.0 Attribution International license, CC BY 4.0" plus mandatory WIPO mediation and arbitration ✅ | Long-term average 🟡 | The arbitration clause is unusual; the lead should know it exists |
| [WSF Evolution (DLR)](https://geoservice.dlr.de/web/datasets/wsf_evo) | "License: CC-BY-4.0", attribution "© 2024 DLR" ✅ | 30 m, yearly 1985–2015, 2°×2° GeoTIFF tiles ✅ | Yearly where GHSL has 5-year epochs; a second built-up claim |
| [EOG VIIRS VNL](https://eogdata.mines.edu/products/vnl/) | "Many of the VIIRS Nighttime Lights data are available under" CC BY 4.0 ✅; the per-product PDF was unreadable ❌ | 15 arc-seconds (~500 m), latest version v2.2 ✅; last year ❓ | Earth Engine lists the annual composites as public domain 🟡 |
| [SEDAC GRDI v1](https://www.earthdata.nasa.gov/data/catalog/esdis-ciesin-sedac-pmp-grdi-2010-2020-1.00) | "openly shared, without restriction" ✅ | 30 arc-seconds (~1 km), 2010–2020 ✅ | A modelled index about people; show its information floor |
| Impact Observatory 10 m LULC | CC BY 4.0 on the AWS registry 🟡 | 10 m, yearly from 2017 🟡 | Esri says the series now reaches 2025 🟡 |

---

## 3. Restricted or not usable as planned

| Source | Finding | Consequence |
|---|---|---|
| Global Data Lab subnational HDI | "Commercial use is only possible after written permission" ✅ | Non-commercial only (rule 4); not acquired |
| DCS microdata (Lanka Datta, `nada.statistics.gov.lk`) | Priced files (LFS 2024 USD 804.28, HIES 2019 USD 3,431.40) and no onward sharing without the Director General's approval 🟡 | Not for publication. The catalogue's variable lists are useful metadata, and the files could support small-area work with a partner (OPP-27) |
| Aswesuma beneficiary lists (Welfare Benefits Board) | Lists of named households displayed at DS and GN offices and on wbb.gov.lk 🟡 | **Do not scrape** (rule 11). Ask the Board for aggregate counts by DS or GN instead |
| HREA electricity access | Licence given as GPLv3 on GitHub and CC BY 4.0 on Planetary Computer 🟡; site 403 ❌; covers countries not fully electrified by 2015, so Sri Lanka may be absent ❓ | Skip |
| Police crime data on data.gov.lk | 2010–2012 only, "License Not Specified" 🟡 | Too old; no current open series found ❌ |

## 4. Gaps nobody fills yet

- **District GDP:** none found ❌. CBSL's provincial GDP is a top-down split of DCS national GDP 🟡.
- **DS-level poverty after 2012/13:** a World Bank piece mapped poverty for about 300 DS divisions from Census 2011/12 and HIES 2012/13 🟡; no HIES 2019 equivalent found ❌. HIES 2019 is representative only to district level 🟡.
- **Local government 2025 results by ward:** no consolidated dataset found ❌; results are issued per local authority 🟡. Ward boundaries are also missing.
- **Transit:** no official bus or rail GTFS ❌. Transitland lists a Lanka Metro Transit feed 🟡; NTC's 2025 statistics show 418 private and 813 SLTB inter-provincial routes as PDF maps 🟡.
- **Air quality:** CEA runs two automated stations (Battaramulla, Kandy) 🟡; IQAir lists 11 CEA-managed sensors 🟡. Too sparse for place-level values.

## 5. Sources

Read today: [DCS Vital Statistics](https://www.statistics.gov.lk/Population/StaticalInformation/VitalStatistics) · [CROPIX API gateway](https://apiweb.doa.gov.lk) · [Department of Examinations statistics](https://www.doenets.lk/statistics) · [Global Solar Atlas terms](https://globalsolaratlas.info/support/terms-of-use) · [DLR WSF Evolution](https://geoservice.dlr.de/web/datasets/wsf_evo) · [EOG VNL](https://eogdata.mines.edu/products/vnl/) · [SEDAC GRDI](https://www.earthdata.nasa.gov/data/catalog/esdis-ciesin-sedac-pmp-grdi-2010-2020-1.00) · [Global Data Lab terms](https://globaldatalab.org/termsofuse/).

Search results only (not opened): [CBSL provincial GDP 2024](https://www.cbsl.gov.lk/sites/default/files/cbslweb_documents/press/pr/press_20251222_pgdp_2024_e.pdf) · [DCS release calendar](https://www.statistics.gov.lk/qlink/ADRCalender) · [DCS microdata prices, Appendix B](https://www.statistics.gov.lk/Publication/Policy/Appendix_B) · [Lanka Datta HIES 2019](https://nada.statistics.gov.lk/index.php/catalog/476) · [Epidemiology Unit WER](https://www.epid.gov.lk) · [CROPIX launch](https://www.newswire.lk/2026/01/22/govt-launches-cropix-national-digital-platform-for-agri-data/) · [O/L 2024 performance report summary](https://lankapastpapers.com/statistical-report-performance-analysis-of-g-c-e-o-l-examination-2024-released-2025) · [Impact Observatory LULC on AWS](https://registry.opendata.aws/io-lulc/) · [Overture Divisions guide](https://docs.overturemaps.org/guides/divisions) · [GBIF Sri Lanka CC0/CC BY download, 2021](https://doi.org/10.15468/dl.bf7j4e) · [HREA on Planetary Computer](https://planetarycomputer.microsoft.com/api/stac/v1/collections/hrea) · [World Bank: understanding poverty in Sri Lanka](https://www.worldbank.org/en/news/feature/2017/03/02/part1-understanding-poverty-sri-lanka) · [Aswesuma list report](https://www.newswire.lk/fhpq) · [CEA air quality](https://cea.lk/web/air-quality) · [Transitland Lanka Metro Transit](https://www.transit.land/feeds/f-lanka~metro~transit) · [NTC statistics 2025](https://ntc.gov.lk/corporate/pdf/2025/stat/Stat2025-EN.pdf) · [data.gov.lk security topic](https://data.gov.lk/search/field_topic/national-security-and-safety-24).
