# Method: crosswalks and indicators for HeiGIT accessibility and DesInventar

Status: **local build, 2026-11-21, not in any release** · Code: `pipeline/slf/hazard_access.py` (`uv run slf hazard-access build`) · QA: [hazard-access-xwalk-2026-11-21.md](../qa/hazard-access-xwalk-2026-11-21.md)

Legend: ✅ verified by running it · 🟡 claimed by the source · ❓ assumption.

## Crosswalks (rule 5)

| Code system | File | Units matched | Method |
|---|---|---|---|
| `heigit-iso` (ISO 3166-2:LK, HeiGIT accessibility tables) | `catalog/geographies/codes/heigit-iso.csv` | country, 9 provinces, 25 districts: all ✅ | `name_and_parent`: name equals one spine name at the level; districts are matched inside the province given by the ISO number's first digit |
| `desinventar` (DesInventar province and district codes) | `catalog/geographies/codes/desinventar.csv` | 9 provinces, 25 districts: all ✅ | `name_and_parent` for 33; **one `manual`** (confidence 0.95): `lka008002 Moneragala` → `LK82 Monaragala`, a spelling variant, lead review pending |

- ✅ **The ISO district number is not the p-code suffix for four northern districts**: ISO LK-42 Kilinochchi, LK-43 Mannar, LK-44 Vavuniya, LK-45 Mullaitivu, against p-codes LK45, LK42, LK43, LK44. A join on "LK-" + number would have put four districts' values on the wrong places. The ISO code is therefore only ever looked up in the crosswalk.
- ✅ HeiGIT's nine risk-indicator tables are already keyed by ADM2 p-codes; all 25 codes in all nine tables are spine districts (no translation, a check only).
- **Stopped at districts for DesInventar.** The event table has province, district and (for about a quarter of records) GN names, but no DS column. The shapefile holds 328 DS divisions on a 2015 file of unstated vintage; mapping them would need the 2012-to-2024 succession table and is not needed for these records, so it is not done. GN names in the event table are free text with no code table and are not mapped (never a bare name join).
- ❓ District boundaries and names are taken as unchanged across 1965 to 2014 (the record years). The 1984 split of Kilinochchi from Jaffna and Mullaitivu from Mullaitivu-Vavuniya is not modelled; records are placed in the district the database names.

## Indicators ingested (12, 2,632 rows)

| Indicator | Source dataset | Level | Period | Support | Floor |
|---|---|---|---|---|---|
| `access_hospital_{30,60,120}min`, `access_primary_care_{30,60}min`, `access_school_{5,10}km` (share of total population within the limit, cumulative) | `heigit-accessibility` | country, province, district | 2026 | `area_mean`, `interval_mean`, modelled estimate | `grid-100m` (WorldPop, OSM) |
| `di_{flood,landslide,drought,wind}_records`, `di_disaster_records` (records per district per year) | `desinventar-sri-lanka` | district | 1965 to 2014 | `area_total`, `interval_total`, administrative record | district (record location) |

- Every row carries dataset, snapshot sha256, source URL, a locator (file, row and column for HeiGIT; file lines and the counting rule for DesInventar), `verification: machine_extracted`, `boundary_vintage: cod-ab-v03`.
- Only positive counts are stored. **A missing year is not a zero**: reporting effort varies (91 to 260 records in each of 1979, 1980, 1982, 1984, 1985 and 1996 against 8,100 to 9,000 in each of 2006 to 2008 ✅ counted).
- A record is one reported event at one place and date, not one distinct disaster. Epidemics (85,707 matched records), plague, animal attacks and snake bites are left out of the disaster total and of the hazard indicators; no epidemic indicator is built.
- Hazard groups are our grouping of DesInventar's free event labels (listed in the QA report); "RAINS", "FIRE", "LIGHTNING" and others are not grouped into any indicator.
- ✅ HeiGIT shares are cumulative (Colombo: 97.83% within 10 minutes, 99.94% within 20, 100% beyond); `population_share` is used, not the per-band `population_interval_share`.
- Dates that do not exist (for example 31 June, `2005/2/29`) are not given a year; 120 matched records are listed by count in the QA report.

## Rights

- HeiGIT: **CC BY-SA 4.0** with © OpenStreetMap contributors; commercial reuse allowed. **Share-alike applies**: a release that includes these indicators must carry the attribution and offer them under the same licence (catalogue status `permitted_with_conditions`). The release process must check this before inclusion.
- DesInventar (UNDRR, source: Disaster Management Centre): CC-BY-4.0, attribution required.

## Not done

- Not wired into the atlas export or any release; the live preview is unchanged. Wiring means a `--hazard-dir` option for `slf atlas export` and a release decision for the share-alike data.
- 🟡 Nothing is cross-checked against an independent figure (for example DMC annual loss reports); all values are `machine_extracted`.
- HeiGIT per-group breakdowns (adults, elderly, under-5, women of childbearing age) and the other eight risk tables are held but not ingested.
