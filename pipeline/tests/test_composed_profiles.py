"""Profile content for composed units: rates from counts, flags, internal tag (G05)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from slf.datasets import composed_profiles as cp

COLS = [
    "geography_id", "name", "gn_members", "gn_with_census", "population_total",
    "population_age_0_4", "population_age_5_9", "population_age_10_14", "population_age_15_19",
    "households_total", "occupied_housing_units", "population_age_15_plus",
    "population_age_20_plus",
]  # fmt: skip


def _den(tmp: Path, tag: str) -> None:
    rows = [
        ["LK-LA-1", "A MC", 2, 2, 1000, 100, 100, 100, 100, 250, 240, 700, 600],
        ["LK-LA-2", "B PS", 3, 1, 0, None, None, None, None, 0, 0, None, None],
    ]
    pd.DataFrame(rows, columns=COLS).to_csv(tmp / f"la_denominators{tag}.csv", index=False)
    pd.DataFrame({"unit": ["LK-LA-1", "LK-LA-2"], "iou": [0.95, 0.5]}).to_csv(
        tmp / f"la_iou{tag}.csv", index=False
    )
    pd.DataFrame({"geography_id": ["LK-LA-1", "LK-LA-2"], "share_in_own_kind": [1.0, 0.4]}).to_csv(
        tmp / f"la_census_type_check{tag}.csv", index=False
    )


def test_internal_profile_rates_and_flags(tmp_path: Path) -> None:
    _den(tmp_path, "_internal")
    out, summary = cp.build_profiles(tmp_path, "la", publishable=False, source_note="x")
    assert out.name == "la_profiles_internal.json"
    doc = json.loads(out.read_text())
    assert doc["publishable"] is False
    a, b = doc["units"]
    assert a["rates"]["share_aged_0_14"] == 0.3
    assert a["rates"]["population_per_household"] == 4.0
    assert a["flags"] == []
    # A unit with no population keeps its row, with null rates and flags (rule 6).
    assert b["rates"]["share_aged_0_14"] is None
    assert set(b["flags"]) == {
        "some_gn_without_census",
        "shape_disagrees_with_gn_union",
        "dcs_local_authority_type_mismatch",
    }
    assert summary["units"] == 2 and summary["units_with_flags"] == 1


def test_publishable_reads_untagged_files(tmp_path: Path) -> None:
    _den(tmp_path, "")
    out, _ = cp.build_profiles(tmp_path, "la", publishable=True, source_note="x")
    assert out.name == "la_profiles.json"
    assert json.loads(out.read_text())["notice"] is None
    assert json.loads(out.read_text())["publishable"] is True


def test_atlas_copies_only_publishable_profiles(tmp_path: Path) -> None:
    from slf.atlas import _copy_unit_profiles

    (tmp_path / "la").mkdir()
    (tmp_path / "health").mkdir()
    (tmp_path / "la" / "la_profiles.json").write_text(json.dumps({"publishable": True}))
    (tmp_path / "health" / "health_profiles.json").write_text(json.dumps({"publishable": False}))
    (tmp_path / "health" / "health_profiles_internal.json").write_text("{}")
    target = tmp_path / "out"
    target.mkdir()
    assert _copy_unit_profiles(tmp_path, target) == {"available": True, "schemes": ["la"]}
    assert (target / "units-la.json").exists() and not (target / "units-health.json").exists()
    assert _copy_unit_profiles(None, target)["available"] is False
