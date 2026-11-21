# QA report: DCS vital statistics and mid-year population by district (`dcs-vital-statistics`)

- Observations: 3030 across 35 geographies; periods: 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026
- Generic observation checks: 0 errors, 0 warnings
- Null values (stored `not_available`): 0
- Verification: all rows `machine_extracted`. Geography: joined by the reviewed match file to spine ids (country, province, district)
- Unmatched source units (not in output): 0

## Checks

- ✅ counts cover 25 districts: 25 district ids
- ✅ district counts sum to Sri Lanka: largest difference 0 events
- ✅ rate for both sexes lies between male and female: 0 exceptions []
- ✅ rates cover country, 9 provinces, 25 districts each year: 245 place-years
- ✅ mid-year male + female = total (±1 thousand): 0 exceptions []
- ✅ mid-year districts sum to Sri Lanka (±13 thousand: 25 values rounded to thousands): largest difference 0 thousand (none)
- ✅ mid-year: 26 places in each of 13 years 2014-2026: years 2014-2026, 338 place-years

## Notes

- Mid-year_population_by_district_and_sex_2014_2024.pdf p.1: 26 rows for 2014, 2015, 2016, 2017 (Census 2012 basis)
- Mid-year_population_by_district_and_sex_2014_2024.pdf p.2: 26 rows for 2018, 2019, 2020, 2021 (Census 2012 basis)
- Mid-year_population_by_district_and_sex_2014_2024.pdf p.3: 26 rows for 2022, 2023, 2024 (Census 2012 basis)
- Mid-year_population_by_district_and_sex_2025-2026.pdf p.1: 26 rows for 2025, 2026 (Census 2024 basis)
- Series break: 2014-2024 estimates are on the Census 2012 basis, 2025-2026 on the Census 2024 basis (Sri Lanka 2024: 21,916 thousand; 2025: 21,756 thousand). Do not read the step as a change.
- Counts are by place of occurrence and rates by usual residence: counts / population does not reproduce the printed rates and must not be computed that way.

## Unmatched source units

- none
