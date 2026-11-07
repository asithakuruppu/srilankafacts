# R03: Audit an external project or platform

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| any | Research | 1 | 2026-11-07 | active |

## When to use
To evaluate a competing, adjacent or reusable project (for example LankaStatMap, OpenGINXplore, a new Sri Lankan data portal, an open-source tool). Models: `docs/lankadata-audit.md` and `docs/lanka-data-layer-audit.md`.

## Read first
- `AGENTS.md`
- The two existing audits (method, legend, structure)
- `docs/decisions/decision-log.md` (to assess fit) and `docs/vision/vision-and-strategy.md`

## Inputs (fill in)
```
TARGET:        name + URLs (site, repo, docs)
QUESTIONS:     what the lead wants to know (reuse? compete? partner?)
DEPTH:         quick (pages + metadata) | standard (+ public API calls) | deep (+ local build and tests)
```

## Task
1. Gather facts: owner, team, dates, licence (code and data), activity (commits, releases), funding if stated, products and URLs.
2. Test only **public, documented** interfaces, politely (a handful of requests). Record request, status and a trimmed response.
3. For repositories at `deep` depth: clone into an isolated scratch directory, install without global changes, run the tests, and build. Report real counts and timings.
4. Assess data quality where relevant: counts against official figures, hierarchy checks, sample values against sources.
5. Compare with our decisions: fit table (our decision → their approach → gap).
6. List reuse options (use, integrate, fork, borrow ideas, ignore, partner) with pros and cons, and give a recommendation labelled as a recommendation.
7. Write `docs/research/audits/{{target_slug}}-audit.md` with the ✅/🟡/❌ legend, summary, findings, implications, and "not verified".

## Constraints
- No scraping of undocumented or private endpoints. No authenticated areas. No load testing.
- Respect licences: don't copy restricted content into our repository.

## Verify (show real output)
Every ✅ claim must have the command, URL or file behind it in the report.

## Deliverables
The audit document; if useful, an entry in the opportunities register or a proposed decision-log entry.

## Done when
The lead can answer the QUESTIONS from the audit alone.

Report using the format in `AGENTS.md`.
