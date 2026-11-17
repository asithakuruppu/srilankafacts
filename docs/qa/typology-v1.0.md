# QA: `typology` v1.0 (DS divisions)

Built 2026-11-17 with `uv run slf profile spaces --release-dir data/build/releases-preview/v2026.11.17-preview.3`
from the profile build v0.3 (339 DS divisions, 5 axes) · method: [typology.md](../methods/typology.md)

## Rebuild check

DS profile rebuilt from the census vs the stored profile vectors: largest difference 1.18 × 10⁻⁷
(float32 storage) ✅.

## Choice of k (50 bootstrap resamples per k)

| k | silhouette | stability (mean ARI) | qualifies (ARI ≥ 0.75) |
|---|---|---|---|
| 3 | 0.284 | 0.679 | no |
| 4 | 0.328 | 0.598 | no |
| **5** | **0.269** | **0.823** | **yes (chosen)** |
| 6 | 0.281 | 0.743 | no |
| 7 | 0.247 | 0.725 | no |
| 8 | 0.256 | 0.714 | no |
| 9 | 0.241 | 0.636 | no |
| 10 | 0.241 | 0.641 | no |

k = 4 has a higher silhouette but is unstable (ARI 0.60); k = 5 is the only stable choice.

## Types (draft names, machine-generated, awaiting review)

| Type | DS divisions | Mean agreement | Draft name |
|---|---|---|---|
| 1 | 140 | 0.88 | Higher share aged 60-64 and share aged 65+; lower share aged 15-59 |
| 2 | 87 | 0.89 | Higher sex ratio (log) and share Buddhist (religion); lower population density (log) and persons per housing unit (log) |
| 3 | 42 | 0.73 | Higher persons per housing unit (log) and share Islam (religion); lower share Sinhalese (ethnic group) and share Buddhist (religion) |
| 4 | 35 | 0.82 | Higher population (log) and occupied housing units (log); lower share aged 0-14 |
| 5 | 35 | 0.85 | Higher share Sri Lanka Tamil (ethnic group) and share Hindu (religion); lower share Sinhalese (ethnic group) and share Buddhist (religion) |

Sizes sum to 339 ✅. Type 3 is the least stable (0.73): its members trade places with types 2 and
5 across resamples.

## Browser vs pipeline

The browser reads the pipeline's assignments; it computes nothing for the typology. The
explorer's legend and colours were checked on the built site ✅.

## Not checked

No person has judged whether the five groups are meaningful, or reviewed the names.
