# Method: building form, canopy, biomass and the `form` and `context` spaces

Status: **private build, 2026-11-21** · Decision: D-056 (Accepted) · Builds on D-016, D-017, D-044, D-045, D-049 · QA: [form-context-2026-11-21.md](../qa/form-context-2026-11-21.md) · Roll-up method: [landscape.md](landscape.md)

Legend: ✅ verified directly · 🟡 from a secondary source · ❌ not found · ❓ assumption.

## 1. What was missing and what is held

The review queue listed building shapes, canopy, biomass and the `form` and `context` spaces as blocked by "data held only as counts or not processed". Checked against the archive drive on 2026-11-21:

| Item | Held | State before | State now |
|---|---|---|---|
| Overture Buildings 2026-10-21.0 (8,886,949 footprints, ODbL) | ✅ one parquet | counts, total and mean footprint per GN | adds size classes, mean compactness, density, coverage |
| GHS-BUILT-H R2023A ANBH 2018, 100 m | ✅ 4 tiles | not processed | rolled up (area with a height, mean height) |
| Meta/WRI canopy height v2 | ✅ 75 tiles | already rolled up (D-044 build, 2026-11-18) | unchanged; used by `context` |
| CTrees above-ground biomass 2025, 100 m | ✅ 1 GeoTIFF | not processed (units unread) | rolled up |
| `form`, `context` spaces | n/a | not built | v0.1 built for GN and DS (proposed) |

Not available, so **not built**: per-feature `form` and `context` (the feature-level spaces of vector-space-model.md §4): no per-building vectors are built or published (rule 11, D-044); roads and coast layers are not held, so "distance to road and coast" is missing from `context`; Overture carries a height for only 4,338 of 8.9 M footprints, so footprint height is not used; no belowground biomass or uncertainty layer is held for CTrees.

## 2. New roll-ups (same machinery as landscape.md)

**Building footprints.** Each footprint goes to the GN containing its inside point (unchanged). Shape is measured after projecting to EPSG:5235: perimeter, and the Polsby-Popper compactness 4πA/P² (1 for a circle, 0.785 for a square). New additive components per GN: footprints under 20 m² and of 250 m² or more (cuts chosen here, not from a standard), compactness sum and number shaped. Published per place: `buildings_small`, `buildings_large`, their shares, `building_compactness_mean`, and two ratios on the ESA WorldCover mapped land area: `buildings_per_km2` and `building_coverage_share`. Higher levels sum components and recompute, so a district is exactly what its GN divisions give.

**GHSL building height.** ANBH is the modelled average net height of a 100 m cell in metres (0 where none, −1 no data). Each cell is split into 25 sub-cells of 20 m and shared by sub-cell centre, as for GHS-BUILT-S, with the Mollweide ground-area correction. A place's mean counts cells with a height above zero, weighted by ground area; the weight (`building_height_area`) is published too. Cells hold a modelled height for scattered homesteads as well as towns (16,356 km² of cells have a height, against about 977 km² of built-up surface), so the area is "cells with any built form", not built area.

**CTrees biomass.** Pixels are int16, megagrams per hectare ×10, −9999 no data (✅ read from the dataset's HDX record, 🟡 not checked against CTrees' own documentation). The mean is the area-weighted mean over the measured area, including non-forest land; the stock is mean × area, in megagrams of dry matter, not carbon. The file is clipped to the country boundary, so coastal GN divisions lose area (QA §2).

**Canopy height** was already rolled up; `context` reads its mean and the share of the place at 15 m or taller.

All new values are `modelled_estimate`, `machine_extracted`. Building values are `crowd_mapped` counts of mapped features, as in D-044.

## 3. The spaces

Both are built as `profile` and `landscape` are: standardise at each level (GN, DS), winsorise at ±5, weight blocks equally, PCA by SVD (`slf.profile.fit`), keep the fewest axes explaining 85% of variance (at most 6). A distance decomposes exactly into the named inputs, which are ledger indicators ([form.yaml](../../catalog/spaces/form.yaml), [context.yaml](../../catalog/spaces/context.yaml)).

| Space | Blocks (inputs) | Ledger sources |
|---|---|---|
| `form` | intensity: density, coverage, height. character: mean footprint, large share, small share, compactness | Overture Buildings (ODbL), GHS-BUILT-H |
| `context` | vegetation: canopy height, tall canopy share, biomass. land and services: cropland, grassland, water, listed places per km² | Meta/WRI, CTrees, ESA WorldCover, Overture Places |

A first grouping with one-input blocks (height, compactness, services) let those single inputs carry up to a third of the variance each and dominate axes 1 and 2 (services loaded +0.66 and +0.69 on both leading `context` axes). The blocks were regrouped before the numbers in the QA were taken; the axes are now readable (form axis 1: density, coverage and height together; context axis 1: canopy and biomass together).

Places with an undefined input are excluded and listed, never filled: 7 GN divisions for `form` (4 with no footprint, 3 with no GHSL height), 6 for `context` (no CTrees pixel).

**Explanations.** `similar_gn.json` and `similar_ds.json` give, for each place, its 10 nearest places with the distance and the three inputs contributing most to the squared distance. Every file names `space_id` and `space_version`. The decomposition is exact (error about 1e-14 over 300 random pairs per level). Distances are not facts (rule 13): nothing here says two places are alike in any exact sense, and no hierarchy or adjacency is inferred.

## 4. Rights and what stays internal

| Output | Derived from | Status |
|---|---|---|
| Overture-based building indicators and the whole `form` space | ODbL, share-alike | Internal. Whether per-place aggregates are a derivative database is the open question (D-005, multi-scale-features.md §6) |
| GHSL height | GHSL terms (as the other GHSL layers) | Compatible with CC BY with attribution in the same way as GHS-BUILT-S ❓ not re-read |
| CTrees biomass | CC BY (HDX record) | Compatible with attribution |
| Meta/WRI canopy | CC BY 4.0 | Compatible with attribution |
| `context` space | CC BY and CDLA-Permissive inputs only | No ODbL input; still unpublished until the lead approves the recipe |

Nothing is added to a release, the atlas bundle or the live preview. No per-building feature, and no census or people statistic attached to a building, leaves the build folder.

## 5. Commands

| Step | Command (in `pipeline/`) |
|---|---|
| Roll-ups (cached layers reused) | `uv run slf spatial build --data-root ./data --out-dir data/build/landscape-form` |
| Catalogue entries from the specs | `uv run slf spatial catalogue` |
| Spaces and QA | `uv run slf spatial formspace` → `data/build/form/{form,context}/` |

## 6. Known limits

- Footprints are machine-detected and mapped unevenly; compactness depends on how each source draws outlines. Across 13,986 GN divisions with more than 50 footprints the correlation of mean compactness with the Google share of footprints is −0.05 and with the OpenStreetMap share +0.02 ✅, so the source mix does not drive it, but the spread is narrow (5th to 95th percentile 0.716 to 0.751).
- Building height is a modelled, coarse value; most rural places read close to its 2.5 m minimum, so `height` separates urban cores from the rest, not villages from each other.
- Biomass and canopy describe vegetation, including plantations and home gardens, not forest in a legal sense. Biomass was not compared with any published national figure ❓.
- `places_listed` reflects online presence (98% of Overture Places rows come from Meta), not a count of services.
- The recipes are proposals. Axis labels are machine-generated drafts. Neighbour coherence is modest by design: 14% (`form`) and 21% (`context`) of the 10 nearest GN divisions share a district, against 5.6% by chance.

## 7. Per-feature spaces `form-feature` and `context-feature` (private preview)

Built 2026-11-21 on the lead's instruction to build the preview without restrictions while broader permissions are sought. One row per Overture building footprint (8,886,949), with `gn_id` (empty for 853 footprints outside every GN polygon) and the physical inputs only. No people statistic, owner, occupant, name or address is attached (AGENTS rule 11). The output is a 878 MB local Parquet in the gitignored `data/build/form-features/`; nothing is published, released or added to the atlas.

- `form-feature`: footprint area, shape (compactness, rectangularity, elongation) and the modelled GHSL height of its 100 m cell. 4 axes, 98.9% of variance.
- `context-feature`: neighbours within 100 m and 500 m, distance to the nearest other footprint, OSM road, Giga school, healthsites.io facility and the GN coast outline, plus CTrees biomass and elevation at the building's point. 5 axes, 86.6% of variance. 48,778 footprints have no biomass pixel and are excluded (counted in the QA report).
- Method: same as §3 (standardise on a seeded 400,000-footprint sample, winsorise ±5, PCA by SVD, 85% retention), then every footprint is projected. Distances are exact over the stored float32 vectors and decompose into named inputs (largest error over 300 pairs 2.0e-08 and 3.7e-08).
- Command: `uv run slf spatial featurespace` (about 12 minutes on this machine).
- Limits: canopy height per building is left out (too heavy to sample); height is a coarse cell value shared by buildings in the cell; "coast" includes lagoon and island edges. Rule 13 applies: a neighbour list is a distance, not a fact, and must carry `space_id` and `space_version`.
