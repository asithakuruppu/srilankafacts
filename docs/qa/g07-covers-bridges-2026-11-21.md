# QA report: cell covers and bridge library (G07 steps 7 and 8), 2026-11-21

`slf grid covers` builds `cover_{family}_h3r10.parquet` (`footprint_ref`, `h3`, `fraction`) from the r10 cells of the population-weighted grid build (`docs/qa/g07-popweighted-grid-2026-11-21.md`). Cells are equal in area, so a whole GN's fraction per cell is 1 / (its cells); a unit's cover is the union of its member GNs' cells, renormalised to 1. Files stay local (`pipeline/data/build/grid-covers/`, not in Git, not in a release). Tags: ✅ computed in this run · ❌ not built.

## Covers ✅
| Family | Footprints | Rows | Max abs error of fraction sum vs 1 | Source of membership | Rights |
|---|---|---|---|---|---|
| `admin` (province, district, DS, GN) | 14,416 | 16,309,240 | 5.6e-16 | spine `parent_id` | public (COD-AB) |
| `electoral_ed` | 22 | 4,077,310 | 2.2e-16 | `catalog/geographies/relations/electoral_ec-2024.csv` (ED composed of districts, weight 1; secondary-source basis) | public |
| `la` (internal) | 335 | 3,993,372 | 4.4e-16 | nuuuwan gig-data via `la_relations_internal.csv` | unclear, D-046: file name ends `_internal`, never published |
| `moh` (internal) | 323 | 3,629,919 | 2.2e-16 | gig-data via `health_relations_internal.csv` | unclear, D-046: `_internal` |
| `pd` | ❌ | | | The PD to GN membership from gig-data is not persisted as a relation file, and there is no official list | not built |

- Admin units without a cover: 1 of 14,417, the provisional DS `LK-ADM3-P0001` (no spine GN has it as parent; its composition is in `catalog/geographies/relations/provisional.csv`, which this build does not read ❓). Not dropped silently: listed here.
- Member GNs without cells: 0 in every family. GNs not in the LA or MOH lists get no cover there (13,620 of 14,043 GNs are in the LA list, 13,057 in MOH); that gap is the composition's, see `docs/methods/denominators-la-moh.md`.
- One cell is shared: `8a6110260d17fff` is the label-point fallback cell of the tiny GN LK5104003 and also an ordinary cell of LK5104030. Covers of different footprints may overlap by design; a GN-keyed (`geography_id`, `h3`) join is exact, a join on `h3` alone double counts this cell (156.5 people). ✅ found by a round trip over the apportioned census: sums by unit match the GN sums exactly everywhere except the units that contain both GNs (LK51, LK5104, LK5) until the join is keyed by GN.
- Fractions are by area. A population-weighted cover would use the `weight` column of the popweights file instead; not built.

## Bridge library ✅
`pipeline/slf/bridges.py`: `aggregate_sum`, `aggregate_recompute`, `apportion_weighted`, `point_in_polygon`, `zonal_stats`. Each row carries `derived_by` and `data_nature`. Whole-GN sums keep the input's nature and are marked `exact`; split GNs and apportionment give `modelled_estimate`. A unit with a missing member GN returns `value: None` and lists the missing GN. Points outside every polygon return `geography_id: None`; points near an edge are flagged `on_border`; the boundary vintage is recorded. `network_distance` (listed in design §4.3 but not in G07's step 8) is not built.

## Tests and checks ✅
7 new tests in `tests/test_bridges.py` (exact sums, missing members, recomputed rates, apportion round trip to 1e-12, border flags, zonal stats, cover fractions including a split GN, ED expansion). `ruff`, `ruff format --check`, `pyright` clean.

## Not done
- PD cover; population-weighted covers; DS/LA/MOH covers on the web (nothing in the web or release changed).
