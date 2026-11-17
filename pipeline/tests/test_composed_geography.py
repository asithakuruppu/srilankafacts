"""GN-composed geographies (G05 la and health): composition, checks and the rights gate."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import box

from slf.datasets import composed_geography as cg

GNS = ["LK1101001", "LK1101002", "LK1101003", "LK1101004"]


def _spine(tmp_path: Path) -> Path:
    spine = tmp_path / "spine"
    spine.mkdir()
    pd.DataFrame(
        [{"geography_id": "LK1101", "level": 3}] + [{"geography_id": g, "level": 4} for g in GNS]
    ).to_parquet(spine / "geographies.parquet")
    gpd.GeoDataFrame(
        {"geography_id": GNS, "level": [4] * 4},
        geometry=[box(80 + i * 0.01, 7, 80.01 + i * 0.01, 7.01) for i in range(4)],
        crs=4326,
    ).to_parquet(spine / "geography_versions.geoparquet")
    return spine


def _census(tmp_path: Path) -> Path:
    census = tmp_path / "census"
    census.mkdir()
    rows = []
    for i, gn in enumerate(GNS):
        values = {name: 0.0 for name in cg.DENOMINATORS}
        values["population_total"] = 1000.0 * (i + 1)
        values["population_local_authority_municipal_council"] = 1000.0 * (i + 1) if i < 2 else 0.0
        values["population_local_authority_urban_council"] = 0.0
        values["population_local_authority_pradeshiya_sabha"] = 0.0 if i < 2 else 1000.0 * (i + 1)
        rows += [
            {"indicator_id": k, "geography_id": gn, "value": v, "breakdown": None}
            for k, v in values.items()
        ]
    pd.DataFrame(rows).to_parquet(census / "observations.parquet")
    return census


UNITS = [
    cg.Unit("001", "Alpha MC", "MC"),
    cg.Unit("002", "Beta PS", "PS"),
    cg.Unit("003", "Gamma PS"),
]
MEMBERS = [
    cg.Member("A1", "001"),
    cg.Member("A2", "001"),
    cg.Member("A3", "002", 0.5),
    cg.Member("A3", "001", 0.5),
    cg.Member("A3", "001", 0.5),  # repeated row
    cg.Member("A4", ""),  # the source assigns no unit
    cg.Member("A9", "002"),  # not in the crosswalk
    cg.Member("A1", "999"),  # unit not in the unit list
]
CROSSWALK = {f"A{i + 1}": gn for i, gn in enumerate(GNS)}


def _composed() -> cg.Composed:
    return cg.compose(
        cg.SCHEMES["la"], UNITS, MEMBERS, CROSSWALK, set(GNS), method="official_list", source="x"
    )


def test_compose_resolves_through_the_crosswalk_and_drops_nothing_silently() -> None:
    c = _composed()
    assert c.composition.members["LK-LA-001"] == {GNS[0]: 1.0, GNS[1]: 1.0, GNS[2]: 0.5}
    assert c.composition.members["LK-LA-002"] == {GNS[2]: 0.5}
    assert [m.gn_code for m in c.unmatched_gn] == ["A9"]
    assert [m.gn_code for m in c.unassigned] == ["A4"]
    assert [m.unit_code for m in c.unknown_unit] == ["999"]
    assert len(c.duplicates) == 1
    assert cg.split_gns(c.composition) == {GNS[2]: ["LK-LA-001", "LK-LA-002"]}
    assert cg.units_without_gn(c) == ["LK-LA-003"]


def test_pcode_membership_needs_no_crosswalk() -> None:
    c = cg.compose(
        cg.SCHEMES["health"],
        [cg.Unit("11001", "One")],
        [cg.Member(GNS[0], "11001"), cg.Member("LK9999999", "11001")],
        None,
        set(GNS),
        method="official_list",
        source="x",
    )
    assert c.composition.members == {"LK-MOH-11001": {GNS[0]: 1.0}}
    assert len(c.unmatched_gn) == 1


def test_la_kind_reads_only_the_three_types() -> None:
    assert cg.la_kind("Colombo MC") == "MC"
    assert cg.la_kind("Kolonnawa uc") == "UC"
    assert cg.la_kind("Kotte") is None


@pytest.mark.parametrize("publishable", [False, True])
def test_build_writes_checks_and_respects_the_rights_gate(tmp_path: Path, publishable) -> None:
    catalog = tmp_path / "catalog"
    (catalog / "geographies" / "codes").mkdir(parents=True)
    (catalog / "geographies" / "relations").mkdir(parents=True)
    out = tmp_path / "out"
    result = cg.build(
        _composed(),
        vintage="test-2026",
        code_system="x",
        relation_method="official_list",
        spine_dir=_spine(tmp_path),
        census_dirs=[_census(tmp_path)],
        catalog=catalog,
        out_dir=out,
        publishable=publishable,
        rights_note="test",
        unit_geoms={"LK-LA-001": box(80, 7, 80.03, 7.01), "LK-LA-002": box(80.02, 7, 80.03, 7.01)},
        published_totals={"LK-LA-001": 4000.0, "LK-LA-002": 1500.0},
    )
    s = result.summary
    assert s["weight_sums"] == {"0.0": 1, "1.0": 3}
    assert (s["units_listed"], s["units_with_gn"], s["units_without_gn"]) == (3, 2, 1)
    tag = "" if publishable else "_internal"
    den = pd.read_csv(out / f"la_denominators{tag}.csv")
    population = dict(zip(den["geography_id"], den["population_total"], strict=True))
    # 1000 + 2000 + half of 3000; and the other half of 3000
    assert population == {"LK-LA-001": 4500, "LK-LA-002": 1500}
    assert dict(zip(den["geography_id"], den["difference"], strict=True))["LK-LA-001"] == 500
    kinds = pd.read_csv(out / f"la_census_type_check{tag}.csv")
    shares = dict(zip(kinds["geography_id"], kinds["share_in_own_kind"], strict=True))
    assert shares["LK-LA-001"] == pytest.approx(3000 / 4500, abs=1e-4)
    assert shares["LK-LA-002"] == 1.0
    iou = pd.read_csv(out / f"la_iou{tag}.csv")
    assert dict(zip(iou["unit"], iou["iou"], strict=True))["LK-LA-001"] == pytest.approx(
        1.0, abs=1e-3
    )
    assert pd.read_csv(out / f"la_spine_gn_without_unit{tag}.csv")["gn"].tolist() == [GNS[3]]
    codes = catalog / "geographies" / "codes" / "la-test-2026.csv"
    rels = catalog / "geographies" / "relations" / "la_test-2026.csv"
    assert codes.exists() is publishable
    assert rels.exists() is publishable
    assert result.committed == publishable
    assert ("INTERNAL ONLY" in result.qa) != publishable
    if publishable:
        frame = pd.read_csv(rels)
        assert set(frame["relation"]) == {"composed_of"}
        assert float(frame["weight"].to_numpy().sum()) == 3.0


def test_rights_gate_reads_the_catalogue() -> None:
    catalog = Path(__file__).resolve().parents[2] / "catalog"
    ok, note = cg.rights_allow_catalog(catalog, "nuuuwan-gig-data")
    assert not ok and "unclear" in note
    ok, _ = cg.rights_allow_catalog(catalog, "cod-ab-lka")
    assert ok
    ok, note = cg.rights_allow_catalog(catalog, "no-such-dataset")
    assert not ok and "not in the catalogue" in note
