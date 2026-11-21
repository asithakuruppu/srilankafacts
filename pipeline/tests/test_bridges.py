"""Bridge methods stamp their method and nature, keep exact sums exact and drop nothing."""

from __future__ import annotations

from typing import Any

from shapely.geometry import box

from slf import bridges, covers

MEMBERS = {"U1": {"A": 1.0, "B": 1.0}, "U2": {"B": 0.25, "C": 1.0}}


def test_aggregate_sum_exact_for_whole_gns_and_flags_splits_and_missing() -> None:
    rows = {
        r["geography_id"]: r for r in bridges.aggregate_sum({"A": 10, "B": 20, "C": 5}, MEMBERS)
    }
    assert rows["U1"]["value"] == 30 and rows["U1"]["exact"] is True
    assert rows["U1"]["data_nature"] == "census_count"
    assert rows["U2"]["value"] == 10.0 and rows["U2"]["exact"] is False
    assert rows["U2"]["data_nature"] == "modelled_estimate"
    assert rows["U2"]["derived_by"] == bridges.AGGREGATE_SUM
    partial = {r["geography_id"]: r for r in bridges.aggregate_sum({"A": 1}, MEMBERS)}
    assert partial["U1"]["value"] is None and partial["U1"]["missing_gn"] == ["B"]


def test_aggregate_recompute_does_not_average_rates() -> None:
    num = {"A": 1, "B": 9}
    den = {"A": 10, "B": 90}
    row = bridges.aggregate_recompute(num, den, {"U": {"A": 1.0, "B": 1.0}}, scale=100)[0]
    assert row["value"] == 10.0 and row["numerator"] == 10 and row["denominator"] == 100
    zero = bridges.aggregate_recompute({"A": 1}, {"A": 0}, {"U": {"A": 1.0}})[0]
    assert zero["value"] is None


def test_apportion_round_trip_is_exact() -> None:
    weights = [
        {"geography_id": "A", "h3": "c1", "weight": 0.75},
        {"geography_id": "A", "h3": "c2", "weight": 0.25},
    ]
    cells = bridges.apportion_weighted({"A": 100.0}, weights, "test_source")
    assert {c["data_nature"] for c in cells} == {"modelled_estimate"}
    assert abs(sum(c["value"] for c in cells) - 100.0) < 1e-12
    assert cells[0]["weight_source"] == "test_source"


def test_point_in_polygon_records_vintage_border_and_misses() -> None:
    polygons = {"P": box(0, 0, 1, 1), "Q": box(1, 0, 2, 1)}
    rows = {
        r["point_id"]: r
        for r in bridges.point_in_polygon(
            [("in", 0.5, 0.5), ("edge", 1.0, 0.5), ("out", 5.0, 5.0)], polygons, "v1"
        )
    }
    assert rows["in"]["geography_id"] == "P" and rows["in"]["on_border"] is False
    assert rows["edge"]["on_border"] is True
    assert rows["out"]["geography_id"] is None
    assert rows["in"]["boundary_vintage"] == "v1"


def test_zonal_stats_sum_and_mean_with_licence() -> None:
    values = {"c1": 2.0, "c2": 4.0, "c3": 9.0, "c4": 1.0}
    zones = {"c1": "Z", "c2": "Z", "c3": "Y"}
    total = {r["geography_id"]: r for r in bridges.zonal_stats(values, zones, "sum", "CC BY 4.0")}
    mean = {r["geography_id"]: r for r in bridges.zonal_stats(values, zones, "mean", "CC BY 4.0")}
    assert total["Z"]["value"] == 6.0 and mean["Z"]["value"] == 3.0 and total["Y"]["cells"] == 1
    assert total["Z"]["source_licence"] == "CC BY 4.0"


def test_covers_fractions_sum_to_one_including_split_gn() -> None:
    gn_cells = {"A": ["a1", "a2"], "B": ["b1", "b2", "b3", "b4"]}
    cov: Any = covers.cover({"U": {"A": 1.0, "B": 0.5}, "V": {"B": 1.0}}, gn_cells)
    sums: Any = cov.groupby("footprint_ref")["fraction"].sum()
    assert float(abs(sums - 1.0).max()) < 1e-12
    u: Any = cov[cov.footprint_ref == "U"].set_index("h3")["fraction"]
    assert abs(u["a1"] - 1 / 3) < 1e-12 and abs(u["b1"] - 1 / 12) < 1e-12
    summary = covers.check(cov)
    assert summary["footprints"] == 2


def test_expand_districts() -> None:
    admin = {"D1": {"A": 1.0, "B": 1.0}, "D2": {"C": 1.0}}
    assert covers.expand_districts({"ED": {"D1": 1.0, "D2": 1.0}}, admin) == {
        "ED": {"A": 1.0, "B": 1.0, "C": 1.0}
    }
