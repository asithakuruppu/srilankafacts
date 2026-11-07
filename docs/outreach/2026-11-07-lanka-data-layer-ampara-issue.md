# Draft: GitHub issue for Lanka Data Layer (Ampara district parent)

Status: **draft** · Channel: GitHub issue at https://github.com/prabhavalabs/lanka-data-layer/issues (no issue template found) · Prompt: R04

---

**Title:** Ampara District (LK52) is parented to Uva Province (LK8) instead of Eastern Province (LK5)

Hi, thanks for building and publishing Lanka Data Layer. While validating admin boundaries for a separate open project (Sri Lanka Facts, https://github.com/asithakuruppu/srilankafacts), we found a hierarchy error that seems worth reporting.

**What happens**

`GET https://lanka-data-layer.prabhavalabs.com/v1/admin/LK52` returns:

```json
"pcode": "LK52", "level": 2, "name": "Ampara District", "parent_pcode": "LK8"
```

with `parent_chain` LK → LK8 (Uva Province). The 19 DS divisions under LK52 therefore roll up to Uva, and Eastern Province rolls up without Ampara.

**Expected**

`parent_pcode: "LK5"` (Eastern Province). Two independent sources agree:
- **COD-AB v03 (HDX, `lka_admin_boundaries.gdb`, layer `lka_admin2`):** the row for `adm2_pcode = LK52` has `adm1_pcode = LK5`. This is the attribute parent, not a spatial inference.
- **NSDI boundaries service** (`gisapps.nsdi.gov.lk/server/rest/services/Srilanka/Boundaries/MapServer`) places district code 52 in province 5.

**Reproduced**

- On the live API (re-checked 2026-11-07).
- On a fresh local build of the repository (earlier audit, 2026-11-07).

**Possible cause (a guess)**

If parents for levels 1–2 are assigned spatially (for example, from a centroid or the largest overlap), Ampara's shape could produce Uva. Taking the parent from COD-AB's `adm1_pcode` attribute would avoid it. In our own pipeline we keep attribute parents and run a regression test that LK52 → LK5.

Happy to share more detail if useful.

---

## Facts stated and their sources

| Claim | Source |
|---|---|
| Live API returns `parent_pcode: LK8` for LK52 | ✅ `curl https://lanka-data-layer.prabhavalabs.com/v1/admin/LK52`, 2026-11-07 |
| 19 DS divisions under LK52 | ✅ 19 child edges of LK52 in `catalog/geographies/relations/admin_cod-ab-v03.csv`; also the audit §10 |
| COD-AB `lka_admin2`: LK52 → `adm1_pcode` LK5 | ✅ our build; test `test_committed_hierarchy_ampara_in_eastern_province` |
| NSDI puts district 52 in province 5 | `docs/lanka-data-layer-audit.md` §11 🟡 |
| No existing issue about Ampara | ✅ GitHub API, 12 issues listed, none mention Ampara/LK52/parent (2026-11-07) |

## Notes for the lead
- Post from your own GitHub account. The issue is factual and neutral; edit freely.
