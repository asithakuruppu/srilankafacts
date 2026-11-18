# Review queue after the autonomous build-out, 2026-11-18

On 2026-11-17 the lead asked for every coding stage of the roadmap to be built, following the agents' recommended decisions, with all review and manual checking moved to the end. This is that end: one list of what now waits for a person. Nothing here is published; everything runs in the local preview.

**How to use it:** work top to bottom. Each item says what to look at and the agent's recommendation. Record outcomes in `docs/decisions/lead-approvals-log.md` (approvals) or the decision log (status changes).

## 1. Decisions acted on, awaiting confirmation

| Decision | What it did | Recommendation | Main thing to check |
|---|---|---|---|
| D-043 | Release boundaries simplified as a coverage: 0 overlaps at every level except the provisional unit | Accept | `admin4.geojson` grew from 11.8 to 16.1 MB |
| D-044 | Open spatial layers rolled up to every place as modelled estimates (other session) | Accept, after the licence review in §3 | Indicator list and licences |
| D-045 | Landscape space v0.1 recipe | Accept for preview | Machine-drafted axis names |
| D-046 | Elections lens at ED level; LA and MOH wait for an official GN list | Accept | Whether turnout maps are acceptable under D-039 |
| D-047 | Typology, trajectory (private), composite weights, text search, two-map explorer | Accept with renamed types | **Three of five type names lead with ethnic group or religion.** Rename or approve |
| D-048 | H3 r9 grid, equal-share weights, `/area` and point resolver | Accept; plan population weights (G07 steps 1–4) | Equal shares misplace people inside mixed GNs |
| D-049 | Landscape lens on real layers; named features drawn locally only | Accept for preview; keep features out of releases | Feature names come from open registries |
| D-050 | Stage 3 indicators (OPHI, WFP, HeiGIT), release calendar, opt-in draft translations | Accept | Survey and modelled values sit next to census ones; labels must keep them apart |
| D-051 | Local MCP server, private eval set, embed map, SQL in the browser | Accept | Three new dependencies; site grows by about 46 MB |
| D-052 | Events layer (2025 floods, fires, storms); no live feeds, no Movement | Accept | Flood shares are lower bounds |
| D-042 | Map-first atlas home (recorded Accepted on 2026-11-17 on the lead's instruction) | Keep | Confirm in the approvals log |

## 2. Wording and labels written by machine

- Typology type names (5), landscape and profile axis names: `docs/qa/typology-v1.0.md`, `docs/qa/landscape-2026-11-17.md`, `docs/qa/profile-space-v0.3.md`.
- Sinhala and Tamil interface drafts (25 strings each): `docs/translation/request-si.csv`, `request-ta.csv`. They show only when a visitor opts in, under a banner. Needs a translator per D-012.
- All panel, legend and page wording added in Phases 1 to 8 (neutral-tone check, especially Elections and the typology).

## 3. Rights and licences

| Item | Status | Recommendation |
|---|---|---|
| Census 2024 (DCS) | D-030 non-commercial; no reply from DCS | Unchanged; blocks the CC BY evaluation set |
| Census history (2012 mirror) | Private under D-038 | Decide whether to extend D-030; the Change lens and trajectory stay private until then |
| Copernicus DEM | Catalogue says "public licence", commercial use unknown | Record the licence text and evidence |
| healthsites.io (ODbL), HeiGIT (CC BY-SA), UNOSAT (CC BY-SA) | Share-alike | Decide whether share-alike outputs may sit in releases |
| Overture places (CDLA) and buildings (ODbL) | Counts only | Keep counts only |
| nuuuwan gig-data (LA and MOH) | No licence | Ask for an official GN list per LA and MOH area |
| A02 evaluation set | Kept local | Publish only when DCS terms allow |

## 4. Data checks only a person can do

- Q01: make the lead sheet a full pass (still provisional, LA-002). The machine re-trace of `v2026.11.17-preview.3` passed: 207 values and 1,471 topic values, 0 failures; Final Report 61/61 (`docs/qa/accuracy-audit-v2026.11.17-preview.3.md`).
- Spot-check five flood shares against Disaster Management Centre reports, and 2025 rainfall against the Department of Meteorology (`docs/methods/events.md`, `docs/methods/subnational.md`).
- Name 5 places to judge similar-place lists (open under LA-003).
- 42 DCS crosswalk items and Kalmunai (DCS 5224) (unchanged).
- Some Sinhala and Tamil district names in the spine look cut short (for example "නුවරඑළිය දිස්ත්‍ර", "நுவரேலியா மாவட்டம"); check against the source.

## 5. Product and design review

- The whole atlas on a real phone and in Safari and Firefox (only headless Chromium was used).
- Performance: on a throttled phone profile the atlas settles in 17.7 s and a GN selection takes about 44 s (`docs/qa/performance-2026-11-18.md`). Decide the budget, then PMTiles (G04).
- Accessibility: contrast, keyboard use of the map and area tool, screen readers (`docs/qa/accessibility-2026-11-18.md`).
- Screenshots of every new view: `docs/qa/screenshots/*-2026-11-18-*.png`.

## 6. Outward-facing steps left to the lead (agents may not do these)

- Hosting (Vercel and R2 are set up but nothing is deployed); the atlas bundle is now about 70 MB uncompressed plus 46 MB for SQL.
- A "report a problem" channel (set `NEXT_PUBLIC_REPORT_URL`).
- A scheduled alert workflow for new source editions (D-050).
- Translators, a GIS reviewer, letters to DCS (2012 GN file, reuse terms) and for official LA and MOH GN lists.

## 7. Not built, and why

| Roadmap item | Why not |
|---|---|
| LA and MOH profiles | No official GN list with rights (D-046) |
| `/si` and `/ta` routes, translated indicator names | No reviewed translation (D-012) |
| HIES poverty, LFS labour, school census, health bulletin, dengue, paddy, CBSL strip | No tables held |
| DesInventar and HeiGIT travel-time indicators | Names and ISO codes only; need crosswalks (rule 5) |
| Population-weighted grid, resolution 10 | G07 completeness and rights work first |
| Building shapes, canopy, biomass, `form` and `context` spaces | Data held only as counts or not processed |
| Chart embeds, hosted MCP endpoint, newsletter | Hosting and outward actions |
| Live feeds, Movement (trains, aircraft) | No scheduler by policy; no timetable data |
| Dynamic API (S01), paid pilot (S02), partnerships | Triggered by real demand, or the lead's work |
