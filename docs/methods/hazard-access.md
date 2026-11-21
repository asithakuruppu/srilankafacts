# Method: crosswalks and indicators for HeiGIT accessibility and DesInventar

Status: **local build, 2026-11-21 (extended the same day), not in any release** · Code: `pipeline/slf/hazard_access.py` (`uv run slf hazard-access build`) · QA: [hazard-access-xwalk-2026-11-21.md](../qa/hazard-access-xwalk-2026-11-21.md) · cross-checks: [hazard-access-checks-2026-11-21.md](../qa/hazard-access-checks-2026-11-21.md) · rights: [heigit-share-alike.md](../research/rights/heigit-share-alike.md)

Legend: ✅ verified by running it · 🟡 claimed by the source · ❓ assumption.

## Crosswalks (rule 5)

| Code system | File | Units matched | Method |
|---|---|---|---|
| `heigit-iso` (ISO 3166-2:LK, HeiGIT accessibility tables) | `catalog/geographies/codes/heigit-iso.csv` | country, 9 provinces, 25 districts: all ✅ | `name_and_parent` |
| `desinventar` provinces and districts | `catalog/geographies/codes/desinventar.csv` | 9 + 25: all ✅ | `name_and_parent`; one `manual` (0.95): `lka008002 Moneragala` → `LK82` (accepted by the lead 2026-11-21) |
| `desinventar` DS divisions (2015 shapefile, 328) | same file | **309 matched** ✅ | `exact_code` (DesInventar's DCS-style DS code equals the DCS code already mapped to a spine DS, names at least 0.80 alike, unit inside the matched district) or `name_and_parent` (0.9) |

- ✅ ISO district numbers are not p-code suffixes for four northern districts (LK-42 Kilinochchi → LK45, LK-43 Mannar → LK42, LK-44 Vavuniya → LK43, LK-45 Mullaitivu → LK44).
- ✅ HeiGIT's nine risk tables are p-coded already; all codes are spine districts.
- **DS divisions.** The event table's "Code Commune" column is the DS division code (34,707 records carry one), not a GN code. 17 DS divisions are **not mapped and listed for review**: 10 where the same code now belongs to a unit with a different name, or the same name differs by a transliteration below the 0.80 threshold (for example Kanthalai/Kantale, Ambanganga Korale/Ambanganga, Hanwella/Seethawaka), and 7 that land on a unit created by a 2012 to 2024 split (Baddegama, Hikkaduwa, Balangoda, Kothmale, Hanguranketha, Nuwara Eliya, Walapane; Ambagamuwa Korale): the old unit's events cannot be assigned to one part. 2 more (Eravu Pattu and Porathivu Pattu, Batticaloa) match neither by code nor by name. Records for unmapped DS divisions (2,502) still count at district level.
- **GN level: stopped.** The "Location" text names GNs and places in free form ("Telangapatha (GN)", "Wijerama Mw, colombo 7"), several per record, with no code table; matching them to spine GNs would be a name join. Not done.
- ❓ District and DS boundaries are taken as unchanged 1965 to 2014, except where the succession table shows a split (refused). The 1984 Kilinochchi and Mullaitivu changes are not modelled.

## Indicators (56, 13,475 rows)

| Group | Indicators | Dataset | Level | Period | Support | Floor |
|---|---|---|---|---|---|---|
| Travel-time and distance access | `access_*` (7): share of total population within 30/60/120 minutes of a hospital, 30/60 of primary care, 5/10 km of a school; cumulative | `heigit-accessibility` | country, province, district | 2026 | `area_mean`, modelled estimate | `grid-100m` |
| DesInventar records | `di_{flood,landslide,drought,wind,disaster}_records`: records per year | `desinventar-sri-lanka` | district and DS division | 1965 to 2014 | `area_total`, administrative record | district or DS (2015 file) |
| Population (modelled) | `heigit_pop_*` (5), `heigit_rural_share` | `heigit-risk-indicators` | district | 2026 | `area_total` / `area_mean`, modelled | `grid-100m` |
| Facilities (OSM) | `osm_hospitals_count`, `osm_primary_care_count` | same | district | 2026 | `area_total` | OSM features |
| Flood evacuation | `evac_minutes_{mean,median}_rp{10,50,100,500}` (8) | same | district | 2026 | `area_mean` | 1-in-N-year flood, JRC |
| Flood exposure | `flood_rp{10,50,100,500}_*` (28): cropland km² and share, exposed women, under-5s, over-65s, hospitals, primary care | same | district | 2026 | `area_total` | JRC 30 cm depth |

Every row carries dataset, snapshot sha256, source URL, a locator (file, row, column for HeiGIT; file lines and counting rule for DesInventar), `verification: machine_extracted`, `boundary_vintage: cod-ab-v03`. HeiGIT values are copied, not computed. Inputs are as HeiGIT states them (WorldPop, GHSL, OSM, JRC; 🟡 not independently verified).

- **A missing year is not a zero.** Only positive DesInventar counts are stored; reporting varies (91 to 260 records in each of 1979, 1980, 1982, 1984, 1985 and 1996 against 8,100 to 9,000 in each of 2006 to 2008 ✅ counted). A record is a reported event at a place and date, not a distinct disaster. Epidemics, plague, animal attacks and snake bites are out of the hazard indicators; no epidemic indicator is built.
- 120 matched DesInventar records have impossible dates (31 June, 29 February 2005) and get no year; 2 have a province that contradicts their district and are excluded (both epidemics).
- HeiGIT shares are cumulative (✅ Colombo 97.83% within 10 minutes, 99.94% within 20, 100% beyond); `population_share` is used, not the per-band share.
- Held, **not** ingested, with the reason: educational-facility counts and exposure (OSM holds about 40% of Giga's school list in the median district, see below); the risk-table `access` counts (they disagree with the accessibility tables by up to 20 points); `coping` and `vulnerability` (identical joins of other tables); per-group RAI and the per-group accessibility tables.
- Existing correction: the Rural Access Index in `subnational.py` was described as "all-season road"; HeiGIT's own description says **paved road** (Mapillary and Planet road-surface data). Text fixed; values unchanged.

## Cross-checks (full numbers in the QA report)

| Check | Independent | Result |
|---|---|---|
| HeiGIT district population against Census 2024 | yes | ✅ **differs by -21% to +42% by district** (total +6.0%); not a substitute for the census, so the definitions say so |
| OSM education features against Giga's 10,112 schools | yes | ✅ OSM 5,047; district ratio 0.16 to 1.44, median 0.40: incomplete, hence not ingested |
| OSM hospitals against healthsites.io | no (both OSM) | ✅ 904 against 905, ratio 0.92 to 1.08 |
| `coping` and `vulnerability` against their parts | no | ✅ identical |
| Access counts against accessibility shares | no | ❌ **disagree** by up to 20 points (Monaragala 64.9% against 85.2%) and 17.9 to 21.5 million people; HeiGIT gives no reason. Only the accessibility tables are ingested |
| Flood exposure by return period, exposed facilities and shares | no | ✅ no violations |
| DesInventar DS sums against district counts | no | ✅ never exceed, every district-year |
| DesInventar 2004 tsunami deaths against ADRC Annual Disaster Report 2004 | yes, partly | ✅ 30,959 = 30,959 (identical, so probably one upstream tally); missing 1,908 against 5,443 ❌ not used |

## Rights

- HeiGIT: CC BY-SA (no version stated); attribution "HeiGIT; © OpenStreetMap contributors". The release builder now writes a **Share-alike terms** section into `NOTICE.md` and the README for any dataset with a share-alike licence, and keeps the values in their own files. The memo and open points: [heigit-share-alike.md](../research/rights/heigit-share-alike.md).
- DesInventar (UNDRR, source: Disaster Management Centre): CC-BY-4.0, attribution.
- `slf atlas export --public` leaves out both HeiGIT datasets until a release carries the statement.

## Not done

- Not in any release; the live preview is unchanged. `slf atlas export --hazard-dir data/build/hazard-access` shows the indicators in a local bundle.
- The 17 DS divisions above need a reviewer's decision (a reviewed alias list, like Moneragala).
- GN-level DesInventar records; per-group HeiGIT breakdowns.
- Upstream licences of WorldPop, GHSL, JRC, Mapillary and Planet are not recorded in the catalogue.
