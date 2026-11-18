"""Events on a synthetic spine: fires counted by place and year, storm passes by district."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from slf import events


def _spine(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    rows = [
        ("LK", 0, None),
        ("LK1", 1, "LK"),
        ("LK11", 2, "LK1"),
        ("LK1101", 3, "LK11"),
        ("LK1101001", 4, "LK1101"),
        ("LK1101002", 4, "LK1101"),
    ]
    pd.DataFrame(
        [{"geography_id": g, "level": lv, "parent_id": p, "name_en": g} for g, lv, p in rows]
    ).to_parquet(tmp_path / "geographies.parquet")
    gpd.GeoDataFrame(
        {"geography_id": ["LK11", "LK1101001", "LK1101002"], "level": [2, 4, 4]},
        geometry=[box(80.0, 7.0, 80.2, 7.1), box(80.0, 7.0, 80.1, 7.1), box(80.1, 7.0, 80.2, 7.1)],
        crs=4326,
    ).to_parquet(tmp_path / "geography_versions.geoparquet")
    return tmp_path


def _snapshot(raw: Path, source: str, dataset: str, name: str, data: bytes) -> None:
    folder = raw / source / dataset / "20261118T000000Z"
    folder.mkdir(parents=True)
    (folder / name).write_bytes(data)
    (folder / f"{name}.meta.json").write_text(json.dumps({"sha256": "0" * 64, "url": None}))


def test_fire_detections_are_counted_by_place_and_year(tmp_path: Path) -> None:
    spine = _spine(tmp_path / "spine")
    raw = tmp_path / "raw"
    csv = (
        "latitude,longitude,acq_date,confidence,type\n"
        "7.05,80.05,2020-03-01,n,0\n"  # counted, GN 001
        "7.05,80.15,2020-03-02,h,0\n"  # counted, GN 002
        "7.05,80.15,2020-03-03,l,0\n"  # low confidence: not counted
        "7.05,80.15,2021-01-01,n,2\n"  # static source: not counted
        "6.00,79.00,2020-01-01,n,0\n"  # at sea: not counted
    )
    archive = tmp_path / "f.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("fire_archive_SV-C2_1.csv", csv)
    _snapshot(
        raw, "nasa-firms", "nasa-firms-active-fire-lk", "DL_FIRE_SV-C2_1.zip", archive.read_bytes()
    )
    versions, parent, level = events._hierarchy(spine)
    rows = events.fires(raw, versions, parent, level)
    value = {(r["geography_id"], r["period"]): r["value"] for r in rows}
    assert value[("LK1101", "2020")] == 2
    assert value[("LK", "2020")] == 2
    assert value[("LK1101", "2021")] == 0


def test_modis_fire_detections_use_numeric_confidence_and_start_in_2001(tmp_path: Path) -> None:
    spine = _spine(tmp_path / "spine")
    raw = tmp_path / "raw"
    csv = (
        "latitude,longitude,acq_date,confidence,type\n"
        "7.05,80.05,2005-03-01,30,0\n"  # counted: confidence 30 is nominal
        "7.05,80.15,2005-03-02,95,0\n"  # counted
        "7.05,80.15,2005-03-03,29,0\n"  # low: not counted
        "7.05,80.15,2005-03-04,80,3\n"  # not a vegetation fire: not counted
        "7.05,80.15,2000-12-05,80,0\n"  # before 2001: outside the yearly series
    )
    archive = tmp_path / "m.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("fire_archive_M-C61_1.csv", csv)
    _snapshot(
        raw, "nasa-firms", "nasa-firms-active-fire-lk", "DL_FIRE_M-C61_1.zip", archive.read_bytes()
    )
    versions, parent, level = events._hierarchy(spine)
    rows = events.fires(raw, versions, parent, level, "modis")
    value = {(r["geography_id"], r["period"]): r["value"] for r in rows}
    assert value[("LK1101", "2005")] == 2
    assert ("LK1101", "2000") not in value and ("LK1101", "2001") in value
    assert {r["indicator_id"] for r in rows} == {"fire_detections_modis"}


def test_storm_passes_use_a_50_km_zone(tmp_path: Path) -> None:
    spine = _spine(tmp_path / "spine")
    raw = tmp_path / "raw"
    csv = (
        "SID,NUMBER,BASIN,SUBBASIN,ISO_TIME,NATURE,LAT,LON,WMO_WIND,WMO_PRES\n"
        " , , , , , ,degrees_north,degrees_east,kts,mb\n"
        "NEAR,1,NI,BB,2000-11-01 00:00:00,TS,7.5,80.1,60, \n"
        "NEAR,1,NI,BB,2000-11-01 03:00:00,TS,7.3,80.1,70, \n"
        "FAR,2,NI,BB,2001-11-01 00:00:00,TS,10.0,85.0,90, \n"
        "FAR,2,NI,BB,2001-11-01 03:00:00,TS,10.5,85.5,90, \n"
    )
    _snapshot(
        raw, "noaa-ncei", "ibtracs-storm-tracks", "ibtracs_all_list_v04r01_lka.csv", csv.encode()
    )
    versions, _, _ = events._hierarchy(spine)
    passes, _ = events.storms(raw, versions)
    assert [p[0] for p in passes["LK11"]] == ["NEAR"]
    assert passes["LK11"][0][2] == 70
