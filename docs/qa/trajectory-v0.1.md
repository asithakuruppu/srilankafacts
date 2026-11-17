# QA: `trajectory` v0.1 (private, D-038)

Built 2026-11-17 with `uv run slf profile spaces` from the local history build (G06) and Census
2024 · method: [trajectory-space.md](../methods/trajectory-space.md)

**Counts only.** This repository is public, and the 2012 comparison is not publishable (D-038), so
no value from the space is reported here.

| Item | Count |
|---|---|
| DS divisions with a 2012–2024 population comparison | 339 |
| In the space (one-to-one 2012 predecessor, unchanged or renamed) | 320 ✅ |
| Excluded: split or boundary-adjusted (no same-footprint 2012 sex ratio) | 19 |
| Excluded for another reason | 0 |
| Of the 320, comparisons flagged `approximate` by the history build | 7 |

## Browser vs pipeline

For all 320 units the browser's 10 nearest (`web/src/lib/atlas/spaces.ts`) equal the pipeline's,
distances within 2 × 10⁻⁶ ✅ (`web/tests/unit/spaces.test.ts`, runs where the local build exists).

## Where it appears

Only on `/explore/space` in a local build with the history build present, under "Trajectory …
(private)", with the D-038 note. Its file is in the local atlas bundle, never in a release.
