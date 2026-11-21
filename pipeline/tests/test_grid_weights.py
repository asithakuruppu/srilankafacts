"""Population-weighted grid: weights sum to 1, empty GNs fall back, totals round-trip."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin

from slf import grid, grid_weights


def _cells() -> list[grid.Row]:
    return [
        {"geography_id": "A", "h3": "a1", "method": grid.METHOD_CENTROID},
        {"geography_id": "A", "h3": "a2", "method": grid.METHOD_CENTROID},
        {"geography_id": "A", "h3": "a3", "method": grid.METHOD_CENTROID},
        {"geography_id": "B", "h3": "b1", "method": grid.METHOD_CENTROID},
        {"geography_id": "B", "h3": "b2", "method": grid.METHOD_CENTROID},
    ]


def test_weights_sum_to_one_with_equal_share_fallback() -> None:
    frame: Any = grid_weights.weight_rows(_cells(), {"a1": 30.0, "a2": 10.0})
    sums: Any = frame.groupby("geography_id")["weight"].sum()
    assert float(abs(sums - 1.0).max()) < 1e-12
    a: Any = frame[frame.geography_id == "A"].set_index("h3")
    assert a.loc["a1", "weight"] == 0.75 and a.loc["a3", "weight"] == 0.0
    b: Any = frame[frame.geography_id == "B"]
    assert set(b["method"]) == {grid_weights.METHOD_EQUAL}
    assert list(b["weight"]) == [0.5, 0.5]
    assert set(frame["information_floor"]) == {grid_weights.INFORMATION_FLOOR}


def test_apportion_round_trip_and_parent_view() -> None:
    frame: Any = grid_weights.weight_rows(_cells(), {"a1": 30.0, "a2": 10.0})
    totals: Any = pd.Series({"A": 1234.0, "B": 99.0})
    out: Any = grid_weights.apportion(frame, totals)
    back: Any = grid.to_gn(out.to_dict("records"))
    assert abs(back["A"] - 1234.0) < 1e-9 and abs(back["B"] - 99.0) < 1e-9


def test_pixel_mass_goes_to_the_cell_holding_the_pixel_centre(tmp_path) -> None:
    data = np.zeros((4, 4), dtype="float32")
    data[1, 1] = 5.0
    data[2, 2] = 7.0
    path = tmp_path / "wp.tif"
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=4,
        width=4,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=from_origin(80.0, 7.004, 0.001, 0.001),
        nodata=-99999.0,
    ) as dst:
        dst.write(data, 1)
    mass = grid_weights.pixel_mass_by_cell(path, 9)
    assert abs(sum(mass.values()) - 12.0) < 1e-9
