# Method: Stage 3 sub-national indicators (p-coded open tables)

Status: **local preview, 2026-11-18** · Decision: D-050 (Proposed) · Code: `pipeline/slf/subnational.py` (`uv run slf subnational build`) · QA: [subnational-2026-11-18.md](../qa/subnational-2026-11-18.md)

Legend: ✅ verified directly · 🟡 from a secondary source · ❌ not found · ❓ assumption.

## Sources

| Indicator group | Dataset | Level | Period | Nature | Licence (catalogue) |
|---|---|---|---|---|---|
| Multidimensional poverty (5 indicators) | `ophi-mpi` | country, province | 2016 (SLDHS) | survey estimate | CC0-1.0 |
| Rainfall: year, normal, anomaly | `wfp-chirps-rainfall-subnational` | country, province, district | latest complete year (2025) | modelled estimate (satellite and gauges) | CC-BY-4.0 |
| Vegetation (NDVI): year, normal, anomaly | `wfp-ndvi-subnational` | country, province, district | latest complete year (2025) | modelled estimate (MODIS) | CC-BY-4.0 |
| Rural Access Index | `heigit-risk-indicators` | district | 2026 (HeiGIT publication) | modelled estimate | CC BY-SA (source entry) |

## How

1. **Join by id.** Every table carries OCHA p-codes (`LK1`…`LK9`, `LK11`…`LK92`), the spine's own ids. A code missing from the spine is listed as unmatched (none in this build ✅).
2. **OPHI and HeiGIT** values are copied cell by cell; each row's `source_locator` names the file, row and column.
3. **Rainfall and NDVI.** The latest year with all 36 ten-day values for all 25 districts is used. Rainfall: the year's total is the sum of the 36 values of `rfh`; the normal is the sum of `rfh_avg`; the anomaly is total ÷ normal − 1. NDVI: the mean of the 36 values of `vim` and of `vim_avg`. Province values are WFP's own province rows. The country value is the district values weighted by WFP's pixel counts, a derived mean.
4. **Information floor.** Rainfall `grid-5km` (CHIRPS), NDVI `grid-250m` (MODIS), RAI `grid-100m` (WorldPop and OSM roads), MPI `province (survey sample)`: a province value from a sample survey, with sampling error not given in the held file ❓.

## Checks

- 285 rows, 12 indicators, 0 unmatched codes ✅.
- 2025 rainfall: 1,361 to 3,816 mm by district; every district 8% to 39% above its normal; country 2,290 mm against 1,867 mm (+22.7%) ✅ (computed; not compared with a Department of Meteorology figure ❌).
- MPI national row 0.0112 with headcount 2.92%, as in the source file ✅.

## Not done

DesInventar and HeiGIT travel-time tables (done 2026-11-21: see [hazard-access.md](hazard-access.md)), WFP market prices (points), HIES poverty and LFS labour (no tables held), CBSL national series (none held).
