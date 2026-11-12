"""Corrections log: the committed file validates and bad entries are refused."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from slf import corrections

REPO = Path(__file__).resolve().parents[2]
LOG = REPO / "docs" / "corrections" / "log.yaml"


def _entry(**over: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": "C-001",
        "found": "2026-11-12",
        "fixed": "2026-11-12",
        "scope": "private_preview",
        "affected_releases": ["v2026.11.5-preview.1"],
        "fixed_in": "v2026.11.6-preview.1",
        "indicators": "all",
        "values_changed": 2,
        "what_was_wrong": "Two units had each other's values.",
        "what_changed": "The matches were swapped back.",
        "cause": "geography_match",
        "evidence": ["docs/x.md"],
    }
    return {**base, **over}


def _write(tmp_path: Path, *entries: dict[str, object]) -> Path:
    path = tmp_path / "log.yaml"
    path.write_text(yaml.safe_dump({"entries": list(entries)}), encoding="utf-8")
    return path


def test_committed_log_validates():
    log = corrections.load(LOG)
    assert log.entries
    entries = corrections.payload(log, "v1")["entries"]
    assert isinstance(entries, list) and entries[0]["id"] == log.entries[0].id


def test_duplicate_ids_are_refused(tmp_path: Path):
    with pytest.raises(ValueError, match="duplicate"):
        corrections.load(_write(tmp_path, _entry(), _entry()))


def test_fixed_before_found_is_refused(tmp_path: Path):
    with pytest.raises(ValueError, match="before found"):
        corrections.load(_write(tmp_path, _entry(fixed="2026-11-01")))


@pytest.mark.parametrize(
    "over",
    [{"cause": "typo"}, {"affected_releases": ["2026.11"]}, {"id": "C1"}, {"evidence": []}],
)
def test_invalid_fields_are_refused(tmp_path: Path, over: dict[str, object]):
    with pytest.raises(ValueError):
        corrections.load(_write(tmp_path, _entry(**over)))


def test_unapproved_entries_are_listed_for_the_public_release_check(tmp_path: Path):
    log = corrections.load(_write(tmp_path, _entry(), _entry(id="C-002", approved_by="lead")))
    assert corrections.unapproved(log) == ["C-001"]
