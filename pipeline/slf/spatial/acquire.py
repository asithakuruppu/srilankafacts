"""Snapshot the files listed in ``catalog/acquisition/spatial-manifest.csv``.

Each row names one original file: its source, dataset, URL and the licence it is published under.
Files are stored through :mod:`slf.snapshot`, so every one gets a ``.meta.json`` with the URL,
retrieval time and sha256, identical bytes are never stored twice, and nothing under ``raw/`` is
ever overwritten. A failed download is reported, never skipped silently.
"""

from __future__ import annotations

import csv
import json
import ssl
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from slf.snapshot import USER_AGENT, SnapshotRef, snapshot_bytes
from slf.storage import Storage


@dataclass(frozen=True)
class ManifestRow:
    source: str
    dataset: str
    filename: str
    url: str
    licence: str


@dataclass(frozen=True)
class AcquireResult:
    row: ManifestRow
    ref: SnapshotRef | None
    error: str | None = None


def read_manifest(path: Path) -> list[ManifestRow]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [ManifestRow(**row) for row in csv.DictReader(handle)]


def existing(storage: Storage, row: ManifestRow) -> SnapshotRef | None:
    """The newest snapshot already held for this manifest row, if any."""
    found: SnapshotRef | None = None
    for key in storage.list(f"raw/{row.source}/{row.dataset}"):
        if key.endswith(f"/{row.filename}.meta.json"):
            meta = json.loads(storage.get(key))
            if meta.get("url") == row.url:
                found = SnapshotRef(**{**meta, "reused": True})
    return found


def _fetch(url: str, timeout: float) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    context = ssl.create_default_context()
    try:
        import certifi

        context = ssl.create_default_context(cafile=certifi.where())
    except ImportError:  # pragma: no cover - certifi ships with the pipeline's dependencies
        pass
    with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
        return response.read()


def acquire(
    storage: Storage,
    rows: list[ManifestRow],
    *,
    refresh: bool = False,
    pause: float = 0.5,
    timeout: float = 600.0,
) -> list[AcquireResult]:
    """Snapshot every row; rows already held are reused unless ``refresh`` is set."""
    results: list[AcquireResult] = []
    for row in rows:
        held = None if refresh else existing(storage, row)
        if held is not None:
            results.append(AcquireResult(row, held))
            continue
        try:
            content = _fetch(row.url, timeout)
        except Exception as exc:
            results.append(AcquireResult(row, None, f"{type(exc).__name__}: {exc}"))
            continue
        ref = snapshot_bytes(
            storage,
            source=row.source,
            dataset=row.dataset,
            filename=row.filename,
            content=content,
            url=row.url,
            licence_note=row.licence,
        )
        results.append(AcquireResult(row, ref))
        time.sleep(pause)
    return results


def inventory_markdown(results: list[AcquireResult]) -> str:
    """A table of what is held: one line per file, with size, hash and retrieval time."""
    lines = [
        "| Source | Dataset | File | Size (bytes) | Retrieved (UTC) | sha256 (first 16) "
        "| Licence |",
        "|---|---|---|---:|---|---|---|",
    ]
    for r in results:
        if r.ref is None:
            lines.append(
                f"| {r.row.source} | {r.row.dataset} | {r.row.filename} | ❌ | | | {r.error} |"
            )
            continue
        lines.append(
            f"| {r.row.source} | {r.row.dataset} | {r.row.filename} | {r.ref.size_bytes} "
            f"| {r.ref.retrieved_at} | `{r.ref.sha256[:16]}` | {r.row.licence} |"
        )
    return "\n".join(lines) + "\n"
