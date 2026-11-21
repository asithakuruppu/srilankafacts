# Method: statistical tables (HIES poverty, LFS labour force, paddy)

Status: **local build, 2026-11-21, not published** · Code: `pipeline/slf/stat_tables.py` (`uv run slf stat-tables build`) · QA: [docs/qa/stat-tables-2026-11-21/](../qa/stat-tables-2026-11-21/) · Pattern: [census-2024.md](census-2024.md)

Legend: ✅ verified by me · 🟡 claimed by a source · ❌ not found / failed · ❓ assumption.

## What is ingested

| Dataset | Table | Level | Period | Observations |
|---|---|---|---|---|
| `hies-poverty` | DCS *Poverty Indicators 2019*, Table 04 (PDF p.4) | Sri Lanka, 3 sectors, 9 provinces, 25 districts; old and updated poverty line | 2019 | 228 ✅ |
| `labour-force-survey` | DCS *LFS Annual Report 2024*, Tables 12, 12A, 12B (PDF pp.92-94) | Sri Lanka and 25 districts; both sexes, male, female | 2024 | 546 ✅ |
| `paddy-statistics` | DCS district paddy tables, acres and bushels (data.gov.lk CSV copies) | 25 districts | Maha 2010/11, Yala 2012 | 250 ✅ |

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

## Unmatched and not ingested

- Paddy: Uda Walawe and Mahaweli 'H' are paddy management areas, not districts; kept out of place output and listed (2 per season).
- Not ingested, held: two metric (hectare) paddy CSVs with no season stated anywhere (cannot assign a period); 2010 paddy `.xls` (no xls reader; adding `xlrd` needs a decision); LFS and unemployment CSVs 2009-2014 from data.gov.lk.
- Season dates for paddy (Maha Sep-Mar, Yala Apr-Aug) are the conventional windows ❓, not stated in the tables.

## Rights

DCS reuse terms are unclear and D-030/D-032 cover only the census. These datasets have **no `publication` decision**, so the release builder refuses them (`slf.release`), and this build writes only a private folder. The data.gov.lk copies are "License Not Specified" and held only. Nothing here changes any release.

## Limits

LFS and HIES are sample surveys: district values carry sampling error (DCS flags high CVs; none is published in the tables read) ❓. HIES poor-population counts are rounded to 100. HIES 2019 and LFS 2024 are different years with different universes; do not compare them.
