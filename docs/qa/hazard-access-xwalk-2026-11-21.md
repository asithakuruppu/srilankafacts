# QA: crosswalks and indicators for HeiGIT and DesInventar

## HeiGIT accessibility (ISO 3166-2 codes → spine)

- Provinces matched: 9; districts matched: 25.
- Unmatched or ambiguous: 0
- ISO number differs from the p-code suffix for: LK-42 Kilinochchi District → LK45, LK-43 Mannar District → LK42, LK-45 Mullaitivu District → LK44, LK-44 Vavuniya District → LK43

## DesInventar (own province and district codes → spine)

- Provinces matched: 9; districts matched: 25.
- Unmatched or ambiguous: 0
- DS divisions: 328 in the shapefile (2015 file, boundary vintage not stated); not mapped, because the event table carries no DS column and a DS crosswalk would need the 2012-to-2024 succession table (rule 5).

## HeiGIT risk-indicator tables (p-coded)

- p-code check on 9 tables: all codes are spine districts
- Not ingested: the nine tables are derived from other datasets (flood hazard layers, population), each needing its own check (catalogue note); only the Rural Access Index is ingested, by `slf subnational build`.

## HeiGIT accessibility indicators

- Unmatched rows: 0

## DesInventar event records

- Records in the file: 123062.
- Not counted as disasters (epidemic, plague, animal attack, snake bite): 99774.
- Records with no district code: 3.
- Records whose district code is not in the crosswalk: 0 
- Records whose province column disagrees with the district code's province (excluded, both are epidemic records): 2.
- Records matched to a district but with an unparseable date (not counted by year): 120; examples ['1981/2/31', '1985/6/31', '1989/6/31', '2001/4/31', '2001/9/31', '2005/2/29', '2005/2/30', '2006/1/0', '2006/2/29', '2006/6/31', '2007/2/29', '2007/9/31']
- Records matched to a district with a valid year: 122937; years (1965, 2014).

| Event type (as written) | Records matched |
|---|---:|
| EPIDEMIC | 88347 |
| ANIMAL ATTACK | 10808 |
| FLOOD | 6799 |
| FIRE | 3523 |
| STRONG WIND | 2804 |
| RAINS | 2531 |
| DROUGHT | 2198 |
| LANDSLIDE | 2100 |
| GALE | 1430 |
| LIGHTNING | 528 |
| PLAGUE | 423 |
| LAND SUBSIDENCE | 187 |
| FOREST FIRE | 172 |
| CYCLONE | 164 |
| CUTTING FAILURE | 164 |
| SNAKE BITE | 125 |
| TSUNAMI | 89 |
| GROUND VIBRATIO | 82 |
| COASTLINE | 81 |
| EARTH SLIP | 80 |
| URBAN FLOOD | 45 |
| ROCK FALL | 35 |
| SURGE | 33 |
| STRUCTURE | 28 |
| CYCLONE & FLOOD | 28 |
| FLASH FLOOD | 27 |
| HAILSTORM | 20 |
| ACCIDENT | 12 |
| DROWNING | 11 |
| BOAT CAPSIZE | 10 |
| TORNADO | 9 |
| SEDIMENTATION | 9 |
| LEAK OR SPILL | 8 |
| TIDAL WAVE | 7 |
| TREE FALLEN | 7 |
| STORM | 4 |
| FROST | 3 |
| CHEMICAL | 3 |
| RETAINING WF | 2 |
| SUBSIDENCE | 1 |

## Observation rows

| Indicator | Rows | Places | Periods |
|---|---:|---:|---|
| access_hospital_120min | 35 | 35 | 2026 to 2026 (1) |
| access_hospital_30min | 35 | 35 | 2026 to 2026 (1) |
| access_hospital_60min | 35 | 35 | 2026 to 2026 (1) |
| access_primary_care_30min | 35 | 35 | 2026 to 2026 (1) |
| access_primary_care_60min | 35 | 35 | 2026 to 2026 (1) |
| access_school_10km | 35 | 35 | 2026 to 2026 (1) |
| access_school_5km | 35 | 35 | 2026 to 2026 (1) |
| di_disaster_records | 861 | 25 | 1965 to 2014 (42) |
| di_drought_records | 370 | 25 | 1974 to 2014 (41) |
| di_flood_records | 547 | 25 | 1974 to 2014 (41) |
| di_landslide_records | 209 | 15 | 1974 to 2014 (40) |
| di_wind_records | 400 | 25 | 1965 to 2014 (40) |
