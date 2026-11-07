# F02: Catalogue schemas, validator and seed entries

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 0 | Foundation | 2 | 2026-11-07 | active |

## When to use
After F01. Defines the machine-checkable shape of everything in `catalog/` and `overrides/`.

## Read first
- `AGENTS.md`
- `docs/architecture/data-model.md` (all of it; §2–§6 define the fields)
- `docs/research/ecosystem-landscape.md` §6 (seed sources)

## Inputs (fill in)
```
(none required)
```

## Task
1. Implement schemas (Pydantic models exported to JSON Schema) for: source, dataset, indicator, geography scheme, geography codes CSV, geography relations CSV and overrides CSV. Use **exactly** the field names and enums in `data-model.md`. If you think a field is wrong or missing, implement the documented version and propose the change in the PR (and update `data-model.md` if the lead agrees).
2. Implement `slf catalog validate`: schema checks, referential integrity (dataset → source; indicator numerator/denominator → indicator; override → dataset), unique IDs, enum values, URL syntax, and the **rights rule** (datasets with `rights.status: unclear` are flagged as not publishable), and the **spatial rule**: every dataset has a `spatial` block as in `docs/architecture/spatial-first-analytics.md` §3 (`support` required; `national` allowed). Also the footprint and time-footprint fields on observations (`docs/architecture/footprint-model.md` §3), and a schema for `catalog/spaces/*.yaml` (vector spaces, `docs/architecture/vector-space-model.md` §8).
3. Tests with valid and invalid fixtures for each schema.
4. Seed `catalog/sources/` and `catalog/datasets/` with the sources in ecosystem-landscape §6, `status: proposed`. Set rights only where the landscape doc marks them known (COD-AB CC BY-IGO, OSM ODbL). Everything else is `unclear`.
5. Seed `catalog/geographies/schemes.yaml` with the schemes in data-model §3.1.
6. Seed `catalog/indicators/` with **no more than 5** example indicators from Census 2024 (population total, male, female, households total, cooking-with-firewood share with components) to exercise the schema.
7. Wire validation into CI.

## Constraints
- Don't invent URLs, contacts or licences for seed entries. Use `null` and `notes`.
- YAML must stay human-readable: comments are allowed, and keys keep the documented order.

## Verify (show real output)
- `slf catalog validate` output on the seeded catalogue (expect "not publishable: N datasets (rights unclear)").
- Test results, including invalid fixtures failing for the right reasons.

## Deliverables
Schemas, validator, tests, seed catalogue and CI step.

## Done when
A bad catalogue edit fails CI with a clear message, and the lead can read any YAML file and understand it.

Report using the format in `AGENTS.md`.
