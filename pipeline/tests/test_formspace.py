"""Building shape roll-up and the form and context spaces (synthetic fixtures only)."""

from __future__ import annotations

import json

import geopandas as gpd
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
import shapely
from shapely.geometry import box

from slf import profile
from slf.spatial import buildings, formspace, layers, zonal


def _held_buildings(root, geometries, heights):
    folder = root / "raw" / "overture" / "overture-buildings" / "20260101T000000Z"
    folder.mkdir(parents=True)
    name = "overture-buildings-lk.parquet"
    sources = [[{"dataset": "OpenStreetMap"}] for _ in geometries]
    table = pa.table(
        {
            "geometry": [shapely.to_wkb(g) for g in geometries],
            "sources": sources,
            "height": pa.array(heights, type=pa.float64()),
        }
    )
    pq.write_table(table, folder / name)
    (folder / f"{name}.meta.json").write_text(
        json.dumps({"sha256": "ab" * 32, "url": "x", "retrieved_at": "20260101T000000Z"})
    )


def _zones():
    frame = gpd.GeoDataFrame(
        {"geography_id": ["LK-A", "LK-B"]},
        geometry=[box(80.0, 7.0, 80.1, 7.1), box(80.1, 7.0, 80.2, 7.1)],
        crs="EPSG:4326",
    )
    return zonal.Zones.from_frame(frame)


def test_building_rollup_measures_shape_in_metres(tmp_path):
    # ~10 m square (compactness 0.785) and a ~4 m x 50 m sliver (compactness about 0.12)
    d = 0.0001  # about 11 m
    square = box(80.01, 7.01, 80.01 + d, 7.01 + d)
    sliver = box(80.03, 7.03, 80.03 + 0.00004, 7.03 + 0.00045)
    big = box(80.15, 7.05, 80.15 + 0.0003, 7.05 + 0.0003)  # about 33 m x 33 m, over 250 m2
    _held_buildings(tmp_path, [square, sliver, big], [np.nan, np.nan, 9.0])
    out = buildings.rollup([tmp_path], _zones(), tmp_path / "cache")
    assert out is not None
    assert out.count.tolist() == [2, 1]
    assert out.shaped.tolist() == [2, 1]
    assert out.small.tolist() == [0, 0]
    assert out.large.tolist() == [0, 1]
    assert out.with_height.tolist() == [0, 1]
    # square: compactness pi/4; the sliver is far less compact
    mean_a = out.compact_sum[0] / out.shaped[0]
    assert 0.4 < mean_a < 0.6
    assert out.compact_sum[1] == pytest.approx(np.pi / 4, abs=0.02)
    assert out.perimeter_m[0] > 0


def test_building_specs_name_existing_components():
    for key in (
        "buildings_small_share",
        "buildings_large_share",
        "buildings_per_km2",
        "building_coverage_share",
    ):
        spec = layers.SPECS[key]
        assert spec.denominator in layers.SPECS
        assert spec.numerator in layers.SPECS
    for key in ("building_compactness_mean", "building_height_mean", "biomass_agb_mean"):
        assert layers.SPECS[key].aggregation == "none"


def test_biomass_scale_and_height_validity(tmp_path):
    # int16 stored times 10, nodata -9999; the mean is 40 and 120 Mg/ha over two cells
    moments = zonal.Moments(1, valid=lambda a: a >= 0)
    labels = np.array([[1, 1, 1]], dtype=np.uint16)
    values = np.array([[400, 1200, -9999]], dtype=np.int16)
    moments.add(labels, values, np.array([[10_000.0]]))
    assert moments.area[1] == 20_000.0
    assert moments.invalid_area[1] == 10_000.0
    assert moments.weighted[1] / 10.0 / moments.area[1] == pytest.approx(80.0)


def _ledger(n_gn: int = 60):
    rng = np.random.default_rng(3)
    geos = [("LK1103", 3, "LK11")] + [(f"LK1103{i:03d}", 4, "LK1103") for i in range(n_gn)]
    geos += [("LK1104", 3, "LK11")] + [(f"LK1104{i:03d}", 4, "LK1104") for i in range(n_gn)]
    frame = pd.DataFrame(geos, columns=["geography_id", "level", "parent_id"])
    frame["name_en"] = frame.geography_id
    rows = []

    def add(indicator, period, f):
        for g in frame.geography_id:
            rows.append((indicator, g, period, f(g)))

    def noisy(base):
        return lambda g: base * (1 + (g.startswith("LK1104")) + rng.random())

    add("buildings_per_km2", "2026", noisy(100))
    add("building_coverage_share", "2026", noisy(2))
    add("building_footprint_mean", "2026", noisy(50))
    add("buildings_large_share", "2026", noisy(3))
    add("buildings_small_share", "2026", noisy(10))
    add("building_compactness_mean", "2026", lambda g: 0.5 + 0.2 * rng.random())
    add("building_height_mean", "2018", noisy(3))
    add("canopy_height_mean", "2026", noisy(4))
    add("canopy_15m_share", "2026", noisy(5))
    add("biomass_agb_mean", "2025", noisy(40))
    add("land_cover_cropland_share", "2021", noisy(10))
    add("land_cover_grassland_share", "2021", noisy(8))
    add("land_cover_water_share", "2021", noisy(2))
    add("land_cover_mapped_area", "2021", lambda g: 500.0)
    add("places_listed", "2026", noisy(6))
    obs = pd.DataFrame(rows, columns=["indicator_id", "geography_id", "period", "value"])
    return obs, frame


def test_form_and_context_distances_decompose_exactly(tmp_path):
    obs, geos = _ledger()
    for spec in formspace.SPECS.values():
        summary = formspace.build(spec, obs, geos, tmp_path / spec.space_id)
        gn = summary["levels"]["gn"]
        assert gn["places"] == 120
        assert gn["checks"]["max_abs_decomposition_error"] < 1e-9
        vectors = pd.read_parquet(
            tmp_path / spec.space_id / "vectors" / f"{spec.space_id}_v0.1.parquet"
        )
        assert set(vectors.space_id) == {spec.space_id}
        assert set(vectors.space_version) == {"0.1"}
        similar = json.loads((tmp_path / spec.space_id / "vectors" / "similar_gn.json").read_text())
        assert similar["space_id"] == spec.space_id and similar["space_version"] == "0.1"
        first = next(iter(similar["places"].values()))
        assert len(first) == formspace.K and len(first[0][2]) == formspace.EXPLAIN_TOP
        assert "# QA" in formspace.render_qa(spec, summary)


def test_places_with_an_undefined_input_are_excluded_and_named(tmp_path):
    obs, geos = _ledger()
    mask = (obs.indicator_id == "building_height_mean") & (obs.geography_id == "LK1103005")
    obs.loc[mask, "value"] = np.nan
    summary = formspace.build(formspace.FORM, obs, geos, tmp_path)
    excluded = summary["levels"]["gn"]["excluded"]
    assert excluded == [{"geography_id": "LK1103005", "reason": "no value for height"}]
    assert summary["levels"]["gn"]["places"] == 119


def test_decompose_function_is_the_profile_one():
    assert formspace.profile.decompose is profile.decompose
