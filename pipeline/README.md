# pipeline/

The `slf` Python package: the data pipeline for Sri Lanka Facts.

Every dataset is a module in `slf/datasets/` implementing five stages (see `docs/architecture/architecture-overview.md` §3):

1. **snapshot**: fetch the source and store it immutably under `raw/` with URL, retrieval time and sha256.
2. **extract**: turn the raw file into a tidy table in the source's own terms.
3. **harmonise**: map to Sri Lanka Facts observations (where / when / what, see `docs/architecture/footprint-model.md`).
4. **validate**: check the observations and produce a QA report. Nothing is dropped silently.
5. **publish**: write the dataset's part of a release.

Storage is local (`./data/`) by default, or S3-compatible (Cloudflare R2) when `SLF_STORAGE=s3` is set (see `slf/storage.py`). Raw snapshots and releases are append-only: existing keys are never overwritten.

Commands are listed in the root `AGENTS.md`.
