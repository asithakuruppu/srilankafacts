"""Resolution manifest: metres only where the catalogue states them."""

from __future__ import annotations

from pathlib import Path

from slf.atlas_resolution import build, native_metres

CATALOG = Path(__file__).resolve().parents[2] / "catalog"


def test_metres_from_unit_or_plain_text() -> None:
    assert native_metres("grid-30m", None) == 30.0
    assert native_metres("grid-1km", "1 km") == 1000.0
    assert native_metres("grid-1m", "about 1.2 m") == 1.2
    assert native_metres("grid-100m", None) == 100.0
    assert native_metres(None, "about 100 m (0.00089 degrees)") == 100.0
    assert native_metres(None, "375 m (VIIRS), 1 km (MODIS)") == 375.0
    assert native_metres(None, "h3:8") == 461.0


def test_unstated_resolution_stays_null() -> None:
    assert native_metres(None, None) is None
    assert native_metres(None, "not read") is None
    assert native_metres(None, "0.05 degree") is None
    assert native_metres(None, "1:250,000 map scale") is None


def test_build_writes_sorted_rows(tmp_path: Path) -> None:
    entry = build(CATALOG, tmp_path)
    import json

    rows = json.loads((tmp_path / "resolution.json").read_text())["datasets"]
    assert entry["datasets"] == len(rows) > 0
    metres = [r["native_resolution_m"] for r in rows if r["native_resolution_m"] is not None]
    assert metres == sorted(metres)
    firsts_null = [r["native_resolution_m"] is None for r in rows]
    assert firsts_null == sorted(firsts_null)  # all stated values come before the unstated
    assert all(
        r["tier"] != "finer_than_gn"
        or r["native_resolution_m"]
        or r["support"] in {"point", "line"}
        for r in rows
    )
