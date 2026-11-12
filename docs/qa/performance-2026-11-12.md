# Q02 performance audit: 2026-11-12

Prepared by an agent for the lead. Verification tags: ✅ measured here · 🟡 claimed, not checked ·
❌ not done or failed · ❓ assumption.

## Verdict

- **Core Web Vitals "good" thresholds are met on all 10 routes after this PR's fixes** ✅. LCP is
  1.7–2.5 s, CLS is 0.000 and TBT is 89–316 ms (Lighthouse mobile, simulated throttling).
- **Before the fixes, district, DS and GN place pages failed CLS** at 0.696, against a "good"
  limit of 0.1. Their performance scores were 69–74. A one-rule CSS fix brought them to 0.000
  and 91–97.
- **There is no agreed performance budget.** W01 was meant to write
  `docs/design/performance-budget.md`, but that file does not exist. This report measures against
  Google's "good" thresholds and proposes a budget for the lead to confirm (section 6).

## 1. Setup ✅

| Item | Value |
|---|---|
| Site | Production build (`pnpm build`, `next start`) on localhost:3420; release `v2026.11.8-preview.1` |
| Tool | Lighthouse 12.8.2 (Node API), performance and accessibility categories |
| Device profile | Lighthouse default mobile: simulated throttling, 150 ms RTT, 1.6 Mbps down, 4× CPU slowdown |
| Browser | Headless Chrome for Testing 158 (Playwright build 1254) |
| Machine | Apple M2, macOS 27.2 |
| Runs | 3 per route; the median is reported |

Simulated throttling is an estimate, not a real mid-range Android phone ❓. A field check on a
real device is still needed.

## 2. Lighthouse results (median of 3) ✅

Before is the code on `main`; after includes this PR's fixes.

| Route | Perf before → after | LCP s | TBT ms | CLS before → after | JS KB | Data KB |
|---|---|---|---|---|---|---|
| `/` | 93 → 95 | 2.02 | 236 | 0.000 → 0.000 | 429 | 79 |
| `/explore` | 94 → 97 | 1.66 | 173 | 0.000 → 0.000 | 429 | 79 |
| `/place/LK` | 95 → 92 | 2.48 | 273 | 0.000 → 0.000 | 429 | 84 |
| `/place/LK11` (district) | 71 → 93 | 2.48 | 233 | **0.696** → 0.000 | 429 | 92 |
| `/place/LK1103` (DS) | 69 → 91 | 2.42 | 316 | **0.696** → 0.000 | 429 | 320 |
| `/place/LK1103005` (GN) | 74 → 97 | 2.42 | 115 | **0.696** → 0.000 | 148 | 34 |
| `/indicator/population_total` | 95 → 95 | 2.12 | 238 | 0.000 → 0.000 | 429 | 84 |
| `/indicators` | 98 → 98 | 2.11 | 104 | 0.000 → 0.000 | 148 | 33 |
| `/data` | 98 → 99 | 2.10 | 91 | 0.000 → 0.000 | 148 | 22 |
| `/methods` | 99 → 99 | 2.09 | 89 | 0.000 → 0.000 | 148 | 22 |

- **JS KB** is compressed script transfer on first load. **Data KB** is fetch/XHR transfer, mostly
  boundary GeoJSON for the map.
- `/place/LK` dropped from 95 to 92 between runs, with an unchanged page. Read differences of ±3
  points as run-to-run noise.
- Raw per-run numbers: `docs/qa/data/lighthouse-2026-11-12-{before,after}.json`.

**INP is not measured.** Lighthouse lab runs report TBT as a proxy; INP needs field data.

## 3. What caused the layout shift ✅

Lighthouse's `layout-shifts` audit named a single element, `body > footer.site-footer`, with a
score of 0.696.

Place pages below the country level stream their content into a short "Loading place…"
placeholder, and the footer jumped down when the content arrived. The fix gives that placeholder
the height of the viewport (`.place-skeleton { min-height: 100vh }`), so the footer starts below
the fold.

## 4. Bundle ✅

- The largest chunk is MapLibre: 1,054 KB raw, 286 KB gzipped. It is behind a dynamic `import()`
  in `map-view.tsx`, so it is a separate chunk.
- **It still loads on first paint of every route that shows a map**: 429 KB of JS on those routes,
  against 148 KB on routes without one. The map mounts immediately, so "lazy" only means "a
  separate file".
- The other chunks are 72, 47 and 39 KB gzipped (framework and app code). No duplicate
  dependencies were checked ❌. There is no bundle analyser in the project, and none was added.

## 5. Network, caching and runtime ✅

| Check | Result |
|---|---|
| DS page data | 320 KB of fetches (DS-level boundaries) vs 79–92 KB at country and district |
| `/_next/static/*` | `public, max-age=31536000, immutable` ✅ |
| HTML pages | `s-maxage=31536000` (CDN may cache for a year; invalidated by redeploy) |
| `/release/*` (boundaries, search index) | `public, max-age=0`: revalidated on every view ❌ |
| `/api/v1/places/*` | `public, max-age=300` |
| Memory, 20 client-side place navigations (0 full reloads) | JS heap 6.2 MB at start, 8.6 MB after the first, then 10.4–12.9 MB; plateau, no steady climb |
| Fly-to frame rate | Not applicable: the map has no fly-to animation (`fitBounds` with `duration: 0`) |
| Lite mode | Not applicable: no lite mode exists in the code (`grep -i lite` finds none) |

## 6. Recommendations, ranked

| # | Change | Expected gain | Status |
|---|---|---|---|
| 1 | Reserve viewport height while place pages stream in | CLS 0.696 → 0 on district, DS and GN pages | **Done in this PR** ✅ |
| 2 | Load MapLibre only when the map scrolls into view, or on a "Show map" tap on mobile | About 280 KB less JS on first load of 6 routes; lower TBT | Follow-up |
| 3 | Serve boundaries as PMTiles or simplified per-level files | DS view data 320 KB → well under 100 KB ❓ | Follow-up (the PMTiles deviation is already recorded) |
| 4 | Version `/release/*` paths (by release id) and cache them `immutable` | Repeat views skip revalidation | Follow-up; depends on hosting |
| 5 | Write the performance budget (W01) and add Lighthouse CI | Regressions caught before merge | Needs lead to confirm numbers |

Proposed budget for the lead to confirm. It is based on these measurements, not on user data ❓:

- LCP ≤ 2.5 s, CLS ≤ 0.1 and TBT ≤ 300 ms, on Lighthouse mobile;
- ≤ 160 KB compressed JS on first load, map excluded;
- the map chunk loaded only when the map is visible;
- ≤ 150 KB of data per view.
