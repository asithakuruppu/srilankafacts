# Q02 performance re-check: 2026-11-14

Prepared by an agent for the lead. Verification tags: ✅ measured here · 🟡 claimed, not checked ·
❌ not done or failed · ❓ assumption. Follows [the 2026-11-12 audit](performance-2026-11-12.md).

## Why

Since the first audit, the place page no longer streams its content behind a "Loading place…"
placeholder (PR 37, which made place pages readable without JavaScript). That placeholder's
height was the fix for the 0.696 layout shift found on 2026-11-12, and PR 37 removed it. The site
also now carries the four D-032 census steps (larger place files, grouped indicator lists).

## Verdict ✅

All 10 routes still meet Google's "good" thresholds: **CLS 0.000 everywhere**, LCP 1.81–2.20 s,
TBT 40–131 ms. The layout shift has not come back.

## Setup ✅

Same as 2026-11-12, except the release:

| Item | Value |
|---|---|
| Site | Production build (`pnpm build`, `next start`) on localhost:3420; local release `v2026.11.10-preview.2` (`main` at `ee6d3af`) |
| Tool | Lighthouse 12.8.2 (Node API), performance category; script [`data/lighthouse-2026-11-14-run.mjs`](data/lighthouse-2026-11-14-run.mjs) |
| Device profile | Lighthouse default mobile, simulated throttling |
| Browser | Headless Chrome for Testing (Playwright build 1254) |
| Runs | 3 per route; median reported |

## Results (median of 3) ✅

| Route | Perf (11-12 → now) | LCP s | TBT ms | CLS | JS KB | Data KB |
|---|---|---|---|---|---|---|
| `/` | 95 → 99 | 2.05 | 73 | 0.000 | 430 | 89 |
| `/explore` | 97 → 98 | 2.20 | 71 | 0.000 | 430 | 87 |
| `/place/LK` | 92 → 98 | 2.20 | 88 | 0.000 | 430 | 97 |
| `/place/LK11` (district) | 93 → 99 | 1.81 | 72 | 0.000 | 430 | 114 |
| `/place/LK1103` (DS) | 91 → 98 | 2.20 | 131 | 0.000 | 430 | 342 |
| `/place/LK1103005` (GN) | 97 → 99 | 2.20 | 43 | 0.000 | 148 | 55 |
| `/indicator/population_total` | 95 → 99 | 2.05 | 74 | 0.000 | 430 | 97 |
| `/indicators` | 98 → 99 | 2.20 | 41 | 0.000 | 148 | 40 |
| `/data` | 99 → 99 | 2.04 | 40 | 0.000 | 148 | 34 |
| `/methods` | 99 → 99 | 2.05 | 42 | 0.000 | 148 | 34 |

Raw per-run numbers: [`data/lighthouse-2026-11-14.json`](data/lighthouse-2026-11-14.json).

## Reading the numbers

- TBT is 2–3× lower than on 2026-11-12 on every route, including pages this work did not touch
  (`/data`, `/methods`: 91 → 40 ms). So most of the gain is likely a difference in the run, not
  in the site ❓; the two runs used different scripts (the 11-12 one was not kept). Compare scores
  within one run, not across runs.
- Data KB grew by 10–25 KB on most routes and 22 KB on the DS page; place files now carry the
  D-032 shares.
- The map still loads 430 KB of JavaScript on first paint wherever it appears (finding unchanged
  from 2026-11-12).

## Not checked

- No real device, no field data (INP) ❌. Accessibility was not re-run ❌.
- The performance budget is still not agreed (2026-11-12 §6).
