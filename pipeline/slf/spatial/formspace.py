"""The `form` and `context` spaces v0.1: places by built form and by surroundings.

Both are built exactly like `profile` and `landscape` (same standardisation, block weighting
and PCA: :func:`slf.profile.fit`), so a distance decomposes exactly into named indicators that
resolve to ledger values (AGENTS rule 13). They describe **places** (GN and DS divisions) from
aggregates only: no per-building vector is built or published, and no census value is attached to
a building (rule 11).

- ``form``: how a place is built: density and coverage of mapped footprints, footprint size and
  shape, and the modelled height of its built-up cells.
- ``context``: what surrounds a settlement there: tree canopy, biomass, open land and water, and
  how many listed places (shops, services) are around.

Rights: ``form`` is derived from Overture Buildings (ODbL, share-alike) and stays internal until the
D-005 / multi-scale-features §6 question is settled. ``context`` uses CC BY and CDLA-Permissive
sources only, but nothing is published until the lead approves the recipes (D-045 pattern).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from slf import profile

K = 10
RETAIN_VARIANCE = 0.85
MAX_AXES = 6
EXPLAIN_TOP = 3


@dataclass(frozen=True)
class SpaceSpec:
    space_id: str
    version: str
    blocks: dict[str, list[str]]
    # input name -> (ledger indicator and period, transformation in words)
    inputs: dict[str, tuple[str, str]]
    derive: Callable[[pd.DataFrame], pd.DataFrame]
    period: str  # the time footprint recorded on the vectors


def _col(obs: pd.DataFrame, indicator: str, period: str) -> pd.Series:
    rows = obs[(obs.indicator_id == indicator) & (obs.period == period)]
    return rows.set_index("geography_id").value.astype(float)


def _where_positive(series: pd.Series) -> pd.Series:
    return series.where(series >= 0)


def derive_form(obs: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "density": np.log10(1 + _where_positive(_col(obs, "buildings_per_km2", "2026"))),
            "coverage": np.sqrt(_where_positive(_col(obs, "building_coverage_share", "2026"))),
            "footprint": np.log10(
                _col(obs, "building_footprint_mean", "2026").where(lambda s: s > 0)
            ),
            "large": np.sqrt(_where_positive(_col(obs, "buildings_large_share", "2026"))),
            "small": np.sqrt(_where_positive(_col(obs, "buildings_small_share", "2026"))),
            "compactness": _col(obs, "building_compactness_mean", "2026"),
            "height": np.log10(_col(obs, "building_height_mean", "2018").where(lambda s: s > 0)),
        }
    )


def derive_context(obs: pd.DataFrame) -> pd.DataFrame:
    land_km2 = _col(obs, "land_cover_mapped_area", "2021") / 100.0
    listed = _col(obs, "places_listed", "2026")
    return pd.DataFrame(
        {
            "canopy_height": _col(obs, "canopy_height_mean", "2026"),
            "canopy_tall": np.sqrt(_col(obs, "canopy_15m_share", "2026")),
            "biomass": np.sqrt(_col(obs, "biomass_agb_mean", "2025")),
            "cropland": np.sqrt(_col(obs, "land_cover_cropland_share", "2021")),
            "grassland": np.sqrt(_col(obs, "land_cover_grassland_share", "2021")),
            "water": np.sqrt(_col(obs, "land_cover_water_share", "2021")),
            "services": np.log10(1 + listed / land_km2.where(land_km2 > 0)),
        }
    )


FORM = SpaceSpec(
    "form",
    "0.1",
    {
        "intensity": ["density", "coverage", "height"],
        "character": ["footprint", "large", "small", "compactness"],
    },
    {
        "density": ("buildings_per_km2 2026", "log10(1 + footprints per km2)"),
        "coverage": ("building_coverage_share 2026", "square root of percent"),
        "footprint": ("building_footprint_mean 2026", "log10(square metres)"),
        "large": ("buildings_large_share 2026", "square root of percent"),
        "small": ("buildings_small_share 2026", "square root of percent"),
        "compactness": ("building_compactness_mean 2026", "none (index 0 to 1)"),
        "height": ("building_height_mean 2018", "log10(metres)"),
    },
    derive_form,
    "2026",
)

CONTEXT = SpaceSpec(
    "context",
    "0.1",
    {
        "vegetation": ["canopy_height", "canopy_tall", "biomass"],
        "land_and_services": ["cropland", "grassland", "water", "services"],
    },
    {
        "canopy_height": ("canopy_height_mean 2026", "none (metres)"),
        "canopy_tall": ("canopy_15m_share 2026", "square root of percent"),
        "biomass": ("biomass_agb_mean 2025", "square root of megagrams per hectare"),
        "cropland": ("land_cover_cropland_share 2021", "square root of percent"),
        "grassland": ("land_cover_grassland_share 2021", "square root of percent"),
        "water": ("land_cover_water_share 2021", "square root of percent"),
        "services": (
            "places_listed 2026 / land_cover_mapped_area 2021",
            "log10(1 + listed places per km2)",
        ),
    },
    derive_context,
    "2026",
)

SPECS = {s.space_id: s for s in (FORM, CONTEXT)}


def _reason(row: pd.Series) -> str:
    bad = ~np.isfinite(row.to_numpy(dtype=float))
    return "no value for " + ", ".join(sorted(str(c) for c in row.index[bad]))


def _explain(f: profile.Fit, a: int, b: int) -> list[list[Any]]:
    _, _, indicator = profile.decompose(f, a, b)
    order = np.argsort(-indicator)[:EXPLAIN_TOP]
    return [[f.columns[i], round(float(indicator[i]), 4)] for i in order]


def fit_level(spec: SpaceSpec, raw: pd.DataFrame, ids: list[str]) -> tuple[profile.Fit, list[dict]]:
    """Fit one level; places with any undefined input are excluded and named with the reason."""
    x = raw.reindex(ids)
    finite = np.isfinite(x.to_numpy(dtype=float)).all(axis=1)
    excluded = [{"geography_id": g, "reason": _reason(x.loc[g])} for g in x.index[~finite]]
    f = profile.fit(x.iloc[np.flatnonzero(finite)], spec.blocks)
    cumulative = np.cumsum(f.eigenvalues / f.eigenvalues.sum())
    f.retained = list(range(min(int(np.searchsorted(cumulative, RETAIN_VARIANCE) + 1), MAX_AXES)))
    return f, excluded


def checks(f: profile.Fit, district_of: dict[str, str] | None, seed: int = 20261121) -> dict:
    """Evidence that the space behaves: exact decomposition and spatial coherence of neighbours."""
    rng = np.random.default_rng(seed)
    n = len(f.ids)
    pairs = rng.integers(0, n, size=(300, 2))
    err = 0.0
    scores = f.scores
    for a, b in pairs:
        if a == b:
            continue
        sq, axis, indicator = profile.decompose(f, int(a), int(b))
        direct = float(((scores[a] - scores[b]) ** 2).sum())
        err = max(err, abs(sq - direct), abs(axis.sum() - sq), abs(indicator.sum() - sq))
    out: dict[str, Any] = {"max_abs_decomposition_error": err, "pairs_checked": 300}
    if district_of:
        idx, _ = profile.nearest_scores(scores, K)
        own = np.array([district_of.get(g, "") for g in f.ids])
        same = (own[idx] == own[:, None]).mean()
        _, counts = np.unique(own, return_counts=True)
        chance = float(((counts / counts.sum()) ** 2).sum())
        out["neighbours_in_same_district"] = round(float(same), 4)
        out["same_district_by_chance"] = round(chance, 4)
    return out


def build(
    spec: SpaceSpec,
    observations: pd.DataFrame,
    geographies: pd.DataFrame,
    out_dir: Path,
) -> dict[str, Any]:
    raw = spec.derive(observations)
    geos = geographies.set_index("geography_id")
    names = geos.name_en.to_dict()
    level_of = geos.level.to_dict()
    parent = geos.parent_id.to_dict()
    vectors_dir = out_dir / "vectors"
    vectors_dir.mkdir(parents=True, exist_ok=True)
    tag = f"{spec.space_id}_v{spec.version}"
    vector_rows: list[dict[str, Any]] = []
    axis_rows: list[dict[str, Any]] = []
    summary: dict[str, Any] = {
        "space_id": spec.space_id,
        "space_version": spec.version,
        "inputs": {k: {"ledger": v[0], "transform": v[1]} for k, v in spec.inputs.items()},
        "levels": {},
    }
    for level, label in ((4, "gn"), (3, "ds")):
        ids = sorted(g for g in raw.index if level_of.get(g) == level)
        f, excluded = fit_level(spec, raw, ids)
        norms = np.sqrt((f.scores**2).sum(axis=1))
        for gid, vec, norm in zip(f.ids, f.scores, norms, strict=True):
            vector_rows.append(
                {
                    "entity_type": "place",
                    "entity_id": gid,
                    "level": label,
                    "period": spec.period,
                    "space_id": spec.space_id,
                    "space_version": spec.version,
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
                        "input": column,
                        "ledger_input": spec.inputs[column][0],
                        "loading": float(load[i]),
                        "draft_label": draft,
                        "label_status": "machine_generated_draft",
                        "space_id": spec.space_id,
                        "space_version": spec.version,
                    }
                )
        idx, dist = profile.nearest_scores(f.scores, K)
        similar = {
            "space_id": spec.space_id,
            "space_version": spec.version,
            "level": label,
            "metric": "euclidean",
            "k": K,
            "axes_retained": len(f.retained),
            "inputs": f.columns,
            "explanation": f"top {EXPLAIN_TOP} inputs by exact contribution to squared distance",
            "places": {
                f.ids[a]: [
                    [f.ids[int(b)], round(float(d), 4), _explain(f, a, int(b))]
                    for b, d in zip(idx[a], dist[a], strict=True)
                ]
                for a in range(len(f.ids))
            },
        }
        (vectors_dir / f"similar_{label}.json").write_text(json.dumps(similar) + "\n")
        unusual: Any = pd.DataFrame(
            {"geography_id": f.ids, "name_en": [names.get(g) for g in f.ids], "norm": norms}
        )
        unusual["percentile"] = unusual.norm.rank(pct=True).round(4)
        unusual = unusual.sort_values("norm", ascending=False)
        unusual.to_parquet(vectors_dir / f"unusual_{label}.parquet", index=False)
        district = (
            {g: parent.get(parent.get(g)) or "" for g in f.ids}
            if label == "gn"
            else {g: parent.get(g) or "" for g in f.ids}
        )
        summary["levels"][label] = {
            "places": len(f.ids),
            "excluded": excluded,
            "axes_retained": len(f.retained),
            "variance_explained_retained": round(float(share[f.retained].sum()), 4),
            "clipped": {k: v for k, v in f.clipped.items() if v},
            "checks": checks(f, district),
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
            "most_unusual": unusual.head(10)[["geography_id", "name_en", "norm"]]
            .round(3)
            .to_dict("records"),
            "input_summary": {
                c: {
                    "p1": round(float(raw.loc[f.ids, c].quantile(0.01)), 3),
                    "median": round(float(raw.loc[f.ids, c].median()), 3),
                    "p99": round(float(raw.loc[f.ids, c].quantile(0.99)), 3),
                }
                for c in f.columns
            },
        }
    pd.DataFrame(vector_rows).to_parquet(vectors_dir / f"{tag}.parquet", index=False)
    pd.DataFrame(axis_rows).to_parquet(vectors_dir / f"{tag}_axes.parquet", index=False)
    (vectors_dir / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    return summary


def cross_space(
    a_dir: Path, b_dir: Path, a_tag: str, b_tag: str, level: str = "ds"
) -> dict[str, Any]:
    """Rank correlation of pairwise distances between two spaces for places in both."""

    def load(d: Path, tag: str) -> pd.DataFrame:
        v = pd.read_parquet(d / "vectors" / f"{tag}.parquet")
        return v[v.level == level].set_index("entity_id")

    a, b = load(a_dir, a_tag), load(b_dir, b_tag)
    common = sorted(set(a.index) & set(b.index))

    def distances(v: pd.DataFrame) -> np.ndarray:
        m = np.stack(v.loc[common, "vector"].to_numpy())
        sq = (m**2).sum(axis=1)
        d = np.sqrt(np.maximum(sq[:, None] + sq[None, :] - 2 * m @ m.T, 0))
        return d[np.triu_indices(len(common), 1)]

    da, db = distances(a), distances(b)
    corr = float(
        np.corrcoef(pd.Series(da).rank().to_numpy(), pd.Series(db).rank().to_numpy())[0, 1]
    )
    return {"places_in_both": len(common), "rank_correlation_of_distances": round(corr, 4)}


def render_qa(spec: SpaceSpec, summary: dict[str, Any]) -> str:
    lines = [
        f"# QA: `{spec.space_id}` space v{spec.version}",
        "",
        "Generated by `slf spatial formspace`. Every number below was computed in this run. "
        "Proposed recipe: nothing here is published.",
        "",
        "## Inputs",
        "",
        "| Input | Ledger value | Transformation |",
        "|---|---|---|",
    ]
    for name, info in summary["inputs"].items():
        lines.append(f"| {name} | {info['ledger']} | {info['transform']} |")
    for label, info in summary["levels"].items():
        c = info["checks"]
        lines += [
            "",
            f"## {label.upper()} level",
            "",
            f"- Places in the space: {info['places']:,}; excluded for an undefined input: "
            f"{len(info['excluded']):,}.",
            f"- Axes retained: {info['axes_retained']} "
            f"({info['variance_explained_retained']:.1%} of variance).",
            f"- Exact decomposition: max absolute error over {c['pairs_checked']} random pairs "
            f"{c['max_abs_decomposition_error']:.2e} (axis sums and input sums both equal the "
            "squared distance).",
            f"- Spatial coherence: {c['neighbours_in_same_district']:.1%} of each place's "
            f"{K} nearest neighbours lie in the same district; by chance it would be "
            f"{c['same_district_by_chance']:.1%}.",
            "",
            "| Input | p1 | median | p99 |",
            "|---|---:|---:|---:|",
        ]
        for column, s in info["input_summary"].items():
            lines.append(f"| {column} | {s['p1']} | {s['median']} | {s['p99']} |")
        lines += ["", "| Axis | Variance | Strongest loadings |", "|---|---:|---|"]
        for ax in info["axes"]:
            top = sorted(ax["loadings"].items(), key=lambda kv: -abs(kv[1]))[:3]
            lines.append(
                f"| {ax['axis']} | {ax['variance_explained']:.1%} | "
                + ", ".join(f"{k} {v:+.2f}" for k, v in top)
                + " |"
            )
        if info["excluded"]:
            reasons: dict[str, int] = {}
            for e in info["excluded"]:
                reasons[e["reason"]] = reasons.get(e["reason"], 0) + 1
            lines += ["", "Excluded places by reason (full list in `summary.json`):", ""]
            for reason, n in sorted(reasons.items(), key=lambda kv: -kv[1]):
                lines.append(f"- {n:,} places: {reason}")
        lines += ["", "Most unusual places (length from the national centre):", ""]
        for r in info["most_unusual"]:
            lines.append(f"- {r['name_en']} ({r['geography_id']}): {r['norm']}")
    return "\n".join(lines) + "\n"
