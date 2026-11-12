# Q03 accessibility audit: 2026-11-12

Prepared by an agent for the lead. Verification tags: ✅ checked here · 🟡 claimed, not checked ·
❌ not done or failed · ❓ assumption.

## Verdict

- **Automated checks:** before the fixes, axe found **23 rule-page violations**, in 2 rules. After
  this PR's fixes it finds **0**, in light and dark themes, on 10 routes ✅. Lighthouse
  accessibility is 100 on 9 of 10 routes and 96 on the indicator page.
- **Keyboard:** the journeys work ✅. The skip link did not move focus; that is fixed.
- **No screen-reader testing was done** ❌. VoiceOver is available on this Mac, but an agent cannot
  listen to its output. A person needs to do this pass (about 20 minutes).

## 1. Tools used ✅

- **axe-core 4.10.3**, injected with Playwright into a production build (`next start`, release
  `v2026.11.8-preview.1`). Rule tags: `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`. Viewport
  1280×900. Run in light and dark (`prefers-color-scheme`).
- **Lighthouse 12.8.2** accessibility category (mobile).
- **Keyboard:** scripted Tab, Enter and arrow-key presses in Playwright Chromium, recording the
  focused element and whether it shows an outline or focus ring.
- **Code review** for motion, `lang` attributes and text alternatives.

Routes: `/`, `/explore`, `/place/LK`, `/place/LK11`, `/place/LK1103`, `/place/LK1103005`,
`/indicator/population_total`, `/indicators`, `/data`, `/methods`.

## 2. Automated results ✅

| Rule | Severity | Where | Before | After |
|---|---|---|---|---|
| `color-contrast` | serious | "Private preview" banner on every page (light): warm text 3.87:1 on its background | 11 pages, 20 nodes | 0 |
| `color-contrast` | serious | Home page hero (dark theme): button 1.89:1, kicker 1.13:1, big number 1.36:1 | (in the 20 above) | 0 |
| `aria-hidden-focus` | serious | Map canvas focusable inside an `aria-hidden` container | 6 routes × 2 themes | 0 |
| `target-size` (WCAG 2.2, Lighthouse only) | moderate | 25 place-name links in the indicator page's ranking, 18 px tall | 1 page | Fix applied, **not re-measured** |

Raw results: `docs/qa/data/axe-2026-11-12-{before,after}.json`.

## 3. Manual and scripted checks

| Check | Result |
|---|---|
| Skip link is the first Tab stop | ✅ "Skip to content" |
| Skip link moves focus to the content | ❌ → ✅. It changed the URL to `#main` but focus stayed on `body`. Fixed with `tabIndex={-1}` on `<main>` and re-tested (focus on `main`) |
| Tab order, home and DS page (first 25 stops) | ✅ Logical: skip link, brand, nav, search, then page content. Every stop had a visible outline or focus ring |
| Map in the tab order | ❌ → ✅. The canvas was a Tab stop although hidden from screen readers. It now has `tabIndex = -1`; the table next to it carries the same values |
| Search by keyboard: type "Kandy", Enter | ✅ The first option (Kandy district) is pre-selected and Enter opens `/place/LK21`. Arrow keys move the selection |
| Journey search → place → indicator → download | 🟡 Search → place checked by script. Indicator and download links are ordinary links in the tab order, but the full journey was not scripted |
| Every map has a text or table alternative | ✅ All 6 routes with a map also have a table (`/`: hero facts and the place list) |
| Charts have text | ✅ The age bars print their numbers and percentages; the sex bar prints both counts |
| Legends readable without colour | ✅ The map legend labels every class with its range. Choropleth contrast against the basemap was not measured ❌ |
| `prefers-reduced-motion` | ✅ A global rule shortens animations and transitions and turns off smooth scrolling. The map never animates (`duration: 0`) |
| `lang` on Sinhala and Tamil names | ❌ → ✅. The place-page heading showed them with no `lang`. They now carry `lang="si"` / `lang="ta"`. Places with no English name still show a Sinhala or Tamil fallback label without `lang` (breadcrumbs, lists) ❌ |
| Screen reader (VoiceOver or NVDA) | ❌ Not done (see verdict) |
| Sinhala and Tamil font rendering | 🟡 Glyphs render in Chromium on macOS. Not checked on Android or Windows |

## 4. Fixes in this PR

1. Light-theme `--warm` darkened from `#a5641c` to `#8f5413`: 4.99:1 on `--warm-soft`, 5.55:1 on
   paper.
2. Button and home-hero text now use the theme's paper colour, so dark mode gets dark text on
   the light-green fills: 9.6–12.4:1.
3. Map canvas taken out of the tab order.
4. `<main tabIndex={-1}>`, so the skip link moves focus.
5. `lang` attributes on the Sinhala and Tamil names in the place heading.
6. Ranking links at least 24 px tall.
7. (Performance) A place-page placeholder with the viewport's height, to remove the layout shift.

## 5. Not fixed: follow-ups

| # | Issue | Severity | Suggestion |
|---|---|---|---|
| 1 | No screen-reader pass | high (unknown) | The lead or a tester does a 20-minute VoiceOver pass of search → place → indicator |
| 2 | Fallback labels in Sinhala or Tamil (places with no English name) have no `lang` | moderate | Return the script with the label from `geographyLabel` and set `lang` where it renders |
| 3 | Choropleth colours vs basemap and labels not measured | moderate | Check the 5 classes in both themes with a contrast tool |
| 4 | Full keyboard journey to download not scripted | low | Add it to the Playwright smoke test |
| 5 | WCAG 2.2 rules beyond `target-size` not run | low | Add the `wcag22aa` tag once axe supports it fully |
