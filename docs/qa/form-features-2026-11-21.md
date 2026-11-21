# QA: per-feature `form-feature` and `context-feature` v0.1 (private preview)

Run: `uv run slf spatial featurespace`, 2026-11-21. Full output and per-input table: `data/build/form-features/qa.md` and `summary.json` (gitignored). All numbers below are from that run ✅.

## 1. What was built

- 8,886,949 footprints, one vector each, with `gn_id` (853 are outside every GN polygon, kept with an empty id).
- `form-feature`: 4 axes, 98.9% of variance, 0 excluded.
- `context-feature`: 5 axes, 86.6% of variance, 8,838,171 in the space; **48,778 excluded** (no CTrees biomass pixel at the point; reported, not filled).
- Fitted on a seeded 400,000 sample, all footprints projected. Output 878 MB Parquet (private).

## 2. Checks

| Check | `form-feature` | `context-feature` |
|---|---:|---:|
| Largest decomposition error, 300 pairs | 2.04e-08 | 3.67e-08 |
| 5 nearest in space, mean ground distance (2,000 features) | 123.4 km | 84.6 km |
| 5 random, mean ground distance | 131.7 km | 129.3 km |
| Nearest neighbours in the same GN | 0.4% | 10.0% |

Reading: `form-feature` neighbours are similar buildings anywhere in the country (no geographic coherence, as expected for shape and size). `context-feature` neighbours are somewhat more local but mostly not in the same GN, so the space groups settings (for example dense, low, near-coast) across the island.

Axes (top loadings): `form-feature` axis 1 compactness against size; axis 2 height. `context-feature` axis 1 elevation against neighbour density; axis 2 and 3 biomass; axis 4 remoteness from the nearest footprint, school and health site; axis 5 road distance. Labels are machine drafts.

## 3. Rules

- Rule 11: rows hold physical attributes and a GN id only; nothing about people. Not published.
- Rule 13: distances carry `space_id` and `space_version` (`0.1`) and decompose into named inputs.
- Rights: ODbL share-alike material (Overture Buildings, OSM); kept internal.

## 4. Not checked

- No sampled neighbour pairs were inspected by a person ❓; axis labels are drafts.
- Canopy height per building is not an input (too heavy to sample).
- Height is a 100 m cell value; OSM road distance uses vertices every 30 m, so it can overstate the distance by up to about 15 m.
- Giga school and healthsites.io rights for any release were not re-read here ❓.
