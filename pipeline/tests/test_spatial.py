"""Zonal statistics, acquisition and roll-up rules for the open spatial layers."""

import json

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
import rasterio
from rasterio.crs import CRS
from rasterio.transform import from_origin
from shapely.geometry import box

from slf.spatial import acquire, build, layers, zonal
from slf.storage import LocalStorage


def _zones() -> zonal.Zones:
    # two squares side by side near Sri Lanka's latitude, 0.1 degree each
    frame = gpd.GeoDataFrame(
        {"geography_id": ["LK-A", "LK-B"]},
        geometry=[box(80.0, 7.0, 80.1, 7.1), box(80.1, 7.0, 80.2, 7.1)],
        crs="EPSG:4326",
    )
    return zonal.Zones.from_frame(frame)


def _raster(path, data, *, west=79.9, north=7.2, pixel=0.01, crs="EPSG:4326", nodata=None):
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=data.shape[0],
        width=data.shape[1],
        count=1,
        dtype=data.dtype,
        crs=crs,
        transform=from_origin(west, north, pixel, pixel),
        nodata=nodata,
    ) as dst:
        dst.write(data, 1)
    return rasterio.open(path)


def test_row_areas_match_geodesic_area():
    areas = zonal.geographic_row_areas(7.2, 0.01, 0.01, 30)
    from pyproj import Geod

    expected, _ = Geod(ellps="WGS84").polygon_area_perimeter(
        [80.0, 80.01, 80.01, 80.0], [7.2, 7.2, 7.19, 7.19]
    )
    assert areas[0] == pytest.approx(abs(expected), rel=1e-6)
    assert areas[0] < areas[-1]  # pixels grow towards the equator


def test_class_areas_split_by_zone_and_sum_to_zone_area(tmp_path):
    data = np.zeros((30, 40), dtype=np.uint8)
    data[:, :25] = 10  # columns west of 80.15 are class 10, the rest class 40
    data[:, 25:] = 40
    lut = np.full(256, 2, dtype=np.int64)
    lut[10], lut[40] = 0, 1
    reducer = zonal.ClassAreas(2, lut, 3)
    with _raster(tmp_path / "c.tif", data) as dataset:
        used = zonal.walk([dataset], _zones(), reducer, block=16)
    table = reducer.table()
    assert used > 0
    # zone A lies wholly in class 10; zone B is half class 10, half class 40
    assert table[0, 1] == 0
    assert table[1, 0] == pytest.approx(table[1, 1], rel=1e-3)
    true_area = _zones().frame.geometry.to_crs(5235).area.to_numpy()
    assert table.sum(axis=1) == pytest.approx(true_area, rel=2e-3)


def test_block_size_does_not_change_the_result(tmp_path):
    data = (np.arange(30 * 40) % 7).astype(np.uint8).reshape(30, 40)
    lut = np.arange(256, dtype=np.int64) % 7
    results = []
    for block in (7, 16, 64):
        reducer = zonal.ClassAreas(2, lut, 7)
        with _raster(tmp_path / f"b{block}.tif", data) as dataset:
            zonal.walk([dataset], _zones(), reducer, block=block)
        results.append(reducer.table())
    assert np.allclose(results[0], results[1])
    assert np.allclose(results[0], results[2])


def test_upsampling_shares_a_coarse_cell_between_zones(tmp_path):
    # one 0.2-degree cell covering both zones; without sub-cells one zone would get nothing
    data = np.full((1, 1), 5000, dtype=np.uint16)
    reducer = zonal.Moments(2, valid=lambda a: a <= 10_000)
    with _raster(tmp_path / "u.tif", data, west=80.0, north=7.15, pixel=0.2) as dataset:
        zonal.walk([dataset], _zones(), reducer, upsample=20)
    assert reducer.area[1] > 0 and reducer.area[2] > 0
    assert reducer.area[1] == pytest.approx(reducer.area[2], rel=1e-2)
    assert reducer.mean() == pytest.approx([5000, 5000])


def test_moments_ignore_invalid_values_and_report_their_area(tmp_path):
    data = np.full((30, 40), 100.0, dtype=np.float32)
    data[:, :15] = -1.0  # invalid strip over half of zone A
    reducer = zonal.Moments(2, valid=lambda a: a >= 0, thresholds=(50.0,))
    with _raster(tmp_path / "m.tif", data) as dataset:
        zonal.walk([dataset], _zones(), reducer)
    assert reducer.mean() == pytest.approx([100.0, 100.0])
    assert reducer.invalid_area[1] == pytest.approx(reducer.area[1], rel=1e-2)
    assert reducer.invalid_area[2] == 0
    assert reducer.above[0][2] == pytest.approx(reducer.area[2])


def test_terrain_slope_of_a_tilted_plane(tmp_path):
    # rises 10 m per pixel going east; at 7 N a 0.01 degree pixel is about 1,105 m wide
    data = np.tile(np.arange(40, dtype=np.float32) * 10, (30, 1))
    reducer = zonal.Terrain(2)
    with _raster(tmp_path / "t.tif", data) as dataset:
        zonal.walk([dataset], _zones(), reducer, halo=1, block=16)
    expected = np.degrees(np.arctan(10 / 1104.6))
    assert reducer.slope.mean() == pytest.approx([expected, expected], rel=5e-3)
    assert reducer.elevation.minimum[1] == 100.0
    assert reducer.elevation.maximum[2] == 290.0


def test_forest_loss_counts_only_inside_tree_cover(tmp_path):
    cover = np.zeros((30, 40), dtype=np.uint8)
    cover[:, :20] = 80  # zone A forested, zone B not
    loss = np.zeros((30, 40), dtype=np.uint8)
    loss[10:15, :] = 5  # a band of loss in 2005 across both zones
    reducer = zonal.ForestChange(2, canopy_threshold=30, last_year=24)
    with (
        _raster(tmp_path / "cover.tif", cover) as c,
        _raster(tmp_path / "loss.tif", loss) as year,
    ):
        zonal.walk([c, year], _zones(), reducer)
    table = reducer.loss_table()
    assert table[0, 4] > 0 and table[0].sum() == pytest.approx(table[0, 4])
    assert table[1].sum() == 0
    assert reducer.loss_outside_cover[2] > 0
    assert reducer.cover[1] == pytest.approx(reducer.land[1])


def test_ground_scale_of_world_mollweide_is_below_one_near_the_equator():
    crs = CRS.from_string("ESRI:54009")
    scale = zonal.ground_scale(crs, (7_959_000.0, 0.0, 8_159_000.0, 200_000.0))
    assert 0.990 < scale < 0.996


def test_acquire_stores_meta_and_reuses_held_files(tmp_path, monkeypatch):
    calls: list[str] = []

    def fake_fetch(url: str, timeout: float) -> bytes:
        calls.append(url)
        if "broken" in url:
            raise OSError("no route")
        return b"bytes of " + url.encode()

    monkeypatch.setattr(acquire, "_fetch", fake_fetch)
    manifest = tmp_path / "manifest.csv"
    manifest.write_text(
        "source,dataset,filename,url,licence\n"
        "src,ds,a.tif,https://example.org/a.tif,CC BY 4.0\n"
        "src,ds,b.tif,https://example.org/broken.tif,CC BY 4.0\n"
    )
    storage = LocalStorage(tmp_path / "data")
    rows = acquire.read_manifest(manifest)
    first = acquire.acquire(storage, rows, pause=0)
    assert first[0].ref is not None and first[0].ref.licence_note == "CC BY 4.0"
    assert first[1].ref is None and "no route" in (first[1].error or "")
    meta = json.loads(storage.get(first[0].ref.key + ".meta.json"))
    assert meta["url"] == "https://example.org/a.tif"
    second = acquire.acquire(storage, rows[:1], pause=0)
    assert second[0].ref is not None and second[0].ref.reused
    assert calls.count("https://example.org/a.tif") == 1
    assert "❌" in acquire.inventory_markdown(first)


def test_hierarchy_sums_gn_values_to_every_level(tmp_path):
    geos = pd.DataFrame(
        {
            "geography_id": [
                "LK",
                "LK1",
                "LK11",
                "LK1103",
                "LK1103005",
                "LK1103010",
                "LK-ADM3-P0001",
            ],
            "level": [0, 1, 2, 3, 4, 4, 3],
            "parent_id": [None, "LK", "LK1", "LK11", "LK1103", "LK1103", "LK11"],
        }
    )
    geos.to_parquet(tmp_path / "geographies.parquet")
    pd.DataFrame(
        {
            "geography_id": ["LK-ADM3-P0001"],
            "related_id": ["LK1103010"],
            "relation": ["composed_of"],
        }
    ).to_parquet(tmp_path / "geography_relations.parquet")
    frame = gpd.GeoDataFrame(
        {"geography_id": ["LK1103005", "LK1103010"]},
        geometry=[box(80.0, 7.0, 80.1, 7.1), box(80.1, 7.0, 80.2, 7.1)],
        crs="EPSG:4326",
    )
    zones = zonal.Zones.from_frame(frame)
    h = build.Hierarchy.from_spine(zones, tmp_path)
    totals = dict(zip(h.ids, h.total(np.array([3.0, 4.0])), strict=True))
    assert totals["LK"] == 7.0 and totals["LK1103"] == 7.0
    assert totals["LK-ADM3-P0001"] == 4.0  # a provisional unit is the sum of its listed GNs
    assert h.ids[:2] == ["LK1103005", "LK1103010"]


def test_every_share_names_components_that_exist():
    for spec in layers.SPECS.values():
        if spec.aggregation == "recompute_from_components":
            assert spec.numerator in layers.SPECS and spec.denominator in layers.SPECS
        text = layers.indicator_yaml(spec)
        assert text.startswith(f"id: {spec.id}\n")
