# Method: landscape and feature roll-ups (open spatial layers by place)

Status: **private build, 2026-11-17** · Decisions: D-043 (Proposed), D-044 (Proposed) · Builds on D-013, D-014, D-016, D-017, D-018 · QA: [landscape-2026-11-17.md](../qa/landscape-2026-11-17.md) · Sources and rights: [discovery catalogue](../research/spatial/discovery-catalogue.md)

Legend: ✅ verified directly · 🟡 from a secondary source · ❌ not found · ❓ assumption.

## 1. What this is

Open satellite-derived rasters and open point and footprint layers, summarised for **every place in the spine**: 14,043 GN divisions, 340 DS divisions, 25 districts, 9 provinces and the country. The result is 69 indicators and 1,714,992 observations in the same ledger format as the census, each with its dataset, snapshot hash, source locator, time footprint and information floor.

None of it is a statistic about people. Every raster-derived value is a `modelled_estimate` (D-013: a value moved from one support to another is at best that), and it is `machine_extracted`.

Commands (in `pipeline/`):

| Step | Command |
|---|---|
| Fetch originals | `uv run slf spatial snapshot` |
| Extract Overture (large) | `uv run slf spatial overture places --release 2026-10-21.0 --data-root <drive>` (and `buildings`) |
| Roll up to places | `uv run slf spatial build --data-root ./data --data-root <drive>` |
| Landscape space | `uv run slf spatial space --profile-dir data/build/profile-v03` |
| Findings against the census | `uv run slf spatial findings --data-root ./data --data-root <drive>` |
| Catalogue entries from the specs | `uv run slf spatial catalogue` |

## 2. Rasters: zonal sums on the source's own grid

1. **No resampling.** GN polygons are reprojected to the raster's CRS and burnt onto the raster's own pixel grid. A pixel belongs to the GN that contains its centre.
2. **Ground area per pixel.** For rasters in longitude and latitude, each row's pixel area is computed exactly on the WGS 84 ellipsoid. For GHSL's World Mollweide tiles, the nominal cell area is multiplied by the ratio of the block's geodesic area to its map area: the projection is computed on a sphere, so a nominal hectare is about 0.66% smaller on the ground at Sri Lanka's latitude ✅ (measured: uncorrected totals were 1.0066 times the spine area; corrected, 1.0001).
3. **Coarse cells are shared by area.** A 100 m GHSL cell is split into 25 sub-cells of 20 m, a 1 km settlement cell into 2,500, and each sub-cell goes to the GN containing its centre. The information is still that of the source cell: the `information_footprint_ref` says `grid-100m` or `grid-1km`.
4. **Only additive components are stored per GN** (areas in m², area-weighted sums, minimum, maximum). Every share and mean is recomputed from components at each level, so a district value is exactly what its GN divisions give. The provisional DS unit `LK-ADM3-P0001` is the sum of its 29 listed GN divisions; those GN divisions also count in their COD-AB parent, as in the spine ❓ (not re-checked here).
5. **Coverage check.** For every layer the measured area is compared with the GN polygon's area in EPSG:5235. All six layers total 1.0001 of the spine area ✅.

| Dataset | Floor | What is computed | Time footprint used |
|---|---|---|---|
| Copernicus DEM GLO-30 | 30 m | Mean, lowest and highest elevation; mean slope (central differences, metres per pixel from the ellipsoid); area steeper than 15° | 2010-12-12 to 2015-01-16, `observed_around`, period `2013` 🟡 (acquisition dates from the product documentation, not re-read) |
| ESA WorldCover 2021 v200 | 10 m | Area and share of nine land-cover classes | 2021, `observed_around` |
| Global Forest Change v1.12 | 30 m | Tree cover in 2000 (canopy ≥ 30%); loss per year 2001 to 2024 inside that cover; total loss and its share of the 2000 cover | 2000; each year `interval_total` |
| JRC Global Surface Water v1.4 | 30 m | Area with water in ≥ 75% of valid observations; area with water ever detected | 1984-03-16 to 2021-12-31, `interval_mean` |
| GHS-BUILT-S R2023A | 100 m | Built-up surface and its share, ten epochs 1975 to 2020 | each epoch year, `observed_around` |
| GHS-SMOD R2023A 2020 | 1 km | Area in urban centre cells; area in urban centre or urban cluster cells | 2020 |

What the definitions do **not** mean, stated on each indicator: tree cover includes rubber, coconut and other plantations; tree cover loss is not deforestation and regrowth is not subtracted; the surface model includes buildings and canopy; land cover is a classification, not a land-use survey; "urban" in GHS-SMOD is a density rule on a modelled population grid, not Sri Lanka's administrative definition.

## 3. Points and footprints

Each point goes to the GN division that contains it (points on a shared border go to the first GN in id order). Points outside every GN polygon are counted in QA and kept in the feature table with an empty `gn_id`; they are in no place's count (rule 6).

| Dataset | Licence | Published per place | Note |
|---|---|---|---|
| Giga school locations | CC BY | Schools located; schools recorded as connected; share; straight-line distance from the GN label point to the nearest school | The list names the Ministry of Education as its source 🟡. The CSV states no CRS ❓ |
| healthsites.io (OpenStreetMap) | ODbL | Mapped hospitals, clinics and doctors; straight-line distance to the nearest | A count of what is mapped. Completeness is not measured |
| Overture Places 2026-10-21.0 | CDLA-Permissive-2.0 | Listed places with confidence ≥ 0.5, total and by 13 top-level categories | 98% of rows come from Meta; reflects online presence |
| Wikidata | CC0 | Items with coordinates | |
| Overture Buildings 2026-10-21.0 | ODbL | Footprints mapped; footprint area; mean footprint | Footprint goes to the GN containing its inside point; area in EPSG:5235 |

The straight-line distances are not travel distances. They are published for GN divisions only, measured from the label point, so a large GN with a small settled corner can show a long distance that few residents experience.

**No people at feature level.** No addresses, phone numbers, emails, websites or social links are extracted from Overture. No census value is attached to a building. Individual features are not published; the resolved tables stay in the build folder with their licences.

**A gap in the data model.** `data_nature` has no value for "a count of mapped features". These rows use `modelled_estimate` with universe `mapped_features` and say so in each definition. A new value is proposed under "Decisions needed" in the PR.

## 4. The `landscape` space v0.1 (proposed, D-044)

Nine inputs in three equally weighted blocks (terrain: elevation, slope; cover: tree, cropland, grassland, built-up, water; change: built-up growth 1975 to 2020, tree cover loss 2001 to 2024), transformed as listed in [`catalog/spaces/landscape.yaml`](../../catalog/spaces/landscape.yaml), then the same standardisation, block weighting and PCA code as the `profile` space. Distances decompose exactly into the nine named inputs.

One recipe difference from `profile`: axes are kept until they explain 85% of the variance (at most 6). D-029's rule kept only one axis at DS level, which reduced the space to "highland or lowland" and paired places such as Kaduwela and Kuchchaweli at distance 0.001 ✅ (seen in the first build, then corrected).

Vector doc naming: [vector-space-model.md](../architecture/vector-space-model.md) reserved `landscape` for satellite embeddings. This version uses named indicators so that every distance can be explained.

## 5. Licences of the outputs

| Derived from | Output licence |
|---|---|
| Copernicus DEM, WorldCover, Global Forest Change, Global Surface Water, GHSL, Giga, Wikidata | Compatible with CC BY 4.0 with the source attributions (the Copernicus DEM licence still needs a full read: R02) |
| Overture Places | CDLA-Permissive-2.0 source; counts can be CC BY with attribution ❓ (confirm in R02) |
| healthsites.io, Overture Buildings | **ODbL.** Kept apart from CC BY outputs (D-005); whether per-place counts are a derivative database is the open legal question already listed in multi-scale-features.md §6 |

Nothing here is in a release. The catalogue marks rights per dataset; the release builder will refuse a dataset whose rights are unclear.

## 6. Known limits

- GN boundaries are COD-AB v03; the Census 2024 comparison covers the 13,962 GN divisions with a census match.
- GHSL's early epochs are modelled back from later imagery; treat growth since 1975 as an estimate.
- WorldCover often classes paddy as grassland or cropland depending on season; class shares are not land-use statistics.
- The lowest pixel in the country is −21.4 m. Negative heights occur in the surface model (pits, noise over water); they are reported as read.
- Values were not compared with any published national total in this run (see QA §"Not checked").
