# W02: Persistent map shell and explorer

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 1 | Frontend / Maps | 2 | 2026-11-08 | active |

## When to use
To build the map experience that stays mounted across place pages and powers `/explore`.

**Implemented 2026-11-08 (Stage 1A), with deviations:**
- The preview has a per-page `MapView` (home, `/explore`, place pages), not yet one
  layout-level MapLibre instance that persists across navigation. Persistence remains
  required for Stage 1B; do not describe the current map as persistent.
- Boundaries come from the release's GeoJSON (`admin0`–`admin4`), with **no basemap**.
  `tippecanoe`, `pmtiles` and `ogr2ogr` were unavailable, so G04's PMTiles path was not
  built. GeoJSON is a recorded fallback, not the target architecture.
- The browser gets the full release from `SLF_RELEASE_DIR`, else the newest
  `pipeline/data/build/releases-preview/v*`, else the committed `web/fixtures/preview`
  subset so CI builds without the 459 MB release.
- MapLibre's worker is copied by `scripts/prepare-release.mjs` and loaded from
  `/release/maplibre-gl-worker.mjs`; the default relative worker URL fails in Next.js.
- Every page is complete without the map, and the table is the primary accessible view.
  Place, indicator, data and methods pages render server-side; `/explore` builds its table
  in the browser and therefore needs JavaScript, though not the map.

## Read first
- `AGENTS.md`
- Decision D-002 (map-first, not map-only) in `docs/decisions/decision-log.md`
- `docs/architecture/architecture-overview.md` §5.1–§5.2
- `tiles/README.md` (G04) and `docs/design/design-system.md` (W01)
- Release static API layout (W05/D04)

## Inputs (fill in)
```
DEFAULT_INDICATOR: e.g. population_density
LEVELS:            province, district, ds, gn
```

## Task
1. A layout-level client component in the Next.js App Router that holds **one** MapLibre instance (PMTiles protocol registered once) and persists across navigation between `/place/[geoId]` routes and `/explore`.
2. Sources per boundary level with `promoteId: "geography_id"`. Level switching by zoom and by the current route.
3. **Choropleth via `feature-state`:** fetch `/api/v1/indicators/{id}/{level}.json` (or the release equivalent), set state per feature, colour with the W01 scale; no-data and suppressed styles; legend synced.
4. **Route ↔ map sync:** on navigation to a place, fly to its bounds (respect reduced motion) and highlight it; clicking a feature navigates to its place route (a real link, so the history works); hover shows name and value.
5. **`/explore`:** full-screen mode with indicator, level and period pickers and a compare toggle. All state lives in the URL, so views can be shared.
6. **Lite mode** per W01: no WebGL → static map image plus table, and the page still works.
7. **Accessibility:** keyboard navigation of the map's main actions, visible focus, a "view as table" alternative, ARIA live region for the selected place.
8. Playwright tests: open a district page → map highlights it → click a DS → URL changes → panel updates; explore URL round-trip; lite-mode rendering.

## Constraints
- **Server-rendered page content must be complete without the map** (D-002). The map enhances; it never contains the only copy of information.
- One map instance only. Don't re-create it on navigation.
- Respect the performance budget: lazy-load the map chunk; no indicator data in the initial HTML beyond what the page displays.

## Verify (show real output)
Playwright results; Lighthouse mobile scores for a place page with and without the map; a screen recording or screenshot sequence of a place-to-place transition; memory check after 20 navigations (no leak).

## Deliverables
Map shell components, explorer route, tests, notes in `web/README.md`.

## Done when
Navigating between places feels continuous on the map, every place has a real URL with full HTML content, and the budget holds.

Report using the format in `AGENTS.md`.
