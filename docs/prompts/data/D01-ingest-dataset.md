# D01: Ingest a tabular dataset (snapshot → harmonise → validate)

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 1+ | Data engineering | 2 | 2026-11-08 | active |

## When to use
To bring an Excel or CSV dataset into the pipeline. The default first use is the **DCS Census 2024 GN-level tables**. For PDF tables, use D02 for extraction, then this prompt for the rest.

**Actual scope held (checked 2026-11-08):** only **two** workbooks exist in `raw/`:
GN population by sex and age group, and occupied housing units by GN. The other ten
topic tables named in earlier drafts (ethnicity, religion, household structure, wall,
floor, roof, drinking water, cooking fuel, lighting, toilet facilities) were never
downloaded and must not be assumed to exist. Build only what is held; add a topic when
its snapshot and catalogue entry exist. Ethnicity and religion stay out of default
profiles under D-015 even when those tables arrive.

## Read first
- `AGENTS.md`
- `docs/architecture/architecture-overview.md` §3 (stages and rules)
- `docs/architecture/data-model.md` §4–§8 (indicators, observations, quality, validation)
- The dataset's `catalog/` entry, R01 dossier and R02 rights memo
- `catalog/geographies/codes/` (crosswalk from G02)
- An existing dataset module, to follow its pattern

## Inputs (fill in)
```
DATASET_ID:       e.g. census-2024-gnd-tables
SOURCE_URLS:      exact file URLs (from the landing page)
TABLES:           which files/sheets
INDICATORS:       indicators to produce (counts as components + derived shares)
PUBLISHED_TOTALS: where official totals are printed (e.g. "Final report Table 3.2, p.__")
CROSS_CHECK:      e.g. nuuuwan/lk_census_2024 (comparison only)
```

## Task
1. **Snapshot** each file (hash, URL, retrieved_at, headers).
2. **Extract** deterministically (openpyxl/pandas). Handle merged headers and footnotes explicitly. Keep the source's own unit codes and names. Record `source_locator` (file, sheet, row/column) per value.
3. **Harmonise:** map units through the crosswalk (`dcs_census2024` system). Unmatched units → QA report (never dropped). Create indicator YAMLs (definitions taken from the source's own wording, with a citation). Store components (counts); compute shares.
4. **Validate** with tests:
   - category counts sum to the stated totals within each unit
   - GN → DS → district → province → country sums equal published totals (0 tolerance for census counts, unless a documented source inconsistency)
   - national and district totals equal PUBLISHED_TOTALS (cite page and table)
   - coverage: every current GN present, or listed as missing with reason
   - ranges and duplicates
5. **Cross-check** against CROSS_CHECK: a diff report of values that differ. Investigate the top differences, then explain or fix our side. **Never adopt the upstream value as source.**
6. Set `data_nature: census_count`, `verification: machine_extracted` (spot-checking happens in Q01 or D02's sheet).
7. Write observations Parquet into the local build, plus `qa/{{dataset_id}}.md`.

## Constraints
- No manual edits to extracted data in code. Corrections go to `overrides/` with reason and evidence.
- If rights are `unclear`, you may build locally, but the dataset must be marked not publishable (the validator enforces this).

## Verify (show real output)
Test output; reconciliation table against published totals; unmatched-unit list; cross-check diff summary (count of differing values, top 10).

## Deliverables
Dataset module, indicator YAMLs, tests, QA report, catalogue updates.

## Done when
Every value can be traced to a file, sheet and cell, totals reconcile with the official publication, and nothing went missing silently.

Report using the format in `AGENTS.md`.
