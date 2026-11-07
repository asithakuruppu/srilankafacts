"""Geometry QA (G03) on small synthetic shapes near Sri Lanka."""

from __future__ import annotations

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import MultiPolygon, Polygon, box

from slf.datasets import geometry_qa as gq


def frame(rows: list[tuple[str, int, str | None, object]]) -> tuple[gpd.GeoDataFrame, pd.DataFrame]:
    ids, levels, parents, geoms = zip(*rows, strict=True)
    v = gpd.GeoDataFrame(
        {"geography_id": ids, "level": levels}, geometry=list(geoms), crs="EPSG:4326"
    )
    g = pd.DataFrame({"geography_id": ids, "level": levels, "parent_id": parents})
    return v, g


@pytest.fixture
def toy() -> tuple[gpd.GeoDataFrame, pd.DataFrame]:
    holed = Polygon(
        [(80.1, 7.0), (80.2, 7.0), (80.2, 7.1), (80.1, 7.1)],
        [[(80.14, 7.04), (80.16, 7.04), (80.16, 7.06), (80.14, 7.06)]],
    )
    return frame(
        [
            ("LK", 0, None, box(80.0, 7.0, 80.2, 7.1)),
            ("LK1", 1, "LK", box(80.0, 7.0, 80.1, 7.1)),
            ("LK2", 1, "LK", holed),  # leaves a hole → gap in LK coverage
            ("LK11", 2, "LK1", box(80.0, 7.0, 80.06, 7.1)),
            ("LK12", 2, "LK1", box(80.05, 7.0, 80.1, 7.1)),  # overlaps LK11 by 0.01°
            (
                "LK21",
                2,
                "LK2",
                MultiPolygon([box(80.1, 7.0, 80.13, 7.1), box(80.17, 7.0, 80.2, 7.1)]),
            ),
        ]
    )


def test_structure_counts_parts_and_holes(toy: tuple[gpd.GeoDataFrame, pd.DataFrame]) -> None:
    v, _ = toy
    s = gq.structure(v).set_index("level")
    assert s.loc[1, "units_with_holes"] == 1 and s.loc[1, "invalid"] == 0
    assert s.loc[2, "multipart_units"] == 1 and s.loc[2, "max_parts"] == 2


def test_overlaps_found_and_marked_as_siblings(toy: tuple[gpd.GeoDataFrame, pd.DataFrame]) -> None:
    v, g = toy
    ov = gq.sibling_overlaps(v, g, level=2)
    assert len(ov) == 1
    row = ov.iloc[0]
    assert {row["geography_id"], row["other_id"]} == {"LK11", "LK12"} and bool(row["same_parent"])
    assert row["overlap_km2"] == pytest.approx(1.1 * 11.0, rel=0.05)  # ~0.01 deg by 0.1 deg


def test_gaps_inside_parent(toy: tuple[gpd.GeoDataFrame, pd.DataFrame]) -> None:
    v, g = toy
    gaps = gq.parent_gaps(v, g, level=2)
    assert list(gaps["parent_id"]) == ["LK2"]  # LK21 leaves the middle strip of LK2 uncovered
    assert gaps.iloc[0]["gap_km2"] > 10
    assert gq.parent_gaps(v, g, level=1).iloc[0]["parent_id"] == "LK"  # LK2's hole


def test_nsdi_label_swap_detected(toy: tuple[gpd.GeoDataFrame, pd.DataFrame]) -> None:
    v, _ = toy
    # NSDI-like layer where the two district codes are attached to each other's polygons
    nsdi = gpd.GeoDataFrame(
        {"district_code": [11, 12], "district_name": ["A", "B"], "adjusted_area": [1, 1]},
        geometry=[box(80.06, 7.0, 80.1, 7.1), box(80.0, 7.0, 80.05, 7.1)],
        crs="EPSG:4326",
    )
    res = gq.compare_with_nsdi(v, nsdi, {"11": "LK11", "12": "LK12"}, level=2).set_index(
        "geography_id"
    )
    assert res.loc["LK11", "nsdi_polygon_mostly_on"] == "LK12"
    assert res.loc["LK12", "nsdi_polygon_mostly_on"] == "LK11"
    assert res.loc["LK11", "iou"] < 0.2


def test_no_repair_copy_when_all_valid(toy: tuple[gpd.GeoDataFrame, pd.DataFrame]) -> None:
    v, _ = toy
    assert gq.make_valid_copy(v).empty
    assert gq.invalid_reasons(v).empty
