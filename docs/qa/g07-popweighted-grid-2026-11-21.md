# QA report: population-weighted grid (G07), 2026-11-21

Built by `slf grid popweights` from the held WorldPop R2025A 100 m constrained grid (sha256 `4c781514ba619dc07b4b5bbe8b60aae93f4d0d338441dd9a1a7327fdf62f3144`), COD-AB v03 GN geometry and the census GN totals of release v2026.11.19. Outputs stay local in `pipeline/data/build/grid-popweighted/` (not in Git, not in any release). Tags: ✅ computed in this run · 🟡 claimed by a source · ❓ assumption.

## Method ✅
- Cells are the existing grid's: each H3 cell belongs to the GN containing its centre (`slf.grid.gn_cells`), at r10 (4,077,310 cells) and r9 (729,561 GN-cell rows, summed from r10 children).
- Each WorldPop pixel with a positive value goes to the r10 cell that holds its centre. A cell's raw weight is the sum of its pixels; within a GN the weights are normalised to 1 (`worldpop_pixel_mass_by_cell_centre`). A GN with no pixel mass gets equal shares (`equal_share_no_pixel_mass`).
- GN census totals (`population_total`, 2024) are multiplied by the weights (`apportion_weighted`). Every row records `weight_source`, `method`, `information_floor` and `data_nature = modelled_estimate`.
- Information floor, as written in every row: "100 m WorldPop cells; the population information inside a GN division is WorldPop's modelled pattern, the GN total is the 2024 census figure". WorldPop's own census input for Sri Lanka in R2025A is not confirmed ❓, so the within-GN pattern is a modelled one of unknown vintage; the census total fixes the GN level only.

## Sum checks ✅
| Check | r10 | r9 |
|---|---|---|
| GN divisions in the grid | 14,043 | 14,043 |
| Max abs error of weights per GN against 1 | 3.3e-16 | 4.4e-16 |
| GN with a census total and cells | 13,967 | 13,967 |
| Census total over those GN | 21,710,113 | 21,710,113 |
| Sum of apportioned cell values | 21,710,113 | 21,710,113 |
| Max abs residual for one GN (people) | 3.6e-12 | 3.6e-12 |
| GN with residual above 1e-6 | 0 | 0 |
| Census totals without cells | 0 | 0 |
| GN in the grid with no 2024 census total | 76 | 76 |

The residual is floating-point rounding only. The 76 GN with cells but no census total (for example LK1321190, LK2209125, LK2224100 to LK2224155, LK4130000, LK5104002) get weights but no apportioned values; they are not counted as zero.

## Cells with no weight ✅
- r10: 2,181,909 of 4,077,310 cells (53.5%) hold no WorldPop pixel mass; r9: 281,365 of 729,561 (38.6%). An r10 cell (about 0.015 km²) is about as large as a 100 m pixel, so many have no pixel centre with population, and unpopulated land has zero in WorldPop. People are therefore placed only on populated cells; this is intended, not a loss.
- WorldPop mass: 23,162,794 in the raster; 23,114,730 lands in cells of a GN; 48,064 (0.21%) fall in cells owned by no GN (coast and polygon edges) and are not apportioned.
- GN with no pixel mass at all (equal-share fallback, 13): LK2209130, LK4112120, LK4112180, LK4112185, LK4112190, LK4112195, LK4112200, LK4112220, LK4415015, LK4415155, LK4512020, LK5109012, LK5110025. Eight of them have a census total above zero (39 to 1,162 people) and are spread evenly over all their cells.

## Completeness of the weight source against the census ✅ (not a quality verdict)
WorldPop 2025 pixel sum inside a GN's cells over the census 2024 total, 13,962 GN: median ratio 1.053; 28.2% within 10%; 12.3% differ by more than 50%. Different years and methods; this is a comparison, not an error rate. It does not matter for totals (they are exact by construction) but shows where the within-GN pattern is least anchored. Maps of weak areas and the Kontur, Overture and OSM comparisons were not made: those inputs are excluded on rights (see `docs/research/rights/g07-weighting-inputs.md`).

## Rights ✅
See `docs/research/rights/g07-weighting-inputs.md`. Weight files use WorldPop (CC BY 4.0) and COD-AB (CC BY-IGO) only and are commercial-capable with attribution. Apportioned counts use the DCS totals (unclear, D-030) and carry `NONCOMMERCIAL` in the file name.

## Not done
- Round trip to other footprint families (cell covers for DS, LA, MOH, ED/PD, G07 step 7) and a 2024-rescaled grid comparison with WorldPop's own census input (step 6 evidence on WorldPop's input year).
- Web: the `/area` page and the point resolver still use the r9 equal-share grid (D-048) and are unchanged; the live release is unchanged.
