# Start here

Sri Lanka Facts: *every place in Sri Lanka, every number about it, with its source.*

## Current status

| | |
|---|---|
| **Stage** | **Stage 1A: private preview built; Stage 1B unblocked on rights by D-030 (non-commercial only), with agent work still open.** Stage 0's agent deliverables are complete and the [retrospective](roadmap/retros/stage-0-2026-11-08.md) is written. Since then (lead, reported 2026-11-12): the outreach letters are sent and awaiting replies, the QGIS spot-check is done ("looks alright"), and the interim domain is `kuruppu.xyz`. Name check and charter are still open, so Stage 0 has not formally exited. Decisions D-001 to D-031 accepted. The Census 2024 preview covers GN population by sex and age plus occupied housing units, with neighbour, parent, national and cluster context ([QA](qa/census-2024-gnd-tables.md), [dataset method](methods/census-2024.md), [spatial method](methods/spatial-context.md)). The release builder now honours D-030: a public build is marked non-commercial and carries the DCS attribution and notice in every payload, page and download. The current local build `v2026.11.7-preview.1` (12 newly named GNs; v2026.11.6 corrected a Kandalama/Kiralessa swap) is still a private preview, because public hosting does not exist yet; it adds the 22 accepted GNs (41 DCS GNs remain unmatched). |
| **Team** | One product/research lead plus AI agents. Self-funded. No institutional relationships yet. |
| **Next actions** | **Lead:** confirm the 20 values in the Q01 sheet ([audit](qa/accuracy-audit-v2026.11.7-preview.1.md), [sheet](qa/q01-lead-sheet-v2026.11.7-preview.1.csv)); the machine re-trace found 0 errors in 207 values, but Q01 passes only with your check. record the letters' actual send dates if known; review the DCS crosswalk queue, 42 items left after the lead accepted 22 on 2026-11-12 ([analysis](research/geography/dcs-review-items-dating.md)); name check and charter; R2 and Vercel (deferred); user testing. **Lead:** name 5 places to judge the profile space's similar-place lists, and write the axis labels (v0.2 built locally under D-029: [method](methods/profile-space.md), [QA](qa/profile-space-v0.2.md)). **Agents:** profile is in preview `v2026.11.8-preview.1` under D-031 (DS similar places; GN axis position and unusualness, linking to the DS); D-028 done for the resolvable names: 12 promoted, 53 stay p-code labelled until an official GN list arrives ([null-name-gns](research/geography/null-name-gns.md)). **Then:** Stage 1B public beta, non-commercial, once hosting exists: build the release without `--preview` and the website switches to the non-commercial banner. |
| **Last updated** | 2026-11-12 |

## Reading order

**For you (the lead), about 60–90 minutes:**
1. [Vision and strategy](vision/vision-and-strategy.md): what to build, what to change from the brainstorm and why.
2. [Ecosystem landscape](research/ecosystem-landscape.md): who else is working on Sri Lankan data, and verified facts with sources.
3. [Development strategy](roadmap/development-strategy.md): stages, dependencies, budget, how to work with agents.
4. [Decision log](decisions/decision-log.md): confirm, change or reject each Proposed decision.
5. [Spatial-first analytics](architecture/spatial-first-analytics.md): how every number gets a *where*, a *compared to where* and a profile vector (D-013 to D-015).
6. [Vector-space model](architecture/vector-space-model.md): the conceptual core. Every entity is a point in named spaces; relationships are distances (D-016).
7. [Multi-scale features](architecture/multi-scale-features.md): zooming below GN to buildings, land, trees and landmarks; the two atoms (D-017).
8. [Footprint model](architecture/footprint-model.md): every value has a where, a when and a what (D-018).
9. [Live data, events and sources](architecture/live-events-and-sources.md): elections, live feeds, movement, news, conflicting sources, and the recommended order (D-019, D-020).
10. Skim: [architecture](architecture/architecture-overview.md), [business model](vision/organisation-and-business-model.md), [opportunities](ideas/opportunities-register.md).

**For AI agents:** [`AGENTS.md`](../AGENTS.md) → this file → [decision log](decisions/decision-log.md) → the docs your prompt names.

## Map of the documents

```
AGENTS.md                         Standing rules for every AI agent (CLAUDE.md imports it)
docs/
├── 00-start-here.md              This file: status, reading order, map
├── vision/
│   ├── vision-and-strategy.md    The recommended vision; challenges to the original direction
│   └── organisation-and-business-model.md   Revenue, licensing, governance, partnerships, legal checklist
├── research/
│   └── ecosystem-landscape.md    Sri Lankan data ecosystem, comparables, seed source register (with sources)
├── architecture/
│   ├── architecture-overview.md  Principles, system diagram, pipeline, serving, evolution, hosting, security
│   ├── data-model.md             Catalogue, geography spine, indicators, observations, quality, provenance
│   ├── spatial-first-analytics.md  Spatial contract, fabrics (GN atoms, H3), spatial context, drawn areas
│   ├── vector-space-model.md     Conceptual core: ledger + named vector spaces; relationships as distances
│   ├── live-events-and-sources.md  Elections, live feeds, movement, news/social, conflicting sources
│   ├── footprint-model.md        Every value: spatial footprint + time footprint + meaning; grid as index
│   ├── multi-scale-features.md   The ~100 m cell atom, information floors, and buildings, trees, landmarks below it
│   └── technology-choices.md     Comparisons, recommendations, reuse/integrate/build matrix
├── roadmap/
│   └── development-strategy.md   Stages, dependencies, agent workflow, budget, risks, first 30 days
├── decisions/
│   └── decision-log.md           All decisions (Accepted / Proposed / Superseded)
├── ideas/
│   └── opportunities-register.md Ideas log with value, effort and what to investigate
├── prompts/
│   ├── README.md                 How to use, index of prompts by stage
│   ├── _template.md              Template for new prompts
│   └── {research,foundation,geography,data,web,content,quality,ops,ai,services,meta}/
│
├── brainstorm-decisions.md       Input: earlier brainstorm (historical; superseded where the decision log says)
├── lanka-data-layer-audit.md     Input: audit of Lanka Data Layer (2026-11-07)
└── lankadata-audit.md            Input: audit of LankaData.net (2026-11-07)
```

**Folders now in use:** `docs/research/sources/`, `docs/research/rights/`, `docs/research/geography/`, `docs/methods/`, `docs/ops/`, `docs/outreach/`, `docs/qa/`, `docs/roadmap/retros/`. Still to create: `docs/design/` (W01) and `docs/research/user-research/` (R05).

## How these documents stay useful

- **Decisions live in one place.** The decision log overrides everything else, including the brainstorm. Other docs link to decision IDs instead of restating them.
- **Ideas wait in the register** until an evaluation (prompt M01) moves them into the roadmap.
- **Prompts evolve.** When one misleads an agent, fix it and bump its version. Refresh `draft` prompts when their stage arrives (M03).
- **Every stage ends with a retrospective** (M02) that updates estimates, this status table and the prompts.
- **Verification tags** are used everywhere: ✅ verified · 🟡 secondary source · ❌ not found · ❓ assumption. Keep using them; they are how future readers know what to trust.
