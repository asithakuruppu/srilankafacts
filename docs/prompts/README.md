# Prompt collection

Reusable, project-specific prompts for AI coding agents and research assistants working on Sri Lanka Facts. They are written for the architecture and roadmap in this repository, not generic software work.

## How to use a prompt

1. Pick the prompt for your task from the index below. Check its **stage** and **prerequisites**.
2. Open a fresh agent session at the repository root, so the agent reads `AGENTS.md` automatically (Claude Code reads `CLAUDE.md`, which imports it).
3. Paste: `Read docs/prompts/<folder>/<file>.md and carry it out with these inputs:` followed by the filled-in **Inputs** block. Or paste the whole prompt with the `{{PLACEHOLDERS}}` filled.
4. The agent works on a branch and finishes with the report format in `AGENTS.md`.
5. For anything non-trivial, run **Q05** (PR review) in a *separate* session before you approve.
6. After use, note in the prompt's header if it needed changes, and bump its version when you edit it.

**Rule of thumb:** one prompt = one PR = one thing you can verify.

## Index

| ID | Prompt | Stage | Needs first |
|---|---|---|---|
| **Research** | | | |
| [R01](research/R01-source-dossier.md) | Investigate a source and add it to the catalogue | 0+ | F02 (or draft YAML by hand) |
| [R02](research/R02-reuse-rights.md) | Reuse-rights investigation for a dataset | 0+ | R01 |
| [R03](research/R03-project-audit.md) | Audit an external project or platform | any | — |
| [R04](research/R04-outreach-draft.md) | Draft an outreach letter, email or RTI request (never send) | 0+ | R01/R02 for context |
| [R05](research/R05-user-discovery.md) | Plan and synthesise user and customer interviews | 1+ | — |
| **Foundation** | | | |
| [F01](foundation/F01-repo-bootstrap.md) | Bootstrap the monorepo, tooling and CI | 0 | Decisions D-003, D-005, D-007 |
| [F02](foundation/F02-catalogue-schemas.md) | Catalogue schemas, validator and seed entries | 0 | F01 |
| **Geography** | | | |
| [G01](geography/G01-geography-spine.md) | Geography spine v0 (admin levels 0–4 from COD-AB) | 0 | F02 |
| [G02](geography/G02-crosswalk.md) | Cross-source code crosswalk (DCS, NSDI, OCHA, LDL, nuuuwan) | 0 | G01 |
| [G03](geography/G03-geometry-qa.md) | Geometry QA report and QGIS review pack | 0 | G01 |
| [G04](geography/G04-boundary-tiles.md) | Boundary PMTiles and Sri Lanka basemap extract | 1 | G01, G03, W01 tokens |
| [G05](geography/G05-non-admin-geographies.md) | Non-admin geographies (LA, ED/PD, MOH) and denominators | 2 | G02, D01, R02 for boundaries |
| [G06](geography/G06-boundary-vintages.md) | Boundary vintages and 2012↔2024 comparability | 2 | G02, D01 |
| [G07](geography/G07-analytic-grid.md) | Analytic grid (H3) and GN-to-hex weights | 2 | G01, G03, R02 |
| [G08](geography/G08-feature-layer.md) | Feature layer v1: buildings, landmarks, land cover | 2 | G07, legal checks |
| **Data** | | | |
| [D01](data/D01-ingest-dataset.md) | Ingest a tabular dataset (snapshot → validate), default Census 2024 | 1+ | G02, F02 |
| [D02](data/D02-pdf-extraction.md) | AI-assisted PDF table extraction with human verification | 1+ | D01 pattern |
| [D03](data/D03-reconcile-figures.md) | Reconcile conflicting figures | any | — |
| [D04](data/D04-release-build.md) | Build a versioned release | 1+ | D01 |
| [D05](data/D05-freshness-monitor.md) | Freshness monitor and release calendar | 3 | catalogue with schedules |
| [D06](data/D06-spatial-context.md) | Spatial context: neighbours, clusters, outliers, small numbers | 1 | D01, G01 (adjacency) |
| **Web** | | | |
| [W01](web/W01-design-system.md) | Design system, motion, colour scales, performance budget (spike) | 0–1 | sample data |
| [W02](web/W02-map-shell.md) | Persistent map shell and explorer | 1 | G04, W01 |
| [W03](web/W03-place-pages.md) | Place pages | 1 | D04, W02 |
| [W04](web/W04-indicator-pages.md) | Indicator pages and charts | 1 | D04, W01 |
| [W05](web/W05-downloads-static-api.md) | Downloads and static API | 1 | D04 |
| [W06](web/W06-place-search.md) | Trilingual place search | 1 | G02 |
| [W07](web/W07-sinhala-tamil-ui.md) | Sinhala and Tamil interface | 3 | W03, W04 |
| [W08](web/W08-two-map-explorer.md) | Two-map explorer: geography beside similarity | 2 | A03, W02 |
| **Content** | | | |
| [C01](content/C01-methodology-page.md) | Methodology page for a dataset | 1+ | D01 |
| [C02](content/C02-data-story.md) | Data story / explainer | 1+ | D04 |
| **Quality** | | | |
| [Q01](quality/Q01-accuracy-audit.md) | Accuracy audit of published values | every release | D04, W03 |
| [Q02](quality/Q02-performance-audit.md) | Performance audit (low-end mobile) | 1+ | W02, W03 |
| [Q03](quality/Q03-accessibility-audit.md) | Accessibility audit | 1+ | W03 |
| [Q04](quality/Q04-security-review.md) | Security and privacy review | 1+ | O01 |
| [Q05](quality/Q05-pr-review.md) | Review another agent's PR (for the lead) | any | an open PR |
| **Operations** | | | |
| [O01](ops/O01-deploy-release.md) | Deployment, release workflow and rollback | 1 | F01, D04 |
| [O02](ops/O02-monitoring-costs.md) | Monitoring, costs and maintenance routine | 1 | O01 |
| **AI** | | | |
| [A01](ai/A01-mcp-server.md) | MCP server over the static API | 2 | W05 |
| [A02](ai/A02-ai-eval-set.md) | Public AI evaluation set | 2 | D04 |
| [A03](ai/A03-place-vectors.md) | Profile vector space (places + indicators), "places like this", typology | 1 (typology 2) | D01, G01 |
| **Services** | | | |
| [S01](services/S01-dynamic-api.md) | Dynamic API service (only when triggered) | 3 | decision-log entry |
| [S02](services/S02-commissioned-analysis.md) | Commissioned analysis for a client | 1+ | rights checked |
| **Meta** | | | |
| [M01](meta/M01-evaluate-idea.md) | Evaluate an idea from the opportunities register | any | — |
| [M02](meta/M02-stage-retro.md) | Stage retrospective and docs refresh | end of each stage | — |
| [M03](meta/M03-new-prompt.md) | Write a new prompt for this collection | any | — |

## Conventions

- **IDs:** a letter for the workstream plus a number. Don't renumber; retire instead (mark `Status: retired` in the header).
- **Placeholders:** `{{UPPER_SNAKE}}`. Each prompt's *Inputs* block lists them.
- **Header table:** stage, workstream, version, last revised, status (`active` / `draft` / `retired`).
- **Later-stage prompts** (Stage 2+) are marked `draft`. Refresh them with M03 when their stage arrives, because the code will have evolved.
- Prompts reference standing rules in `AGENTS.md` instead of repeating them.

## Adding or changing prompts

Use **M03**. Base new prompts on the real repository state, not on this index alone. Add a row to the index. When a prompt turns out wrong in use, fix it straight away and bump its version. Prompts drift out of date unless you maintain them.
