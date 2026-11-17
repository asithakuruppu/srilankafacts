"""Atlas bundle: shared borders are written once and ranked by the level they divide."""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely
from shapely.geometry import box

from slf.atlas import _borders, _ranked_mesh, build_adjacency, build_geometry

# A 4 x 2 grid of 1 km squares in EPSG:5235 metres: 8 GNs, 4 DS (pairs stacked vertically),
# 2 districts (left and right halves), 1 province, 1 country.
ORIGIN_X, ORIGIN_Y = 400_000.0, 500_000.0


def _square(col: int, row: int) -> shapely.Polygon:
    x, y = ORIGIN_X + col * 1000, ORIGIN_Y + row * 1000
    return box(x, y, x + 1000, y + 1000)


def _spine(tmp_path: Path) -> Path:
    rows = [("LK", 0, None), ("LK1", 1, "LK"), ("LK11", 2, "LK1"), ("LK12", 2, "LK1")]
    geoms: dict[str, shapely.Polygon] = {}
    for col in range(4):
        district = "LK11" if col < 2 else "LK12"
        ds = f"{district}0{col}"
        rows.append((ds, 3, district))
        for row in range(2):
            gn = f"{ds}00{row}"
            rows.append((gn, 4, ds))
            geoms[gn] = _square(col, row)
    geographies = pd.DataFrame(
        [
            {
                "geography_id": gid,
                "level": level,
                "parent_id": parent,
                "name_en": f"Unit {gid}",
            }
            for gid, level, parent in rows
        ]
    )
    geographies.to_parquet(tmp_path / "geographies.parquet")
    versions = gpd.GeoDataFrame(
        {
            "geography_id": [gid for gid, _, _ in rows],
            "level": [level for _, level, _ in rows],
            "area_km2": [1.0] * len(rows),
            "label_lon": [80.0] * len(rows),
            "label_lat": [7.0] * len(rows),
        },
        geometry=[
            geoms.get(gid, box(ORIGIN_X, ORIGIN_Y, ORIGIN_X + 4000, ORIGIN_Y + 2000))
            for gid, _, _ in rows
        ],
        crs=5235,
    ).to_crs(4326)
    versions.to_parquet(tmp_path / "geography_versions.geoparquet")
    return tmp_path


def test_shared_borders_are_counted_once() -> None:
    squares = [_square(0, 0), _square(1, 0)]
    # Two squares: 8 km of outline in total, but the shared 1 km edge is one line, so 7 km.
    assert shapely.length(_borders(squares)) == 7000


def test_mesh_ranks_do_not_overlap_and_cover_every_border() -> None:
    gns = [_square(col, row) for col in range(4) for row in range(2)]
    ds = [shapely.union_all([_square(col, 0), _square(col, 1)]) for col in range(4)]
    districts = [shapely.union_all(ds[:2]), shapely.union_all(ds[2:])]
    country = shapely.union_all(districts)
    ranked = _ranked_mesh([[country], districts, ds, gns])
    lengths = [shapely.length(geom) for geom in ranked]
    # Coast 12 km; one district border 2 km; two more DS borders 4 km; four GN borders 4 km.
    assert lengths == [12000, 2000, 4000, 4000]
    assert sum(lengths) == shapely.length(_borders(gns))
    for i, a in enumerate(ranked):
        for b in ranked[i + 1 :]:
            assert shapely.length(shapely.intersection(a, b)) == 0


def test_geometry_bundle_nests_and_has_no_gaps(tmp_path: Path) -> None:
    (tmp_path / "spine").mkdir()
    spine = _spine(tmp_path / "spine")
    out = tmp_path / "out"
    summary = build_geometry(spine, out)
    assert summary["gn_polygons"] == 8
    assert summary["ds_polygons"] == 4
    assert summary["detail_files"] == 2

    overview = gpd.read_file(out / "overview.geojson")
    assert len(overview) == 4
    # DS polygons tile the country exactly: no gap and no overlap between neighbours.
    union = shapely.union_all(overview.geometry.values)
    total = sum(geom.area for geom in overview.geometry.values)
    assert abs(union.area - total) < 1e-12

    mesh = json.loads((out / "mesh.geojson").read_text())
    assert [feature["properties"]["rank"] for feature in mesh["features"]] == [0, 2, 3]

    detail = json.loads((out / "detail" / "LK11.json").read_text())
    assert len(detail["gn"]["features"]) == 4
    assert {f["properties"]["ds"] for f in detail["gn"]["features"]} == {"LK1100", "LK1101"}
    # Inside a district only DS and GN borders are written; district borders live in fine.json.
    assert {f["properties"]["rank"] for f in detail["mesh"]["features"]} == {3, 4}

    units = json.loads((out / "units.json").read_text())
    assert units["LK11"]["p"] == "LK1"
    assert units["LK1100"]["l"] == 3
    assert len(units["LK"]["b"]) == 4


def test_adjacency_is_symmetric_and_keeps_the_kind(tmp_path: Path) -> None:
    spine = tmp_path
    pd.DataFrame(
        [{"geography_id": "LK11", "level": 2, "parent_id": "LK1", "name_en": "A"}]
    ).to_parquet(spine / "geographies.parquet")
    (spine / "spatial").mkdir()
    pd.DataFrame(
        [
            {"geography_id": "LK11", "neighbour_id": "LK12", "type": "border"},
            {"geography_id": "LK13", "neighbour_id": "LK11", "type": "distance_band"},
        ]
    ).to_parquet(spine / "spatial" / "adjacency_district_cod-ab-v03.parquet")
    summary = build_adjacency(spine, tmp_path / "out")
    graph = json.loads((tmp_path / "out" / "adjacency.json").read_text())["district"]
    assert graph["LK11"] == [["LK12", 0], ["LK13", 1]]
    assert graph["LK12"] == [["LK11", 0]]
    assert graph["LK13"] == [["LK11", 1]]
    assert summary["pairs"] == {"district": 2}
