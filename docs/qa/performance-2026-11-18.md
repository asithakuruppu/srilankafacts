# Q02 performance check, 2026-11-18 (end of the build-out)

Production build (`next start`, compression on) of `main` at the end of Phases 1 to 8, local preview `v2026.11.17-preview.3` with the full atlas bundle. Headless Chromium, 390 × 844 mobile viewport, network throttled to 1.6 Mbps down / 750 kbps up with 150 ms latency, CPU slowed 4×: a rough stand-in for a low-end phone on a weak 4G signal, not a real device.

| Page | Load event (ms) | Map settled, network idle (ms) | Data at load (KB) | Data when settled (KB) |
|---|---:|---:|---:|---:|
| `/` | 2,019 | 17,691 | 325 | 3,223 |
| `/?place=LK1103005` | 1,971 | 43,710 | 325 | 8,466 |
| `/?place=LK23&lens=landscape` | 1,971 | 41,053 | 325 | 7,878 |
| `/area` | 1,881 | 7,479 | 300 | 1,087 |
| `/query` | 1,760 | – | 277 | – |
| `/about` | 1,835 | – | 297 | – |
| `/indicators` | 1,785 | – | 300 | – |
| `/data/calendar` | 1,748 | – | 283 | – |
| `/elections` | 1,742 | – | 275 | – |
| `/explore` | 1,833 | – | 304 | – |

## Findings

- Every page reaches its load event in about 2 s and transfers about 300 KB first ✅.
- **The atlas map is slow on this profile**: 17.7 s and 3.2 MB to a settled country view; **selecting a GN takes about 44 s and 8.5 MB**, mostly the district's detail geometry (up to 3.8 MB per district before compression), the GN values of the indicator and the landscape or feature files ❌.
- `/area` settles in 7.5 s (1.1 MB); the grid files load only when an area is drawn.
- `/query` loads the 33 MB DuckDB engine only when a query is run.

## What would help (not done)

PMTiles or vector tiles for GN geometry (G04), splitting GN values by district, lazy loading of features and landscape values per district, and a service worker cache. The budget is still not agreed (2026-11-12 §6).
