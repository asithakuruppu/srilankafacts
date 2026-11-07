# A01: MCP server over the static API

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 2 | AI / Developer experience | 1 | 2026-11-07 | draft (refresh with M03 at Stage 2) |

## When to use
Once the static API (W05) is live, to let AI assistants query Sri Lanka Facts and cite it (D-011, OPP-09).

## Read first
- `AGENTS.md`
- Decision D-011 (AI policy)
- `docs/architecture/architecture-overview.md` §5.5
- W05 OpenAPI document and JSON Schemas
- The current official Model Context Protocol specification and SDK documentation (check the version; don't rely on memory)

## Inputs (fill in)
```
RUNTIME:  TypeScript or Python official MCP SDK
HOSTING:  serverless platform consistent with current hosting
```

## Task
1. Design a small tool set with clear descriptions and input schemas: `search_places(query, level?)`, `get_place_profile(geography_id, indicators?)`, `list_indicators(topic?)`, `get_indicator(indicator_id, level, period?)`, `get_sources(dataset_id)`. Consider `resolve_point(lat, lon)` only if reverse geocoding exists.
2. Every tool response includes values **with** units, period, `data_nature`, `verification`, release, source and a ready-to-quote citation plus URL. Never return a bare number.
3. Implement against the static API only (no database). Cache responses. Rate-limit politely.
4. Write tool descriptions that steer models to cite sources and to say "not available" rather than guess.
5. Add `llms.txt` at the site root describing the API, the MCP endpoint, licences and citation rules.
6. Tests: unit tests per tool, plus an end-to-end test with an MCP client. Run the A02 evaluation set if it exists and report scores.
7. A docs page with setup instructions for common MCP clients.

## Constraints
- Read-only. No user data stored. Log only aggregate usage.

## Verify (show real output)
Test results; a transcript of an MCP client calling each tool (trimmed); evaluation scores if available.

## Deliverables
MCP server, `llms.txt`, docs page, tests.

## Done when
An assistant connected to the server answers sub-national questions with correct, cited numbers.

Report using the format in `AGENTS.md`.
