# Method: the `profile` space (v0.2)

Status: **built locally, not published.** Recipe: [`catalog/spaces/profile.yaml`](../../catalog/spaces/profile.yaml)
v0.2 (D-025; the axis-retention rule is the proposed D-029). QA:
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
| `sensitivity.json` | Neighbour-list overlap at K = 20 with one block removed |
| `excluded_places.csv` | Spine units without a vector, with the reason |

## Known limits

- **GN neighbour lists are not stable.** With either block removed, about 2% of a GN's top 20
  stays the same (DS: 27–38%) ✅. With 13,934 GNs packed into three axes, many places are almost
  equally close, so small changes reorder the list. Don't present GN similar places as robust
  until a further check, for example overlap under resampling or a larger K, supports it.
- **Size is counted twice.** Persons per housing unit is population ÷ housing units, so log
  housing units adds little beyond log population, and settlement size gets extra weight. D-029
  lists dropping housing units as a v0.3 option.
- **Axis labels are machine drafts.** They are built from the strongest loadings and need the
  lead's wording before any display.
- **Not wired into a release or the website.** That waits for the lead's decision on D-029.
