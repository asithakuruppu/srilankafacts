# Census 2024: GN population and occupied housing units

Status: **private preview** · Dataset `census-2024-gnd-tables` · Period `2024` · Last revised 2026-11-08.

This document explains how the first Census Atlas dataset is built, what it covers, how it is
joined to the geography spine, and what has not been checked. It is the public methodology page
for the dataset in miniature. The release itself is marked `publishable: false` because DCS
rights are unclear.

Verification tags: ✅ verified by running or reading the cited source · 🟡 claimed by a source,
not independently checked · ❌ not found or failed · ❓ assumption.

## 1. What the dataset is

The dataset holds counts and derived rates for every Sri Lankan GN division for which the
Department of Census and Statistics (DCS) published a 2024 Census of Population and Housing
row. It covers:

- total population, male and female;
- population aged 0–14, 15–59, 60–64 and 65+;
- occupied housing units;
- derived indicators: population aged 60+, sex ratio, two age shares, persons per occupied
  housing unit, and population density.

It is **not** the full census topic set. Only two DCS workbooks are held: population by sex and
age group, and occupied housing units. Ten other topic tables that a full atlas would want
(education, employment, housing amenities, lighting, cooking fuel, water, toilet, floor, roof,
tenure) are not in this build and are not pretended to exist. The catalogue lists exactly the
14 indicators that were built.

The census reference date is **19 December 2024** ✅ (DCS final report).

## 2. Sources and snapshots

| Item | Value |
|---|---|
| Publisher | Department of Census and Statistics (DCS) |
| Landing page | <https://www.statistics.gov.lk/Population/StaticalInformation/CPH2024> |
| Population workbook | `GN_population.xlsx` (sheet `Population`) |
| Housing workbook | `GN_housing.xlsx` (sheet `Housing Units`) |
| Population snapshot | `raw/dcs/census-2024-gnd-tables/20261107T165036Z/GN_population.xlsx` |
| Population sha256 | `2e0168c5daa43af4c4f61a55389768d5c86508ad47252a2d8c89a52986215425` |
| Population size | 1,541,342 bytes, retrieved 2026-11-07T16:50:36Z |
| Housing snapshot | `raw/dcs/census-2024-gnd-tables/20261107T165040Z/GN_housing.xlsx` |
| Housing sha256 | `db5a9af593316cfce8ac72282ebc0aba4edc91443d0afce233db09cd53d8c62a` |
| Housing size | 824,477 bytes, retrieved 2026-11-07T16:50:40Z |
| Final report snapshot | `raw/dcs/census-2024-gnd-tables/20261107T171418Z/CPH2024_Final_Eng.pdf` |
| Final report sha256 | `a6dea9388d05bbb8c9f08d32f562a258838b737938275ed4a2f6ee34ecd670ca` |
| Final report size | 21,432,384 bytes, retrieved 2026-11-07T17:14:18Z |

The raw snapshots are immutable. Every observation records the workbook sha256 and a
`source_locator` naming the sheet, row and column (or the row range for an aggregate).

## 3. Tables and columns used

Population workbook, sheet `Population`, data rows 6–14,013 (14,008 GN rows):

| Column | Field | Used as |
|---|---|---|
| 9 | Total | `population_total` |
| 10 | Male | `population_male` |
| 11 | Female | `population_female` |
| 13 | 0 – 14 | `population_age_0_14` |
| 14 | 15 – 59 | `population_age_15_59` |
| 15 | 60 – 64 | `population_age_60_64` |
| 16 | 65 and above | `population_age_65_plus` |

Housing workbook, sheet `Housing Units`, data rows 6–14,013 (14,008 GN rows):

| Column | Field | Used as |
|---|---|---|
| 9 | Occupied Housing Units | `occupied_housing_units` |

Both files carry DCS codes (`DDSSGGG` for GN, `DDSS` for DS), not geometry, so no source CRS
applies (`crs_source: not_applicable`).

## 4. Geography and joins

The joins go **through the G02 crosswalk**, never by name:

- `catalog/geographies/codes/dcs-census2024.csv` maps DCS 7-digit GN codes to spine IDs and
  4-digit DS codes to DS IDs.
- Of 14,008 DCS GN rows, **13,945** match a current COD-AB v03 GN. The remaining **63** are
  listed in the QA report and the crosswalk review queue. Their values **do** enter their DS,
  district, province and country totals, but no GN-level row is published for them.
- **98** spine GNs have no DCS row in these workbooks. They have no GN-level values and appear
  as `no_data` in the spatial-context tables.
- DCS DS **5221 Kalmunai North Sub** maps to the provisional spine unit
  `LK-ADM3-P0001` (29 GNs, 31,556 people, 8,675 occupied housing units, 12.699301 km²). The
  provisional unit has no DS-level neighbours in the COD-AB contiguity graph, so its spatial
  context is `no_neighbours` rather than a fabricated neighbour list.
- DCS DS **5224 Kalmunai** has no spine equivalent ❌ (D-022). Its 29 GNs and 52,798 people
  enter the Ampara district total, but no DS-level row is published for it.

Consequence for Ampara (`LK52`): the district total is **744,551**. The published DS rows under
`LK52` sum to **691,753** (660,197 for the regular DS rows plus 31,556 for the provisional
unit). The difference, 52,798, is DS 5224. The release does not hide this: the dataset QA report
states it and the district row carries an aggregate locator.

## 5. Indicators and formulas

Counts are exact integers from the workbooks. Derived values are computed from those counts;
they are never copied from another source.

| Indicator | Definition |
|---|---|
| `population_total` | Total population |
| `population_male` | Male population |
| `population_female` | Female population |
| `population_age_0_14` | Population aged 0–14 |
| `population_age_15_59` | Population aged 15–59 |
| `population_age_60_64` | Population aged 60–64 |
| `population_age_65_plus` | Population aged 65 and over |
| `population_age_60_plus` | Sum of 60–64 and 65+ |
| `occupied_housing_units` | Occupied housing units |
| `sex_ratio` | 100 × male ÷ female |
| `population_age_0_14_share` | 100 × age 0–14 ÷ total |
| `population_age_60_plus_share` | 100 × age 60+ ÷ total |
| `persons_per_occupied_housing_unit` | Total population ÷ occupied housing units |
| `population_density` | Total population ÷ area in km² |

Areas come from COD-AB v03 geometry, computed in EPSG:5235 (SLD99 / Sri Lanka Grid 1999), not
from the census table. Density is therefore a derived context value, not a DCS statistic.

A person per occupied housing unit is **not** mean household size: one housing unit can contain
more than one household. The 2024 census reports 6,111,315 households against 6,030,541
occupied housing units nationally 🟡 (final report), so the indicator is labelled as persons per
unit, not household size.

## 6. Aggregation and validation

DS, district, province and country values are built by summing the GN rows, including the 63
unmatched GNs. Rates are recomputed from the summed components, never averaged from GN rates.

Checks that passed in the build:

- **National anchors** ✅: population 21,781,800; male 10,512,344; female 11,269,456;
  age 0–14 4,506,839; age 15–59 13,353,837; age 60–64 1,183,310; age 65+ 2,737,814;
  occupied housing units 6,030,541.
- **All 25 district anchors** ✅ against DCS final-report tables: population (Table 3.1, printed
  p. 67) and occupied housing units (Table 11.2, printed p. 185 / PDF p. 202). The check uses
  the DCS numeric district code, not name matching.
- **Arithmetic** ✅: total = male + female for all 14,008 GN rows; age components sum to the
  total for all 14,008 rows.
- **Independent comparison, not authority** 🟡: `nuuuwan/lk_census_2024` agrees on total, male
  and female for all 14,008 GN rows (0 mismatches). This is a comparison only; nuuuwan is not
  the source of any published value.

Five GNs have zero population (`LK4112185`, `LK4112220`, `LK4112225`, `LK5110025`,
`LK7210065`). Their counts are zero and their rates are `not_available`, not zero. `LK5315010`
has 1 male and 0 female, so its sex ratio is `not_available`.

## 7. Precision and rounding

Counts are published as integers. Derived values are stored to four decimal places and displayed
using each indicator's `decimals` setting (sex ratio and age shares 1 decimal, persons per unit
2, density 1). Rounding is presentation only; aggregation and validation use the unrounded
components. A rate whose denominator is zero is `not_available`, never 0.

## 8. Verification and known gaps

- Every value is `verification: machine_extracted` and `revision_status: provisional`. No human
  has yet spot-checked a sample of GN cells against the workbook.
- No QGIS visual check of the GN boundaries against DCS names has been done.
- The 63 unmatched GNs are unresolved; see the crosswalk QA and D-022. Until they are matched,
  GN-level coverage is 13,945 of 14,043 spine GNs.
- DS 5224 Kalmunai is absent at DS level by decision D-022; its population is only in higher
  totals.
- The DCS final report is used for anchors and the census date. The GN workbooks are provisional
  and may be revised by DCS.
- Rights are **unclear**. The DCS page, workbooks and final report carry no licence or reuse
  terms that the rights review could find. The dataset cannot enter a public release until the
  lead records a decision or DCS replies. D-023 kept Stage 1A private; the letter has since been
  sent. D-030 (2026-11-12) allows non-commercial publication with attribution and a notice
  before DCS replies; commercial use stays forbidden, and the release builder must be changed
  before a public release. See
  `docs/research/rights/census-2024-gnd-tables.md`.

## 9. Reproduction

From `pipeline/`:

```bash
uv run slf snapshot census-2024-gnd-tables
uv run slf build census-2024-gnd-tables --out-dir ./data/build
uv run slf release --version vYYYY.MM.N-preview.1 \
  --dataset census-2024-gnd-tables --preview \
  --out-dir ./data/build/releases-preview
```

The release builder refuses a public release while rights are unclear. It writes the
observations, boundaries, GeoPackage, static API, data package, checksums, spatial-context
tables and QA reports.

## 10. Citation

Cite values as: Department of Census and Statistics, Census of Population and Housing 2024,
GN population by sex and age group / occupied housing units; Sri Lanka Facts release
`vYYYY.MM.N-preview.1`, dataset `census-2024-gnd-tables`, snapshot sha256 and source locator as
recorded in the observation. The preview is not an official DCS publication and must not be
presented as one.
