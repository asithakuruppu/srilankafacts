"""Upload a built release folder to S3-compatible storage (Cloudflare R2).

Rules: only a release marked publishable is uploaded; an existing key is never overwritten;
credentials come from the environment only. The raw bucket is never touched here.
"""

from __future__ import annotations

import json
import mimetypes
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class NotPublishableError(Exception):
    pass


@dataclass
class UploadResult:
    uploaded: list[str] = field(default_factory=list)
    skipped_existing: list[str] = field(default_factory=list)
    bytes_uploaded: int = 0


def _transfer_config() -> Any:
    """Few connections per big file: many files already run at once, and R2 drops floods."""
    try:
        from boto3.s3.transfer import TransferConfig  # type: ignore[import-not-found]
    except ImportError:  # tests with a fake client
        return None
    return TransferConfig(max_concurrency=2)


def _exists(client: Any, bucket: str, key: str) -> bool:
    from botocore.exceptions import ClientError  # type: ignore[import-not-found]

    try:
        client.head_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
            return False
        raise
    return True


def _list_keys(client: Any, bucket: str, prefix: str) -> set[str]:
    """All keys already under ``prefix``: a few paged listings instead of one request per file."""
    keys: set[str] = set()
    for page in client.get_paginator("list_objects_v2").paginate(
        Bucket=bucket, Prefix=prefix + "/"
    ):
        keys.update(obj["Key"] for obj in page.get("Contents", []))
    return keys


def check_publishable(release_dir: Path) -> str:
    """Return the release version, or raise if the release must not be public."""
    pkg = json.loads((release_dir / "datapackage.json").read_text("utf-8"))
    if pkg.get("publishable") is not True or pkg.get("access") == "private_preview":
        raise NotPublishableError(
            f"{release_dir.name} is not publishable (access={pkg.get('access')!r}, "
            f"publishable={pkg.get('publishable')!r}); refusing to upload."
        )
    latest = json.loads((release_dir / "api/v1/releases/latest.json").read_text("utf-8"))
    return str(latest["release"])


def upload_release(
    release_dir: Path,
    client: Any,
    bucket: str,
    prefix: str | None = None,
    dry_run: bool = False,
    exists=None,
    workers: int = 1,
    progress=None,
) -> UploadResult:
    """Upload every file under ``release_dir`` to ``<prefix>/<relative path>``.

    Existing keys are skipped and reported, never overwritten, so an interrupted upload can be
    resumed. ``exists`` is injectable for tests. ``workers`` > 1 sends files in parallel;
    ``progress(done, total)`` is called after each file when given.
    """
    version = check_publishable(release_dir)
    prefix = (prefix or f"releases/{version}").strip("/")
    if exists is None:
        present = _list_keys(client, bucket, prefix)
        check = present.__contains__
    else:
        check = exists
    result = UploadResult()
    todo: list[tuple[Path, str]] = []
    for path in sorted(p for p in release_dir.rglob("*") if p.is_file()):
        key = f"{prefix}/{path.relative_to(release_dir).as_posix()}"
        if check(key):
            result.skipped_existing.append(key)
        else:
            todo.append((path, key))

    def send(item: tuple[Path, str]) -> tuple[str, int]:
        path, key = item
        if not dry_run:
            ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            client.upload_file(
                str(path), bucket, key, ExtraArgs={"ContentType": ctype}, Config=_transfer_config()
            )
        return key, path.stat().st_size

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for done, (key, size) in enumerate(pool.map(send, todo), start=1):
            result.uploaded.append(key)
            result.bytes_uploaded += size
            if progress:
                progress(done, len(todo))
    return result
