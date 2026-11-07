# C01: Methodology page for a dataset

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 1+ | Content / Methods | 1 | 2026-11-07 | active |

## When to use
For every dataset before it is published, and when its processing changes.

## Read first
- `AGENTS.md` (rule 7: AI-drafted text is labelled until the lead approves it)
- The dataset's catalogue entry, R02 rights memo, D01/D02 QA reports, crosswalk report

## Inputs (fill in)
```
DATASET_ID: e.g. census-2024-gnd-tables
AUDIENCE:   general reader first, technical appendix second
```

## Task
1. Write `docs/methods/{{dataset_id}}.md` (it also feeds the site's `/methods` page), with:
   - What the source is, who produces it, coverage, reference date and how often it updates
   - Definitions of key concepts in the source's own terms (cited)
   - What we did: snapshot, extraction method, geography matching (match rates, unmatched units), validation results, overrides applied (count and reasons)
   - Verification status: counts of values by `verification` level
   - Known limitations and how to interpret (for example boundary vintage, small populations)
   - Rights and attribution; how to cite
   - Change history for this page
2. Plain language first (short sentences, no jargon), then a technical appendix.
3. Every factual claim cites a source or a QA report. Mark the page `Status: AI draft, pending review`.

## Constraints
- Don't speculate about causes or policy. Describe the method and the data.

## Verify (show real output)
A list of claims with their citations; numbers checked against the QA reports (show the comparison).

## Deliverables
Methodology markdown, ready for the lead's edit.

## Done when
A sceptical researcher can understand exactly how a published value was produced.

Report using the format in `AGENTS.md`.
