# Census 2024: five-year age, sector and local authority type by GN

Status: **built, not in any release** · Dataset `census-2024-topic-tables` (step b of D-032) · Period `2024` · Last revised 2026-11-13.

Verification tags: ✅ verified by running or reading the cited source · 🟡 claimed by a source,
not independently checked · ❌ not found or failed · ❓ assumption.

## 1. What is built

For every GN division in DCS's files, the population split three ways. Each person is counted
in exactly one category of each:

| Topic | Categories | Indicator ids |
|---|---|---|
| Five-year age group | 20 (0–4, 5–9 … 90–94, 95 and over) | `population_age_{lo}_{hi}`, `population_age_95_plus` |
| Sector | 3: urban, rural, estate rural | `population_sector_{urban,rural,estate_rural}` |
| Local authority type | 3: municipal council, urban council, pradeshiya sabha | `population_local_authority_{municipal_council,urban_council,pradeshiya_sabha}` |

That gives 51 indicators: 25 counts and 26 shares (count ÷ total population × 100).

- **No new 60–64 count.** The population workbook (`census-2024-gnd-tables`) already publishes
  `population_age_60_64`, and claim ids must stay unique, so this step publishes only
  `population_age_60_64_share`. The two sources agree in every GN ✅ (§4).
- **No new total.** Shares use each file's own Total column. That column equals
  `population_total` from the population workbook in every matched GN ✅.
- **Sector wording (DCS's notes in the file, kept).** "Urban" combines DCS's "Urban" and "Estate
  Urban" sectors. "Estate rural" is the sector the 2012 Census called "Estate".
- **Local authority type** is the kind of local authority governing the GN's area. It is not a
  link to a named local authority (`LK-LA-…`), which needs its own crosswalk.
- **Mixed GNs.** A GN can be split between categories: 1,215 of 14,003 GNs have people in more
  than one sector and 120 in more than one local authority type ✅.

As with the households (LA-004), the 25 counts are `distribution: downloads_only` and the 26
shares go to place pages and the API. That follows LA-004's pattern; the lead has not ruled on
these topics specifically (see "Decisions needed").

## 2. Source

| File | Sheet | Snapshot | sha256 (first 12) |
|---|---|---|---|
| `GN_Level_Population_by_Five_Year_Age_Group.xlsx` | `By Age group(Orignal)` | 20261112T173200Z | `b1842df8f30f` ✅ |
| `GN_Level_Population_by_Sector.xlsx` | `By Sector` | 20261112T173218Z | `1eb5c73d0aa3` ✅ |
| `GN_Level_Population_by_Local_Government_Area.xlsx` | `By LGA` | 20261112T173206Z | `0a42634ef2c8` ✅ |

All from <https://www.statistics.gov.lk/Population/StaticalInformation/CPH2024>. Rights:
unclear; non-commercial publication under D-030 as extended by D-032. DCS's headings are kept
as printed, typos included ("Municiple Council"). The local authority file labels its category
block "Sector"; the module checks the file title instead.

## 3. How it is built

1. **Header check.** The title line, the Total column and every category heading must be where
   the module expects. Otherwise the build stops.
2. **Line types.** Each file has a Sri Lanka line, a line per district, a line per DS division
   (under its district) and a line per GN. The module tells them apart by which code columns
   are filled.
3. **Row check.** On every line, GN or subtotal, the categories must add up to the total. One
   failure stops the build. All lines pass ✅.
4. **Join.** GN codes (district, DS, GN) join to the spine through the G02 crosswalk, never by
   name. 13,962 GNs match. The 41 unmatched GNs are the same as in the other census files.
5. **Totals.** DS, district, province and country values are sums of all GN rows, unmatched
   GNs included (province comes from the households file's district-to-province codes). DCS DS
   5224 Kalmunai has no spine unit (D-022).
6. **Check against DCS's own subtotals.** Our sums by DCS DS code, by district and for Sri Lanka
   must equal DCS's subtotal lines in the same file, for the total and every category. Any
   difference is a QA error. Result: 340 DS + 25 districts + 1 national line × 3 files, 0
   differences ✅. No value is taken from the subtotal lines.

Locators name the file, sheet, row and column. Values stay `machine_extracted` (AGENTS rule 7)
and `revision_status: provisional`.

## 4. Cross-checks with the population workbook ✅

Run once on the build (a script, not part of the pipeline), over the 13,962 matched GNs:

| Check | GNs that differ |
|---|---:|
| Total column = `population_total`, each of the three files | 0 |
| 0–4 + 5–9 + 10–14 = `population_age_0_14` | 0 |
| 15–19 … 55–59 = `population_age_15_59` | 0 |
| 60–64 = `population_age_60_64` | 0 |
| 65–69 … 95 and over = `population_age_65_plus` | 0 |

## 5. Gaps

- **5 GNs are missing from all three files.** They are in the households file and have
  population 0 in the population workbook: 4112185, 4112220, 4112225, 5110025, 7210065. They
  get no age, sector or local authority values, rather than invented zeros. Listed in QA.
- No comparison with the Final Report PDF ❌. No human check (Q01 not run for this dataset) ❌.
- Small numbers: five-year age shares in small GNs are unstable. The small-denominator flag
  (D-026) has not been checked on these indicators ❓.
- Not in a release yet. The trial release size is in the QA report.
