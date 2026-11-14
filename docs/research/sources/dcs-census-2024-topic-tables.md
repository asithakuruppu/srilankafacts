# Census 2024 topic tables: what DCS publishes, and what we now hold

Prepared 2026-11-12 by an agent for the lead (Stage 1B item 1). Tags: ✅ verified by reading or
running · 🟡 claimed by a source, not checked · ❌ not found or failed · ❓ assumption.

## Answer

**Yes, the remaining census tables can be downloaded, and they are now snapshotted** ✅. 31
workbooks plus a fresh copy of the CPH 2024 page were fetched on 2026-11-12 into
`raw/dcs/census-2024-topic-tables/` (immutable, sha256 recorded; list at the end). Nothing is
ingested or published yet. The catalogue entry `census-2024-topic-tables` is `proposed`, with
no `publication` block, so a public release cannot include it.

What is available at each level ✅:

| Topic | GN | DS | District | File |
|---|---|---|---|---|
| Households | ✅ | ✅ | ✅ | `HH_GND_excel`, `HH_DS_excel` |
| Drinking water, cooking fuel, lighting, toilet (households) | ✅ | ✅ | ✅ | `HH_GND_excel`; Housing A5–A8, A13–A16 |
| Ethnic group | ✅ (small groups folded, see below) | ✅ | ✅ | `GN_Level_…Ethnic_Group`; Population A2, A6 |
| Religion | ✅ (small groups folded) | ✅ | ✅ | `GN_Level_…Religion`; Population A3, A7 |
| Five-year age groups (0–4 … 95+) | ✅ | ✅ | ✅ | `GN_Level_…Five_Year_Age_Group` |
| Sector (urban, rural, estate rural) | ✅ | ✅ | ✅ | `GN_Level_…Sector` |
| Local authority type (municipal, urban, pradeshiya sabha) | ✅ | ✅ | ✅ | `GN_Level_…Local_Government_Area` |
| Occupied housing units | (held already) | ✅ | ✅ | `OHU_DS_excel` |
| Housing unit structure; wall, roof, floor materials | ❌ | ✅ | ✅ | Housing A1–A4, A9–A12 |
| Migration by main reason | ❌ | ❌ | ✅ | Population A4 |
| Education, work, disability, marital status | ❌ not on the page | | | |

## Checks run ✅

All on the snapshots, against the population workbook already in the release
(`census-2024-gnd-tables`, 14,008 GNs, 21,781,800 people).

- **Households (`HH_GND_excel`):** 14,008 GN rows, the same GN codes as the population workbook
  (0 missing, 0 extra). 6,111,315 households in total, the same as the Sri Lanka row of Housing
  A14. In every one of the 14,008 rows, each of the four amenity groups (water 15 categories,
  cooking 8, lighting 7, toilet 7) adds up exactly to the household count.
- **Ethnicity, religion, five-year age, sector, local authority:** 14,003 GN rows each. The 5 GNs
  left out all have population 0 in the population workbook (three in Valikamam North
  (Tellipallai), one each in Koralai Pattu South (Kiran) and Welikanda). For every GN, the total
  equals the population workbook's total (0 differences in all five files), and the categories
  add up to the total (0 rows that do not).
- **Format:** `OHU_DS_excel` and `HH_DS_excel` are legacy Excel 97 (.xls) files served under an
  "Excel" link, saved as `.xlsx`. The snapshot keeps the bytes as served; a parser must read them
  as .xls. All other files are real .xlsx.
- **Labels:** the DS and district tables (A-series) carry Sinhala, Tamil and English labels; the
  GN tables are English only.
- **Page:** the 2026-11-12 page has the same download links as the 2026-11-07 snapshot (only a
  webmail link changed).

## Important: small groups are folded into "Other" at GN level ✅

The GN ethnicity and religion files say: when a group has fewer than 10 people in a GN, the
count is added to "Other". The cells for those groups show `-` (101,464 such cells for
ethnicity, 39,241 for religion). Summed over all GNs, the named groups are therefore lower than
DCS's own district tables, and "Other" is much higher:

| Total | 21,781,800 | 21,781,800 | +0 |
| Sinhalese | 16,140,688 | 16,144,037 | -3,349 |
| Sri Lanka Tamil | 2,665,574 | 2,681,627 | -16,053 |
| Indian Tamil/ Malaiyaga Thamilar | 590,087 | 600,360 | -10,273 |
| Sri Lanka Moor/Muslim | 2,274,372 | 2,283,246 | -8,874 |
| Burgher | 25,159 | 31,721 | -6,562 |
| Malay | 22,838 | 26,650 | -3,812 |
| Sri Lanka Chetty | 1,753 | 2,443 | -690 |
| Bharatha | 553 | 1,183 | -630 |
| Veddahs | 1,287 | 1,373 | -86 |
| Other | 59,489 | 9,160 | +50,329 |
| GN_Level_Population_by_Religion.xlsx |

| Buddhist | 15,196,960 | 15,199,093 | -2,133 |
| Hindu | 2,718,154 | 2,734,839 | -16,685 |
| Islam | 2,327,605 | 2,337,379 | -9,774 |
| Roman Catholic | 1,209,072 | 1,224,348 | -15,276 |
| Other Christian | 266,515 | 282,185 | -15,670 |
| Other | 63,494 | 3,956 | +59,538 |

| File | Level | Rows | sha256 (first 12) | Bytes |

Within each table, the shortfalls add up exactly to the "Other" surplus (50,329 for ethnicity,
59,538 for religion). So:

1. **DS, district and national ethnicity and religion must come from DCS's DS and district tables
   (A2, A3, A6, A7), never from summing GN rows.** That differs from how the release builds
   aggregates now (by summing GNs), so it needs its own method.
2. **A GN-level `-` means "fewer than 10, counted in Other", not zero.** It must not be shown as
   0, and the GN "Other" value is not a real "Other" group.
3. Small groups (Burgher, Malay, Chetty, Bharatha, Veddah) lose a large share at GN level
   (Burgher: 25,159 of 31,721). A GN map of these groups would understate them.

## Ingest progress and what remains

- **Step (a) done, 2026-11-13:** households and the four amenity groups at GN level, 75
  indicators, checked against district tables A5–A8 with 0 differences. Not in a release.
  Method: [census-2024-households.md](../../methods/census-2024-households.md); QA:
  [census-2024-households.md](../../qa/census-2024-households.md).
- **Step (b) done, 2026-11-13:** five-year age, sector and local authority type at GN level, 51
  indicators, checked against DCS's own DS, district and national subtotal lines with 0
  differences, and against the population workbook. Not in a release. Method:
  [census-2024-age-sector-local-authority.md](../../methods/census-2024-age-sector-local-authority.md);
  QA: [census-2024-age-sector-local-authority.md](../../qa/census-2024-age-sector-local-authority.md).
- Ethnicity and religion need `sensitivity` set and the folding rule recorded.
- DS-level values for structure and materials, with an information floor that says "DS level;
  no GN breakdown is published".
- A reader for the two .xls files (the `xlrd` dependency, or convert during extract). Either way,
  that is a new dependency or a decision, under AGENTS rule 8.
- Q01 sampling extends to the new tables before any public release.

## Not verified / limits

- Values were checked for internal consistency and against the population workbook and the
  A-series Sri Lanka rows only. They were not checked against the Final Report PDF.
- DS-level A-series files were inventoried (titles, row counts), not parsed. The two .xls files
  were not opened.
- Rights: same as the rest of CPH 2024. DCS publishes no reuse terms ❌.

## Decisions (accepted by the lead, 2026-11-12)

All three recommendations below were accepted: recorded as D-032 (items 1 and 3) and D-033 (item 2)
in the decision log.


1. **Does D-030 (non-commercial publication) cover these tables too?** D-030 speaks of "Census 2024
   GN tables"; the A-series tables are DS and district tables. Recommendation: yes, the same
   source, terms and notice. Record it as an amendment to D-030, not a new decision.
2. **Should ethnicity and religion be published at all in 1B, and at which levels?** D-015 keeps
   them out of profiles, but says nothing about showing them as indicators. They are sensitive
   (AGENTS rule 12), and the GN files are distorted by the folding.
   Recommendation: publish them at DS and district level from DCS's own tables, with neutral
   labels and no rankings or "most/least" lists. At GN level, hold back until there is an agreed
   way to show `-` (fewer than 10, folded into Other).
3. **Which topics go first?** Recommendation: households plus the four amenity groups at GN level
   (the most useful, and fully consistent), then five-year age, sector and local authority type.
   Then DS-level materials, and ethnicity and religion last.

## Snapshots (2026-11-12)

All under `raw/dcs/census-2024-topic-tables/<timestamp>/`, fetched from
`https://www.statistics.gov.lk/Population/StaticalInformation/CPH2024/…` with 3 seconds between
requests.

| File | Level | Snapshot | sha256 (first 12) | Bytes |
|---|---|---|---|---|
| `CPH2024_page.html` | page | 20261112T173128Z | `b168bdba4bd6` | 121,394 |
| `HH_GND_excel.xlsx` | GN | 20261112T173135Z | `c41c0d2c384f` | 3,722,895 |
| `OHU_DS_excel.xlsx` | DS/district | 20261112T173141Z | `d24b73d086f0` | 167,424 |
| `HH_DS_excel.xlsx` | DS/district | 20261112T173146Z | `e6a00ff9d079` | 162,816 |
| `GN_Level_Population_by_Ethnic_Group.xlsx` | GN | 20261112T173154Z | `23aa46295be0` | 6,807,560 |
| `GN_Level_Population_by_Five_Year_Age_Group.xlsx` | GN | 20261112T173200Z | `b1842df8f30f` | 2,144,495 |
| `GN_Level_Population_by_Local_Government_Area.xlsx` | GN | 20261112T173206Z | `0a42634ef2c8` | 751,727 |
| `GN_Level_Population_by_Religion.xlsx` | GN | 20261112T173212Z | `2598faf0e728` | 1,008,130 |
| `GN_Level_Population_by_Sector.xlsx` | GN | 20261112T173218Z | `1eb5c73d0aa3` | 798,805 |
| `PopulationA_A1.xlsx` | DS/district | 20261112T173223Z | `388c7d1ef5fa` | 18,543 |
| `PopulationA_A2.xlsx` | DS/district | 20261112T173229Z | `e8aa7d4635ae` | 17,361 |
| `PopulationA_A3.xlsx` | DS/district | 20261112T173234Z | `2486798e3a6d` | 15,841 |
| `PopulationA_A4.xlsx` | DS/district | 20261112T173239Z | `f01f54e943ca` | 17,460 |
| `PopulationA_A5.xlsx` | DS/district | 20261112T173245Z | `878d35a9f7b3` | 54,687 |
| `PopulationA_A6.xlsx` | DS/district | 20261112T173250Z | `1b27e53e0c37` | 51,828 |
| `PopulationA_A7.xlsx` | DS/district | 20261112T173256Z | `e0012c7c463f` | 48,626 |
| `HousingA_A1.xlsx` | DS/district | 20261112T173301Z | `44309189a3dc` | 19,797 |
| `HousingA_A2.xlsx` | DS/district | 20261112T173307Z | `47de5ba6306f` | 21,464 |
| `HousingA_A3.xlsx` | DS/district | 20261112T173313Z | `592bf46c1ea7` | 19,434 |
| `HousingA_A4.xlsx` | DS/district | 20261112T173318Z | `b30b8ac2a27d` | 19,771 |
| `HousingA_A5.xlsx` | DS/district | 20261112T173324Z | `3a6f3fa43f8d` | 23,289 |
| `HousingA_A6.xlsx` | DS/district | 20261112T173329Z | `0e32ae5ea664` | 19,533 |
| `HousingA_A7.xlsx` | DS/district | 20261112T173335Z | `def404ab95f0` | 19,595 |
| `HousingA_A8.xlsx` | DS/district | 20261112T173340Z | `a62691adc09b` | 19,257 |
| `HousingA_A9.xlsx` | DS/district | 20261112T173346Z | `eaf028784449` | 51,714 |
| `HousingA_A10.xlsx` | DS/district | 20261112T173351Z | `cc03307167cd` | 54,172 |
| `HousingA_A11.xlsx` | DS/district | 20261112T173356Z | `dead8fbe90cf` | 50,170 |
| `HousingA_A12.xlsx` | DS/district | 20261112T173402Z | `ef543939789a` | 48,126 |
| `HousingA_A13.xlsx` | DS/district | 20261112T173407Z | `da920a1cae95` | 48,253 |
| `HousingA_A14.xlsx` | DS/district | 20261112T173413Z | `6502766c66a8` | 63,877 |
| `HousingA_A15.xlsx` | DS/district | 20261112T173419Z | `afc82d212ea4` | 46,989 |
| `HousingA_A16.xlsx` | DS/district | 20261112T173424Z | `60f269f05fe1` | 48,171 |

The full sha256 values are in each snapshot's `.meta.json`. Five-year age, sector and local
authority files also carry DCS's own DS and district subtotal rows; DS-level households also
appear in Housing A13–A16.
