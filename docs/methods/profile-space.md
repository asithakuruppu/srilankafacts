# Method: the `profile` space (v0.2)

Status: **built locally, not published.** Recipe: [`catalog/spaces/profile.yaml`](../../catalog/spaces/profile.yaml)
v0.2 (D-025; axis-retention rule D-029, accepted 2026-11-12). QA:
[`docs/qa/profile-space-v0.2.md`](../qa/profile-space-v0.2.md). Code: `pipeline/slf/profile.py`,
run with `uv run slf profile build` in `pipeline/`.

Everything in this space is machine-computed from census values and has not been validated by a
person. A distance says two places have similar figures on these nine inputs. It is not a fact
about the places, and it never ranks places as better or worse (AGENTS rule 13).

## What goes in

Nine Census 2024 values per place, in two blocks:

- **Demography (6):** population (log), the shares aged 0–14, 15–59, 60–64 and 65+, and the sex
  ratio (log).
- **Housing (3):** occupied housing units (log), persons per housing unit (log) and population
  density (log).

Ethnicity and religion are excluded (D-015). Amenities and education/work are not held, so they
are not in the space.

A place gets a vector only when all nine inputs exist, its population is at least 100 (D-026)
and it has at least one female resident. Every other spine unit is listed with its reason in
`excluded_places.csv`: at GN level 76 have no census row and 33 have fewer than 100 people; at
DS level, Kalmunai `LK5221` has no census row (D-022) ✅.

## How the coordinates are made

1. Transform: logs for skewed counts and ratios; counts by age become shares.
2. Standardise each input to mean 0 and SD 1, separately at GN and DS level, so GN and DS
   distances are not on one scale and are never compared.
3. Clip at ±5 SD, and report how many values were clipped.
4. Give each block equal weight: scale its columns by 1/√(inputs in the block).
5. PCA by SVD. Keep an axis when its eigenvalue is above the average (total ÷ 9) and at least
   3 inputs load on it at |0.3| or more, up to 6 axes (D-029). This keeps 3 axes at each level ✅.

Places and indicators share one factorisation: a place's coordinates are its PCA scores, and an
indicator's coordinates are its loadings scaled by √eigenvalue.

## Reasons for similarity are exact

The squared distance between two places splits exactly into one part per axis and one part per
input. The input parts are each input's weighted standardised difference multiplied by the
difference projected back from the kept axes. They sum to the squared distance. Within a single
axis, a part can be negative when that input pulls the two places together. The QA check on
100 random pairs per level matches to within 6 × 10⁻¹⁵ ✅. "Most alike" lists the three inputs
with the smallest parts and "most different" the three with the largest.

## Outputs (`pipeline/data/build/profile/`)

| File | Content |
|---|---|
| `vectors/profile_v0.2.parquet` | One row per place and per indicator per level: `entity_type`, `entity_id`, `level`, `period`, `space_id`, `space_version`, `vector` (float32), `norm` |
| `vectors/profile_v0.2_axes.parquet` | Every computed axis: eigenvalue, variance explained, retained flag, loading per input, machine draft label |
| `vectors/similar_{gn,ds}_2024.json` | Top 20 similar places per place with distance and the three most alike and most different inputs |
| `vectors/unusual_{gn,ds}_2024.parquet` | Distance from the national centre, percentile and the inputs that contribute most |
| `vectors/contrasts_{gn,ds}_2024.parquet` | Every bordering pair's distance; flagged above the 95th percentile of bordering pairs |
| `sensitivity.json` | Neighbour-list overlap at K = 20 with one block removed, plus the stability checks (refit, axis count, small-count noise by population band) |
| `excluded_places.csv` | Spine units without a vector, with the reason |

## Known limits

- **The axes are stable; GN similar-places lists are not** ✅ (QA §4b).
  - Refitting the PCA on resampled places leaves 89% of a GN's top 20 unchanged (DS 93%), so
    the axes don't depend on which places are included.
  - Redrawing every count from a Poisson distribution, a model of ordinary small-number
    variation rather than census error, leaves 13% of a GN's top 20 unchanged (DS 84%).
  - Under that variation a typical GN moves 0.32 in the space. Its 20th-nearest neighbour is
    only 0.16 away, so the order of its neighbours is mostly noise. Its wider neighbourhood
    holds better: 47% of the redrawn list stays inside the original top 200.
  - Stability rises with size: GNs with 5,000+ people keep 61% (346 GNs); GNs with
    100–1,999 people keep 7–9%.
  - Removing a block (QA §4) changes what the space measures, so its low overlap is not a
    noise test.
  - D-031 (accepted 2026-11-12) sets what the website shows as a result: similar places for DS divisions only.
- **Size is counted twice.** Persons per housing unit is population ÷ housing units, so log
  housing units adds little beyond log population, and settlement size gets extra weight. D-029
  lists dropping housing units as a v0.3 option.
- **Axis labels are machine drafts.** They are built from the strongest loadings and need the
  lead's wording before any display.
- **In the release from `v2026.11.8-preview.1` (D-031).** `slf release --profile-dir data/build/profile` copies the vectors, axes, DS similar places and unusualness tables to `vectors/` and adds a `profile` block to each place's API file. DS pages list the 10 closest DS divisions with reasons. GN pages show axis positions and distance from the centre, and link to their DS division's list. GN similar-place lists are not published.
