# Method: local authorities and MOH areas as GN compositions (G05, schemes `la` and `health`)

Status: **code built and tested; no publishable source held** · 2026-11-17 · Decision: D-046
(Proposed) · Module `pipeline/slf/datasets/composed_geography.py` · command
`uv run slf composition build` · QA: [la-moh-composition-2026-11-17.md](../qa/la-moh-composition-2026-11-17.md)

Verification tags: ✅ checked by running it · 🟡 from a source, not independently checked · ❓ assumption.

## What it does

Local authorities (municipal councils, urban councils, pradeshiya sabhas) and Medical Officer
of Health (MOH) areas do not nest in the administrative hierarchy. Each is a set of GN
divisions. The command takes two plain tables:

- a **unit list**: `unit_code,name[,kind]` (`kind` = `MC`, `UC` or `PS` for local authorities);
- a **membership list**: `gn_code,unit_code[,weight]` (weight 1 by default; a GN split across
  units has one row per unit and weights that sum to 1).

It then follows the pattern of `slf electoral build`:

1. **Ids** per D-004: `LK-LA-<code>`, `LK-MOH-<code>`, using the source's own unit code.
2. **Join** each GN code to the spine through a crosswalk file in
   `catalog/geographies/codes/` (or directly when the source uses p-codes). Names are never
   used to join (rule 5).
3. **Composition**: `composed_of` relations, unit → GN, with the weight and method
   (`official_list` for an authority's list; `attribute` for a GN attribute in another source;
   `overlay_*` for a spatial overlay).
4. **Checks** (G05 step 4): unit counts; each spine GN's weight sum across the scheme (expect
   1.0); GNs in no unit; units with no GN; GNs split across units; rows whose GN code did not
   match, whose unit is not in the list, or that repeat — each written to its own CSV, never
   dropped silently (rule 6); IoU of each unit's shape against the union of its GNs in
   EPSG:5235 when shapes are given; comparison with published unit totals when given.
5. **Local authorities only — an official, independent check:** DCS's Census 2024 GN table
   gives every GN's population by local-authority *type* (municipal council, urban council,
   pradeshiya sabha). For each unit the command reports the share of its members' population
   that DCS places under the unit's own type. A council named "… MC" whose GNs DCS puts under
   pradeshiya sabhas is flagged.
6. **Denominators**: population, five-year age groups to 19, households and occupied housing
   units as Σ(weight × GN value), with 15+ and 20+ bracketing 18+ (census bands are
   five-year). Rates are recomputed from these counts, never averaged.

## Rights gate (rule 4)

Codes and relations are written to `catalog/geographies/codes/<scheme>-<vintage>.csv` and
`relations/<scheme>_<vintage>.csv` **only** if the membership dataset's recorded rights allow
publication: `open` or `permitted_with_conditions`, or `unclear` with an Accepted publication
decision (as D-030, D-039). Otherwise the run is internal: every file carries `_internal` in
its name and stays in `pipeline/data/build/<scheme>/`, which is not committed.

## What is held (2026-11-17)

| Need | Held? | Notes |
|---|---|---|
| Official list of local authorities with codes | ❌ | Ministry of Public Administration / Provincial Councils; no snapshot with rights recorded |
| Official GN list per local authority | ❌ | — |
| Local-authority boundaries with rights | ❌ | — |
| Official list of MOH areas with codes | ❌ | `catalog/datasets/moh-boundaries.yaml` is a placeholder; source `ministry-of-health` rights `unclear`, no homepage recorded |
| MOH boundaries with rights | ❌ | — |
| nuuuwan `gig-data` (`lg_id`, `moh_id` per GN; unit lists; shapes) | ✅ held | **No licence, no stated origin** (catalogue `nuuuwan-gig-data`, rights unclear). Used for an internal run only, exactly as for polling divisions (D-040) |
| DCS GN population by local-authority type | ✅ | Census 2024 topic tables (D-032); used as the independent check above |

So **no local-authority or MOH composition is published**, and the atlas draws neither
scheme: its scale switcher shows LA and MOH as unavailable with the reason.

## What the internal run shows

Run on `gig-data` (QA report for the counts): coverage is incomplete (423 spine GNs have no
local authority; 986 have no MOH area, 571 of them because gig-data leaves `moh_id` empty) and
several units' own shapes overlap their own GN lists poorly. Against DCS's local-authority
types, most local authorities hold all their population in their own type, but 16 fall below
90 % and 3 below 50 %. Even if it were licensed, gig-data would need these resolved before it
could serve as a denominator source.

## Next step

Obtain an official GN list per local authority (Ministry of Public Administration, the
Provincial Councils, or DCS, whose census already tags each GN's local-authority type) and per
MOH area (Ministry of Health / Epidemiology Unit), record its rights in `catalog/`, and run:

```bash
uv run slf composition build --scheme la --vintage <vintage> --units <units.csv> --membership <members.csv> --source-dataset <dataset-id> --code-system <crosswalk or pcode> --method official_list
```
