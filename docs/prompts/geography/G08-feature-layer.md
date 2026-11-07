# G08: Feature layer v1 (buildings, landmarks, land cover)

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 2 | Geography | 1 | 2026-11-07 | draft |

## When to use
Stage 2, after the legal checks on map publication and ODbL aggregates (see `docs/vision/organisation-and-business-model.md` §7). Brings the physical atom (individual features) into the platform. Shares the completeness work with G07.

## Read first
- `AGENTS.md` (especially rules 4, 11 and 13)
- `docs/architecture/multi-scale-features.md` (all)
- `docs/decisions/decision-log.md` D-005, D-016, D-017
- G07 completeness report, if it exists

## Inputs (fill in)
```
FEATURE_CLASSES: buildings, places, landcover     # each must pass the admission test first
BUILDING_CANDIDATES: overture_buildings, osm, microsoft, google_open_buildings
PLACES_CANDIDATES: overture_places, osm, wikidata
PARTITION: district
```

## Task
1. **Admission test** per class, written to `docs/research/features/{class}-admission.md`: the question it answers and for whom, rights (R02 pattern), measured coverage and completeness, update source. Stop for the lead's approval before ingesting a class.
2. **Coverage check** for every candidate. Confirm whether it covers Sri Lanka at all (Microsoft and Google coverage are unconfirmed ❓). Record evidence.
3. **Completeness:** compare building counts per GN with Census 2024 occupied housing units; map where each source is weak. Rank candidates. For places, sample-check 100 landmarks per source against a known list.
4. **Ingest** the approved sources through snapshot → extract → harmonise. Prefer Overture's conflated buildings and its GERS IDs; write other source IDs to `features/codes/`. **Physical attributes only**: drop any personal or owner fields at extract, and log that they were dropped.
5. **Resolve** every feature to its GN, DS, district, province and, where available, LA, MOH and electorate (point-in-polygon on a representative point; record the boundary vintage; flag features on borders).
6. **Roll-ups** per GN: building count, density, footprint area distribution, landmarks by category, land-cover shares. Written as observations with `data_nature` set correctly and the source licence recorded (ODbL where OSM-derived).
7. **Tiles:** feature PMTiles for zoom 13–16, one layer per class, `feature_id` as the feature ID, minimal properties.
8. **Measure compute:** report run time, memory and disk for the full island; recommend where heavy builds should run (CI or a larger machine).

## Constraints
- Never attach statistics about people to individual features; never publish owner, claimant or occupant data.
- No extra detail on military, security or critical-infrastructure sites beyond the source.
- Don't conflate sources yourself if Overture already provides the conflated layer; propose it first if you think it's needed.
- Licence per output file; ODbL layers kept apart from CC BY outputs.

## Verify (show real output)
- Feature counts per class and source; share resolved to a GN; unresolved list.
- Completeness table and weak-area map.
- 20 random buildings and 20 random landmarks with their resolved geographies, for the lead to eyeball in QGIS.
- Compute measurements.

## Deliverables
Admission notes, feature GeoParquet by district, feature code crosswalk, GN roll-up observations, PMTiles, QA report.

## Done when
A user can zoom into any GN and see its buildings and landmarks, and the GN's profile includes feature roll-ups with sources and licences.

Report using the format in `AGENTS.md`.
