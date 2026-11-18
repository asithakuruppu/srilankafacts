"""Point resolver on a synthetic spine: hierarchy by id, sea points resolve to nothing."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from slf.resolver import Resolver


def _spine(tmp_path: Path) -> Path:
    rows = [
        ("LK", 0, None),
        ("LK1", 1, "LK"),
        ("LK11", 2, "LK1"),
        ("LK1101", 3, "LK11"),
        ("LK1101001", 4, "LK1101"),
        ("LK1101002", 4, "LK1101"),
    ]
    pd.DataFrame(
        [{"geography_id": g, "level": lv, "parent_id": p, "name_en": f"N {g}"} for g, lv, p in rows]
    ).to_parquet(tmp_path / "geographies.parquet")
    gpd.GeoDataFrame(
        {"geography_id": ["LK1101001", "LK1101002"], "level": [4, 4]},
        geometry=[box(80.0, 7.0, 80.1, 7.1), box(80.1, 7.0, 80.2, 7.1)],
        crs=4326,
    ).to_parquet(tmp_path / "geography_versions.geoparquet")
    relations = tmp_path / "relations"
    relations.mkdir()
    (relations / "electoral_ec-2024.csv").write_text(
        "geography_id,related_id,relation\nLK-ED-01,LK11,composed_of\n"
    )
    return tmp_path


def test_point_resolves_up_the_hierarchy(tmp_path: Path) -> None:
    spine = _spine(tmp_path)
    result = Resolver(spine, spine / "relations").resolve(80.15, 7.05)
    assert result.places == {
        "gn": "LK1101002",
        "ds": "LK1101",
        "district": "LK11",
        "province": "LK1",
        "country": "LK",
        "ed": "LK-ED-01",
    }


def test_shared_border_goes_to_the_first_gn_and_sea_to_nothing(tmp_path: Path) -> None:
    spine = _spine(tmp_path)
    resolver = Resolver(spine)
    assert resolver.resolve(80.1, 7.05).places["gn"] == "LK1101001"
    sea = resolver.resolve(79.0, 7.05)
    assert sea.places == {} and sea.note
