# W04: Indicator pages and charts

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 1 | Frontend / Content | 1 | 2026-11-07 | active |

## When to use
To build `/indicator/[id]` pages that explain a measure and show it across places.

## Read first
- `AGENTS.md`
- `catalog/indicators/` (definitions, aggregation, higher_is)
- `docs/architecture/data-model.md` §4, §6
- W01 chart decision and components

## Inputs (fill in)
```
INDICATORS: list for this PR (start with the headline set)
```

## Task
1. Template: plain-language definition, how it is measured (source definition, reference date), map at a sensible default level, distribution chart, highest and lowest units (only where neutral and meaningful, with context), time series if available, caveats, related indicators, downloads, provenance and citation.
2. Charts from the W01 library with text alternatives and a "show as table" toggle.
3. Colour direction respects `higher_is` (neutral indicators use sequential scales without good/bad framing).
4. Link the methodology page (C01) and source pages.
5. Tests: render each indicator in the release; the values on the page equal the release values (an automated comparison on a sample).

## Constraints
- No editorial judgement in labels. Explain, don't advocate.

## Verify (show real output)
Screenshots; automated value comparison output; axe results.

## Deliverables
Templates, tests, any new shared chart components.

## Done when
Each headline indicator has a page a journalist could cite with confidence.

Report using the format in `AGENTS.md`.
