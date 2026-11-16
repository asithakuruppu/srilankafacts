"""Electoral code lists let a release accept ED/PD ids that are not in the spine (D-040)."""

from __future__ import annotations

from pathlib import Path

from slf.release import _non_spine_code_files


def test_reads_electoral_code_lists_only(tmp_path: Path):
    codes = tmp_path / "geographies" / "codes"
    codes.mkdir(parents=True)
    (codes / "electoral-ec-2024.csv").write_text(
        "geography_id,vintage\nLK-ED-01,ec-2024\nLK-ED-01,ec-2024\nLK-PD-01A,ec-2024\n"
    )
    (codes / "dcs-census-2024.csv").write_text("geography_id,vintage\nLK11,2024\n")
    assert _non_spine_code_files(tmp_path) == {"electoral-ec-2024.csv": {"LK-ED-01", "LK-PD-01A"}}


def test_no_code_lists(tmp_path: Path):
    assert _non_spine_code_files(tmp_path) == {}
