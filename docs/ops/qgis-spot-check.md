# Boundary spot-check in QGIS (lead, 1–2 hours)

Purpose: a human look at the geography spine v0 before anything is built on it. You're checking that the boundaries and names look right to someone who knows Sri Lanka, not reviewing code.

## Get the file

In `pipeline/`, run once (downloads COD-AB, ~60 MB, about a minute):

```bash
uv run slf spine build
```

Open `pipeline/data/build/geography-spine/geography_spine_cod-ab-v03.gpkg` in QGIS (drag it onto the map, select all layers). Add a basemap with *XYZ Tiles → OpenStreetMap* in the Browser panel.

Layers: `admin0_country` … `admin4_gn` (one per level) and `label_points` (one point inside every unit).

## What to check (tick and note anything odd)

1. [ ] **Places you know.** Zoom to 3–5 GN divisions you know well (home, work, family). Do the boundaries and English and Sinhala names look right?
2. [ ] **Ampara.** Ampara district (`LK52`) sits in Eastern Province (`LK5`). Select it in `admin2_district` and check the `parent_id` field.
3. [ ] **Islands.** Delft (`LK4142`), Eluvaitivu, Iranaitivu and Palliyawatta exist as separate units. The QA report lists them as having no land neighbours.
4. [ ] **Coast and lagoons.** The GN layer covers about 57 km² less than the country outline (QA report §5). Look along the coast and the big lagoons (Batticaloa, Puttalam, Jaffna) for gaps. Are they water or missing land?
5. [ ] **Duplicate names.** 21 GNs share an English name with another GN in the same DS division (for example two "Sapugasthenna" in `LK1227`). Spot-check two of them: are they genuinely different places?
6. [ ] **DS divisions vs what you expect.** COD-AB has 339 DS units; the commonly cited number is 331. Look for DS "units" that seem to be parts of one division (for example "Sub" divisions). This feeds G02.

## What to send back

A short list: what looked right, what looked wrong (with the `geography_id` from the attribute table), and anything you're unsure about. Corrections go through `overrides/` with evidence; nothing is changed by editing the file.

The full numbers are in [docs/qa/geography-spine-v0.md](../qa/geography-spine-v0.md).
