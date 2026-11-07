"""Storage for raw snapshots and releases.

Two backends share one interface:

- ``LocalStorage``: a directory on disk (default ``./data``).
- ``S3Storage``: S3-compatible object storage such as Cloudflare R2, configured by environment
  variables. Requires the optional ``s3`` extra (boto3).

Raw snapshots and releases are immutable (AGENTS.md rule 3): writing to an existing key raises
``ImmutableKeyError``. Nothing in this module deletes data.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol


class ImmutableKeyError(Exception):
    """Raised when a write would overwrite an existing raw or release object."""


class Storage(Protocol):
    def put(self, key: str, data: bytes) -> None: ...
    def get(self, key: str) -> bytes: ...
    def exists(self, key: str) -> bool: ...
    def list(self, prefix: str) -> list[str]: ...


def _check_key(key: str) -> str:
    key = key.strip("/")
    if not key or ".." in key.split("/"):
        raise ValueError(f"invalid storage key: {key!r}")
    return key


class LocalStorage:
    """Append-only storage in a local directory."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def _path(self, key: str) -> Path:
        return self.root / _check_key(key)

    def put(self, key: str, data: bytes) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            # "xb" fails if the file exists, so an existing object can never be overwritten.
            with path.open("xb") as f:
                f.write(data)
        except FileExistsError as exc:
            raise ImmutableKeyError(f"refusing to overwrite existing key: {key}") from exc

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()

    def list(self, prefix: str) -> list[str]:
        base = self.root / _check_key(prefix) if prefix.strip("/") else self.root
        if not base.exists():
            return []
        return sorted(p.relative_to(self.root).as_posix() for p in base.rglob("*") if p.is_file())


class S3Storage:
    """Append-only storage in an S3-compatible bucket (for example Cloudflare R2).

    Not yet exercised against a real bucket: the lead creates buckets and credentials first
    (see docs/ops/accounts-setup.md). Credentials come only from the environment.
    """

    def __init__(self, bucket: str, endpoint_url: str | None = None) -> None:
        try:
            import boto3  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise RuntimeError("S3 storage needs the optional extra: uv sync --extra s3") from exc
        self.bucket = bucket
        self._s3 = boto3.client("s3", endpoint_url=endpoint_url)

    def put(self, key: str, data: bytes) -> None:
        key = _check_key(key)
        if self.exists(key):
            raise ImmutableKeyError(f"refusing to overwrite existing key: {key}")
        self._s3.put_object(Bucket=self.bucket, Key=key, Body=data)

    def get(self, key: str) -> bytes:
        return self._s3.get_object(Bucket=self.bucket, Key=_check_key(key))["Body"].read()

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError  # type: ignore[import-not-found]

        try:
            self._s3.head_object(Bucket=self.bucket, Key=_check_key(key))
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
                return False
            raise
        return True

    def list(self, prefix: str) -> list[str]:
        keys: list[str] = []
        paginator = self._s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket, Prefix=prefix.strip("/")):
            keys.extend(obj["Key"] for obj in page.get("Contents", []))
        return sorted(keys)


def from_env() -> Storage:
    """Build storage from environment variables.

    - ``SLF_STORAGE``: ``local`` (default) or ``s3``.
    - ``SLF_DATA_DIR``: local root, default ``./data``.
    - ``SLF_S3_BUCKET``, ``SLF_S3_ENDPOINT``: bucket and endpoint for ``s3``; credentials via the
      standard ``AWS_ACCESS_KEY_ID`` / ``AWS_SECRET_ACCESS_KEY`` variables.
    """
    kind = os.environ.get("SLF_STORAGE", "local")
    if kind == "local":
        return LocalStorage(os.environ.get("SLF_DATA_DIR", "./data"))
    if kind == "s3":
        bucket = os.environ.get("SLF_S3_BUCKET")
        if not bucket:
            raise RuntimeError("SLF_S3_BUCKET must be set when SLF_STORAGE=s3")
        return S3Storage(bucket, endpoint_url=os.environ.get("SLF_S3_ENDPOINT"))
    raise RuntimeError(f"unknown SLF_STORAGE: {kind!r} (expected 'local' or 's3')")
