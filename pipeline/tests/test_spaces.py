"""Vector spaces v2: typology, trajectory, composite and text (fixtures only)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from slf import profile as pf
from slf import spaces as sp


def _blobs(seed: int = 1) -> np.ndarray:
    rng = np.random.default_rng(seed)
    centres = np.array([[0.0, 0.0], [6.0, 0.0], [0.0, 6.0]])
    return np.vstack([c + rng.normal(scale=0.4, size=(30, 2)) for c in centres])


def test_kmeans_finds_separated_groups_and_is_stable() -> None:
    x = _blobs()
    truth = np.repeat([0, 1, 2], 30)
    labels, centres, _ = sp.kmeans(x, 3, np.random.default_rng(0))
    assert sp.adjusted_rand(labels, truth) == pytest.approx(1.0)
    assert sp.silhouette(x, labels) > 0.8
    stability, agreement = sp.bootstrap(x, 3, labels, np.random.default_rng(1), runs=10)
    assert stability > 0.95 and agreement.min() > 0.9
    assert centres.shape == (3, 2)


def test_adjusted_rand_is_label_free_and_zero_ish_for_noise() -> None:
    a = np.array([0, 0, 1, 1, 2, 2])
    assert sp.adjusted_rand(a, np.array([5, 5, 7, 7, 9, 9])) == pytest.approx(1.0)
    rng = np.random.default_rng(3)
    noise = [
        sp.adjusted_rand(rng.integers(3, size=300), rng.integers(3, size=300)) for _ in range(5)
    ]
    assert abs(float(np.mean(noise))) < 0.05


def _fit() -> pf.Fit:
    rng = np.random.default_rng(7)
    blocks = {"demography": ["a", "b"], "housing": ["c"], "identity": ["d", "e", "f"]}
    x = pd.DataFrame(
        rng.normal(size=(40, 6)),
        columns=["a", "b", "c", "d", "e", "f"],
        index=[f"LK{1100 + i}" for i in range(40)],
    )
    f = pf.fit(x, blocks)
    f.retained = [0, 1, 2]  # random inputs pass no retention rule; keep three axes for the test
    return f


def test_composite_blocks_sum_to_the_profile_scores_and_weights_scale_them(monkeypatch) -> None:
    f = _fit()
    blocks = {"demography": ["a", "b"], "housing": ["c"], "identity": ["d", "e", "f"]}
    monkeypatch.setitem(pf.BLOCKS_BY_LEVEL, "ds", blocks)
    names, contrib = sp.block_contributions(f)
    assert names == ["demography", "housing", "identity"]
    assert np.abs(contrib.sum(axis=1) - f.scores).max() < 1e-12
    equal = sp.composite_scores(contrib, [1, 1, 1])
    assert np.allclose(equal, f.scores)
    # Weight 0 removes a block exactly: the identity block no longer moves anyone.
    no_id = sp.composite_scores(contrib, [1, 1, 0])
    assert np.allclose(no_id, contrib[:, 0, :] + contrib[:, 1, :])


def test_nearest_rows_breaks_ties_by_id() -> None:
    z = np.array([[0.0], [1.0], [-1.0], [2.0]])
    rows = sp.nearest_rows(z, ["d", "b", "a", "c"], 2)
    assert rows["d"] == [["a", 1.0], ["b", 1.0]]


def test_typology_names_are_drafts_and_types_are_numbered_by_size(tmp_path: Path) -> None:
    rng = np.random.default_rng(2)
    x = pd.DataFrame(
        np.vstack([rng.normal(loc=m, scale=0.3, size=(n, 4)) for m, n in ((0, 30), (3, 12))]),
        columns=["a", "b", "c", "d"],
        index=[f"LK{2000 + i}" for i in range(42)],
    )
    f = pf.fit(x, {"demography": ["a", "b"], "housing": ["c", "d"]})
    summary = sp.build_typology(f, tmp_path, runs=5)
    data = json.loads((tmp_path / "typology.json").read_text())
    assert data["space_id"] == "typology" and data["space_version"] == sp.TYPOLOGY_VERSION
    sizes = [t["size"] for t in data["types"]]
    assert sizes == sorted(sizes, reverse=True) and sum(sizes) == 42
    assert {t["label_status"] for t in data["types"]} == {"machine_generated_draft"}
    assert summary["k"] in sp.K_RANGE
    assert len(data["type_of"]) == 42


def test_trajectory_keeps_only_one_to_one_units_and_carries_the_flag(tmp_path: Path) -> None:
    history = tmp_path / "history"
    history.mkdir()
    pd.DataFrame(
        [
            {"geography_id": "LK1101", "annual_rate_pct": 1.0, "comparison": "exact"},
            {"geography_id": "LK1102", "annual_rate_pct": -0.5, "comparison": "approximate"},
            {"geography_id": "LK1103", "annual_rate_pct": 0.2, "comparison": "exact"},
            {"geography_id": "LK1104", "annual_rate_pct": 2.0, "comparison": "approximate"},
        ]
    ).to_csv(history / "ds_comparison_2012_2024.csv", index=False)
    pd.DataFrame(
        [
            {"geography_id": "LK1101", "change_type": "unchanged", "male": 100, "female": 100},
            {"geography_id": "LK1102", "change_type": "renamed", "male": 90, "female": 100},
            {"geography_id": "LK1103", "change_type": "unchanged", "male": 95, "female": 100},
            {"geography_id": "LK-ADM3-V2012-11-04", "change_type": "split", "male": 1, "female": 1},
        ]
    ).to_csv(history / "ds_2012_units.csv", index=False)
    wide = pd.DataFrame(
        {"sex_ratio": [102.0, 91.0, 95.0, 99.0]}, index=["LK1101", "LK1102", "LK1103", "LK1104"]
    )
    summary = sp.build_trajectory(history, wide, tmp_path)
    data = json.loads((tmp_path / "trajectory.json").read_text())
    assert data["ids"] == ["LK1101", "LK1102", "LK1103"]
    assert data["status"] == "local_build_not_in_release"
    assert data["comparison"] == ["exact", "approximate", "exact"]
    assert data["raw"][0] == [1.0, 2.0]  # sex ratio 100 -> 102
    assert [e["id"] for e in data["excluded"]] == ["LK1104"]
    assert summary["approximate_in_space"] == 1
    z = np.array(data["vectors"])
    assert np.allclose(z.mean(axis=0), 0, atol=1e-6) and np.allclose(z.std(axis=0), 1, atol=1e-5)


@pytest.mark.parametrize(
    ("raw", "folded"),
    [
        ("Thoppur", "topur"),
        ("Kotte  (East)", "kote east"),
        ("Wellawatta", "veləvata".replace("ə", "a")),
        ("  කොළඹ ", "කොළඹ"),
        ("Pérez", "perez"),
    ],
)
def test_normalise_matches_the_website_rules(raw: str, folded: str) -> None:
    assert sp.normalise(raw) == folded


def test_text_space_finds_misspelt_and_sinhala_names() -> None:
    admin = [
        {"geography_id": "LK11", "level": 2, "name_en": "Colombo", "name_si": "කොළඹ"},
        {"geography_id": "LK12", "level": 2, "name_en": "Gampaha", "name_si": "ගම්පහ"},
        {"geography_id": "LK1103", "level": 3, "name_en": "Colombo North", "name_si": None},
        {"geography_id": "LK13", "level": 2, "name_en": "Kalutara", "name_ta": "களுத்துறை"},
    ]
    index = sp.build_text_index(admin)
    assert index.n_docs == 7
    top = sp.text_search(index, "Colmbo")
    assert top[0][0] == "LK11" and top[1][0] == "LK1103"
    assert sp.text_search(index, "කොළඹ")[0] == ("LK11", 1.0)
    assert sp.text_search(index, "களுத்துறை")[0][0] == "LK13"
    assert sp.text_search(index, "   ") == []
    assert sp.typo("Gampaha") == "Gamaha"
