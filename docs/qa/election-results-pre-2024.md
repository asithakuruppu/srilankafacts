# QA: Presidential Election 2024 results by polling division and electoral district

Dataset `election-results` · built 2026-11-15 with `uv run slf build election-results` · method: [election-results.md](../methods/election-results.md) · source: [dossier](../research/sources/election-commission.md) · rights: **unclear, not publishable** ([memo](../research/rights/election-results.md); proposed D-039)

## Headline

| Check | Result |
|---|---|
| Files snapshotted from the Commission's 2024 results page | 231 stored, 0 failed ✅ (`raw/election-commission/election-results/`, page snapshot sha256 `7739f1c1…`) |
| Result sheets parsed | 182: 160 polling division + 22 postal-vote ✅ |
| PDs in the register (2016–2025) vs PD result sheets | 160 vs 160; none missing, none extra ✅ |
| Sheets complete and adding up (38 candidates sum to valid votes; valid + rejected = polled) | **170 of 182** ✅ |
| Values on the sheets (4 totals + 38 candidates × 182) | 7,644 |
| Read and accepted | 7,593 (99.3%) |
| Fixed by the sheet's own total and printed percentages (`derived`) | 23 (all 23 equal nuuuwan's value) |
| Not read | 33 |
| Withheld (read, but on a sheet that does not add up and not confirmed by its printed percentage) | 18 |
| Against `nuuuwan/lk_elections` (commit `5bae534`, comparison only) | **7,593 agree, 0 differ** ✅ |
| Our ED and national sums against the Commission's own district and all-island sheets | **879 compared, 0 differ** ✅ (63 not comparable because our sum is `not_available`) |
| National totals (sum of 182 sheets) | registered electors 17,140,354 · votes polled 13,619,916 · valid 13,319,616 · rejected 300,300 · turnout 79.46% (all totals complete) |
| Observations | 16,810 (16,572 `normal`, 238 `not_available`); 0 errors; 52 warnings (the unread and withheld values) |

## What the numbers mean

- **All four totals** (registered electors, polled, valid, rejected) were read on all 182 sheets, so every PD, ED and national total and turnout is available.
- **Candidate counts:** 51 cells on 23 sheets are `not_available`. Any ED or national sum that would include one of them is also `not_available`; sums are never partial. The affected EDs (candidate rows only): Matale (05), Digamadulla (13), Matara (08), Kegalle (22), Badulla (19), Mahanuwara (04), Anuradhapura (17) and Galle (07). The national figures for those candidates are therefore also `not_available`.
- **Postal votes** stay on the ED (`vote_type: postal`) and are never assigned to PDs.

## How errors were found and prevented

The first build accepted a value when at least two OCR passes agreed. That rule produced 4 wrong values (out of 7,604 then read), for example SLCP in `17_E.pdf` read as 199 where nuuuwan has 661. The Commission's district sheets independently showed that the ED sums were off by exactly those amounts: Anuradhapura SLCP −462 and Matara SLCP −994. So the errors were ours, not nuuuwan's. All four were on sheets that did not add up.

The rule is now: on a sheet whose candidates do not sum to its valid votes, keep only values confirmed by their printed percentage. After the change, 0 values differ from nuuuwan and 0 sums differ from the district sheets. The cost is 18 withheld values, some of which are probably right; they are on the verification sheet.

## Verification sheet

[`election-results-pre-2024-verification-sheet.csv`](election-results-pre-2024-verification-sheet.csv): 74 rows, one per value that is unread (33), withheld (18) or derived (23). Each row has the file, item, our value, the reads by method, and nuuuwan's value for reference. The columns `lead_value` and `lead_status` are left for the lead to fill (D02). By sheet: 12_PV (8), 5_PV (7), 4_I (6), 19_F, 13_C, 17_E and 22_D (5 each), and 16 others with 1–4 each. Most are small counts (single digits) that Vision OCR does not read when they stand alone in a cell.

Nothing is filled from nuuuwan. Every value remains `verification: machine_extracted` until the lead checks it (AGENTS rule 7).

## Not verified

- No value has been checked by a person against the PDFs. The agreement with nuuuwan and with the district sheets is strong evidence, not human verification.
- The district sheets contain rotated text; only their values confirmed by printed percentages were compared (879).
- The preference-count sheets (`*_Pref.pdf`) and `All_Island_Final_Votes.pdf` were snapshotted but not parsed (the second count is out of scope).
- `results.elections.gov.lk` was unreachable, so the live-results PDFs there could not be compared.
- The "displaced voters" (Vanni) link on the results page is a placeholder (`XXXVanni_Displaced_V1.pdf`) and was not fetched. nuuuwan's Vanni ED total equals its PDs plus postal votes (checked for Colombo, Jaffna and Kegalle only). ❓ Whether displaced-voter counts are inside the PD sheets was not checked.
