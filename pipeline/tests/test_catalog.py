"""Catalogue validator: links between files and publishing rules (F02)."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from slf.catalog import validate_catalog
from slf.cli import app

REAL_CATALOG = Path(__file__).resolve().parents[2] / "catalog"


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def mini(tmp_path: Path) -> Path:
    root = tmp_path / "catalog"
    for d in ("sources", "datasets", "indicators", "geographies", "spaces"):
        (root / d).mkdir(parents=True)
    write(
        root,
        "sources/dcs.yaml",
        """
id: dcs
name: DCS
publisher_type: government
rights: {status: unclear, last_reviewed: 2026-11-07}
""",
    )
    write(
        root,
        "geographies/schemes.yaml",
        """
schemes:
  - id: admin
    name: Admin
    stage: "0"
    levels: [{level: 4, id: gn, name: GN}]
""",
    )
    write(
        root,
        "indicators/total.yaml",
        """
id: total
name: Total
measure_type: count
unit: persons
aggregation: sum
definition: total
""",
    )
    write(
        root,
        "datasets/census.yaml",
        """
id: census
source: dcs
title: Census
spatial: {support: area, scheme: admin, level: gn, crs_source: not_applicable}
indicators: [total]
""",
    )
    return root


def test_mini_catalogue_is_valid_but_not_publishable(mini: Path) -> None:
    report = validate_catalog(mini, mini.parent / "overrides")
    assert report.ok, report.errors
    assert report.not_publishable == ["census: rights unclear"]


def test_dataset_pointing_to_missing_source_fails(mini: Path) -> None:
    text = (mini / "datasets/census.yaml").read_text().replace("source: dcs", "source: nobody")
    write(mini, "datasets/census.yaml", text)
    report = validate_catalog(mini)
    assert any("source 'nobody' not found" in e for e in report.errors)


def test_missing_indicator_and_component_fail(mini: Path) -> None:
    write(
        mini,
        "indicators/share.yaml",
        """
id: share
name: Share
measure_type: share
unit: percent
numerator: missing_count
denominator: total
aggregation: recompute_from_components
definition: share
""",
    )
    text = (mini / "datasets/census.yaml").read_text().replace("[total]", "[total, ghost]")
    write(mini, "datasets/census.yaml", text)
    errors = validate_catalog(mini).errors
    assert any("indicator 'ghost' not found" in e for e in errors)
    assert any("numerator 'missing_count' not found" in e for e in errors)


def test_unknown_level_and_scheme_fail(mini: Path) -> None:
    text = (mini / "datasets/census.yaml").read_text().replace("level: gn", "level: village")
    write(mini, "datasets/census.yaml", text)
    assert any("spatial.level 'village'" in e for e in validate_catalog(mini).errors)
    text = text.replace("scheme: admin", "scheme: postal")
    write(mini, "datasets/census.yaml", text)
    assert any("scheme 'postal' not in schemes.yaml" in e for e in validate_catalog(mini).errors)


def test_file_name_must_match_id(mini: Path) -> None:
    (mini / "sources/dcs.yaml").rename(mini / "sources/census-dept.yaml")
    assert any("must match the file name" in e for e in validate_catalog(mini).errors)


def test_override_csv_checked_and_linked(mini: Path) -> None:
    ov = mini.parent / "overrides"
    header = (
        "override_id,dataset_id,target,field,old_value,new_value,reason,evidence,reviewer,date\n"
    )
    write(
        ov,
        "census.csv",
        header
        + "ov-1,census,c1,value,10,12,typo,Report p.4,lead,2026-11-07\n"
        + "ov-2,elsewhere,c2,value,1,2,typo,Report p.5,lead,2026-11-07\n"
        + "ov-3,census,c3,value,1,2,typo,,lead,2026-11-07\n",
    )
    errors = validate_catalog(mini, ov).errors
    assert any("dataset 'elsewhere' not found" in e for e in errors)
    assert any("census.csv row 4: evidence" in e for e in errors)


def test_relation_csv_rows_validated(mini: Path) -> None:
    header = (
        "geography_id,related_id,relation,vintage,weight,method,source,valid_from,valid_to,notes\n"
    )
    write(
        mini,
        "geographies/relations/admin.csv",
        header
        + "LK1,LK11,parent,v,,attribute,cod-ab-lka,,,\n"
        + "LK-LA-0001,LK1103005,composed_of,v,,official_list,x,,,\n",
    )
    errors = validate_catalog(mini).errors
    assert any("admin.csv row 3" in e and "weight" in e for e in errors)


def test_broken_yaml_reported(mini: Path) -> None:
    write(mini, "sources/bad.yaml", "id: bad\nname: Title: with colon\n")
    assert any("invalid YAML" in e for e in validate_catalog(mini).errors)


def test_real_catalogue_passes_and_lists_unpublishable() -> None:
    result = CliRunner().invoke(app, ["catalog", "validate", "--root", str(REAL_CATALOG)])
    assert result.exit_code == 0, result.output
    assert "catalogue OK" in result.output
    assert "rights unclear" in result.output


def test_cli_fails_on_bad_catalogue(mini: Path) -> None:
    write(mini, "sources/bad.yaml", "id: bad\n")
    result = CliRunner().invoke(app, ["catalog", "validate", "--root", str(mini)])
    assert result.exit_code == 1
