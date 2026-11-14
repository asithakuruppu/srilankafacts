# Census 2024: housing unit structure and wall, roof and floor materials by DS

Status: **built, not in any release** · Dataset `census-2024-topic-tables` (step c of D-032) · Period `2024` · Last revised 2026-11-14.

Verification tags: ✅ verified by running or reading the cited source · 🟡 claimed by a source,
not independently checked · ❌ not found or failed · ❓ assumption.

## 1. What is built

For every DS division, district, province and the country, occupied housing units split four
ways. Each housing unit is counted in exactly one category of each topic:

| Topic | Categories | DCS tables (DS / district) | Indicator ids |
|---|---|---|---|
| Structure | 10: single house 1 floor, 2 floors, more than 2; attached house 1, 2, 3–4, 5–10, 11–19, 20+ floors; other | A9 / A1 | `housing_structure_*` |
| Main wall material | 11: brick, cement block, granite/cube stones, cabook, pressed soil bricks, mud/warichchi, cadjan/palmyrah, plank/metal sheet/asbestos, zinc aluminium sheets, other, not relevant | A10 / A2 | `housing_wall_*` |
| Main roof material | 8: tile, asbestos, concrete, zinc aluminium sheet, metal sheet, cadjan/palmyrah/straw, other, not relevant | A11 / A3 | `housing_roof_*` |
| Main floor material | 8: cement, terrazzo/tile/granite/finished wood/titanium, concrete, mud, wood, sand, other, not relevant | A12 / A4 | `housing_floor_*` |

That gives 74 indicators: 37 counts and 37 shares (count ÷ occupied housing units × 100).

- **No GN values.** DCS publishes these tables for DS divisions and districts only. Every value
  carries `information_footprint_ref: ds-2024`: the finest unit the information comes from is
  the DS division. GN pages must not show these as GN facts (AGENTS rule 7).
- **No new total.** Each table's "Number of housing units" equals `occupied_housing_units` from
  the GN housing workbook (`census-2024-gnd-tables`) in every place ✅ (§4). Shares use that
  total; this step does not publish a second copy of it.
- **"Attached house" floors (reading to confirm ❓).** DCS's English headings say "Attached House
  - 1st Floor", "2nd Floor", "3rd or 4th Floors" and so on. The Sinhala ("1 මහල") and Tamil
  ("2 தளங்கள்", plural) headings appear to give the number of floors in the building, not the
  floor the unit is on. Names follow that reading ("Attached house, 2 floors"). Locators keep
  DCS's English heading. The lead should confirm the reading.
- **"Not relevant" (as printed: "Not Relavent").** In every one of the 374 places, the wall,
  roof and floor "Not relevant" counts each equal the structure "Other" count ✅. It looks like
  DCS records no materials for "Other" housing units, but the tables do not say so ❓. DCS's
  Final Report (Table 11.6) has no "Not relevant" line and folds it into "Other" ✅. Labelled
  as DCS's category, with no interpretation.
- As with the households and the age, sector and local authority topics (LA-004, LA-005), the 37
  counts are `distribution: downloads_only` and the 37 shares go to place pages and the API.

## 2. Source

| File | Level | Snapshot | sha256 (first 12) |
|---|---|---|---|
| `HousingA_A9.xlsx` (structure) | Sri Lanka, district, DS | 20261112T173346Z | `eaf028784449` ✅ |
| `HousingA_A10.xlsx` (wall) | Sri Lanka, district, DS | 20261112T173351Z | `cc03307167cd` ✅ |
| `HousingA_A11.xlsx` (roof) | Sri Lanka, district, DS | 20261112T173356Z | `dead8fbe90cf` ✅ |
| `HousingA_A12.xlsx` (floor) | Sri Lanka, district, DS | 20261112T173402Z | `ef543939789a` ✅ |
| `HousingA_A1.xlsx` … `A4.xlsx` | Sri Lanka, district (check only) | 20261112T173301Z … 173318Z | see dossier |

All from <https://www.statistics.gov.lk/Population/StaticalInformation/CPH2024> (Housing
A-series). Rights: unclear; non-commercial publication under D-030 as extended by D-032. DCS's
headings are kept as printed in locators, typos included ("Zink", "Relavent"). Table A2's
category heading says "roof" for the wall table; A10 says "wall". The module checks each title.

## 3. How DS rows join to the spine

The A-series tables have **no codes**. Each line has a trilingual name only. AGENTS rule 5
forbids joining on names alone, so:

1. **A reviewed match file**, `catalog/geographies/name-matches/dcs-census2024-a-series-ds.csv`,
   maps each of the 340 DS lines (district code + English label as printed) to a DCS DS code.
   The build never matches names itself; a DS line missing from the file stops the build.
2. **How the file was made (2026-11-14, by the agent):** within each district, the label was
   compared with DCS's own DS name from the GN population workbook (same census, same codes).
   - 323 matched exactly (letters only, case ignored).
   - 17 are spelling variants, for example "Delthota" → 2148 "Deltota", "Weligam" → 3239
     "Weligama", "Vadamaradchy East" → 4124 "Vadamaradchi East". Each was matched as the only DS
     in its district whose GN occupied housing units add up to the table's total. The 17 are
     listed in the QA report for review.
3. **Numeric check, every build:** each DS line's total must equal the sum of GN occupied housing
   units for its matched DCS code (GN housing workbook). One difference stops the build. All
   340 pass ✅. No two DS divisions in the same district have the same total ✅, so a wrong match
   cannot pass this check by coincidence.
4. DCS codes join to the spine through the G02 crosswalk, as for GN data. DCS 5224 Kalmunai has
   no spine unit (D-022): its values stay in Ampara district and Sri Lanka, with no DS row.

## 4. Checks

All run by the build; any failure stops it.

| Check | Result |
|---|---|
| Title and every category heading where expected, in all eight tables | pass ✅ |
| On every line, categories sum to the total | 0 failures ✅ |
| A9–A12 list the same 366 lines (Sri Lanka, 25 districts, 340 DS) with the same totals | 0 differences ✅ |
| DS lines sum to their district line; district lines sum to Sri Lanka (each table, each category) | 0 differences ✅ |
| A1–A4 district and Sri Lanka lines equal those in A9–A12 | 0 differences ✅ |
| DS total = GN sum of occupied housing units, for the matched DCS code | 340 of 340 ✅ |
| Every topic covers the same places | ✅ |

Run once on the build (a script, not part of the pipeline):

- In all 374 places and all four topics, the categories add up to `occupied_housing_units` from
  `census-2024-gnd-tables`, joined by spine id ✅. This check does not use the match file.
- 60 randomly sampled count cells, read back from the raw files at their locators, all equal ✅.
- Of the 339 DS rows, 66 have a table label spelt differently from the spine's (COD-AB) name, for
  example "Mathugama"/"Matugama" and "Galle Four Gravets"/"Galle 4 Gravets". All 66 were read:
  each is the same division ✅.

## 5. Values and locators

- DS, district and Sri Lanka values are DCS's own lines, not sums of ours. Locators name the
  file, sheet, row and column.
- Province values are sums of DCS's district lines (A-series tables have no province lines),
  with note `aggregate`.
- Values stay `machine_extracted` (AGENTS rule 7), `revision_status: provisional`.

## 6. Gaps

- No comparison with the Final Report PDF ❌. No human check (Q01 not run for this dataset) ❌.
- The "attached house" floor reading and the meaning of "Not relevant" are not confirmed ❓.
- The 17 spelling-variant matches were made by the agent with a numeric check; lead review is
  pending.
- Not in a release yet. Size is in the QA report.
