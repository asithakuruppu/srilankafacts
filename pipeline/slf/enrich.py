"""Spatial context enrichment (prompt D06).

Reads validated observations and the contiguity graph and writes, for every indicator and
level, neighbour comparisons, parent and national values, a rank, and a local Moran's I
cluster/outlier class with false-discovery-rate control. Rate indicators also get a
small-denominator flag and an empirical Bayes smoothed value, stored separately and labelled
``modelled_estimate``. Published values are never modified.

The stage is deterministic: permutations use a fixed seed, files are sorted, and no
wall-clock value is written.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from esda.moran import Moran_Local
from libpysal.weights import W

from slf.catalog import Catalog

LEVELS = {4: "gn", 3: "ds", 2: "district"}
SMALL_DENOMINATOR_THRESHOLD = 100.0
FDR_Q = 0.05
PERMUTATIONS = 999
SEED = 20241108

QUADRANT_CLASS = {1: "high_high", 2: "low_high", 3: "low_low", 4: "high_low"}


@dataclass
class RateSpec:
    """How to reconstruct a rate and smooth it.

    ``model`` is ``beta_binomial`` for proportions (smoothed on the 0-1 scale, then
    multiplied by ``multiplier``) or ``gamma_poisson`` for counts per exposure.
    ``small_denominator_source`` names the column used for the small-number flag; it is the
    rate denominator unless a different population base is more meaningful.
    """

    numerator: str
    denominator: str
    model: str
    multiplier: float = 1.0
    odds_per_100: bool = False
    denominator_kind: str = "persons"
    small_denominator_source: str | None = None


@dataclass
class SpatialContextResult:
    files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    class_counts: dict[str, dict[str, int]] = field(default_factory=dict)


def load_neighbours(spine_dir: Path, level_name: str) -> dict[str, list[str]]:
    """Load a symmetric contiguity graph for one level."""
    matches = sorted((spine_dir / "spatial").glob(f"adjacency_{level_name}_*.parquet"))
    if not matches:
        raise FileNotFoundError(f"no adjacency file for {level_name} under {spine_dir / 'spatial'}")
    if len(matches) > 1:
        raise ValueError(f"more than one adjacency file for {level_name}: {matches}")
    frame = pd.read_parquet(matches[0])
    graph: dict[str, set[str]] = {}
    for left, right in zip(
        frame["geography_id"].astype(str).tolist(),
        frame["neighbour_id"].astype(str).tolist(),
        strict=False,
    ):
        if left == right:
            continue
        graph.setdefault(left, set()).add(right)
        graph.setdefault(right, set()).add(left)
    return {key: sorted(value) for key, value in sorted(graph.items())}


def benjamini_hochberg(p_values: pd.Series) -> pd.Series:
    """Benjamini-Hochberg adjusted p-values, preserving the input index."""
    result = pd.Series(np.nan, index=p_values.index, dtype="float64")
    valid = p_values.dropna()
    if valid.empty:
        return result
    values = valid.to_numpy(dtype="float64")
    order = np.argsort(values)
    ranked = values[order]
    count = len(ranked)
    adjusted = ranked * count / np.arange(1, count + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    adjusted = np.clip(adjusted, 0.0, 1.0)
    ordered_index = valid.index.to_numpy()[order]
    result.loc[ordered_index] = adjusted
    return result


def _empirical_bayes_beta(
    numerator: np.ndarray, denominator: np.ndarray
) -> tuple[np.ndarray, float]:
    """Beta-binomial empirical Bayes, prior moments by the method of moments."""
    valid = np.isfinite(numerator) & np.isfinite(denominator) & (denominator > 0)
    smoothed = np.full(len(numerator), np.nan, dtype="float64")
    if valid.sum() < 2:
        return smoothed, float("nan")
    k = numerator[valid]
    n = denominator[valid]
    total = n.sum()
    p_bar = float(k.sum() / total) if total > 0 else float("nan")
    if not math.isfinite(p_bar) or p_bar <= 0 or p_bar >= 1:
        return smoothed, float("nan")
    p = k / n
    observed = float(np.average((p - p_bar) ** 2, weights=n))
    noise = float(p_bar * (1 - p_bar) * np.average(1.0 / n, weights=n))
    tau2 = max(observed - noise, 1e-12)
    prior_size = p_bar * (1 - p_bar) / tau2 - 1.0
    prior_size = float(np.clip(prior_size, 1.0, 1e6))
    alpha = p_bar * prior_size
    beta = (1 - p_bar) * prior_size
    smoothed[valid] = (alpha + k) / (alpha + beta + n)
    return smoothed, prior_size


def _empirical_bayes_gamma(numerator: np.ndarray, exposure: np.ndarray) -> tuple[np.ndarray, float]:
    """Gamma-Poisson empirical Bayes for a count per exposure, moments estimator."""
    valid = np.isfinite(numerator) & np.isfinite(exposure) & (exposure > 0)
    smoothed = np.full(len(numerator), np.nan, dtype="float64")
    if valid.sum() < 2:
        return smoothed, float("nan")
    k = numerator[valid]
    e = exposure[valid]
    total_exposure = e.sum()
    mean_rate = float(k.sum() / total_exposure) if total_exposure > 0 else float("nan")
    if not math.isfinite(mean_rate) or mean_rate <= 0:
        return smoothed, float("nan")
    rates = k / e
    observed = float(np.average((rates - mean_rate) ** 2, weights=e))
    noise = float(np.average(rates / e, weights=e))
    tau2 = max(observed - noise, 1e-12)
    alpha = max(mean_rate * mean_rate / tau2, 1e-6)
    beta = alpha / mean_rate
    smoothed[valid] = (alpha + k) / (beta + e)
    return smoothed, alpha


def local_moran(
    values: pd.Series,
    neighbours: dict[str, list[str]],
    *,
    permutations: int = PERMUTATIONS,
    seed: int = SEED,
) -> pd.DataFrame:
    """Local Moran's I with conditional permutation and BH-FDR control.

    Units with no value or no neighbour that also has a value are returned with a class of
    ``no_data`` or ``no_neighbours``. All other units get an I, permutation p-value,
    adjusted q-value and one of the four LISA classes or ``not_significant``.
    """
    index = pd.Index(values.index.astype(str))
    out = pd.DataFrame(index=index)
    out.index.name = "geography_id"
    out["value"] = values.reindex(index).astype("float64")
    out["neighbour_count"] = [len(neighbours.get(key, [])) for key in index]
    out["local_moran_i"] = np.nan
    out["p_value"] = np.nan
    out["q_value"] = np.nan
    out["class"] = "no_data"

    has_value = out["value"].notna()
    candidates = {key for key in index if has_value.loc[key]}
    sub_ids = sorted(
        key for key in candidates if any(n in candidates for n in neighbours.get(key, []))
    )
    # Dropping neighbours without values can isolate a unit; repeat until stable.
    while True:
        sub = set(sub_ids)
        trimmed = [key for key in sub_ids if any(n in sub for n in neighbours.get(key, []))]
        if len(trimmed) == len(sub_ids):
            break
        sub_ids = trimmed
    out.loc[has_value, "class"] = "no_neighbours"
    if len(sub_ids) < 3:
        out.loc[sub_ids, "class"] = "not_significant"
        return out

    y = values.loc[sub_ids].to_numpy(dtype="float64")
    if float(np.nanstd(y)) == 0.0:
        out.loc[sub_ids, "class"] = "not_significant"
        return out

    sub = set(sub_ids)
    weights = W(
        {key: [n for n in neighbours.get(key, []) if n in sub] for key in sub_ids},
        silence_warnings=True,
    )
    weights.transform = "r"
    moran = Moran_Local(
        y,
        weights,
        permutations=permutations,
        seed=seed,
        island_weight=0,
        alternative="directed",
    )
    p_values = pd.Series(moran.p_sim, index=sub_ids, dtype="float64")
    q_values = benjamini_hochberg(p_values)
    out.loc[sub_ids, "local_moran_i"] = moran.Is
    out.loc[sub_ids, "p_value"] = p_values
    out.loc[sub_ids, "q_value"] = q_values
    classes = []
    for key, quadrant in zip(sub_ids, moran.q.tolist(), strict=False):
        if pd.notna(q_values.loc[key]) and q_values.loc[key] <= FDR_Q:
            classes.append(QUADRANT_CLASS.get(int(quadrant), "not_significant"))
        else:
            classes.append("not_significant")
    out.loc[sub_ids, "class"] = classes
    return out


def _rate_spec(catalog: Catalog, indicator_id: str) -> RateSpec | None:
    indicator = catalog.indicators.get(indicator_id)
    if indicator is None:
        return None
    if indicator_id == "population_density":
        return RateSpec(
            numerator="population_total",
            denominator="area_km2",
            model="gamma_poisson",
            denominator_kind="km2",
            small_denominator_source="population_total",
        )
    if indicator_id == "sex_ratio":
        return RateSpec(
            numerator="population_male",
            denominator="population_female",
            model="beta_binomial",
            multiplier=100.0,
            odds_per_100=True,
            denominator_kind="females",
        )
    if (
        indicator.measure_type in ("share", "ratio", "rate")
        and indicator.numerator
        and indicator.denominator
    ):
        model = "gamma_poisson" if indicator.measure_type == "ratio" else "beta_binomial"
        multiplier = 100.0 if indicator.unit == "percent" else 1.0
        return RateSpec(
            numerator=indicator.numerator,
            denominator=indicator.denominator,
            model=model,
            multiplier=multiplier,
        )
    return None


def _smoothed_rate(
    spec: RateSpec, source: pd.DataFrame, areas: pd.Series
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Return smoothed values, denominators and method labels aligned to ``source``."""
    index = source.index.astype(str)
    numerator = np.asarray(pd.to_numeric(source[spec.numerator], errors="coerce"), dtype="float64")
    if spec.denominator == "area_km2":
        denominator = np.asarray(
            pd.to_numeric(areas.reindex(index), errors="coerce"), dtype="float64"
        )
    else:
        denominator = np.asarray(
            pd.to_numeric(source[spec.denominator], errors="coerce"), dtype="float64"
        )
    if spec.model == "beta_binomial":
        if spec.odds_per_100:
            # Model males as a share of males + females, then convert the smoothed
            # proportion back to males per 100 females.
            female = denominator
            male = numerator
            total = male + female
            smoothed_share, _ = _empirical_bayes_beta(male, total)
            smoothed_share = np.clip(smoothed_share, 1e-9, 1 - 1e-9)
            smoothed = 100.0 * smoothed_share / (1.0 - smoothed_share)
            method = "beta-binomial empirical Bayes (method of moments; males per 100 females)"
        else:
            smoothed_share, _ = _empirical_bayes_beta(numerator, denominator)
            smoothed = smoothed_share * spec.multiplier
            method = "beta-binomial empirical Bayes (method of moments)"
    else:
        smoothed, _ = _empirical_bayes_gamma(numerator, denominator)
        method = "gamma-Poisson empirical Bayes (method of moments)"
    return (
        pd.Series(smoothed, index=index),
        pd.Series(denominator, index=index),
        pd.Series(method, index=index),
    )


def _neighbour_summary(values: pd.Series, neighbours: dict[str, list[str]]) -> pd.DataFrame:
    rows = []
    for key in values.index.astype(str):
        neighbour_values = [
            float(values.loc[n])
            for n in neighbours.get(key, [])
            if n in values.index and pd.notna(values.loc[n])
        ]
        rows.append(
            {
                "geography_id": key,
                "neighbour_value_count": len(neighbour_values),
                "neighbour_median": float(np.median(neighbour_values))
                if neighbour_values
                else np.nan,
                "neighbour_min": float(np.min(neighbour_values)) if neighbour_values else np.nan,
                "neighbour_max": float(np.max(neighbour_values)) if neighbour_values else np.nan,
                "neighbour_mean": float(np.mean(neighbour_values)) if neighbour_values else np.nan,
                "spatial_lag": float(np.mean(neighbour_values)) if neighbour_values else np.nan,
            }
        )
    return pd.DataFrame(rows).set_index("geography_id")


def _context_table(
    *,
    indicator_id: str,
    level: int,
    level_name: str,
    units: pd.DataFrame,
    values: pd.Series,
    status: pd.Series,
    neighbours: dict[str, list[str]],
    parent_values: pd.Series,
    national_value: float | None,
    rate_spec: RateSpec | None,
    source_values: pd.DataFrame,
    areas: pd.Series,
    permutations: int,
    seed: int,
) -> pd.DataFrame:
    values = values.reindex(units["geography_id"].astype(str))
    neighbours_frame = _neighbour_summary(values, neighbours)
    lisa = local_moran(values, neighbours, permutations=permutations, seed=seed)
    frame = pd.DataFrame({"geography_id": units["geography_id"].astype(str).tolist()}).set_index(
        "geography_id"
    )
    frame["geography_name"] = units.set_index("geography_id")["name_en"].reindex(frame.index)
    frame["level"] = level
    frame["level_name"] = level_name
    frame["indicator_id"] = indicator_id
    frame["value"] = values
    frame["value_status"] = status.reindex(frame.index)
    frame["neighbour_count"] = lisa["neighbour_count"]
    for column in (
        "neighbour_value_count",
        "neighbour_median",
        "neighbour_min",
        "neighbour_max",
        "neighbour_mean",
        "spatial_lag",
    ):
        frame[column] = neighbours_frame[column].reindex(frame.index)
    parent_ids = units.set_index("geography_id")["parent_id"].reindex(frame.index)
    frame["parent_id"] = [None if pd.isna(value) else str(value) for value in parent_ids.tolist()]
    parent_lookup = {
        str(key): float(value) for key, value in parent_values.items() if pd.notna(value)
    }
    frame["parent_value"] = [
        parent_lookup.get(str(parent), np.nan) if pd.notna(parent) else np.nan
        for parent in parent_ids.tolist()
    ]
    frame["national_value"] = national_value
    valid_values = frame["value"].dropna()
    ranks = valid_values.rank(method="min", ascending=False)
    frame["rank"] = ranks.reindex(frame.index).astype("Int64")
    frame["rank_total"] = len(valid_values)
    frame["local_moran_i"] = lisa["local_moran_i"]
    frame["p_value"] = lisa["p_value"]
    frame["q_value"] = lisa["q_value"]
    frame["class"] = lisa["class"]
    if rate_spec is None:
        frame["denominator"] = np.nan
        frame["small_denominator"] = False
        frame["small_denominator_basis"] = None
        frame["smoothed_value"] = np.nan
        frame["smoothed_method"] = None
        frame["smoothed_data_nature"] = None
    else:
        source = source_values.reindex(frame.index)
        smoothed, denominator, method = _smoothed_rate(rate_spec, source, areas)
        frame["denominator"] = denominator
        basis = rate_spec.small_denominator_source or rate_spec.denominator
        frame["small_denominator_basis"] = basis
        threshold_values = (
            pd.to_numeric(areas.reindex(frame.index), errors="coerce")
            if basis == "area_km2"
            else pd.to_numeric(source[basis], errors="coerce")
        )
        threshold = np.asarray(threshold_values, dtype="float64")
        frame["small_denominator"] = pd.Series(
            np.isfinite(threshold) & (threshold < SMALL_DENOMINATOR_THRESHOLD),
            index=frame.index,
        )
        frame["smoothed_value"] = smoothed
        frame["smoothed_method"] = method
        frame["smoothed_data_nature"] = "modelled_estimate"
    return frame.sort_index()


def _qa_report(
    tables: dict[str, pd.DataFrame],
    *,
    permutations: int,
    seed: int,
) -> str:
    lines = [
        "# Spatial context QA (D06)",
        "",
        f"Local Moran's I: rook contiguity from the spine graph (shared border >= 10 m, "
        f"3 nearest units for isolated units), row-standardised; "
        f"{permutations} conditional permutations, seed {seed}; "
        f"Benjamini-Hochberg FDR at q ≤ {FDR_Q}.",
        "",
        "Classes are spatial-association labels, not causal findings. Counts are included; "
        "for counts, clusters partly reflect settlement size.",
        "",
        "## Class counts",
        "",
        "| indicator | level | units | values | no data | no neighbours | "
        "HH | LL | HL | LH | not sig. |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for key in sorted(tables):
        table = tables[key]
        counts = {
            label: len(table[table["class"] == label].index)
            for label in (
                "no_data",
                "no_neighbours",
                "high_high",
                "low_low",
                "high_low",
                "low_high",
                "not_significant",
            )
        }
        lines.append(
            f"| {table['indicator_id'].iloc[0]} | {table['level_name'].iloc[0]} | "
            f"{len(table)} | {len(table[table['value'].notna()].index)} | "
            f"{counts['no_data']} | {counts['no_neighbours']} | "
            f"{counts['high_high']} | {counts['low_low']} | "
            f"{counts['high_low']} | {counts['low_high']} | "
            f"{counts['not_significant']} |"
        )
    lines += ["", "## Spatial outliers to check", ""]
    outliers = []
    for table in tables.values():
        selected = table[table["class"].isin(["high_low", "low_high"])].reset_index()
        for record in selected.to_dict("records"):
            q_value = record["q_value"]
            outliers.append(
                (
                    float(q_value) if pd.notna(q_value) else 1.0,
                    str(record["indicator_id"]),
                    str(record["level_name"]),
                    str(record["geography_id"]),
                    str(record["geography_name"]),
                    float(record["value"]) if pd.notna(record["value"]) else float("nan"),
                    float(record["neighbour_median"])
                    if pd.notna(record["neighbour_median"])
                    else float("nan"),
                    str(record["class"]),
                    float(q_value) if pd.notna(q_value) else float("nan"),
                )
            )
    outliers.sort(key=lambda item: (item[0], -abs(item[5]) if pd.notna(item[5]) else 0))
    if not outliers:
        lines.append("- none")
    else:
        lines += [
            "| indicator | level | geography | name | value | neighbour median | class | q |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for item in outliers[:50]:
            lines.append(
                f"| {item[1]} | {item[2]} | `{item[3]}` | {item[4]} | {item[5]:.2f} | "
                f"{item[6]:.2f} | {item[7]} | {item[8]:.4f} |"
            )
        if len(outliers) > 50:
            lines.append(f"| … | | | | | | | {len(outliers) - 50} more in the stats files |")
    lines += [
        "",
        "## Small denominators",
        "",
        f"Rate indicators are flagged when their denominator is below "
        f"{SMALL_DENOMINATOR_THRESHOLD:g}. Smoothed values use empirical Bayes (beta-binomial "
        "for proportions, gamma-Poisson for counts per exposure), are stored separately and "
        "are labelled `modelled_estimate`; raw values remain the published values.",
        "",
        "| indicator | level | flagged | share of values |",
        "|---|---|---|---|",
    ]
    for key in sorted(tables):
        table = tables[key]
        if len(table[table["smoothed_method"].notna()].index) == 0:
            continue
        flagged = len(table[table["small_denominator"]].index)
        total = len(table[table["value"].notna()].index)
        share = f"{100 * flagged / total:.1f}%" if total else "n/a"
        lines.append(
            f"| {table['indicator_id'].iloc[0]} | {table['level_name'].iloc[0]} | "
            f"{flagged} | {share} |"
        )
    return "\n".join(lines) + "\n"


def build_spatial_context(
    *,
    observations: pd.DataFrame,
    geographies: pd.DataFrame,
    catalog: Catalog,
    spine_dir: Path,
    out: Path,
    permutations: int = PERMUTATIONS,
    seed: int = SEED,
) -> SpatialContextResult:
    """Compute and write spatial-context files for every indicator and level."""
    result = SpatialContextResult()
    out_stats = out / "stats"
    out_stats.mkdir(parents=True, exist_ok=True)
    (out / "qa").mkdir(parents=True, exist_ok=True)
    geo = pd.DataFrame(geographies.copy())
    geo["geography_id"] = geo["geography_id"].astype(str)
    areas = pd.Series(dtype="float64")
    if "area_km2" in geo:
        areas = pd.Series(
            np.asarray(pd.to_numeric(geo["area_km2"], errors="coerce"), dtype="float64"),
            index=geo["geography_id"].astype(str),
        )

    values = pd.DataFrame(
        observations.pivot_table(
            index="geography_id", columns="indicator_id", values="value", aggfunc="first"
        )
    )
    values.index = values.index.astype(str)
    status = pd.DataFrame(
        observations.pivot_table(
            index="geography_id", columns="indicator_id", values="value_status", aggfunc="first"
        )
    )
    status.index = status.index.astype(str)

    tables: dict[str, pd.DataFrame] = {}
    outlier_tables = 0
    for level, level_name in sorted(LEVELS.items(), reverse=True):
        units = pd.DataFrame(geo[geo["level"] == level]).copy()
        if units.empty:
            continue
        units = units.sort_values("geography_id")
        try:
            neighbours = load_neighbours(spine_dir, level_name)
        except (FileNotFoundError, ValueError) as exc:
            result.warnings.append(str(exc))
            continue
        national = (
            pd.Series(values.loc["LK"]) if "LK" in values.index else pd.Series(dtype="float64")
        )
        for indicator_id in sorted(values.columns):
            if indicator_id not in catalog.indicators:
                continue
            if catalog.indicators[indicator_id].distribution == "places_only":
                # D-033: no neighbour comparisons for ethnicity and religion
                continue
            indicator_values = pd.Series(values[indicator_id]).reindex(
                units["geography_id"].astype(str)
            )
            if not indicator_values.notna().any():
                # e.g. DS-only tables at GN level: no table, rather than one full of no_data
                continue
            indicator_status = pd.Series(status[indicator_id]).reindex(
                units["geography_id"].astype(str)
            )
            rate_spec = _rate_spec(catalog, indicator_id)
            national_value = national.get(indicator_id)
            table = _context_table(
                indicator_id=indicator_id,
                level=level,
                level_name=level_name,
                units=units,
                values=indicator_values,
                status=indicator_status,
                neighbours=neighbours,
                parent_values=pd.Series(values[indicator_id]),
                national_value=(
                    float(national_value)
                    if national_value is not None and pd.notna(national_value)
                    else None
                ),
                rate_spec=rate_spec,
                source_values=values,
                areas=areas,
                permutations=permutations,
                seed=seed,
            )
            key = f"{indicator_id}_{level_name}"
            tables[key] = table
            rel = f"stats/local_{indicator_id}_{level_name}.parquet"
            table.reset_index().to_parquet(out / rel, index=False, compression="zstd")
            result.files.append(rel)
            counts = {str(k): int(v) for k, v in table["class"].value_counts().items()}
            result.class_counts[key] = counts
            outlier_count = counts.get("high_low", 0) + counts.get("low_high", 0)
            if outlier_count:
                outlier_tables += 1
    if outlier_tables:
        result.warnings.append(
            f"spatial context: {outlier_tables} indicator-level tables contain high-low or "
            "low-high outliers; see qa/spatial-context.md"
        )
    summary = {
        "method": "local Moran's I",
        "permutations": permutations,
        "seed": seed,
        "fdr_q": FDR_Q,
        "small_denominator_threshold": SMALL_DENOMINATOR_THRESHOLD,
        "class_counts": result.class_counts,
    }
    rel = "stats/spatial_summary.json"
    (out / rel).write_bytes(
        (
            json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
    )
    result.files.append(rel)
    qa = _qa_report(tables, permutations=permutations, seed=seed)
    (out / "qa" / "spatial-context.md").write_bytes(qa.encode("utf-8"))
    result.files.append("qa/spatial-context.md")
    return result
