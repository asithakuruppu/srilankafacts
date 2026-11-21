# QA report: HIES poverty indicators 2019 (`hies-poverty`)

- Observations: 228 across 35 geographies; periods: 2019
- Generic observation checks: 0 errors, 0 warnings
- Null values (stored `not_available`): 0
- Verification: all rows `machine_extracted`. Geography: joined by the reviewed match file to spine ids (country, province, district)
- Unmatched source units (not in output): 0

## Checks

- ✅ row counts: {'country': 1, 'sector': 3, 'province': 9, 'district': 25}
- ✅ sector poor population sums to Sri Lanka (old PL): sum 689,800 vs published 689,800 (tolerance 250)
- ✅ sector poor population sums to Sri Lanka (updated PL): sum 3,042,300 vs published 3,042,300 (tolerance 250)
- ✅ province poor population sums to Sri Lanka (old PL): sum 689,800 vs published 689,800 (tolerance 550)
- ✅ province poor population sums to Sri Lanka (updated PL): sum 3,042,200 vs published 3,042,300 (tolerance 550)
- ✅ district poor population sums to Sri Lanka (old PL): sum 689,800 vs published 689,800 (tolerance 1350)
- ✅ district poor population sums to Sri Lanka (updated PL): sum 3,041,900 vs published 3,042,300 (tolerance 1350)

## Notes

- rows read: 1 country, 3 sector, 9 province, 25 district (expected 1 country, 3 sector, 9 province, 25 district)

## Unmatched source units

- none
