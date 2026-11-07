# Q04: Security and privacy review

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 1+ | Quality / Security | 1 | 2026-11-07 | active |

## When to use
Before launch, before adding any server component, accounts or forms, and every six months.

## Read first
- `AGENTS.md` (rules 10–11)
- `docs/architecture/architecture-overview.md` §8
- `.github/workflows/`, hosting configuration, R2 configuration docs, `docs/ops/`

## Inputs (fill in)
```
SCOPE: static site + CDN + R2 + CI (Stage 1) | + API/accounts (Stage 3)
```

## Task
1. A threat model for the current scope: assets (releases, credentials, domain), threats (supply chain, credential leak, release tampering, defacement, abuse of embed routes), mitigations.
2. CI review: actions pinned by SHA; minimal `permissions`; secrets only in protected environments; no secrets in logs; release workflow requires manual approval; branch protection and required checks.
3. Dependencies: `pip-audit`, `pnpm audit`; Dependabot/Renovate active.
4. Web: security headers (CSP, HSTS, Referrer-Policy, frame-ancestors with an embed exception), CORS limited to API and tiles, no mixed content.
5. Storage: buckets private except via CDN paths; write keys scoped to CI; release immutability (object lock or a convention verified by tests).
6. Privacy: analytics without personal data or cookies; any forms (contact, newsletter) checked against the privacy policy and the PDPA (core provisions from 1 Jan 2027 🟡). Data-retention statement.
7. Write `qa/security-{{date}}.md`. Fix trivial issues; file the rest with severity.

## Constraints
- No intrusive testing of third-party services. Test our own assets only.

## Verify (show real output)
Header check output; audit outputs; workflow permission listing.

## Deliverables
Report, fixes and issues.

## Done when
No high-severity issues remain open for the launch scope.

Report using the format in `AGENTS.md`.
