# Method: denominators for electoral districts and polling divisions (G05, scheme `electoral`)

Module `pipeline/slf/datasets/electoral_geography.py` · command `uv run slf electoral build` · QA: [electoral-geography-ec-2024.md](../qa/electoral-geography-ec-2024.md)

## Units and identifiers (D-004)

| Level | Id | Count | Source of the list |
|---|---|---|---|
| Electoral district (`electoral_district`) | `LK-ED-NN`, NN = the Commission's ED number (`LK-ED-01` Colombo … `LK-ED-22` Kegalle) | 22 | Register of electors by polling division 2016–2025 (Election Commission) |
| Polling division (`polling_division`) | `LK-PD-NNX`, ED number + the Commission's PD letter (`LK-PD-01A` Colombo North) | 160 | Same register; the same 160 have 2024 result sheets |

The vintage is `ec-2024`. Codes are in `catalog/geographies/codes/electoral-ec-2024.csv`: the Commission's code (`1`, `1-B`) and nuuuwan's (`EC-01`, `EC-01B`). PD → ED `parent` edges are in `relations/electoral_ec-2024.csv`. Both files are generated; do not edit them by hand.

## Electoral districts: exact, from whole administrative districts

Each ED is one administrative district, except:
- Jaffna ED = Jaffna + Kilinochchi districts;
- Vanni ED = Mannar + Vavuniya + Mullaitivu districts.

The grouping comes from a secondary source (Wikipedia 🟡) and matches the register's PD names (Kilinochchi PD under Jaffna; Mannar, Vavuniya and Mullaitivu PDs under Vanni) ✅. It also agrees with nuuuwan's per-GN ED for all 13,620 matched GNs ✅.

The relation is `LK-ED-NN composed_of <district p-code>`, weight 1, `method: manual`. GN membership follows from the admin hierarchy (spine `parent` edges), so every spine GN is in exactly one ED.

**Denominators:** an ED's population, households and age groups are the **sum of its districts' Census 2024 totals**. This needs no apportionment and is `census_count`, not `modelled_estimate`. Summing GN values instead would miss 71,687 people in DCS GNs not matched to the spine (52,798 of them in Kalmunai, Digamadulla); that sum is kept only as a QA check.

## Polling divisions: no GN composition yet

data-model §3.4 prefers an official GN list, then a building or population overlay, then an area overlay. None of these is possible today:
- no official list of GNs per PD is published;
- no PD boundary file with known rights exists, so there is nothing to overlay ([rights memo](../research/rights/election-results.md)).

nuuuwan's `gig-data` assigns a PD to 14,021 GNs, but it has no licence and states no origin. It is used only inside the local build, to exercise the checks. Those checks show it is not usable as a denominator source:
- 423 spine GNs have no PD;
- for 21 PDs, nuuuwan's own shape and its own GN list overlap with IoU below 0.9;
- electors per 100 adults reach 655 in one PD and 40 in another.

So **PD denominators are not published**, and PD-level per-capita figures cannot be computed yet. PD results (counts, shares, turnout) do not need a census denominator and are unaffected.

Next step: the Commission's GN list per PD (asked in the [drafted letter](../outreach/2026-11-15-election-commission-results-and-gn-lists.md)). When it arrives, PD relations go in `relations/electoral_ec-2024.csv` with `method: official_list`. GNs split across PDs (if any) need weights, and the same checks are re-run.

## Rules

- Counts re-aggregate by summation. Rates (for example electors per 100 adults) are recomputed from numerator and denominator, never averaged.
- Registered electors are 18+. Census 2024 publishes five-year age bands, so the adult population can only be bracketed (aged 15+ and aged 20+), never stated as 18+.
- Comparing a register (where people are registered) with a census (where people were counted) is a comparison of two different things. Report it, don't interpret it (AGENTS rule 12).
