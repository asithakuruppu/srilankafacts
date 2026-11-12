"""Experiment for D-031 option (c): GN similar-place lists from smoothed values.

D-031 withholds GN similar-place lists because only 13% of a GN's top-20 list survives ordinary
small-number variation (Poisson redraw of every count). This module tests whether empirical
Bayes smoothing of the noisy shares, using the same beta-binomial and gamma-Poisson estimators as
the census spatial context (`slf.enrich`), makes the lists stable enough to publish.

Bar, set before the run: mean top-20 overlap of at least 0.70 under the same count-noise test
(DS lists reach 0.84 on raw values).

Variants:
- `raw`: profile inputs as published (the D-031 baseline);
- `eb_national`: age shares, sex ratio and persons per unit shrunk towards the national rate;
- `eb_ds`: the same, shrunk towards the GN's own DS division (national prior where a DS has
  fewer than `MIN_GROUP` GNs);
- `eb_ds_within_district`: `eb_ds`, with neighbours drawn only from the same district.

Population, housing units and density are not smoothed: they are counts or count-based, and
their relative noise is small on the log scale used by the space.

This is research output, not a release input: nothing here changes what is published.
"""

from __future__ import annotations

import dataclasses
from typing import Any

import numpy as np
import pandas as pd

from slf import profile
from slf.enrich import _empirical_bayes_beta, _empirical_bayes_gamma  # pyright: ignore[reportPrivateUsage]

K = profile.TOP_K
NOISE_RUNS = 5
SEED = profile.SEED
BAR = 0.70
MIN_GROUP = 5
POPULATION_BANDS: list[tuple[int, int | None]] = [
    (100, 1000),
    (1000, 2000),
    (2000, 5000),
    (5000, None),
]
NOISE_COUNTS = [
    *profile.AGE_COUNTS,
    "population_male",
    "population_female",
    "occupied_housing_units",
]
VARIANTS = ["raw", "eb_national", "eb_ds", "eb_ds_within_district"]


def perturb_counts(wide: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Poisson redraw of every count, as in the D-031 stability test (PR 14, `profile.py`)."""
    w = wide.copy()
    for col in NOISE_COUNTS:
        w[col] = rng.poisson(w[col].fillna(0).clip(lower=0).to_numpy()).astype(float)
    w["population_total"] = w[profile.AGE_COUNTS].sum(axis=1)
    w["sex_ratio"] = w["population_male"] / w["population_female"] * 100
    w["persons_per_occupied_housing_unit"] = w["population_total"] / w["occupied_housing_units"]
    w["population_density"] = (
        wide["population_density"] * w["population_total"] / wide["population_total"]
    )
    return w


def _shrink(wide: pd.DataFrame) -> pd.DataFrame:
    """Empirical Bayes on one group of places; returns smoothed age counts, sex ratio and ppu."""
    out = wide.copy()
    total = wide["population_total"].to_numpy(dtype=float)
    shares = []
    for col in profile.AGE_COUNTS:
        s, _ = _empirical_bayes_beta(wide[col].to_numpy(dtype=float), total)
        shares.append(s)
    share = np.vstack(shares).T
    share = share / share.sum(axis=1, keepdims=True)  # the four shares sum to 1 again
    for j, col in enumerate(profile.AGE_COUNTS):
        out[col] = share[:, j] * total
    male = wide["population_male"].to_numpy(dtype=float)
    female = wide["population_female"].to_numpy(dtype=float)
    m_share, _ = _empirical_bayes_beta(male, male + female)
    m_share = np.clip(m_share, 1e-9, 1 - 1e-9)
    out["sex_ratio"] = 100 * m_share / (1 - m_share)
    ppu, _ = _empirical_bayes_gamma(total, wide["occupied_housing_units"].to_numpy(dtype=float))
    out["persons_per_occupied_housing_unit"] = ppu
    return out


def smooth(wide: pd.DataFrame, prior: str) -> pd.DataFrame:
    """Smooth GN rows towards the national rate (`national`) or their DS division (`ds`)."""
    if prior == "national":
        return _shrink(wide)
    national = _shrink(wide)
    parts = []
    for _, group in wide.groupby(wide.index.str[:6], sort=False):
        parts.append(_shrink(group) if len(group) >= MIN_GROUP else national.loc[group.index])
    out = pd.concat(parts).loc[wide.index]
    bad = ~np.isfinite(out[["sex_ratio", "persons_per_occupied_housing_unit"]]).all(axis=1)
    out.loc[bad] = national.loc[bad]
    return out


def _inputs(wide: pd.DataFrame, variant: str) -> pd.DataFrame:
    if variant == "raw":
        return wide
    return smooth(wide, "national" if variant == "eb_national" else "ds")


@dataclasses.dataclass
class Standardiser:
    """The standardisation `profile.fit` applies, kept so noisy rows can be projected the same way
    (the same as `profile.project` in PR 14, which is not on main yet)."""

    columns: list[str]
    mean: np.ndarray
    sd: np.ndarray
    weights: np.ndarray
    centre: np.ndarray

    @classmethod
    def of(cls, x: pd.DataFrame, blocks: dict[str, list[str]] = profile.BLOCKS) -> Standardiser:
        columns = [c for block in blocks.values() for c in block]
        raw = x[columns].to_numpy(dtype=float)
        mean, sd = raw.mean(axis=0), raw.std(axis=0)
        weights = np.concatenate([np.full(len(b), 1 / np.sqrt(len(b))) for b in blocks.values()])
        z = np.clip((raw - mean) / sd, -profile.WINSOR_SD, profile.WINSOR_SD) * weights
        return cls(columns, mean, sd, weights, z.mean(axis=0))

    def project(self, x: pd.DataFrame) -> np.ndarray:
        raw = x[self.columns].to_numpy(dtype=float)
        z = np.clip((raw - self.mean) / self.sd, -profile.WINSOR_SD, profile.WINSOR_SD)
        return z * self.weights - self.centre


def _knn(f: profile.Fit, z: np.ndarray, groups: np.ndarray | None) -> np.ndarray:
    """Top-K neighbours from standardised rows `z`; optionally only within the same group."""
    if groups is None:
        idx, _ = profile.nearest(dataclasses.replace(f, z=z), K)
        return idx
    idx = np.full((len(z), K), -1, dtype=np.int64)
    for g in np.unique(groups):
        rows = np.flatnonzero(groups == g)
        if len(rows) <= K:
            continue
        sub = dataclasses.replace(f, z=z[rows], ids=[f.ids[i] for i in rows])
        local, _ = profile.nearest(sub, K)
        idx[rows] = rows[local]
    return idx


# Exploratory (not part of the pre-set test): the space without persons per housing unit, the
# input that carries most of the count noise.
WITHOUT_PPU: dict[str, list[str]] = {
    "demography": profile.BLOCKS["demography"],
    "housing": ["occupied_housing_units", "population_density"],
}


def run_variant(
    wide: pd.DataFrame, variant: str, blocks: dict[str, list[str]] = profile.BLOCKS
) -> dict[str, Any]:
    gn = wide.loc[wide.index.str.len() == 9]
    x, excluded = profile.prepare(_inputs(gn, variant), list(gn.index))
    f = profile.fit(x, blocks)
    std = Standardiser.of(x, blocks)
    if not np.allclose(std.project(x), f.z, atol=1e-9):
        raise AssertionError("local standardiser does not reproduce profile.fit")
    if not f.retained:
        return {"variant": variant, "axes": 0, "note": "no axes retained"}
    within = variant.endswith("within_district")
    groups = np.array([i[:4] for i in f.ids]) if within else None
    idx = _knn(f, f.z, groups)
    valid = (idx >= 0).all(axis=1)
    rng = np.random.default_rng(SEED)
    overlaps, shifts = [], []
    for _ in range(NOISE_RUNS):
        noisy = _inputs(perturb_counts(gn, rng), variant).loc[f.ids]
        zp = std.project(profile.transform(noisy))
        bad = ~np.isfinite(zp).all(axis=1)
        zp[bad] = f.z[bad]
        ip = _knn(f, zp, groups)
        overlaps.append(profile.overlap(idx[valid], ip[valid]))
        shifts.append(np.linalg.norm((zp - f.z) @ f.basis, axis=1))
    ov = np.mean(overlaps, axis=0)
    pop = gn.loc[np.array(f.ids)[valid], "population_total"].to_numpy(dtype=float)
    bands = []
    for lo, hi in POPULATION_BANDS:
        m = (pop >= lo) & (pop < (hi if hi is not None else np.inf))
        bands.append(
            {
                "population": f"{lo:,}+" if hi is None else f"{lo:,}-{hi - 1:,}",
                "places": int(m.sum()),
                "mean_overlap": round(float(ov[m].mean()), 3) if m.any() else None,
            }
        )
    if groups is None:
        chance = K / (len(f.ids) - 1)
    else:
        sizes = pd.Series(groups[valid]).map(pd.Series(groups).value_counts()).to_numpy()
        chance = float(np.mean(K / (sizes - 1)))
    _, dist = profile.nearest(dataclasses.replace(f, z=f.z), K)
    return {
        "variant": variant,
        "places": int(valid.sum()),
        "excluded": len(excluded),
        "axes": len(f.retained),
        "variance_explained": round(
            float(f.eigenvalues[f.retained].sum() / f.eigenvalues.sum()), 3
        ),
        "mean_overlap": round(float(ov.mean()), 3),
        "passes_bar": bool(ov.mean() >= BAR),
        "chance_overlap": round(chance, 4),
        "median_shift": round(float(np.median(np.mean(shifts, axis=0))), 4),
        "median_distance_20th": round(float(np.median(dist[:, -1])), 4),
        "by_population": bands,
        "_idx": idx,
        "_ids": f.ids,
    }


def run(observations: pd.DataFrame, exploratory: bool = True) -> list[dict[str, Any]]:
    wide = profile.census_wide(observations)
    results = [run_variant(wide, v) for v in VARIANTS]
    if exploratory:
        for v in ("raw", "eb_ds_within_district"):
            r = run_variant(wide, v, WITHOUT_PPU)
            r["variant"] = f"{v} without persons per unit (exploratory)"
            results.append(r)
    base = results[0]
    pos = {g: i for i, g in enumerate(base["_ids"])}
    for r in results:
        common = [i for i, g in enumerate(r["_ids"]) if g in pos]
        a = np.array(
            [
                [pos.get(r["_ids"][j], -1) if j >= 0 else -1 for j in row]
                for row in r["_idx"][common]
            ]
        )
        b = base["_idx"][[pos[r["_ids"][i]] for i in common]]
        r["overlap_with_raw_lists"] = round(float(profile.overlap(a, b).mean()), 3)
    for r in results:
        r.pop("_idx")
        r.pop("_ids")
    return results


def render(results: list[dict[str, Any]]) -> str:
    lines = [
        "| Variant | Places | Axes | Mean overlap under count noise | Passes 0.70 | Chance | "
        "Median shift | Median distance to 20th | Same list as raw |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        if r.get("axes", 0) == 0:
            lines.append(f"| `{r['variant']}` | n/a | 0 | {r.get('note', '')} | | | | | |")
            continue
        lines.append(
            f"| `{r['variant']}` | {r['places']:,} | {r['axes']} | **{r['mean_overlap']:.3f}** | "
            f"{'yes' if r['passes_bar'] else 'no'} | {r['chance_overlap']:.4f} | "
            f"{r['median_shift']:.3f} | {r['median_distance_20th']:.3f} | "
            f"{r['overlap_with_raw_lists']:.3f} |"
        )
    lines += [
        "",
        "| Variant | " + " | ".join(b["population"] for b in results[0]["by_population"]) + " |",
    ]
    lines.append("|---|" + "---|" * len(results[0]["by_population"]))
    for r in results:
        if r.get("axes", 0) == 0:
            continue
        cells = [f"{b['mean_overlap']:.3f} ({b['places']:,})" for b in r["by_population"]]
        lines.append(f"| `{r['variant']}` | " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"
