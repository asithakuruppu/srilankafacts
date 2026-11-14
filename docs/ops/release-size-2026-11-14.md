# Release size, raw and compressed (2026-11-14)

Prepared by an agent for the lead, as evidence for the hosting decision. Verification tags: ✅
measured here · ❓ assumption. Release measured: local preview `v2026.11.10-preview.2` (both
Census 2024 datasets, all four D-032 steps).

## Answer

**2.1 GB on disk, 319 MB gzipped** ✅. The large raw parts are repetitive JSON and CSV that
compress to 5–7% of their size. **Changing the API format to save space is not worth it**: it
would cut the compressed place files by only about 15%. Store or serve the files compressed
instead.

This withdraws the agent's earlier suggestion (step reports for D-032) to slim the per-value
provenance text in place files.

## Where the bytes are ✅

| Part | Raw | gzip -6 | Notes |
|---|---|---|---|
| Whole release (`tar` of the folder) | 2.1 GB | **319 MB** | 15,922 files |
| `api/v1/places/` (14,418 files) | 734 MB | 52 MB | JSON; 7% |
| `observations/` | 1.1 GB | 62 MB | topic-tables CSV 1.03 GB → ~48 MB (4.7% on its first 100 MB); Parquet copies 13 MB, already compressed |
| `geography_versions.geoparquet` | 126 MB | ~126 MB ❓ | Parquet, already compressed; full-resolution geometry history |
| `stats/` (spatial context) | 91 MB | 83 MB | Parquet; the website reads only `stats/spatial_summary.json` |
| `boundaries/` | | 3 MB | GeoJSON |

## Place files in detail ✅

In a random sample of 400 place files (20.5 MB, 31,941 values), the number itself is **2.3%** of
the bytes. The rest is provenance and labels repeated on every value: source locator 18.7%,
snapshot sha256 13.4%, claim id 11.8%, indicator id 7.8%, dataset id 6.3%, information
footprint 6.1%, verification 5.6%, and so on.

A simulated normalised layout (one small `sources` table per file; each value a short row pointing
to it) was measured on the same sample:

| | Now | Normalised |
|---|---|---|
| Raw | 20.5 MB | 7.6 MB (37%) |
| gzip | 1.5 MB (7%) | 1.3 MB (6%) |

Scaled to all place files: raw 734 → ~273 MB, but gzipped only ~54 → ~46 MB. The API change would
touch the release builder, the website, the Q01 audit and every API user, for an 8 MB saving once
files are compressed.

## What this means for hosting ❓

- If the host compresses responses (for example Vercel does for static files) or the release is
  uploaded pre-compressed with `Content-Encoding` set (an option for R2), transfer and most storage
  costs follow the 319 MB figure, not 2.1 GB.
- `geography_versions.geoparquet` and `stats/` are download artefacts the website does not read.
  They could be left out of the site deploy and offered from object storage only.
- These are options for O01 (deployment); nothing is changed here.

## How measured

Run from the release folder: `tar cf - . | gzip -6 | wc -c`, and the same per part. The sample
and the normalised layout were simulated with a short Python script over 400 random place files
(seed 1); no release file was modified.
