# Census 2024: population by ethnic group and by religion, DS and district

Status: **built, not in any release** · Dataset `census-2024-topic-tables` (step d of D-032, under
D-033) · Period `2024` · Last revised 2026-11-14.

Verification tags: ✅ verified by running or reading the cited source · 🟡 claimed by a source,
not independently checked · ❌ not found or failed · ❓ assumption.

## 1. What is built

For every DS division, district, province and the country, the population split two ways. Each
person is counted in exactly one category of each topic:

| Topic | Categories (DCS's names) | DCS tables (DS / district) | Indicator ids |
|---|---|---|---|
| Ethnic group | 10: Sinhalese, Sri Lanka Tamil, Indian Tamil / Malaiyaga Thamilar, Sri Lanka Moor / Muslim, Burgher, Malay, Sri Lanka Chetty, Bharatha, Veddha, Other | A6 / A2 | `population_ethnicity_*` |
| Religion | 6: Buddhist, Hindu, Islam, Roman Catholic, Other Christian, Other | A7 / A3 | `population_religion_*` |

That gives 32 indicators: 16 counts and 16 shares (count ÷ population × 100).

- **D-033 applies.** Values come from DCS's own DS and district tables, never from sums of GN
  values. DCS's GN files fold any group under 10 people in a GN into "Other", so GN sums
  under-count small groups (Burgher: 25,159 from GN sums, 31,721 in A2 and A6 ✅).
- **No GN values.** Every value carries `information_footprint_ref: ds-2024`. The build fails if
  any ethnicity or religion value is attached to a GN id.
- **Labels** are DCS's category names, with spelling fixed only where DCS's heading has an
  obvious typo: "Sinhalees" → Sinhalese, "Sri lanka Tamil" → Sri Lanka Tamil, "Veddhas" → Veddha.
  Locators keep the heading as printed.
- **No new total.** Each table's "Total number of persons" equals `population_total` from the GN
  population workbook (`census-2024-gnd-tables`) in every place ✅ (§4). Shares use that total.

## 2. How a release carries them (D-033)

- Rows carry `sensitivity: sensitive_group` (every other census row is `public`).
- The 32 indicators are `distribution: places_only`, a new catalogue value. A release puts them in
  the observation downloads and in place files (`api/v1/places/<id>.json`), and lists their
  metadata in `api/v1/indicators.json`. It writes **no** per-level files
  (`api/v1/indicators/<id>/<level>.json`), which are what the website's indicator pages, ranked
  bars and Explore tables read, and the spatial-context stage computes **no** neighbour
  comparisons (`stats/local_*`) for them. Tests cover both.
- The website leaves `places_only` indicators out of every indicator list. On DS, district,
  province and country pages, a separate "Ethnic group and religion" section shows counts and
  shares in DCS's column order (never sorted by value), names the DCS table, and links each count
  to its source. It does not link to an indicator page, and there is no map.
- Counts are shown as well as shares, unlike the other topic-table steps (LA-004, LA-005): D-033
  says "counts and shares", and 16 counts per place is small.
- Profile and similarity spaces already refuse ethnicity and religion inputs (D-015, schema check).

## 3. Source

| File | Level | Snapshot | sha256 (first 12) |
|---|---|---|---|
| `PopulationA_A6.xlsx` (ethnic group) | Sri Lanka, district, DS | 20261112T173250Z | `1b27e53e0c37` ✅ |
| `PopulationA_A7.xlsx` (religion) | Sri Lanka, district, DS | 20261112T173256Z | `e0012c7c463f` ✅ |
| `PopulationA_A2.xlsx`, `PopulationA_A3.xlsx` | Sri Lanka, district (check only) | 20261112T173229Z, 173234Z | `e8aa7d4635ae`, `2486798e3a6d` ✅ |

All from <https://www.statistics.gov.lk/Population/StaticalInformation/CPH2024> (Population
A-series). Rights: unclear; non-commercial publication under D-030 as extended by D-032. Numbers
are stored as text in these files; the parser accepts digits only.

## 4. How DS rows join to the spine

The A-series tables have no codes (AGENTS rule 5), so, as in step (c):

1. **A match file**, `catalog/geographies/name-matches/dcs-census2024-population-a-series-ds.csv`,
   maps each of the 340 DS lines (district code + English label as printed) to a DCS DS code. The
   build never matches names itself.
2. **How it was made (2026-11-14, by the agent):** 339 of the 340 A6/A7 labels are identical to
   the Housing A9–A12 labels and take the same DCS code as the step (c) match file. One differs:
   A6/A7 "Padavisripura" (district 53) where A9–A12 print "Padavisiripura"; it is matched to DCS
   5303 "Padavi Sri Pura", the only DS in district 53 whose GN population adds up to its total.
   The step (c) lead review of the 17 spelling-variant matches covers this file too.
3. **Numeric check, every build:** each DS line's total must equal the sum of GN population for
   its matched DCS code (GN population workbook). All 340 pass ✅. No two DS divisions in the same
   district have the same population ✅, so a wrong match cannot pass by coincidence.
4. DCS 5224 Kalmunai has no spine unit (D-022): its people stay in Ampara district and Sri Lanka,
   with no DS row.

## 5. Checks

All run by the build; any failure stops it.

| Check | Result |
|---|---|
| Title and every category heading where expected, in all four tables | pass ✅ |
| On every line, categories sum to the total | 0 failures ✅ |
| A6 and A7 list the same 366 lines (Sri Lanka, 25 districts, 340 DS) with the same totals | 0 differences ✅ |
| DS lines sum to their district line; district lines sum to Sri Lanka (each table, each category) | 0 differences ✅ |
| A2 and A3 equal the district and Sri Lanka lines of A6 and A7 | 0 differences ✅ |
| DS total = GN sum of population, for the matched DCS code | 340 of 340 ✅ |
| Both topics cover the same places; no value on a GN id | ✅ |

## 6. Values and locators

- DS, district and Sri Lanka values are DCS's own lines. Locators name the file, sheet, row and
  column. Province values are sums of DCS's district lines, with note `aggregate`.
- Values stay `machine_extracted` (AGENTS rule 7), `revision_status: provisional`.

## 7. Gaps

- Final Report: Tables 6.1.11 (ethnic group) and 6.1.15 (religion), 2024, Sri Lanka and all 25
  districts: 390 values, 0 differences ✅ ([QA](../qa/census-2024-ethnicity-religion.md)). DS
  values have no Final Report counterpart. No human check (Q01) ❌.
- The website section was checked against a trial release only; it is not in a published release.
- GN-level ethnicity and religion are not ingested (D-033 allows it for QA only); the folding
  figures above come from the source dossier.
