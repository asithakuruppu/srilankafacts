# QA: LA and MOH profiles, internal re-run (2026-11-21)

Re-ran `uv run slf composition build --scheme la|health --gig-internal --with-geometry` (drive
mounted) ✅. Numbers are identical to [la-moh-composition-2026-11-17.md](la-moh-composition-2026-11-17.md):

| | Local authorities | MOH areas |
|---|---|---|
| Units with GN / listed | 335 / 341 | 323 / 333 |
| Spine GNs in no unit | 423 | 986 (571 gig-data rows have empty `moh_id`) |
| Population in GNs in no unit | 548,290 | 1,653,942 |
| Units with IoU < 0.9 | 97 | 88 |
| LA units with DCS own-type share < 0.9 | 16 | n/a |

Profiles: 335 LA and 323 MOH units, 100 and 88 with at least one flag. **Internal only**: files
are `*_profiles_internal.json` in `pipeline/data/build/{la,health}/`, not committed, not copied to
the site. Unmatched/unassigned rows stay in their CSVs (rule 6).

## Later the same day: preview publication (D-057)

After the lead's instruction, the gig-data run passes the rights gate through the new catalogue
entry `nuuuwan-gig-data-lg-moh` and writes publishable files. Counts above are unchanged. The static
site build with the bundle shows 335 LA rows with the notice and the coverage line (423 GNs in no
area). Not verified: the full `slf atlas export` with `--units-dir` on a release (the file copy was
done with the same function), browser screenshots.
