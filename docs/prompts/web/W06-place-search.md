# W06: Trilingual place search

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 1 | Frontend / Search | 1 | 2026-11-07 | active |

## When to use
To let people find any place by name, in English now and in Sinhala and Tamil as names become available.

## Read first
- `AGENTS.md`
- `docs/architecture/data-model.md` §3.6 (names, alt_names)
- G02 crosswalk report (spelling variants found)

## Inputs (fill in)
```
RELEASE: version
```

## Task
1. Build a compact search index at release time: `name_en`, `name_si`, `name_ta`, `alt_names`, parent names, level and ID. Measure its size and lazy-load it on first focus.
2. Normalisation: case, diacritics, whitespace, common romanisation variants (for example oo/u, w/v, th/t, double letters), and Sinhala/Tamil Unicode normalisation.
3. Ranking: exact > prefix > fuzzy; higher levels first for ties; always show level and parent so duplicates are distinguishable (17 groups of GN share a name within the same parent ✅).
4. Keyboard-accessible combobox (ARIA pattern) in the shared header and in `/explore`.
5. Pagefind index for content pages (methods, stories).
6. Tests with tricky queries: spelling variants from G02, duplicate names, Sinhala and Tamil input where names exist, partial names.

## Constraints
- No external search service.

## Verify (show real output)
Index size; test query results table (query → top 3); accessibility check of the combobox.

## Deliverables
Index builder, search component, tests.

## Done when
Typing a reasonable spelling of any place name finds it within the first three results, with its parent shown.

Report using the format in `AGENTS.md`.
