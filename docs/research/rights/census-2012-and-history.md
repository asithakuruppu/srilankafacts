# Rights memo: census-2012-tables, census-district-series, nuuuwan-lk-census-2012

Reviewed 2026-11-15 · Prompt R02 · Not legal advice.

## Evidence

| # | Source | Where | Finding |
|---|---|---|---|
| E1 | Statistical Abstract 2024, chapter 2 page | `https://www.statistics.gov.lk/abstract2024/chapter2` (2026-11-14), full page text searched for "copyright", "licence/license", "terms", "rights reserved", "©", "reproduc", "permission" | No match |
| E2 | Abstract Table 2.1 and 2.7 PDFs | snapshots `raw/dcs/census-district-series/…/abstract2024_table2.1.pdf`, `raw/dcs/census-2012-tables/…/abstract2024_table2.7.pdf`, all pages' text searched for "copyright", "reproduc", "permission", "©" | No match; each ends "Source - Department of Census and Statistics" |
| E3 | DCS-authored 2012 GN file (mirrored) | snapshot `raw/nuuuwan/…/population-gender_source.pdf`, first two and last pages | Title and data only; no notice |
| E4 | Census 2024 Final Report | existing memo [`census-2024-gnd-tables.md`](census-2024-gnd-tables.md) E4 | No copyright or reuse notice |
| E5 | DCS 2012 "Population Census 2012" page | `https://www.statistics.gov.lk/Population/StaticalInformation/CPH2011` (2026-11-14), page text searched as in E1 | No match |
| E6 | `nuuuwan/lk_census_2012` | GitHub API `license: MIT`; `LICENSE` file "Copyright (c) 2026 Nuwan I. Senaratna" | MIT covers the repository; the figures and the PDF are DCS's |
| E7 | Sri Lankan copyright in government works | not checked | ❓ for a lawyer (same gap as Census 2024) |

## Uses

| Use | Classification | Next step |
|---|---|---|
| Internal analysis (this G06 work) | Not addressed | Done privately; nothing published |
| Display on the website (DS comparisons, district series) | Not addressed | Needs a lead decision extending D-030 to these datasets (as D-032 did for the topic tables), or a DCS reply |
| Redistribute original PDFs (including the mirrored GN file) | Not addressed | Don't; link to DCS. For the GN file there is no DCS link to give (❌), so neither link nor redistribute |
| Redistribute derived tables (comparison table, district series) | Not addressed | As for display |
| Commercial use | Not addressed | Not allowed (`commercial_reuse: unknown`) |
| Modification | Not addressed | Official figures are never altered; transcription and reaggregation are labelled |
| Share-alike | Not addressed | — |
| Compatibility with CC BY 4.0 output | Unknown | Depends on DCS |
| Using nuuuwan's mirror as the carrier of a DCS document | MIT permits copying the repository; it says nothing about the DCS content | D-038 (Proposed); credit nuuuwan as the mirror |

Catalogue: all three datasets `rights: inherit` from their sources, which stay `status: unclear`,
`commercial_reuse: unknown`. None has a `publication` block, so the release builder refuses to
publish them.

## Attribution text (proposed, if the lead extends D-030)

"Source: Department of Census and Statistics, Sri Lanka: Census of Population and Housing 2012
(DS and GN population tables); Statistical Abstract 2024, Tables 2.1 and 2.7; Census of Population
and Housing 2024 Final Report, Tables 2.1–3.3. 2012 GN-level file obtained from a copy held in
github.com/nuuuwan/lk_census_2012."

## Questions for DCS

In the draft `docs/outreach/2026-11-15-dcs-census-history-queries.md` (not sent; AGENTS rule 9).
