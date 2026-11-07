# G02: Cross-source code crosswalk

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 0 | Geography | 1 | 2026-11-07 | active |

## When to use
After G01, to link every external code system to our IDs, and before any statistics are joined. Re-run when a source changes.

## Read first
- `AGENTS.md`
- `docs/architecture/data-model.md` §3.2 (IDs, GEO_CODE, match methods)
- `docs/lanka-data-layer-audit.md` §11 (NSDI comparison: 326 shared DS codes, 61 name differences, DS 2309 conflict, Water Area pseudo-units, empty NSDI GN codes)
- G01 QA report

## Inputs (fill in)
```
SYSTEMS: dcs_census2024 (unit codes from the DCS GN tables), nsdi, ldl, nuuuwan
DCS_TABLE_SNAPSHOT: snapshot id of a DCS Census 2024 GN-level table (from D01 or a fresh snapshot)
```

## Task
1. **Collect unit lists** per system with codes, names and parent names:
   - DCS Census 2024 GN tables (authoritative for census joins).
   - NSDI ArcGIS REST attributes only (page through at ≤1,000 records per query, with pauses).
   - Lanka Data Layer `admin` data (npm package `@lanka-data-layer/admin` or repository files).
   - nuuuwan `lk_census_2024` IDs (cross-check only).
2. **Test code equivalence on a sample before assuming it.** For example, check whether DCS codes map to p-codes by a fixed transformation for 50 random units. Report the result, and use code matching only where equivalence holds.
3. **Match in order:** `exact_code` (where equivalence is proven) → `name_and_parent` with documented normalisation (case, diacritics, spacing, known variants such as Pujapitiya/Poojapitiya, suffixes such as "Korale", "Pattu") → `spatial` (for NSDI, using geometry overlap where available) → a **manual review queue** (CSV with candidates and evidence). Set `confidence` by method.
4. **Special cases to document:** unit counts differ by source. Census 2024 tables as parsed by nuuuwan have 340 DSD and 14,008 GND rows ✅, COD-AB has 339/14,043, NSDI has 332/14,051, and 331/14,022 are commonly cited. Also NSDI "Water Area" (code 9999) pseudo-units; Kalmunai North Sub (unmatched in LDL); DS 2309 (Walapane vs Nildandahinna); DS units present in COD-AB but not NSDI (13 listed in the audit); GN groups sharing names within a parent.
5. **Explain DS 339 vs 331 vs 332** unit by unit as far as the evidence allows. For each extra or missing unit, say whether it appears in DCS 2024 tables, NSDI, COD-AB, and any official gazette or list you can find (cite it). Where unresolved, say so.
6. Write `catalog/geographies/codes/{system}.csv` (`geography_id, system, code, name_in_system, match_method, confidence, valid_from, note`), `catalog/geographies/manual-review.csv`, and `docs/research/geography/crosswalk-report.md` (match rates per system and level, unmatched lists, special cases).

## Constraints
- Never auto-accept fuzzy name matches below a threshold you state. They go to manual review.
- Manual matches need evidence (a source URL or document) in `note`.
- Nothing is dropped. Every unit in every system ends up matched, in the review queue, or listed as no counterpart.

## Verify (show real output)
- Match-rate table per system and level.
- Count of review-queue items.
- A sample of 20 random matches with both names shown, for the lead to eyeball.

## Deliverables
Crosswalk CSVs, review queue, report, tests asserting that DCS census GN codes map to unique p-codes or are listed as unmatched.

## Done when
For any DCS census unit, the lead can find its `geography_id` or the reason it has none.

Report using the format in `AGENTS.md`.
