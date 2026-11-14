# QA: DS boundary change 2012 → 2024, and the district census series

G06 v2 · built 2026-11-15 with `uv run slf history build` · method:
[`docs/methods/boundary-change-2012-2024.md`](../methods/boundary-change-2012-2024.md) ·
tables: [`docs/qa/data/boundary-change-2012-2024/`](data/boundary-change-2012-2024/) ·
relations: [`catalog/geographies/relations/succession_ds_2012-2024.csv`](../../catalog/geographies/relations/succession_ds_2012-2024.csv)

Tags: ✅ verified by running or reading · 🟡 claimed by a source, not checked · ❌ not found · ❓ assumption.
Not in any release. Rights for all inputs are `unclear` (DCS); nothing here is published.

## Headline

- **331 DS divisions in 2012 → 340 in 2024** ✅. 305 unchanged, 16 renamed (spelling or naming
  only, identical GN lists), 8 split into 17 units (+9), 2 adjusted by a 3-GN transfer, 0 merged.
- **314 of 340 DS comparisons are `exact`; 26 are `approximate`**, each with a reason.
- **National totals reconcile to the person for both years** (below), and the 2012 column of
  the comparison table adds up to the full 2012 population: no one is dropped by the rebuild.
- All 9 new DS are in Nuwara Eliya (5), Galle (3) and Ratnapura (1), which is exactly where DCS
  Tables 2.3 and 2.4 show the DS count rising (5→10, 19→22, 17→18) ✅.

## Verify 1: national totals reconcile (both years)

```
2012: gn_file 20,359,439; Table 3.3 20,359,439; DS sum 20,359,439
2024: gn_workbook 21,781,800; Table 3.3 21,781,800; DS sum 21,781,800
DS 2012: 331 (Table 2.3: 331); in Abstract 2.7: 331
```

| Check | Result |
|---|---|
| 2012 national total in the GN file = Final Report 2024 Table 3.3 (2012) = sum of 331 DS rows | 20,359,439 all three ✅ |
| 2012 district totals (25) vs Table 3.3 | 0 differ ✅ |
| 2012 DS count per district vs Final Report Table 2.3 | 0 differ ✅ |
| 2012 DS rows found in DCS Abstract 2024 Table 2.7 (same total, male, female) | 331 of 331 ✅ |
| 2024 GN workbook total = Table 3.3 (2024) = sum of 340 DS | 21,781,800 all three ✅ |
| 2024 district totals (25) vs Table 3.3 | 0 differ ✅ |
| Sum of the 2012 column of the DS comparison (2024 boundaries) | 20,359,439 ✅ |
| Lines of the 2012 GN file not parsed (other than headers and page numbers) | 0 ✅ |
| DCS 2012–2024 district growth rates reproduced by our formula (one decimal) | Sri Lanka and 24 of 25; Kilinochchi ours 1.5, DCS 1.4 |

## Verify 2: change-type counts

| 2012 units (331) | n | 2024 units (340) | n |
|---|---|---|---|
| unchanged | 305 | unchanged | 305 |
| renamed | 16 | renamed | 16 |
| split | 8 | new | 11 |
| | | split_remainder | 6 |
| boundary_adjusted | 2 | boundary_adjusted | 2 |
| merged | 0 | merged | 0 |

Comparison labels (one per 2024 DS): `exact` 314 (`same_gn_list`); `approximate` 26: 19
`gn_reaggregation` (the 17 split units and the 2 boundary-adjusted units) and 7
`same_ds_total_gns_unverified` (unchanged units with a GN left unmatched: Colombo 1103,
Medadumbara 2124 (Victoria, listed without figures), Naula 2209 and Laggala-Pallegama 2224 (the
Matale reservoir GNs), Eravur Pattu 5112, Padavi Sri Pura 5303 and Kuchchaveli 5306). Full list:
`ds_comparison_2012_2024.csv`, column `reason`.

GN matching (2012 side, 14,022 rows): number and name 13,623 · number only 301 · name only 78 ·
number, name and DS 2 · **unmatched 18**. 2024 side: 4 unmatched of 14,008.

Succession relations: 17 `succeeded_by` + 17 `preceded_by` edges for the 8 retired 2012 units
(`LK-ADM3-V2012-…`). `succeeded_by` weights sum to 1.000000 for each retired unit ✅; every new
or remainder unit has exactly one predecessor (`preceded_by` weight 1.0) ✅.

Closed groups (all GNs stay inside the group; group-level comparison `exact`) ✅:

| 2012 | 2024 | 2012 pop. | 2024 pop. | Annual rate % |
|---|---|---|---|---|
| Kothmale | Kothmale West; Kothmale East | 101,180 | 103,697 | 0.19 |
| Hanguranketha | Hanguranketha; Mathurata | 88,528 | 92,106 | 0.31 |
| Walapane | Walapane; Nildandahinna | 104,119 | 107,709 | 0.27 |
| Nuwara Eliya | Nuwara Eliya; Thalawakelle | 212,094 | 217,863 | 0.21 |
| Ambagamuwa | Norwood; Ambagamuwa Koralaya | 205,723 | 203,905 | −0.07 |
| Baddegama | Baddegama; Wanduramba | 75,008 | 78,658 | 0.37 |
| Hikkaduwa | Madampagama; Hikkaduwa; Rathgama | 101,909 | 101,080 | −0.06 |
| Panduwasnuwara West + East | Panduwasnuwara West + East | 96,128 | 102,976 | 0.54 |
| Balangoda | Balangoda; Kaltota | 81,563 | 87,911 | 0.59 |

## Verify 3: ten sample changes with evidence

Locators: "p/l" = page and line of the 2012 GN file (snapshot
`raw/nuuuwan/nuuuwan-lk-census-2012/20261114T194914Z/population-gender_source.pdf`, sha256
`85a30345…`); 2024 DS codes are DCS codes in `GN_population.xlsx`. GN numbers are DCS's own.
Every GN in these flows matched on DCS GN number (and, except where noted, name).

| # | 2012 DS (row) | Change | 2024 DS: GNs moved (examples) · 2012 pop. on 2024 boundary → 2024 pop. | Label |
|---|---|---|---|---|
| 1 | Kothmale, Nuwara Eliya (p90 l42; 101,180; 96 GNs) | split, retired → `LK-ADM3-V2012-23-01` | 2302 Kothmale West: 49 (460A, 460K, 460L) · 39,253 → 41,955; 2303 Kothmale East: 47 (456D, 456A, 474F) · 61,927 → 61,742 | approximate (group exact) |
| 2 | Hanguranketha (p92 l43; 88,528; 131) | split | 2306 Hanguranketha: 79 (486A, 486B, 485B) · 55,371 → 58,931; 2307 Mathurata: 52 (491D, 491, 491C; one by number only) · 33,157 → 33,175 | approximate (group exact) |
| 3 | Walapane (p95 l31; 104,119; 125) | split | 2309 Walapane: 62 (513B, 516, 515) · 62,501 → 65,287; 2310 Nildandahinna: 63 (519E, 521A, 521) · 41,618 → 42,422 | approximate (group exact) |
| 4 | Nuwara Eliya (p98 l13; 212,094; 72) | split | 2312 Nuwara Eliya: 38 (476C, 535J, 534G) · 89,256 → 88,332; 2313 Thalawakelle: 34 (475P, 475Q, 475D) · 122,838 → 129,531 | approximate (group exact) |
| 5 | Ambagamuwa (p99 l38; 205,723; 67) | split | 2314 Norwood: 35 (320E, 320P, 320I) · 162,563 → 161,367; 2315 Ambagamuwa Koralaya: 32 (316C, 316D, 316) · 43,160 → 42,538 | approximate (group exact) |
| 6 | Baddegama, Galle (p108 l33; 75,008; 70) | split | 3127 Baddegama: 48 (199B, 199A, 199) · 48,057 → 50,956; 3128 Wanduramba: 22 (186D, 191B, 186A) · 26,951 → 27,702 | approximate (group exact) |
| 7 | Hikkaduwa, Galle (p111 l38; 101,909; 97) | split into three | 3135 Madampagama: 38 (80, 80C, 80B) · 33,935 → 33,408; 3136 Hikkaduwa: 27 (59D, 59A, 58) · 27,075 → 26,216; 3137 Rathgama: 32 (48A, 49A, 49B) · 40,899 → 41,456 | approximate (group exact) |
| 8 | Balangoda, Ratnapura (p280 l25; 81,563; 53) | split | 9118 Balangoda: 41 (266, 265A, 265C) · 69,395 → 74,893; 9119 Kaltota: 12 (258C, 258, 259A) · 12,168 → 13,018 | approximate (group exact) |
| 9 | Panduwasnuwara East, Kurunegala (p205 l26; 32,386; 39) | boundary-adjusted: 3 GNs listed under East in 2012 and West in 2024 | 6145 Panduwasnuwara West gains 1341 Thengodagedara, 1342 Rideekanda, 1344 Moragolla (2,380 people in 2012); 6148 Panduwasnuwara East keeps 36 · 30,006 → 31,790 | approximate (group exact) |
| 10 | Poojapitiya, Kandy (p55 l24; 57,914; 67) | renamed (spelling) | 2106 Pujapitiya: all 67 GNs (531, 528, 529 …) · 57,914 → 60,316 | **exact** |

Corroboration: the DS counts by district in Final Report Tables 2.3 (2012) and 2.4 (2024)
change only in Nuwara Eliya (+5), Galle (+3) and Ratnapura (+1), matching samples 1–8 ✅. The
gazettes creating the new divisions were **not** found or checked ❌; the evidence is DCS's own GN
lists in both years.

## Unmatched GNs (all listed, none dropped)

`gn_unmatched_2012_2024.csv` lists 18 2012 rows and 4 2024 rows.

| Group | n | Reason |
|---|---|---|
| Matale 2012 GNs in Naula (5) and Laggala-Pallegama (8) | 13 | DCS: 13 of 545 Matale GNs removed for the Kalu Ganga and Moragahakanda reservoirs (Final Report Table 2.4 note 1) ✅. The count matches exactly. |
| Victoria, Kandy (2012, GN 825) | 1 | Listed in 2012 without figures; no 2024 row ❓ |
| Slave Island (2012) / Kompagngnaweediya (2024), Colombo DS | 1 + 1 | No GN numbers in Colombo; names differ. Possibly a rename ❓; not matched |
| Kommathurai East, Eravur Pattu | 1 + 1 | The 2012 text layer garbles the name ("Kommathurai EastKommathurai Eas196"); not matched |
| Kavanthissapura and Pulmoddai Division No. 2 (both GN 31H in 2012 and 2024), Trincomalee | 2 + 2 | Duplicate GN number in both lists; names spelled differently; not matched |

Population in unmatched 2012 GNs: 13,002 (all inside units whose comparison uses the DCS DS
total, so the national rebuild stays complete).

## District census series

`district_census_series.csv`: 475 rows (26 places × 14 Abstract years + Final Report 1981/2001/
2012/2024 rows). Labels: `exact` 128, `approximate` 333, `not_comparable` 14 (Chilaw). Value
status: `normal` 400, `not_available` 68 (district not yet created), `estimate` 7 (2001, seven
Northern and Eastern districts).

Abstract Table 2.1 transcription check ✅: 310 values, 0 missing from the PDF text layer;
districts minus national total by year (thousands): 1871 −0.9, 1881 +0.1, 1891 0.0, 1901 +0.1,
1911 −0.1, 1921 −0.1, 1931 −0.3, 1946 +0.1, 1953 +0.6, 1963 −0.6, 1971 −0.4, 1981 −0.2, 2001 0.0,
2012 −0.2 (rounding of 20–25 one-decimal figures).

Disagreements between DCS's own tables (kept side by side, D-019):

| Year | Abstract 2024 T2.1 vs Final Report 2024 T3.3 |
|---|---|
| 2012 | identical in all 25 districts (to the thousand) ✅ |
| 2001 | Abstract higher in all 18 enumerated districts (Colombo +11,604; Anuradhapura +3,165; …) |
| 1981 | Abstract higher in every district (Colombo +23,353; Gampaha +23,087; Nuwara Eliya +19,884; Jaffna +96,126, where T3.3 uses current boundaries for Jaffna and Kilinochchi). **T3.3's 1981 districts sum to 14,629,224, 217,050 below its own national 14,846,274** (checked against the page image); T3.1 gives 14,846,750 for the same census |

## Not verified

- The DCS original of the 2012 GN file (we hold a mirror; D-035). Its DS totals all agree with
  DCS's Abstract Table 2.7, and its district totals with the Final Report, so a corrupted copy is
  unlikely ❓, but GN-level rows have no independent DCS check.
- Gazettes for the 2012–2024 DS creations, and whether any GN boundary moved without a GN
  number change.
- The Abstract Table 2.1 transcription has not been checked by a person.
- Which districts lost ground to each district created before 2001.
