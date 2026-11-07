# Q03: Accessibility audit

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 1+ | Quality / Frontend | 1 | 2026-11-07 | active |

## When to use
Before launch and after major UI changes. Target: WCAG 2.2 AA.

## Read first
- `AGENTS.md`
- `docs/design/design-system.md` (W01)
- D-002 (content must not depend on the map)

## Inputs (fill in)
```
URL:    preview base URL
ROUTES: same set as Q02, plus /data and /methods
```

## Task
1. Automated checks (axe) on each route and template, in light and dark themes.
2. Manual checks: keyboard-only journeys (search → place → indicator → download), focus order and visibility, skip links; screen-reader pass with VoiceOver or NVDA (whichever is available; state which).
3. Maps and charts: does every map view have a table or text alternative? Do charts have text descriptions? Are legends perceivable without colour (patterns or labels where needed)? Contrast of choropleth colours against basemap and text.
4. Motion: `prefers-reduced-motion` respected everywhere.
5. Language: `lang` attributes for Sinhala and Tamil text; font rendering.
6. Write `qa/accessibility-{{date}}.md` with issues by severity and fix suggestions; implement trivial fixes and file the rest.

## Constraints
- Report the tools and assistive technology actually used. Don't claim screen-reader testing that wasn't done.

## Verify (show real output)
axe output summary; manual checklist with pass/fail.

## Deliverables
Report, fixes and issues.

## Done when
No critical or serious issues remain on launch routes.

Report using the format in `AGENTS.md`.
