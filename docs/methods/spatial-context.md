# Method: spatial context and local clusters (D06)

Status: **implemented in the private preview** · 2026-11-08 · Prompt D06 ·
Code: `pipeline/slf/enrich.py` · Outputs: `stats/` and `qa/spatial-context.md` in each release.

This note describes how every published value gets its neighbour, parent, national and
cluster context. It does not change any published value: raw census values stay exactly as
the dataset build wrote them. The spatial-context tables are a separate, derived layer.

Verification: ✅ parameters and outputs were read from the code and the release files;
🟡 the choice of method is cited to the architecture and decision log, not independently
benchmarked; ✅ the small-denominator threshold was confirmed by the lead on 2026-11-08
(D-026).

## 1. What is computed

For every indicator and every level with a contiguity graph (GN, DS, district), one row per
unit in `stats/local_<indicator>_<level>.parquet`:

| Column | Meaning |
|---|---|
| `value` | Published value from the ledger, unchanged |
| `value_status` | `normal`, `not_available`, … as published |
| `neighbour_count` | Number of graph neighbours (before dropping units with no value) |
| `neighbour_value_count` | Neighbours that have a value for this indicator |
| `neighbour_median`, `neighbour_min`, `neighbour_max`, `neighbour_mean` | Summary over those neighbours |
| `spatial_lag` | Mean of neighbour values (the local Moran lag) |
| `parent_id`, `parent_value` | Parent unit and its value at the next coarser level |
| `national_value` | Country value for the same indicator |
| `rank`, `rank_total` | Rank by value, descending (1 = highest), among units with a value |
| `local_moran_i`, `p_value`, `q_value`, `class` | Local Moran's I and its class |
| `denominator` | Rate denominator where the indicator is a rate |
| `small_denominator`, `small_denominator_basis` | Small-number flag and the column it uses |
| `smoothed_value`, `smoothed_method`, `smoothed_data_nature` | Empirical Bayes estimate, labelled `modelled_estimate` |

A national summary is written to `stats/spatial_summary.json`; the human-readable QA tables
are in `qa/spatial-context.md`.

## 2. The neighbour graph

Neighbours come from the geography spine (`spatial/adjacency_<level>_cod-ab-v03.parquet`),
built by G01, not from this stage:

- **Rook contiguity** on COD-AB v03 boundaries in EPSG:5235. Two units are border
  neighbours when their boundaries come within **1 m** and share at least **10 m** of
  border. Shorter contacts, such as corner touches, do not count.
- A unit with no border neighbour gets its **3 nearest units** as `distance_band`
  neighbours, so it is never silently isolated in the statistics.
- The graph is made symmetric before use.

The provisional DS `LK-ADM3-P0001` is not in the COD-AB adjacency file, so it has no
neighbours. Its spatial context is `no_neighbours`, not an invented list. This is a known
gap, recorded in the QA report.

## 3. Local Moran's I

Local Moran's I measures whether a unit's value is similar to, or different from, its
neighbours, relative to the whole field:

1. Values are taken for units with a value at that level. Units with no value are
   `no_data`.
2. Units whose remaining neighbours all lack a value are dropped iteratively, then marked
   `no_neighbours`. Fewer than three connected units, or a constant field, yields
   `not_significant` for all (no variance to test).
3. The neighbour weights are row-standardised.
4. `esda.moran.Moran_Local` runs **999 conditional permutations** with seed
   **20241108** and `alternative="directed"`. The directed alternative is the one-sided
   test for positive spatial association at each unit (the cluster and outlier quadrants),
   not a two-sided "any association" test.
5. P-values are adjusted across all units of that indicator and level with
   **Benjamini–Hochberg** at **q ≤ 0.05**.
6. A unit gets a class only when `q ≤ 0.05`; otherwise it is `not_significant`. Classes:
   `high_high`, `low_low`, `high_low`, `low_high`.

The class is a **spatial-association label, not a causal finding**. For count indicators,
clusters partly reflect where people live, not a process. A `high_low` or `low_high` unit is
a spatial outlier to check, not an error and not a story by itself.

## 4. Small denominators and empirical Bayes

A rate on a small base is noisy. The release flags and smooths, but **never replaces** the
published value.

| Indicator | Model | Denominator | Small-denominator flag when |
|---|---|---|---|
| `population_age_0_14_share` | Beta-binomial | Total population | Total population < 100 |
| `population_age_60_plus_share` | Beta-binomial | Total population | Total population < 100 |
| `sex_ratio` | Beta-binomial on males ÷ (males + females), converted back to per 100 females | Females | Females < 100 |
| `persons_per_occupied_housing_unit` | Gamma–Poisson | Occupied housing units | Occupied housing units < 100 |
| `population_density` | Gamma–Poisson | Area (km²) | Total population < 100 |

Counts (population and age groups, occupied housing units) are not rates, so they get no
denominator, no small-number flag and no smoothing. `population_density` is smoothed with
area as exposure but flagged on population, because a density on a handful of people is
not meaningful even when the area is large.

Prior parameters use the method of moments over all units at that level, so the estimate is
deterministic. A smoothed value is `modelled_estimate`; it must never be shown as a census
count or used in a total.

## 5. Thresholds and their status

| Parameter | Value | Status |
|---|---|---|
| Small-denominator threshold | **100** | ✅ confirmed by the lead 2026-11-08 (D-026) |
| Permutations | 999 | ✅ fixed in code |
| Seed | 20241108 | ✅ fixed in code |
| FDR q | 0.05 | ✅ fixed in code |
| Neighbour minimum shared border | 10 m (spine G01) | ✅ fixed in code |
| Distance-band neighbours for isolated units | 3 nearest | ✅ fixed in code |

The small-denominator threshold is a project judgement, not a DCS rule, now confirmed at
100 (D-026). Changing it changes flags and smoothed values but not published values. It is
recorded in `stats/spatial_summary.json` so a future run can be compared like for like.

## 6. What the preview shows

At GN level, with 14,043 units and 98 with no data:

| Indicator | HH | LL | HL | LH | Not significant |
|---|---|---|---|---|---|
| Population total | 420 | 755 | 13 | 7 | 12,750 |
| Population aged 0–14 share | 852 | 887 | 24 | 50 | 12,127 |
| Population density | 611 | 3,005 | 1 | 13 | 10,315 |
| Sex ratio | 0 | 0 | 0 | 0 | 13,939 |
| Persons per occupied unit | 0 | 0 | 0 | 0 | 13,940 |

Sex ratio and persons per occupied unit show no significant local clusters at GN level.
That is a result, not a missing step: after FDR control, their local variation is not
spatially organised at this scale. The counts and the child share do cluster.

## 7. Limits

1. **Machine output only.** No human has checked the cluster maps or the outlier list
   against local knowledge. Classes are `machine_extracted`.
2. **Rook only, one vintage.** Adjacency is from COD-AB v03. Boundary changes or a new
   vintage need a new graph and a crosswalk.
3. **One scale at a time.** GN clusters do not aggregate into DS clusters; each level is
   computed separately.
4. **No correction for multiple indicators.** FDR is applied within each indicator-level
   table, not across all 42 tables.
5. **Islands.** The provisional DS `LK-ADM3-P0001` has no graph neighbours; 98 GN units
   have no value. Both appear as such, never as zero or as "not significant".
6. **Counts are not population-normalised.** Population clusters partly reflect settlement
   size; use the share indicators for age structure.
7. **No confidence interval on the smoothed values.** They are a point estimate for
   context, stored separately from the published values.
