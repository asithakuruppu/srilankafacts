# Q03 accessibility checks, 2026-11-18 (automated subset only)

Headless Chromium on ten pages (`/`, a GN in the atlas, the Landscape lens, `/area`, `/query`, `/about`, `/indicators`, `/data/calendar`, `/elections`, `/explore`) at 390 × 844.

| Check | Result |
|---|---|
| `<html lang>` set | ✅ all pages (`en`; follows the draft language when a visitor opts in) |
| Visible controls without an accessible name | ✅ 0 on every page |
| Form fields without a label | ✅ 0 |
| Images without `alt` | ✅ 0 |
| Sideways scrolling at phone width | ✅ none (a header overflow at 1,024 px was fixed in Phase 4) |
| One `h1` per page | ✅ after this phase; the atlas home had a second `h1` in its loading fallback, now an `h2` |

**Not checked:** colour contrast of the map palettes and tags, keyboard-only use of the map and the area tool, focus order in the panel, screen readers (VoiceOver, TalkBack, NVDA), reduced motion, zoom to 200%. These need a person (Q03 prompt).
