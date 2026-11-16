# Source dossier: nuuuwan, `lk_census_2024`

Prompt R01 · checked 2026-11-07 · catalogue: `catalog/sources/nuuuwan.yaml`, `catalog/datasets/nuuuwan-lk-census-2024.yaml`

| Finding | Status | Evidence |
|---|---|---|
| Repository `nuuuwan/lk_census_2024`, MIT licence (repository), last push 2026-08-05 | ✅ | GitHub API |
| GN-level JSON per topic (e.g. `data/Person-Sex/gnd_data.json`: 14,008 records with `region_id` like `LK-1103005`, name and values) plus parsed final-report tables with the original PDF pages | ✅ | snapshot `raw/nuuuwan/nuuuwan-lk-census-2024/20261107T165224Z/Person-Sex_gnd_data.json`; repository tree |
| Its GN ids are DCS codes with an `LK-` prefix, a 1:1 relabelling of the DCS workbook's 14,008 units | ✅ | G02 (`inherit_matches` check passes) |
| The data originates from DCS, so the MIT licence covers the code, while the rights in the figures follow DCS | ❓ | inference; to confirm with the maintainer (introduction drafted) |

Use: cross-check of our own DCS extraction (D01), never as authority.

## `lk_census_2012` (checked 2026-11-14, G06)

| Finding | Status | Evidence |
|---|---|---|
| Repository `nuuuwan/lk_census_2012`, MIT, created 2026-03-26, last push 2026-06-13; pinned commit `8d8af05` | ✅ | GitHub API |
| Per topic: `source.pdf` (a DCS-authored PDF, e.g. "Population by GN division and sex 2012", created 2015-05-06), `raw_data.json`, `data.json`, `validation.json` | ✅ | snapshot `raw/nuuuwan/nuuuwan-lk-census-2012/20261114T194914Z/population-gender_source.pdf`, `…/20261114T194916Z/population-gender_data.json` |
| `data.json` region ids (`LK-1103005` style) are given by matching names to a later GN list, not printed by DCS; `validation.json` lists the 9 DS divisions created after 2012 as missing | ✅ | read |
| The DCS original of `source.pdf` is not on any DCS address we found | ❌ | [DCS 2012 dossier](dcs-census-2012-and-history.md) |

Use: the `source.pdf` is used as a copy of a DCS document under D-038 (Proposed); our own parse
replaces nuuuwan's. `data.json` is a cross-check only (D-008).
