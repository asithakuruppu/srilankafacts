# Method: DS boundary change 2012 → 2024, and the district census series

Prompt G06 (v2) · Stage 2 history · written 2026-11-15 by an agent · decision D-035 (Proposed)
QA report: [`docs/qa/boundary-change-2012-2024.md`](../qa/boundary-change-2012-2024.md) ·
command: `uv run slf history snapshot` then `uv run slf history build` (in `pipeline/`)

Tags: ✅ verified by running or reading · 🟡 claimed by a source, not checked · ❌ not found · ❓ assumption.

## 1. What this answers

Between the 2012 and 2024 censuses Sri Lanka went from **331 to 340 Divisional Secretariat (DS)
divisions** (DCS Final Report 2024, Tables 2.3 and 2.4 ✅). A 2012 DS total and a 2024 DS total
can only be compared directly when the DS covers the same ground in both years. This method
finds out, for every DS, whether it does, using DCS's own lists of the Grama Niladhari (GN)
divisions in each DS in 2012 and 2024, and labels every comparison `exact` or `approximate`.

## 2. Inputs (all DCS; one via a mirror)

| Input | What it gives | Where it comes from |
|---|---|---|
| "Population by GN division and sex 2012" (PDF, 300 pages) | 25 district, 331 DS and 14,022 GN rows, with DCS GN numbers (e.g. `495B`) and population by sex; final 2012 figures (national 20,359,439) | Authored by DCS (PDF metadata: printed from `Population by GN and Sex 2012.xlsx`, 2015-05-06). **The DCS address was not found** ❌ on the live site or in the Web Archive; the copy used is the one in `nuuuwan/lk_census_2012` at commit `8d8af05` (D-035) |
| Statistical Abstract 2024, Table 2.7 | Population by DS division and sex, Census 2012, final | DCS, `statistics.gov.lk/abstract2024/CHAP2/2.7.pdf` |
| Census 2024 GN workbook (`GN_population.xlsx`) | 14,008 GNs with DCS DS and GN codes, GN numbers, provisional 2024 population | DCS (already held for Census 2024) |
| Census 2024 Final Report, Tables 2.1, 2.3, 2.4, 3.1, 3.3 | Number of DS and GNs by district (2012, 2024); district populations 1981–2024 | DCS (already held) |
| Statistical Abstract 2024, Table 2.1 | Population by district, census years 1871–2012 (thousands) | DCS, `statistics.gov.lk/abstract2024/CHAP2/2.1.pdf` |

PDF text is read with `pipeline/scripts/pdf_pages.swift` (macOS PDFKit), as for the Q01 audit.

## 3. Steps

**3.1 Rebuild the 2012 hierarchy.** The 2012 GN file prints district, DS and GN rows with no
level column. The pipeline recovers the levels from arithmetic alone: a DS row's total equals the
sum of the GN rows below it, and a district's total equals the sum of its DS rows. Any break
stops the build. GN rows printed without figures (33, for example GNs DCS did not enumerate in
2012) stay attached to the DS they appear under. Each 2012 DS gets a working id
`<district code>-<order in the table>` (for example `23-01` Kothmale), because the file has no
DS codes. Result ✅: 331 DS divisions, the same count per district as Final Report Table 2.3;
every DS total equals a row of DCS's Abstract Table 2.7 (331 of 331, matched on total, male and
female); every district total equals Final Report Table 3.3.

**3.2 Match GNs between 2012 and 2024, inside each district.** In four layers, each requiring a
key that is unique on both sides among rows not yet matched:
1. DCS GN number **and** GN name (13,623 GNs);
2. GN number alone, for a GN whose name spelling changed (301);
3. GN name alone, mainly Colombo district, where DCS prints no GN numbers (78);
4. number, name **and** DS name, for the one GN DCS lists under two DS divisions (Punanai East
   211B, Final Report Table 2.4 note 2) (2).

GN numbers are compared after removing separators and leading zeros (`J-37` = `J/37`, `06` =
`6`), because DCS writes them differently in the two lists. GNs are never matched across
districts, and nothing is matched to another publisher's names or codes (AGENTS rule 5). 18 2012
GNs and 4 2024 GNs stay unmatched and are listed in the QA tables with a reason where DCS gives
one (13 are the Matale GNs DCS removed for the Kalu Ganga and Moragahakanda reservoirs, Final
Report Table 2.4 note 1).

**3.3 Classify each DS.** Each matched GN is a *flow* from a 2012 DS to a 2024 DS. A flow is
*major* when it carries at least 10% of the GNs of either DS, otherwise it is a *transfer*.

| Type | Rule |
|---|---|
| `unchanged` | one major flow each way, same name (after normalising spelling marks) |
| `renamed` | one major flow each way, different name; GN lists identical |
| `split` (2012 unit) | two or more major successors; the 2024 units are `split_remainder` (same name as the parent) or `new` |
| `merged` | two or more major predecessors (none found) |
| `boundary_adjusted` | otherwise one-to-one, but GNs were transferred to or from another DS |

**3.4 Identity and relations** (data-model §3.3). A 2012 DS that was split is retired and gets a
vintage id `LK-ADM3-V2012-<district>-<order>`; every other 2012 DS continues under its 2024 spine
id (renaming and GN transfers do not change identity). For each retired unit the pipeline writes
`succeeded_by` (weight = share of the 2012 unit's population that went to each successor) and
the reverse `preceded_by` (weight = share of the successor's 2012-boundary population that came
from that predecessor), `method: official_list`, to
`catalog/geographies/relations/succession_ds_2012-2024.csv`. Weights come from the 2012 GN
populations, so they are counts, not areas or models.

**3.5 Comparison labels**, one row per 2024 DS:

| Label | Method | When | 2012 figure used |
|---|---|---|---|
| `exact` | `same_gn_list` | unchanged or renamed, and every GN on both sides matched | DCS's 2012 DS total |
| `approximate` | `same_ds_total_gns_unverified` | unchanged or renamed, but some GNs unmatched, so a transfer cannot be ruled out | DCS's 2012 DS total |
| `approximate` | `gn_reaggregation` | split, new or boundary-adjusted | sum of 2012 GN populations now in the 2024 DS |

Why reaggregated figures are `approximate` even though they are sums of official counts: GN
boundaries themselves may have moved between censuses, and the GN match is by DCS number and
name, not by a published DCS concordance ❓. Where a whole group of 2012 and 2024 units is
closed (no GN enters or leaves the group, none unmatched), the **group** comparison is `exact`
(for example Kothmale 2012 = Kothmale West + Kothmale East 2024); these are in
`ds_comparison_groups_2012_2024.csv`.

Growth rates use DCS's formula: average annual rate = ln(P₂₀₂₄ / P₂₀₁₂) / t, with t = 12.75
years between 20 March 2012 and 19 December 2024 (census dates, Final Report Table 3.1). This
reproduces DCS's published 2012–2024 rates to one decimal for Sri Lanka and 24 of 25 districts;
Kilinochchi differs (ours 1.5, DCS 1.4) ✅, probably rounding at DCS's end ❓.

## 4. What it does not do

- No boundaries are drawn or inferred from geometry. COD-AB and NSDI shapes are not used here.
- No 2012 GN-level values are published; GN rows are used only to classify DS changes and to
  rebuild 2012 populations on 2024 DS boundaries.
- The 2024 GN figures are DCS's provisional GN-level workbook, which adds up to the Final
  Report's 21,781,800 exactly ✅.
- Kalmunai: DCS publishes Kalmunai North Sub (5221) and Kalmunai (5224) in both years (2012
  names: "Kalmunai Tamil Division (Sub Division)" and "Kalmunai"). Both comparisons are `exact`
  on GN lists. 5221 maps to the provisional unit `LK-ADM3-P0001` (D-022); 5224 still has no spine
  id, so it appears in the comparison table without a `geography_id` and gets no relation (D-022
  unchanged). The naming follows DCS and implies no position (AGENTS rule 12).

## 5. District census series 1871–2024

`district_census_series.csv` combines two DCS tables, keeping both where they overlap (D-019):

- **Abstract 2024 Table 2.1**, 1871–2012, in thousands to one decimal. An agent transcribed it
  from the page image to `catalog/references/dcs-abstract2024-table2.1-transcription.csv`,
  because the PDF's text layer scrambles several rows. The build checks the transcription: all
  310 values occur verbatim in the text layer, and each year's districts add up to the printed
  national figure within rounding ✅. Values stay `machine_extracted` until a person checks them.
- **Final Report 2024 Table 3.3**, exact counts for 1981, 2001, 2012 and 2024.

`comparison_to_2024` labels:
- `exact` for 2012 and 2024 (25 districts unchanged since 2001, Final Report §2.2.2; DS and GN
  counts per district in Tables 2.3/2.4 are identical except Matale's 13 reservoir GNs and the
  9 new DS, all created inside existing districts) and for 2001 where DCS enumerated fully. The
  2001 figures for Jaffna, Mannar, Vavuniya, Mullaitivu, Kilinochchi, Batticaloa and Trincomalee
  are DCS **estimates** (`value_status: estimate`, `approximate`).
- `approximate` for every year before 2001. DCS records districts being created (Gampaha and
  Mullaitivu in September 1978, Kilinochchi in February 1984; Ampara, Polonnaruwa and Moneragala
  appear from 1963; Final Report Table 2.1 and the Abstract's note) and abolished (Chilaw appears
  from 1891 to 1953; Negombo in two early censuses, Final Report Table 2.1). When a district is carved out, its parents lose ground, so
  a long series for a parent district is not like-for-like. Which districts lost ground to each
  new one is **not** stated in these tables ❓, so every pre-2001 figure is labelled approximate,
  not only the obviously affected ones.
- `not_comparable` for Chilaw, which no longer exists.

Known disagreement between the two DCS tables ✅: for 1981 the Abstract is higher than Final
Report Table 3.3 in every district (Colombo 1,699.2 thousand vs 1,675,847; Jaffna 830.6 thousand
vs 734,474, where Table 3.3 note 2 says Jaffna and Kilinochchi are shown on current boundaries).
Table 3.3's 1981 districts add up to 14,629,224, which is 217,050 below its own national figure of
14,846,274 (checked against the page image), while the Abstract's add up to its national figure
within rounding. For 2001 the Abstract is also higher in the 18 enumerated districts. Neither is
preferred; both claims are kept with their source, and the question goes to DCS (draft in
`docs/outreach/2026-11-15-dcs-census-history-queries.md`).
