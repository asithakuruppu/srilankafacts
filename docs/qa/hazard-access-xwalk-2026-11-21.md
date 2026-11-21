# QA: crosswalks and indicators for HeiGIT and DesInventar

## HeiGIT accessibility (ISO 3166-2 codes → spine)

- Provinces matched: 9; districts matched: 25.
- Unmatched or ambiguous: 0
- ISO number differs from the p-code suffix for: LK-42 Kilinochchi District → LK45, LK-43 Mannar District → LK42, LK-45 Mullaitivu District → LK44, LK-44 Vavuniya District → LK43

## DesInventar (own province and district codes → spine)

- Provinces matched: 9; districts matched: 25.
- Unmatched or ambiguous: 2
  - lka005001012 Eravu Pattu(Chenkalady) (Batticaloa): no DS code match and no same-name DS in the district
  - lka005001033 Porathivu Pattu(Ellavul) (Batticaloa): no DS code match and no same-name DS in the district
- DS divisions: 328 in DesInventar's 2015 shapefile; 309 matched, 17 to review, 2 unmatched (listed below).
- To review, not mapped: 17
  - lka005002034 Eragama (Ampara): DCS code 5234 is LK5234 'Irakkamam' but the names differ (similarity 0.62); renamed or reassigned code, not mapped
  - lka001001015 Hanwella (Colombo): DCS code 1115 is LK1115 'Seethawaka' but the names differ (similarity 0.44); renamed or reassigned code, not mapped
  - lka003001027 Baddegama (Galle): lands on LK3127 'Baddegama', created by a 2012 to 2024 split; the old unit's events cannot be assigned to one part, not mapped
  - lka003001036 Hikkaduwa (Galle): lands on LK3136 'Hikkaduwa', created by a 2012 to 2024 split; the old unit's events cannot be assigned to one part, not mapped
  - lka006001048 Katupotha (Kurunegala): DCS code 6148 is LK6148 'Panduwasnuwara East' but the names differ (similarity 0.15); renamed or reassigned code, not mapped
  - lka006001024 Mahawa (Kurunegala): DCS code 6124 is LK6124 'Maho' but the names differ (similarity 0.60); renamed or reassigned code, not mapped
  - lka002002021 Ambanganga Korale (Matale): DCS code 2221 is LK2221 'Ambanganga' but the names differ (similarity 0.77); renamed or reassigned code, not mapped
  - lka002002024 Laggala-Pallegama (Matale): DCS code 2224 is LK2224 'Laggala' but the names differ (similarity 0.61); renamed or reassigned code, not mapped
  - lka002003015 Ambagamuwakorale (Nuwara Eliya): lands on LK2315 'Ambagamuwa Korale', created by a 2012 to 2024 split; the old unit's events cannot be assigned to one part, not mapped
  - lka002003006 Hanguranketha (Nuwara Eliya): lands on LK2306 'Hanguranketa', created by a 2012 to 2024 split; the old unit's events cannot be assigned to one part, not mapped
  - lka002003003 Kothmale (Nuwara Eliya): lands on LK2303 'Kothmale East', created by a 2012 to 2024 split; the old unit's events cannot be assigned to one part, not mapped
  - lka002003012 Nuwara Eliya (Nuwara Eliya): lands on LK2312 'Nuwara Eliya', created by a 2012 to 2024 split; the old unit's events cannot be assigned to one part, not mapped
  - lka002003009 Walapane (Nuwara Eliya): lands on LK2324 'Walapane', created by a 2012 to 2024 split; the old unit's events cannot be assigned to one part, not mapped
  - lka006002018 Mundalama (Puttalam): DCS code 6218 is LK6218 'Mundel' but the names differ (similarity 0.67); renamed or reassigned code, not mapped
  - lka009001018 Balangoda (Ratnapura): lands on LK9118 'Balangoda', created by a 2012 to 2024 split; the old unit's events cannot be assigned to one part, not mapped
  - lka005003033 Verugal/Eachchalampattai (Trincomalee): DCS code 5333 is LK5333 'Verugal' but the names differ (similarity 0.47); renamed or reassigned code, not mapped
  - lka005003021 Kanthalai (Trincomalee): DCS code 5321 is LK5321 'Kantale' but the names differ (similarity 0.75); renamed or reassigned code, not mapped

## HeiGIT risk-indicator tables (p-coded)

- p-code check on 9 tables: all codes are spine districts
- Ingested: demographics (5), rural share, OSM hospitals and primary care counts, evacuation times (8) and flood exposure (28); the checks report covers each group. Not ingested: educational-facility counts (OSM holds about 40% of Giga's school list in the median district), the `access` counts (two HeiGIT products disagree by up to 20 points), `coping` and `vulnerability` (identical joins of other tables) and the per-group RAI columns (only RAI_total_pop, by `slf subnational build`).

## HeiGIT accessibility indicators

- Unmatched rows: 0

## DesInventar event records

- Records in the file: 123062.
- Not counted as disasters (epidemic, plague, animal attack, snake bite): 99774.
- Records with no district code: 3.
- Records whose district code is not in the crosswalk: 0 
- Records whose province column disagrees with the district code's province (excluded, both are epidemic records): 2.
- Records matched to a district but with an unparseable date (not counted by year): 120; examples ['1981/2/31', '1985/6/31', '1989/6/31', '2001/4/31', '2001/9/31', '2005/2/29', '2005/2/30', '2006/1/0', '2006/2/29', '2006/6/31', '2007/2/29', '2007/9/31']
- DS division level: 34707 matched records carry a DS code; 32205 reach a spine DS; 0 contradict their district (excluded); 2502 carry a DS code not mapped (22 codes, counted at district level only): {'lka009001018': 419, 'lka006001024': 415, 'lka002003012': 261, 'lka002002024': 204, 'lka002003009': 164, 'lka002003015': 138, 'lka005001033': 138, 'lka002003003': 121, 'lka002003006': 112, 'lka006002018': 87, 'lka005003021': 82, 'lka005002034': 79, 'lka005001012': 62, 'lka001001015': 46, 'lka003001027': 42}
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
| di_disaster_records | 5503 | 334 | 1965 to 2014 (42) |
| di_drought_records | 1432 | 271 | 1974 to 2014 (41) |
| di_flood_records | 2711 | 330 | 1974 to 2014 (41) |
| di_landslide_records | 773 | 146 | 1974 to 2014 (40) |
| di_wind_records | 1711 | 328 | 1965 to 2014 (40) |
| evac_minutes_mean_rp10 | 25 | 25 | 2026 to 2026 (1) |
| evac_minutes_mean_rp100 | 25 | 25 | 2026 to 2026 (1) |
| evac_minutes_mean_rp50 | 25 | 25 | 2026 to 2026 (1) |
| evac_minutes_mean_rp500 | 25 | 25 | 2026 to 2026 (1) |
| evac_minutes_median_rp10 | 25 | 25 | 2026 to 2026 (1) |
| evac_minutes_median_rp100 | 25 | 25 | 2026 to 2026 (1) |
| evac_minutes_median_rp50 | 25 | 25 | 2026 to 2026 (1) |
| evac_minutes_median_rp500 | 25 | 25 | 2026 to 2026 (1) |
| flood_rp100_crops_km2 | 25 | 25 | 2026 to 2026 (1) |
| flood_rp100_crops_share | 25 | 25 | 2026 to 2026 (1) |
| flood_rp100_hospitals | 25 | 25 | 2026 to 2026 (1) |
| flood_rp100_pop_65plus | 25 | 25 | 2026 to 2026 (1) |
| flood_rp100_pop_female | 25 | 25 | 2026 to 2026 (1) |
| flood_rp100_pop_under5 | 25 | 25 | 2026 to 2026 (1) |
| flood_rp100_primary_care | 25 | 25 | 2026 to 2026 (1) |
| flood_rp10_crops_km2 | 25 | 25 | 2026 to 2026 (1) |
| flood_rp10_crops_share | 25 | 25 | 2026 to 2026 (1) |
| flood_rp10_hospitals | 25 | 25 | 2026 to 2026 (1) |
| flood_rp10_pop_65plus | 25 | 25 | 2026 to 2026 (1) |
| flood_rp10_pop_female | 25 | 25 | 2026 to 2026 (1) |
| flood_rp10_pop_under5 | 25 | 25 | 2026 to 2026 (1) |
| flood_rp10_primary_care | 25 | 25 | 2026 to 2026 (1) |
| flood_rp500_crops_km2 | 25 | 25 | 2026 to 2026 (1) |
| flood_rp500_crops_share | 25 | 25 | 2026 to 2026 (1) |
| flood_rp500_hospitals | 25 | 25 | 2026 to 2026 (1) |
| flood_rp500_pop_65plus | 25 | 25 | 2026 to 2026 (1) |
| flood_rp500_pop_female | 25 | 25 | 2026 to 2026 (1) |
| flood_rp500_pop_under5 | 25 | 25 | 2026 to 2026 (1) |
| flood_rp500_primary_care | 25 | 25 | 2026 to 2026 (1) |
| flood_rp50_crops_km2 | 25 | 25 | 2026 to 2026 (1) |
| flood_rp50_crops_share | 25 | 25 | 2026 to 2026 (1) |
| flood_rp50_hospitals | 25 | 25 | 2026 to 2026 (1) |
| flood_rp50_pop_65plus | 25 | 25 | 2026 to 2026 (1) |
| flood_rp50_pop_female | 25 | 25 | 2026 to 2026 (1) |
| flood_rp50_pop_under5 | 25 | 25 | 2026 to 2026 (1) |
| flood_rp50_primary_care | 25 | 25 | 2026 to 2026 (1) |
| heigit_pop_65plus | 25 | 25 | 2026 to 2026 (1) |
| heigit_pop_female | 25 | 25 | 2026 to 2026 (1) |
| heigit_pop_total | 25 | 25 | 2026 to 2026 (1) |
| heigit_pop_under15 | 25 | 25 | 2026 to 2026 (1) |
| heigit_pop_under5 | 25 | 25 | 2026 to 2026 (1) |
| heigit_rural_share | 25 | 25 | 2026 to 2026 (1) |
| osm_hospitals_count | 25 | 25 | 2026 to 2026 (1) |
| osm_primary_care_count | 25 | 25 | 2026 to 2026 (1) |
