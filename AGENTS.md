# AGENTS.md: standing rules for AI agents working on Sri Lanka Facts

Read this file completely before doing anything. It applies to every task. Task prompts live in `docs/prompts/`.

## What this project is

Sri Lanka Facts is a place-based data platform: *every place in Sri Lanka, every number about it, with its source.* Its core asset is a **geography spine** (all Sri Lankan geographies, stable IDs, history, crosswalks), with census and other indicators joined to it, published as a map-first website, downloads and an API. Trust is the product: every number must trace back to a source.

Conceptually the core is **vector-native**: every entity (place, indicator, place-period, feature) has coordinates in named, versioned vector spaces, from the country down to individual buildings, trees and landmarks, and relationships such as similarity and change are distances in those spaces. The exact, cited **ledger** stays the source of truth; vectors are derived from it (see `docs/architecture/vector-space-model.md`).

The project lead is a **product/research lead, not a day-to-day programmer**. Write your reports so they can review **evidence**, not code internals.

## Read before working

1. `docs/00-start-here.md`: map of the docs and current stage.
2. `docs/decisions/decision-log.md`: never contradict an `Accepted` decision. Treat `Proposed` decisions as the working direction unless the task says otherwise.
3. The documents your task prompt names (architecture, data model, etc.).
4. The existing code and data in the area you will touch. **Inspect before you change.**

## Golden rules

1. **Never fabricate.** No invented numbers, counts, sources, URLs, licences, API responses, test results, deployments or quotes. If you don't know, say so. If a step failed, say so and show the output.
2. **Provenance or it doesn't ship.** Every published value must resolve to dataset → snapshot (URL, retrieval time, sha256) → source, plus a source locator (page/table/cell).
3. **Raw snapshots are immutable.** Never edit or delete anything under `raw/` (local or object storage). Corrections go to `overrides/` with a reason and evidence.
4. **Rights before publishing.** Do not add a dataset to a release unless its `catalog/` entry records its rights. Do not use non-commercial or unclear-rights data in commercial work.
5. **Geography joins go through the crosswalk.** Never join on names alone or on codes from a different source without `catalog/geographies/codes/`. Never join across boundary vintages without a crosswalk.
6. **Never drop data silently.** Unmatched units, failed rows and suppressed values must appear in a QA report.
7. **Label what was not checked, and how fine the information really is.** Machine-extracted values stay `verification: machine_extracted` until a human verifies them. AI-generated text is labelled as such until a human edits and approves it. Gridded or apportioned values record and show their information floor (for example "100 m cells; population information from 2012 GN totals").
8. **Smallest change that does the job.** One task per branch and PR. Don't refactor unrelated code. Don't add services, frameworks or dependencies the architecture doesn't call for without proposing a decision-log entry first.
9. **No outward-facing actions.** Do not send emails, file RTI requests, post, publish releases to production, or contact anyone. Draft them for the lead.
10. **No secrets in Git.** Credentials only via environment or CI secrets. Never print secrets in logs or reports.
11. **Respect people's data.** Aggregates only. Never publish lists of named private individuals. Never attribute statistics about people to individual buildings or parcels, and never publish owner, claimant or occupant data on features. Collect no personal data without a documented need and a privacy review.
12. **Neutral tone.** Factual, sourced, no political judgement, especially for ethnicity, religion and elections.
13. **Distances are not facts.** Never infer an exact relation (hierarchy, adjacency, membership) from vectors. Every published distance, neighbour list or cluster records its `space_id` and `space_version` and can be explained from ledger values.

## Conventions

- **Languages:** Python for data (`pipeline/`), TypeScript for web (`web/`).
- **Python:** `uv`, `ruff`, `pyright`, `pytest`. **Web:** `pnpm`, TypeScript strict, ESLint/Biome, Vitest, Playwright.
- **Geography IDs:** OCHA p-codes for admin units (`LK`, `LK1`, `LK11`, `LK1103`, `LK1103005`); prefixed IDs for other schemes (`LK-LA-…`, `LK-ED-…`, `LK-PD-…`, `LK-MOH-…`); provisional `LK-ADM3-P0001` for units not in COD-AB. See `docs/architecture/data-model.md`.
- **Footprints:** every value has a `support_type`, a spatial footprint and a time footprint (`docs/architecture/footprint-model.md`). Combined results take the coarser footprint of their inputs, in space and in time.
- **Periods:** `2024`, `2024-Q3`, `2024-07`, `2024-W32`, `2024-07-15`, seasons `2024/25-maha`, `2025-yala`.
- **Formats:** Parquet/GeoParquet (canonical), CSV (human), GeoPackage (GIS), PMTiles (maps), JSON (web/API).
- **CRS:** publish in EPSG:4326; compute areas and distances in EPSG:5235 (SLD99 / Sri Lanka Grid 1999) unless the task specifies otherwise. Always confirm a source's CRS; never assume it.
- **Verification tags in reports and docs:** ✅ verified by you (ran it, read it) · 🟡 claimed by a source, not independently checked · ❌ not found / failed · ❓ assumption.

## Commands

Prerequisites: `uv` (Python 3.12 is fetched by uv), Node.js 20+ and pnpm 12 (`npm install -g pnpm@12`, or prefix commands with `npx -y pnpm@12.18.0`).

**Pipeline** (run in `pipeline/`):

| Task | Command |
|---|---|
| Install | `uv sync` (add `--extra s3` for R2 storage) |
| Lint and format check | `uv run ruff check . && uv run ruff format --check .` |
| Type check | `uv run pyright` |
| Tests | `uv run pytest` |
| Catalogue check | `uv run slf catalog validate --root ../catalog` |
| Run a dataset end to end (local) | `uv run slf build <dataset> --out-dir ./data/build` |
| Snapshot only / validate only | `uv run slf snapshot <dataset>` · `uv run slf validate <dataset>` |
| Release | `uv run slf release` (stub until D04) |

Storage: local `./data/` by default; `SLF_STORAGE=s3` with `SLF_S3_BUCKET`, `SLF_S3_ENDPOINT` and standard AWS credential variables for Cloudflare R2. Existing raw and release keys can never be overwritten.

**Web** (run in `web/`):

| Task | Command |
|---|---|
| Install | `pnpm install` |
| Dev server | `pnpm dev` |
| Lint | `pnpm lint` |
| Type check | `pnpm typecheck` |
| Unit tests | `pnpm test` |
| Build | `pnpm build` |
| Browser smoke test | `pnpm exec playwright install chromium` once, then `pnpm test:e2e` |

CI (`.github/workflows/ci.yml`) runs all of the above on every pull request.

## How to finish a task

End every task with a report in this shape (also used as the PR description):

```
## Summary
What changed and why, in 3–6 plain sentences.

## Evidence
- Commands run and their real output (trimmed, not paraphrased)
- Test results (counts of passed/failed)
- QA report location and headline numbers
- Screenshots for UI changes (desktop and mobile)

## Not verified / known gaps
Honest list. "None" only if true.

## Docs updated
Which docs, decision-log entries or catalogue files changed.

## Decisions needed from the lead
Questions only the lead can answer, each with your recommendation.
```

If a task cannot be completed as written, for example because the data doesn't exist, rights are unclear or a decision is missing, **stop and report**. Don't improvise around it.
