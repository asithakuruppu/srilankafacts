# G07: Analytic grid and GN-to-hex weights

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 2 | Geography | 2 | 2026-11-07 | draft |

## When to use
Stage 2, before drawn or radius areas and grid-based layers. Builds the H3 fabric and the weights that let GN data move onto it, honestly labelled.

## Read first
- `AGENTS.md`
- `docs/architecture/spatial-first-analytics.md` §4, §7, §10
- `docs/decisions/decision-log.md` D-014
- G01 and G03 QA reports

## Inputs (fill in)
```
H3_RESOLUTIONS: 10, 8, 6        # 10 is the atom (D-017)
VINTAGE: 2024
WEIGHT_CANDIDATES: openbuildings_v3, overture_buildings, osm_buildings, worldpop_100m, ghsl_pop_100m
```

## Task
1. **Check rights** for each weight candidate (R02 pattern). Drop any with unclear rights from published outputs; they may still be compared internally if their terms allow.
2. **Check coverage:** confirm whether each candidate covers Sri Lanka at all (Open Buildings coverage is unconfirmed ❓).
3. **Measure completeness:** for each candidate, compare building counts (or modelled population) per GN with Census 2024 housing-unit or population counts. Report correlation, the share of GNs with implausible ratios, and maps of where each source is weak.
4. Recommend one primary weight source and a fallback, with evidence. **Stop for the lead's approval.**
5. Build H3 cells covering the land area at each resolution, and `spatial/gn_h3r10_weights_{vintage}.parquet` (coarser resolutions derived from it) (`geography_id`, `h3`, `weight`, `method`, `weight_source`). Weights per GN sum to 1 (test it).
6. **Population grid for 2024:** check whether WorldPop or GHSL publish a Sri Lanka grid built on 2024 census inputs (record the evidence). If not, produce a 2024-rescaled grid: each GN's cells scaled to its Census 2024 total, labelled `modelled_estimate` with `information_unit: gn-2024`. Compare with WorldPop's 2012-based grid and report where they differ most.
7. **Cell covers** for every footprint family (GN 2024, DS, LA, MOH, ED/PD): `spatial/cover_{family}_h3r10.parquet` (`footprint_ref`, `h3`, `fraction`), per [footprint-model.md](../../architecture/footprint-model.md) §2. Fractions per footprint sum to 1 (test it).
8. Library functions for the bridge methods in design §4.3 (`aggregate_sum`, `aggregate_recompute`, `apportion_weighted`, `point_in_polygon`, `zonal_stats`), each stamping `derived_by` and `data_nature`.

## Constraints
- Grid outputs are always `modelled_estimate` and never the default map of an official indicator.
- Prefer the Python `h3` package in the pipeline. If you use the DuckDB `h3` community extension, pin its version (DuckDB doesn't vet community extensions).
- Don't assume coverage or licence; record evidence.

## Verify (show real output)
- Round-trip test: GN counts → hex → back to GN reproduce the original totals exactly.
- Completeness table per candidate.
- Hex counts per resolution.

## Deliverables
Rights notes, completeness report (`docs/research/geography/building-completeness.md`), weights file, bridge functions with tests.

## Done when
Any GN-level count can be moved onto H3 and back with exact totals, using a weight source chosen on evidence.

Report using the format in `AGENTS.md`.
