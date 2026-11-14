# QA report: Census 2024 households and amenities by GN

Dataset `census-2024-topic-tables`, step (a) of D-032. Built 2026-11-13 with
`uv run slf build census-2024-topic-tables --out-dir ./data/build`. Method:
[census-2024-households.md](../methods/census-2024-households.md).

**Result:** 0 errors, 2 recorded warnings. **Not in any release.** Values are `machine_extracted`.

## Headline numbers ✅

| Item | Value |
|---|---|
| Source rows (GN) | 14,008 in `HH_GND_excel.xlsx` (sha256 `c41c0d2c384f…`) |
| Observations | 1,075,575 (75 indicators × 14,341 places) |
| Places | 13,967 GN · 338 DS · 25 districts · 9 provinces · Sri Lanka |
| Unmatched GNs | 41 (the same 41 as `census-2024-gnd-tables`); counted in DS and district totals, no GN rows |
| Rows where a group does not sum to households | 0 of 14,008 × 4 groups (the build stops on any) |
| District and national values vs DCS tables A5–A8 | 26 rows × 4 tables, every count: 0 differences |
| Shares `not_available` | 185 (5 GNs with 0 households × 37 shares) |
| Households, Sri Lanka | 6,111,315 (equals A5–A8 and A14) |

## Warnings

1. 41 DCS GN units are unmatched in the G02 crosswalk; codes are listed in the build's `qa.md`.
2. DCS 5224 Kalmunai has no spine unit (D-022); its households count in Ampara district only.

## National values (sum of GN rows; each equals the Sri Lanka row of A5–A8) ✅

| Group | Category | Households | Share % |
|---|---|---:|---:|
| water | Protected well | 1,624,506 | 26.58 |
| water | Semi-protected well | 267,327 | 4.37 |
| water | Unprotected well | 77,806 | 1.27 |
| water | Tube well | 270,401 | 4.42 |
| water | Spring or fountain | 230,268 | 3.77 |
| water | Pipe-borne water from the National Water Supply and Drainage Board | 2,374,349 | 38.85 |
| water | Pipe-borne water from a local authority | 100,764 | 1.65 |
| water | Pipe-borne water from a community-based organisation | 419,247 | 6.86 |
| water | Pipe-borne water from a private water supply project | 130,394 | 2.13 |
| water | Tank, river or stream | 59,336 | 0.97 |
| water | Rain water | 4,346 | 0.07 |
| water | Bottled water | 63,753 | 1.04 |
| water | Filtered water (R.O. plant) | 456,849 | 7.48 |
| water | Bowser | 31,208 | 0.51 |
| water | Other source of drinking water | 761 | 0.01 |
| cooking | Firewood | 3,381,781 | 55.34 |
| cooking | Kerosene | 32,974 | 0.54 |
| cooking | Gas | 2,588,502 | 42.36 |
| cooking | Electricity | 19,540 | 0.32 |
| cooking | Sawdust or paddy husk | 1,739 | 0.03 |
| cooking | Biogas | 7,179 | 0.12 |
| cooking | Other cooking fuel | 2,361 | 0.04 |
| cooking | Not relevant | 77,239 | 1.26 |
| lighting | Electricity from the national grid or a rural hydro power project | 5,987,585 | 97.98 |
| lighting | Kerosene lamp | 95,150 | 1.56 |
| lighting | Solar power (grid connected) | 8,093 | 0.13 |
| lighting | Solar power (stand-alone) | 5,817 | 0.10 |
| lighting | Biogas | 244 | 0.00 |
| lighting | Generator | 1,230 | 0.02 |
| lighting | Other source of lighting | 13,196 | 0.22 |
| toilet | Toilet within the housing unit, for the household only | 3,798,777 | 62.16 |
| toilet | Toilet within the housing unit, shared with another household | 157,456 | 2.58 |
| toilet | Toilet within the premises, for the household only | 1,832,587 | 29.99 |
| toilet | Toilet within the premises, shared with another household | 197,678 | 3.23 |
| toilet | No toilet of its own; shares with another housing unit or units | 101,924 | 1.67 |
| toilet | Common or public toilet | 9,567 | 0.16 |
| toilet | Not using a toilet | 13,326 | 0.22 |

## DS-level cross-check against DCS tables A13–A16 (added 2026-11-14) ✅

The build compares district and national sums with A5–A8 only. DCS's DS tables A13 (cooking),
A14 (drinking water), A15 (lighting) and A16 (toilets) were then compared with the release's
GN-summed values on every line ([script](data/census-2024-a13-a16-crosscheck.py); release
`v2026.11.10-preview.2`). Each table column was mapped to the release count indicator with the
same national value (one-to-one for all 37 categories), then tested on every other line. DS lines
join through the reviewed Housing A-series match file and the G02 crosswalk.

| Table | Categories | Lines | Values compared | Differ |
|---|---|---|---|---|
| A13 cooking | 8 + households | Sri Lanka, 25 districts, 339 DS | 3,285 | 0 |
| A14 drinking water | 15 + households | same | 5,840 | 0 |
| A15 lighting | 7 + households | same | 2,920 | 0 |
| A16 toilets | 7 + households | same | 2,920 | 0 |

DCS 5224 Kalmunai is skipped (no spine unit, D-022). Every A13–A16 DS label is in the match file.

## Final Report comparison (added 2026-11-14)

Final Report housing chapter against the release ([script](data/census-2024-final-report-housing.py); `v2026.11.10-preview.2`):

| Table | What | Values | Differ |
|---|---|---|---|
| 11.9 (PDF p. 208) | Households by main source of drinking water, Sri Lanka, counts | 15 | 0 ✅ |
| 11.13 (p. 212) | Households by main source of lighting, Sri Lanka, counts ("Other" = biogas + generator + other) | 5 | 0 ✅ |
| 11.12 (p. 211) | Share of households cooking with firewood / gas, Sri Lanka and 25 districts, one decimal | 52 | **14** ❓ |

The 14 differences in Table 11.12 are all 0.1 percentage point, in both directions (for example
Sri Lanka firewood: Final Report 55.4, release 55.3 from 3,381,781 of 6,111,315 households).
No grouping of cooking categories, and neither denominator (all households, or excluding "Not
relevant"), reproduces all 52 values; the best fits reproduce 18 of 26 firewood and 21 of 26 gas
values. DCS's own district table A13 matches the release on every line (above), so the Final
Report's percentages appear to come from a slightly different base ❓. The release is unchanged.

Footnote 11.13 lists "Biogas, Generator and Other" under Other, which supports the release's
"generator" category (DCS table A15 heads that column "Rural water supply project").

## Not checked

- Final Report tables for toilets (11.16 uses a different classification: water-sealed or not)
  ❌; human source check (Q01) ❌.
- Small-denominator behaviour of the 37 shares in the release builder ❓.
- Not yet in a release. Under LA-004 a trial preview was 1.4 GB (current preview 449 MB) and one
  DS place file 38 KB (now 14 KB); see the method §5.
