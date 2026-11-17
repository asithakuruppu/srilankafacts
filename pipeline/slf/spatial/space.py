"""The `landscape` space v0.1: places as points in a space of physical character.

Built from the landscape observations exactly as the `profile` space is built from the census
(same standardisation, block weighting and PCA: :func:`slf.profile.fit`), so a distance here
decomposes exactly into named indicators too. The recipe is a proposal (D-045) until the lead
approves it; nothing here is published.

It also answers the two-space questions of vector-space-model.md §6: which places share a
landscape but differ in who lives there, and the reverse.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from slf import profile

SPACE_ID = "landscape"
SPACE_VERSION = "0.1"
K = 10
RETAIN_VARIANCE = 0.85
MAX_AXES = 6

BLOCKS: dict[str, list[str]] = {
    "terrain": ["elevation", "slope"],
    "cover": ["tree", "cropland", "grassland", "built_up", "water"],
    "change": ["built_up_growth", "tree_cover_loss"],
}

INPUTS: dict[str, tuple[str, str]] = {
    "elevation": ("elevation_mean 2013", "log10(1 + metres), negative means set to 0"),
    "slope": ("slope_mean 2013", "square root of degrees"),
    "tree": ("land_cover_tree_share 2021", "square root of percent"),
    "cropland": ("land_cover_cropland_share 2021", "square root of percent"),
    "grassland": ("land_cover_grassland_share 2021", "square root of percent"),
    "built_up": ("land_cover_built_up_share 2021", "square root of percent"),
    "water": ("surface_water_ever_share 2021", "square root of percent"),
    "built_up_growth": (
        "built_up_surface_share 2020 minus 1975",
        "square root of percentage points, negative differences set to 0",
    ),
    "tree_cover_loss": (
        "tree_cover_loss_total_area 2024 / forest_measured_area 2000",
        "square root of percent of the place's area",
    ),
}


def inputs(observations: pd.DataFrame) -> pd.DataFrame:
    """One row per place with the transformed inputs of the recipe."""

    def col(indicator: str, period: str) -> pd.Series:
        rows = observations[
            (observations.indicator_id == indicator) & (observations.period == period)
        ]
        return rows.set_index("geography_id").value

    raw = pd.DataFrame(
        {
            "elevation": np.log10(1 + col("elevation_mean", "2013").clip(lower=0)),
            "slope": np.sqrt(col("slope_mean", "2013")),
            "tree": np.sqrt(col("land_cover_tree_share", "2021")),
            "cropland": np.sqrt(col("land_cover_cropland_share", "2021")),
            "grassland": np.sqrt(col("land_cover_grassland_share", "2021")),
            "built_up": np.sqrt(col("land_cover_built_up_share", "2021")),
            "water": np.sqrt(col("surface_water_ever_share", "2021")),
            "built_up_growth": np.sqrt(
                (
                    col("built_up_surface_share", "2020") - col("built_up_surface_share", "1975")
                ).clip(lower=0)
            ),
            "tree_cover_loss": np.sqrt(
                100
                * col("tree_cover_loss_total_area", "2024")
                / col("forest_measured_area", "2000")
            ),
        }
    )
    return raw


def _explain(f: profile.Fit, a: int, b: int) -> list[list[Any]]:
    _, _, indicator = profile.decompose(f, a, b)
    order = np.argsort(-indicator)[:3]
    return [[f.columns[i], round(float(indicator[i]), 4)] for i in order]


def build(
    observations: pd.DataFrame, geographies: pd.DataFrame, out_dir: Path, profile_dir: Path | None
) -> dict[str, Any]:
    raw = inputs(observations)
    names = geographies.set_index("geography_id").name_en.to_dict()
    level_of = geographies.set_index("geography_id").level.to_dict()
    vectors_dir = out_dir / "vectors"
    vectors_dir.mkdir(parents=True, exist_ok=True)
    vector_rows: list[dict[str, Any]] = []
    axis_rows: list[dict[str, Any]] = []
    summary: dict[str, Any] = {"space_id": SPACE_ID, "space_version": SPACE_VERSION, "levels": {}}
    fits: dict[str, profile.Fit] = {}
    for level, label in ((4, "gn"), (3, "ds")):
        ids = sorted(g for g in raw.index if level_of.get(g) == level)
        x = raw.loc[ids]
        complete = x[np.isfinite(x.to_numpy()).all(axis=1)]
        excluded = sorted(set(ids) - set(complete.index))
        f = profile.fit(complete, BLOCKS)
        d029_retained = len(f.retained)
        # D-029's rule (eigenvalue above the mean and three loadings of 0.3 or more) keeps one
        # axis at DS level here, which collapses the space to "highland or lowland". This recipe
        # keeps the fewest axes that explain RETAIN_VARIANCE of the variance, at most MAX_AXES.
        cumulative = np.cumsum(f.eigenvalues / f.eigenvalues.sum())
        f.retained = list(
            range(min(int(np.searchsorted(cumulative, RETAIN_VARIANCE) + 1), MAX_AXES))
        )
        fits[label] = f
        scores = f.scores
        norms = np.sqrt((scores**2).sum(axis=1))
        for gid, vec, norm in zip(f.ids, scores, norms, strict=True):
            vector_rows.append(
                {
                    "entity_type": "place",
                    "entity_id": gid,
                    "level": label,
                    "period": "2021",
                    "space_id": SPACE_ID,
                    "space_version": SPACE_VERSION,
                    "vector": vec.astype(np.float32),
                    "norm": float(norm),
                }
            )
        share = f.eigenvalues / f.eigenvalues.sum()
        for j in range(len(f.eigenvalues)):
            load = f.loadings[:, j]
            order = np.argsort(-np.abs(load))[:3]
            draft = ", ".join(f"{'+' if load[i] > 0 else '-'}{f.columns[i]}" for i in order)
            for i, column in enumerate(f.columns):
                axis_rows.append(
                    {
                        "level": label,
                        "axis": j + 1,
                        "eigenvalue": float(f.eigenvalues[j]),
                        "variance_explained": float(share[j]),
                        "retained": j in f.retained,
                        "indicator_id": column,
                        "loading": float(load[i]),
                        "draft_label": draft,
                        "label_status": "machine_generated_draft",
                        "space_id": SPACE_ID,
                        "space_version": SPACE_VERSION,
                    }
                )
        idx, dist = profile.nearest_scores(scores, K)
        similar = {
            "space_id": SPACE_ID,
            "space_version": SPACE_VERSION,
            "level": label,
            "metric": "euclidean",
            "k": K,
            "axes_retained": len(f.retained),
            "inputs": f.columns,
            "places": {
                f.ids[a]: [
                    [f.ids[int(b)], round(float(d), 4), _explain(f, a, int(b))]
                    for b, d in zip(idx[a], dist[a], strict=True)
                ]
                for a in (range(len(f.ids)) if label == "ds" else [])
            },
        }
        if label == "gn":
            # GN lists are large; store neighbour ids and distances only
            similar["places"] = {
                f.ids[a]: [
                    [f.ids[int(b)], round(float(d), 4)]
                    for b, d in zip(idx[a], dist[a], strict=True)
                ]
                for a in range(len(f.ids))
            }
        (vectors_dir / f"similar_{label}.json").write_text(json.dumps(similar) + "\n")
        unusual: Any = pd.DataFrame(
            {"geography_id": f.ids, "name_en": [names.get(g) for g in f.ids], "norm": norms}
        )
        unusual["percentile"] = unusual.norm.rank(pct=True).round(4)
        unusual.sort_values("norm", ascending=False).to_parquet(
            vectors_dir / f"unusual_{label}.parquet", index=False
        )
        summary["levels"][label] = {
            "places": len(f.ids),
            "excluded": excluded,
            "axes_retained": len(f.retained),
            "axes_retained_under_d029_rule": d029_retained,
            "variance_explained_retained": round(float(share[f.retained].sum()), 4),
            "threshold": round(f.threshold, 4),
            "clipped": {k: v for k, v in f.clipped.items() if v},
            "axes": [
                {
                    "axis": j + 1,
                    "variance_explained": round(float(share[j]), 4),
                    "loadings": {
                        c: round(float(v), 3)
                        for c, v in zip(f.columns, f.loadings[:, j], strict=True)
                    },
                }
                for j in f.retained
            ],
            "most_unusual": unusual.sort_values("norm", ascending=False)
            .head(10)[["geography_id", "name_en", "norm"]]
            .round(3)
            .to_dict("records"),
        }
    pd.DataFrame(vector_rows).to_parquet(
        vectors_dir / f"{SPACE_ID}_v{SPACE_VERSION}.parquet", index=False
    )
    pd.DataFrame(axis_rows).to_parquet(
        vectors_dir / f"{SPACE_ID}_v{SPACE_VERSION}_axes.parquet", index=False
    )

    if profile_dir is not None and (profile_dir / "vectors").exists():
        summary["cross_space_ds"] = cross_space(fits["ds"], profile_dir, names, vectors_dir)
    (vectors_dir / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    return summary


def cross_space(
    f: profile.Fit, profile_dir: Path, names: dict[str, str], out: Path
) -> dict[str, Any]:
    """DS pairs that are close in one space and far in the other (rank-based, both versions named)."""
    files = sorted((profile_dir / "vectors").glob("profile_v*.parquet"))
    files = [p for p in files if not p.name.endswith("_axes.parquet")]
    vectors = pd.read_parquet(files[-1])
    ds = vectors[(vectors.entity_type == "place") & (vectors.level == "ds")].set_index("entity_id")
    version = str(ds.space_version.iloc[0])
    common = [g for g in f.ids if g in ds.index]
    rows = [f.ids.index(g) for g in common]
    land = f.scores[rows]
    prof = np.stack(ds.loc[common, "vector"].to_numpy())

    def distances(m: np.ndarray) -> np.ndarray:
        sq = (m**2).sum(axis=1)
        return np.sqrt(np.maximum(sq[:, None] + sq[None, :] - 2 * m @ m.T, 0))

    d_land, d_prof = distances(land), distances(prof)
    iu = np.triu_indices(len(common), 1)
    rank_land = pd.Series(d_land[iu]).rank(pct=True).to_numpy()
    rank_prof = pd.Series(d_prof[iu]).rank(pct=True).to_numpy()
    table = pd.DataFrame(
        {
            "a": [common[i] for i in iu[0]],
            "b": [common[j] for j in iu[1]],
            "landscape_distance": d_land[iu],
            "profile_distance": d_prof[iu],
            "landscape_rank": rank_land,
            "profile_rank": rank_prof,
        }
    )
    table["a_name"] = table.a.map(names)
    table["b_name"] = table.b.map(names)
    table["space_versions"] = f"{SPACE_ID} {SPACE_VERSION}; profile {version}"
    same_land: Any = table.sort_values("landscape_rank").head(len(table) // 100)
    same_land = same_land.sort_values("profile_rank", ascending=False).head(25)
    same_people: Any = table.sort_values("profile_rank").head(len(table) // 100)
    same_people = same_people.sort_values("landscape_rank", ascending=False).head(25)
    same_land.to_csv(out / "cross_space_ds_same_landscape_different_profile.csv", index=False)
    same_people.to_csv(out / "cross_space_ds_same_profile_different_landscape.csv", index=False)
    corr = float(np.corrcoef(rank_land, rank_prof)[0, 1])
    cols = ["a", "a_name", "b", "b_name", "landscape_distance", "profile_distance"]
    return {
        "profile_version": version,
        "ds_in_both": len(common),
        "pairs": len(table),
        "rank_correlation_of_distances": round(corr, 4),
        "same_landscape_different_profile": same_land[cols].head(8).round(3).to_dict("records"),
        "same_profile_different_landscape": same_people[cols].head(8).round(3).to_dict("records"),
    }
