# S01: Dynamic API service (only when triggered)

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 3 | Backend | 1 | 2026-11-07 | draft (refresh with M03 when triggered) |

## When to use
Only after the trigger in `docs/architecture/architecture-overview.md` §6 has fired **and** a decision-log entry approves it: logged user requests the static API can't serve, or paying users needing keys and quotas.

## Read first
- `AGENTS.md`
- The approving decision-log entry; architecture §5.3 and §6; technology-choices §1
- Request logs or customer evidence that justified the trigger

## Inputs (fill in)
```
USE_CASES:  the specific queries users need (from evidence)
DB_HOST:    managed Postgres+PostGIS provider (decided)
AUTH:       API keys (default) | OAuth
```

## Task
1. Design endpoints for USE_CASES only: for example filters across units, point-in-polygon for any scheme, bulk lookups. Version under `/v2` and keep the static `/v1` working.
2. An idempotent loader that builds the database from a release (never edited by hand): schema, indexes (including spatial), a `release` column, and atomic switch-over between releases.
3. A FastAPI service: validation, pagination, consistent error envelope, citations in every response, OpenAPI.
4. API keys, quotas and rate limits. Usage logging with only key ID and endpoint (privacy).
5. Tests: unit, contract (OpenAPI) and load test at the expected traffic.
6. Deploy on a managed platform with health checks; update the runbook (O01) and monitoring (O02).
7. A cost estimate at expected and 10× traffic.

## Constraints
- The database is a cache of releases, not a source of truth (D-003). No writes except by the loader.

## Verify (show real output)
Test results; load-test summary; a loader run log with timings.

## Deliverables
Service, loader, docs, runbook updates, cost estimate.

## Done when
The use cases are served with citations, within budget, and the database can be rebuilt from any release.

Report using the format in `AGENTS.md`.
