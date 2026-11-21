"""Atlas bundle: shared borders are written once and ranked by the level they divide."""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
import shapely
from shapely.geometry import box

from slf import atlas
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


def test_release_boundaries_share_edges(tmp_path: Path) -> None:
    """Release boundaries are simplified as a coverage: neighbours never overlap (D-043)."""
    import geopandas as gpd
    import pandas as pd

    from slf.release import _boundary_frames

    spine = _spine(tmp_path)
    geographies = pd.read_parquet(spine / "geographies.parquet")
    versions = gpd.GeoDataFrame(gpd.read_parquet(spine / "geography_versions.geoparquet"))
    versions["status"] = "current"
    geographies["name_si"] = None
    geographies["name_ta"] = None
    notes: list[str] = []
    frames = _boundary_frames(versions, geographies, notes)
    assert notes == []
    total = {
        level: float(frame.to_crs(5235).geometry.area.sum()) for level, frame in frames.items()
    }
    for level, frame in frames.items():
        union = frame.to_crs(5235).geometry.union_all()
        # Rounding to 6 decimals moves vertices by centimetres; allow one part in 10,000.
        assert abs(total[level] - union.area) < total[level] * 1e-4, level
    assert abs(total[0] - total[4]) < total[4] * 1e-4


def test_ed_geometry_is_dissolved_from_districts_and_borders_drawn_once(tmp_path: Path) -> None:
    (tmp_path / "spine").mkdir()
    spine = _spine(tmp_path / "spine")
    out = tmp_path / "out"
    # Both districts form one ED (as Jaffna ED = Jaffna + Kilinochchi): no internal ED border.
    one = build_geometry(spine, out, {"LK11": "LK-ED-01", "LK12": "LK-ED-01"})["electoral"]
    assert one["units"]["LK-ED-01"]["districts"] == ["LK11", "LK12"]
    mesh = json.loads((out / "ed-mesh.geojson").read_text())
    assert [f["properties"]["rank"] for f in mesh["features"]] == [0]
    # Two EDs: the district border becomes the ED border, rank 2.
    two = build_geometry(spine, out, {"LK11": "LK-ED-01", "LK12": "LK-ED-02"})["electoral"]
    assert sorted(two["units"]) == ["LK-ED-01", "LK-ED-02"]
    mesh = json.loads((out / "ed-mesh.geojson").read_text())
    assert [f["properties"]["rank"] for f in mesh["features"]] == [0, 2]
    overview = json.loads((out / "overview.geojson").read_text())
    assert {f["properties"]["ed"] for f in overview["features"]} == {"LK-ED-01", "LK-ED-02"}
    detail = json.loads((out / "detail" / "LK12.json").read_text())
    assert {f["properties"]["ed"] for f in detail["gn"]["features"]} == {"LK-ED-02"}


def test_electoral_bundle_keeps_release_values_and_ballot_order(tmp_path: Path) -> None:
    from slf.atlas import build_electoral

    release = tmp_path / "release"
    (release / "observations").mkdir(parents=True)
    (release / "geographies").mkdir()
    catalog = tmp_path / "catalog"
    (catalog / "geographies" / "relations").mkdir(parents=True)

    def obs(gid, ind, value, breakdown=None, status="normal"):
        return {
            "geography_id": gid,
            "indicator_id": ind,
            "value": value,
            "breakdown": breakdown,
            "value_status": status,
            "verification": "machine_extracted",
            "source_locator": f"{gid} sheet",
            "snapshot_sha256": "ab" * 32,
            "period": "2024-09-21",
            "release": "vtest",
        }

    def cand(ballot, postal=False):
        return {
            "ballot_number": str(ballot),
            "candidate": f"C{ballot}",
            "party": f"P{ballot}",
            "vote_type": "postal" if postal else None,
        }

    rows = [
        obs("LK-ED-01", "votes_valid", 100.0),
        obs("LK-ED-01", "turnout", 80.0),
        obs("LK-ED-01", "votes_candidate", 60.0, cand(2)),
        obs("LK-ED-01", "votes_candidate", 40.0, cand(1)),
        obs("LK-ED-01", "votes_candidate", None, cand(1, postal=True), "not_available"),
        obs("LK-ED-01", "votes_valid", 5.0, {"vote_type": "postal", "ballot_number": None}),
        obs("LK-PD-01A", "votes_valid", 95.0),
    ]
    pd.DataFrame(rows).to_parquet(release / "observations" / "election-results.parquet")
    pd.DataFrame(
        [
            {"geography_id": "LK-ED-01", "code_system": "election-commission",
             "external_code": "1", "external_name": "Colombo"},
            {"geography_id": "LK-PD-01A", "code_system": "election-commission",
             "external_code": "1-A", "external_name": "Colombo North"},
        ]
    ).to_csv(release / "geographies" / "electoral-ec-2024.csv", index=False)  # fmt: skip
    pd.DataFrame(
        [{"geography_id": "LK-ED-01", "related_id": "LK-PD-01A", "relation": "parent"}]
    ).to_csv(catalog / "geographies" / "relations" / "electoral_ec-2024.csv", index=False)

    summary = build_electoral(release, catalog, tmp_path, {"LK-ED-01": {"c": [80, 7]}})
    assert (summary["eds"], summary["pds"], summary["candidates"]) == (1, 1, 2)
    data = json.loads((tmp_path / "electoral.json").read_text())
    ed = data["eds"][0]
    assert ed["name"] == "Colombo" and ed["c"] == [80, 7]
    assert ed["values"]["votes_valid"] == 100.0 and ed["postal"]["votes_valid"] == 5.0
    # Ballot order, not vote order; a postal unread cell never leaks into the total.
    assert [v[0] for v in ed["votes"]] == [1, 2]
    assert ed["votes"][0][1] == 40.0
    assert ed["not_available"] == 1
    assert data["pds"][0]["parent"] == "LK-ED-01"
    assert [c["ballot"] for c in data["candidates"]] == [1, 2]


def test_split_lines_keeps_every_vertex_and_joins_the_pieces() -> None:
    from slf.atlas import _split_lines

    line = shapely.LineString([(float(i), 0.0) for i in range(50)])
    pieces = _split_lines(line, max_points=20)
    assert [len(shapely.get_coordinates(p)) for p in pieces] == [20, 20, 12]
    assert shapely.length(shapely.union_all(pieces)) == shapely.length(line)


def test_public_bundle_leaves_out_the_trajectory_space(tmp_path: Path) -> None:
    spaces = tmp_path / "spaces"
    spaces.mkdir()
    for name in atlas.SPACE_FILES:
        (spaces / name).write_text(json.dumps({"space_id": name, "space_version": "1"}))
    private = atlas.build_spaces(spaces, tmp_path / "private")
    public = atlas.build_spaces(spaces, tmp_path / "public", public=True)
    assert "trajectory" in private["spaces"]
    assert "trajectory" not in public["spaces"] and "typology" in public["spaces"]
    assert not (tmp_path / "public" / "spaces" / "trajectory.json").exists()


def test_public_bundle_needs_a_publishable_release(tmp_path: Path) -> None:
    release = tmp_path / "release"
    (release / "api/v1/releases").mkdir(parents=True)
    (release / "api/v1/releases/latest.json").write_text(
        json.dumps({"release": "v1-preview", "publishable": False})
    )
    with pytest.raises(ValueError, match="not publishable"):
        atlas.export(release, tmp_path / "spine", tmp_path / "out", public=True)
