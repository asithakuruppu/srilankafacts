"""Profile vector space (A03 steps 2-6, D-025, D-029)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from slf import profile

REPO = Path(__file__).resolve().parents[2]


def _wide(n: int = 300, seed: int = 1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    total = rng.integers(200, 20000, n).astype(float)
    young = rng.uniform(0.15, 0.35, n)
    old65 = rng.uniform(0.03, 0.2, n)
    old60 = rng.uniform(0.02, 0.06, n)
    units = total / rng.uniform(2.5, 5.0, n)
    female = total * rng.uniform(0.45, 0.55, n)
    frame = pd.DataFrame(
        {
            "population_total": total,
            "population_age_0_14": total * young,
            "population_age_60_64": total * old60,
            "population_age_65_plus": total * old65,
            "population_female": female,
            "population_male": total - female,
            "sex_ratio": (total - female) / female * 100,
            "occupied_housing_units": units,
            "population_density": rng.lognormal(6, 1.5, n),
        },
        index=[f"LK{i:07d}" for i in range(n)],
    )
    frame["population_age_15_59"] = total - frame[
        ["population_age_0_14", "population_age_60_64", "population_age_65_plus"]
    ].sum(axis=1)
    frame["persons_per_occupied_housing_unit"] = total / units
    return frame


def test_decomposition_is_exact_for_100_random_pairs():
    x, _ = profile.prepare(_wide(), list(_wide().index))
    f = profile.fit(x)
    assert f.retained
    rng = np.random.default_rng(0)
    for _ in range(100):
        a, b = (int(v) for v in rng.choice(len(f.ids), 2, replace=False))
        d2, axis, ind = profile.decompose(f, a, b)
        direct = float(((f.scores[a] - f.scores[b]) ** 2).sum())
        assert d2 == pytest.approx(direct, abs=1e-12)
        assert axis.sum() == pytest.approx(direct, abs=1e-12)
        assert ind.sum() == pytest.approx(direct, abs=1e-12)


def test_block_weighting_fixes_total_variance_so_eigenvalue_one_rule_is_unusable():
    x, _ = profile.prepare(_wide(), list(_wide().index))
    f = profile.fit(x)
    # Each block carries variance 1, so eigenvalues sum to 2 (less any clipping) and an
    # eigenvalue > 1 needs one axis to hold over half of everything: D-029's reason.
    assert f.eigenvalues.sum() == pytest.approx(2.0, abs=0.05)
    assert f.threshold == pytest.approx(f.eigenvalues.sum() / 9)
    # Age shares sum to 100 and persons per unit = population / units: two exact redundancies.
    assert (f.eigenvalues < 1e-12).sum() == 2


def test_excluded_places_are_listed_with_reasons():
    wide = _wide(50)
    wide.loc["LK0000001", "population_total"] = 40.0
    wide.loc["LK0000002", "population_female"] = 0.0
    wide.loc["LK0000003", "sex_ratio"] = np.nan
    universe = [*wide.index, "LK9999999"]
    x, excluded = profile.prepare(wide, universe)
    reasons = dict(zip(excluded["geography_id"], excluded["reason"], strict=True))
    assert reasons["LK0000001"] == "population below 100"
    assert reasons["LK0000002"] == "no females (sex ratio undefined)"
    assert reasons["LK0000003"].startswith("missing input: sex_ratio")
    assert reasons["LK9999999"] == "no census row"
    assert len(x) + len(excluded) == len(universe)
    assert not set(x.index) & set(reasons)


def test_nearest_excludes_self_and_is_sorted():
    x, _ = profile.prepare(_wide(), list(_wide().index))
    f = profile.fit(x)
    idx, dist = profile.nearest(f, k=10, chunk=37)
    assert idx.shape == (len(f.ids), 10)
    assert not (idx == np.arange(len(f.ids))[:, None]).any()
    assert (np.diff(dist, axis=1) >= -1e-12).all()
    brute = np.sqrt(((f.scores[5] - f.scores) ** 2).sum(axis=1))
    brute[5] = np.inf
    assert set(idx[5]) == set(np.argsort(brute)[:10])


def test_overlap_of_identical_lists_is_one():
    a = np.array([[1, 2, 3], [4, 5, 6]])
    assert profile.overlap(a, a).tolist() == [1.0, 1.0]
    assert profile.overlap(a, np.array([[1, 9, 8], [7, 8, 9]])).tolist() == pytest.approx(
        [1 / 3, 0.0]
    )


def test_committed_space_matches_the_coded_recipe():
    space = profile.load_space(REPO / "catalog")
    assert space.version == profile.SPACE_VERSION
    assert "ethnicity" in space.excludes and "religion" in space.excludes


def test_space_version_mismatch_is_refused(tmp_path: Path):
    (tmp_path / "spaces").mkdir()
    text = (REPO / "catalog" / "spaces" / "profile.yaml").read_text(encoding="utf-8")
    (tmp_path / "spaces" / "profile.yaml").write_text(
        text.replace('version: "0.2"', 'version: "0.1"'), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="version"):
        profile.load_space(tmp_path)


def test_project_reproduces_the_fitted_rows():
    x, _ = profile.prepare(_wide(), list(_wide().index))
    f = profile.fit(x)
    assert np.allclose(profile.project(f, x), f.z, atol=1e-12)


def test_count_noise_keeps_derived_values_consistent():
    wide = _wide(100)
    noisy = profile.perturb_counts(wide, np.random.default_rng(3))
    ages = noisy[profile.AGE_COUNTS].sum(axis=1)
    assert np.allclose(noisy["population_total"], ages)
    assert np.allclose(
        noisy["persons_per_occupied_housing_unit"],
        noisy["population_total"] / noisy["occupied_housing_units"],
    )
    area = wide["population_total"] / wide["population_density"]
    assert np.allclose(noisy["population_total"] / noisy["population_density"], area)
    assert not noisy[profile.AGE_COUNTS].equals(wide[profile.AGE_COUNTS])


def test_stability_report_has_every_check():
    wide = _wide(200)
    x, _ = profile.prepare(wide, list(wide.index))
    f = profile.fit(x)
    idx, dist = profile.nearest(f, k=10)
    st = profile.stability(wide, x, f, idx, dist)
    assert st["chance_overlap"] == pytest.approx(10 / 199, abs=1e-4)
    boot = st["bootstrap"]
    noise = st["count_noise"]
    assert isinstance(boot, dict) and isinstance(noise, dict)
    assert 0 <= boot["min_overlap"] <= boot["mean_overlap"] <= 1
    assert 0 <= noise["mean_overlap"] <= 1
    assert sum(b["places"] for b in noise["by_population"]) == len(f.ids)
