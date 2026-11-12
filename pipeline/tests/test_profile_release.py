"""Profile packaging for releases (D-031): DS lists ship, GN lists do not."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from slf import profile, profile_release

REPO = Path(__file__).resolve().parents[2]
V = profile.SPACE_VERSION
P = profile.PERIOD


def _fixture(root: Path) -> Path:
    vec = root / "vectors"
    vec.mkdir(parents=True)
    rows = [
        ("place", "LK1103", "ds", [1.0, 0.5, -0.2]),
        ("place", "LK1106", "ds", [0.9, 0.4, -0.1]),
        ("place", "LK1103005", "gn", [2.0, 0.1, 0.3]),
        ("indicator", "population_total", "gn", [0.3, 0.0, 0.1]),
    ]
    pd.DataFrame(
        [
            {
                "entity_type": t,
                "entity_id": i,
                "level": lv,
                "period": P,
                "space_id": "profile",
                "space_version": V,
                "vector": v,
                "norm": 1.0,
            }
            for t, i, lv, v in rows
        ]
    ).to_parquet(vec / f"profile_v{V}.parquet")
    axes = [
        {
            "level": lv,
            "axis": a,
            "eigenvalue": 0.5,
            "variance_explained": 0.3,
            "retained": True,
            "indicator_id": "population_total",
            "loading": 0.4,
            "draft_label": f"axis {a}",
            "label_status": "machine_generated_draft",
            "space_id": "profile",
            "space_version": V,
        }
        for lv in ("gn", "ds")
        for a in (1, 2, 3)
    ]
    pd.DataFrame(axes).to_parquet(vec / f"profile_v{V}_axes.parquet")
    similar = {
        "indicators": ["population_total", "sex_ratio"],
        "places": {
            "LK1103": [["LK1106", 0.81, [[1, -0.1]], [[0, 0.9]]]],
            "LK1106": [["LK1103", 0.81, [[1, -0.1]], [[0, 0.9]]]],
        },
    }
    (vec / f"similar_ds_{P}.json").write_text(json.dumps(similar), encoding="utf-8")
    for level, ids in (("ds", ["LK1103", "LK1106"]), ("gn", ["LK1103005"])):
        pd.DataFrame(
            {
                "geography_id": ids,
                "distance_from_centre": [1.5] * len(ids),
                "percentile": [90.0] * len(ids),
                "top_indicators": [["population_total"]] * len(ids),
            }
        ).to_parquet(vec / f"unusual_{level}_{P}.parquet")
    return root


GEOS = pd.DataFrame(
    {
        "geography_id": ["LK1103", "LK1106", "LK1103005"],
        "name_en": ["Colombo", "Kolonnawa", "Sammanthranapura"],
        "parent_id": ["LK11", "LK11", "LK1103"],
    }
)


def test_ds_gets_similar_list_and_gn_does_not(tmp_path: Path):
    src = _fixture(tmp_path / "profile")
    out = tmp_path / "release"
    res = profile_release.build(src, REPO / "catalog", out, GEOS)
    assert not res.errors
    ds, gn = res.payloads["LK1103"], res.payloads["LK1103005"]
    assert ds["similar"][0] == {
        "geography_id": "LK1106",
        "name_en": "Kolonnawa",
        "distance": 0.81,
        "alike": ["sex_ratio"],
        "different": ["population_total"],
    }
    assert gn["similar"] is None and gn["similar_via"] == "LK1103"
    for block in (ds, gn):
        assert block["space_id"] == "profile" and block["space_version"] == V
        assert all(a["label_status"] == "machine_generated_draft" for a in block["axes"])
    assert "population_total" not in res.payloads  # indicator vectors are not places
    shipped = sorted(p.name for p in (out / "vectors").iterdir())
    assert f"similar_gn_{P}.json" not in shipped
    assert shipped == sorted(profile_release.shipped_files(V))


def test_missing_profile_build_is_an_error(tmp_path: Path):
    res = profile_release.build(tmp_path, REPO / "catalog", tmp_path / "out", GEOS)
    assert res.errors and "slf profile build" in res.errors[0]
