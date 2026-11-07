# Q01: Accuracy audit of published values

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| every release | Quality | 1 | 2026-11-07 | active |

## When to use
Before every public release (a hard gate for the Stage 1 launch) and after major pipeline changes.

## Read first
- `AGENTS.md`
- The release manifest, QA summary and changelog (D04)
- `docs/architecture/data-model.md` §5–§7

## Inputs (fill in)
```
RELEASE:      version (or the release candidate path)
SAMPLE_SIZE:  default max(100, 2% of headline values)
THRESHOLDS:   headline figures 0 errors; others ≤ 0.5% (lead may change)
```

## Task
1. Draw a **stratified random sample** (by dataset, level, indicator; oversample national, province and district headline figures and every value with an override). Record the random seed.
2. For each sampled value, trace release → dataset → snapshot → source locator, open the source (file cell or PDF page) and compare. Also check that the **website and API display the same value** as the release.
3. Classify each mismatch: extraction, harmonisation (wrong unit mapping), unit or scale, rounding, display bug, source ambiguity.
4. Compute error rates against THRESHOLDS. List every error with evidence and a GitHub issue per root cause.
5. Prepare a short sheet for the lead: the 20 highest-stakes sampled values with source images, for personal confirmation.
6. Write `qa/accuracy-audit-{{release}}.md` with the seed, sample, results and verdict (pass/fail).

## Constraints
- The auditor doesn't fix errors in the same PR. Fixes go to separate PRs so the audit stays independent.

## Verify (show real output)
Sample composition table; per-value results table; error rates; the seed.

## Deliverables
Audit report, issues, the lead's confirmation sheet.

## Done when
The lead has a pass/fail verdict with evidence. Fail blocks the release.

Report using the format in `AGENTS.md`.
