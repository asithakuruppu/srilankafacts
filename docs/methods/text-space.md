# Method: `text` v0.1, place names for search

Status: **built locally; runs in every build of the site** · 2026-11-17 · Decision: D-047
(Proposed) · Code: `pipeline/slf/spaces.py` (`build_text_index`, `text_search`),
`web/src/lib/text-space.ts`, ranking in `web/src/lib/search.ts` · Catalogue:
`catalog/spaces/text.yaml` · QA: [text-v0.1.md](../qa/text-v0.1.md)

## Vectors

Every non-empty English, Sinhala and Tamil name of every place is one document. A name is folded
exactly as the search box already did (accents, punctuation and common romanisation variants for
Latin script; Sinhala and Tamil kept as written), padded with a space and cut into character 2-
and 3-grams. Each gram weighs count × idf, with idf = ln((N + 1)/(df + 1)) + 1 over all name
documents, and vectors are normalised to length 1. A query is scored by cosine similarity, and a
place takes the score of its best name. No language model and no download are involved; the
browser builds the index from the existing `search-index.json` on the first search.

Aliases are not included: the spine's `alt_names` is empty for every unit.

## Ranking

The earlier tiers stay: an exact name beats a prefix, which beats a word start, which beats a
substring. Within a tier, the cosine adds up to 100 points, so closer spellings come first. A
place that matches no substring still appears when its cosine is at least 0.45, so a misspelt
name ("Colmbo") finds its place.

## Same answers in the pipeline and the browser

The Python and TypeScript implementations are written to match, and a test compares them on a
misspelling of every name (the middle character dropped): 25,461 queries, same top 5 for all ✅.
