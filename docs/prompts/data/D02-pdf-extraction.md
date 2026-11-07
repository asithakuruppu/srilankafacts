# D02: AI-assisted PDF table extraction with human verification

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 1+ | Data engineering / AI | 1 | 2026-11-07 | active |

## When to use
When the source table exists only in a PDF (census final-report tables, annual reports, health bulletins). The output then goes through D01's harmonise and validate steps.

## Read first
- `AGENTS.md` (rules 1, 7)
- `docs/architecture/architecture-overview.md` §3 (human-in-the-loop verification)
- `docs/architecture/technology-choices.md` §2.7 (deterministic first, LLM fallback)
- `docs/architecture/data-model.md` §6 (verification values)

## Inputs (fill in)
```
DATASET_ID:   catalog id
PDF_SNAPSHOT: snapshot id(s)
TABLES:       page numbers + table titles
TARGET_SCHEMA: columns expected (units, categories, totals)
KEY_VALUES:   which values must be human-verified (e.g. all totals, all district rows)
```

## Task
1. Try deterministic extraction first (pdfplumber, camelot, Docling). Record which method succeeded per table.
2. Where deterministic extraction fails or is unreliable, use an LLM with page images plus extracted text and a **strict structured-output schema** requiring cell-level `source_locator` (page, row label, column label). Record model ID, prompt and date in the extraction log.
3. Automatic checks: row and column totals, sums against stated totals, digit-count sanity, cross-check with any existing extraction (nuuuwan or LDF, comparison only).
4. Generate a **verification sheet** (static HTML plus CSV): for each KEY_VALUE, a cropped image of the PDF region beside the extracted value, with fields to mark `ok / corrected value / unreadable`. Order by risk (failed checks first).
5. Write an ingestion step that reads the lead's completed sheet. Corrections become `overrides/` rows (reason: "verification sheet {{date}}"); confirmed values become `human_verified`. Unreviewed values stay `machine_extracted`.
6. Measure: for a random sample the lead verified, report the error rate by extraction method. Estimate cost per page for LLM use.

## Constraints
- **Never mark values `human_verified` yourself.** Only the lead's completed sheet can.
- Don't send PDFs with personal data to external AI services. Census and statistical tables are fine; check anything else first.
- Keep LLM outputs and prompts in the extraction log for reproducibility.

## Verify (show real output)
Methods-per-table summary; automatic check results; the verification sheet file path; after ingestion, counts by verification status.

## Deliverables
Extraction module, extraction log, verification sheet, sheet-ingestion step, tests.

## Done when
The lead can verify the key values for a table in minutes, and the pipeline records exactly what was verified and how.

Report using the format in `AGENTS.md`.
