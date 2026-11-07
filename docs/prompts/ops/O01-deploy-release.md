# O01: Deployment, release workflow and rollback

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 1 | Operations | 1 | 2026-11-07 | active |

## When to use
Before the first public deployment. Revisit when the hosting setup changes.

## Read first
- `AGENTS.md`
- `docs/architecture/architecture-overview.md` §6–§8
- `docs/ops/accounts-setup.md` (F01). The lead must have created accounts and secrets first.

## Inputs (fill in)
```
HOSTING:  Vercel Pro (default) | Cloudflare
DOMAINS:  site domain, data/tiles domain
```

## Task
1. **Web deploys:** preview deployment per PR; production deploy from `main` after required checks pass.
2. **Data release workflow** (GitHub Actions, `workflow_dispatch`): build release → validate → Q01 summary present → upload to R2 under `releases/{version}/` → smoke tests against the uploaded files → **manual approval** (protected environment) → update the `latest` pointer → trigger web revalidation or rebuild.
3. **Tiles** uploaded under versioned paths. Old versions kept.
4. **Rollback:** one documented command or workflow to point `latest` at the previous release and redeploy the previous web build. Test it.
5. **Cache headers:** immutable for versioned paths; short for `latest` and HTML.
6. DNS and domain configuration notes (Cloudflare).
7. Write `docs/ops/runbook.md`: how to release, roll back, rotate keys, and what to do if a wrong number is found (corrections-log entry plus a new release).

## Constraints
- The agent never holds production credentials outside CI. All production actions happen through workflows that need the lead's approval.

## Verify (show real output)
A full dry run on a staging bucket or path: workflow logs; a rollback test log; cache-header checks.

## Deliverables
Workflows, runbook, configuration docs.

## Done when
The lead can publish or roll back a release from the GitHub UI by following the runbook.

Report using the format in `AGENTS.md`.
