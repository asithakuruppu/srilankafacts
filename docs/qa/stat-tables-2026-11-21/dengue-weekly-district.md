# QA report: Dengue weekly reports by district (RDHS) (`dengue-weekly-district`)

- Observations: 520 across 26 geographies; periods: 2026-W27, 2026-W28, 2026-W29, 2026-W30, 2026-W31, 2026-W32, 2026-W33, 2026-W34, 2026-W35, 2026-W36, 2026-W37, 2026-W38, 2026-W39, 2026-W40, 2026-W41, 2026-W42, 2026-W43, 2026-W44, 2026-W45, 2026-W46
- Generic observation checks: 0 errors, 0 warnings
- Null values (stored `not_available`): 0
- Verification: all rows `machine_extracted`. Geography: joined by the reviewed match file to spine ids (country, province, district)
- Unmatched source units (not in output): 0

## Checks

- ✅ week 27 (revised): districts sum to the printed total: sum 7,891 vs total 7,891
- ✅ week 28 (revised): districts sum to the printed total: sum 7,619 vs total 7,619
- ✅ week 29 (revised): districts sum to the printed total: sum 7,352 vs total 7,352
- ✅ week 30 (revised): districts sum to the printed total: sum 6,004 vs total 6,004
- ✅ week 31 (revised): districts sum to the printed total: sum 4,387 vs total 4,387
- ✅ week 32 (revised): districts sum to the printed total: sum 3,254 vs total 3,254
- ✅ week 33 (revised): districts sum to the printed total: sum 2,613 vs total 2,613
- ✅ week 34 (revised): districts sum to the printed total: sum 1,802 vs total 1,802
- ✅ week 35 (revised): districts sum to the printed total: sum 1,295 vs total 1,295
- ✅ week 36 (revised): districts sum to the printed total: sum 1,152 vs total 1,152
- ✅ week 37 (revised): districts sum to the printed total: sum 1,156 vs total 1,156
- ✅ week 38 (revised): districts sum to the printed total: sum 1,276 vs total 1,276
- ✅ week 39 (revised): districts sum to the printed total: sum 1,216 vs total 1,216
- ✅ week 40 (revised): districts sum to the printed total: sum 1,239 vs total 1,239
- ✅ week 41 (revised): districts sum to the printed total: sum 1,223 vs total 1,223
- ✅ week 42 (revised): districts sum to the printed total: sum 1,111 vs total 1,111
- ✅ week 43 (revised): districts sum to the printed total: sum 1,398 vs total 1,398
- ✅ week 44 (revised): districts sum to the printed total: sum 1,324 vs total 1,324
- ✅ week 45 (revised): districts sum to the printed total: sum 1,410 vs total 1,410
- ✅ week 46 (provisional): districts sum to the printed total: sum 1,888 vs total 1,888

## Notes

- 20 weekly reports (weeks 27-46 of 2026). Week n is read from the next report's previous-week column when held (19 weeks, status revised), else from its own report (week 46, provisional). Revisions: 155 area-week values differ between first report and the next report; later weeks' counts rise as late notifications arrive.
- Not stored: the 2025 columns and the cumulative 'up to week' columns (their start dates are not stated). Ampara and Kalmunai RDHS rows are not separate places in the spine; Ampara district (LK52) is their sum.

## Unmatched source units

- none
