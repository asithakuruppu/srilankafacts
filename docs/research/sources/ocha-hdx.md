# Source dossier: OCHA HDX, COD-AB Sri Lanka

Prompt R01 · checked 2026-11-07 · catalogue: `catalog/sources/ocha-hdx.yaml`, `catalog/datasets/cod-ab-lka.yaml`

| Finding | Status | Evidence |
|---|---|---|
| Dataset "Sri Lanka - Subnational Administrative Boundaries", version 03; 9 / 25 / 339 / 14,043 units at levels 1–4 | ✅ | HDX API `package_show?id=cod-ab-lka` (snapshot `raw/ocha-hdx/cod-ab-lka/20261107T163632Z/hdx_package_show.json`); counts reproduced in our build |
| Licence field: `cc-by-igo`, "Creative Commons Attribution for Intergovernmental Organisations (CC BY-IGO)", licence URL CC BY 3.0 IGO legal code | ✅ | same snapshot, fields `license_id`, `license_title`, `license_url` |
| Source named: Survey Department of Sri Lanka; boundaries created 2022-08-02, valid for humanitarian use from 2022-08-16, reviewed 2025-10-30 | ✅ | same snapshot, `dataset_source`, `notes` |
| Formats: geodatabase, shapefile, GeoJSON, XLSX; we use the geodatabase (richest: name fields en/si/ta, versions, admin lines and points) | ✅ | resource list; G01 inspection |
| CRS EPSG:4326 on all layers | ✅ | G01 QA report §2 |
| Caveats: 530 GN features with conflicting Sinhala names; 65 GN with unknown English names | ✅ | `caveats` field |
| HDX web pages (licence FAQ, terms) returned HTTP 202, an automated-client challenge, so their text could not be read | ❌ | 2026-11-07 |
| Contact: through HDX/OCHA; no individual contact recorded | — | — |

Community use: Lanka Data Layer builds DS and GN units from this dataset (its README) ✅.

Open question: did the Survey Department authorise the CC BY-IGO licence that OCHA applies? Asked in the Survey Department letter draft.
