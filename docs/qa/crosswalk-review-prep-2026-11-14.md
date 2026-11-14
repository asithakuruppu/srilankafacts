# Crosswalk review queue: pre-triage for the lead (agent suggestions, no decisions)

Prepared 2026-11-14 by an agent. **Nothing here is a decision.** No crosswalk entry, `manual-matches.csv`, `manual-review.csv`, override or `raw/` file was changed. Every recommendation is an *agent suggestion* for the lead to approve, change or reject.

Per-item table: [`crosswalk-review-prep-2026-11-14.csv`](crosswalk-review-prep-2026-11-14.csv) (428 rows = the whole queue; columns: item id, group, queue candidates, suggested unit, action, evidence, recommendation, confidence).

Tags: ✅ verified by the agent (ran it, read it) · 🟡 claimed by a source or read by the agent but not independently checked (for example Sinhala names read by the agent, not by a Sinhala speaker) · ❌ not found / failed · ❓ assumption.

## 1. What the queue is

`catalog/geographies/manual-review.csv` (written by `slf crosswalk build`, `docs/research/geography/crosswalk-report.md` §3) holds **428 items** ✅:

| System | Items | What they are |
|---|---|---|
| DCS Census 2024 (authoritative for census joins) | 42 | 41 GN + the DS `5224 Kalmunai`. This is the "41 unmatched DCS GN units" |
| nuuuwan (copy of DCS codes) | 41 | the same 41 GN units as DCS; they follow the DCS decision |
| NSDI 2017 (cross-check only) | 345 | 341 GN-layer rows + 4 DS rows |

So there are really **42 DCS questions** that affect published census values, and about 340 NSDI cross-check rows that do not. The 2026-11-12 review already cleared 22 other DCS items (`manual-matches.csv`); they are not in the queue.

## 2. Groups at a glance (approve a whole group at once)

| Group | Items | What it is | Agent suggestion | Confidence | Lead effort |
|---|---|---|---|---|---|
| **G1** | 3 DCS (+3 nuuuwan) | Same code and DS; COD-AB/NSDI Sinhala name equals the DCS name though the English label differs | Match | high 🟡 | approve as a group |
| **G2** | 3 DCS (+3) | Same code and DS; DCS label is a spelling/granularity variant of COD-AB's | Match | medium | approve after a glance |
| **G3** | 2 DCS (+2) | DCS label duplicates another DCS unit in the same DS; the same-code COD-AB unit has no DCS partner | Match, flagged as probable DCS label error | medium ❓ | decide individually |
| **G4** | 1 DCS (+1) | Kokuthoduvai South: in DCS only | Do not match; likely new GN | medium | lead's call |
| **G5** | 3 DCS (+3, +3 NSDI) | Eravur boundary difference | Hold | low | needs outside evidence |
| **G6** | 30 DCS (+29, +29 NSDI) | Kalmunai: DS 5224 and its 29 GNs | Hold | low | waits on D-022 follow-up |
| **N1** | 277 NSDI | NSDI GN row under an old DS code; same-name, same-GN-number unit exists in the right COD-AB DS | Match | high ✅ | approve as a group |
| **N4** | 34 NSDI | NSDI polygons with no GN code/name, and two "Water Area" pseudo-DS | No match (not admin units) | high | approve as a group |
| **N5** | 2 NSDI | Duplicate NSDI DS records (2154, 6175) | No action | high | approve as a group |

**Easy bulk approvals:** G1 + N1 + N4 + N5 (3 DCS GNs plus 313 NSDI rows). **Quick look:** G2, G3 (5 DCS GNs). **Hard cases:** G4, G5, G6 (34 DCS items). Census effect of the DCS suggestions (DCS 2024 population in the units concerned ✅): G1 5,701, G2 6,358, G3 3,087, G4 196, G5 3,547, G6 52,798 people.

**How to act on this:** reply with the groups to approve (for example "approve G1, G2, N1, N4, N5; G3 only 1321190"). A follow-up task then writes the rows into `manual-matches.csv` as `decided_by: lead` with the evidence from the CSV, rebuilds the crosswalk and re-runs QA. Nothing is applied until then.

**Checks run on all suggestions** ✅: every suggested spine unit exists; none of the 8 DCS suggested units is already matched to another DCS code; none of the 277 N1 target units is already matched to another NSDI row or targeted twice.

## 3. DCS groups in detail

### G1: same code, Sinhala name agrees (3 units, high)

| DCS code | DCS name | DCS pop. | Suggested unit (en / si) | Conf. |
|---|---|---|---|---|
| 4133065 | Neeraviyady | 1,501 | LK4133065 Vannarponnai N.E. (South) / නීරාවියඩි | high |
| 7215170 | Gallella | 2,255 | LK7215170 Gallalla East / ගල්ලෑල්ල | high |
| 8124160 | Kottagoda | 1,945 | LK8124160 Imbulgoda / කෝට්ටගොඩ | high |

Evidence per unit is in the CSV. Pattern: the DCS 2024 label is the Tamil/Sinhala-origin name, COD-AB's English label is different (for LK8124160 it repeats the neighbour's name "Imbulgoda"), but COD-AB and NSDI Sinhala names for the same code read as the DCS name 🟡. A Sinhala reader should confirm the three readings.

### G2: same code, label variant (3 units, medium)

| DCS code | DCS name | DCS pop. | Suggested unit (en / si) | Conf. |
|---|---|---|---|---|
| 4133055 | Vannarpannai N.W. | 2,439 | LK4133055 Vannarponnai N.W. (West) / වන්නාර්පන්නයි වයඹ | medium |
| 4133060 | Vannarpannai N.E. | 2,205 | LK4133060 Vannarponnai N.E. (North) / වන්නාර්පන්නයි ඊසා | medium |
| 7142005 | Thulana Track 18 | 1,714 | LK7142005 Track 13,18 / රාජාංගනය යාය 18 | medium |

The three Nallur units (4133055, 4133060, 4133065 with G1) form one consistent set: NSDI GN numbers 98–101 run in code order. Approving 4133055/4133060 without 4133065 would be odd; approve the three together.

### G3: probable DCS label errors (2 units, medium ❓)

| DCS code | DCS name | DCS pop. | Suggested unit (en / si) | Conf. |
|---|---|---|---|---|
| 1321190 | Pothupitiya North | 2,410 | LK1321190 Kuda Waskaduwa South / කුඩා වස්කඩුව දකුණ | medium |
| 7151120 | Perimiyankulama | 677 | LK7151120 Paindikulama / පයින්ඩිකුලම | medium |

In both cases the DCS label copies another DCS unit in the same DS (a duplicate name), and the same-code COD-AB unit would otherwise have **no** DCS partner. The queue's top candidate in both cases is the twin, which is wrong. Not confirmed; only an official GN list settles it. If the lead prefers caution, keep these two unmatched and approve the rest.

### G4: Kokuthoduvai South `4415095` (1 unit)

DCS only: absent from NSDI 2017 and COD-AB 2022 ✅, population 196, in a gap of the COD-AB code sequence (090, then 100). Suggestion: no match; options are to leave it unmatched (it stays in the QA report) or to create a provisional unit as for Kalmunai (D-022). This is the dating note's one likely new GN (`docs/research/geography/dcs-review-items-dating.md`).

### G5: Eravur Town / Eravur Pattu (3 units, low)

| DCS code | DCS name | DCS pop. | Suggested unit (en / si) | Conf. |
|---|---|---|---|---|
| 5115005 | Ellainagar | 1,146 | - | low |
| 5115010 | Eravur 04 | 847 | - | low |
| 5115075 | Eravur 05 | 1,554 | - | low |

Facts ✅: DCS and NSDI 2017 agree (Eravur Town 15 GNs, Eravur Pattu 39); COD-AB has Eravur Town 13 and Eravur Pattu 47, with unnamed units `LK5139007` (0.05 km²), `LK5115006` (0.87), `LK5115014` (0.39), `LK5115016` (0.15). NSDI flags all three DCS units "GN boundary dispute with Gap". The queue's candidates are misleading: code `5115005` etc. exists in COD-AB, but as Eravur Pattu units that DCS DS 5112 already matches. Three DCS units against four unnamed COD-AB units, with no way to pair them ❓. Suggestion: hold for an official GN list or GN boundaries.

### G6: Kalmunai DS 5224 and its 29 GNs (30 items, low)

The DS question was reviewed on 2026-11-08 and is unchanged. NSDI 2017 already lists these 29 codes under 5224 with DCS names ✅, so the split predates COD-AB. COD-AB's 29 unnamed units `LK5221150`–`LK5221300` (area km² in brackets: 5221150 (0.32), 5221155 (0.13), 5221160 (0.14), 5221165 (0.22), 5221170 (0.72), 5221175 (0.32), 5221180 (0.35), 5221185 (0.52), 5221190 (0.32), 5221195 (0.17), 5221200 (0.09), 5221205 (0.17), 5221210 (0.25), 5221215 (0.59), 5221230 (0.23), 5221235 (0.66), 5221240 (0.73), 5221245 (0.08), 5221250 (0.05), 5221255 (0.11), 5221260 (0.08), 5221265 (0.07), 5221270 (0.17), 5221275 (0.08), 5221280 (0.53), 5221285 (0.09), 5221290 (0.08), 5221295 (0.12), 5221300 (0.84)) are the only possible homes, but nothing in the held data says which is which: NSDI's DS polygon covers all of LK5221 ✅ and we hold no NSDI GN polygons ❌. Each queue candidate shown for these rows is a named DCS 5221 unit that is already matched, so it is wrong. DCS 5224080 `Kalmunaikudi 01` (also flagged "already matched to LK5221080") is the same case.

| DCS code | DCS name | DCS pop. | NSDI GN no. | NSDI Sinhala (gazetted) |
|---|---|---|---|---|
| 5224005 | Periyaneelavanai  Muslim Section | 2,245 | KP/72 | පෙරියනීලාවණයි 01 (MD) |
| 5224010 | Periyaneelavanai  Muslim Section | 1,199 | KP/72A | පෙරියනීලාවණයි 02 (MD) |
| 5224015 | Maruthamunai 01 | 1,141 | KP/67B | මරදමුනේ 01 |
| 5224020 | Maruthamunai 02 | 1,419 | KP/67 | මරදමුනේ 02 |
| 5224025 | Maruthamunai 03 | 4,840 | KP/67A | මරදමුනේ 03 |
| 5224030 | Maruthamunai 04 | 2,162 | KP/67C | මරදමුනේ 04 |
| 5224035 | Maruthamunai 05 | 1,360 | KP/67D | මරදමුනේ 05 |
| 5224040 | Maruthamunai 06 | 4,251 | KP/68 | මරදමුනේ 06 |
| 5224045 | Natpiddimunai (M.P ) 03 | 1,167 | KP/64 | නට්පිට්ටිමුනේ 03 (MD) |
| 5224050 | Natpiddimunai (M.P ) 02 | 877 | KP/64B | නට්පිට්ටිමුනේ 02 (MD) |
| 5224055 | Natpiddimunai (M.P ) 01 | 947 | KP/64A | නට්පිට්ටිමුනේ 01 (MD) |
| 5224060 | Natpiddimunai (M.P ) 05 | 1,046 | KP/64D | නට්පිට්ටිමුනේ 05 (MD) |
| 5224065 | Natpiddimunai (M.P ) 04 | 1,127 | KP/64C | නට්පිට්ටිමුනේ 04 (MD) |
| 5224070 | Islamabad & kalmunai Town | 1,684 | KP/59A | කල්මුණේ 01 (MD) |
| 5224075 | Kalmunai Muslim Section | 3,546 | KP/59 | කල්මුණේ 03 (MD) |
| 5224085 | Kalmunaikudi 03 | 2,880 | KP/58A | කල්මුණේකුඩි 03 |
| 5224090 | Kalmunaikudi 02 | 1,599 | KP/58C | කල්මුණේකුඩි 02 |
| 5224095 | Kalmunaikudi 04 | 950 | KP/58B | කල්මුණේකුඩි 04 |
| 5224100 | Kalmunaikudi 05 | 1,827 | KP/56 | කල්මුණේකුඩි 05 |
| 5224105 | Kalmunaikudi 06 | 1,281 | KP/56F | කල්මුණේකුඩි 06 |
| 5224110 | Kalmunaikudi 08 | 1,117 | KP/56D | කල්මුණේකුඩි 08 |
| 5224115 | Kalmunaikudi 09 | 3,267 | KP/56B | කල්මුණේකුඩි 09 |
| 5224120 | Kalmunaikudi 07 | 1,792 | KP/56E | කල්මුණේකුඩි 07 |
| 5224125 | Kalmunaikudi 10 | 1,075 | KP/56C | කල්මුණේකුඩි 10 |
| 5224130 | Kalmunaikudi 11 | 1,218 | KP/56A | කල්මුණේකුඩි 11 |
| 5224135 | Kalmunaikudi 12 | 1,105 | KP/55 | කල්මුණේකුඩි 12 |
| 5224140 | Kalmunaikudi 13 | 1,899 | KP/54A | කල්මුණේකුඩි 13 |
| 5224145 | Kalmunaikudi 14 | 2,212 | KP/54 | කල්මුණේකුඩි 14 |
| 5224080 | Kalmunaikudi 01 | 1,565 | KP/58 | කල්මුණේකුඩි 01 |

Suggestion: keep all 30 in the queue. A route that does not need the pairing: create a second provisional DS unit for DCS 5224 composed of its 29 GNs (as D-022 did for Kalmunai North Sub) and keep the 29 unnamed COD-AB GNs labelled by p-code. That is a lead decision; the agent has not created anything. Total DCS 2024 population in these 29 GNs: 52,798 ✅.

## 4. NSDI groups in detail (cross-check source only)

### N1: old DS code, 277 rows (high ✅)

NSDI GN rows carry a DS code that differs from COD-AB's for nine DS divisions. In each, the NSDI DS *name* equals the COD-AB DS name, the NSDI GN name is unique within that COD-AB DS, and the last three digits (the GN number within the DS) agree. 271 also have an equal Sinhala name and 270 are independently listed under the same name in DCS and matched to the same unit ✅ (every row has at least one of the two). The cause of the DS code difference is not established ❓ (`crosswalk-report.md` §4 lists the DS-level differences for eight of these DS divisions; Panduwasnuwara West is not in that table, see section 6).

| NSDI DS name | NSDI old DS code | COD-AB DS | GN rows to match |
|---|---|---|---|
| Kalthota | 9118 | LK9154 Kalthota | 12 |
| Kothmale West | 2303 | LK2321 Kothmale West | 49 |
| Madampagama | 3136 | LK3160 Madampagama | 38 |
| Mathurata | 2306 | LK2318 Mathurata | 52 |
| Norwood | 2315 | LK2330 Norwood | 35 |
| Panduwasnuwara West | 6148 | LK6145 Panduwasnuwara West | 3 |
| Rathgama | 3136 | LK3163 Rathgama | 32 |
| Thalawakele | 2312 | LK2327 Thalawakele | 34 |
| Wanduramba | 3127 | LK3157 Wanduramba | 22 |

Why it matters little for census: NSDI is a cross-check, so matching these would lift NSDI GN coverage from 97.57% (build report) to about 99.5% (13,987 of 14,051; arithmetic only 🟡).

### N2 / N3: Kalmunai (29) and Eravur (3) NSDI rows

The same units as G6 and G5; decide together.

### N4: no-code polygons and "Water Area" (34 rows)

32 NSDI GN-layer rows have `admin_code` 0 and no GN name (listed with their DS name, mainly Koralai Pattu, Eravur Pattu and Water Area), and two DS rows are `Water Area` code 9999 ✅. They are not administrative units. Suggestion: record as "no spine counterpart"; exclude from joins.

### N5: duplicate NSDI DS records (2 rows)

NSDI lists DS 2154 Ganga Ihala Korale and 6175 Udubaddawa twice; the first record is matched ✅. No action.

## 5. What was and was not checked

- ✅ Counts, codes, names, candidates: read from `manual-review.csv`, `codes/*.csv`, the spine (`geographies.parquet`, GN polygons in the spine gpkg, areas in EPSG:5235) and the raw NSDI attribute and DCS workbook snapshots (read only).
- ✅ Neighbour lists for the Eravur units: spine adjacency (`adjacency_gn_cod-ab-v03.parquet`).
- ❌ **No boundary overlap at GN level.** We hold NSDI attributes for GNs but no NSDI GN polygons; only DS-level polygons were compared in G03 (`docs/research/geography/geometry-qa-cod-ab-v03.md`). So no GN-level overlap figure is given anywhere here.
- 🟡 Sinhala names were read by the agent (G1, N1 Sinhala equality is exact string equality on the stored text, which is a stronger check ✅, but the *meaning* of the three G1 readings is the agent's). Tamil names: neither COD-AB nor NSDI holds Tamil GN names in the spine (`name_ta` is empty for the units shown), so no Tamil evidence exists ❌.
- ❓ COD-AB and NSDI probably share Survey Department lineage, so their agreement is not two independent confirmations (`dcs-review-items-dating.md`).
- ❓ Whether the 2022 COD-AB or the 2017 NSDI layer is closer to the 2024 DCS units is not settled beyond what `dcs-review-items-dating.md` states.
- Not run: the pipeline (`slf crosswalk build`) was not re-run; the committed queue was used, as the crosswalk build does not change it.

## 6. Odd findings

- **Panduwasnuwara West** (3 N1 rows): NSDI DS code 6148 vs COD-AB `LK6145`. This DS is not in the DS-drift table of `crosswalk-report.md` §4 (which lists DCS-vs-COD-AB drift, not NSDI-vs-COD-AB). The three rows still pass every N1 check ✅, but the DS-level cause is unexplained ❓.
- The queue's "candidates" for G5, G6 and several G1–G3 items are wrong by construction (they are units already matched to another row). A reviewer using only `manual-review.csv` could approve a wrong match; the CSV here records the right one.

## 7. Report

### Summary
Pre-triaged all 428 crosswalk review items into nine groups with evidence, an agent-suggested action and a confidence each. Three DCS units and 313 NSDI rows are easy bulk approvals, five DCS units need a quick look, and 34 DCS items (Kalmunai, Eravur, Kokuthoduvai South) are hard and need outside evidence. Nothing was approved or changed; this is a review document and CSV only.

### Evidence
- Queue read from `catalog/geographies/manual-review.csv`: 428 rows (DCS 42, nuuuwan 41, NSDI 345) ✅
- Grouping result: G1 3, G2 3, G3 2, G4 1, G5 3, G6 30 (DCS); N1 277, N2 29, N3 3, N4 34, N5 2 (NSDI) ✅ (printed by the generating script)
- Suggested-unit checks: 0 of 8 DCS suggestions already matched elsewhere; 0 of 277 N1 targets duplicated ✅
- The generating script was a one-off (not committed), like `dcs-review-items-dating.md`; the CSV is its output.

### Not verified / known gaps
No GN-level boundary overlap (no NSDI GN polygons held). Agent-read Sinhala meanings are unreviewed. No Tamil names. Causes of DS code drift (including Panduwasnuwara West) unexplained. Kalmunai and Eravur pairings cannot be made from held data.

### Docs updated
Added this document and its CSV. No decision-log, catalogue or crosswalk file changed.

### Decisions needed from the lead
1. Approve G1 + N1 + N4 + N5 as groups? Recommendation: yes.
2. Approve G2 (the three Nallur/Track units, ideally with the Nallur unit from G1)? Recommendation: yes after a glance.
3. G3: match the two probable DCS label errors, or keep unmatched? Recommendation: match, labelled as probable label error.
4. G4: leave Kokuthoduvai South unmatched or create a provisional unit? Recommendation: leave unmatched for now.
5. G5/G6: keep held, and ask the Survey Department for the official GN list (already in the outreach draft)? Recommendation: yes; consider a provisional DS unit for Kalmunai 5224 as a separate decision.
