"""The `profile` vector space (prompt A03 steps 2-6; D-025, D-029).

Builds place and indicator coordinates from one PCA of the nine Census 2024 inputs named in
``catalog/spaces/profile.yaml``, separately at GN and DS level, then derives similar places
with an exact distance decomposition, distance from the national centre, contrasts between
bordering units, and a block-removal sensitivity check.

Everything here is derived from the ledger and machine-computed. A distance is a similarity
statement, never a fact and never a ranking (AGENTS rule 13). Nothing here changes a
published census value. The stage is deterministic: no randomness except a seeded sample for
the decomposition check, and no wall-clock values are written.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from slf.enrich import load_neighbours
from slf.schemas import VectorSpace

SPACE_ID = "profile"
SPACE_VERSION = "0.2"
PERIOD = "2024"
LEVELS = {4: "gn", 3: "ds"}

AGE_COUNTS = [
    "population_age_0_14",
    "population_age_15_59",
    "population_age_60_64",
    "population_age_65_plus",
]
BLOCKS: dict[str, list[str]] = {
    "demography": ["population_total", *AGE_COUNTS, "sex_ratio"],
    "housing": [
        "occupied_housing_units",
        "persons_per_occupied_housing_unit",
        "population_density",
    ],
}
INPUTS = [i for block in BLOCKS.values() for i in block]
INPUT_LABELS = {
    "population_total": "population (log)",
    "population_age_0_14": "share aged 0-14",
    "population_age_15_59": "share aged 15-59",
    "population_age_60_64": "share aged 60-64",
    "population_age_65_plus": "share aged 65+",
    "sex_ratio": "sex ratio (log)",
    "occupied_housing_units": "occupied housing units (log)",
    "persons_per_occupied_housing_unit": "persons per housing unit (log)",
    "population_density": "population density (log)",
}

MIN_POPULATION = 100.0  # D-026 / D-025
WINSOR_SD = 5.0
LOADING_MIN = 0.3  # D-029
MIN_LOADINGS = 3
MAX_AXES = 6
TOP_K = 20
CONTRAST_PERCENTILE = 95.0
CHECK_PAIRS = 100
SEED = 20241108
BOOTSTRAP_RUNS = 10
NOISE_RUNS = 5
WIDE_K = 200
POPULATION_BANDS = [(100, 1000), (1000, 2000), (2000, 5000), (5000, None)]
NOISE_COUNTS = [
    *AGE_COUNTS,
    "population_male",
    "population_female",
    "occupied_housing_units",
]
LABEL_STATUS = "machine_generated_draft"


# --- recipe -------------------------------------------------------------------------------


def load_space(catalog_root: Path) -> VectorSpace:
    """Load the space definition and refuse to build if it is not the recipe coded here."""
    path = catalog_root / "spaces" / f"{SPACE_ID}.yaml"
    space = VectorSpace.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))
    if space.version != SPACE_VERSION:
        raise ValueError(
            f"{path}: version {space.version!r}, but the code implements {SPACE_VERSION}"
        )
    ids = [i.id for i in space.inputs]
    if ids != INPUTS:
        raise ValueError(f"{path}: inputs {ids} differ from the coded recipe {INPUTS}")
    return space


def transform(wide: pd.DataFrame) -> pd.DataFrame:
    """Apply the recipe's transformations to one row per place of raw census values."""
    total = wide["population_total"]
    out = pd.DataFrame(index=wide.index)
    out["population_total"] = np.log10(total)
    for col in AGE_COUNTS:
        out[col] = wide[col] / total * 100.0
    out["sex_ratio"] = np.log10(wide["sex_ratio"])
    out["occupied_housing_units"] = np.log10(wide["occupied_housing_units"])
    out["persons_per_occupied_housing_unit"] = np.log10(wide["persons_per_occupied_housing_unit"])
    out["population_density"] = np.log10(wide["population_density"])
    return out.loc[:, INPUTS]


def prepare(wide: pd.DataFrame, universe: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return transformed inputs for eligible places and the excluded places with reasons.

    ``wide`` has one row per geography with raw indicator columns; ``universe`` is every spine
    unit at the level, so units without a census row are listed rather than dropped.
    """
    reasons: dict[str, str] = {}
    for gid in universe:
        if gid not in wide.index:
            reasons[gid] = "no census row"
    rows = wide.loc[[g for g in universe if g in wide.index]]
    needed = [*INPUTS, "population_female"]
    for gid, row in rows.iterrows():
        gid = str(gid)
        missing = [c for c in needed if c not in row.index or pd.isna(row[c])]
        pop = row.get("population_total")
        if pop is not None and not pd.isna(pop) and pop < MIN_POPULATION:
            reasons[gid] = f"population below {MIN_POPULATION:.0f}"
        elif missing:
            reasons[gid] = "missing input: " + ", ".join(missing)
        elif row["population_female"] <= 0:
            reasons[gid] = "no females (sex ratio undefined)"
        elif row["occupied_housing_units"] <= 0 or row["population_density"] <= 0:
            reasons[gid] = "zero housing units or density (log undefined)"
    keep = [str(g) for g in rows.index if str(g) not in reasons]
    x = transform(rows.loc[keep])
    bad = x.index[~np.isfinite(x.to_numpy()).all(axis=1)]
    for gid in bad:
        reasons[str(gid)] = "non-finite transformed value"
    x = x.drop(index=bad).sort_index()
    excluded = pd.DataFrame(sorted(reasons.items()), columns=["geography_id", "reason"])
    return x, excluded


# --- factorisation ------------------------------------------------------------------------


@dataclass
class Fit:
    ids: list[str]
    columns: list[str]
    z: np.ndarray  # centred, winsorised, block-weighted inputs (n x p)
    eigenvalues: np.ndarray  # p
    loadings: np.ndarray  # unit eigenvectors, p x p (columns are axes)
    retained: list[int]
    threshold: float
    clipped: dict[str, int] = field(default_factory=dict)
    fallback: str | None = None
    mean: np.ndarray | None = None  # standardisation parameters, kept so new rows can be
    sd: np.ndarray | None = None  # projected exactly as the fitted rows were
    weights: np.ndarray | None = None
    centre: np.ndarray | None = None

    @property
    def basis(self) -> np.ndarray:
        return self.loadings[:, self.retained]

    @property
    def scores(self) -> np.ndarray:
        return self.z @ self.basis


def fit(x: pd.DataFrame, blocks: dict[str, list[str]] = BLOCKS) -> Fit:
    """Standardise, winsorise, weight blocks equally and run PCA by SVD."""
    columns = [c for block in blocks.values() for c in block]
    raw = x[columns].to_numpy(dtype=float)
    sd = raw.std(axis=0)
    if (sd == 0).any():
        flat = [c for c, s in zip(columns, sd, strict=True) if s == 0]
        raise ValueError(f"inputs with zero variance cannot be standardised: {flat}")
    z = (raw - raw.mean(axis=0)) / sd
    clipped = {c: int(n) for c, n in zip(columns, (np.abs(z) > WINSOR_SD).sum(axis=0), strict=True)}
    z = np.clip(z, -WINSOR_SD, WINSOR_SD)
    weights = np.concatenate([np.full(len(b), 1 / np.sqrt(len(b))) for b in blocks.values()])
    z = z * weights
    centre = z.mean(axis=0)
    z = z - centre
    _, s, vt = np.linalg.svd(z, full_matrices=False)
    eig = s**2 / len(z)
    v = vt.T
    for j in range(v.shape[1]):  # deterministic sign: largest |loading| is positive
        k = int(np.argmax(np.abs(v[:, j])))
        if v[k, j] < 0:
            v[:, j] = -v[:, j]
    threshold = float(eig.sum() / len(columns))
    retained = [
        j
        for j in range(len(eig))
        if eig[j] > threshold and int((np.abs(v[:, j]) >= LOADING_MIN).sum()) >= MIN_LOADINGS
    ][:MAX_AXES]
    return Fit(
        ids=[str(i) for i in x.index],
        columns=columns,
        z=z,
        eigenvalues=eig,
        loadings=v,
        retained=retained,
        threshold=threshold,
        clipped=clipped,
        mean=raw.mean(axis=0),
        sd=sd,
        weights=weights,
        centre=centre,
    )


def project(f: Fit, x: pd.DataFrame) -> np.ndarray:
    """Standardise new rows with a fit's own parameters (same clip, weights and centre)."""
    if f.mean is None or f.sd is None or f.weights is None or f.centre is None:
        raise ValueError("fit has no standardisation parameters")
    raw = x[f.columns].to_numpy(dtype=float)
    z = np.clip((raw - f.mean) / f.sd, -WINSOR_SD, WINSOR_SD) * f.weights
    return z - f.centre


def decompose(f: Fit, a: int, b: int | None = None) -> tuple[float, np.ndarray, np.ndarray]:
    """Exact decomposition of the squared distance between places a and b (or the centre).

    Returns (squared distance, per-axis contributions, per-indicator contributions). Both
    contribution vectors sum to the squared distance. An indicator's contribution is its
    weighted standardised difference times the difference projected back from the retained
    axes, so it can be negative when an indicator pulls two places together on an axis.
    """
    dz = f.z[a] - (f.z[b] if b is not None else 0.0)
    basis = f.basis
    ds = dz @ basis
    axis = ds**2
    indicator = dz * (basis @ ds)
    return float(axis.sum()), axis, indicator


def nearest(f: Fit, k: int = TOP_K, chunk: int = 512) -> tuple[np.ndarray, np.ndarray]:
    """Top-k nearest places for every place (self excluded), ties broken by row order."""
    return nearest_scores(f.scores, k, chunk)


def nearest_scores(
    s: np.ndarray, k: int = TOP_K, chunk: int = 512
) -> tuple[np.ndarray, np.ndarray]:
    """Top-k nearest rows of a score matrix (self excluded), ties broken by row order."""
    n = len(s)
    k = min(k, n - 1)
    sq = (s**2).sum(axis=1)
    idx = np.zeros((n, k), dtype=np.int64)
    dist = np.zeros((n, k), dtype=float)
    for start in range(0, n, chunk):
        block = s[start : start + chunk]
        d2 = sq[start : start + chunk, None] + sq[None, :] - 2 * block @ s.T
        np.maximum(d2, 0, out=d2)
        rows = np.arange(len(block))
        d2[rows, start + rows] = np.inf
        part = np.argpartition(d2, k, axis=1)[:, : k + 1]
        for r in range(len(block)):
            cand = part[r]
            order = np.lexsort((cand, d2[r, cand]))[:k]
            idx[start + r] = cand[order]
            dist[start + r] = np.sqrt(d2[r, cand[order]])
    return idx, dist


def overlap(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Share of each row's neighbour list that two neighbour tables have in common."""
    k = a.shape[1]
    return np.array([len(set(x) & set(y)) / k for x, y in zip(a.tolist(), b.tolist(), strict=True)])


def axis_label(f: Fit, j: int) -> str:
    """A mechanical draft label from the strongest loadings; the lead writes the real one."""
    col = f.loadings[:, j]
    order = np.argsort(-col)
    high = [INPUT_LABELS[f.columns[i]] for i in order if col[i] >= LOADING_MIN][:2]
    low = [INPUT_LABELS[f.columns[i]] for i in order[::-1] if col[i] <= -LOADING_MIN][:2]
    parts = []
    if high:
        parts.append("higher " + " and ".join(high))
    if low:
        parts.append("lower " + " and ".join(low))
    return "; ".join(parts) or "no strong loadings"


# --- outputs ------------------------------------------------------------------------------


@dataclass
class LevelResult:
    level: str
    fit: Fit
    excluded: pd.DataFrame
    neighbours: np.ndarray
    distances: np.ndarray
    unusual: pd.DataFrame
    contrasts: pd.DataFrame
    sensitivity: dict[str, dict[str, object]]
    check_max_error: float
    stability: dict[str, object] = field(default_factory=dict)


@dataclass
class ProfileResult:
    out_dir: Path
    levels: dict[str, LevelResult] = field(default_factory=dict)
    files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def census_wide(observations: pd.DataFrame) -> pd.DataFrame:
    keep = observations["period"].astype(str) == PERIOD
    if "preferred" in observations.columns:
        keep &= observations["preferred"].astype(bool)
    obs: pd.DataFrame = observations.loc[keep]
    wide = obs.pivot_table(
        index="geography_id", columns="indicator_id", values="value", aggfunc="first"
    )
    wide.index = wide.index.astype(str)
    return wide


def _sensitivity(x: pd.DataFrame, full: np.ndarray) -> dict[str, dict[str, object]]:
    out: dict[str, dict[str, object]] = {}
    for removed in BLOCKS:
        blocks = {name: cols for name, cols in BLOCKS.items() if name != removed}
        f = fit(x, blocks)
        if not f.retained:
            positive = [j for j in range(len(f.eigenvalues)) if f.eigenvalues[j] > f.threshold]
            f.retained = positive[:MAX_AXES]
            f.fallback = "loading rule retained no axes; used eigenvalue rule alone"
        if not f.retained:
            out[f"without_{removed}"] = {"axes": 0, "note": "no axes retained"}
            continue
        idx, _ = nearest(f, full.shape[1])
        ov = overlap(full, idx)
        out[f"without_{removed}"] = {
            "axes": len(f.retained),
            "mean_overlap": round(float(ov.mean()), 3),
            "median_overlap": round(float(np.median(ov)), 3),
            "share_at_least_half": round(float((ov >= 0.5).mean()), 3),
            "note": f.fallback,
        }
    return out


def perturb_counts(wide: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Redraw each count from a Poisson distribution with the published count as its mean.

    The census is a full count, not a sample. This models the ordinary random variation that
    makes small-area rates unstable (the reason for D-026); it is a sensitivity test, not an
    estimate of census error. Area is held fixed, so density moves with population.
    """
    w = wide.copy()
    for col in NOISE_COUNTS:
        w[col] = rng.poisson(w[col].fillna(0).clip(lower=0).to_numpy()).astype(float)
    w["population_total"] = w[AGE_COUNTS].sum(axis=1)
    w["sex_ratio"] = w["population_male"] / w["population_female"] * 100
    w["persons_per_occupied_housing_unit"] = w["population_total"] / w["occupied_housing_units"]
    w["population_density"] = (
        wide["population_density"] * w["population_total"] / wide["population_total"]
    )
    return w


def stability(
    wide: pd.DataFrame, x: pd.DataFrame, f: Fit, idx: np.ndarray, dist: np.ndarray
) -> dict[str, object]:
    """How much a place's similar-places list depends on the fit, the axes and small counts."""
    n, k = idx.shape
    rng = np.random.default_rng(SEED)
    out: dict[str, object] = {"k": k, "chance_overlap": round(k / (n - 1), 4)}

    axes: dict[str, float] = {}
    for m in (len(f.retained) - 1, len(f.retained) + 1):
        if 1 <= m <= len(f.eigenvalues):
            ids_m, _ = nearest_scores(f.z @ f.loadings[:, :m], k)
            axes[f"{m}_axes"] = round(float(overlap(idx, ids_m).mean()), 3)
    out["axis_count"] = axes

    boot = []
    for _ in range(BOOTSTRAP_RUNS):
        fb = fit(x.iloc[rng.choice(n, n, replace=True)])
        ids_b, _ = nearest_scores(project(fb, x) @ fb.basis, k)
        boot.append(float(overlap(idx, ids_b).mean()))
    out["bootstrap"] = {
        "runs": BOOTSTRAP_RUNS,
        "mean_overlap": round(float(np.mean(boot)), 3),
        "min_overlap": round(float(np.min(boot)), 3),
    }

    wide_idx, _ = nearest(f, WIDE_K)
    pop = wide.loc[f.ids, "population_total"].to_numpy(dtype=float)
    exact, within, shift, fallback = [], [], [], []
    for _ in range(NOISE_RUNS):
        xp = transform(perturb_counts(wide, rng).loc[f.ids])
        zp = project(f, xp)
        bad = ~np.isfinite(zp).all(axis=1)
        zp[bad] = f.z[bad]
        fallback.append(int(bad.sum()))
        sp = zp @ f.basis
        ids_p, _ = nearest_scores(sp, k)
        exact.append(overlap(idx, ids_p))
        within.append(
            np.array(
                [np.isin(ids_p[i], wide_idx[i]).mean() for i in range(n)],
            )
        )
        shift.append(np.linalg.norm(sp - f.scores, axis=1))
    ex = np.mean(exact, axis=0)
    wi = np.mean(within, axis=0)
    bands = []
    for lo, hi in POPULATION_BANDS:
        m = (pop >= lo) & (pop < (hi if hi is not None else np.inf))
        bands.append(
            {
                "population": f"{lo:,}+" if hi is None else f"{lo:,}-{hi - 1:,}",
                "places": int(m.sum()),
                "mean_overlap": round(float(ex[m].mean()), 3) if m.any() else None,
                f"inside_original_top_{WIDE_K}": round(float(wi[m].mean()), 3) if m.any() else None,
            }
        )
    out["count_noise"] = {
        "runs": NOISE_RUNS,
        "mean_overlap": round(float(ex.mean()), 3),
        f"inside_original_top_{WIDE_K}": round(float(wi.mean()), 3),
        "median_shift": round(float(np.median(np.mean(shift, axis=0))), 4),
        "rows_kept_unperturbed": max(fallback),
        "by_population": bands,
    }
    out["median_distance_1st"] = round(float(np.median(dist[:, 0])), 4)
    out[f"median_distance_{k}th"] = round(float(np.median(dist[:, -1])), 4)
    return out


def build_level(
    wide: pd.DataFrame, universe: list[str], level: str, neighbours: dict[str, list[str]]
) -> LevelResult:
    x, excluded = prepare(wide, universe)
    f = fit(x)
    if not f.retained:
        raise ValueError(f"{level}: the retention rule kept no axes")
    idx, dist = nearest(f)

    centre = np.array([decompose(f, i)[0] for i in range(len(f.ids))])
    centre_d = np.sqrt(centre)
    pct = pd.Series(centre_d).rank(pct=True, method="average").to_numpy() * 100
    top_ind = []
    for i in range(len(f.ids)):
        _, _, ind = decompose(f, i)
        top_ind.append([f.columns[j] for j in np.argsort(-ind)[:3]])
    unusual = pd.DataFrame(
        {
            "geography_id": f.ids,
            "distance_from_centre": centre_d.round(6),
            "percentile": pct.round(2),
            "top_indicators": top_ind,
        }
    )

    pos = {g: i for i, g in enumerate(f.ids)}
    pairs = sorted(
        {(a, b) for a, nbrs in neighbours.items() for b in nbrs if a < b and a in pos and b in pos}
    )
    pair_d = np.array([np.sqrt(decompose(f, pos[a], pos[b])[0]) for a, b in pairs])
    cut = float(np.percentile(pair_d, CONTRAST_PERCENTILE)) if len(pair_d) else float("nan")
    contrasts = pd.DataFrame(
        {
            "geography_id": [a for a, _ in pairs],
            "neighbour_id": [b for _, b in pairs],
            "distance": pair_d.round(6),
            "percentile_among_bordering_pairs": (
                pd.Series(pair_d).rank(pct=True).to_numpy() * 100
            ).round(2),
        }
    )
    contrasts["flagged"] = contrasts["distance"] > cut

    rng = np.random.default_rng(SEED)
    err = 0.0
    for _ in range(CHECK_PAIRS):
        a, b = rng.choice(len(f.ids), size=2, replace=False)
        d2, axis, ind = decompose(f, int(a), int(b))
        direct = float(((f.scores[a] - f.scores[b]) ** 2).sum())
        err = max(err, abs(axis.sum() - direct), abs(ind.sum() - direct), abs(d2 - direct))

    return LevelResult(
        level=level,
        fit=f,
        excluded=excluded,
        neighbours=idx,
        distances=dist,
        unusual=unusual,
        contrasts=contrasts,
        sensitivity=_sensitivity(x, idx),
        check_max_error=err,
        stability=stability(wide, x, f, idx, dist),
    )


def _similar_json(r: LevelResult) -> dict[str, object]:
    f = r.fit
    places: dict[str, list[object]] = {}
    for i, gid in enumerate(f.ids):
        rows = []
        for j, d in zip(r.neighbours[i].tolist(), r.distances[i].tolist(), strict=True):
            d2, _, ind = decompose(f, i, j)
            share = ind / d2 if d2 > 0 else np.zeros_like(ind)
            order = np.argsort(share)
            alike = [[int(c), round(float(share[c]), 4)] for c in order[:3]]
            differ = [[int(c), round(float(share[c]), 4)] for c in order[::-1][:3]]
            rows.append([f.ids[j], round(d, 4), alike, differ])
        places[gid] = rows
    return {
        "space_id": SPACE_ID,
        "space_version": SPACE_VERSION,
        "level": r.level,
        "period": PERIOD,
        "metric": "euclidean",
        "k": int(r.neighbours.shape[1]),
        "axes_retained": len(f.retained),
        "indicators": f.columns,
        "row_format": [
            "neighbour_id",
            "distance",
            "alike: [indicator index, share of squared distance] x3 (smallest)",
            "different: [indicator index, share of squared distance] x3 (largest)",
        ],
        "notes": (
            "Machine-computed similarity in the profile space. A distance is a similarity "
            "statement, not a fact and not a ranking. Shares sum to 1 over all indicators and "
            "can be negative. Not validated by a person."
        ),
        "places": places,
    }


def write_outputs(result: ProfileResult) -> None:
    out = result.out_dir
    vec_dir = out / "vectors"
    vec_dir.mkdir(parents=True, exist_ok=True)
    vec_rows: list[dict[str, object]] = []
    axis_rows: list[dict[str, object]] = []
    excluded = []
    for level, r in result.levels.items():
        f = r.fit
        for gid, vec in zip(f.ids, f.scores, strict=True):
            vec_rows.append(_vec_row("place", gid, level, vec))
        coords = f.basis * np.sqrt(f.eigenvalues[f.retained])
        for col, vec in zip(f.columns, coords, strict=True):
            vec_rows.append(_vec_row("indicator", col, level, vec))
        total = f.eigenvalues.sum()
        for j, ev in enumerate(f.eigenvalues):
            for c, col in enumerate(f.columns):
                axis_rows.append(
                    {
                        "level": level,
                        "axis": j + 1,
                        "eigenvalue": float(ev),
                        "variance_explained": float(ev / total),
                        "retained": j in f.retained,
                        "indicator_id": col,
                        "loading": float(f.loadings[c, j]),
                        "draft_label": axis_label(f, j) if j in f.retained else None,
                        "label_status": LABEL_STATUS if j in f.retained else None,
                        "space_id": SPACE_ID,
                        "space_version": SPACE_VERSION,
                    }
                )
        excluded.append(r.excluded.assign(level=level))
        sim = vec_dir / f"similar_{level}_{PERIOD}.json"
        sim.write_text(json.dumps(_similar_json(r), separators=(",", ":")), encoding="utf-8")
        result.files.append(str(sim))
        for name, frame in (("unusual", r.unusual), ("contrasts", r.contrasts)):
            path = vec_dir / f"{name}_{level}_{PERIOD}.parquet"
            frame.assign(space_id=SPACE_ID, space_version=SPACE_VERSION).to_parquet(
                path, index=False
            )
            result.files.append(str(path))
    for name, rows in (
        (f"profile_v{SPACE_VERSION}.parquet", vec_rows),
        (f"profile_v{SPACE_VERSION}_axes.parquet", axis_rows),
    ):
        path = vec_dir / name
        pd.DataFrame(rows).to_parquet(path, index=False)
        result.files.append(str(path))
    exc_path = out / "excluded_places.csv"
    pd.concat(excluded).to_csv(exc_path, index=False)
    sens_path = out / "sensitivity.json"
    sens_path.write_text(
        json.dumps(
            {lv: {**r.sensitivity, "stability": r.stability} for lv, r in result.levels.items()},
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    result.files += [str(exc_path), str(sens_path)]


def _vec_row(kind: str, entity_id: str, level: str, vec: np.ndarray) -> dict[str, object]:
    v = np.asarray(vec, dtype=np.float32)
    return {
        "entity_type": kind,
        "entity_id": entity_id,
        "level": level,
        "period": PERIOD,
        "space_id": SPACE_ID,
        "space_version": SPACE_VERSION,
        "vector": v.tolist(),
        "norm": float(np.linalg.norm(v)),
    }


def build_profile(
    observations: pd.DataFrame,
    geographies: pd.DataFrame,
    spine_dir: Path,
    catalog_root: Path,
    out_dir: Path,
) -> ProfileResult:
    load_space(catalog_root)
    wide = census_wide(observations)
    result = ProfileResult(out_dir=out_dir)
    for code, level in LEVELS.items():
        universe = sorted(
            geographies.loc[geographies["level"] == code, "geography_id"].astype(str).tolist()
        )
        r = build_level(wide, universe, level, load_neighbours(spine_dir, level))
        result.levels[level] = r
        if r.check_max_error > 1e-9:
            result.warnings.append(f"{level}: decomposition error {r.check_max_error:.2e}")
    write_outputs(result)
    return result


# --- QA report ----------------------------------------------------------------------------

EXAMPLE_DS = ["LK1103", "LK2312", "LK4136", "LK5124", "LK7109"]  # agent's picks, not the lead's


def render_qa(result: ProfileResult, geographies: pd.DataFrame) -> str:
    names = dict(
        zip(geographies["geography_id"].astype(str), geographies["name_en"].fillna(""), strict=True)
    )

    def nm(gid: str) -> str:
        return f"{names.get(gid) or '(no name)'} `{gid}`"

    lines = [
        f"# Profile space v{SPACE_VERSION}: QA report",
        "",
        "Generated by `slf profile build`. Machine-computed and not validated by a person. A "
        "distance is a similarity statement, never a fact and never a ranking (AGENTS rule 13). "
        f"Recipe: `catalog/spaces/profile.yaml` v{SPACE_VERSION} (D-025, retention rule D-029).",
        "",
        "## 1. Places with and without vectors",
        "",
        "| Level | Spine units | With vector | Excluded | Exclusion reasons |",
        "|---|---|---|---|---|",
    ]
    for level, r in result.levels.items():
        counts = r.excluded["reason"].str.split(":").str[0].value_counts()
        reasons = ", ".join(f"{k} {v}" for k, v in counts.items()) or "none"
        n_all = len(r.fit.ids) + len(r.excluded)
        lines.append(
            f"| {level} | {n_all:,} | {len(r.fit.ids):,} | {len(r.excluded)} | {reasons} |"
        )
    lines += ["", "Every excluded unit is listed with its reason in `excluded_places.csv`.", ""]

    lines += ["## 2. Axes", ""]
    for level, r in result.levels.items():
        f = r.fit
        total = f.eigenvalues.sum()
        lines += [
            f"### {level.upper()}",
            "",
            f"Total weighted variance {total:.3f}; retention threshold {f.threshold:.3f} "
            f"(total / {len(f.columns)}); loading rule: at least {MIN_LOADINGS} loadings with "
            f"|loading| ≥ {LOADING_MIN}. Retained axes: {len(f.retained)}.",
            "",
            "| Axis | Eigenvalue | Variance explained | Retained | "
            "Draft label (machine-generated) |",
            "|---|---|---|---|---|",
        ]
        for j, ev in enumerate(f.eigenvalues):
            label = axis_label(f, j) if j in f.retained else ""
            ret = "yes" if j in f.retained else "no"
            lines.append(f"| {j + 1} | {ev:.3f} | {ev / total:.1%} | {ret} | {label} |")
        lines += ["", "Loadings on retained axes:", ""]
        lines.append("| Indicator | " + " | ".join(f"Axis {j + 1}" for j in f.retained) + " |")
        lines.append("|---|" + "---|" * len(f.retained))
        for c, col in enumerate(f.columns):
            vals = " | ".join(f"{f.loadings[c, j]:+.2f}" for j in f.retained)
            lines.append(f"| {INPUT_LABELS[col]} | {vals} |")
        clipped = {INPUT_LABELS[k]: v for k, v in f.clipped.items() if v}
        lines += [
            "",
            "Values clipped at ±5 SD: "
            + (", ".join(f"{k} {v}" for k, v in clipped.items()) if clipped else "none"),
            "",
        ]

    lines += [
        "## 3. Distance decomposition check",
        "",
        f"For {CHECK_PAIRS} random pairs per level (seed {SEED}), the axis contributions and the "
        "indicator contributions were each summed and compared with the squared distance "
        "computed directly from the vectors.",
        "",
    ]
    for level, r in result.levels.items():
        lines.append(f"- {level}: largest absolute difference {r.check_max_error:.1e}")
    lines += [
        "",
        "## 4. Sensitivity: neighbour lists with one block removed",
        "",
        f"Overlap is the share of each place's top-{TOP_K} list that is unchanged.",
        "",
        "| Level | Run | Axes | Mean overlap | Median | Places with ≥ 50% unchanged |",
        "|---|---|---|---|---|---|",
    ]
    for level, r in result.levels.items():
        for run, s in r.sensitivity.items():
            lines.append(
                f"| {level} | {run.replace('_', ' ')} | {s['axes']} | {s.get('mean_overlap', '')} "
                f"| {s.get('median_overlap', '')} | {s.get('share_at_least_half', '')} |"
            )
    lines += [""]

    lines += [
        "Removing a block changes what the space measures, so low overlap here shows how much "
        "each block shapes the lists, not that the lists are noisy. Section 4b tests noise.",
        "",
        "## 4b. Stability of similar-places lists",
        "",
        "- **Refit:** the PCA is refitted on places resampled with replacement and every place "
        "is projected again. This tests whether the axes depend on which places happen to be "
        "included.",
        "- **Axes:** one axis fewer and one more than the rule keeps.",
        "- **Small counts:** every count is redrawn from a Poisson distribution with the "
        "published count as its mean, then projected through the original standardisation. "
        "The census is a full count; this models the ordinary random variation that makes "
        "small-area rates unstable (the reason for D-026). It is a sensitivity test, not an "
        "estimate of census error.",
        "",
        "| Level | Chance | Refit | Fewer axes | More axes | Small counts | "
        f"Small counts, inside original top {WIDE_K} | Median shift | Median distance to 1st / "
        f"{TOP_K}th |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for level, r in result.levels.items():
        st = r.stability
        if not st:
            continue
        ax = st["axis_count"]
        axes_vals = list(ax.values()) if isinstance(ax, dict) else []
        fewer = axes_vals[0] if axes_vals else ""
        more = axes_vals[1] if len(axes_vals) > 1 else ""
        bo = st["bootstrap"]
        no = st["count_noise"]
        assert isinstance(bo, dict) and isinstance(no, dict)
        lines.append(
            f"| {level} | {st['chance_overlap']} | {bo['mean_overlap']} (min {bo['min_overlap']}) "
            f"| {fewer} | {more} | {no['mean_overlap']} | {no[f'inside_original_top_{WIDE_K}']} "
            f"| {no['median_shift']} | {st['median_distance_1st']} / "
            f"{st[f'median_distance_{TOP_K}th']} |"
        )
    lines += [
        "",
        "Overlap is the mean share of a place's top-"
        f"{TOP_K} list that is unchanged. Chance is the overlap two random lists would have. "
        "Median shift is how far a place moves in the space under small-count noise; compare it "
        "with the distance to its neighbours.",
        "",
    ]
    for level, r in result.levels.items():
        no = r.stability.get("count_noise") if r.stability else None
        if not isinstance(no, dict):
            continue
        lines += [
            f"Small-count overlap by population, {level.upper()}:",
            "",
            f"| Population | Places | Overlap | Inside original top {WIDE_K} |",
            "|---|---|---|---|",
        ]
        for b in no["by_population"]:
            lines.append(
                f"| {b['population']} | {b['places']:,} | {b['mean_overlap']} "
                f"| {b[f'inside_original_top_{WIDE_K}']} |"
            )
        lines.append("")
    lines += ["## 5. Distance from the national centre (most unusual 10)", ""]
    for level, r in result.levels.items():
        top = r.unusual.sort_values("distance_from_centre", ascending=False).head(10)
        lines += [f"### {level.upper()}", "", "| Place | Distance | Largest contributions |"]
        lines.append("|---|---|---|")
        for row in top.to_dict("records"):
            inds = ", ".join(INPUT_LABELS[i] for i in row["top_indicators"])
            lines.append(
                f"| {nm(str(row['geography_id']))} | {row['distance_from_centre']:.2f} | {inds} |"
            )
        lines.append("")

    lines += [
        "## 6. Contrasts between bordering units",
        "",
        f"A bordering pair is flagged when its profile distance is above the "
        f"{CONTRAST_PERCENTILE:.0f}th percentile of distances between bordering pairs "
        "at that level.",
        "",
    ]
    for level, r in result.levels.items():
        c = r.contrasts
        flagged = c["flagged"].astype(bool).tolist().count(True)
        lines.append(f"- {level}: {flagged:,} of {len(c):,} bordering pairs flagged")
    if "ds" in result.levels:
        c = result.levels["ds"].contrasts.sort_values("distance", ascending=False).head(10)
        lines += [
            "",
            "Largest DS contrasts:",
            "",
            "| Place | Neighbour | Distance |",
            "|---|---|---|",
        ]
        for row in c.to_dict("records"):
            lines.append(
                f"| {nm(str(row['geography_id']))} | {nm(str(row['neighbour_id']))} "
                f"| {row['distance']:.2f} |"
            )
    lines.append("")

    if "ds" in result.levels:
        r = result.levels["ds"]
        f = r.fit
        pos = {g: i for i, g in enumerate(f.ids)}
        lines += [
            "## 7. Example places (DS, agent's picks; the lead should name their own)",
            "",
        ]
        for gid in EXAMPLE_DS:
            if gid not in pos:
                lines += [f"- {nm(gid)}: no vector", ""]
                continue
            i = pos[gid]
            lines += [
                f"### {nm(gid)}",
                "",
                "| # | Similar place | Distance | Most alike | Most different |",
            ]
            lines.append("|---|---|---|---|---|")
            for rank, (j, d) in enumerate(
                zip(r.neighbours[i][:10], r.distances[i][:10], strict=True), 1
            ):
                d2, _, ind = decompose(f, i, int(j))
                share = ind / d2 if d2 > 0 else np.zeros_like(ind)
                order = np.argsort(share)
                alike = ", ".join(INPUT_LABELS[f.columns[c]] for c in order[:3])
                differ = ", ".join(INPUT_LABELS[f.columns[c]] for c in order[::-1][:3])
                lines.append(f"| {rank} | {nm(f.ids[int(j)])} | {d:.2f} | {alike} | {differ} |")
            lines.append("")
    return "\n".join(lines) + "\n"
