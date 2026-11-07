# D05: Freshness monitor and release calendar

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 3 | Data engineering / Ops | 1 | 2026-11-07 | draft (refresh with M03 at Stage 3) |

## When to use
When enough datasets are active that missing a new publication becomes likely.

## Read first
- `AGENTS.md`
- `catalog/datasets/` (schedules, landing pages)
- `docs/ideas/opportunities-register.md` OPP-20

## Inputs (fill in)
```
DATASETS: all active | list
CHANNEL:  GitHub issues (default)
```

## Task
1. For each active dataset, define a cheap change signal: landing-page link list hash, `ETag`/`Last-Modified` on known files, or presence of the next expected file name.
2. A scheduled GitHub Actions workflow that checks signals politely (low frequency, identifying user agent with the project URL, no personal email), and opens or updates a GitHub issue per detected change.
3. Compute "expected next release" from the catalogue schedule and past snapshots, and flag overdue datasets.
4. Generate a public release-calendar JSON and page data (expected vs actual).
5. Note where community scrapers (nuuuwan, LDF) already detect releases, and consider subscribing to their outputs as an extra signal.
6. Document in `docs/ops/freshness.md`.

## Constraints
- No heavy crawling. Respect robots.txt and rate limits. Detection only; snapshots run through D01.

## Verify (show real output)
A dry run listing each dataset's signal and current state; a test issue created in a fork or test repository.

## Deliverables
Workflow, calendar data, docs.

## Done when
A new DCS or CBSL publication relevant to an active dataset creates an issue within a week.

Report using the format in `AGENTS.md`.
