# G06: Boundary vintages and 2012↔2024 comparability

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 2 | Geography | 1 | 2026-11-07 | draft (refresh with M03 at Stage 2) |

## When to use
To make change-over-time comparisons honest when DS and GN units were split, merged or renamed between censuses.

## Read first
- `AGENTS.md`
- `docs/architecture/data-model.md` §3.3 (identity vs version; succession relations; comparison labels)
- Census 2024 final report tables 2.2–2.4 (administrative structure by district, 1981, 2012, 2024) 🟡, as parsed in nuuuwan `lk_census_2024` (cross-check)
- G02 crosswalk report

## Inputs (fill in)
```
FROM_VINTAGE: 2012
TO_VINTAGE:   2024
LEVEL:        ds (start here; gn only if 2012 GN data and boundaries exist)
```

## Task
1. Assemble the FROM unit list (DCS 2012 census tables; nuuuwan `lk_census_2012` as cross-check) and any FROM boundaries available with recorded rights.
2. Identify changes FROM→TO: unchanged, renamed, split, merged, boundary-adjusted, new. Use evidence (census report tables, gazettes, name and parent matching, spatial overlap where geometry exists). Cite evidence per change.
3. Create succession relations (`preceded_by` / `succeeded_by`) with weights. For splits, use TO-vintage GN population shares where GN membership is known; otherwise area, flagged.
4. Classify every FROM→TO pair as `comparison: exact` or `approximate`, with the method.
5. Produce a comparable DS-level population table (2012 vs 2024, change and growth rate) where comparisons are valid, and list where they are not.
6. QA report and methods note `docs/methods/boundary-change-2012-2024.md`.

## Constraints
- Never present an approximate comparison as exact. The UI must be able to show the label.
- Don't reconstruct boundaries by drawing. Use existing evidence only.

## Verify (show real output)
Change-type counts; national total reconciliation (sums equal official totals for both years); 10 sample changes with evidence.

## Deliverables
Succession relations, comparison table, QA report and methods note.

## Done when
Every DS-level 2012→2024 change shown on the site carries an exact/approximate label backed by evidence.

Report using the format in `AGENTS.md`.
