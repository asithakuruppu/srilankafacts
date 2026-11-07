"""Immutable snapshots of source files.

A snapshot is the exact bytes retrieved from a source, stored under
``raw/{source}/{dataset}/{retrieved_at}/{filename}`` with a ``.meta.json`` beside it recording
the URL, retrieval time, sha256 and any licence note. Identical content already snapshotted for
the same dataset is not stored twice.
"""

from __future__ import annotations

import hashlib
import json
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from slf.storage import Storage

USER_AGENT = "srilankafacts-pipeline/0.0.1"


@dataclass(frozen=True)
class SnapshotRef:
    key: str
    sha256: str
    url: str | None
    retrieved_at: str
    size_bytes: int
    licence_note: str | None = None
    reused: bool = False


def _timestamp(now: datetime | None = None) -> str:
    return (now or datetime.now(UTC)).strftime("%Y%m%dT%H%M%SZ")


def snapshot_bytes(
    storage: Storage,
    *,
    source: str,
    dataset: str,
    filename: str,
    content: bytes,
    url: str | None = None,
    licence_note: str | None = None,
    now: datetime | None = None,
) -> SnapshotRef:
    """Store ``content`` as a new snapshot, or return the existing one with the same hash."""
    digest = hashlib.sha256(content).hexdigest()
    prefix = f"raw/{source}/{dataset}"
    for key in storage.list(prefix):
        if key.endswith(".meta.json"):
            meta = json.loads(storage.get(key))
            if meta.get("sha256") == digest:
                return SnapshotRef(**{**meta, "reused": True})

    retrieved_at = _timestamp(now)
    key = f"{prefix}/{retrieved_at}/{filename}"
    ref = SnapshotRef(
        key=key,
        sha256=digest,
        url=url,
        retrieved_at=retrieved_at,
        size_bytes=len(content),
        licence_note=licence_note,
    )
    storage.put(key, content)
    meta = {k: v for k, v in asdict(ref).items() if k != "reused"}
    storage.put(f"{key}.meta.json", json.dumps(meta, indent=2).encode())
    return ref


def snapshot_url(
    storage: Storage,
    *,
    source: str,
    dataset: str,
    url: str,
    filename: str | None = None,
    licence_note: str | None = None,
    timeout: float = 60.0,
) -> SnapshotRef:
    """Fetch ``url`` and snapshot the response body."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content = response.read()
    name = filename or url.rstrip("/").rsplit("/", 1)[-1] or "download"
    return snapshot_bytes(
        storage,
        source=source,
        dataset=dataset,
        filename=name,
        content=content,
        url=url,
        licence_note=licence_note,
    )
