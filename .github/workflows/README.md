# .github/workflows/

GitHub Actions. `ci.yml` is manual only (`workflow_dispatch`): it does not run on push or pull request, to avoid Actions cost. When run, it covers pipeline lint, type check, tests and catalogue check; web lint, type check, unit tests, build and a browser smoke test. Run the same checks locally before merging (commands in `AGENTS.md`). Actions are pinned by commit SHA with the version in a comment; Dependabot proposes updates monthly.

Scheduled data jobs and release workflows arrive with later prompts (D04, O01).
