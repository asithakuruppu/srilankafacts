#!/bin/sh
# Dry run of the R2 upload: checks the bucket, sends nothing. Run from pipeline/.
uv run --env-file .env slf upload --release-dir ./data/build/releases/v2026.11.14 --dry-run
