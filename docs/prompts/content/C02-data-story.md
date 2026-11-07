# C02: Data story / explainer

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 1+ | Content / Analysis | 1 | 2026-11-07 | active |

## When to use
To draft a short explainer built on released data (for example "How Sri Lankans cook, GN by GN" or "Where Sri Lanka is ageing fastest").

## Read first
- `AGENTS.md` (rules 1, 7, 12)
- The relevant indicator pages, methods pages and release
- `docs/vision/vision-and-strategy.md` §3 (explain, don't advocate)

## Inputs (fill in)
```
QUESTION:   the reader's question this answers
INDICATORS: ids
RELEASE:    version
LENGTH:     600–1000 words
```

## Task
1. Analyse reproducibly: a script or notebook in `analysis/stories/{{slug}}/`, reading the release Parquet, that outputs every number used.
2. Find what the data actually shows: patterns, exceptions and caveats. Separate observation from interpretation; interpretation only when it is supported by a cited source.
3. Draft `content/stories/{{slug}}.md`: headline, standfirst, 3–5 sections, specs for 2–4 charts or maps (which component, data, annotation), and a "How we did this" box.
4. Every number links to its release, indicator and place. Add a numbers checklist (each figure → script output line) for the lead to verify.
5. Sensitive topics: neutral wording, no ranking of ethnic or religious groups, context from official sources.
6. Mark `Status: AI draft, pending review`.

## Constraints
- No causal claims without strong cited evidence. No political commentary.

## Verify (show real output)
Script output with all figures; the numbers checklist.

## Deliverables
Analysis script, story draft, chart specs, checklist.

## Done when
The lead can edit and publish with every number already traceable.

Report using the format in `AGENTS.md`.
