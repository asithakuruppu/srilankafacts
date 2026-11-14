# Q03 accessibility re-check: 2026-11-14

Prepared by an agent for the lead. Verification tags: ✅ checked here · 🟡 claimed, not checked ·
❌ not done or failed · ❓ assumption. Follows [the 2026-11-12 audit](accessibility-2026-11-12.md).

## Why

Since the first audit: place pages show a new "Ethnic group and religion" section (D-033), the
home page groups 115 indicators in collapsible sections, indicator pages list their group, and
place pages no longer stream (PR 37).

## Verdict

- **axe: 0 violations** on all 10 routes, light and dark ✅.
- **Lighthouse accessibility: 100 on all 10 routes** ✅, after one fix in this PR. Before it, the
  home page scored 96: one link in the new indicator groups was 19 px tall (`target-size`). Links
  in those groups now have a 24 px minimum height.
- The `target-size` fix from 2026-11-12 (indicator page ranking links), never re-measured then,
  is confirmed: the indicator page scores 100 ✅.
- **Still no screen-reader pass** ❌ (needs a person; about 20 minutes with VoiceOver).

## Setup ✅

| Item | Value |
|---|---|
| Site | Production build on localhost:3420; local release `v2026.11.10-preview.2` |
| axe | axe-core 4.10.3 injected with Playwright; tags `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`; 1280×900; light and dark |
| Lighthouse | 12.8.2, accessibility category, mobile |
| Script | [`data/axe-2026-11-14-run.mjs`](data/axe-2026-11-14-run.mjs); raw results [`data/axe-2026-11-14.json`](data/axe-2026-11-14.json) |

Routes: `/`, `/explore`, `/place/LK`, `/place/LK11`, `/place/LK1103` (includes the ethnicity and
religion tables), `/place/LK1103005`, `/indicator/population_total`, `/indicators`, `/data`,
`/methods`.

## Not checked

- Keyboard journeys were not re-scripted ❌. The new groups use native `<details>`/`<summary>`,
  which are keyboard operable by default ❓.
- Screen reader, zoom to 400% and a real mobile device ❌.
