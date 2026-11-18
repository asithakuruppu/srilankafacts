# Method: events layer and place timelines

Status: **local preview, 2026-11-18** · Decision: D-052 (Proposed) · Code: `pipeline/slf/events.py` (`uv run slf events`)

Legend: ✅ verified directly · 🟡 from a secondary source · ❌ not found · ❓ assumption.

| Layer | Source | Places | Period | Method |
|---|---|---|---|---|
| Area and share flooded | UNOSAT multi-sensor flood extent, FL20251128LKA (CC BY-SA per HDX) | every level to GN | 26 Nov to 2 Dec 2025 | Flood polygons (99,373 parts, permanent water excluded by UNOSAT) indexed and intersected with each GN polygon in EPSG:5235; summed up the hierarchy |
| Fire detections | NASA FIRMS, VIIRS S-NPP archive | DS, district, province, country | each complete year 2013 to 2025 | Type 0 (presumed vegetation fire), confidence nominal or high, point in GN polygon |
| Fire detections (long record) | NASA FIRMS, MODIS Terra and Aqua C6.1 archive | DS, district, province, country | each complete year 2001 to 2025 | Type 0, confidence 30 or more, 1 km pixel, point in GN polygon; separate indicator `fire_detections_modis` |
| Storm passes | IBTrACS v04r01 (track points around Sri Lanka) | district | 1842 to 2026 (panel shows since 1950) | Track line within 50 km of the district boundary; highest WMO wind reported at track points in that zone |

## Checks

- Flooded area inside GN divisions: 4,119 km² (6.24% of land); UNOSAT's own polygon area is 4,134 km² ✅, the rest offshore or in boundary gaps.
- Highest flooded shares by district: Trincomalee 14.4%, Batticaloa 14.2%, Kilinochchi 13.5%, Mullaitivu 11.2%, Jaffna 10.7% ✅ (computed; not compared with DMC reports ❌).
- Fire detections per year nationally: 3,570 (2021) to 10,187 (2016) ✅ (computed).
- MODIS and VIIRS national yearly counts move together over 2013-2025 (correlation 0.95, Spearman 0.93; computed) ✅; the counts themselves differ because pixels (1 km against 375 m) and sensors differ, so they are never added or compared as levels. MODIS gives 1,012 to 1,786 detections a year in 2004-2012 and 506 to 1,356 in 2013-2025.
- 407 storm passes across 25 districts; Ditwah (IBTrACS 2025331N06083) passes Trincomalee and Batticaloa on 27 Nov 2025 ✅.

## Limits

Floods: cloud and tree cover hide flooding, so shares are lower bounds; the landslide layer is not used. Fires: detections are hot 375 m (VIIRS) or 1 km (MODIS) pixels; MODIS Terra and Aqua are combined and the archive is standard quality to 2026-08-30 (2026 is not a complete year and is left out); cloud cover and overpass times miss some; year-to-year swings follow weather. Storms: early records lack wind; 50 km is a fixed choice, not an impact zone.
