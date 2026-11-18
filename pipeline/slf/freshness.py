"""Freshness monitor and release calendar (D05), local and detection-only.

For every catalogued dataset: its schedule, the newest raw snapshot held (from the
`raw/<source>/<dataset>/<timestamp>/` layout), when the next one is expected, and whether
it is overdue. With `probe=True` it also asks each landing page for `ETag` and
`Last-Modified` with a HEAD request (one request per dataset, a pause between them, a generic
user agent) and compares them with the previous run, so a changed page is flagged. It never
downloads data, opens issues or contacts anyone; snapshots go through the dataset pipeline.
"""

from __future__ import annotations

import json
import time
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

EXPECTED_EVERY = {"daily": 1, "weekly": 7, "monthly": 31}
USER_AGENT = "freshness-check/0.1"


def _snapshots(raw_roots: list[Path], source: str, dataset: str) -> list[str]:
    found: set[str] = set()
    for root in raw_roots:
        folder = root / source / dataset
        if folder.exists():
            found.update(p.name for p in folder.iterdir() if p.is_dir() and p.name[:8].isdigit())
    return sorted(found)


def _parse(stamp: str) -> datetime:
    return datetime.strptime(stamp[:15], "%Y%m%dT%H%M%S").replace(tzinfo=UTC)


def _head(url: str, timeout: float = 15.0) -> dict[str, Any]:
    request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {
                "status": response.status,
                "etag": response.headers.get("ETag"),
                "last_modified": response.headers.get("Last-Modified"),
            }
    except Exception as error:  # a failed probe is reported, never fatal
        return {"status": None, "error": str(error)[:200]}


def build(
    catalog_dir: Path,
    raw_roots: list[Path],
    out_dir: Path,
    now: datetime | None = None,
    probe: bool = False,
    pause_s: float = 2.0,
) -> dict[str, Any]:
    from slf.catalog import CatalogReport, load_catalog

    now = now or datetime.now(UTC)
    catalog = load_catalog(catalog_dir, catalog_dir.parent / "overrides", CatalogReport())
    previous_path = out_dir / "signals.json"
    previous = json.loads(previous_path.read_text()) if previous_path.exists() else {}
    signals: dict[str, Any] = {}
    rows: list[dict[str, Any]] = []
    for dataset in sorted(catalog.datasets.values(), key=lambda d: d.id):
        stamps = _snapshots(raw_roots, dataset.source, dataset.id)
        last = _parse(stamps[-1]) if stamps else None
        every = EXPECTED_EVERY.get(dataset.schedule)
        expected = last + timedelta(days=every) if last and every else None
        if not stamps:
            state = "not_held"
        elif expected is None:
            state = "held_unscheduled"
        elif expected < now:
            state = "overdue"
        else:
            state = "current"
        row: dict[str, Any] = {
            "dataset_id": dataset.id,
            "title": dataset.title,
            "source": dataset.source,
            "status": dataset.status,
            "schedule": dataset.schedule,
            "reference_period": dataset.reference_period,
            "landing_page": str(dataset.landing_page) if dataset.landing_page else None,
            "snapshots": len(stamps),
            "last_snapshot": last.isoformat() if last else None,
            "expected_next": expected.date().isoformat() if expected else None,
            "state": state,
            "page_changed": None,
        }
        if probe and dataset.landing_page:
            signal = _head(str(dataset.landing_page))
            signals[dataset.id] = signal
            before = previous.get(dataset.id)
            if before and signal.get("status") and before.get("status"):
                row["page_changed"] = (signal.get("etag"), signal.get("last_modified")) != (
                    before.get("etag"),
                    before.get("last_modified"),
                )
            time.sleep(pause_s)
        rows.append(row)
    out_dir.mkdir(parents=True, exist_ok=True)
    if probe:
        previous_path.write_text(json.dumps(signals, indent=2) + "\n")
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["state"]] = counts.get(row["state"], 0) + 1
    calendar = {
        "generated_at": now.isoformat(timespec="seconds"),
        "probed": probe,
        "counts": counts,
        "datasets": rows,
        "note": (
            "Detection only. 'held_unscheduled' means the source has no fixed schedule in the "
            "catalogue; 'expected_next' is shown only for daily, weekly or monthly datasets."
        ),
    }
    (out_dir / "calendar.json").write_text(json.dumps(calendar, indent=2) + "\n")
    return calendar
