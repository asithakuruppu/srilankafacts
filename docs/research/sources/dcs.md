# Source dossier: Department of Census and Statistics (DCS), Census 2024

Prompt R01 · checked 2026-11-07 · catalogue: `catalog/sources/dcs.yaml`, `catalog/datasets/census-2024-gnd-tables.yaml`, `catalog/datasets/dcs-gn-reference.yaml`
Legend: ✅ verified by reading or running · 🟡 claimed by a source · ❌ not found · ❓ assumption

## Why we need it
The authoritative population and housing figures for every GN division (Stage 1 Census Atlas) and the unit codes for census joins (G02).

## Findings

| Finding | Status | Evidence |
|---|---|---|
| The CPH 2024 page lists GN-level Excel and PDF downloads: population (by sex and age group), housing, households, occupied housing units, and GN-level tables by ethnic group, five-year age group, local government area, religion and sector | ✅ | `https://www.statistics.gov.lk/Population/StaticalInformation/CPH2024` (snapshot `raw/dcs/census-2024-gnd-tables/20261107T165043Z/CPH2024_page.html`) |
| The GN population workbook is titled "…by Sex and Age Group (Provisional)" with 14,008 GN rows in 340 DS divisions and 25 districts; columns carry province, district, DS and GN codes and names, plus GN number | ✅ | snapshot `raw/dcs/census-2024-gnd-tables/20261107T165036Z/GN_population.xlsx` (sha256 `2e0168c5…`) |
| The final report is a 266-page PDF (ISBN 978-624-6716-46-2), last modified 2026-06-10 per the server | ✅ | snapshot `raw/dcs/census-2024-gnd-tables/20261107T171418Z/CPH2024_Final_Eng.pdf` (sha256 `a6dea938…`) |
| A "Grama Niladhari Divisions" reference page exists at `/ref/GNbyDistrict` | ✅ | snapshot `raw/dcs/dcs-gn-reference/20261107T165045Z/GNbyDistrict.html` (content not yet analysed) |
| **No copyright notice, licence or terms of use** on the CPH 2024 page, the homepage, the GN workbook, or the first six and last three pages of the final report | ❌ | pages read 2026-11-07 (see the URL table below) |
| "Appendix D: Terms and Conditions on the Use of Licensed Data Files" covers **microdata** requests only; it says the data provided should not be "shared, redistributed or sold" | ✅ | `https://www.statistics.gov.lk/Publication/Policy/Appendix_D` §8 (snapshot `raw/dcs/dcs-policy/20261107T171448Z/Appendix_D.pdf`) |
| Contact route published on the final report's back cover: information@statistics.gov.lk, 011 214 7000, "Sankyana Mandiraya", 306/71 Polduwa Road, Battaramulla | ✅ | final report p.266 |
| Access classes: `download_table` (Excel), `pdf`, `licensed_microdata` (Appendix D) | ✅ | as above |
| Update frequency: census every ~10 years; the GN workbook is labelled provisional while the final report is out, so GN figures may be revised | 🟡 | workbook title vs final report |

## Community extractions (cross-checks only)

| Project | What | Licence | Freshness |
|---|---|---|---|
| `nuuuwan/lk_census_2024` | GN-level JSON per topic (14,008 GN ids `LK-DDSSGGG`), final-report tables | MIT (code repo) ✅ | pushed 2026-08-05 ✅ |
| `prabhavalabs/lanka-data-layer` | Census 2024 population by sex, age, ethnicity, religion | README: "2024: not stated" for licence 🟡 | pushed 2026-09-30 ✅ |

## URLs checked (2026-11-07)

| URL | HTTP |
|---|---|
| https://www.statistics.gov.lk/ | 200 |
| https://www.statistics.gov.lk/Population/StaticalInformation/CPH2024 | 200 |
| https://www.statistics.gov.lk/Population/StaticalInformation/CPH2024/GN_population_excel | 200 (xlsx) |
| https://www.statistics.gov.lk/Population/StaticalInformation/CPH2024/GN_housing_excel | 200 (xlsx) |
| https://www.statistics.gov.lk/Resource/en/Population/CPH_2024/CPH2024_Final_Eng.pdf | 200 (pdf, 21.4 MB) |
| https://www.statistics.gov.lk/ref/GNbyDistrict | 200 |
| https://www.statistics.gov.lk/Publication/Policy/Appendix_D | 200 (pdf) |
| https://www.statistics.gov.lk/robots.txt | 200, but the body is "page not found", so there are no robots rules |

## Open questions
1. Reuse terms for the published tables (asked in the DCS letter draft).
2. Will the provisional GN figures be revised to match the final report? If so, when?
3. Is `/ref/GNbyDistrict` the official current GN list? It may help resolve 14,008 (census) vs 14,043 (COD-AB).
4. Topic tables (2026-11-12): households, amenities, ethnicity, religion, five-year age, sector and local authority type are published at GN level and are now snapshotted. Structure and materials are DS level only. See [dcs-census-2024-topic-tables.md](dcs-census-2024-topic-tables.md).
