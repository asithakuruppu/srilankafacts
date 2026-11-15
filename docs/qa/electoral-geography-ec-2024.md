# QA: electoral geography (G05, scheme `electoral`, vintage `ec-2024`)

Built 2026-11-15 with `uv run slf electoral build` (spine `cod-ab-v03` and the Census 2024 builds from the main checkout) · method: [denominators-electoral.md](../methods/denominators-electoral.md) · prompt: [G05 v2](../prompts/geography/G05-non-admin-geographies.md)

**Summary:**
- The 22 electoral districts (ED) are in the catalogue, with Election Commission codes, a district grouping and Census 2024 denominators. Every check passes.
- The 160 polling divisions (PD) have ids, codes and their parent ED, but **no GN composition is published**. No official GN list per PD exists publicly. The only list available (nuuuwan `gig-data`) has no licence, and the checks below show it is not reliable enough for denominators even if it were licensed.

## Verify (G05)

### 1. Counts

| Item | Count | Expected | |
|---|---|---|---|
| EDs in the Commission's register of electors 2016–2025 | 22 | 22 | ✅ |
| PDs in the register | 160 | 160 | ✅ |
| PD result sheets for the 2024 presidential election | 160 | 160 | ✅ (same 160 ids) |
| Postal-vote sheets | 22 | 22 | ✅ |
| Register: for every ED and every year 2016–2025, the PD figures sum to the printed ED total | 22 of 22 EDs | all | ✅ |
| COD-AB districts grouped into EDs | 25 | 25 | ✅ (each once) |
| nuuuwan `gig-data` PDs / EDs | 160 / 22 | — | ✅ same ids |
| nuuuwan GN rows / matched to the spine through `codes/nuuuwan.csv` | 14,021 / 13,620 | — | 401 nuuuwan GN ids have no crosswalk row ([unmatched list in the build](#outputs)) |

### 2. Weight sums (each spine GN's total weight across the scheme's units)

| Scheme level | Distribution over 14,043 spine GNs |
|---|---|
| ED (district grouping, catalogue) | 14,043 GNs with weight 1.0 ✅ |
| PD (nuuuwan, internal only) | 13,620 with 1.0; **423 with 0** (no PD) ❌ |

ED against nuuuwan's per-GN `ed_id`: **0 of 13,620** matched GNs disagree ✅. Every nuuuwan PD's GNs fall inside that PD's own ED (0 PDs cross an ED boundary) ✅.

### 3. IoU (EPSG:5235), unit shape against the union of its member GNs

| | min | p5 | p25 | median | p75 | max | n |
|---|---|---|---|---|---|---|---|
| ED: nuuuwan ED shape vs COD-AB GNs of the district grouping | 0.941 | 0.976 | 0.986 | 0.994 | 0.996 | 0.998 | 22 |
| PD (internal): nuuuwan PD shape vs the COD-AB GNs nuuuwan assigns to it | 0.221 | 0.781 | 0.936 | 0.961 | 0.977 | 0.994 | 160 |

- The lowest ED is Jaffna (0.941: 2,299 km² against 2,410 km² for the GN union). That is consistent with coastline and island differences between two boundary sources. ❓ Not inspected on a map.
- 21 PDs have IoU < 0.9 and 10 have < 0.8. The worst is Galle PD G (07G) at 0.22: a 66 km² shape against 15 km² of assigned GNs. The others below 0.8 include the four Nuwara-Eliya PDs (06A–D: 0.36–0.60), Digamadulla C (13C, 0.49) and Colombo Central (01B, 0.69).
- nuuuwan's shapes and nuuuwan's own GN list disagree, so at least one of them is wrong for these PDs ❌.

### 4. Denominators against published totals

The published totals are the registered electors on the 2024 presidential result sheets. For EDs these include postal voters. Electors are 18+ and the census has five-year bands, so the adult population is bracketed by aged 15+ and aged 20+ (Census 2024, 19 Dec 2024).

| | min | p5 | p25 | median | p75 | max |
|---|---|---|---|---|---|---|
| ED: electors per 100 people aged 20+ | 97.9 | 104.2 | 111.6 | 113.5 | 115.5 | 123.2 |
| ED: electors per 100 people aged 15+ | 89.0 | 94.2 | 99.2 | 101.4 | 103.3 | 109.0 |
| PD (internal composition): electors per 100 aged 20+ | 40.1 | 93.2 | 103.5 | 106.8 | 112.1 | 654.9 |

The 10 EDs furthest from the median (electors per 100 aged 20+):

| ED | electors | aged 20+ | aged 15+ | per 100 aged 20+ |
|---|---|---|---|---|
| LK-ED-01 Colombo | 1,765,351 | 1,802,824 | 1,982,690 | 97.9 |
| LK-ED-06 Nuwara-Eliya | 605,292 | 491,430 | 555,582 | 123.2 |
| LK-ED-02 Gampaha | 1,881,129 | 1,808,492 | 1,997,515 | 104.0 |
| LK-ED-13 Digamadulla | 555,432 | 452,363 | 516,243 | 122.8 |
| LK-ED-11 Vanni | 306,081 | 284,173 | 321,704 | 107.7 |
| LK-ED-03 Kalutara | 1,024,244 | 943,039 | 1,049,707 | 108.6 |
| LK-ED-16 Puttalam | 663,673 | 562,097 | 632,830 | 118.1 |
| LK-ED-05 Matale | 429,991 | 368,170 | 411,512 | 116.8 |
| LK-ED-20 Moneragala | 399,166 | 360,707 | 403,353 | 110.7 |
| LK-ED-19 Badulla | 705,772 | 610,736 | 682,709 | 115.6 |

Digamadulla's census figures here are GN sums and miss 52,798 people in GNs not matched to the spine (Kalmunai, see below). Against the district total its ratio is lower.

In 21 of 22 EDs there are more registered electors than residents aged 20+ (all but Colombo), and in 16 of 22 more than residents aged 15+. The register and the census count different things: the register lists citizens at their registered address, while the census counts people where they were on census night. Explaining the gap is out of scope ❓ (possible reasons include registration away from where people live, and people abroad). These are reported figures, not a finding about any place.

PD outliers (internal composition) are extreme, for example Kankesanthurai (10C) at 655 electors per 100 aged 20+ and Jaffna PD A (10A) at 40. These are errors in the composition, not facts about the places. This is a second reason not to use nuuuwan's GN→PD list.

### 5. ED population: GN sums against census district totals

The sum of district totals over all EDs is 21,781,800. GN sums give 21,710,113. The gap of 71,687 is people in DCS GNs that the crosswalk does not match to the spine. By ED: Digamadulla 52,798 (Kalmunai, DCS 5224, no spine equivalent), Jaffna 6,145, Batticaloa 3,547, Kalutara 2,410, Anuradhapura 2,391, Polonnaruwa 2,255, Badulla 1,945 and Vanni 196. **ED denominators therefore use the district totals.** That is exact, because every ED is a set of whole districts. GN sums are kept only as this check.

## Outputs

Committed (generated by `slf electoral build`; do not edit by hand):
- `catalog/geographies/codes/electoral-ec-2024.csv`: 364 rows, for 22 EDs and 160 PDs, each with an `election-commission` code (`1`, `1-B`) and a `nuuuwan` code (`EC-01`, `EC-01B`).
- `catalog/geographies/relations/electoral_ec-2024.csv`: 25 ED `composed_of` district rows (weight 1, `manual`, grouping 🟡 from Wikipedia) and 160 ED `parent` PD rows (`official_list`, from the register).

Local build only (`pipeline/data/build/electoral/`, not committed): `ed_denominators.csv`, `ed_iou.csv`, `pd_denominators_internal.csv`, `pd_iou_internal.csv`, `ed_nuuuwan_disagreements.csv` (empty), `gig_gn_unmatched.csv` (401 rows) and `qa.md`. The two files marked internal are derived from unlicensed data and must not be published.

## Not verified

- The ED district grouping rests on a secondary source (Wikipedia) plus the register's PD names. The Constitution's text was not read ❓.
- No map check of ED or PD shapes was made (QGIS spot-check not done).
- Whether PDs are made of whole GNs at all (they predate today's GN boundaries) is unknown ❓. That is a question for the Election Commission (in the drafted letter).
