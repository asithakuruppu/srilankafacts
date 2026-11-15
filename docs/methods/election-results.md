# Method: election results (Presidential Election 2024)

Dataset `election-results` · module `pipeline/slf/datasets/election_results.py` (parser `election_parse.py`, snapshots `election_snapshot.py`, OCR `pipeline/scripts/pdf_ocr.swift`) · QA: [election-results-pre-2024.md](../qa/election-results-pre-2024.md)

## Source

The Election Commission of Sri Lanka's 2024 presidential results page links one signed result sheet per polling division (160), one postal-vote sheet per electoral district (22), 22 district sheets and the all-island sheets. The page is snapshotted first, and the files to fetch are read from that snapshot. Each PDF is snapshotted unchanged (`raw/election-commission/election-results/<time>/<file>`, with URL, time and sha256).

## What a value means

| Indicator | Meaning |
|---|---|
| `electors_registered` | "Number of Registered Electors" printed on the sheet. On a postal-vote sheet this is the number of postal voters, who are not counted in any PD |
| `votes_polled`, `votes_valid`, `votes_rejected` | As printed. Valid votes are first-preference votes |
| `votes_candidate` | Votes obtained by one candidate (first preferences). The breakdown gives the ballot number, party code and name as printed |
| `turnout` | `votes_polled / electors_registered × 100`, recomputed. Postal turnout uses postal voters as the denominator and is not comparable with PD turnout |
| `votes_rejected_share`, `votes_candidate_share` | Recomputed from counts. The printed percentages are used only to check reads |

## Footprints

- A PD sheet → the PD (`LK-PD-NNX`).
- A postal-vote sheet → the ED (`LK-ED-NN`), breakdown `vote_type: postal`. **Never pushed down to PDs.**
- ED (no breakdown) = the sum of its PD sheets plus its postal sheet; national (`LK`) = the sum of all 182 sheets. The Commission's ED electors equal PD electors plus postal voters, so the sum is like for like. ✅ checked against nuuuwan's ED rows for Colombo, Jaffna and Kegalle, and against the Commission's district sheets (879 values, 0 differ).
- A sum with any `not_available` part is itself `not_available`.
- Time: `2024-09-21`, `snapshot`. Geography vintage `ec-2024`.

## Reading the sheets

Many sheets are scans. Each page is read four ways, all on the lead's Mac (nothing is sent to any service):

1. Vision OCR of the whole page;
2. Vision OCR of the right half;
3. Vision OCR of the votes column only, located from the "Votes Obtained" heading. Vision skips some numbers on a full page, for example 46,362 on `2_D.pdf`, which a column crop reads;
4. the PDF's own text layer, where there is one.

A candidate's row is found by party code (38 fixed codes; ballot number 4 is not on the sheets), or else by the printed name. A read is accepted when it matches the printed percentage (`|100 × votes / valid − printed| ≤ 0.0051`), else by a clear majority of reads. Then the sheet must add up: 38 candidates = valid, and valid + rejected = polled.

- **Sum repair:** if a sheet is off and exactly one other read fixes it, that read is used.
- **Derived:** if some cells are unread and the printed percentages plus the sheet total allow exactly one solution, the cells get that solution. They are marked `derived`, with note `derived_from_sheet_total`.
- **Withheld:** on a sheet that still does not add up, every value not confirmed by its printed percentage is withheld (`not_available`). This rule was added after majority reads produced 4 wrong values that the district sheets exposed (QA report).

Nothing is ever filled from another source. nuuuwan's `lk_elections` TSV is a comparison only.

## Verification

All values are `machine_extracted`. The 74 values that are unread, withheld or derived are listed in [the verification sheet](../qa/election-results-pre-2024-verification-sheet.csv) for the lead. A future step reads the completed sheet and writes `overrides/` rows (D02).

## Presentation rules (AGENTS rule 12; [live-events §3](../architecture/live-events-and-sources.md#3-election-results))

Counts, shares and turnout as published, with the Commission named on every page. No party-favourable colours, no "winner" language beyond the published count, and no inference about how groups of people voted. Linking results to census profiles is ecological and is labelled as such. Not publishable until a lead decision on rights (proposed D-039).

## Reproduce

```bash
cd pipeline
uv run slf build election-results --out-dir ./data/build   # macOS: needs swiftc for page text
```
