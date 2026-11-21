# QA: building form, GHSL height, CTrees biomass and the `form` and `context` spaces (2026-11-21)

Private build. Numbers below were produced in this run (`slf spatial build --out-dir data/build/landscape-form`, then `slf spatial formspace`). Method: [form-context.md](../methods/form-context.md) · Decision: D-056 (Proposed). Legend: ✅ verified by running or reading it · 🟡 from a source, not independently checked · ❓ assumption.

## 1. Inputs read (all ✅ held on the archive drive)

| Dataset | Files | Floor | Combined sha256 (first 16) | Blocks read |
|---|---:|---|---|---:|
| overture-buildings 2026-10-21.0 | 1 parquet, 8,886,949 footprints | feature | `e2395801f2a685952390f4854126d86dcda0a4ae9924a5dc9db52344bc83ce64` (file) | n/a |
| ghsl-building-height (ANBH 2018) | 4 tiles | grid-100m | see `sources.json` | rolled up (cached) |
| ctrees-aboveground-biomass | 1 GeoTIFF, EPSG:4326, 0.000889° | grid-100m | `821f4821b56dcefa` | 5 |
| meta-wri-canopy-height-v2 | 75 tiles | grid-1m | `a2554682e917dcb6` | 11,830 (earlier build, cache reused) |

Per-file hashes and retrieval times are in `data/build/landscape-form/sources.json`. The build reports 108 indicators (96 before).

## 2. Coverage against the spine (GN polygon area in EPSG:5235)

| Layer | Measured km² | Spine km² | Ratio | GN p1 | p50 | p99 | GN outside 0.9–1.1 | GN with no pixel |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| canopy_height | 65,983.6 | 65,976.9 | 1.0001 | 1.000 | 1.000 | 1.000 | 0 | 0 |
| biomass | 65,720.9 | 65,976.9 | 0.9961 | 0.780 | 1.000 | 1.072 | 397 | 6 |

Biomass falls short on the coast: CTrees clips to the country boundary, and 100 m pixel centres miss small coastal GN divisions. 6 GN divisions have no pixel and are `not_available` (excluded from `context`, listed in its summary). GHSL height has no coverage ratio: only cells with a height above zero count (16,356 km² nationally).

## 3. Roll-up figures for the country (LK) ✅ computed; none compared with a published total ❓

| Indicator | Value |
|---|---:|
| Footprints inside a GN polygon / read | 8,886,096 / 8,886,949 (853 outside every GN, reported) |
| Mean compactness (Polsby-Popper) | 0.734 |
| Footprints under 20 m² / 250 m² or more | 7.22% / 3.95% |
| Footprints per km² of land | 134.7 |
| Footprint coverage of land | 1.387% (914.9 km²; GHS-BUILT-S 2020 gives 977.1 km² from other imagery) |
| Mean GHSL building height (cells above zero) | 2.895 m over 16,356 km² of cells |
| Mean biomass density, whole measured area | 69.77 Mg/ha |
| Biomass stock | 458.5 million Mg (dry matter, not carbon) over 65,721 km² |
| Mean canopy height (existing) | 6.24 m |

GN divisions with no footprint: 4 (all `form`-excluded). Footprints with a recorded height: 4,338 (not used).

## 4. Spaces

| Space | Level | Places | Excluded | Axes | Variance | Exact decomposition error | Neighbours in same district (chance) |
|---|---|---:|---:|---:|---:|---:|---|
| `form` 0.1 | GN | 14,036 | 7 | 3 | 87.1% | 1.4e-14 | 14.1% (5.6%) |
| `form` 0.1 | DS | 340 | 0 | 3 | 91.3% | 1.4e-14 | 17.5% (4.8%) |
| `context` 0.1 | GN | 14,037 | 6 | 4 | 90.4% | 7e-15 | 20.7% (5.6%) |
| `context` 0.1 | DS | 340 | 0 | 3 | 87.3% | 1.1e-14 | 17.7% (4.8%) |

Error: largest absolute gap, over 300 random pairs, between the squared distance and the sum of its axis contributions or its input contributions. Excluded `form`: 4 with no footprint (LK2209130, LK2209140, LK2224120, LK5109012) and 3 with no GHSL height (LK4112220, LK4403070, LK4415080). Excluded `context`: 6 with no biomass pixel.

Axes (GN): `form` 1 = coverage, density, height together (53.8%), 2 = footprint size (20.1%), 3 = small share (13.1%). `context` 1 = canopy and biomass (52.8%), 2 = listed places against cropland (17.2%), 3 = water (11.8%), 4 = grassland against water (8.6%). Labels are machine drafts.

Most unusual places: `form` DS Thimbirigasyaya, Colombo, Dehiwala; GN Ibbanwala, Soysapura North, Suduwella (Colombo core). `context` DS Colombo, Hatharaliyadda, Dehiwala.

Checks that the build is not an artefact:
- Compactness against footprint source mix, 13,986 GN divisions with more than 50 footprints: correlation −0.05 with the Google share, +0.02 with the OpenStreetMap share ✅.
- Rank correlation of DS pairwise distances, `form` against `context`: 0.34 ✅ (the spaces are related but not the same).
- An earlier grouping with one-input blocks let listed places load +0.66 and +0.69 on the first two `context` axes; the blocks were regrouped before these numbers (method §3).

Files: `data/build/form/{form,context}/` hold `vectors/{space}_v0.1.parquet`, `_axes.parquet`, `similar_gn.json`, `similar_ds.json`, `unusual_*.parquet`, `summary.json` and `qa.md`; `data/build/form/cross_space.json`. All in the gitignored build folder.

## 5. Tests and lint

`uv run pytest`: 312 passed (8 new in `tests/test_formspace.py`, including exact-decomposition, exclusion and shape-measurement fixtures). `uv run ruff check .` and `ruff format --check .`: clean. `uv run pyright`: 0 errors. `uv run slf catalog validate --root ../catalog`: OK.

## 6. Not checked

- No biomass, canopy or GHSL height value was compared with a published national or district figure ❓.
- CTrees units and year come from the HDX record, not CTrees' own documentation 🟡; GHSL and CTrees terms were not read in full ❓.
- Footprint size cuts (20 m², 250 m²) are chosen here and not tested for sensitivity.
- Similar-place lists were not reviewed by a person; axis labels are drafts.
