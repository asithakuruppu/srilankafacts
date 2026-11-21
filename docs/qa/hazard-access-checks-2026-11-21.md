# QA: cross-checks of the HeiGIT and DesInventar indicators

Built by `uv run slf hazard-access checks`. A check reports a size or a pass; it never changes a value. “Independent” means the comparison figure does not come from the source being checked.

| Check | Independent | Result |
|---|---|---|
| heigit-population-vs-census-2024 | yes | largest district difference 42.0% |
| heigit-composites-are-joins | no | identical |
| heigit-access-counts-vs-shares | no | share differs by up to 20.3 percentage points; people count by up to 216.3% |
| heigit-flood-exposure-logic | no | no violations |
| osm-education-vs-giga-schools | yes | OSM 5,047 against Giga 10,112 schools; district ratio 0.16 to 1.44, median 0.40 |
| osm-hospitals-vs-healthsites | no | HeiGIT 904 against healthsites 905; district ratio 0.92 to 1.08, median 1.00 |
| desinventar-ds-within-district | no | holds in every district-year |
| desinventar-tsunami-2004-deaths | yes | deaths 30,959 against 30,959; missing 1,908 against 5,443 |

## heigit-population-vs-census-2024

HeiGIT district population (WorldPop, modelled) against the Census 2024 district figure in the release

**Result:** largest district difference 42.0%

- `total_pop` against census `population_total`: 25 districts; sum 23,090,430 against 21,781,800 (+6.0%); district difference -20.6% to +42.0%, median +5.1%; beyond ±10%: {'LK11': -20.6, 'LK12': 13.0, 'LK13': 14.6, 'LK22': -15.9, 'LK31': 14.7, 'LK32': -16.2, 'LK42': -17.1, 'LK51': -16.9, 'LK52': 23.8, 'LK61': 21.8, 'LK71': 24.0, 'LK82': 42.0, 'LK91': 24.2, 'LK92': -12.4}
- `female_pop` against census `population_female`: 25 districts; sum 11,887,542 against 11,269,456 (+5.5%); district difference -21.4% to +40.8%, median +2.5%; beyond ±10%: {'LK11': -21.4, 'LK12': 12.4, 'LK13': 14.3, 'LK22': -15.5, 'LK31': 15.1, 'LK32': -16.1, 'LK42': -18.8, 'LK51': -18.6, 'LK52': 21.2, 'LK61': 21.7, 'LK71': 23.0, 'LK82': 40.8, 'LK91': 23.5, 'LK92': -12.2}
- `pop_u15` against census `population_age_0_14`: 25 districts; sum 4,737,800 against 4,506,839 (+5.1%); district difference -19.6% to +32.2%, median +5.6%; beyond ±10%: {'LK11': -16.9, 'LK12': 14.7, 'LK13': 14.0, 'LK22': -19.3, 'LK31': 13.6, 'LK32': -19.6, 'LK42': -17.9, 'LK44': 12.3, 'LK45': 26.6, 'LK51': -12.4, 'LK52': 18.4, 'LK61': 16.1, 'LK71': 20.2, 'LK82': 32.2, 'LK91': 18.9, 'LK92': -14.0}
- `elderly` against census `population_age_65_plus`: 25 districts; sum 3,042,966 against 2,737,814 (+11.1%); district difference -20.2% to +41.8%, median +10.3%; beyond ±10%: {'LK11': -13.3, 'LK12': 18.7, 'LK13': 35.2, 'LK21': 13.9, 'LK22': -14.6, 'LK23': 10.3, 'LK31': 34.4, 'LK41': 11.8, 'LK42': -20.2, 'LK44': -11.2, 'LK51': -18.0, 'LK52': 27.4, 'LK53': 10.9, 'LK61': 20.2, 'LK71': 13.4, 'LK81': 12.9, 'LK82': 41.8, 'LK91': 31.4}

## heigit-composites-are-joins

The `coping` and `vulnerability` tables against the tables HeiGIT says they combine

**Result:** identical

- coping = access + facilities + evacuability + rai: 43 of 44 columns compared, largest absolute difference 0; columns not found in the parts: none
- vulnerability = demographics + rural_population: 19 of 20 columns compared, largest absolute difference 0; columns not found in the parts: none

## heigit-access-counts-vs-shares

People within 30 minutes of a hospital: the risk-indicator count table against the accessibility table, joined by the reviewed ISO crosswalk

**Result:** share differs by up to 20.3 percentage points; people count by up to 216.3%

- 25 districts joined; share gap median 3.69 points
- people counts: risk table 21,470,512, accessibility table 17,850,813
- Differences are expected if the two products used different population grids or routing runs; HeiGIT does not say. Large gaps are listed in the report.
- LK21: share 95.4% against 99.0%
- LK22: share 87.5% against 96.4%
- LK23: share 85.7% against 94.4%
- LK32: share 96.1% against 99.7%
- LK43: share 94.5% against 98.7%
- LK44: share 86.8% against 96.0%
- LK51: share 93.0% against 96.3%
- LK52: share 86.1% against 93.1%
- LK53: share 84.4% against 96.4%
- LK62: share 93.4% against 96.2%
- LK71: share 85.7% against 92.7%
- LK72: share 77.7% against 91.8%
- LK81: share 90.1% against 96.9%
- LK82: share 64.9% against 85.2%
- LK91: share 86.8% against 97.0%
- LK92: share 94.1% against 98.4%

## heigit-flood-exposure-logic

Flood exposure by return period: non-decreasing from 10 to 500 years; exposed facilities not above the district's facilities; shares within 0 to 100

**Result:** no violations


## osm-education-vs-giga-schools

OpenStreetMap educational facilities (HeiGIT) against Giga's school point list, by district (point in district)

**Result:** OSM 5,047 against Giga 10,112 schools; district ratio 0.16 to 1.44, median 0.40

- Different definitions: OSM counts any mapped education feature (including universities, kindergartens and tuition centres), Giga lists schools.
- Giga points outside every district polygon: 34

## osm-hospitals-vs-healthsites

OpenStreetMap hospitals (HeiGIT) against healthsites.io hospitals (also OSM-derived), by district

**Result:** HeiGIT 904 against healthsites 905; district ratio 0.92 to 1.08, median 1.00

- healthsites.io is itself extracted from OpenStreetMap, so this is a consistency check between two extractions, not an independent count.

## desinventar-ds-within-district

DesInventar record counts: the sum over DS divisions never exceeds the district count for the same hazard and year

**Result:** holds in every district-year


## desinventar-tsunami-2004-deaths

Deaths recorded for the 26 December 2004 tsunami in DesInventar, summed over its 89 TSUNAMI records dated 2004, against the national figure in the ADRC Annual Disaster Report 2004, Sri Lanka chapter (page 1 of 6-2.pdf, read 2026-11-21): 30,959 deaths and 5,443 missing, which it attributes to UN/OCHA, 4 February 2005

**Result:** deaths 30,959 against 30,959; missing 1,908 against 5,443

- Source: https://web.adrc.asia/publications/annual/04/04eng/pdf/6-2.pdf
- The deaths figure is identical, which suggests both trace to the same government tally, so it confirms transcription rather than the count itself.
- The missing figure differs: DesInventar holds fewer than the report. People missing are not used by any indicator here.
