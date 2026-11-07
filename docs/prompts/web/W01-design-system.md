# W01: Design system, motion, colour scales and performance budget (spike)

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 0–1 | Frontend / Design | 1 | 2026-11-07 | active |

## When to use
Before building map and page components, to set the visual and performance rules. Can run in parallel with Stage 0 data work using sample data.

## Read first
- `AGENTS.md`
- `docs/vision/vision-and-strategy.md` §4 (fluid, high-tech UI with restraint; map-first, not map-only)
- `docs/architecture/architecture-overview.md` §5.1–§5.2 (persistent map shell, lite mode)
- `docs/architecture/technology-choices.md` §4 (chart library left open)

## Inputs (fill in)
```
BRAND_DIRECTION: any words/references the lead wants (e.g. "calm, precise, dark-capable, Sri Lankan without clichés")
SAMPLE_DATA:     path to a small sample (district population, a GN-level share)
```

## Task
1. **Tokens:** colour (light and dark), typography, spacing, radii, elevation and z-layers (map, panels, overlays). Choose fonts that render **Sinhala and Tamil** well (for example Noto Sans Sinhala and Noto Sans Tamil; confirm licences are OFL) alongside a Latin face. Test the mixed-script rendering of real place names.
2. **Choropleth scales:** sequential and diverging palettes that are colour-blind safe (test with a simulator) and readable on the basemap in both themes. Styles for *no data*, *suppressed*, *not applicable*. A documented classification approach (quantiles vs fixed breaks; when each applies) and a legend component.
3. **Motion language:** purposeful transitions only (place-to-place fly, panel enter/exit, scroll-driven story steps). Duration and easing tokens. Full `prefers-reduced-motion` behaviour. No decorative looping animation.
4. **Core components** (in a `/styleguide` route): panel/sheet (desktop side panel, mobile bottom sheet), stat tile with provenance badge, provenance panel (source, document, locator, retrieval date, release, verification), legend, data table with "show as table" for every chart, citation block, breadcrumb, search box.
5. **Chart spike:** build the same three charts (time series, ranked bar, population pyramid) in Observable Plot, visx and plain D3. Compare bundle size, SSR support, accessibility (text alternatives, keyboard) and code clarity. Recommend one and record the decision (propose a decision-log entry).
6. **Performance budget** (`docs/design/performance-budget.md`), with proposed numbers to confirm: JS per route excluding the map chunk; map chunk loaded lazily; LCP and CLS on a mid-range Android profile over slow 4G; data bytes per indicator view; tile bytes per view. Lighthouse CI config enforcing it.
7. **Lite mode spec:** triggers (no WebGL, `Save-Data`, low device memory, user toggle) and what replaces the map (pre-rendered static image plus table).
8. Write `docs/design/design-system.md`.

## Constraints
- Restraint signals trust: no glassmorphism or glow effects that reduce legibility; contrast meets WCAG AA.
- No heavy UI kits. Small, owned components.

## Verify (show real output)
Screenshots (light, dark, mobile, desktop); colour-blind simulation images; chart spike bundle-size table; Lighthouse run on `/styleguide`.

## Deliverables
Tokens, styleguide route, components, chart recommendation, performance budget and CI config, design-system doc.

## Done when
Other web prompts can build on these tokens and components, and the budget is enforced in CI.

Report using the format in `AGENTS.md`.
