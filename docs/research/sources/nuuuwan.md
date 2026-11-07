# Source dossier: nuuuwan, `lk_census_2024`

Prompt R01 · checked 2026-11-07 · catalogue: `catalog/sources/nuuuwan.yaml`, `catalog/datasets/nuuuwan-lk-census-2024.yaml`

| Finding | Status | Evidence |
|---|---|---|
| Repository `nuuuwan/lk_census_2024`, MIT licence (repository), last push 2026-08-05 | ✅ | GitHub API |
| GN-level JSON per topic (e.g. `data/Person-Sex/gnd_data.json`: 14,008 records with `region_id` like `LK-1103005`, name and values) plus parsed final-report tables with the original PDF pages | ✅ | snapshot `raw/nuuuwan/nuuuwan-lk-census-2024/20261107T165224Z/Person-Sex_gnd_data.json`; repository tree |
| Its GN ids are DCS codes with an `LK-` prefix, a 1:1 relabelling of the DCS workbook's 14,008 units | ✅ | G02 (`inherit_matches` check passes) |
| The data originates from DCS, so the MIT licence covers the code, while the rights in the figures follow DCS | ❓ | inference; to confirm with the maintainer (introduction drafted) |

Use: cross-check of our own DCS extraction (D01), never as authority.
