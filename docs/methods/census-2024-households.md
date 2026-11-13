# Census 2024: households and amenities by GN

Status: **built, not in any release** · Dataset `census-2024-topic-tables` (step a of D-032) · Period `2024` · Last revised 2026-11-13.

Verification tags: ✅ verified by running or reading the cited source · 🟡 claimed by a source,
not independently checked · ❌ not found or failed · ❓ assumption.

## 1. What is built

For every GN division DCS lists, the number of households and how they are split in four groups.
Each household falls in exactly one category of each group:

| Group | DCS heading | Categories |
|---|---|---|
| Drinking water | Main Source/way of drinking water | 15 (wells, spring, four kinds of pipe-borne water, tank/river, rain, bottled, R.O. plant, bowser, other) |
| Cooking | Main Source of Energy/Fuel Used for Cooking | 8 (firewood, kerosene, gas, electricity, sawdust/paddy husk, biogas, other, "not relevant") |
| Lighting | Main source of Lighting | 7 (grid electricity, kerosene lamp, solar grid-connected, solar stand-alone, biogas, generator, other) |
| Toilet | Toilet facilities | 7 (within the unit or premises, own or shared; sharing another unit's; public; not using a toilet) |

That gives 75 indicators: `households_total`, 37 category counts (`households_{group}_{category}`)
and 37 shares (`…_share`, count ÷ households × 100). The full list and each DCS column heading,
typos kept, are in `catalog/indicators/households_*.yaml` and
`pipeline/slf/datasets/census_2024_topics.py`.

"Households" is not "occupied housing units". One housing unit can hold more than one household;
nationally there are 6,111,315 households ✅ and 6,030,541 occupied housing units ✅ (from the
existing dataset).

## 2. Source

| Item | Value |
|---|---|
| File | `HH_GND_excel.xlsx`, sheet `Households`, titled "Household Information by Grama Niladhari Division (Provisional)" ✅ |
| URL | <https://www.statistics.gov.lk/Population/StaticalInformation/CPH2024/HH_GND_excel> |
| Snapshot | `raw/dcs/census-2024-topic-tables/20261112T173135Z/`, sha256 `c41c0d2c384f…` ✅ |
| Check tables | `HousingA_A5.xlsx` (water), `A6` (cooking), `A7` (lighting), `A8` (toilets): district tables from the same page ✅ |
| Rights | Unclear; non-commercial publication allowed by D-030 as extended by D-032 |

The snapshot's own `.meta.json` licence note, written before D-032, says D-030 covers only
`census-2024-gnd-tables`. Snapshots are immutable (AGENTS rule 3), so the note stays; D-032 is
the current position.

## 3. How it is built

1. **Header check.** The module checks the four group titles and all 37 column headings against
   what it expects. If DCS moves or renames a column, the build stops.
2. **Row check.** For every GN row, each group's categories must add up to the number of
   households. One failure stops the build. All 14,008 rows pass ✅.
3. **Join.** DCS GN codes (DDSSGGG) join to the spine through the G02 crosswalk
   (`catalog/geographies/codes/dcs-census2024.csv`), never by name. 13,967 GNs match; 41 do not
   (the same 41 as the population dataset) and are listed in the QA report.
4. **Totals.** DS, district, province and country values are sums of all GN rows, unmatched GNs
   included. DCS DS 5224 Kalmunai has no spine unit (D-022): its households count in Ampara
   district, but no DS row is produced.
5. **Shares** are computed from the counts at every level. A GN with 0 households (5 GNs) has
   shares marked `not_available`, not 0.
6. **Check against DCS's district tables.** For every district and the Sri Lanka row of A5–A8,
   the summed households and every category count must equal the published value. They all do ✅
   (25 districts + national × 4 tables, 0 differences). The district rows are matched by their
   English names because those tables carry no codes; "Monaragala" in A5–A8 is matched to
   "Moneragala" in the GN file. This is a check only; no value is taken from those tables.

Every GN value's locator names the file, sheet, row and column letter; every total names the
number of GN rows and the row range summed. Values stay `machine_extracted` (AGENTS rule 7) and
`revision_status: provisional` (DCS's title says provisional).

## 4. What has not been checked

- No comparison with the Final Report PDF tables ❌.
- No human has checked any of these values against the source (Q01 not run for this dataset) ❌.
- Whether DCS's "Not relevant" cooking category means households that do not cook at home is
  not documented in the file ❓. It is shown with DCS's wording.
- Small numbers: many GNs have fewer than 100 households in some categories. Shares for GNs
  with few households are unstable; the release builder's small-denominator flag (D-026) is
  generic, but has not been checked on these indicators ❓.

## 5. Not in a release yet

A trial preview release with both census datasets built ✅, but it is not kept:

| | v2026.11.9-preview.1 | Trial with households |
|---|---|---|
| Release size | 449 MB | 1.7 GB |
| API folder | 193 MB | 913 MB |
| One DS place file (`LK1103.json`) | 14 KB | 60 KB |
| Files | 14,595 | 15,345 |

Putting all 75 indicators on every place page would make each page's data about four times
larger. Which of these indicators the website and place files carry, and which stay in downloads
only, is a decision for the lead before they go into a release (see the performance budget, Q02).
