# O02: Monitoring, costs and maintenance routine

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 1 | Operations | 1 | 2026-11-07 | active |

## When to use
At launch, then review quarterly.

## Read first
- `AGENTS.md`
- `docs/ops/runbook.md` (O01)
- `docs/roadmap/development-strategy.md` §6 (budget)

## Inputs (fill in)
```
ALERT_CHANNEL: email to the lead (address supplied by the lead, kept in CI secrets or monitoring settings, not in the repo)
BUDGET_LIMITS: monthly limits per service
```

## Task
1. Uptime checks for the site, API `latest.json`, a tile file and the MCP endpoint when it exists, using a free monitor.
2. Alerts for CI and release workflow failures, failed freshness checks and expiring domains.
3. Cost visibility: budget alerts in each provider (hosting, R2, AI); a monthly cost log template in `docs/ops/costs.md`.
4. A backup of releases to a second location (for example a second bucket or provider, or Zenodo for major releases), with a restore test.
5. A monthly maintenance checklist in `docs/ops/maintenance.md`: dependency updates, broken-link check, freshness issues triage, corrections-log review, cost review, a sample accuracy spot-check.
6. Optional, privacy-respecting error tracking for the web app. Only if it collects no personal data; document the configuration.

## Constraints
- No monitoring tool that adds third-party trackers to public pages.

## Verify (show real output)
A test alert received (the lead confirms); a restore test log; screenshots of budget alerts configured (by the lead, if credentials are needed).

## Deliverables
Monitoring configuration, cost log, backup job, maintenance checklist.

## Done when
The lead finds out about outages and cost spikes from alerts, not from users.

Report using the format in `AGENTS.md`.
