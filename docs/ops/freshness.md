# Freshness monitor and release calendar (D05)

Status: **local, detection only** · 2026-11-18 · Decision: D-050 (Proposed)

## Run it

```bash
cd pipeline
uv run slf freshness                 # from catalogue schedules and held snapshots
uv run slf freshness --probe         # also HEAD each landing page (about 2 s per dataset)
```

It writes `data/build/freshness/calendar.json`; the website's `/data/calendar` page shows it (the web build copies it). With `--probe`, `signals.json` keeps each landing page's `ETag` and `Last-Modified`, and the next probe flags pages that changed.

## States

| State | Meaning |
|---|---|
| Not held yet | Catalogued, no raw snapshot |
| Held, no fixed schedule | Snapshot held; the catalogue schedule is `manual` or `on_release` |
| Current / Overdue | Daily, weekly or monthly datasets: the next copy is due one period after the last |

First run (2026-11-18, offline): 60 datasets; 41 held without a fixed schedule, 19 not held.

## Not done (needs the lead)

- A scheduled GitHub workflow that opens an issue per change (D05 step 2): outward-facing, and CI is manual-only to save cost.
- Community signals (nuuuwan, LDF) as an extra input (step 5).
- Schedules in the catalogue are mostly `manual`; filling in real publication rhythms (DCS, CBSL) would make "overdue" meaningful.
