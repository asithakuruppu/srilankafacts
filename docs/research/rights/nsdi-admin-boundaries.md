# Rights memo: nsdi-admin-boundaries (NSDI geoportal)

Reviewed 2026-11-07 · Not legal advice.

## Evidence
| # | Source | Where | Finding |
|---|---|---|---|
| E1 | MapServer service and layer metadata | `https://gisapps.nsdi.gov.lk/server/rest/services/Srilanka/Boundaries/MapServer?f=json` | `copyrightText` empty |
| E2 | Geoportal home | `https://geoportal.nsdi.gov.lk/` | JavaScript app; no readable terms |
| E3 | GN layer fields | layer 1 metadata | Contains GN officers' names and phone numbers (personal data) |

## Uses
| Use | Classification | Note |
|---|---|---|
| Internal comparison (counts, codes, shapes) | Not addressed | What we do now; nothing is published |
| Display, redistribution, derived tables, commercial | Not addressed | Not allowed until terms are known (AGENTS rule 4) |
| Personal data (officer names, phones) | **Never collect or publish** | AGENTS rule 11; excluded from every query |

Catalogue: `unclear`. Attribution if ever allowed: "Boundaries: National Spatial Data Infrastructure (NSDI), Sri Lanka" (to confirm).

Questions (in the Survey Department / NSDI letter draft): reuse terms; who maintains the service; vintage of the DS layer.
