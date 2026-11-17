# Spatial discovery catalogue (living document)

Started 2026-11-17 · Maintained by agents; update the row and the date when a status changes · Rights rules: [rights README](../rights/README.md) · Machine-readable companions: [`catalog/sources/`](../../../catalog/sources/), [`catalog/datasets/`](../../../catalog/datasets/), [`catalog/acquisition/spatial-manifest.csv`](../../../catalog/acquisition/spatial-manifest.csv)

Legend: ✅ verified directly on 2026-11-17 (licence text read, file opened, or count queried) · 🟡 stated by a secondary source · ❌ not found / failed · ❓ assumption or not checked.

**Status words.** *Integrated*: rolled up to places with QA. *Acquired*: original file held with hash, not yet used. *Catalogued*: found and assessed, not downloaded. *Needs permission*: publicly visible, no reuse terms. *Restricted*: terms forbid our intended use.

"Publicly accessible" is never read as "reusable": a dataset is *Needs permission* until terms are found.

## 1. Summary

| | Count |
|---|---:|
| Original files held (laptop) | 112 files, 1,147.6 MB ✅ |
| Overture extracts held (external drive) | 3 files, 901 MB ✅ |
| Datasets integrated into place roll-ups | 11 ✅ |
| Datasets acquired, not yet integrated | 18 ✅ |
| Indicators added | 69 ✅ |
| Observations built | 1,714,992 ✅ |
| Sri Lanka datasets listed on HDX, with licence field | 162 ✅ ([CSV](hdx-sri-lanka-datasets-2026-11-17.csv)) |
| NSDI layers found in the public service directory | 670 layers in 72 services ✅ ([CSV](nsdi-layer-inventory-2026-11-17.csv)); **no reuse terms** |

## 2. Integrated (in `pipeline/data/build/landscape/`, private)

| Dataset | Publisher | What it holds | Resolution | Period | Licence | What it unlocked |
|---|---|---|---|---|---|---|
| Copernicus DEM GLO-30 | EU / ESA | Surface height | 30 m | 2010–2015 🟡 | Copernicus DEM public licence; registry page read ✅, licence PDF not read ❓ | Elevation, slope and steep-land share for every GN; the terrain block of the landscape space |
| ESA WorldCover 2021 v200 | ESA | Land cover, 11 classes | 10 m | 2021 | CC BY 4.0 ✅ | Tree, crop, grass, built-up, water, wetland, mangrove shares per GN |
| Global Forest Change v1.12 | Univ. of Maryland | Tree cover 2000, loss year | 30 m | 2000–2024 | CC BY 4.0 ✅ | A 24-year yearly series of tree-cover loss for every place |
| JRC Global Surface Water v1.4 | EC JRC | Share of observations with water | 30 m | 1984–2021 | Copernicus: free, no restriction of use ✅ | Permanent and ever-flooded area per GN (tanks, lagoons, paddy flooding) |
| GHS-BUILT-S R2023A | EC JRC | Built-up surface | 100 m | 1975–2020, 10 epochs | Reuse authorised with acknowledgement ✅; CC BY on HDX ✅ | **Built-up change since 1975 for every GN**: the first long change series below district level |
| GHS-SMOD R2023A | EC JRC | Degree of urbanisation class | 1 km | 2020 | as above | A settlement type independent of the administrative urban definition |
| Giga school locations | Giga (UNICEF/ITU); source named: Ministry of Education 🟡 | 10,146 schools with coordinates, level, connectivity | point | 2024 🟡 | CC BY ✅ (HDX field; version not stated ❓) | Schools per place, distance to nearest school, connectivity share |
| healthsites.io | healthsites / OSM | 2,003 health sites | point | 2026 | ODbL ✅ (HDX field) | Mapped facilities per place (completeness unknown) |
| Overture Places 2026-10-21.0 | Overture Maps Foundation | 139,056 places with category and confidence | point | 2026 | CDLA-Permissive-2.0 ✅ (read from every row) | An activity profile per place: 13 categories (lodging, shopping, education…) |
| Overture Buildings 2026-10-21.0 | Overture Maps Foundation | 8,886,949 footprints (Google 4.68 M, OSM 3.39 M, Microsoft 0.81 M) ✅ | footprint | 2026 | ODbL 🟡 | Footprints and footprint area per GN; a first comparison with census housing units |
| Wikidata | Wikimedia | 12,071 items with coordinates; 1,392 Sinhala and 1,560 Tamil labels ✅ | point | 2026 | CC0 ✅ | Landmark density; a seed for the trilingual gazetteer (OPP-13) |

Two open questions from [multi-scale-features.md §10](../../architecture/multi-scale-features.md) are now answered ✅: Google Open Buildings and Microsoft footprints **do** cover Sri Lanka (through Overture), and the Meta/WRI canopy height map is CC BY 4.0 (AWS registry page).

## 3. Acquired, not yet integrated

| Dataset | What it holds | Licence | Why it matters | Next step |
|---|---|---|---|---|
| GHS-BUILT-H 2018 | Average building height, 100 m | as GHSL | Building height per place (only 4,338 Overture footprints carry a height) | Add to the roll-up |
| WorldPop Global2 R2025A, 2025 | Modelled population, 100 m | CC BY 4.0 ✅ | Used only to test it against Census 2024 ([findings](findings-2026-11-17.md)) | Keep as a comparison; do not publish as population |
| Kontur Population 2023-11 | Modelled population on H3 (~400 m) | CC BY ✅ (HDX) | A ready H3 layer for the analytic grid (D-014) | Open and assess inputs |
| OpenStreetMap extract (Geofabrik) | All OSM features, 144.6 MB | ODbL ✅ | Roads, railways, waterways, land use, amenities (G08) | Split into feature classes |
| GeoNames LK | 56,996 named places | CC BY ✅ | Gazetteer; 17,728 populated places, 6,761 reservoirs, 5,829 estate records | Resolved to GN already; join to names |
| IBTrACS storm tracks | Track points since 1842 | CC BY-IGO ✅ (HDX) | Cyclone passes near each place by decade | Line-to-place distance |
| UNOSAT flood extent, Cyclone Ditwah 2025 | Satellite-detected water, 26–30 Nov 2025 | CC BY-SA ✅ (HDX) | Share of each GN under water in the 2025 floods | Open the geodatabase; keep share-alike apart |
| WFP ADAM flood, 1 Dec 2025 | Flood raster | CC BY-SA ✅ | Second flood source for D-019 comparison | Open |
| EOS-RS flood proxy map, 2 Dec 2025 | Sentinel-1 flood proxy v0.9 | CC BY ✅ | Third flood source | Open |
| DesInventar Sri Lanka | Disaster loss records (source: DMC) with a boundary set | CC BY ✅ | Decades of disaster events by DS division | Read the workbook; boundary vintage needs a crosswalk |
| WFP/CHIRPS rainfall | Rainfall every 10 days since 1981, by p-code | CC BY ✅ | Rainfall normals and anomalies for 25 districts, already keyed to our ids | Straightforward ingest |
| WFP/MODIS NDVI | Vegetation index since 2002, by p-code | CC BY ✅ | Seasonal greenness by district | Ingest |
| WFP food prices | 34,262 price rows, 150 located markets | CC BY-IGO ✅ | Food price atlas (OPP-24) | Ingest |
| CTrees biomass | Above-ground biomass raster | CC BY ✅ | Carbon per place | Read units and year first |
| Climate TRACE | Emission estimates by source | CC BY ✅ | Emissions by place; many rows are modelled aggregates | Separate true assets from aggregates |
| HeiGIT accessibility | Travel-time bands to schools, hospitals, primary care | CC BY-SA ✅ | The `access` space, ready-made at district level | Crosswalk their unit ids |
| HeiGIT risk indicators | Flood exposure by return period, by ADM2 p-code | CC BY-SA ✅ | Flood exposure per district | Check each input |
| OPHI MPI | Multidimensional poverty by province (2016 DHS) | CC0 ✅ | Poverty context (survey estimate) | Ingest as a claim |

## 4. Catalogued, not acquired

| Dataset | What | Access | Licence | Assessment |
|---|---|---|---|---|
| Meta / WRI canopy height | Canopy height, 1 m | AWS S3, no account | CC BY 4.0 ✅ | Passes the admission test for greenery (OPP-37). Tens of GB for the island; process tile by tile from the external drive |
| AlphaEarth satellite embeddings | 64-dim annual embedding, 10 m | Earth Engine (account) | CC BY 4.0 ✅ | The original idea for a `landscape` space; needs an Earth Engine account, so not acquired |
| Google Open Buildings 2.5D temporal | Building presence and height by year | Earth Engine / GCS | CC BY 4.0 or ODbL ✅ | Building change by year; larger than v3 |
| HydroSHEDS / HydroRIVERS | River network, basins | Download | Free for commercial use under its own licence ✅ | River basins as a geography scheme |
| Global Mangrove Watch | Mangrove extent by year | Zenodo | CC BY 4.0 ✅ | Mangrove change; WorldCover already gives one year |
| CHIRPS rainfall grids | Rainfall, ~5 km, since 1981 | Download | Public domain ✅ | Rainfall below district level |
| Malaria Atlas Project travel time | Travel time to cities and healthcare, 1 km | Download | CC BY 3.0 ✅ | Access space without building a router |
| NASA FIRMS active fire | Fire detections, 375 m, daily | HDX / NASA | CC0 ✅ (HDX) | A live layer (D-020) |
| Stanford scans of "Ceylon one inch" maps | 72-sheet topographic series, 1:63,360 | Stanford library | Index record says public domain ✅; individual sheets not checked ❓ | **Historical land use, tanks, roads and place names.** Needs georeferencing and extraction: a real project |
| Meta high-resolution population (2020) | Modelled population, 30 m | HDX | CC BY ✅ | Another modelled grid; the WorldPop test suggests caution |
| Meta social connectedness index | Friendship links between regions | HDX | CC0 ✅ | Relations between districts; check which Sri Lankan units it uses |
| UNDP/other Ditwah assessments | Flood exposure reports | Reports | per document | Context for the flood layers |
| Kelani and Attanagalu LULC 1991/2001/2012 | Land use change | World Bank | CC BY 4.0 ✅ (earlier note) | Regional history |

## 5. Needs permission (no reuse terms found)

See [permissions-and-authorities.md](permissions-and-authorities.md) for who controls each and the process.

| Source | What is visible | Evidence |
|---|---|---|
| **NSDI geoportal services** | 670 layers. Counts queried ✅: land use 1:10,000 (513,157 polygons), landslide hazard (312,403), village tanks (10,739), anicuts (12,900), tank cascades (1,676), reservoirs (1,819), forest boundaries (10,252), protected areas (119), schools (10,155), hospitals (1,528), places of worship (14,518), archaeological sites (1,745, trilingual names), place names (134,717), agro-ecological zones (48), rain gauges (1,085), building footprints (85,514), parcel fabrics (122,314) | `copyrightText` is empty on every service ✅; no terms page found ❌ |
| Survey Department topographic data | 1:50,000 and 1:10,000 vector databases 🟡 | Sold by the Department 🟡; price list and licence not found ❌ |
| Department of Census and Statistics | Census tables (in use under D-030), GN reference | No terms ✅ (earlier work) |
| Election Commission | Results, electors | No terms ✅ (earlier work) |
| Irrigation Department, Mahaweli Authority | Reservoir levels, issued to the press | No data portal found ❌ |
| Disaster Management Centre | River levels, situation reports | Site reachable ✅; terms not read ❓ |
| Department of Meteorology | Rainfall, stations | Site reachable ✅; terms and fees not found ❌ |
| NBRO | Landslide hazard zonation | Site reachable ✅; the hazard layer is also in NSDI |
| data.gov.lk | Open data portal | **Unreachable** from this machine on 2026-11-17 (timeout) ❌; a search result says licences vary per dataset 🟡 |

## 6. Restricted (do not use for the platform as planned)

| Source | Terms | Consequence |
|---|---|---|
| WDPA / Protected Planet (UNEP-WCMC) | No commercial use of the data or anything derived without written permission ✅ | Not acquired. Protected areas would have to come from OSM, Wikidata, or the Department of Wildlife Conservation by permission |
| Ookla speedtest tiles | CC BY-NC-SA 4.0 ✅ | Non-commercial and share-alike: conflicts with commercial services (rule 4) |
| Meta relative wealth index | CC BY-NC 4.0 ✅ (HDX licence text) | Non-commercial; also a modelled estimate about people |
| DHS sub-national data on HDX | CC BY-ND text in the HDX licence field ✅ | No derivatives |
| ACLED | Own terms ("Other" on HDX) ❓ | Not assessed; assume restricted |
| NSDI layers with personal fields | The building footprint layer has an `owner` field ✅ | Even with permission, personal fields must be dropped (rule 11) |

## 7. What becomes possible by combining them

Done in this run (numbers in [findings](findings-2026-11-17.md)):

1. **Two definitions of "urban" side by side**: the census's administrative sector against a satellite-era density rule, by district.
2. **A test of gridded population against the census**: WorldPop 2025 against Census 2024 for 13,962 GN divisions.
3. **Built-up growth since 1975** for every DS division, next to its 2012→2024 population change (the Change lens can now show land as well as people).
4. **Buildings against housing units**: how many mapped footprints per census-occupied housing unit, by district and GN.
5. **Landscape twins**: places that look alike from above but differ in who lives there, and the reverse.
6. **An activity signature per place** from listed places (for example the share of lodging).

Not yet done, now within reach:

- **Flood exposure of the 2025 floods per GN**, from three independent satellite products, shown as conflicting claims (D-019).
- **Tank country**: village tanks and cascades per GN (surface water is in; the official tank inventory needs NSDI permission; GeoNames lists 6,761 reservoirs under CC BY).
- **Estate landscapes**: GeoNames' 5,829 estate records with tree cover, slope and the census "estate" sector.
- **Rainfall and vegetation rhythm** for each district since 1981 and 2002.
- **A dasymetric 2024 population grid** of our own: Census 2024 GN totals spread over 8.9 million footprints (multi-scale-features.md §2.3, option 3). The WorldPop test is the argument for it.
- **Historical land use** from the one-inch series, compared with WorldCover 2021.
- **Tree canopy at 1 m** for urban greenery (OPP-37).

## 8. Sources

- HDX CKAN API, `package_search?fq=groups:lka` (read 2026-11-17)
- NSDI ArcGIS service directory, `gisapps.nsdi.gov.lk/server/rest/services` (read 2026-11-17; directory and count queries only, paced)
- Licence pages: [Global Forest Change](https://storage.googleapis.com/earthenginepartners-hansen/GFC-2024-v1.12/download.html), [ESA WorldCover](https://esa-worldcover.org/en/data-access), [Copernicus DEM on AWS](https://registry.opendata.aws/copernicus-dem/), [Global Surface Water](https://global-surface-water.appspot.com/download), [GHSL](https://human-settlement.emergency.copernicus.eu/download.php), [GeoNames](https://www.geonames.org/export/), [Geofabrik](https://download.geofabrik.de/asia/sri-lanka.html), [Wikidata licensing](https://www.wikidata.org/wiki/Wikidata:Licensing), [WorldPop hub](https://hub.worldpop.org/geodata/listing?id=135), [Open Buildings](https://sites.research.google/gr/open-buildings/), [Meta canopy height on AWS](https://registry.opendata.aws/dataforgood-fb-forests/), [CHIRPS](https://www.chc.ucsb.edu/data/chirps), [Malaria Atlas Project](https://malariaatlas.org/open-access-policy/), [WDPA licence](https://www.unep-wcmc.org/en/wdpa-data-license), [Ookla on AWS](https://registry.opendata.aws/speedtest-global-performance/), [HydroRIVERS](https://www.hydrosheds.org/products/hydrorivers), [Global Mangrove Watch](https://zenodo.org/records/6894273), [AlphaEarth](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL)
- [Stanford: Ceylon one inch, maps index](https://purl.stanford.edu/yk696bp5456)
- [ICTA: National Spatial Data Infrastructure](https://www.icta.lk/projects/digital-government/national-spatial-data-infrastructure-nsdi) (search result, not opened)
- [UN-GGIM Sri Lanka country report 2019](https://ggim.un.org/country-reports/documents/SriLanka-2019-country-report.pdf) (search result, not opened)
