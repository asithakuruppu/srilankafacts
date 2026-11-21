# Rights memo: weighting inputs for the population-weighted grid (G07)

Reviewed 2026-11-21 · Not legal advice. Evidence: catalogue source files (reviewed 2026-11-17), the WorldPop file's `meta.json` and the R2025A release statement (read 2026-11-21).

Tags: ✅ read by us · 🟡 claimed by a source · ❌ not found · ❓ assumption.

## Table

| Input | Held? | Rights on record | Commercial-capable output? | Used as |
|---|---|---|---|---|
| WorldPop R2025A constrained 100 m, 2025 | ✅ held, sha256 `4c781514…f3144` | CC BY 4.0 🟡 (page footer; `licence_note` in `meta.json` ✅). Statement lists GHSL, Google Open Buildings V3 and Microsoft footprints as model inputs ✅; we rely on WorldPop's CC BY grant for its own output, upstream terms not independently checked ❓ | Yes, with attribution | **Weight source** (pattern inside each GN) |
| COD-AB v03 boundaries | ✅ | CC BY-IGO 3.0 (see `cod-ab-lka.md`) | Yes, with attribution | Cell-to-GN assignment |
| Census 2024 GN totals (DCS) | ✅ | **Unclear**; D-030 non-commercial publication position; no reply from DCS | **No** | Totals that are spread over cells; kept out of the weight file |
| Kontur Population H3 (20231101) | ✅ held, not opened | HDX field says CC-BY-4.0 🟡; model uses OSM buildings (ODbL) among others, so share-alike on the derived grid is unclear ❓ | Unclear, so excluded | Not used |
| GHSL built-up and SMOD R2023A | ✅ held | CC BY 4.0 / reuse with acknowledgement 🟡 | Yes | Not used as a weight: it is a built-up mask, not population; WorldPop already folds it in as a covariate |
| Overture buildings 2026-10-21.0 | ✅ held | ODbL (buildings) 🟡; D-005 keeps ODbL-derived outputs apart from CC BY | Only as a separate ODbL database | Not used |
| OpenStreetMap (Geofabrik) | ✅ held | ODbL | Only as a separate ODbL database | Not used |

## Consequence

- The **weight file** (`gn_h3r{9,10}_popweights_2024.parquet`) contains cell shares only. Inputs: WorldPop (CC BY 4.0) and COD-AB (CC BY-IGO). It is commercial-capable with both attributions. No input in it is unclear or non-commercial-only.
- The **apportioned counts** (`…_population_2024_NONCOMMERCIAL.parquet`) multiply those shares by the census GN total, so they inherit D-030: non-commercial, local, not part of any release.
- No weighting input was blocked by rights, so the build went ahead. The remaining blocker for commercial use of *counts* is DCS's reuse terms, not G07.
- Kontur, Overture and OSM are left out because they are unclear or ODbL, not because they are known to be bad. If the lead wants Kontur compared internally, that needs a short memo on its OSM share-alike position first.
