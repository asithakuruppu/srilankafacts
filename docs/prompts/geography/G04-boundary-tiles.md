# G04: Boundary PMTiles and Sri Lanka basemap extract

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 1 | Geography / Maps | 1 | 2026-11-07 | active |

## When to use
To produce the vector tiles the map shell (W02) uses. Re-run when boundaries change (new vintage), never for data changes.

## Read first
- `AGENTS.md`
- `docs/architecture/architecture-overview.md` §5.2 (maps: feature-state joins, zoom detail, basemap)
- `docs/architecture/technology-choices.md` §2.5
- G01 outputs, G03 recommendation on which geometry to tile
- `docs/design/design-system.md` (W01) for colour tokens, if it exists

## Inputs (fill in)
```
VINTAGE:            e.g. cod-ab-v03
LEVELS:             province, district, ds, gn (later: la, ed, pd, moh)
PROTOMAPS_BUILD:    a specific daily build date/URL to pin (don't use "latest" unpinned)
SIZE_BUDGET:        e.g. GN tileset ≤ 25 MB, all boundary tilesets ≤ 40 MB (adjust after first build)
```

## Task
1. Write `tiles/` recipes (a script plus a config per level). Tippecanoe with explicit min/max zoom per level (for example provinces z0–z9, districts z4–z11, DS z6–z12, GN z9–z14; tune and justify), simplification and coalescing settings. Each feature carries **only** `geography_id` and `name_en`.
2. Make the IDs work with MapLibre `feature-state`: string p-codes can't be numeric feature IDs, so configure the source with `promoteId: "geography_id"` and confirm it works with PMTiles.
3. Produce the basemap: `pmtiles extract` from the pinned Protomaps build, for Sri Lanka's bounding box plus a margin. Record the build date and hash. Style light and dark variants with brand tokens. Include the required OSM/Protomaps attribution string.
4. A test page (in `web/` under a dev-only route, or `tiles/preview.html`) showing each level over the basemap, with a toggle and a random choropleth via feature-state to prove the join.
5. Measure tileset sizes, tile counts per zoom, the largest tile, and load time for a national view and a GN-level city view. Compare with SIZE_BUDGET.
6. Check visually and numerically that boundaries align with the basemap coastline at z8, z11 and z14 (screenshots).
7. Document in `tiles/README.md`: how to rebuild, inputs (snapshot hashes), outputs and sizes. Upload happens only through CI (O01).

## Constraints
- No indicator values baked into tiles.
- Don't depend on third-party tile servers at runtime.

## Verify (show real output)
Tippecanoe and `pmtiles show` output; the size table; screenshots at the three zooms; feature-state demo screenshot.

## Deliverables
Tile recipes, built PMTiles (local or CI artefact), basemap extract, styles, preview, README.

## Done when
The map shell can load every level from PMTiles and colour any level by `geography_id` without rebuilding tiles.

Report using the format in `AGENTS.md`.
