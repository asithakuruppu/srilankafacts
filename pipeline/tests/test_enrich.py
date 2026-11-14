from pathlib import Path

import numpy as np
import pandas as pd

from slf.enrich import (
    _empirical_bayes_beta,
    _neighbour_summary,
    benjamini_hochberg,
    local_moran,
)


def _rook_grid(
    size: int = 7, outlier: float = 5.0
) -> tuple[dict[str, float], dict[str, list[str]]]:
    values: dict[str, float] = {}
    neighbours: dict[str, list[str]] = {}
    for row in range(size):
        for column in range(size):
            key = f"G{row:02d}{column:02d}"
            values[key] = 10.0 if 2 <= row < 5 and 2 <= column < 5 else 1.0
            neighbours[key] = []
    if outlier:
        values[f"G{size - 1:02d}{size - 1:02d}"] = outlier
    for row in range(size):
        for column in range(size):
            key = f"G{row:02d}{column:02d}"
            for d_row, d_column in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                other_row, other_column = row + d_row, column + d_column
                if 0 <= other_row < size and 0 <= other_column < size:
                    neighbours[key].append(f"G{other_row:02d}{other_column:02d}")
    return values, neighbours


def test_benjamini_hochberg_known_values():
    p_values = pd.Series([0.01, 0.02, 0.03, 0.9], index=list("abcd"))
    q_values = benjamini_hochberg(p_values)
    assert np.allclose(q_values.to_numpy(), [0.04, 0.04, 0.04, 0.9])


def test_local_moran_planted_cluster_and_outlier():
    values, neighbours = _rook_grid(7)
    series = pd.Series(values)
    result = local_moran(series, neighbours, permutations=999, seed=20241108)
    assert result.loc["G0303", "class"] == "high_high"
    assert result.loc["G0606", "class"] == "high_low"
    assert result["q_value"].dropna().between(0, 1).all()
    assert result.loc["G0303", "local_moran_i"] > 0


def test_local_moran_marks_islands_and_missing_values():
    values, neighbours = _rook_grid(5)
    values["ISLAND"] = 5.0
    values["MISSING"] = np.nan
    result = local_moran(pd.Series(values), neighbours, permutations=99, seed=20241108)
    assert result.loc["ISLAND", "class"] == "no_neighbours"
    assert result.loc["MISSING", "class"] == "no_data"
    assert result.loc["MISSING", "neighbour_count"] == 0


def test_neighbour_summary_excludes_self_and_missing():
    values = pd.Series({"A": 1.0, "B": 2.0, "C": 3.0, "D": np.nan, "E": 4.0})
    neighbours = {"A": ["B", "C", "D"], "B": ["A"], "C": ["A"], "D": ["A"], "E": []}
    summary = _neighbour_summary(values, neighbours)
    assert summary.loc["A", "neighbour_value_count"] == 2
    assert summary.loc["A", "neighbour_median"] == 2.5
    assert summary.loc["A", "neighbour_min"] == 2.0
    assert summary.loc["A", "neighbour_max"] == 3.0
    assert np.isnan(summary.loc["E", "neighbour_median"])


def test_empirical_bayes_beta_shrinks_small_denominators():
    numerator = np.array([1.0, 50.0, 100.0])
    denominator = np.array([10.0, 100.0, 1000.0])
    smoothed, prior_size = _empirical_bayes_beta(numerator, denominator)
    assert prior_size > 0
    assert smoothed[0] > 0.1
    assert abs(smoothed[2] - 0.1) < 0.01


def test_local_moran_constant_field_is_not_called_significant():
    values, neighbours = _rook_grid(6)
    constant = pd.Series({key: 5.0 for key in values})
    result = local_moran(constant, neighbours, permutations=99, seed=20241108)
    assert set(result["class"]) == {"not_significant"}


def test_build_spatial_context_skips_empty_levels_and_places_only(tmp_path):
    from slf.catalog import Catalog, CatalogReport, load_catalog
    from slf.enrich import build_spatial_context

    full = load_catalog(Path(__file__).resolve().parents[2] / "catalog", None, CatalogReport())
    gn_ids = ["LK1103005", "LK1103010", "LK1103015"]
    ds_ids = ["LK1103", "LK1106"]
    (tmp_path / "spatial").mkdir()
    for level_name, ids in (("gn", gn_ids), ("ds", ds_ids)):
        pd.DataFrame({"geography_id": ids[:-1], "neighbour_id": ids[1:]}).to_parquet(
            tmp_path / "spatial" / f"adjacency_{level_name}_test.parquet"
        )
    geographies = pd.DataFrame(
        {
            "geography_id": gn_ids + ds_ids,
            "level": [4] * len(gn_ids) + [3] * len(ds_ids),
            "parent_id": ["LK1103"] * len(gn_ids) + ["LK11"] * len(ds_ids),
            "name_en": gn_ids + ds_ids,
        }
    )
    rows = [("occupied_housing_units", g, 10.0 + i) for i, g in enumerate(gn_ids + ds_ids)]
    rows += [("housing_roof_tile", g, 5.0 + i) for i, g in enumerate(ds_ids)]
    rows += [("population_religion_hindu_share", g, 5.0 + i) for i, g in enumerate(ds_ids)]
    observations = pd.DataFrame(rows, columns=["indicator_id", "geography_id", "value"])
    observations["value_status"] = "normal"
    catalog = Catalog(
        indicators={
            k: full.indicators[k]
            for k in (
                "occupied_housing_units",
                "housing_roof_tile",
                "population_religion_hindu_share",
            )
        }
    )
    result = build_spatial_context(
        observations=observations,
        geographies=geographies,
        catalog=catalog,
        spine_dir=tmp_path,
        out=tmp_path / "out",
        permutations=9,
    )
    assert "stats/local_occupied_housing_units_gn.parquet" in result.files
    assert "stats/local_housing_roof_tile_ds.parquet" in result.files
    assert "stats/local_housing_roof_tile_gn.parquet" not in result.files
    assert not (tmp_path / "out" / "stats" / "local_housing_roof_tile_gn.parquet").exists()
    # D-033: places_only indicators get no neighbour comparisons at any level
    assert not [f for f in result.files if "population_religion" in f]
