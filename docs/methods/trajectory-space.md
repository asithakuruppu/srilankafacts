# Method: `trajectory` v0.1, how DS divisions changed between 2012 and 2024

Status: **built locally, private under D-038: never in a release or a public build** ·
2026-11-17 · Decision: D-047 (Proposed) · Code: `pipeline/slf/spaces.py` (`build_trajectory`) ·
Catalogue: `catalog/spaces/trajectory.yaml` · QA: [trajectory-v0.1.md](../qa/trajectory-v0.1.md)

## Axes

| Axis | Definition | Source |
|---|---|---|
| growth | annual population growth, 2012 → 2024, % | history build (G06) `ds_comparison_2012_2024.csv` |
| sex_ratio_change | males per 100 females in 2024 minus the same in 2012 | Census 2024 `sex_ratio`; DCS 2012 DS list (male, female) |

Only two axes exist because the held 2012 DS data gives population by sex and nothing else. Each
axis is standardised (mean 0, SD 1 across the units in the space). Distance is Euclidean; each
axis's share of a squared distance is exact.

## Which divisions are in it

A DS division enters only if it has **exactly one 2012 predecessor that is unchanged or
renamed**. The 2012 sex ratio of a split or boundary-adjusted division is not on the same
footprint, and nothing is imputed, so those divisions are listed as excluded with the reason. The
history build's `exact` / `approximate` flag is carried for every unit and shown beside every
neighbour.

## Rights

The 2012 DS list is a DCS document found only in a mirror (D-038, Accepted for local use). D-030
has not been extended to it. The space is written only to the local build and the local atlas
bundle, is labelled "private, local build" wherever it appears, and its QA report in this public
repository gives counts only, never values.
