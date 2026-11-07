# R01: Investigate a data source and add it to the catalogue

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 0+ | Research | 1 | 2026-11-07 | active |

## When to use
Before any dataset from a new publisher or portal enters the pipeline. Not for auditing a whole competing platform (use R03).

## Read first
- `AGENTS.md`
- `docs/research/ecosystem-landscape.md` (§1, §3, §6 seed register)
- `docs/architecture/data-model.md` §2 (catalogue fields and rights rules)
- Existing `catalog/sources/` and `catalog/datasets/` files (avoid duplicates)

## Inputs (fill in)
```
SOURCE_NAME:    e.g. "Department of Census and Statistics"
START_URLS:     official pages to begin from
DATASETS_OF_INTEREST: e.g. "Census 2024 GN-level tables"
WHY:            what Sri Lanka Facts would use it for
```

## Task
1. Visit the official pages (no logins, respect robots.txt, a few requests only). Identify the datasets of interest and, briefly, any other relevant datasets.
2. For each dataset record: title, landing page, formats (Excel/CSV/PDF/API/web tool), geographic levels, periods covered, update frequency, last update seen, and access class (`download_table`, `pdf`, `api`, `web_query`, `on_request`, `licensed_microdata`).
3. Find the terms of use, copyright notice or licence statement for the site and each dataset. Copy the exact location (URL plus section). Quote at most a short phrase. **Don't interpret beyond the text.** Leave full rights analysis to R02.
4. Check whether community projects already extract it: search `github.com/nuuuwan`, `github.com/LDFLK`, `github.com/prabhavalabs/lanka-data-layer`. Note the repository, format, freshness and licence. Treat them as cross-checks only.
5. Note the contact route if published (office, email, phone from an official page). **Never guess an email address.**
6. Create or update `catalog/sources/{{source_id}}.yaml` and one `catalog/datasets/{{dataset_id}}.yaml` per dataset of interest, with `status: proposed`. Set `rights.status: unclear` unless explicit licence text exists.
7. Write `docs/research/sources/{{source_id}}.md`: a dossier with a findings table (✅/🟡/❌/❓), the URLs checked with HTTP status, and open questions.

## Constraints
- Reading pages only. No bulk downloading or scraping in this task (snapshots happen in D01).
- If a page fails to load, record it and move on. Don't retry in loops.
- Don't copy data from LankaData.net or LDF (licence terms).

## Verify (show real output)
- `slf catalog validate` (or the current validator) passes for the new files.
- A table of every URL checked with HTTP status and the date.

## Deliverables
Catalogue YAML files, dossier markdown, and a row added or updated in the seed register in `docs/research/ecosystem-landscape.md` §6.

## Done when
The lead can see from the dossier what exists, in what form, under what terms (or that terms are unknown), and who else already extracts it.

Report using the format in `AGENTS.md`.
