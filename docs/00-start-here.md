# Start here

Sri Lanka Facts: *every place in Sri Lanka, every number about it, with its source.*

## Current status

| | |
|---|---|
| **Stage** | **Stage 1A: exit gate met (lead approvals 2026-11-12); Stage 1B public beta is next, non-commercial only (D-030), blocked mainly on hosting.** The 1A gate: every preview value traces to a file, sheet and cell (Q01 machine re-trace: 0 errors in 207 values); the release is reproducible (rebuilding changes 0 values); Q01 passes on a sample, provisionally (the lead approved the 20 sheet values "for now", [LA-002](decisions/lead-approvals-log.md)); the site is labelled "Private preview, not for publication". The current local build is `v2026.11.9-preview.1`: Census 2024 GN population by sex and age plus occupied housing units, with neighbour, parent, national and cluster context ([QA](qa/census-2024-gnd-tables.md), [dataset method](methods/census-2024.md), [spatial method](methods/spatial-context.md)); profile under D-031 ([method](methods/profile-space.md)); the corrections log with C-001 approved by the lead ([LA-001](decisions/lead-approvals-log.md)); and source comparisons under D-019 (24 of 470 comparisons differ, all unit counts; census totals agree). 41 DCS GNs remain unmatched and DCS 5224 Kalmunai has no spine equivalent; both are reported in QA. Stage 0 has not formally exited: name check and charter are still open. Outreach letters are sent and awaiting replies; the interim domain is `kuruppu.xyz`. Decisions D-001 to D-033 accepted. |
| **Team** | One product/research lead plus AI agents. Self-funded. No institutional relationships yet. |
| **Next actions** | **Lead (blocks 1B):** decide hosting (R2 and Vercel, still deferred); nothing can go public without it. Make Q01 a full pass for a public release: record which source pages or cells you checked for the 20 values, or re-check them ([sheet](qa/q01-lead-sheet-v2026.11.7-preview.1.csv)), and record it as a new LA entry. Review the DCS crosswalk queue, 42 items left ([analysis](research/geography/dcs-review-items-dating.md)); for 1B each unmatched GN is resolved or explicitly deferred. Choose the "report a problem" channel and confirm the performance budget ([Q02](qa/performance-2026-11-12.md)). **Lead (open, not blocking):** name check and charter (Stage 0 exit); name 5 places to judge the DS similar-place lists and write the axis labels (still open under [LA-003](decisions/lead-approvals-log.md)); a VoiceOver pass ([Q03](qa/accessibility-2026-11-12.md)); record the letters' send dates if known; a list of 20–30 soft-launch users and 8–10 customer-discovery conversations. **Agents:** households and GN amenities are ingested ([QA](qa/census-2024-households.md)); place pages will carry households and the 37 shares, counts in downloads only ([LA-004](decisions/lead-approvals-log.md)); not yet in a release (place files would grow about 3×, [method §5](methods/census-2024-households.md)); next under D-032, five-year age, sector and local authority type ([dossier](research/sources/dcs-census-2024-topic-tables.md)); ethnicity and religion last, at DS and district level only (D-033); test and merge Dependabot PRs 23 and 24. **Then:** once hosting exists, build the release without `--preview`; the website switches to the non-commercial banner. |
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
