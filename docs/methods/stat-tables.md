# Method: statistical tables (HIES poverty, LFS labour force, paddy)

Status: **local build, 2026-11-21, not published** · Code: `pipeline/slf/stat_tables.py` (`uv run slf stat-tables build`) · QA: [docs/qa/stat-tables-2026-11-21/](../qa/stat-tables-2026-11-21/) · Pattern: [census-2024.md](census-2024.md)

Legend: ✅ verified by me · 🟡 claimed by a source · ❌ not found / failed · ❓ assumption.

## What is ingested

| Dataset | Table | Level | Period | Observations |
|---|---|---|---|---|
| `hies-poverty` | DCS *Poverty Indicators 2019*, Table 04 (PDF p.4) | Sri Lanka, 3 sectors, 9 provinces, 25 districts; old and updated poverty line | 2019 | 228 ✅ |
| `labour-force-survey` | DCS *LFS Annual Report 2024*, Tables 12, 12A, 12B (PDF pp.92-94) | Sri Lanka and 25 districts; both sexes, male, female | 2024 | 546 ✅ |
| `paddy-statistics` | DCS district paddy tables, acres and bushels (data.gov.lk CSV copies) | 25 districts | Maha 2010/11, Yala 2012 | 250 ✅ |

| `dcs-vital-statistics` | DCS Vital Statistics: births, deaths, marriages registered by district (xlsx Table 2); crude birth and death rates by sex (xlsx Table 1); Registrar General's mid-year population by district and sex (2 PDFs) | Sri Lanka, 9 provinces (rates only), 25 districts | 2014-2026 | 3,030 ✅ |
| `dengue-weekly-district` | NDCU *Weekly Dengue Update*, Table 1 (20 PDFs, weeks 27-46 of 2026) | Sri Lanka and 25 districts (Ampara = Ampara RDHS + Kalmunai RDHS, derived) | weeks 2026-W27 to W46 | 520 ✅ |

Every row carries the snapshot sha256 (recomputed at build time) and a locator (PDF page, table, row label and column, or CSV row and column), `verification = machine_extracted`, and `data_nature` `survey_estimate` (HIES, LFS) or `official_estimate` (paddy).

## How

1. **Snapshots** are immutable files under `raw/dcs/<dataset>/<time>/` (HIES, LFS; fetched politely from statistics.gov.lk with 4 s between requests, sha256 and URL in the `.meta.json`) and `raw/data-gov-lk/...` (paddy; already held).
2. **PDF text** comes from the PDF's own text layer (`swift scripts/pdf_pages.swift <pdf> data/build/stat-tables/pdf-pages/<pdf name> <pages>`), no OCR. One row (Kegalle, LFS Table 12A) is scrambled in the text layer and is reassembled in printed order; its row sums then pass ✅.
3. **Geography only through the reviewed match file** `catalog/geographies/name-matches/dcs-statistical-tables-districts.csv` (rule 5): each printed label maps to a spine id per dataset; labels not listed are unmatched; every target must exist in the spine at build time. Spelling variants (Vavunia, Mullativu, Kilinochchci, Moneragala, Rathnapura, NUWARAELIYA...) are recorded as `spelling_variant`.
4. **Sector rows** (urban, rural, estate) are attached to `LK` with `breakdown = {"sector": ...}`; they are not places.
5. **No value is derived**: the LFS "employed rate" column is not stored (it is 100 minus the unemployment rate); counts are not summed across areas except in checks.

## Checks (all ✅, see QA reports)

- HIES: 1 + 3 + 9 + 25 rows; sector, province and district poor counts sum to the national figure within the printed rounding (to 100).
- LFS: 26 rows in each of three tables; employed + unemployed = labour force and labour force + not in labour force = population on every row (±1 rounding); districts sum to Sri Lanka; male + female = both sexes.
- Paddy: the CSV's gross sown extent sums to the national total I read from the DCS PDF page image (1,804,204 acres Maha 2010/11; 900,795 Yala 2012) ✅. The data.gov.lk file named `maha_2011` is the **2010/11** season: the PDF title says so (the file name is misleading).

## Vital statistics notes (D-061, 2026-11-22)

- Snapshots: `raw/dcs/dcs-vital-statistics/` (two `.xlsx` workbooks from the page's Excel links, two PDFs, and the page itself), fetched with the pipeline's own user agent, 4 s apart.
- Excel cells are read with `openpyxl`; the year and measure headers carry `*` for provisional values (for example 2021 births and marriages, every column from 2022). These rows get `revision_status = provisional`.
- Mid-year PDFs are read from their text layer; the year order of the columns is taken from the page image (2014-2017, 2018-2021, 2022-2024; 2025-2026). Values are stored as printed, in **thousands** (`unit = thousand persons`). The source marks 2018 onwards as provisional.
- **Two universes:** counts are by place of occurrence, rates and population by usual residence (both stated in the DCS notes). Counts divided by population do not give the printed rates, and the pipeline never derives them.
- **Series break:** 2014-2024 estimates are carried forward from Census 2012 and 2025-2026 from Census 2024 (Sri Lanka 21,916 thousand in 2024, 21,756 thousand in 2025). The step is a change of basis.
- Checks ✅ ([QA](../qa/stat-tables-2026-11-22/dcs-vital-statistics.md)): district counts sum exactly to Sri Lanka every year; the both-sexes rate lies between the male and female rates; male + female = total; district populations sum exactly to Sri Lanka; 26 places in each of 13 years.
- Not yet ingested from the same page: infant, neonatal, under-five and maternal mortality by district (2012-2021) and the district life tables.
- Publication: `dcs-vital-statistics` carries a `publication` block under D-061 (non-commercial, attribution, notice), unlike HIES, LFS, paddy and dengue.

## Dengue notes

- Public reports are by district/RDHS, not MOH area, so this is a new dataset (`dengue-weekly-district`); `dengue-by-moh` stays open until NDCU supplies MOH-level counts.
- Week n is read from the next report's previous-week column when held (status `revised`), else from its own report (`provisional`): 155 area-week values changed between first report and the next ✅. Week 46 is provisional.
- Source misprints "Ni" in a few 2025 cells (not used) are read as unreadable, never as 0. Week dates are ISO weeks (report 46 states 9-15 Nov 2026 ✅).
- Not stored: 2025 columns and cumulative "up to week" columns (start dates not stated).

## Unmatched and not ingested

- Paddy: Uda Walawe and Mahaweli 'H' are paddy management areas, not districts; kept out of place output and listed (2 per season).
- Not ingested, held: two metric (hectare) paddy CSVs with no season stated anywhere (cannot assign a period); 2010 paddy `.xls` (no xls reader; adding `xlrd` needs a decision); LFS and unemployment CSVs 2009-2014 from data.gov.lk.
- Season dates for paddy (Maha Sep-Mar, Yala Apr-Aug) are the conventional windows ❓, not stated in the tables.

## Rights

DCS and NDCU reuse terms are unclear and D-030/D-032 cover only the census. These datasets have **no `publication` decision**, so a public release is refused by the release builder; `slf release --preview` (private, `publishable: false`) accepts them. The lead (2026-11-21) said the preview is built without restrictions until permissions arrive. The data.gov.lk copies are "License Not Specified" and held only. Nothing here changes any release.

## Limits

LFS and HIES are sample surveys: district values carry sampling error (DCS flags high CVs; none is published in the tables read) ❓. HIES poor-population counts are rounded to 100. HIES 2019 and LFS 2024 are different years with different universes; do not compare them.

## Atlas and website (private preview)

`uv run slf atlas export ... --stat-tables-dir data/build/stat-tables` copies the latest period of each stat-table indicator into the atlas bundle's `extra/` folder, where the website's Geography lens reads it. Only whole-population rows are shown (HIES district and country rows; LFS both-sexes rows); the sector and sex breakdowns stay in the observation downloads. Each map shows the latest period only (paddy: 2012 Yala; dengue: the latest week). Their rights are unclear (D-030/D-032 cover only the census), so a `--public` bundle leaves them out.
