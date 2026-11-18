# Method: national population estimates 1891-1946

Built by `slf history estimates` (`pipeline/slf/population_estimates.py`) from the Harvard Dataverse table (doi:10.7910/DVN/29209, CC0), which reproduces Chandra and Sarathchandra (2014).

- **What it is:** one row per year for the whole island, two columns (all districts; non-plantation districts). There are no districts in the file. Each value is copied; the locator names the file row and column.
- **What it is not:** a census count. 55 of 56 year-to-year steps have the identical growth rate (1.5664% a year), so the series is a smooth reconstruction. Treat it as an estimate with `data_nature: reconstruction`.
- **1918 appears twice** with values of 4,604,380 and 4,317,665 (all districts). The file does not say why (a fall of about 6%, in the year of the influenza pandemic ❓). Both rows are kept with distinct claim ids (`:row29`, `:row30`); neither is chosen.
- **Cross-check:** against DCS Statistical Abstract 2024 Table 2.1 census totals for 1891, 1901, 1911, 1921, 1931 and 1946: differences between -0.86% and +0.62%. The 1918 pair is excluded. See `data/build/population-estimates/qa.md` after a run.
- **Not checked:** the underlying census sources; the meaning of "non-plantation districts"; that the tab and xlsx copies agree row by row.
- **Geography:** country only (`LK`), so no crosswalk is needed. District figures for the period are not in this dataset; the DCS district census series in the history build covers census years.
