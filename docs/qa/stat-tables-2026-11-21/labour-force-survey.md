# QA report: Labour Force Survey 2024, district tables (`labour-force-survey`)

- Observations: 546 across 26 geographies; periods: 2024
- Generic observation checks: 0 errors, 0 warnings
- Null values (stored `not_available`): 0
- Verification: all rows `machine_extracted`. Geography: joined by the reviewed match file to spine ids (country, province, district)
- Unmatched source units (not in output): 0

## Checks

- ✅ both: 26 rows (Sri Lanka + 25 districts): 26 rows
- ✅ both: employed+unemployed = labour force; LF + not in LF = population (+/-1: printed counts are rounded): all 26 rows
- ✅ both: districts sum to Sri Lanka (population; +/-25 rounding): sum 17,547,864 vs 17,547,864
- ✅ both: districts sum to Sri Lanka (labour force; +/-25 rounding): sum 8,315,703 vs 8,315,702
- ✅ both: districts sum to Sri Lanka (unemployed; +/-25 rounding): sum 365,952 vs 365,951
- ✅ male: 26 rows (Sri Lanka + 25 districts): 26 rows
- ✅ male: employed+unemployed = labour force; LF + not in LF = population (+/-1: printed counts are rounded): all 26 rows
- ✅ male: districts sum to Sri Lanka (population; +/-25 rounding): sum 8,195,169 vs 8,195,169
- ✅ male: districts sum to Sri Lanka (labour force; +/-25 rounding): sum 5,525,405 vs 5,525,402
- ✅ male: districts sum to Sri Lanka (unemployed; +/-25 rounding): sum 166,848 vs 166,849
- ✅ female: 26 rows (Sri Lanka + 25 districts): 26 rows
- ✅ female: employed+unemployed = labour force; LF + not in LF = population (+/-1: printed counts are rounded): all 26 rows
- ✅ female: districts sum to Sri Lanka (population; +/-25 rounding): sum 9,352,694 vs 9,352,695
- ✅ female: districts sum to Sri Lanka (labour force; +/-25 rounding): sum 2,790,298 vs 2,790,299
- ✅ female: districts sum to Sri Lanka (unemployed; +/-25 rounding): sum 199,100 vs 199,102
- ✅ male + female = both sexes (counts, every row, +/-2 rounding): all rows

## Notes

- text-layer rows reassembled in printed order (checked by the row sums): Kegalle

## Unmatched source units

- none
