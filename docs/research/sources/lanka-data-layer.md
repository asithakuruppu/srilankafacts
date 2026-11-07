# Source dossier: Lanka Data Layer (Prabhava Labs)

Prompt R01 · checked 2026-11-07 · catalogue: `catalog/sources/lanka-data-layer.yaml`, `catalog/datasets/ldl-admin-npm.yaml`

| Finding | Status | Evidence |
|---|---|---|
| Repository `prabhavalabs/lanka-data-layer`, MIT licence, last push 2026-09-30 | ✅ | GitHub API |
| npm package `@lanka-data-layer/admin` 0.1.0 (MIT): 14,417 units keyed by COD-AB p-codes, data version 20260813.8; sources listed as "geoBoundaries + OCHA COD-AB Sri Lanka", "CC BY 3.0 IGO / CC BY-IGO" | ✅ | snapshot `raw/lanka-data-layer/ldl-admin-npm/20261107T165154Z/admin-0.1.0.tgz` |
| README source table: geoBoundaries (levels 0–2, CC BY 3.0 IGO), COD-AB (levels 3–4), OSM (ODbL), GeoNames (CC BY 4.0), Census 2024 licence "not stated", WorldPop (CC BY 4.0) | ✅ | README (HTTP 200) |
| Live API still parents Ampara `LK52` to Uva `LK8` | ✅ | `/v1/admin/LK52`, 2026-11-07 |
| DS and GN codes identical to COD-AB (339 / 14,043, 100 % exact) | ✅ | G02 report §3 |
| Access class: `download_table` (npm, repository), API | ✅ | — |

Use: cross-check only, never as authority, and its geometry is never used as a source (G01 constraint). Bug report drafted in `docs/outreach/`.
