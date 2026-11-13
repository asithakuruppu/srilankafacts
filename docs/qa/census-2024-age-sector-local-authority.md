# QA report: Census 2024 five-year age, sector and local authority type by GN

Dataset `census-2024-topic-tables`, step (b) of D-032. Built 2026-11-13 with
`uv run slf build census-2024-topic-tables --out-dir ./data/build`. Method:
[census-2024-age-sector-local-authority.md](../methods/census-2024-age-sector-local-authority.md).

**Result:** 0 errors, 8 recorded warnings (6 new, about the 5 missing GNs). **Not in any
release.** Values are `machine_extracted`.

## Headline numbers ✅

| Item | Value |
|---|---|
| Source rows (GN) | 14,003 in each of the three files |
| New observations | 731,136 (51 indicators × 14,336 places); dataset total 1,806,711 |
| Places | 13,962 GN · 338 DS · 25 districts · 9 provinces · Sri Lanka |
| Lines where categories do not sum to the total | 0 (GN and subtotal lines; the build stops on any) |
| Our sums vs DCS subtotal lines (340 DS, 25 districts, Sri Lanka) | 0 differences in all 3 files |
| Totals vs `population_total` (population workbook), matched GNs | 0 differences in all 3 files |
| Age bands vs existing 0–14, 15–59, 60–64, 65+ counts | 0 differences |
| Shares `not_available` | 0 |
| GNs in more than one sector / local authority type | 1,215 / 120 |

## Warnings

1. For each of the three files, 5 GNs in the households file have no row: 4112185, 4112220,
   4112225, 5110025, 7210065. They have population 0 in the population workbook. No values are
   produced for them (2 warnings per file).
2. 41 DCS GN units are unmatched in the G02 crosswalk (unchanged).
3. DCS 5224 Kalmunai has no spine unit (D-022) (unchanged).

## National values (sum of GN rows; each equals DCS's Sri Lanka line) ✅

Population 21,781,800.

| Topic | Category | Persons | Share % |
|---|---|---:|---:|
| sector | Urban (including estate urban) | 3,819,203 | 17.53 |
| sector | Rural | 17,096,918 | 78.49 |
| sector | Estate rural | 865,679 | 3.97 |
| local authority | Municipal council | 2,574,112 | 11.82 |
| local authority | Urban council | 1,245,091 | 5.72 |
| local authority | Pradeshiya sabha | 17,962,597 | 82.47 |
| age | 0–4 | 1,215,120 | |
| age | 5–9 | 1,556,523 | |
| age | 10–14 | 1,735,196 | |
| age | 15–19 | 1,795,038 | |
| age | 20–24 | 1,608,606 | |
| age | 25–29 | 1,372,458 | |
| age | 30–34 | 1,414,060 | |
| age | 35–39 | 1,452,703 | |
| age | 40–44 | 1,602,344 | |
| age | 45–49 | 1,490,765 | |
| age | 50–54 | 1,341,807 | |
| age | 55–59 | 1,276,056 | |
| age | 60–64 | 1,183,310 (from the population workbook) | 5.43 |
| age | 65–69 | 991,814 | |
| age | 70–74 | 795,539 | |
| age | 75–79 | 522,990 | |
| age | 80–84 | 268,415 | |
| age | 85–89 | 111,029 | |
| age | 90–94 | 39,235 | |
| age | 95 and over | 8,792 | |

## Size in a trial release ✅

A trial preview release with both census datasets (built in a scratch folder, then deleted):

| | v2026.11.9-preview.1 | After households (LA-004) | Plus this step |
|---|---|---|---|
| Release size | 449 MB | 1.4 GB | 2.1 GB |
| API folder | 193 MB | 581 MB | 842 MB |
| Place files | 170 MB | 506 MB | 730 MB |
| Observations download | not measured | 667 MB | 1.0 GB |
| One DS place file (`LK1103.json`) | 14 KB | 38 KB | 54 KB (78 values) |
| Files | 14,595 | 15,123 | 15,483 |

Place files are now about 4× today's. As before, most of each value's size is provenance text,
not the number.

## Not checked

- Final Report PDF tables ❌. Human spot check (Q01) ❌.
- Small-denominator flag on these shares ❓.
