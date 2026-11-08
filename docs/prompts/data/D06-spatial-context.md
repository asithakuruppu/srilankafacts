# D06: Spatial context (neighbours, clusters, outliers, small numbers)

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 1 | Data | 2 | 2026-11-08 | active |

## When to use
After the first validated census observations exist (D01) and the contiguity graph exists (G01). Adds the *enrich* stage that makes every value answer "compared to where?". Re-run for each release.

## Read first
- `AGENTS.md`
- `docs/architecture/spatial-first-analytics.md` §4.1, §5 (and §2 cautions on MAUP and the ecological fallacy)
- `docs/architecture/data-model.md` §5, §6, §9
- The latest QA report from D01

## Inputs (fill in)
```
INDICATORS: {{INDICATOR_IDS}}        # start with 10–20 core census indicators
LEVELS: gn, ds, district
SMALL_DENOMINATOR_THRESHOLD: 100   # confirmed by the lead 2026-11-08 (D-026)
FDR_Q: 0.05
PERMUTATIONS: 999
```

## Task
1. Add a pipeline stage `enrich` that reads **only validated observations** and the contiguity graph, and writes to the release build. It must not modify observations.
2. For each indicator × level: neighbour summary (count, median, min, max of bordering units), parent values, national value, rank.
3. Local Moran's I with PySAL (`libpysal`, `esda`) using row-standardised contiguity weights; conditional permutation p-values; Benjamini–Hochberg FDR at `FDR_Q`. Classes: `high_high`, `low_low`, `high_low`, `low_high`, `not_significant`. Islands and units with no neighbours: `no_neighbours`, never silently dropped.
4. Rates on small denominators: flag below the threshold, and compute an empirical Bayes smoothed rate (state which variant), stored separately with `data_nature: modelled_estimate`. The raw rate stays the published value.
5. Write `stats/local_{indicator}_{level}.parquet` and add spatial outliers (`high_low`, `low_high`) to the QA report as candidate errors to check.
6. Write `docs/methods/spatial-context.md`: plain-language explanation for the public methodology page, including MAUP and the ecological fallacy.

## Constraints
- Use only methods in the design doc. Propose others in the PR, don't add them.
- No cluster or hotspot wording for units that are not significant after FDR.
- Smoothed values never replace published values in any file.

## Verify (show real output)
- **Known-answer tests:** a synthetic grid with a planted cluster and a planted outlier is detected; a spatially random field yields roughly no significant units after FDR.
- Class counts per indicator × level.
- 10 random units with raw value, neighbour median, class and p-value, for the lead to eyeball.
- A QGIS project showing one indicator's classes for the lead's visual check.

## Deliverables
Enrich stage, tests, stats files, QA additions, methods doc.

## Done when
For any GN and core indicator, the release says how it compares with its neighbours, parent and country, and whether it's part of a significant cluster or an outlier.

Report using the format in `AGENTS.md`.
