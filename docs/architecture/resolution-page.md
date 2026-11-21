# Finest view (`/resolution`)

Purpose: show every dataset at the best resolution the platform holds, without implying more information than exists (D-017, D-018, D-053).

- **Manifest:** `pipeline/slf/atlas_resolution.py` reads `catalog/datasets/*.yaml` and writes `resolution.json` into the atlas bundle (`slf atlas export --catalog-dir`). Metres come only from `spatial.information_unit` (`grid-30m`) or a plain "<n> m"/"<n> km" in `spatial.resolution`; H3 uses the documented average edge length. Everything else is null ("not recorded"), never guessed.
- **Tiers:** `finer_than_gn` (a stated size, or point/line data), `gn`, `coarser_than_gn`, `national`, `unknown` (grid with no stated size).
- **Page:** table of all datasets, finest first, with filters; a district map with GN outlines, H3 r9 cells (badge: modelled from GN totals) and named features (local preview only).
- **Not built:** native 10 m / 30 m raster tiles. Needs a tile stack and a decision.
