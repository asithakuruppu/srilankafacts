# QA report: Census 2024 housing unit structure and materials by DS

Dataset `census-2024-topic-tables`, step (c) of D-032. Built 2026-11-14 with
`uv run slf build census-2024-topic-tables --out-dir ./data/build`. Method:
[census-2024-housing-materials.md](../methods/census-2024-housing-materials.md).

**Result:** 0 errors, 9 recorded warnings (1 new: DCS 5224 Kalmunai has no spine unit). **Not
in any release.** Values are `machine_extracted`.

## Headline numbers ✅

| Item | Value |
|---|---|
| Source lines (A9–A12) | 366 in each: Sri Lanka, 25 districts, 340 DS |
| New observations | 27,676 (74 indicators × 374 places); dataset total 1,834,387 |
| Places | 339 DS (338 COD-AB + `LK-ADM3-P0001` Kalmunai North) · 25 districts · 9 provinces · Sri Lanka |
| Lines where categories do not sum to the total | 0 (the build stops on any) |
| A9–A12 lines, labels and totals identical | yes |
| DS sums vs district lines, district sums vs Sri Lanka | 0 differences in all 4 tables |
| A1–A4 vs district and Sri Lanka lines of A9–A12 | 0 differences |
| DS total vs GN sum of occupied housing units (matched DCS code) | 340 of 340 equal |
| Category sums vs `occupied_housing_units` (other dataset, by spine id), all places and topics | 0 differences |
| Sampled count cells re-read from raw files at their locators | 60 of 60 equal |
| Shares `not_available` | 0 |

## Warnings

1. **New:** DCS 5224 Kalmunai has no spine unit (D-022). Its housing units count in Ampara
   district and Sri Lanka; no DS row is produced.
2. The 8 earlier warnings are unchanged (5 GNs missing from the population files, 41 unmatched
   GN units, 5224 for households).

## DS matches for review (spelling variants)

323 of 340 DS labels match DCS's own DS name exactly within their district. These 17 do not, and
were matched because each is the only DS in its district with the same total. The lead should
glance at them; the full list is `catalog/geographies/name-matches/dcs-census2024-a-series-ds.csv`.

| District | A9–A12 label | DCS DS | DCS name |
|---|---|---|---|
| 21 | Delthota | 2148 | Deltota |
| 23 | Thalawakele | 2313 | Thalawakelle |
| 23 | Ambagamuwa | 2315 | Ambagamuwa Koralaya |
| 31 | Benthota | 3103 | Bentota |
| 32 | Weligam | 3239 | Weligama |
| 33 | Lunugamwehera | 3306 | Lunugamvehera |
| 41 | Valikamam North | 4112 | Valikamam North (Tellipallai) |
| 41 | Vadamaradchy South-West (Karaveddy) | 4121 | Vadamaradchi South-West (Karaveddy) |
| 41 | Vadamaradchy East | 4124 | Vadamaradchi East |
| 41 | Vadamaradchy North (Point Perdro) | 4127 | Vadamaradchi North (Point Pedro) |
| 41 | Thenmaradchy (Chavakachcheri) | 4130 | Thenmaradchi (Chavakachcheri) |
| 44 | Puthukudiyiruppu | 4409 | Puthukkudiyiruppu |
| 44 | Oddusudan | 4412 | Oddusuddan |
| 51 | Poratheevu Pattu | 5133 | Porativu Pattu |
| 52 | Sainthamarathu | 5225 | Sainthamaruthu |
| 53 | Padavisiripura | 5303 | Padavi Sri Pura |
| 91 | Kalthota | 9119 | Kaltota |

## National values (DCS's Sri Lanka line) ✅

Occupied housing units 6,030,541.

| Topic | Category | Housing units | Share % |
|---|---|---:|---:|
| structure | Single house, 1 floor | 4,958,009 | 82.22 |
| structure | Single house, 2 floors | 751,375 | 12.46 |
| structure | Single house, more than 2 floors | 59,484 | 0.99 |
| structure | Attached house, 1 floor | 164,419 | 2.73 |
| structure | Attached house, 2 floors | 50,030 | 0.83 |
| structure | Attached house, 3 or 4 floors | 25,373 | 0.42 |
| structure | Attached house, 5 to 10 floors | 12,853 | 0.21 |
| structure | Attached house, 11 to 19 floors | 6,031 | 0.10 |
| structure | Attached house, 20 or more floors | 1,756 | 0.03 |
| structure | Other | 1,211 | 0.02 |
| wall | Brick | 2,799,913 | 46.43 |
| wall | Cement block | 2,828,027 | 46.90 |
| wall | Granite or cube stones | 95,717 | 1.59 |
| wall | Cabook | 68,497 | 1.14 |
| wall | Pressed soil bricks | 111,245 | 1.84 |
| wall | Mud or warichchi | 70,011 | 1.16 |
| wall | Cadjan or palmyrah | 7,650 | 0.13 |
| wall | Plank, metal sheet or asbestos | 43,260 | 0.72 |
| wall | Zinc aluminium sheets | 3,870 | 0.06 |
| wall | Other | 1,140 | 0.02 |
| wall | Not relevant | 1,211 | 0.02 |
| roof | Tile | 2,032,441 | 33.70 |
| roof | Asbestos | 3,209,496 | 53.22 |
| roof | Concrete | 440,761 | 7.31 |
| roof | Zinc aluminium sheet | 85,422 | 1.42 |
| roof | Metal sheet | 163,735 | 2.72 |
| roof | Cadjan, palmyrah or straw | 88,820 | 1.47 |
| roof | Other | 8,655 | 0.14 |
| roof | Not relevant | 1,211 | 0.02 |
| floor | Cement | 3,710,163 | 61.52 |
| floor | Terrazzo, tile, granite, finished wood or titanium | 1,692,659 | 28.07 |
| floor | Concrete | 498,925 | 8.27 |
| floor | Mud | 115,259 | 1.91 |
| floor | Wood | 2,579 | 0.04 |
| floor | Sand | 7,707 | 0.13 |
| floor | Other | 2,038 | 0.03 |
| floor | Not relevant | 1,211 | 0.02 |

"Not relevant" equals structure "Other" (1,211) in every place, not only nationally.

## Size in a trial release ✅

A trial preview release with both census datasets, run 2026-11-14 in a scratch folder and then
deleted (the old local preview releases were deleted first, with the lead's approval, to free
disk space):

| | Step (b) trial | Plus this step |
|---|---|---|
| Release size | 2.1 GB | 2.1 GB |
| API folder | 842 MB | 851 MB |
| Place files | 730 MB | 737 MB |
| Observations download | 1.0 GB | 1.0 GB (1,002,841,164 bytes CSV) |
| One DS place file (`LK1103.json`) | 54 KB (78 values) | 75 KB (115 values) |
| Files | 15,483 | 15,890 |

The earlier estimate (about +9 MB of place files) was close: +7 MB measured.

**Fixed in this step:** the first trial wrote spatial-context tables (`stats/local_*_gn.parquet`)
for all 74 new indicators at GN level, although they have no GN values: 74 files, 13.1 MB, every
row `no_data`. They held no values, and GN place files never showed materials ✅. The
spatial-context stage now skips a level where an indicator has no values (`slf/enrich.py`, with a
test). The second trial has 0 such files ✅ and 74 fewer files in total.

## Final Report comparison (added 2026-11-14) ✅

Final Report Table 11.6 (PDF page 205) prints the national percentage of housing units by wall,
roof and floor material, to one decimal ([script](data/census-2024-final-report-housing.py)):
**24 values, 0 differences**, once the Final Report's "Other" is compared with the release's
Other **plus "Not relevant"**. The Final Report has no "Not relevant" line; its roof "Other" is
0.2 (8,655 + 1,211 = 9,866 housing units, 0.16 percent) where the release's roof Other alone is
0.14 percent. So DCS's own report folds "Not relevant" into "Other" ✅, consistent with "Not
relevant" being the "Other" structures, but still not a definition ❓.

## Not checked

- Final Report tables by district for materials, and for structure ❌. Human spot check (Q01) ❌.
- The "attached house" floor reading ❓ and the meaning of "Not relevant" ❓.
