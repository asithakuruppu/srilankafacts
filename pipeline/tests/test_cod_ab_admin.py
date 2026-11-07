"""Geography spine (G01): synthetic geometry tests, plus checks on the committed hierarchy."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box

from slf.datasets import cod_ab_admin as cab

REPO = Path(__file__).resolve().parents[2]
RELATIONS_CSV = REPO / "catalog" / "geographies" / "relations" / "admin_cod-ab-v03.csv"
BUILD = Path(__file__).resolve().parents[1] / "data" / "build" / "geography-spine"

D = 0.01  # degrees, ~1.1 km near Sri Lanka


def sq(col: int, row: int, size: float = D) -> object:
    x, y = 80.0 + col * D, 7.0 + row * D
    return box(x, y, x + size, y + size)


def frame(rows: list[tuple[str, int, str | None, object]]) -> tuple[pd.DataFrame, gpd.GeoDataFrame]:
    ids, levels, parents, geoms = zip(*rows, strict=True)
    geos = pd.DataFrame({"geography_id": ids, "level": levels, "parent_id": parents})
    g = gpd.GeoDataFrame(
        {"geography_id": ids, "level": levels}, geometry=list(geoms), crs="EPSG:4326"
    )
    rp = g.geometry.representative_point()
    g["label_lon"], g["label_lat"] = rp.x.values, rp.y.values
    return geos, g


@pytest.fixture
def toy() -> tuple[pd.DataFrame, gpd.GeoDataFrame]:
    """Country LK with provinces LK1 and LK2. In LK1, LK11 and LK12 share an edge and LK13
    touches LK12 only at a corner. LK21 in LK2 is an isolated island."""
    return frame(
        [
            ("LK", 0, None, box(80.0, 7.0, 80.2, 7.2)),
            ("LK1", 1, "LK", box(80.0, 7.0, 80.1, 7.2)),
            ("LK2", 1, "LK", box(80.1, 7.0, 80.2, 7.2)),
            ("LK11", 2, "LK1", sq(0, 0)),
            ("LK12", 2, "LK1", sq(1, 0)),  # shares an edge with LK11
            ("LK13", 2, "LK1", sq(2, 1)),  # touches LK12 only at a corner
            ("LK21", 2, "LK2", sq(15, 15)),  # isolated island
        ]
    )


def test_hierarchy_passes_on_toy(toy: tuple[pd.DataFrame, gpd.GeoDataFrame]) -> None:
    geos, _ = toy
    assert cab.check_hierarchy(geos) == []


def test_hierarchy_catches_bad_parents(toy: tuple[pd.DataFrame, gpd.GeoDataFrame]) -> None:
    geos, _ = toy
    bad = geos.copy()
    bad.loc[bad["geography_id"] == "LK11", "parent_id"] = "LK"  # skips a level
    bad.loc[bad["geography_id"] == "LK12", "parent_id"] = "LK9"  # does not exist
    bad = pd.concat([bad, bad.iloc[[3]]])  # duplicate id
    errors = " | ".join(cab.check_hierarchy(bad))
    assert "LK11: parent LK is level 0, expected 1" in errors
    assert "LK12: parent LK9 does not exist" in errors
    assert "duplicate geography_id" in errors


def test_adjacency_rook_with_island_distance_band(
    toy: tuple[pd.DataFrame, gpd.GeoDataFrame],
) -> None:
    _, g = toy
    adj = cab.adjacency(g, level=2)
    border = adj[adj["type"] == "border"]
    pairs = set(zip(border["geography_id"], border["neighbour_id"], strict=True))
    assert ("LK11", "LK12") in pairs and ("LK12", "LK11") in pairs  # symmetric
    assert ("LK12", "LK13") not in pairs  # corner touch is not a border
    shared = border.loc[border["geography_id"] == "LK11", "shared_border_m"].iloc[0]
    assert 1000 < shared < 1200  # ~0.01 degree of latitude
    band = adj[(adj["type"] == "distance_band")]
    assert set(band["geography_id"]) == {"LK13", "LK21"}
    assert len(band[band["geography_id"] == "LK21"]) == min(cab.DISTANCE_BAND_K, 3)


def test_outside_parent_detects_spill(toy: tuple[pd.DataFrame, gpd.GeoDataFrame]) -> None:
    geos, g = toy
    out = cab.outside_parent(g, geos).set_index("geography_id")
    # Reprojection bends straight edges slightly, so "inside" means a tiny share, not exactly 0.
    assert out.loc["LK11", "share_outside"] == pytest.approx(0.0, abs=1e-3)
    assert out.loc["LK21", "share_outside"] == pytest.approx(0.0, abs=1e-3)
    g2 = g.copy()
    g2.loc[g2["geography_id"] == "LK12", "geometry"] = box(80.095, 7.0, 80.105, 7.01)
    spill = cab.outside_parent(g2, geos).set_index("geography_id").loc["LK12", "share_outside"]
    assert spill == pytest.approx(0.5, abs=0.01)


def test_spatial_parent_disagreement_reported_not_fixed(
    toy: tuple[pd.DataFrame, gpd.GeoDataFrame],
) -> None:
    geos, g = toy
    wrong = geos.copy()
    wrong.loc[wrong["geography_id"] == "LK21", "parent_id"] = "LK1"
    dis = cab.spatial_parent_disagreements(g, wrong)
    assert dis.to_dict("records") == [
        {"geography_id": "LK21", "attribute_parent": "LK1", "spatial_parent": "LK2"}
    ]
    assert wrong.loc[wrong["geography_id"] == "LK21", "parent_id"].item() == "LK1"


def test_geo_vectors_are_unit_length(toy: tuple[pd.DataFrame, gpd.GeoDataFrame]) -> None:
    _, g = toy
    v = cab.geo_vectors(g)
    assert np.allclose(v["norm"], 1.0, atol=1e-6)
    assert set(v["space_id"]) == {"geo"} and len(v) == len(g)


def test_relations_are_parent_edges(toy: tuple[pd.DataFrame, gpd.GeoDataFrame]) -> None:
    geos, _ = toy
    geos = geos.assign(valid_from=None)
    rel = cab.build_relations(geos)
    assert len(rel) == len(geos) - 1
    assert set(rel["relation"]) == {"parent"} and set(rel["method"]) == {"attribute"}


# --- Committed hierarchy (runs in CI without downloading boundaries) -------------------------


def _edges() -> list[dict[str, str]]:
    with RELATIONS_CSV.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def test_committed_hierarchy_ampara_in_eastern_province() -> None:
    parent = {e["related_id"]: e["geography_id"] for e in _edges()}
    assert parent["LK52"] == "LK5"  # Lanka Data Layer has LK8 (Uva); see audit §7


def test_committed_hierarchy_is_a_tree_rooted_at_lk() -> None:
    edges = _edges()
    children = Counter(e["related_id"] for e in edges)
    assert max(children.values()) == 1, "a unit has more than one parent"
    parent = {e["related_id"]: e["geography_id"] for e in edges}
    depth: Counter[int] = Counter()
    for unit in parent:
        d, cur = 0, unit
        while cur in parent:
            cur, d = parent[cur], d + 1
            assert d <= 4, f"{unit}: hierarchy deeper than 4 levels"
        assert cur == "LK", f"{unit}: does not roll up to LK"
        depth[d] += 1
    assert dict(depth) == {1: 9, 2: 25, 3: 339, 4: 14043}  # HDX: 9 / 25 / 339 / 14,043


@pytest.mark.skipif(not (BUILD / "geographies.parquet").exists(), reason="run `slf spine build`")
def test_local_build_matches_committed_hierarchy() -> None:
    geos = pd.read_parquet(BUILD / "geographies.parquet")
    geos = pd.DataFrame(geos[geos["status"] == "current"])  # provisional edges: catalogue
    built = set(
        zip(
            geos["parent_id"].dropna(),
            geos.loc[geos["parent_id"].notna(), "geography_id"],
            strict=True,
        )
    )
    committed = {(e["geography_id"], e["related_id"]) for e in _edges()}
    assert built == committed


def test_provisional_unit_is_composed_of_kalmunai_north_gns() -> None:
    rel = pd.read_csv(REPO / "catalog" / "geographies" / "relations" / "provisional.csv", dtype=str)
    members = rel[(rel["geography_id"] == "LK-ADM3-P0001") & (rel["relation"] == "composed_of")]
    assert len(members) == 29
    parent = {e["related_id"]: e["geography_id"] for e in _edges()}
    assert {parent[m] for m in members["related_id"]} == {"LK5221"}  # all inside COD-AB Kalmunai


def test_add_provisional_unions_members(
    tmp_path: Path, toy: tuple[pd.DataFrame, gpd.GeoDataFrame]
) -> None:
    geos, g = toy
    geos = geos.assign(status="current", name_en=geos["geography_id"])
    g = gpd.GeoDataFrame(g.assign(status="current"), crs="EPSG:4326")
    (tmp_path / "geographies" / "relations").mkdir(parents=True)
    (tmp_path / "geographies" / "provisional.csv").write_text(
        "geography_id,scheme,level,name_en,name_si,name_ta,parent_id,status,valid_from,source,evidence,notes\n"
        "LK-ADM1-P0001,admin,1,Toy Sub,,,LK,provisional,,x,y,\n"
    )
    (tmp_path / "geographies" / "relations" / "provisional.csv").write_text(
        "geography_id,related_id,relation,vintage,weight,method,source,valid_from,valid_to,notes\n"
        "LK-ADM1-P0001,LK11,composed_of,v,1.0,official_list,x,,,\n"
        "LK-ADM1-P0001,LK12,composed_of,v,1.0,official_list,x,,,\n"
    )
    ref = cab.SnapshotRef(
        key="k",
        sha256="a" * 64,
        url=None,
        retrieved_at="t",
        size_bytes=1,
        licence_note=None,
        reused=True,
    )
    geos2, v2, _rel, errors = cab.add_provisional(geos, g, tmp_path, ref)
    assert errors == []
    row = v2[v2["geography_id"] == "LK-ADM1-P0001"].iloc[0]
    assert row["status"] == "provisional"
    assert row["area_km2"] == pytest.approx(2 * 1.1 * 1.1, rel=0.05)  # two ~1.1 km squares
    assert cab.check_hierarchy(geos2) == []
