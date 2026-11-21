"""Population-weighted grid (G07, D-014): GN totals apportioned over H3 cells.

Weights come from one rights-checked source only: WorldPop's 100 m constrained population
grid (CC BY 4.0). Each raster pixel is assigned to the H3 cell holding its centre; a cell's raw
weight is the sum of its pixels; within a GN the weights are normalised to sum to 1. The weight
file holds **no census numbers** and depends only on CC BY inputs and the COD-AB boundaries, so
it is commercial-capable. The census GN total (rights unclear, D-030, non-commercial) is applied
in a separate step, `apportion`, whose output carries that restriction.

A GN whose cells hold no WorldPop mass falls back to equal shares and is flagged. Pixels whose
cell belongs to no GN (coast, water edge) are not dropped silently: their mass is reported.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import geopandas as gpd
import h3
import numpy as np
import pandas as pd
import rasterio

from slf import grid

WEIGHT_SOURCE = "worldpop_2025_cn_100m_r2025a"
METHOD_PIXELS = "worldpop_pixel_mass_by_cell_centre"
METHOD_EQUAL = "equal_share_no_pixel_mass"
INFORMATION_FLOOR = (
    "100 m WorldPop cells; the population information inside a GN division is WorldPop's "
    "modelled pattern, the GN total is the 2024 census figure"
)
DATA_NATURE = "modelled_estimate"
DERIVED_BY = "apportion_weighted"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pixel_mass_by_cell(tif: Path, resolution: int, band_rows: int = 512) -> dict[str, float]:
    """Sum WorldPop pixel values into the H3 cell that holds each pixel centre."""
    mass: dict[str, float] = {}
    with rasterio.open(tif) as src:
        nodata = src.nodata
        transform = src.transform
        for row0 in range(0, src.height, band_rows):
            rows = min(band_rows, src.height - row0)
            window = rasterio.windows.Window(0, row0, src.width, rows)  # type: ignore[attr-defined]
            values = src.read(1, window=window)
            keep = values > 0
            if nodata is not None:
                keep &= values != nodata
            keep &= np.isfinite(values)
            r_idx, c_idx = np.nonzero(keep)
            if r_idx.size == 0:
                continue
            xs = transform.c + (c_idx + 0.5) * transform.a
            ys = transform.f + (r_idx + row0 + 0.5) * transform.e
            vals = values[r_idx, c_idx].astype("float64")
            for lon, lat, value in zip(xs.tolist(), ys.tolist(), vals.tolist(), strict=True):
                cell = h3.latlng_to_cell(lat, lon, resolution)
                mass[cell] = mass.get(cell, 0.0) + value
    return mass


def weight_rows(cells: list[grid.Row], mass: dict[str, float]) -> Any:
    """Normalise cell mass within each GN. Weights per GN sum to 1."""
    raw: Any = pd.DataFrame(cells)
    frame: Any = raw[["geography_id", "h3", "method"]].rename(columns={"method": "cell_assignment"})
    frame["raw_mass"] = frame["h3"].map(mass).fillna(0.0)
    total: Any = frame.groupby("geography_id")["raw_mass"].transform("sum")
    count: Any = frame.groupby("geography_id")["h3"].transform("size")
    has_mass: Any = total > 0
    frame["weight"] = np.where(
        has_mass, frame["raw_mass"] / total.where(has_mass, 1.0), 1.0 / count
    )
    frame["method"] = np.where(has_mass, METHOD_PIXELS, METHOD_EQUAL)
    frame["weight_source"] = WEIGHT_SOURCE
    frame["information_floor"] = INFORMATION_FLOOR
    frame["data_nature"] = DATA_NATURE
    return frame


def to_parent(weights: Any, resolution: int) -> Any:
    """Coarser view: sum child weights into parent cells, per GN (weights still sum to 1)."""
    coarse: Any = weights.assign(h3=[h3.cell_to_parent(str(c), resolution) for c in weights["h3"]])
    keys = ["geography_id", "h3"]
    out: Any = coarse.groupby(keys, as_index=False).agg(
        weight=("weight", "sum"),
        raw_mass=("raw_mass", "sum"),
        method=("method", "first"),
        cell_assignment=("cell_assignment", "first"),
        weight_source=("weight_source", "first"),
        information_floor=("information_floor", "first"),
        data_nature=("data_nature", "first"),
    )
    return out


def apportion(weights: Any, totals: Any) -> Any:
    """GN totals spread over cells (`apportion_weighted`); sums back to each GN total."""
    out: Any = weights[["geography_id", "h3", "weight"]].copy()
    out["value"] = out["geography_id"].map(totals) * out["weight"]
    return out[out["value"].notna()]


def qa_tables(weights: Any, apportioned: Any, totals: Any, mass_all: float) -> dict[str, Any]:
    wsum: Any = weights.groupby("geography_id")["weight"].sum()
    asum: Any = apportioned.groupby("geography_id")["value"].sum()
    both: Any = pd.concat([totals.rename("total"), asum.rename("sum")], axis=1).dropna(
        subset=["total"]
    )
    both["sum"] = both["sum"].fillna(0.0)
    both["abs_residual"] = (both["sum"] - both["total"]).abs()
    no_weight_gn = sorted(weights.loc[weights["method"] == METHOD_EQUAL, "geography_id"].unique())
    zero_cells = int((weights["raw_mass"] == 0).sum())
    kept: Any = float(weights["raw_mass"].sum())
    return {
        "gn_in_grid": int(wsum.size),
        "max_weight_sum_error": float(abs(wsum - 1.0).max()),
        "gn_with_census_total": int(both.shape[0]),
        "gn_total_without_cells": sorted(set(totals.index) - set(wsum.index)),
        "gn_cells_without_total": sorted(set(wsum.index) - set(totals.index)),
        "census_total_sum": float(both["total"].sum()),
        "apportioned_sum": float(both["sum"].sum()),
        "max_abs_residual_people": float(both["abs_residual"].max()),
        "gn_residual_over_1e-6": int((both["abs_residual"] > 1e-6).sum()),
        "cells": len(weights),
        "cells_no_weight": zero_cells,
        "cells_no_weight_share": zero_cells / len(weights),
        "gn_equal_share_fallback": no_weight_gn,
        "worldpop_mass_in_grid": kept,
        "worldpop_mass_total": mass_all,
        "worldpop_mass_outside_any_gn": mass_all - kept,
        "worldpop_mass_outside_share": (mass_all - kept) / mass_all if mass_all else 0.0,
    }


def build(
    spine_dir: Path,
    tif: Path,
    census_parquet: Path,
    out_dir: Path,
    resolutions: tuple[int, ...] = (10, 9),
) -> dict[str, Any]:
    versions: Any = gpd.GeoDataFrame(gpd.read_parquet(spine_dir / "geography_versions.geoparquet"))
    census: Any = pd.read_parquet(
        census_parquet, columns=["indicator_id", "geography_id", "period", "value"]
    )
    pop: Any = census[(census["indicator_id"] == "population_total") & (census["period"] == "2024")]
    gn_ids: Any = set(versions.loc[versions["level"] == 4, "geography_id"].astype(str))
    totals: Any = pop.groupby("geography_id")["value"].first().astype(float)
    totals: Any = totals[totals.index.isin(gn_ids)]
    finest = max(resolutions)
    cells = grid.gn_cells(versions, finest)
    mass = pixel_mass_by_cell(tif, finest)
    mass_all: Any = float(sum(mass.values()))
    out_dir.mkdir(parents=True, exist_ok=True)
    summary: dict[str, Any] = {
        "weight_source": WEIGHT_SOURCE,
        "raster": tif.name,
        "raster_sha256": _sha256(tif),
        "census_input": census_parquet.name,
        "census_input_sha256": _sha256(census_parquet),
        "information_floor": INFORMATION_FLOOR,
        "data_nature": DATA_NATURE,
        "derived_by": DERIVED_BY,
        "resolutions": {},
    }
    weights: Any = weight_rows(cells, mass)
    for resolution in sorted(resolutions, reverse=True):
        view: Any = weights if resolution == finest else to_parent(weights, resolution)
        apportioned: Any = apportion(view, totals)
        report: Any = qa_tables(view, apportioned, totals, mass_all)
        view.to_parquet(
            out_dir / f"gn_h3r{resolution}_popweights_{grid.VINTAGE}.parquet", index=False
        )
        apportioned.to_parquet(
            out_dir / f"gn_h3r{resolution}_population_2024_NONCOMMERCIAL.parquet", index=False
        )
        summary["resolutions"][str(resolution)] = report
        if resolution == finest:
            per_gn: Any = pd.concat(
                [
                    totals.rename("census_total"),
                    apportioned.groupby("geography_id")["value"].sum().rename("cell_sum"),
                    view.groupby("geography_id")["weight"].sum().rename("weight_sum"),
                    view.groupby("geography_id")["h3"].size().rename("cells"),
                    (view["raw_mass"] > 0)
                    .groupby(view["geography_id"])
                    .sum()
                    .rename("cells_with_mass"),
                    view.groupby("geography_id")["raw_mass"].sum().rename("worldpop_2025_in_cells"),
                ],
                axis=1,
            )
            per_gn["residual"] = per_gn["cell_sum"] - per_gn["census_total"]
            per_gn.index.name = "geography_id"
            per_gn.to_csv(out_dir / "per_gn_sum_check.csv")
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary
