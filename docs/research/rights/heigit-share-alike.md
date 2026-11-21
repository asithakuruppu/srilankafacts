# Rights memo: HeiGIT datasets (CC BY-SA) and what a release owes

Reviewed 2026-11-21 · Not legal advice · The lead confirms before any public release that includes these values.

## Evidence
| # | Source | Where |
|---|---|---|
| E1 | HDX record, accessibility | `https://data.humdata.org/dataset/sri-lanka-accessibility-indicators`, licence field "Creative Commons Attribution Share-Alike (CC BY-SA)" (read 2026-11-17, catalogue `sources/heigit.yaml`) |
| E2 | HDX record, risk indicators | `https://data.humdata.org/dataset/sri-lanka---risk-assessment-indicators`, licence field "Creative Commons Attribution Share-Alike (CC BY-SA)"; description names WorldPop, OpenStreetMap, Google Earth Engine, GHSL, JRC, Mapillary and Planet as inputs (API read 2026-11-21) |

❓ Neither record states a licence **version** (3.0 or 4.0). The release statement therefore says "CC BY-SA" and "the source's record states no version".

## Uses
| Use | Classification | Conditions |
|---|---|---|
| Display in the atlas and download | Permitted with conditions | Attribution "HeiGIT; © OpenStreetMap contributors" |
| Commercial use | Permitted (catalogue `commercial_reuse: yes`) | Same conditions |
| Adapted values (joined, recomputed, derived indicators) | Permitted with conditions | **Share-alike**: the adapted values are offered under the same licence |
| Upstream inputs | 🟡 claimed by HeiGIT, not checked | OSM is ODbL; WorldPop, GHSL and JRC terms are not recorded in our catalogue |

## What a release owes (built into the release builder)
1. `NOTICE.md` and the README carry a **Share-alike terms** section for every dataset whose recorded licence is share-alike (`share_alike_datasets` in `pipeline/slf/release.py`): licence as recorded, attribution, source, and the share-alike obligation.
2. The values stay in their own files (`observations/<dataset>.parquet` and `.csv`), so the licence of other datasets is not changed. They are not blended into a combined table without a notice.
3. The attribution string from the source entry is shown wherever values appear (atlas panel, API payload, download).
4. The public atlas bundle leaves these indicators out (`--public`), so nothing is published until a release carries the statement and the lead has confirmed it.

## Open points for the lead
- Confirm the statement wording, and whether to ask HeiGIT (communications address on their HDX page) which licence version applies.
- The Rural Access Index from `heigit-risk-indicators` is already in the current preview bundle (`slf subnational build`). It is CC BY-SA. Recommendation: keep the preview non-commercial as is, and add the same share-alike statement to the next release before the public site shows it.
- Upstream inputs (WorldPop, GHSL, JRC, Mapillary, Planet) need their own rights lines in the catalogue before a public release; not done here.
