"""Freshness states from schedules and snapshot folders."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from slf import freshness


def test_snapshot_folders_are_found_and_parsed(tmp_path: Path) -> None:
    for stamp in ("20261101T000000Z", "20261110T120000Z"):
        (tmp_path / "wfp" / "wfp-food-prices" / stamp).mkdir(parents=True)
    (tmp_path / "wfp" / "wfp-food-prices" / "notes").mkdir()
    stamps = freshness._snapshots([tmp_path], "wfp", "wfp-food-prices")
    assert stamps == ["20261101T000000Z", "20261110T120000Z"]
    assert freshness._parse(stamps[-1]) == datetime(2026, 11, 10, 12, tzinfo=UTC)


def test_calendar_over_the_real_catalogue_has_a_state_for_every_dataset(tmp_path: Path) -> None:
    catalog = Path(__file__).resolve().parents[2] / "catalog"
    # The weekly dataset, last snapshot 17 days ago: overdue.
    (tmp_path / "raw" / "epidemiology-unit" / "dengue-by-moh" / "20261101T000000Z").mkdir(
        parents=True
    )
    calendar = freshness.build(
        catalog, [tmp_path / "raw"], tmp_path / "out", now=datetime(2026, 11, 18, tzinfo=UTC)
    )
    states = {row["dataset_id"]: row["state"] for row in calendar["datasets"]}
    assert all(
        state in {"not_held", "held_unscheduled", "overdue", "current"} for state in states.values()
    )
    assert states["dengue-by-moh"] == "overdue"
    assert (tmp_path / "out" / "calendar.json").exists()
