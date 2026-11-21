# QA report: Paddy statistics by district and season (`paddy-statistics`)

- Observations: 250 across 25 geographies; periods: 2010/11-maha, 2012-yala
- Generic observation checks: 0 errors, 0 warnings
- Null values (stored `not_available`): 0
- Verification: all rows `machine_extracted`. Geography: joined by the reviewed match file to spine ids (country, province, district)
- Unmatched source units (not in output): 4

## Checks

- ✅ 2010/11-maha: gross extent sown sums to the PDF's Sri Lanka total: CSV sum 1,804,204.0 vs PDF Sri Lanka 1,804,204 acres (read from the PDF page image)
- ✅ 2012-yala: gross extent sown sums to the PDF's Sri Lanka total: CSV sum 900,795.0 vs PDF Sri Lanka 900,795 acres (read from the PDF page image)

## Notes

- 2010/11-maha: 27 rows in paddy_production_statistics_maha_2011_0.csv; season evidence: paddy_production_statistics_maha_2011.pdf title: '2010/11 MAHA SEASON', final estimate, issued 30 Oct 2011
- 2012-yala: 27 rows in paddy_production_statistics_yala_2012_0.csv; season evidence: paddy_production_statistics_yala_2012.pdf title: '2012 YALA SEASON', final estimate, issued 24 Jan 2013

## Unmatched source units

- 2010/11-maha: 'UDAWALAWE' (csv row 27) is a paddy management area, not a spine place
- 2010/11-maha: 'MAHAWELI' (csv row 28) is a paddy management area, not a spine place
- 2012-yala: 'UDA WALAWE' (csv row 27) is a paddy management area, not a spine place
- 2012-yala: "MAHAWELI 'H'" (csv row 28) is a paddy management area, not a spine place

## Held but not ingested

- department_of_census_and_statistics_paddy_statistics_0.csv: metric units (hectares), no season or year in the file or its name; the DCS title page is not held
- paddy statistics_extent_sown_harvested_(gross & nett)_average_yield_and_production_by_district_maha_season_0.csv: metric units (hectares), no season or year in the file or its name; the DCS title page is not held
- paddy_production_statistics_maha_2010.xls / yala_2010.xls: xls only (no csv); reading .xls needs a new dependency (xlrd), not added
