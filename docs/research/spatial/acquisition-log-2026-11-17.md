# Acquisition log: open spatial data, 2026-11-17

Legend: ✅ verified directly · 🟡 from a secondary source · ❌ not found / failed · ❓ assumption.

Every file below was fetched on 2026-11-17 by `uv run slf spatial snapshot` from the URL in
[`catalog/acquisition/spatial-manifest.csv`](../../../catalog/acquisition/spatial-manifest.csv) and stored unchanged under
`pipeline/data/raw/<source>/<dataset>/<retrieval time>/` with a `.meta.json` beside it (URL, retrieval
time, sha256, licence note). Sizes, times and hashes are copied from those files by the command, not typed ✅.

- **Files held:** 112 on the laptop (1,147.6 MB) and 3 Overture extracts on the external drive.
- **Failed:** 1. `https://ourairports.com/countries/LK/airports.csv` was refused because the server's TLS certificate had expired ❌. Certificate checks were not turned off; the row was removed from the manifest. Retry later.
- **Originals and processed data are separate:** originals are under `raw/` and are never edited; everything derived is under `pipeline/data/build/landscape/`.
- **One wording error in the stored notes:** the 12 Copernicus DEM `.meta.json` files carry the licence note "free, any use, attribution", written before the licence was checked. Only the registry page was read, not the licence PDF, so the manifest now says so. The stored notes cannot be edited (raw is immutable); treat the manifest and `catalog/sources/copernicus.yaml` as correct.

## Where the data is

| Location | What | Size |
|---|---|---:|
| `pipeline/data/raw/` (laptop, not in Git) | The 112 files below | 1,148 MB |
| `/Volumes/Earth for Air/srilankafacts-data/raw/overture/` (external drive) | Overture places and buildings extracts | 901 MB |
| `/Volumes/Earth for Air/srilankafacts-data/tmp/failed-20261117T0914Z/` | A 5 KB partial file from a buildings extract that timed out; moved out of `raw/`, safe to delete | 0 MB |
| `pipeline/data/build/landscape/` (laptop, not in Git) | Derived observations, vectors, QA, resolved feature tables | see QA |
| Google Drive | Documentation copies only (see the PR report); the data files are not on Drive | |

Nothing else on the external drive was read or changed beyond listing its top-level folder to choose a folder name.

## Overture extracts (external drive)

Overture publishes global files, so these are extracts written by `uv run slf spatial overture`, not Overture's own bytes. Each records the release and the filter, so it can be repeated.

| Dataset | Release | Rows | Size (bytes) | Retrieved (UTC) | sha256 (first 16) | Columns dropped at extract |
|---|---|---:|---:|---|---|---|
| overture-buildings | 2026-10-21.0 | 8,886,949 | 877850209 | 20261117T035054Z | `e2395801f2a68595` | facade_color, facade_material, has_parts, is_underground, level, min_floor, min_height, num_floors_underground, roof_color, roof_direction, roof_height, roof_material, roof_orientation, version |
| overture-places | 2026-10-21.0 | 139,056 | 11767148 | 20261117T034319Z | `cb37e1a05f4ad53c` | addresses, basic_category, emails, operating_status, phones, socials, taxonomy, version, websites |
| overture-places | 2026-10-21.0 | 139,056 | 11872894 | 20261117T035210Z | `aff33e753868e5a3` | addresses, emails, phones, socials, version, websites |

Two places extracts exist: the first dropped the category columns by mistake, so a second was taken; the build uses the newer one. Addresses, phone numbers, emails, websites and social links are never extracted (AGENTS rule 11).

## Files held on the laptop

| Source | Dataset | File | Size (bytes) | Retrieved (UTC) | sha256 (first 16) | Licence |
|---|---|---|---:|---|---|---|
| copernicus | copernicus-dem-glo30 | Copernicus_DSM_COG_10_N05_00_E080_00_DEM.tif | 1213814 | 20261117T033209Z | `4f8276c4efe55a68` | Copernicus DEM GLO-30 Public licence (free of charge; terms in the licence PDF, not yet read in full) |
| copernicus | copernicus-dem-glo30 | Copernicus_DSM_COG_10_N06_00_E079_00_DEM.tif | 2995555 | 20261117T033212Z | `74c8e6a977714030` | Copernicus DEM GLO-30 Public licence (free of charge; terms in the licence PDF, not yet read in full) |
| copernicus | copernicus-dem-glo30 | Copernicus_DSM_COG_10_N06_00_E080_00_DEM.tif | 47653237 | 20261117T033232Z | `bfa222f4daa21161` | Copernicus DEM GLO-30 Public licence (free of charge; terms in the licence PDF, not yet read in full) |
| copernicus | copernicus-dem-glo30 | Copernicus_DSM_COG_10_N06_00_E081_00_DEM.tif | 27972443 | 20261117T033243Z | `5df3709dcf6fe531` | Copernicus DEM GLO-30 Public licence (free of charge; terms in the licence PDF, not yet read in full) |
| copernicus | copernicus-dem-glo30 | Copernicus_DSM_COG_10_N07_00_E079_00_DEM.tif | 10303928 | 20261117T033252Z | `f398794c8b79efe8` | Copernicus DEM GLO-30 Public licence (free of charge; terms in the licence PDF, not yet read in full) |
| copernicus | copernicus-dem-glo30 | Copernicus_DSM_COG_10_N07_00_E080_00_DEM.tif | 48214379 | 20261117T033319Z | `b9389797c27105f1` | Copernicus DEM GLO-30 Public licence (free of charge; terms in the licence PDF, not yet read in full) |
| copernicus | copernicus-dem-glo30 | Copernicus_DSM_COG_10_N07_00_E081_00_DEM.tif | 36719490 | 20261117T033331Z | `3d9774e46eb4f2fc` | Copernicus DEM GLO-30 Public licence (free of charge; terms in the licence PDF, not yet read in full) |
| copernicus | copernicus-dem-glo30 | Copernicus_DSM_COG_10_N08_00_E079_00_DEM.tif | 7163593 | 20261117T033335Z | `aed165b96429d47f` | Copernicus DEM GLO-30 Public licence (free of charge; terms in the licence PDF, not yet read in full) |
| copernicus | copernicus-dem-glo30 | Copernicus_DSM_COG_10_N08_00_E080_00_DEM.tif | 47178963 | 20261117T033404Z | `1a59eb43c6fcf914` | Copernicus DEM GLO-30 Public licence (free of charge; terms in the licence PDF, not yet read in full) |
| copernicus | copernicus-dem-glo30 | Copernicus_DSM_COG_10_N08_00_E081_00_DEM.tif | 13938291 | 20261117T033417Z | `2e3adc419e810123` | Copernicus DEM GLO-30 Public licence (free of charge; terms in the licence PDF, not yet read in full) |
| copernicus | copernicus-dem-glo30 | Copernicus_DSM_COG_10_N09_00_E079_00_DEM.tif | 4583187 | 20261117T033420Z | `f94b30ecbb3e0a54` | Copernicus DEM GLO-30 Public licence (free of charge; terms in the licence PDF, not yet read in full) |
| copernicus | copernicus-dem-glo30 | Copernicus_DSM_COG_10_N09_00_E080_00_DEM.tif | 22354859 | 20261117T033432Z | `befd264ff4cc8b0c` | Copernicus DEM GLO-30 Public licence (free of charge; terms in the licence PDF, not yet read in full) |
| esa | esa-worldcover-2021 | ESA_WorldCover_10m_2021_v200_N03E078_Map.tif | 2233905 | 20261117T033436Z | `e6ee55a914127318` | CC BY 4.0 |
| esa | esa-worldcover-2021 | ESA_WorldCover_10m_2021_v200_N06E078_Map.tif | 34407738 | 20261117T033445Z | `a2de57f330a5a2e3` | CC BY 4.0 |
| esa | esa-worldcover-2021 | ESA_WorldCover_10m_2021_v200_N06E081_Map.tif | 19310758 | 20261117T033453Z | `484ca627ac65c6c6` | CC BY 4.0 |
| esa | esa-worldcover-2021 | ESA_WorldCover_10m_2021_v200_N09E078_Map.tif | 92254923 | 20261117T033516Z | `ef5465394f62ee33` | CC BY 4.0 |
| umd-glad | hansen-global-forest-change | Hansen_GFC-2024-v1.12_lossyear_10N_070E.tif | 15489803 | 20261117T033521Z | `6553ca6d035fe118` | CC BY 4.0 |
| umd-glad | hansen-global-forest-change | Hansen_GFC-2024-v1.12_lossyear_10N_080E.tif | 17206412 | 20261117T033528Z | `8e770dee00b4e15e` | CC BY 4.0 |
| umd-glad | hansen-global-forest-change | Hansen_GFC-2024-v1.12_treecover2000_10N_070E.tif | 39994094 | 20261117T033539Z | `dae0780148920a76` | CC BY 4.0 |
| umd-glad | hansen-global-forest-change | Hansen_GFC-2024-v1.12_treecover2000_10N_080E.tif | 64754171 | 20261117T033555Z | `28dca31f9d545e9b` | CC BY 4.0 |
| jrc | jrc-global-surface-water | occurrence_70E_10Nv1_4_2021.tif | 33529142 | 20261117T033604Z | `26d1da1918ed0447` | Copernicus Programme: free, full and open; attribution |
| jrc | jrc-global-surface-water | occurrence_80E_10Nv1_4_2021.tif | 18380630 | 20261117T033611Z | `1f8d2ec984601e02` | Copernicus Programme: free, full and open; attribution |
| ghsl | ghsl-built-up | GHS_BUILT_S_E1975_GLOBE_R2023A_54009_100_V1_0_R8_C26.zip | 8692543 | 20261117T033625Z | `573d78dd454baff3` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E1975_GLOBE_R2023A_54009_100_V1_0_R8_C27.zip | 1695956 | 20261117T033629Z | `a5163020ce05e596` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E1975_GLOBE_R2023A_54009_100_V1_0_R9_C26.zip | 1533965 | 20261117T033634Z | `9eef8cfd90ca3dce` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E1975_GLOBE_R2023A_54009_100_V1_0_R9_C27.zip | 2330860 | 20261117T033641Z | `58b6c978ae8eb052` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E1980_GLOBE_R2023A_54009_100_V1_0_R8_C26.zip | 9831506 | 20261117T033647Z | `82b7484caf76cf3c` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E1980_GLOBE_R2023A_54009_100_V1_0_R8_C27.zip | 1720540 | 20261117T033651Z | `7ee5b986c0570be2` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E1980_GLOBE_R2023A_54009_100_V1_0_R9_C26.zip | 1542978 | 20261117T033658Z | `fc08c8435bbff977` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E1980_GLOBE_R2023A_54009_100_V1_0_R9_C27.zip | 2462302 | 20261117T033705Z | `7006d0c04d6e25e7` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E1985_GLOBE_R2023A_54009_100_V1_0_R8_C26.zip | 10907337 | 20261117T033711Z | `f94b04f324913214` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E1985_GLOBE_R2023A_54009_100_V1_0_R8_C27.zip | 1743687 | 20261117T033718Z | `dbbe3daefc4f5637` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E1985_GLOBE_R2023A_54009_100_V1_0_R9_C26.zip | 1549828 | 20261117T033725Z | `1c12958ff43e7df3` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E1985_GLOBE_R2023A_54009_100_V1_0_R9_C27.zip | 2590895 | 20261117T033735Z | `ac6b1c0935313f26` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E1990_GLOBE_R2023A_54009_100_V1_0_R8_C26.zip | 11990785 | 20261117T033751Z | `8126cab2d0ff5885` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E1990_GLOBE_R2023A_54009_100_V1_0_R8_C27.zip | 1767110 | 20261117T033758Z | `07bc0bf924643bbe` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E1990_GLOBE_R2023A_54009_100_V1_0_R9_C26.zip | 1557928 | 20261117T033802Z | `5409d7cff32440d9` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E1990_GLOBE_R2023A_54009_100_V1_0_R9_C27.zip | 2715845 | 20261117T033807Z | `cd4a3f4275691cfa` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E1995_GLOBE_R2023A_54009_100_V1_0_R8_C26.zip | 12730683 | 20261117T033823Z | `7737bf9daaaf3980` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E1995_GLOBE_R2023A_54009_100_V1_0_R8_C27.zip | 1793754 | 20261117T033827Z | `782690e8fa2d3181` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E1995_GLOBE_R2023A_54009_100_V1_0_R9_C26.zip | 1559116 | 20261117T033832Z | `f68e90beef557b2c` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E1995_GLOBE_R2023A_54009_100_V1_0_R9_C27.zip | 2857768 | 20261117T033837Z | `2cea8bbc3476de64` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E2000_GLOBE_R2023A_54009_100_V1_0_R8_C26.zip | 13409410 | 20261117T033850Z | `977532cec09c45b5` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E2000_GLOBE_R2023A_54009_100_V1_0_R8_C27.zip | 1818270 | 20261117T033854Z | `5ae6f6bcceb5cddd` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E2000_GLOBE_R2023A_54009_100_V1_0_R9_C26.zip | 1562528 | 20261117T033859Z | `a9b1aa0a83bd0602` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E2000_GLOBE_R2023A_54009_100_V1_0_R9_C27.zip | 2987863 | 20261117T033907Z | `c5477446992d2e1e` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E2005_GLOBE_R2023A_54009_100_V1_0_R8_C26.zip | 14900921 | 20261117T033924Z | `2fd796bf51a7415b` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E2005_GLOBE_R2023A_54009_100_V1_0_R8_C27.zip | 1850793 | 20261117T033933Z | `fae4b1e06d2cb109` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E2005_GLOBE_R2023A_54009_100_V1_0_R9_C26.zip | 1565350 | 20261117T033938Z | `2fc4635a536d1681` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E2005_GLOBE_R2023A_54009_100_V1_0_R9_C27.zip | 3206131 | 20261117T033944Z | `e0bd7973fdd18b79` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E2010_GLOBE_R2023A_54009_100_V1_0_R8_C26.zip | 16405026 | 20261117T033951Z | `a89a5fb88a061c8e` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E2010_GLOBE_R2023A_54009_100_V1_0_R8_C27.zip | 1883444 | 20261117T034001Z | `a13809609b38eccd` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E2010_GLOBE_R2023A_54009_100_V1_0_R9_C26.zip | 1566647 | 20261117T034006Z | `cde727eac14048c9` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E2010_GLOBE_R2023A_54009_100_V1_0_R9_C27.zip | 3426447 | 20261117T034011Z | `59e28cf6ad6cc109` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E2015_GLOBE_R2023A_54009_100_V1_0_R8_C26.zip | 18616040 | 20261117T034023Z | `3e29114f819aa0ab` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E2015_GLOBE_R2023A_54009_100_V1_0_R8_C27.zip | 1932939 | 20261117T034028Z | `3ecfdc6a2d39ed0e` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E2015_GLOBE_R2023A_54009_100_V1_0_R9_C26.zip | 1570068 | 20261117T034033Z | `841c8b06fb9b466b` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E2015_GLOBE_R2023A_54009_100_V1_0_R9_C27.zip | 3856931 | 20261117T034037Z | `f992b1d09e8e64e5` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E2020_GLOBE_R2023A_54009_100_V1_0_R8_C26.zip | 20429152 | 20261117T034054Z | `92df67ba1f1ad0da` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E2020_GLOBE_R2023A_54009_100_V1_0_R8_C27.zip | 1969475 | 20261117T034100Z | `ff90d233851293fa` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E2020_GLOBE_R2023A_54009_100_V1_0_R9_C26.zip | 1573234 | 20261117T034105Z | `a9ae86633604a862` | CC BY 4.0 |
| ghsl | ghsl-built-up | GHS_BUILT_S_E2020_GLOBE_R2023A_54009_100_V1_0_R9_C27.zip | 4173435 | 20261117T034114Z | `54029193ebd1b916` | CC BY 4.0 |
| ghsl | ghsl-settlement-model | GHS_SMOD_E2020_GLOBE_R2023A_54009_1000_V2_0_R8_C26.zip | 1565933 | 20261117T034118Z | `bd59a5637140c83f` | CC BY 4.0 |
| ghsl | ghsl-building-height | GHS_BUILT_H_ANBH_E2018_GLOBE_R2023A_54009_100_V1_0_R8_C26.zip | 13876615 | 20261117T034129Z | `557fbe4658a16c6d` | CC BY 4.0 |
| ghsl | ghsl-settlement-model | GHS_SMOD_E2020_GLOBE_R2023A_54009_1000_V2_0_R8_C27.zip | 1434755 | 20261117T034135Z | `1a5ea6fa61e87e72` | CC BY 4.0 |
| ghsl | ghsl-building-height | GHS_BUILT_H_ANBH_E2018_GLOBE_R2023A_54009_100_V1_0_R8_C27.zip | 1696384 | 20261117T034139Z | `85320ea9c2971c20` | CC BY 4.0 |
| ghsl | ghsl-settlement-model | GHS_SMOD_E2020_GLOBE_R2023A_54009_1000_V2_0_R9_C26.zip | 1435264 | 20261117T034148Z | `64758d8beeeaa81f` | CC BY 4.0 |
| ghsl | ghsl-building-height | GHS_BUILT_H_ANBH_E2018_GLOBE_R2023A_54009_100_V1_0_R9_C26.zip | 1809503 | 20261117T034157Z | `7d2e821030f9cbe8` | CC BY 4.0 |
| ghsl | ghsl-settlement-model | GHS_SMOD_E2020_GLOBE_R2023A_54009_1000_V2_0_R9_C27.zip | 1442864 | 20261117T034205Z | `155fe31782d9a940` | CC BY 4.0 |
| ghsl | ghsl-building-height | GHS_BUILT_H_ANBH_E2018_GLOBE_R2023A_54009_100_V1_0_R9_C27.zip | 2966762 | 20261117T034216Z | `ccfb1b3d51c437f2` | CC BY 4.0 |
| worldpop | worldpop-population-100m | lka_pop_2025_CN_100m_R2025A_v1.tif | 18492647 | 20261117T034318Z | `4c781514ba619dc0` | CC BY 4.0 |
| worldpop | worldpop-population-100m | Global2_Release_Statement_R2025A_v1.pdf | 568633 | 20261117T034322Z | `1a23e31f49102b59` | CC BY 4.0 |
| osm | osm-sri-lanka | sri-lanka-latest.osm.pbf | 144647996 | 20261117T034413Z | `2f3b68a8f8e6b6cf` | ODbL 1.0 |
| geonames | geonames-lk | LK.zip | 1515587 | 20261117T034416Z | `c40421c6d680767e` | CC BY 4.0 |
| giga | giga-school-locations | sri-lanka-school-geolocation-connectivity-data.csv | 783639 | 20261117T034424Z | `b706c8a7d39e9571` | Creative Commons Attribution International (CC BY) (HDX: sri-lanka-school-geolocation-and-connectivity-status) |
| giga | giga-school-locations | schema-giga-columns.csv | 440 | 20261117T034427Z | `c82a1bd579d0b4d8` | Creative Commons Attribution International (CC BY) (HDX: sri-lanka-school-geolocation-and-connectivity-status) |
| kontur | kontur-population-h3 | kontur_population_LK_20231101.gpkg.gz | 3213570 | 20261117T034432Z | `f9a7f22c321ecf49` | Creative Commons Attribution International (CC BY) (HDX: kontur-population-sri-lanka) |
| healthsites | healthsites-lk | sri-lanka.geojson | 2001610 | 20261117T034439Z | `512417f64149f23d` | ODbL (HDX: sri-lanka-healthsites) |
| noaa-ncei | ibtracs-storm-tracks | ibtracs_all_list_v04r01_lka.csv | 7496559 | 20261117T034453Z | `6078d72af7e25929` | Creative Commons Attribution for Intergovernmental Organisations (CC BY-IGO) (HDX: lka-ibtracs-tropical-storm-tracks) |
| unosat | unosat-ditwah-flood-2025 | FL20251128LKA_gdb.zip | 57828641 | 20261117T034522Z | `f1fa386eee4c9aa8` | Creative Commons Attribution Share-Alike (CC BY-SA) (HDX: unosat-live-web-map-cyclone-ditwah-and-floods-in-sri-lanka-november-2025) |
| unosat | unosat-ditwah-flood-2025 | UNOSAT_PopulationExposure_FL20251128LKA_SriLanka_26_To_30_Nov2025.xlsx | 14868 | 20261117T034524Z | `629faafee2c04273` | Creative Commons Attribution Share-Alike (CC BY-SA) (HDX: unosat-live-web-map-cyclone-ditwah-and-floods-in-sri-lanka-november-2025) |
| wfp | wfp-adam-flood-2025 | lka_wfpadam_flood_20251201.zip | 44794 | 20261117T034528Z | `37cda95a0b6e28a0` | Creative Commons Attribution Share-Alike (CC BY-SA) (HDX: lka-flood-fl-20251201-lka-00) |
| wfp | wfp-adam-flood-2025 | lka_wfpadam_flood_20251201.xlsx | 20573 | 20261117T034531Z | `47e9b8346b9d6ec6` | Creative Commons Attribution Share-Alike (CC BY-SA) (HDX: lka-flood-fl-20251201-lka-00) |
| undrr-desinventar | desinventar-sri-lanka | srilanka.zip | 6525937 | 20261117T034610Z | `4982cfd537467095` | Creative Commons Attribution International (CC BY) (HDX: disaster-loss-and-damage-dataset-for-sri-lanka) |
| undrr-desinventar | desinventar-sri-lanka | di_report-srilanka.xls | 12157503 | 20261117T034627Z | `958134d51620a7c4` | Creative Commons Attribution International (CC BY) (HDX: disaster-loss-and-damage-dataset-for-sri-lanka) |
| undrr-desinventar | desinventar-sri-lanka | datadictionary.docx | 139668 | 20261117T034631Z | `e03b169af556b122` | Creative Commons Attribution International (CC BY) (HDX: disaster-loss-and-damage-dataset-for-sri-lanka) |
| wfp | wfp-food-prices | wfp_food_prices_lka.csv | 4402444 | 20261117T034639Z | `06490342f1985e2d` | Creative Commons Attribution for Intergovernmental Organisations (CC BY-IGO) (HDX: wfp-food-prices-for-sri-lanka) |
| wfp | wfp-food-prices | wfp_markets_lka.csv | 7713 | 20261117T034642Z | `9540f5b87b5a1e23` | Creative Commons Attribution for Intergovernmental Organisations (CC BY-IGO) (HDX: wfp-food-prices-for-sri-lanka) |
| ctrees | ctrees-aboveground-biomass | lka_ctrees_aboveground_biomass.tif | 13488669 | 20261117T034652Z | `1e7761c39e179df8` | Creative Commons Attribution International (CC BY) (HDX: lka-ctrees-aboveground-biomass) |
| climate-trace | climate-trace-sources | lka_ch4_source.csv | 1139133 | 20261117T034700Z | `d0326ffafc3b261c` | Creative Commons Attribution International (CC BY) (HDX: lka-climate-trace) |
| climate-trace | climate-trace-sources | lka_co2e_20yr_source.csv | 1183774 | 20261117T034721Z | `6328f6817d1ba5e6` | Creative Commons Attribution International (CC BY) (HDX: lka-climate-trace) |
| climate-trace | climate-trace-sources | lka_pm2_5_source.csv | 1155311 | 20261117T034730Z | `1210281eabeeba41` | Creative Commons Attribution International (CC BY) (HDX: lka-climate-trace) |
| heigit | heigit-accessibility | LKA_primary_healthcare_access_long.csv | 296900 | 20261117T034756Z | `a4c98362254eeadf` | Creative Commons Attribution Share-Alike (CC BY-SA) (HDX: sri-lanka-accessibility-indicators) |
| heigit | heigit-accessibility | LKA_hospitals_access_wide.csv | 88159 | 20261117T034758Z | `e1d6e671a0031874` | Creative Commons Attribution Share-Alike (CC BY-SA) (HDX: sri-lanka-accessibility-indicators) |
| heigit | heigit-accessibility | LKA_education_access_long.csv | 78940 | 20261117T034800Z | `30ed8bb9a657d5bf` | Creative Commons Attribution Share-Alike (CC BY-SA) (HDX: sri-lanka-accessibility-indicators) |
| heigit | heigit-accessibility | LKA_education_access_wide.csv | 44537 | 20261117T034802Z | `ceed409e2cf201bc` | Creative Commons Attribution Share-Alike (CC BY-SA) (HDX: sri-lanka-accessibility-indicators) |
| heigit | heigit-accessibility | LKA_primary_healthcare_access_wide.csv | 92921 | 20261117T034803Z | `9a34287a2194e15a` | Creative Commons Attribution Share-Alike (CC BY-SA) (HDX: sri-lanka-accessibility-indicators) |
| heigit | heigit-accessibility | LKA_hospitals_access_long.csv | 273238 | 20261117T034806Z | `99ea9d3aaba3b140` | Creative Commons Attribution Share-Alike (CC BY-SA) (HDX: sri-lanka-accessibility-indicators) |
| heigit | heigit-risk-indicators | LKA_ADM2_facilities.csv | 562 | 20261117T034807Z | `3c08928b49f8e0c6` | Creative Commons Attribution Share-Alike (CC BY-SA) (HDX: sri-lanka---risk-assessment-indicators) |
| heigit | heigit-risk-indicators | LKA_ADM2_coping.csv | 7105 | 20261117T034809Z | `eef3efbe1fbcf942` | Creative Commons Attribution Share-Alike (CC BY-SA) (HDX: sri-lanka---risk-assessment-indicators) |
| heigit | heigit-risk-indicators | LKA_ADM2_access.csv | 2154 | 20261117T034810Z | `1f70f17d142285cf` | Creative Commons Attribution Share-Alike (CC BY-SA) (HDX: sri-lanka---risk-assessment-indicators) |
| heigit | heigit-risk-indicators | LKA_ADM2_rural_population.csv | 1919 | 20261117T034811Z | `20797c2b1d0023bd` | Creative Commons Attribution Share-Alike (CC BY-SA) (HDX: sri-lanka---risk-assessment-indicators) |
| heigit | heigit-risk-indicators | LKA_ADM2_vulnerability.csv | 3476 | 20261117T034813Z | `7678931f87df4726` | Creative Commons Attribution Share-Alike (CC BY-SA) (HDX: sri-lanka---risk-assessment-indicators) |
| heigit | heigit-risk-indicators | LKA_ADM2_demographics.csv | 1828 | 20261117T034814Z | `29820e9f7e61417c` | Creative Commons Attribution Share-Alike (CC BY-SA) (HDX: sri-lanka---risk-assessment-indicators) |
| heigit | heigit-risk-indicators | LKA_ADM2_flood_exposure.csv | 8090 | 20261117T034815Z | `1237e14145cb35bb` | Creative Commons Attribution Share-Alike (CC BY-SA) (HDX: sri-lanka---risk-assessment-indicators) |
| heigit | heigit-risk-indicators | LKA_ADM2_evacuability.csv | 1843 | 20261117T034817Z | `56fb5dc2f21f650e` | Creative Commons Attribution Share-Alike (CC BY-SA) (HDX: sri-lanka---risk-assessment-indicators) |
| heigit | heigit-risk-indicators | LKA_ADM2_rai.csv | 3089 | 20261117T034818Z | `9b3320caea16d254` | Creative Commons Attribution Share-Alike (CC BY-SA) (HDX: sri-lanka---risk-assessment-indicators) |
| wfp | wfp-chirps-rainfall-subnational | lka-rainfall-subnat-full.csv | 6789779 | 20261117T034838Z | `7c623e8152b17818` | Creative Commons Attribution International (CC BY) (HDX: lka-rainfall-subnational) |
| wfp | wfp-ndvi-subnational | lka-ndvi-subnat-full.csv | 1768820 | 20261117T034843Z | `3df6923f9941d338` | Creative Commons Attribution International (CC BY) (HDX: lka-ndvi-subnational) |
| ophi | ophi-mpi | lka_mpi.csv | 1277 | 20261117T034846Z | `470d08703dc58765` | Public Domain / No restrictions (CC0) (HDX: sri-lanka-mpi) |
| eos-rs | eos-rs-ditwah-flood-proxy | eos-rs_20251202_fpm_s1_sri_lanka_cyclone_ditwah_v0.9.zip | 18456513 | 20261117T034854Z | `b940c05f02ea613f` | Creative Commons Attribution International (CC BY) (HDX: eos-rs-sri-lanka-cyclone-ditwah-dec-2025) |
| wikidata | wikidata-places-lk | wikidata-lk-coordinates.json | 6476993 | 20261117T035131Z | `a65beb1c795583ff` | CC0 1.0 |

## Addendum: second acquisition round (external drive)
Held under `/Volumes/Earth for Air/srilankafacts-data/raw/` (✅ sha256 of each file re-computed and equal to its `.meta.json`):
- Global Mangrove Watch v3.0 (CC BY 4.0, Zenodo 6894273): extent GeoTIFF zips for 1996, 2010, 2020 and the union, tiles index, README, country statistics. 7 files, 269.7 MB. Global 1 degree tiles; Sri Lanka tiles to be selected. Not yet integrated.
- HydroRIVERS v10 Asia shapefile, 90.5 MB, and HydroBASINS v1c Asia levels 1-12, 376.4 MB (HydroSHEDS licence: commercial use allowed, redistribution restricted; agreement not yet read, so raw files are not to be republished). Not yet integrated.

## Addendum: third round (searched again and downloaded)
- ✅ Meta/WRI canopy height v2 (CC BY 4.0 per the AWS registry): correct bucket is `dataforgood-fb-data`, prefix `forests/v2/global/dinov3_global_chm_v2_ml3/`. 75 quadkey tiles intersecting Sri Lanka's bounding box plus `tiles.geojson`: 76 files, 13.5 GB. Some tiles are mostly sea, so not all carry land.
- ✅ CHIRPS v3.0 annual global GeoTIFFs 1981-2025 plus README: 46 files, 1.07 GB. Public domain (CC0 waiver on chc.ucsb.edu). The server returned HTTP 429 on several years; they were retried until all were held.
- ✅ Stanford Ceylon one-inch **index** (6 files, shapefile and geojson): public domain per the Stanford record. ❌ The individual sheet scans were not located; only the index is held.
- ❌ NASA FIRMS: the archive download needs an Earthdata login or email code; creating an account is not something an agent should do, so nothing downloaded. Lead action if wanted.
- ✅ All 128 new files re-hashed; each equals its `.meta.json` sha256.
- Not yet integrated into indicators; CRS and imagery year of the canopy tiles unconfirmed.

## Addendum: NASA FIRMS (2026-11-17/18)
- ✅ The lead signed in to Earthdata; four archive requests (852564 MODIS C6.1, 852565 NOAA-20, 852566 NOAA-21, 852567 S-NPP) for Sri Lanka, 2000-11-11 to 2026-11-16, CSV, were submitted and processed within minutes. The agent entered no credentials.
- ✅ 4 zips (3.9 MB) held under the laptop `pipeline/data/raw/nasa-firms/`; sha256 equals meta. Archive rows: MODIS 28,808; S-NPP 102,841; NOAA-20 49,928; NOAA-21 19,978. Archive files end 2026-07/08; recent detections are in the `fire_nrt_*` files.
- ❓ The NASA policy page was not read; rights status is assumed open until read.
- On 2026-11-18 the drive's `raw/` returned "Operation not permitted" (macOS volume permission), so the files were first saved to the laptop root. ✅ Access returned later the same day and a second snapshot of the same four files was taken on the external drive (`raw/nasa-firms/`); all 4 sha256 equal their meta files. The laptop copy remains (raw is never deleted); the lead may remove it.

## Addendum: search of historical archives and agency sources (2026-11-18)
Held on the external drive, all 13 files re-hashed OK:
- ✅ **World Bank land cover 1991/2001/2012 and change** (CC BY 4.0, energydata.info): 9 files, 844 MB. ❌ It is titled "Sri Lanka" but the shapefiles cover only a window of about 108 x 69 km (read from the 2012 file), so it is not a national layer. One file failed mid-transfer once and was retried.
- ✅ **Open soil property maps** (CC BY 4.0, Mendeley Data 10.17632/5sc7njfcyn.2): 2 rar archives, 14.3 MB, nested rars of 9 soil properties; not yet unpacked.
- ✅ **Population trajectory of Ceylon 1891-1946** (CC0, Harvard Dataverse 10.7910/DVN/29209): tab and xlsx, 25 KB.

Found but deliberately **not** downloaded (rights unclear or not downloadable by link):
- 🟡 data.gov.lk (ICTA): many datasets show "License Not Specified"; its terms text was not retrieved. Includes census-year district population 1871-2012.
- 🟡 HDX "Sri Lanka tanks and reservoirs" (Survey Department, 1:250,000): licence "Other"; terms unread.
- 🟡 Irrigation Department Hydrological Annuals and Department of Meteorology bulletins: PDF reports, no terms found; Meteorology has no open station-level download that I found.
- 🟡 National Archives of Sri Lanka map scans (maps.lakdiva.org.lk): non-commercial research and education only.
- 🟡 Wikimedia Commons old maps and Picryl: per-file licences not checked.
- ❓ IFAD tank water-surface maps 2017-2025 (10 m): page found, licence and download link not exposed.
- ❓ DMC and NBRO landslide hazard layers, GSMB geology: nothing found open; belongs with the NSDI permission request.
- ❌ DCS microdata (1981 etc.): access restricted.

## Addendum: restricted holdings acquired at the lead's direction (2026-11-18)
The lead asked for these to be downloaded and said they will request reuse permission themselves (data.gov.lk, Survey Department) or use them non-commercially (National Archives scans). All are **held only**; none is republished, integrated or in a release.
- ✅ **Survey Department tanks and reservoirs, 1:250,000** (HDX, licence "Other"): 1 zip, 0.7 MB, sha256 recorded and re-checked. 1,280 polygons; CRS "SLD-Kandawala" per the .prj (EPSG code not confirmed). Needs the lead's written permission before any use beyond internal analysis.
- ✅ **Ratnatunga collection maps** (maps.lakdiva.org.lk, scanned at the National Archives): 19 JPGs, 13.1 MB, hashes re-checked. These are the 100 dpi web copies; the 600 dpi originals are only at the National Archives. Non-commercial research use only. They are unreferenced images, so they give no indicators.
- ❌ **data.gov.lk: not downloaded.** The site's TLS certificate fails verification (curl: "unable to get local issuer certificate"; the built-in browser: ERR_CERT_DATE_INVALID). I did not disable certificate checks. Retry when the site owner fixes the certificate, or the lead can list the dataset links they want after receiving permission. The catalogue entry for the portal stays "rights unclear".
- Other National Archives holdings (catalogue at archives.gov.lk) were not found as downloadable scans; no further map scans were retrieved.
- Storage: the external drive was not mounted, so these were first written by mistake to `pipeline/raw/` (an unset data directory), then moved unchanged into `pipeline/data/raw/` (gitignored) and re-hashed OK. Copy them to the drive when it is connected.
