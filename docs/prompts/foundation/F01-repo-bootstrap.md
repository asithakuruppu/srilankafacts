# F01: Bootstrap the monorepo, tooling and CI

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 0 | Foundation | 1 | 2026-11-07 | active |

## When to use
Once, at the start of Stage 0, after the lead confirms D-003, D-005 and D-007 in the decision log. Re-run only parts of it if the structure needs repair.

## Read first
- `AGENTS.md`
- `docs/architecture/architecture-overview.md` §3–§4 (pipeline stages, repository layout)
- `docs/architecture/technology-choices.md` §1 (stack)
- `docs/decisions/decision-log.md` (check that D-003, D-005, D-007 are Accepted; if they are still Proposed, ask before proceeding)

## Inputs (fill in)
```
GITHUB_REPO:   e.g. github.com/<org>/srilankafacts (the lead creates it)
CODE_LICENCE:  Apache-2.0 (per D-005) or as decided
NODE_VERSION / PYTHON_VERSION: leave blank to use current stable LTS / stable
```

## Task
1. Create the layout from architecture §4: `catalog/{sources,datasets,indicators,geographies}/`, `overrides/`, `pipeline/`, `tiles/`, `web/`, `.github/workflows/`, each with a short README saying what belongs there.
2. **Pipeline:** a `uv`-managed Python package `slf` with a `typer` (or similar) CLI exposing `slf snapshot <dataset>`, `slf build [<dataset>]`, `slf validate [<dataset>]`, `slf release`, `slf catalog validate` (stubs where not yet implemented, failing clearly). Add a `datasets/example_dataset.py` showing the five-stage interface (snapshot, extract, harmonise, validate, publish) on a tiny fixture, with tests. Configure ruff, pyright and pytest.
3. **Storage abstraction:** a small module that reads and writes `raw/` and `releases/` either to a local directory (default, `./data/`) or to S3-compatible storage (Cloudflare R2) via environment variables. Raw writes are append-only: refuse to overwrite an existing key.
4. **Web:** a Next.js app (App Router, TypeScript strict, pnpm) with a placeholder home page, ESLint/Biome, Vitest, and a Playwright smoke test. No map yet.
5. **CI** (GitHub Actions): Python lint, type check and test; web lint, test and build; catalogue validation (stub until F02). Pin actions by commit SHA. Minimal `permissions:`. Dependabot or Renovate config.
6. `.gitignore` (`data/`, `.env*`, build outputs), `.editorconfig`, `LICENSE` (CODE_LICENCE), `CONTRIBUTING.md` (short; points to AGENTS.md).
7. Fill the **Commands** section of `AGENTS.md` with the real commands you created.
8. Add a "Pinned versions" section to `docs/architecture/technology-choices.md` listing the versions you installed (from lockfiles, not memory).
9. Write `docs/ops/accounts-setup.md`: a checklist for the lead to create accounts and secrets (GitHub org, Cloudflare R2 buckets `slf-raw` and `slf-releases`, hosting project) **without** the agent handling credentials.

## Constraints
- No database, no Docker requirement for local development, no extra services (D-003).
- Don't create cloud resources or handle credentials. Document what the lead must do.
- Keep the example dataset trivial. Real datasets come in G01 and D01.

## Verify (show real output)
- `tree -L 2` (or equivalent) of the repository.
- Each CI command run locally with output: lint, type check, tests (counts), web build.
- A deliberately failing raw overwrite, showing the refusal.

## Deliverables
A PR with the scaffold, filled AGENTS.md commands, pinned versions and the accounts checklist.

## Done when
A fresh clone can run `uv sync`, `pnpm install`, all tests and the web build with the documented commands, and CI is green.

Report using the format in `AGENTS.md`.
