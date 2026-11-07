# W08: Two-map explorer (geography beside similarity)

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 2 | Web | 1 | 2026-11-07 | draft |

## When to use
Stage 2, once the `profile` space (A03) is in a release and the map shell (W02) is stable.

## Read first
- `AGENTS.md`
- `docs/architecture/vector-space-model.md` §6–§7
- `docs/decisions/decision-log.md` D-002, D-016
- W01 design system and performance budget

## Inputs (fill in)
```
SPACE: profile@{{SPACE_VERSION}}
LEVELS: ds, gn
DEFAULT_LAYOUT: pca          # pca | umap (umap labelled "layout for clusters, not distances")
```

## Task
1. Route `/explore/space` with URL state (selection, layout, level, weights).
2. Left: the existing map shell. Right: places plotted by their first two axes (or the precomputed UMAP layout), coloured by the selected indicator or type.
3. Linked selection both ways: brushing on either view highlights the same places on the other; selecting one place lists its nearest neighbours with exact reasons from the release files.
4. Preset questions as entry points: "places like this", "near here, unlike here", "far away, like here", "how unusual is this place".
5. `composite` sliders (when that space exists): recompute distances in the browser from release vectors; never on the 2D picture.
6. Text alternative: a table of the selected places, neighbours and reasons; works without WebGL.

## Constraints
- Distances come from the full vectors in the release, never from screen positions.
- Every view states the space and version, and links to the methods page.
- Within the W01 performance budget on a low-end phone.

## Verify (show real output)
- Screenshots (desktop and mobile) of linked selection.
- Playwright test: selecting a place on the map highlights it in the similarity view and vice versa.
- Neighbour lists match the release JSON for 5 sample places.

## Deliverables
Route, components, tests, short user guide on the methods page.

## Done when
A first-time user can pick a place and see where similar places are in the country, and why.

Report using the format in `AGENTS.md`.
