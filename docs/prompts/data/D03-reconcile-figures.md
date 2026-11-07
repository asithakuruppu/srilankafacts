# D03: Reconcile conflicting figures

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| any | Data / Research | 1 | 2026-11-07 | active |

## When to use
When two credible sources give different numbers for what looks like the same thing (for example DS division counts of 331, 332 or 339; census totals in a news report vs DCS; MOH population in a health bulletin vs our denominator).

## Read first
- `docs/architecture/live-events-and-sources.md` §2 and decision D-019 (every value is a claim; conflicts are shown, not hidden)
- `AGENTS.md`
- `docs/architecture/data-model.md` §6 (`reconciled` / `disputed`)
- The relevant catalogue entries and QA reports

## Inputs (fill in)
```
QUESTION:  e.g. "How many DS divisions does Sri Lanka have?"
FIGURES:   each figure with its source and locator
```

## Task
1. Pin down each figure exactly: source, document, page or cell, publication date, reference date.
2. Compare definitions: reference date, coverage (for example water areas, disputed areas), de jure vs de facto, boundary vintage, revisions, rounding, units, administrative vs statistical units.
3. Explain each difference with evidence, or mark it unexplained.
4. Recommend display: one preferred figure with the others noted, or `disputed` with both shown. Explain the choice in plain language.
5. Write `docs/methods/reconciliations/{{slug}}.md`. Update affected observations' `verification` and notes. Propose an errata note to a publisher (via R04) if a source appears wrong.

## Constraints
- Don't average conflicting figures. Don't pick the "most common" figure without a reason.

## Verify (show real output)
Each figure with locator and retrieval date; the definition comparison table.

## Deliverables
Reconciliation note and observation updates (through overrides or notes).

## Done when
A reader can see why the numbers differ and which one we show.

Report using the format in `AGENTS.md`.
