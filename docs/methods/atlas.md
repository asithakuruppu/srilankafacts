# Method: the map-first atlas (home page)

Status: **built locally, private preview, not published** · 2026-11-17 · Decision: D-042 (Proposed) ·
Code: `pipeline/slf/atlas.py` (`slf atlas export`), `web/src/components/atlas/`, `web/src/lib/atlas/` ·
QA: [`docs/qa/atlas-2026-11-17.md`](../qa/atlas-2026-11-17.md)

Verification tags: ✅ checked by running it · 🟡 from a source, not independently checked · ❓ assumption.

The home page is a full-screen map of Sri Lanka. A reader pans and zooms from the country to
GN divisions, selects a place, and sees one number against its neighbours, its parent, places
like it and the country. Four lenses change what the map and panel show: Geography, Profile,
Change and Landscape. This note says where every part comes from. Nothing here is a new fact:
every number is a published release value or a plain summary of such values.

## 1. The atlas bundle

`slf atlas export` writes a folder of derived files for the website. It is **not part of a
release**: it sits in `pipeline/data/build/atlas/<release>/` and `web/scripts/prepare-release.mjs`
copies it only when its `manifest.json` names the same release. Without it the home page shows a
readable summary and the older boundary map.

| File | Contents | Source |
|---|---|---|
| `overview.geojson`, `outlines.geojson`, `mesh.geojson` | DS polygons, province/district/country outlines and borders, for zoom below 9.6 | spine `geography_versions.geoparquet` (COD-AB v03) |
| `fine.json`, `detail/<district>.json` | GN polygons, DS outlines and borders, loaded per district when zoomed in | same |
| `units.json` | name, level, parent, label point, bounding box, area for country to DS | spine |
| `adjacency.json`, `adjacency-gn/<district>.json` | neighbour lists | spine `spatial/adjacency_*` (G01), unchanged |
| `clusters/<indicator>.json` | units with a significant local Moran class | release `stats/local_*` (D06) |
| `profile.json` | DS profile vectors, axes, the pipeline's similar lists and reasons | profile build v0.3 (D-037) |
| `change.json` | DS population 2012 and 2024, national census series | history build (G06) |
| `manifest.json` | inputs, sha256 of each input, methods, what was left out | — |

## 2. Borders: drawn once

The release boundaries are simplified one polygon at a time, so neighbours no longer share the
same edge. In the DS layer that leaves 129.9 km² of overlaps and about 84 km² of gaps that are
not in the source ✅ (QA §1). Drawing each polygon's own outline then gives doubled lines and
slivers.

The atlas geometry is made differently:

1. The 14,043 GN polygons are checked to be a valid coverage (no gaps, no overlaps) ✅ and
   simplified **as a coverage** in EPSG:5235 (`shapely.coverage_simplify`), so a shared edge
   stays identical on both sides. Two tolerances: 150 m (overview) and 30 m (detail).
2. DS divisions, districts, provinces and the country are **dissolved from those GNs**, so every
   level nests exactly inside the one above.
3. Borders are written as a **line mesh**, each shared border once, with a rank: 0 coast,
   1 province, 2 district, 3 DS, 4 GN. A border has the rank of the coarsest level it divides.
4. The map fills polygons with no antialiased edge and draws only the mesh on top, up to the
   rank of the level in view. The map tiler's own simplification is switched off for these
   sources, because it would move shared edges apart again.

This geometry is for display. Areas, neighbour lists and every statistic come from the spine's
full-resolution shapes, not from the simplified ones.

One stroke system is used at every scale and in both themes (`MAP_TOKENS` and `STROKE_WIDTH` in
`atlas-map.tsx`); page borders, dividers and radii use the tokens `--border`, `--border-rule`,
`--border-strong` and `--radius` in `globals.css`.

## 3. Scale

| Zoom | Level in view | Geometry |
|---|---|---|
| under 6.9 | provinces | overview (150 m) |
| 6.9 to 8.4 | districts | overview |
| 8.4 to 10.4 | DS divisions | overview, then detail from 9.6 |
| 10.4 and over | GN divisions | detail (30 m), loaded for the districts in view |

A level is offered only if the indicator is published at it (ethnic group and religion stop at
DS, D-036). The reader can pin a level. Below the GN division nothing is shown: the scale bar
says "Features: none yet", because no building, tree or landmark dataset is in the release
(multi-scale-features.md §9).

## 4. Compared to where?

For the selected place and indicator the panel shows four references. Each is a plain summary
the reader can redo from the level file `api/v1/indicators/<id>/<level>.json`:

- **Neighbours:** the median of the neighbours that have a value, and how many are lower. The
  neighbour list is the spine's graph: units sharing at least 10 m of border; a unit with none
  gets its 3 nearest, shown with a "nearest, no shared border" tag.
- **Parent:** the parent's own published value. For counts, the place's share of the parent.
- **Similar places:** DS divisions only. The median over the 10 nearest DS divisions in the
  profile space. For other levels the row says why it is empty (D-031).
- **Country:** the national value, or the place's share of it for counts.

Differences are in percentage points for shares and as a ratio otherwise. The rank is "nth
highest of N with a value", worded as a position, not a judgement. A local Moran class is shown
only when the release's statistics mark the unit significant (q ≤ 0.05), with the note that it
describes a pattern, not a cause. Not shown yet: the small-denominator flag and smoothed rates
(they are in `stats/` but not in the bundle).

## 5. Profile lens

The space is the pipeline's `profile` v0.3 at DS level (339 places, 5 retained axes; method in
[profile-space.md](profile-space.md)). The browser only measures in it: Euclidean distance on
the retained axes, by brute force.

- **Places like this:** the 10 nearest DS divisions. The browser's lists equal the pipeline's
  for all 339 divisions, and distances agree to 0.00006 ✅ (QA §3).
- **Why:** the squared distance is a sum over axes, so each axis's share is exact. For pairs in
  the pipeline's top-20 lists, the input-level reasons (most alike, differ most, with shares)
  are the pipeline's own and are shown as such. For other pairs only axis shares are shown.
- **The similarity map:** every DS division on the first two axes, linked to the geographic map.
  It is labelled as a flat view; distances always use all axes.
- **How unusual:** distance from the national centre, as a percentile, with the wording
  "unusual, not better or worse".
- **Near here, unlike here:** bordering DS pairs by profile distance (the pipeline's contrasts).

Not built, and not faked: a typology of place types, user-chosen recipes, GN similar lists
(D-031), district or province profiles. Axis names are machine drafts and are labelled so.

## 6. Change lens

DS population 2012 → 2024 and the national series 1871–2024 come from the history build (G06,
[boundary-change-2012-2024.md](boundary-change-2012-2024.md)). Each DS shows its comparison
label (`exact` or `approximate`) and the reason. The lens states that this is a local build and
not in a release. Left out: the DCS 5224 Kalmunai row (no spine unit, D-022) and district
totals (the district series is keyed by name only, and names alone are not a join, AGENTS
rule 5). ❓ Rights: these figures are covered by D-038 for local use; they must not go into a
public build until the lead extends D-030 to them.

## 7. Landscape lens

No landscape dataset is ingested. The lens says so, shows the place's area (the one physical
measure the spine holds) and lists what is planned. Nothing is estimated or drawn.

## 8. Reproduce

From `pipeline/`:

```bash
uv run slf atlas export --release-dir data/build/releases-preview/<release> \
  --profile-dir data/build/profile-v03 --history-dir data/build/history
```

Then `pnpm dev` or `pnpm build` in `web/` (the `predev`/`prebuild` step copies the bundle).
