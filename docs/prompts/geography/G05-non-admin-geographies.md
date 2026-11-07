# G05: Non-admin geographies and population denominators

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 2 | Geography | 1 | 2026-11-07 | draft (refresh with M03 at Stage 2) |

## When to use
To add one non-nesting geography scheme (local authorities, electoral districts and polling divisions, or MOH areas) and compute census denominators for it. Run once per scheme.

## Read first
- `AGENTS.md`
- `docs/architecture/data-model.md` §3.1–§3.4 (schemes, IDs, GN atoms, weights, aggregation rules)
- R01/R02 outputs for the boundary source of this scheme. **If rights are unclear, stop.**
- Crosswalk report (G02) and the census release (D01/D04)

## Inputs (fill in)
```
SCHEME:            la | electoral | health
BOUNDARY_SOURCE:   dataset id in catalog (with rights recorded)
MEMBERSHIP_LIST:   official list of GNs per unit, if available (dataset id), else "none"
PUBLISHED_TOTALS:  any official population totals per unit to compare against (dataset id), else "none"
```

## Task
1. Snapshot and inspect the boundaries (CRS, fields, counts). Compare counts with official counts (for example 341 local authorities, of which 339 were elected in 2025 🟡; 22 electoral districts; 160 polling divisions) and explain differences.
2. Assign IDs per D-004 (`LK-LA-…`, `LK-ED-…`, `LK-PD-…`, `LK-MOH-…`) and record authority codes in `catalog/geographies/codes/`.
3. Build `composed_of` relations to GN divisions:
   - from MEMBERSHIP_LIST if available (`method: official_list`), otherwise
   - by spatial overlay in EPSG:5235, with weights by building footprints if a licensed source is available and documented, else by area (`method: overlay_buildings` / `overlay_area`).
   - Flag GNs split across units, and units with weight sums that don't make sense.
4. Validate: each GN's weights across units of the scheme sum to about 1 (report deviations); every unit has at least one GN; the unit geometry against the union of its GNs (IoU report).
5. Compute denominators (population, households, and age groups if available) for each unit from Census 2024 GN data. Compare with PUBLISHED_TOTALS and explain differences.
6. Write relations CSV, release tables, a QA report and a short methods note `docs/methods/denominators-{{scheme}}.md`.

## Constraints
- Rates are recomputed from components. Never average rates.
- Label denominators from overlay methods as `modelled_estimate` where weights are not official.

## Verify (show real output)
Count comparison; weight-sum check results; IoU distribution; top 10 differences against published totals.

## Deliverables
Scheme in the spine, relations, denominators, QA report and methods note.

## Done when
Any per-capita indicator for this scheme can be computed with a documented denominator.

Report using the format in `AGENTS.md`.
