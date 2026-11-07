# Q02: Performance audit (low-end mobile first)

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 1+ | Quality / Frontend | 1 | 2026-11-07 | active |

## When to use
Before launch, after major UI changes, and quarterly.

## Read first
- `AGENTS.md`
- `docs/design/performance-budget.md` (W01)
- `docs/architecture/architecture-overview.md` §5.1–§5.2

## Inputs (fill in)
```
URL:     preview or production base URL
ROUTES:  home, a district page, a GN page, an indicator page, /explore
```

## Task
1. Lighthouse (mobile, throttled) for each route, three runs each with the median reported; Core Web Vitals; compare with the budget.
2. Bundle analysis: JS per route, the largest modules, duplicate dependencies; check the map chunk loads lazily.
3. Network: tile bytes and data bytes per typical view (national view, district view, GN view); cache headers on versioned assets.
4. Runtime: memory after 20 place-to-place navigations; frame rate during fly-to on a throttled CPU.
5. Lite mode: verify triggers and fallback rendering.
6. Ranked recommendations with expected gains. Implement only trivial fixes; everything else becomes issues.
7. Write `qa/performance-{{date}}.md`.

## Constraints
- Measure, don't guess. Report device and throttling profiles used.

## Verify (show real output)
Lighthouse summary table; bundle analysis excerpt; network bytes table.

## Deliverables
Report and issues.

## Done when
The lead knows whether the budget holds and what to fix first.

Report using the format in `AGENTS.md`.
