"""D-031 option (c) experiment helpers."""

from __future__ import annotations

import numpy as np
import pandas as pd

from slf import profile
from slf import profile_smoothing as ps
from tests.test_profile import _wide as _base


def _wide(n: int = 300) -> pd.DataFrame:
    w = _base(n)
    if "population_male" not in w:
        w["population_male"] = w["population_total"] - w["population_female"]
    return w


def test_standardiser_reproduces_profile_fit():
    x, _ = profile.prepare(_wide(), list(_wide().index))
    f = profile.fit(x)
    assert np.allclose(ps.Standardiser.of(x).project(x), f.z, atol=1e-12)


def test_smoothing_keeps_totals_and_pulls_small_places_towards_the_mean():
    wide = _wide(200)
    tiny = wide.index[0]
    wide.loc[tiny, profile.AGE_COUNTS] = [60.0, 40.0, 0.0, 0.0]  # 60% children in 100 people
    wide.loc[tiny, "population_total"] = 100.0
    out = ps.smooth(wide, "national")
    assert np.allclose(out[profile.AGE_COUNTS].sum(axis=1), wide["population_total"])
    national = wide["population_age_0_14"].sum() / wide["population_total"].sum()
    before = 0.60
    after = out.loc[tiny, "population_age_0_14"] / 100.0
    assert abs(after - national) < abs(before - national)


def test_ds_prior_falls_back_to_national_for_small_groups():
    wide = _wide(30)
    wide.index = pd.Index([f"LK11{i // 10:02d}{i:03d}" for i in range(30)])  # 3 DS x 10 GNs
    lone = wide.iloc[[0]].copy()
    lone.index = pd.Index(["LK1199001"])  # a DS with one GN
    both = pd.concat([wide, lone])
    out = ps.smooth(both, "ds")
    nat = ps.smooth(both, "national")
    assert np.allclose(out.loc["LK1199001", "sex_ratio"], nat.loc["LK1199001", "sex_ratio"])
    assert np.isfinite(out["persons_per_occupied_housing_unit"]).all()
