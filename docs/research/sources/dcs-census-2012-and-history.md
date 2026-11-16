# Source dossier: DCS Census 2012 tables and historical district populations

Prompts R01 + G06 · checked 2026-11-14/15 by an agent · catalogue:
`catalog/datasets/census-2012-tables.yaml`, `catalog/datasets/census-district-series.yaml`,
`catalog/datasets/nuuuwan-lk-census-2012.yaml` · rights memo:
[`../rights/census-2012-and-history.md`](../rights/census-2012-and-history.md)

Tags: ✅ verified by reading or running · 🟡 claimed by a source, not checked · ❌ not found or failed · ❓ assumption.

## Answer for the lead

- **2012 DS-level population (final) is published by DCS** and now held ✅: Statistical Abstract
  2024, Table 2.7 (PDF, 331 DS rows, trilingual).
- **2012 GN-level population is published as a DCS-authored PDF, but we could not find it on a
  DCS address** ❌. The copy held is the one mirrored by nuuuwan. Its DS totals agree with Table
  2.7 in all 331 cases and its district totals with the 2024 Final Report ✅. Using it is D-038
  (Proposed).
- **District populations 1871–2012** are published by DCS in Statistical Abstract 2024 Table 2.1
  (thousands) ✅, and 1981–2024 as exact counts in Census 2024 Final Report Table 3.3 ✅. The two
  tables disagree for 1981 and 2001 (see the QA report).
- **Administrative structure 1981, 2012, 2024** (DS, GN and local authority counts by district):
  Final Report 2024 Tables 2.2–2.4 ✅, and district creations 1871–2024 in Table 2.1 ✅.
- **No reuse terms** on any of these pages or PDFs ❌. Rights `unclear`, as for Census 2024.

## Findings

| Finding | Status | Evidence |
|---|---|---|
| DCS "Population Census 2012" page lists per-district pages (each an iframe of a district map PDF), the 2012 Final Report and the 5% sample report; its "Latest District, DS Division and GN Division Level Information" link returns 404 | ✅ / ❌ | `statistics.gov.lk/Population/StaticalInformation/CPH2011` (200, 2026-11-14); link target `…/PopHouSat/CPH2011/index.php?fileName=Activities/TentativelistofPublications` (404) |
| The 2012 Final Report PDF on the DCS site is the **Sinhala** edition (274 pages, legacy font encoding), with district tables but no DS tables found | ✅ | `…/Resource/en/Population/CPH_2011/CensusPopulationHousing2012-FinalReport.pdf` (200, 107.6 MB; read, not snapshotted) |
| Statistical Abstract 2024, chapter 2, has Table 2.1 (population by sex and district, census years), 2.7 (population by DS division and sex, Census 2012) and 2.8 (density) | ✅ | `statistics.gov.lk/abstract2024/chapter2` (200); `…/CHAP2/2.1.pdf`, `2.7.pdf` (200, snapshotted) |
| Abstract Table 2.1 covers 1871–2012 in thousands; footnote: Gampaha and Mullaitivu carved out September 1978, Kilinochchi February 1984; 2001 Northern/Eastern figures are estimates; 2012 from the Final Report | ✅ | snapshot `raw/dcs/census-district-series/20261114T194918Z/abstract2024_table2.1.pdf`, pages 1 and 3 |
| Abstract Table 2.7: 331 DS rows; one printed figure uses a point as thousands separator ("2.324,349", Colombo district) | ✅ | snapshot `raw/dcs/census-2012-tables/20261114T194917Z/abstract2024_table2.7.pdf` |
| Census 2024 Final Report Tables 2.1 (number of districts 1871–2024), 2.2–2.4 (administrative structure 1981, 2012, 2024), 3.1 (national population and census dates 1871–2024), 3.3 (district population 1981, 2001, 2012, 2024) | ✅ | existing snapshot `raw/dcs/census-2024-gnd-tables/20261107T171418Z/CPH2024_Final_Eng.pdf`, PDF pages 60, 62–64, 67, 69 |
| Table 2.4's text layer runs footnote markers into the numbers ("5321" is 532 with note 1; Ampara "204" is 20 with note 4) | ✅ | page 64 text vs. footnotes; numbers read from the page, not parsed |
| DCS 2012 *provisional* tables (A1, A5 by DS) existed at `…/PopHouSat/CPH2011/Pages/Activities/Reports/cph2011Pub/pop31–33.pdf`; now only in the Web Archive (captured 2012-11-13). National total 20,263,723 (provisional), not the final 20,359,439 | ✅ | Web Archive CDX; files read, not used |
| The DCS-authored GN file ("Population by GN division and sex 2012", 300 pages, metadata created 2015-05-06 from `Population by GN and Sex 2012.xlsx`) was not found on any DCS address, live or archived | ❌ | live site links above; Web Archive CDX searches of `…/PopHouSat/CPH2011/…` and `…/Resource/en/Population/CPH_2011/…` |
| nuuuwan `lk_census_2012`: MIT (code), created 2026-03-26, last push 2026-06-13; per topic a `source.pdf` (the DCS file), `raw_data.json`, `data.json` (with region ids) and `validation.json` | ✅ | GitHub API; snapshot at commit `8d8af05` |
| nuuuwan's region ids are assigned by matching GN **names** to a later GN list; its `validation.json` lists the 9 DS divisions created after 2012 as "missing" | ✅ | `data.json`, `validation.json` read; therefore not used as ids |
| data.gov.lk lists a dataset "Population by District in Census Years" (1871–2012) | 🟡 | search result only; the page did not load (connection failed, 2026-11-14) |
| nuuuwan also holds `lk_census_2001` and `lk_census_1971` | ✅ | GitHub search API; not opened |

## URLs checked (2026-11-14)

| URL | HTTP |
|---|---|
| https://www.statistics.gov.lk/Population/StaticalInformation/CPH2011 | 200 |
| https://www.statistics.gov.lk/Population/StaticalInformation/CPH2012 | 200 (41-byte body) |
| https://www.statistics.gov.lk/PopHouSat/CPH2011/index.php | 404 |
| https://www.statistics.gov.lk/Population/StaticalInformation/CPH2011/CensusPopulationHousing2012-FinalReport | 200 (iframe page) |
| https://www.statistics.gov.lk/Resource/en/Population/CPH_2011/CensusPopulationHousing2012-FinalReport.pdf | 200 |
| https://www.statistics.gov.lk/Resource/en/Population/CPH_2011/NuwaraEliya.pdf | 200 (map) |
| https://www.statistics.gov.lk/Censuses | 200 |
| https://www.statistics.gov.lk/abstract2024/chapter2 | 200 |
| https://www.statistics.gov.lk/abstract2024/CHAP2/2.1.pdf · 2.7.pdf · 2.8.pdf | 200 |
| https://data.gov.lk/dataset/population-district-census-years | failed (no response) |
| https://raw.githubusercontent.com/nuuuwan/lk_census_2012/8d8af05…/data/population-gender/source.pdf · data.json | 200 |

## Snapshots taken (immutable, `pipeline/data/raw/`)

| Key | sha256 (first 12) |
|---|---|
| `raw/nuuuwan/nuuuwan-lk-census-2012/20261114T194914Z/population-gender_source.pdf` | `85a303452586` |
| `raw/nuuuwan/nuuuwan-lk-census-2012/20261114T194916Z/population-gender_data.json` | `45d0969d695d` |
| `raw/dcs/census-2012-tables/20261114T194917Z/abstract2024_table2.7.pdf` | `d80a23151e21` |
| `raw/dcs/census-district-series/20261114T194918Z/abstract2024_table2.1.pdf` | `083884051271` |

## Open questions (to DCS; draft in `docs/outreach/2026-11-15-dcs-census-history-queries.md`)

1. Where does DCS publish the 2012 GN-level population file, and is there an official
   2012↔2024 GN or DS concordance?
2. Why do the 1981 and 2001 district figures in Statistical Abstract Table 2.1 differ from Final
   Report 2024 Table 3.3, and why do Table 3.3's 1981 districts sum to 217,050 less than its
   national total?
3. Which districts gave up territory to Gampaha and Mullaitivu (1978) and Kilinochchi (1984), and
   are earlier census figures available on current district boundaries?
4. Reuse terms (same question as the 2026-11-07 letter).
