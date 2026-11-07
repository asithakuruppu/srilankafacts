# D04: Build a versioned release

| Stage | Workstream | Version | Last revised | Status |
|---|---|---|---|---|
| 1+ | Data engineering | 1 | 2026-11-07 | active |

## When to use
To turn validated datasets into an immutable public release. The first use is the Census Atlas 2024 beta.

## Read first
- `AGENTS.md`
- `docs/architecture/architecture-overview.md` §3 (publish stage), §5.3 (API layout), §8 (release integrity)
- `docs/architecture/data-model.md` §5, §7 (observation columns, provenance chain)
- Previous release manifest, if any

## Inputs (fill in)
```
VERSION:   vYYYY.MM.N
DATASETS:  dataset ids to include (must be publishable per the validator)
NOTES:     human-written release notes
```

## Task
1. Implement or extend `slf release`: collect validated datasets; refuse any dataset that isn't publishable (rights) or that failed validation.
2. Write the release layout: `observations/*.parquet` + CSV; `geographies.parquet`, `geography_versions.geoparquet`, GeoPackage; static API JSON (layout from W05 if it exists; otherwise architecture §5.3); `datapackage.json` (Frictionless: resources, schemas, licences, sources); `CHECKSUMS.sha256`; `CHANGELOG.md`; `qa/summary.md`.
3. **Changelog by diff** against the previous release: new, changed and removed values (counts per dataset), corrections applied (with override IDs), new and removed geographies.
4. **Deterministic builds:** two runs from the same inputs produce identical checksums. Fix timestamps, ordering and compression settings.
5. A citation string per release and per dataset. A draft Zenodo metadata file for major releases (not submitted).
6. Dry run locally. Uploading and updating the `latest` pointer happen only through the CI release workflow with manual approval (O01).

## Constraints
- Releases are immutable. A fix is a new release plus a corrections-log entry.
- Never include a dataset whose rights are `unclear` unless the decision log records an explicit decision.

## Verify (show real output)
Two-run checksum comparison; release tree with sizes; `datapackage.json` validated with the Frictionless validator; changelog excerpt.

## Deliverables
Release command, release artefacts (local), changelog, QA summary, tests.

## Done when
A release can be rebuilt bit-for-bit, and every file is described in the manifest with licence and source.

Report using the format in `AGENTS.md`.
