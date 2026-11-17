# QA: local authority and MOH compositions (G05, schemes `la` and `health`) — internal run

Built 2026-11-17 with `uv run slf composition build --scheme la --gig-internal --with-geometry`
and `--scheme health` (spine `cod-ab-v03`, Census 2024 builds) · method:
[denominators-la-moh.md](../methods/denominators-la-moh.md)

**Status: internal only.** The only membership source held is nuuuwan `gig-data`, which has no
licence and no stated origin. Nothing was written to `catalog/`; unit-level outputs stay in
`pipeline/data/build/la/` and `pipeline/data/build/health/` with `_internal` in their names.
This report gives aggregate counts only.

## Counts

| Item | Local authorities | MOH areas |
|---|---|---|
| Units in gig-data's unit list | 341 | 333 |
| Units with at least one GN matched to the spine | 335 | 323 |
| Units with no GN | 6 | 10 |
| Spine GNs (COD-AB v03) | 14,043 | 14,043 |
| Spine GNs covered by a unit | 13,620 | 13,057 |
| gig-data GN rows whose id is not in `codes/nuuuwan.csv` | 401 | 393 |
| gig-data GN rows with no unit (empty id) | 0 | 571 |
| Rows naming a unit not in the unit list / repeated | 0 / 0 | 0 / 0 |
| GNs split across units | 0 | 0 |

## Weight sums per spine GN (expect 1.0 everywhere)

- Local authorities: 13,620 GNs at 1.0; **423 at 0** (in no unit) ❌
- MOH areas: 13,057 at 1.0; **986 at 0** ❌

## Census 2024 population

| | Local authorities | MOH areas |
|---|---|---|
| Summed over units | 21,161,823 | 20,056,171 |
| All spine GNs with a census value | 21,710,113 | 21,710,113 |
| In GNs that are in no unit | 548,290 | 1,653,942 |
| Unit population, median (min–max) | 51,477 (2,561–509,207) | 52,121 (307–247,203) |

## IoU: gig-data unit shape vs union of its own GNs (EPSG:5235)

| | Local authorities | MOH areas |
|---|---|---|
| Median | 0.94 | 0.94 |
| Units below 0.9 / below 0.8 | 97 / 37 | 88 / 38 |
| Shapes not available upstream (HTTP 404) | 0 | 4 |

## Against DCS's local-authority type per GN (official, independent; LA only)

Units by type in gig-data's names: 29 MC, 36 UC, 276 PS. Share of each unit's population that
DCS places under the unit's own type: median 1.0, 5th percentile 0.91; **16 units below 0.9,
3 below 0.5**.

## Against gig-data's own unit populations (comparison only)

Median relative difference +7.0 % (LA) and +7.8 % (MOH) between the census sum over each unit's
GNs and gig-data's own population column. gig-data does not say which census or year its
populations come from ❓, so the differences are not explained here.

## Conclusion

The code path works end to end ✅ (also on a fixture in `tests/test_composed_geography.py`). No
composition is publishable, and gig-data is not reliable enough to be one: GNs without units,
poor shape agreement for about a quarter of units, and type mismatches against DCS. An official
GN list per unit is needed (next step in the method note).
