# Source dossier: NSDI geoportal (boundaries service)

Prompt R01 · checked 2026-11-07 · catalogue: `catalog/sources/nsdi.yaml`, `catalog/datasets/nsdi-admin-boundaries.yaml`

| Finding | Status | Evidence |
|---|---|---|
| ArcGIS MapServer `gisapps.nsdi.gov.lk/server/rest/services/Srilanka/Boundaries/MapServer`: layers Areas, Grama Niladhari Division, Divisional Secretariat, District, Province, Forest, Country; max 1,000 records per query | ✅ | service JSON, 2026-11-07 |
| `copyrightText` is empty for the service and the layers | ✅ | service and layer JSON |
| Geoportal home `geoportal.nsdi.gov.lk` is a JavaScript application; no terms text readable without a browser | ❌ | HTTP 200, 189 characters of text |
| GN layer: 14,051 features; `gnd_code` empty for all; `admin_code` holds the 7-digit district+DS+GN code; `data_source` "Satellite Images" for all | ✅ | attribute snapshot `raw/nsdi/nsdi-admin-boundaries/20261107T165406Z/nsdi_gn_ds_attributes.json` |
| **GN layer includes GN officers' names and phone numbers**: not requested, never to be collected (AGENTS rule 11) | ✅ | layer field list |
| DS layer: 332 features incl. two "Water Area" pseudo-units; 3 duplicated codes | ✅ | G02 report §4 |
| 4 DS polygons carry the code and name of a similarly named unit elsewhere (e.g. Ambalangoda ↔ Ambalantota) | ✅ | G03 report §4 |
| 229 GN units carry boundary-dispute flags | ✅ | G03 report §5 |
| Access class: `api` | ✅ | — |

Community use: Lanka Data Layer audit compared NSDI attributes (docs/lanka-data-layer-audit.md §11).

Open questions: reuse terms; vintage of the DS layer (looks older than COD-AB); whether NSDI is maintained by the Survey Department or ICTA. All are in the Survey Department / NSDI letter draft.
