# G01: Geography spine v0 (admin levels 0–4 from COD-AB)

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 0 | Geography | 2 | 2026-11-07 | active |

## When to use
To build the first version of the admin geography register that every dataset joins to. Re-run when a new COD-AB version or an official boundary source becomes available.

## Read first
- `AGENTS.md`
- `docs/architecture/data-model.md` §3 (spine, IDs, versions, names)
- `docs/lanka-data-layer-audit.md` §7, §10, §11 (known issues: Ampara parent, counts, overlaps, code drift)
- `catalog/sources/` entries for COD-AB and the Survey Department

## Inputs (fill in)
```
COD_AB_URL:    https://data.humdata.org/dataset/cod-ab-lka  (confirm the current resource files)
VINTAGE_NAME:  e.g. cod-ab-v03 (use the version stated by the source; don't guess)
```

## Task
1. **Snapshot** the COD-AB resources (all admin levels; prefer the format with the richest attributes) through the pipeline's snapshot function. Record URL, retrieval time, sha256, and the source's stated version and dates.
2. **Inspect and report**: layers, CRS, attribute fields (names, p-codes, parent codes, Sinhala/Tamil name fields), feature counts per level, geometry types. Put this in the QA report *before* transforming anything.
3. **Build `geographies`** (levels 0–4): `geography_id` = p-code, `scheme: admin`, `level`, `name_en/si/ta`, `alt_names` (empty for now), `parent_id` from the **attribute** parent code (not spatial inference), `status: current`, `valid_from` = source date.
4. **Build `geography_versions`**: canonical (unsimplified) geometry in EPSG:4326, area in km² computed in EPSG:5235, a label point (pole of inaccessibility or representative point), `vintage = VINTAGE_NAME`, `source_dataset`, snapshot hash.
5. **Validate** (as pipeline tests):
   - unique IDs; every parent exists; `parent.level == level - 1`
   - **regression test:** Ampara `LK52` has parent `LK5` (Eastern Province)
   - each unit lies within its parent (share of area outside parent, threshold configurable, report offenders)
   - area roll-ups per level against the country area (report differences)
   - name coverage per level and language (report)
   - duplicate names within the same parent (report; IDs are the keys)
6. **Compare counts** with Lanka Data Layer (1/9/25/339/14,043) and NSDI (9/25/332 features (329 codes)/14,051) from the audit, and the commonly cited 331 DS / 14,022 GN. Present a table. Don't resolve differences here (that is G02).
7. **Build the contiguity graph** per level (`spatial/adjacency_{level}_{vintage}.parquet`: `geography_id`, `neighbour_id`, `shared_border_m`, `type` = `border` | `distance_band`). Compute in EPSG:5235 with a small snapping tolerance you state. Units with no border neighbours (islands such as Delft, if present as separate units ❓) get distance-band neighbours and are listed in the QA report. See `docs/architecture/spatial-first-analytics.md` §4.1.
8. Write the `geo` space coordinates (3D unit vector from each unit's label point) as `vectors/geo_{vintage}.parquet` (`docs/architecture/vector-space-model.md` §4).
9. Write outputs to a local release build: `geographies.parquet`, `geography_versions.geoparquet`, a GeoPackage for QGIS, and `qa/geography-spine-v0.md`.

## Constraints
- Never simplify canonical geometry. Simplification is for tiles (G04).
- Never "fix" a parent by spatial inference silently. If attribute and spatial parents disagree, report it and leave the decision to the lead (or an override with evidence).
- Don't use Lanka Data Layer or nuuuwan geometry as the source in this task.

## Verify (show real output)
- Test run output (pass/fail counts).
- Feature counts per level, the comparison table, and the top 10 "outside parent" offenders.
- `ogrinfo -so` (or equivalent) on the produced GeoPackage.

## Deliverables
Pipeline module `datasets/cod_ab_admin.py`, tests, QA report, local build artefacts, catalogue updates.

## Done when
The lead can open the GeoPackage in QGIS, see all five levels, and read in the QA report exactly which counts and issues exist.

Report using the format in `AGENTS.md`.
