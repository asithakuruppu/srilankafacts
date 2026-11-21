# Statistical tables not ingested (2026-11-21)

Checked by plain fetches with a polite agent, one request per few seconds. Tags: ✅ checked, ❌ not found or blocked, ❓ assumption.

| Dataset | Finding | What is needed from the lead |
|---|---|---|
| `school-census` | ✅ moe.gov.lk/statistics/ and /school-census/ load and describe the census. ❌ No downloadable table was found on either page (no PDF or xlsx link). Rights unclear (`ministry-of-education`). | A link or file for a school census statistical abstract (zone-level tables), or a request to the Ministry's planning branch; plus written reuse terms. |
| `annual-health-bulletin` | ✅ health.gov.lk/annual-health-bulletin/ links AHB PDFs for 2013-2019 (and pages for 2022-2024). Tables are by district/RDHS in long PDFs. Not parsed: needs a per-year table review, and the RDHS scheme has no spine geography (D-046). Rights unclear. | Choose a year and the tables wanted (e.g. facilities and beds by district); confirm that district-level rows are enough, since RDHS has no spine units. |
| `dengue-by-moh` | ✅ dengue.health.gov.lk publishes weekly update PDFs whose Table 1 is by **district/RDHS** (26 rows incl. Kalmunai), not by MOH area; MOH areas appear only in "high risk" lists. ❌ No MOH-level table found. | Decide whether to ingest the district/RDHS weekly series (it is obtainable and fits the spine with Kalmunai handled as in D-022), or ask the National Dengue Control Unit for MOH-level counts. |
| `cbsl-national-series` | ❌ www.cbsl.gov.lk answers a plain fetch with HTTP 403 (bot protection); not worked around. | Download the wanted series (inflation, exchange rate, GDP, policy rate) by hand from the CBSL statistics pages and put the files on the drive, with the licence note. |
| `hies-poverty` DS level | ✅ `PovertyStatisticsDSDivision.pdf` is the 2002 headcount on old DS boundaries in image tables; no DS crosswalk, so not ingested (rule 5). | None unless DS-level 2019 estimates are wanted: ask DCS. |

All of these sources have rights `unclear` and no publication decision.
