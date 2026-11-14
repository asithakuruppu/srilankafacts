"""Check that a bucket's ``releases/<version>/`` folder matches a local release folder.

Read-only. Checks: every local file is present with the same size; no extra keys; for objects
uploaded in one part the ETag equals the local MD5; for multipart objects (ETag has ``-``, not an
MD5) size only, plus a sampled download whose SHA-256 is compared with ``CHECKSUMS.sha256``.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from slf.upload import check_publishable


@dataclass
class VerifyResult:
    prefix: str = ""
    local_files: int = 0
    remote_files: int = 0
    missing: list[str] = field(default_factory=list)
    extra: list[str] = field(default_factory=list)
    size_mismatch: list[str] = field(default_factory=list)
    etag_mismatch: list[str] = field(default_factory=list)
    etag_checked: int = 0
    multipart_size_only: int = 0
    hash_checked: int = 0
    hash_mismatch: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (
            self.missing
            or self.extra
            or self.size_mismatch
            or self.etag_mismatch
            or self.hash_mismatch
        )


def _md5(path: Path) -> str:
    h = hashlib.md5(usedforsecurity=False)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_checksums(release_dir: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in (release_dir / "CHECKSUMS.sha256").read_text("utf-8").splitlines():
        if line.strip():
            digest, _, rel = line.partition("  ")
            out[rel.strip().lstrip("*")] = digest.strip()
    return out


def _remote(client: Any, bucket: str, prefix: str) -> dict[str, dict[str, Any]]:
    objs: dict[str, dict[str, Any]] = {}
    for page in client.get_paginator("list_objects_v2").paginate(
        Bucket=bucket, Prefix=prefix + "/"
    ):
        for o in page.get("Contents", []):
            objs[o["Key"]] = o
    return objs


def _sha256_remote(client: Any, bucket: str, key: str) -> str:
    body = client.get_object(Bucket=bucket, Key=key)["Body"]
    h = hashlib.sha256()
    for chunk in iter(lambda: body.read(1 << 20), b""):
        h.update(chunk)
    return h.hexdigest()


def verify_upload(
    release_dir: Path,
    client: Any,
    bucket: str,
    prefix: str | None = None,
    sample: int = 20,
    seed: int = 0,
) -> VerifyResult:
    version = check_publishable(release_dir)
    prefix = (prefix or f"releases/{version}").strip("/")
    res = VerifyResult(prefix=prefix)
    remote = _remote(client, bucket, prefix)
    local = {
        p.relative_to(release_dir).as_posix(): p for p in release_dir.rglob("*") if p.is_file()
    }
    res.local_files, res.remote_files = len(local), len(remote)
    present: list[str] = []
    for rel, path in sorted(local.items()):
        obj = remote.get(f"{prefix}/{rel}")
        if obj is None:
            res.missing.append(rel)
            continue
        if obj["Size"] != path.stat().st_size:
            res.size_mismatch.append(rel)
            continue
        present.append(rel)
        etag = str(obj.get("ETag", "")).strip('"')
        if "-" in etag or len(etag) != 32:
            res.multipart_size_only += 1
        else:
            res.etag_checked += 1
            if etag.lower() != _md5(path):
                res.etag_mismatch.append(rel)
    res.extra = sorted(k[len(prefix) + 1 :] for k in remote if k[len(prefix) + 1 :] not in local)
    sums = read_checksums(release_dir)
    candidates = [r for r in present if r in sums]
    for rel in random.Random(seed).sample(candidates, min(sample, len(candidates))):
        res.hash_checked += 1
        if _sha256_remote(client, bucket, f"{prefix}/{rel}") != sums[rel]:
            res.hash_mismatch.append(rel)
    return res
