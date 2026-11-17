# Permissions and authorities: spatial data that cannot be reused yet

2026-11-17 · For the lead · Companion to the [discovery catalogue](discovery-catalogue.md) §5 · Outreach rule: agents draft, the lead sends (AGENTS rule 9)

Legend: ✅ verified directly on 2026-11-17 · 🟡 stated by a secondary source · ❌ not found · ❓ assumption.

**No contact names, emails or phone numbers are given here unless they are already recorded in `catalog/sources/` with their evidence.** Where a contact is needed, the row says where to look. Nothing was requested from anyone; no letter was sent.

## 1. The main finding

The government's own geoportal exposes a large, well-structured spatial database through a public service directory, **with no reuse terms at all**:

- 72 map and feature services, 670 layers ✅ ([inventory](nsdi-layer-inventory-2026-11-17.csv)).
- Every service's `copyrightText` field is empty ✅.
- No terms-of-use page for the geoportal was found ❌. A search found only ICTA's 2016 terms of reference asking a consultant to *draft* a national spatial data policy, and terms on the separate open data portal 🟡.
- The services answer anonymous queries. That is access, not permission. Only the directory, layer descriptions and feature **counts** were read; no features were downloaded.

Until terms exist, these layers stay *needs permission*, as the admin boundaries from the same server already are (`catalog/sources/nsdi.yaml`).

## 2. What to ask for, in order of value

| # | Layers | Count ✅ | Why it matters | Likely custodian (as named in the layer or its fields) |
|---|---|---:|---|---|
| 1 | Land use 1:10,000 (`SLNSDI/LUPPD_10K`) | 513,157 polygons | The only detailed national land-use map; with WorldCover it gives official and satellite views side by side | Land Use Policy Planning Department ❓ (from the service name "LUPPD") |
| 2 | Village tanks, anicuts, cascades, reservoirs, basins, watersheds (`SLNSDI/Inland_Waters`) | 10,739 tanks; 12,900 anicuts; 1,676 cascades; 1,819 reservoirs; 103 basins | The tank-cascade system is distinctive to Sri Lanka and absent from every global dataset | Not stated in the service ❓ (Irrigation Department, Department of Agrarian Development or the Survey Department are possibilities, not verified) |
| 3 | Landslide hazard zonation (`SLNSDI/LHazard_10K`, `Geo_Scientific_Information/Landslide`) | 312,403 and 145,145 polygons | Hazard exposure per GN | National Building Research Organisation ❓ (NBRO publishes landslide hazard maps; the service does not name it) |
| 4 | Schools and hospitals (`Projects/Schools`, `Projects/Hospital_All`) | 10,155 and 1,528 points | Official facility registers with census numbers and types; would replace the Giga and OSM lists | Ministry of Education; Ministry of Health ❓ |
| 5 | Archaeological sites, places of worship, place names | 1,745 (trilingual); 14,518; 134,717 | A trilingual gazetteer and heritage layer | Department of Archaeology; Survey Department ❓ |
| 6 | Forest boundaries, protected areas | 10,252; 119 | The open alternative to WDPA, whose terms forbid commercial use | Forest Department; Department of Wildlife Conservation ❓ |
| 7 | Agro-ecological zones, soils, climate zones, rain-gauge stations | 48; 31; 3; 1,085 | Stable physical regions for comparisons and typologies | Department of Agriculture; Department of Meteorology ❓ |
| 8 | Roads (RDA), railways | 2,040 railway lines | Official network for access measures | Road Development Authority; Sri Lanka Railways ❓ |
| — | Building footprints, parcel fabrics | 85,514; 122,314 | **Do not request as they are.** The footprint layer has an `owner` field ✅ and parcels raise claimant data (multi-scale-features.md §6). If ever requested: geometry and land use only | Survey Department |

The custodians marked ❓ are inferred from names. The NSDI metadata catalogue (`catalog.nsdi.gov.lk`, reachable ✅, a JavaScript application not read) is said to record ownership, age, quality and scale for each layer 🟡. **Reading it is the first step**: it should name the owner of each layer without guessing.

## 3. The process, as far as it can be established

| Step | What is known | Status |
|---|---|---|
| 1. Who runs the NSDI | The Information and Communication Technology Agency (ICTA) lists the NSDI as its project, with "over 27 organizations" contributing "over 130 spatial data layers" 🟡 (search result of ICTA's project page, not opened) | 🟡 |
| 2. Is there a data policy? | A draft National Data Sharing Policy is said to exist on the open data portal 🟡. The portal was unreachable from this machine ❌ | ❓ |
| 3. Who can grant reuse | Not established. It may be ICTA for the platform and each agency for its own layers ❓ | ❌ |
| 4. Fees | The Survey Department sells data: for example Rs. 750 per GPS control point ✅ (rate schedule, earlier work in multi-scale-features.md). Fees for vector map data were not found ❌ | ❌ |
| 5. The legal route if informal requests fail | The Right to Information Act is named in a governance assessment as part of the framework 🟡. An RTI request gets *access* to information; it does not by itself grant a licence to republish ❓ (a lawyer should confirm) | ❓ |
| 6. Map-publication approval | Whether publishing detailed maps needs Survey Department approval is still unverified ❓ (open since multi-scale-features.md §6) | ❓ |

## 4. Recommended action (the lead decides and sends)

1. **One letter to ICTA about the NSDI**, not one per agency: ask (a) what terms govern reuse of the layers served at `gisapps.nsdi.gov.lk`, (b) whether there is a published data-sharing policy, (c) who the custodian and contact is for the eight layer groups above. Offer attribution, the catalogue's provenance record, and corrections back. An agent can draft it (prompt R04) once the lead agrees; none is drafted here.
2. **Wait for that answer before writing to custodians.** The answer decides whether there are eight conversations or one.
3. **Keep using the open substitutes meanwhile**, labelled for what they are: Giga for schools, OpenStreetMap for health facilities, WorldCover for land cover, Global Surface Water for tanks, GeoNames and Wikidata for names.
4. **Do not scrape the NSDI layers "for internal use"** beyond the cross-check the lead already approved for boundaries. A private copy tempts publication, and the terms may turn out to forbid it.

## 5. Other sources that need terms

| Source | What is missing | Existing record |
|---|---|---|
| Department of Census and Statistics | Reuse terms (letter sent; D-030 covers non-commercial publication meanwhile) | `catalog/sources/dcs.yaml`, [letter](../../outreach/2026-11-07-dcs-reuse-terms.md) |
| Election Commission | Reuse terms (D-039) | `catalog/sources/election-commission.yaml` |
| Survey Department | Price list and licence for topographic vectors | `catalog/sources/survey-department.yaml` |
| Department of Meteorology, Irrigation Department, Mahaweli Authority, Disaster Management Centre | Whether station, rainfall, reservoir and river-level data can be reused, and in what form it is issued | not yet in the catalogue; add a source entry when first investigated (R01) |
| UNEP-WCMC (WDPA) | Written permission for commercial use, if protected-area polygons are ever wanted from this source ✅ (terms read) | discovery catalogue §6 |

## 6. Sources

- NSDI service directory and layer descriptions (read 2026-11-17)
- [ICTA: NSDI project page](https://www.icta.lk/projects/digital-government/national-spatial-data-infrastructure-nsdi), [ICTA scope of services, 2016](https://www.icta.lk/icta-assets/uploads/2016/06/Brief-of-the-Scope-of-Services1.pdf), [data.gov.lk: about data sharing](https://data.gov.lk/about-data-sharing) (search results; pages not opened or unreachable)
- [UN-GGIM Sri Lanka country report 2019](https://ggim.un.org/country-reports/documents/SriLanka-2019-country-report.pdf) (search result)
- [WDPA data licence](https://www.unep-wcmc.org/en/wdpa-data-license) (read)
