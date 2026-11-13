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

## Not checked

- Final Report PDF tables ❌; human source check (Q01) ❌.
- Small-denominator behaviour of the 37 shares in the release builder ❓.
- Release size: a trial preview with these indicators was 1.7 GB (current preview 449 MB); see
  the method §5. Inclusion in a release waits for the lead's choice of which indicators go on
  place pages.
