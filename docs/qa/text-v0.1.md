# QA: `text` v0.1 (search)

Built 2026-11-17 from the release `v2026.11.17-preview.3` `admin.json` · method:
[text-space.md](../methods/text-space.md)

| Item | Count |
|---|---|
| Places | 14,418 |
| Name documents (English, Sinhala, Tamil) | 29,152 |
| Distinct 2- and 3-grams | 16,630 |
| Aliases | 0 (none held) |

## Browser vs pipeline

A misspelling of every distinct name (middle character dropped): 25,461 queries. The browser's
top 5 equal the pipeline's for all of them ✅ (`web/tests/unit/spaces.test.ts`, local builds).

## Does a misspelt name find its place?

Place found in the top 5 for the misspelling of its own name:

| Script | Found | Names | Share |
|---|---|---|---|
| English | 13,799 | 14,365 | 96.1% |
| Sinhala | 13,839 | 14,360 | 96.4% |
| Tamil | 374 | 374 | 100% |

2,956 places share their folded English name with another place, which limits any name-only
search. The exact English name puts its own place first for 12,519 of 14,365.

## Search box

`Colmbo` now returns Colombo first ✅ (e2e). Exact and prefix matches still outrank fuzzy ones ✅
(unit test). The ranking before this change was not measured on the same queries, so no
before/after figure is claimed.
