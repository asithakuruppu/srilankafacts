# QA report: Census 2024 population by ethnic group and religion, DS and district

Dataset `census-2024-topic-tables`, step (d) of D-032, under D-033. Built 2026-11-14 with
`uv run slf build census-2024-topic-tables --out-dir ./data/build`. Method:
[census-2024-ethnicity-religion.md](../methods/census-2024-ethnicity-religion.md).

**Result:** 0 errors, 10 recorded warnings (1 new: DCS 5224 Kalmunai has no spine unit in A6/A7).
**Not in any release.** Values are `machine_extracted`.

## Headline numbers ✅

| Item | Value |
|---|---|
| Source lines (A6, A7) | 366 in each: Sri Lanka, 25 districts, 340 DS |
| New observations | 11,968 (32 indicators × 374 places); dataset total 1,846,355 |
| Places | 339 DS (338 COD-AB + `LK-ADM3-P0001` Kalmunai North) · 25 districts · 9 provinces · Sri Lanka |
| GN places with an ethnicity or religion value | 0 (the build stops on any) |
| Lines where categories do not sum to the total | 0 (the build stops on any) |
| A6 and A7 lines, labels and totals identical | yes |
| DS sums vs district lines, district sums vs Sri Lanka | 0 differences in both tables |
| A2, A3 vs district and Sri Lanka lines of A6, A7 | 0 differences |
| DS total vs GN sum of population (matched DCS code) | 340 of 340 equal |
| Category sums vs `population_total` (other dataset, by spine id), all places, both topics | 748 compared, 0 differences |
| Shares per place add up to | 100.0 in every place, both topics |
| Sampled count cells re-read from raw files at their locators | 60 of 60 equal |
| Rows with `sensitivity: sensitive_group` | all 11,968; no other census row |
| Shares `not_available` | 0 |

## Warnings

1. **New:** DCS 5224 Kalmunai has no spine unit (D-022). Its people count in Ampara district and
   Sri Lanka; no DS row is produced.
2. The 9 earlier warnings are unchanged.

## DS matches

339 of 340 labels are the same as in Housing A9–A12 and use the step (c) match. The one new
variant is A6/A7 "Padavisripura" (district 53) → DCS 5303 "Padavi Sri Pura" (A9–A12 print
"Padavisiripura"); its total, 12,081 persons, equals the GN population sum for 5303 and no other
DS in district 53. File: `catalog/geographies/name-matches/dcs-census2024-population-a-series-ds.csv`.

## National values (DCS's Sri Lanka line) ✅

Population 21,781,800.

| Topic | Category | Persons | Share % |
|---|---|---:|---:|
| Ethnic group | Sinhalese | 16,144,037 | 74.12 |
| Ethnic group | Sri Lanka Tamil | 2,681,627 | 12.31 |
| Ethnic group | Indian Tamil / Malaiyaga Thamilar | 600,360 | 2.76 |
| Ethnic group | Sri Lanka Moor / Muslim | 2,283,246 | 10.48 |
| Ethnic group | Burgher | 31,721 | 0.15 |
| Ethnic group | Malay | 26,650 | 0.12 |
| Ethnic group | Sri Lanka Chetty | 2,443 | 0.01 |
| Ethnic group | Bharatha | 1,183 | 0.01 |
| Ethnic group | Veddha | 1,373 | 0.01 |
| Ethnic group | Other | 9,160 | 0.04 |
| Religion | Buddhist | 15,199,093 | 69.78 |
| Religion | Hindu | 2,734,839 | 12.56 |
| Religion | Islam | 2,337,379 | 10.73 |
| Religion | Roman Catholic | 1,224,348 | 5.62 |
| Religion | Other Christian | 282,185 | 1.30 |
| Religion | Other | 3,956 | 0.02 |

These are listed in DCS's column order. DCS's own district table prints one decimal (for example
74.1 and 12.3); the shares here are recomputed from the counts.

## D-033 restrictions, as built

SIZE_AND_RELEASE_CHECKS

## Not checked

- Final Report PDF tables ❌. Human spot check (Q01) ❌.
- How the website section reads to users, and whether its wording is neutral enough, needs the
  lead's eye ❓.
