# R02: Reuse-rights investigation for a dataset

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 0+ | Research | 1 | 2026-11-07 | active |

## When to use
Before a dataset is published in a release, used in commercial work, or redistributed as a download. Required for the Census Atlas 2024 inputs (DCS Census 2024, COD-AB, NSDI, OSM/Protomaps).

## Read first
- `AGENTS.md`
- The dataset's `catalog/` entry and its R01 dossier
- `docs/architecture/data-model.md` §2.3 (rights rules)
- `docs/vision/organisation-and-business-model.md` §5 (licensing strategy)

## Inputs (fill in)
```
DATASET_IDS:   e.g. census-2024-gnd-tables, cod-ab-lka
INTENDED_USES: e.g. display on site; CC BY download of derived tables; commercial sampling frames
```

## Task
1. Collect every relevant terms source: site terms, dataset-level licence fields, copyright notices inside publications (check the first and last pages of PDFs), portal-wide licences, data-sharing policies, and any statute the terms refer to. Record URL, section and retrieval date for each.
2. For each intended use, classify it as: *explicitly permitted* / *permitted with conditions (list them)* / *not addressed* / *prohibited*. Cover display, redistribution of the original, redistribution of derived tables, commercial use, modification and share-alike obligations.
3. Check compatibility with our output licences: CC BY 4.0 for derived work, ODbL for OSM derivatives. Explain conflicts (for example CC BY-NC inputs cannot feed CC BY or commercial outputs).
4. Draft the exact attribution text the source requires or that we should use.
5. Write specific questions for the publisher where rights are unclear (these feed R04).
6. Update the catalogue `rights` block: `status`, `licence`, `commercial_reuse`, `attribution`, `evidence[]`, `last_reviewed`.
7. Write `docs/research/rights/{{dataset_id}}.md` with a summary table, evidence and questions.

## Constraints
- This is **not legal advice**. Flag anything material for the lead to take to a Sri Lankan lawyer.
- Never set `status: open` or `commercial_reuse: yes` without explicit text supporting it. Absence of terms means `unclear`.
- Quote at most short phrases (under 15 words each).

## Verify (show real output)
- Catalogue validation passes.
- Every rights claim in the report has a URL and section.

## Deliverables
Updated catalogue entries, rights memo, and a list of publisher questions.

## Done when
For each intended use the lead can see a yes/no/unclear answer with evidence, and the next step for each unclear one.

Report using the format in `AGENTS.md`.
