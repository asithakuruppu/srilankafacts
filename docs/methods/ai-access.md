# Method: AI access, evaluation, embeds and SQL

Status: **local preview, 2026-11-18** · Decision: D-051 (Proposed) · Prompts: A01, A02

## MCP server (`mcp/`)

Read-only, stdio, over a release's `api/v1/` folder or the site's base URL (`SLF_API_ROOT`). Tools: `search_places`, `get_place_profile`, `list_indicators`, `get_indicator` (with `within` to restrict to an area and a total for counts), `compare_places`, `get_sources`. Each response includes the release, the citation and, per value, unit, period, verification, dataset, source locator and snapshot hash. Unknown ids, missing indicators and unpublished levels return `available: false` with a reason. Files are cached in memory; nothing about callers is stored.

Commands (in `mcp/`): `pnpm install`, `pnpm build`, `pnpm test` (in-memory client over the web fixture release), `node tests/e2e-stdio.mjs <release dir>` (stdio client; transcript in [mcp-transcript-2026-11-18.txt](../qa/mcp-transcript-2026-11-18.txt)).

## Evaluation set (A02)

`uv run slf evalset --release-dir <release>` writes 150 questions (seeded): 60 look-ups (district, DS and GN; population, households, housing units, people aged 60+), 30 comparisons, 22 sums of GN values for a DS division (only where the release adds up exactly), 15 definitions and 23 unanswerable questions (GDP, car ownership, income, 1950 figures, 2025 local elections). No questions rank ethnic or religious groups. `node eval/run.mjs <set> <release> <report>` answers each through the tools and scores correct and cited: [ai-eval-2026-11-18.md](../qa/ai-eval-2026-11-18.md), 150 of 150.

**What that does not show:** whether a language model picks the right tool, reads the answer correctly or keeps the citation. Testing assistants needs a manual protocol (date, model, interface) and must respect each service's terms; not done.

## Embeds

`/embed/map?ind=<indicator>&level=<province|district|ds|gn>` draws one census indicator with fifths of the values, a legend and a credit line (Sri Lanka Facts link, release, DCS source, non-commercial, private preview). Use it in an iframe.

## SQL in the browser

`/query` loads DuckDB-WASM 1.32.0 from this site and registers views `census`, `topics`, `elections` and `geographies` over the release's Parquet files. Queries run in the visitor's browser; the first one loads the engine (about 3 s on a laptop in headless Chromium). Results show the first 1,000 rows.
