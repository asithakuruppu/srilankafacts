# G06: Boundary vintages and 2012↔2024 comparability

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 2 | Geography | 2 | 2026-11-15 | active |

## When to use
To make change-over-time comparisons honest when DS (or GN) units were split, merged, renamed or
adjusted between two censuses, and to keep a district census series with comparability labels.
First run: FROM 2012 → TO 2024 at DS level (done 2026-11-15, see Deliverables). Re-run when DCS
publishes a new census, a 2012↔2024 concordance, or the original 2012 GN file (D-035).

## Read first
- `AGENTS.md`
- `docs/architecture/data-model.md` §3.3 (identity vs version; `succeeded_by`/`preceded_by`; comparison labels)
- `docs/decisions/decision-log.md`: D-019 (conflicting sources shown), D-021 (edge tables), D-022 (provisional units, Kalmunai), D-030/D-032 (non-commercial publication), D-035 (2012 GN file via a mirror; vintage ids)
- `docs/methods/boundary-change-2012-2024.md` (the method this prompt runs) and `docs/qa/boundary-change-2012-2024.md` (last run)
- `docs/research/sources/dcs-census-2012-and-history.md` and `docs/research/rights/census-2012-and-history.md`
- Code: `pipeline/slf/history.py`, `pipeline/tests/test_history.py`; the 2024 side reuses `slf.datasets.census_2024_gnd.parse_population` and the DS crosswalk `catalog/geographies/codes/dcs-census2024.csv`

## Inputs (fill in)
```
FROM_VINTAGE: 2012
TO_VINTAGE:   2024
LEVEL:        ds   (gn only if DCS publishes a GN concordance or boundaries for FROM_VINTAGE)
```

## Task
1. **Sources and rights first.** Snapshot the inputs: `uv run slf history snapshot` (in `pipeline/`;
   stores the 2012 GN file from the pinned nuuuwan commit, Abstract 2024 Tables 2.1 and 2.7). The
   Census 2024 Final Report and GN workbook come from `census-2024-gnd-tables`. If a DCS address
   for the 2012 GN file is found, snapshot it under `raw/dcs/census-2012-tables/` and compare
   sha256 with the mirror; record the result in the dossier and D-035. If rights are unclear,
   record that and do not publish (no `publication` block without a lead decision).
2. **Extract page text** with `swift scripts/pdf_pages.swift <pdf> data/build/history/pdf-pages/<name> <pages>`
   for `gn2012` (all 300 pages), `abstract27` (1–6), `abstract21` (1), `fr2024` (60 63 64 67 69).
   `slf history build` prints the exact commands if any folder is missing.
3. **Build**: `uv run slf history build`. It rebuilds the 2012 district > DS > GN hierarchy from
   arithmetic (stops on any break), matches GNs inside each district on DCS GN number and name
   (four layers, never across districts, never against another publisher's names), classifies
   each DS (`unchanged`, `renamed`, `split`, `split_remainder`/`new`, `merged`,
   `boundary_adjusted`), writes `succeeded_by`/`preceded_by` relations for retired units to
   `catalog/geographies/relations/succession_ds_2012-2024.csv`, the comparison table with
   `exact`/`approximate` and method per 2024 DS, closed comparison groups, and the district
   census series, to `data/build/history/` and `docs/qa/data/boundary-change-2012-2024/`.
4. **Review the unmatched GNs** (`gn_unmatched_2012_2024.csv`). Add a documented reason only from
   a DCS source (as for the 13 Matale reservoir GNs). Never force a match by name similarity.
5. **Review new disagreements** between DCS tables in the district series and record them in the
   QA report (D-019: keep both, prefer neither without evidence).
6. Update `docs/qa/boundary-change-2012-2024.md` with the real output, and the method note if a
   rule changed.

## Constraints
- Never present an approximate comparison as exact. A rename alone keeps `exact`; any split,
  transfer or unmatched GN makes the unit-level comparison `approximate`.
- Don't reconstruct boundaries by drawing or from COD-AB/NSDI geometry; use DCS's GN lists.
- 2012 GN-level values stay unpublished (D-035); they are used only to rebuild 2012 DS
  populations on 2024 boundaries.
- Vintage ids `LK-ADM3-V2012-<district>-<order>` are only for retired units; never reuse them.
- DCS 5224 Kalmunai keeps no spine id until D-022 is revisited; no relation is written for it.
- The Abstract Table 2.1 transcription is agent-made; it stays `machine_extracted` until a
  person checks it against the page.

## Verify (show real output)
- The three reconciliation lines printed by `slf history build` (2012 and 2024: source total =
  Final Report Table 3.3 = sum of DS), DS count vs Table 2.3, rows found in Abstract 2.7.
- Change-type counts for both vintages and the comparison label counts.
- 10 sample changes with page/line locators and example GN numbers.
- `uv run ruff check . && uv run ruff format --check . && uv run pyright && uv run pytest` and
  `uv run slf catalog validate --root ../catalog` pass.

## Deliverables
Succession relations; comparison table and groups; district series; unmatched-GN list; QA report;
methods note; catalogue entries for the inputs; decision-log entries for any new rule.

## Done when
Every DS-level 2012→2024 comparison carries an `exact`/`approximate` label backed by GN-list
evidence, both national totals reconcile to the person, and every unmatched GN is listed.

Report using the format in `AGENTS.md`.
