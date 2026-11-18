"""Analytic grid: weights sum to 1 and GN counts survive a round trip through cells."""

from __future__ import annotations

import geopandas as gpd
from shapely.geometry import box

from slf import grid


def _versions() -> gpd.GeoDataFrame:
    # Two ordinary GNs of about 1 km by 1 km, and one far too small to hold a cell centre.
    geoms = [
        box(80.000, 7.000, 80.009, 7.009),
        box(80.009, 7.000, 80.018, 7.009),
        box(80.0300, 7.0300, 80.0301, 7.0301),
    ]
    return gpd.GeoDataFrame(
        {
            "geography_id": ["LK1103001", "LK1103002", "LK1103003"],
            "level": [4, 4, 4],
            "label_lon": [80.0045, 80.0135, 80.03005],
            "label_lat": [7.0045, 7.0045, 7.03005],
        },
        geometry=geoms,
        crs=4326,
    )


def test_weights_sum_to_one_and_no_gn_is_dropped() -> None:
    weights = grid.gn_cells(_versions())
    sums: dict[str, float] = {}
    for row in weights:
        sums[row["geography_id"]] = sums.get(row["geography_id"], 0.0) + row["weight"]
    assert sorted(sums) == ["LK1103001", "LK1103002", "LK1103003"]
    assert max(abs(value - 1.0) for value in sums.values()) < 1e-12
    tiny = [row["method"] for row in weights if row["geography_id"] == "LK1103003"]
    assert tiny == [grid.METHOD_FALLBACK]


def test_cells_of_ordinary_gns_do_not_overlap() -> None:
    weights = grid.gn_cells(_versions())
    cells = [row["h3"] for row in weights if row["method"] == grid.METHOD_CENTROID]
    assert len(cells) == len(set(cells)) > 10


def test_counts_round_trip_exactly() -> None:
    weights = grid.gn_cells(_versions())
    counts = {"LK1103001": 1859.0, "LK1103002": 7.0, "LK1103003": 12345.0}
    back = grid.to_gn(grid.to_cells(counts, weights))
    for gid, value in counts.items():
        assert abs(back[gid] - value) < 1e-9
