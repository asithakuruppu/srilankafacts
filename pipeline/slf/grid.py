"""Analytic grid (D-014, G07): H3 cells over the GN divisions and GN-to-hex weights.

The grid is a derived fabric for moving GN counts onto small cells, for drawn and radius
areas. It carries no new information: a GN count spread over its cells is a
`modelled_estimate` whose information floor stays the GN division (D-017). Weights here are
by area: every cell of a GN gets the same share. A population-weighted source is a later
step and needs its own rights check and completeness report (G07 steps 1 to 4).

Cells are assigned by centroid: a cell belongs to the GN that contains its centre, so each
cell has one GN and the cells of all GNs do not overlap. A GN too small to contain any cell
centre gets the cell under its label point (`label_point_fallback`), so no GN is dropped.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

import geopandas as gpd
import h3
import pandas as pd

RESOLUTION = 9
VINTAGE = "2024"
METHOD_CENTROID = "h3_cell_centroid_in_gn"
METHOD_FALLBACK = "label_point_fallback"
WEIGHT_SOURCE = "area_equal_share"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


Row = dict[str, Any]


def gn_cells(versions: gpd.GeoDataFrame, resolution: int = RESOLUTION) -> list[Row]:
    """One row per (GN, cell) with an equal-share weight; weights per GN sum to 1."""
    frame = pd.DataFrame(versions[versions["level"] == 4])
    rows: list[Row] = []
    for record in cast(list[Row], frame.to_dict("records")):
        gid = str(record["geography_id"])
        cells = sorted(h3.geo_to_cells(record["geometry"], resolution))
        method = METHOD_CENTROID
        if not cells:
            cells = [
                h3.latlng_to_cell(
                    float(record["label_lat"]), float(record["label_lon"]), resolution
                )
            ]
            method = METHOD_FALLBACK
        weight = 1.0 / len(cells)
        rows += [
            {
                "geography_id": gid,
                "h3": cell,
                "weight": weight,
                "method": method,
                "weight_source": WEIGHT_SOURCE,
            }
            for cell in cells
        ]
    return rows


def to_cells(values: dict[str, float], weights: list[Row]) -> list[Row]:
    """Spread GN counts over cells (`apportion_weighted`): geography_id, h3, value."""
    return [
        {
            "geography_id": row["geography_id"],
            "h3": row["h3"],
            "value": values[row["geography_id"]] * row["weight"],
        }
        for row in weights
        if row["geography_id"] in values
    ]


def to_gn(cell_values: list[Row]) -> dict[str, float]:
    """Sum cell shares back to their GN (`aggregate_sum`); the inverse of `to_cells`."""
    totals: dict[str, float] = {}
    for row in cell_values:
        totals[row["geography_id"]] = totals.get(row["geography_id"], 0.0) + float(row["value"])
    return totals


def build(spine_dir: Path, out_dir: Path, resolution: int = RESOLUTION) -> dict[str, Any]:
    source = spine_dir / "geography_versions.geoparquet"
    versions = gpd.GeoDataFrame(gpd.read_parquet(source))
    weights = gn_cells(versions, resolution)
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"gn_h3r{resolution}_weights_{VINTAGE}.parquet"
    pd.DataFrame(weights).to_parquet(target, index=False)
    sums: dict[str, float] = {}
    counts: dict[str, int] = {}
    owners: dict[str, set[str]] = {}
    fallback: set[str] = set()
    for row in weights:
        gid = row["geography_id"]
        sums[gid] = sums.get(gid, 0.0) + row["weight"]
        counts[gid] = counts.get(gid, 0) + 1
        owners.setdefault(row["h3"], set()).add(gid)
        if row["method"] == METHOD_FALLBACK:
            fallback.add(gid)
    summary = {
        "resolution": resolution,
        "average_cell_km2": h3.average_hexagon_area(resolution, "km^2"),
        "gn_divisions": len(sums),
        "rows": len(weights),
        "distinct_cells": len(owners),
        "max_weight_sum_error": max(abs(value - 1.0) for value in sums.values()),
        "gn_with_one_cell": sum(1 for value in counts.values() if value == 1),
        "gn_by_label_point_fallback": len(fallback),
        "cells_shared_by_several_gn": sum(1 for value in owners.values() if len(value) > 1),
        "weight_source": WEIGHT_SOURCE,
        "data_nature": "modelled_estimate",
        "information_unit": f"gn-{VINTAGE}",
        "source": source.name,
        "source_sha256": _sha256(source),
        "output": target.name,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (out_dir / "qa.md").write_text(
        "\n".join(
            [
                f"# Analytic grid QA (H3 resolution {resolution}, vintage {VINTAGE})",
                "",
                "| Measure | Value |",
                "|---|---|",
                *[f"| {key} | {value} |" for key, value in summary.items()],
                "",
                "Weights are equal shares by area. Values moved onto cells are modelled",
                "estimates; their information floor is the GN division.",
                "",
            ]
        )
    )
    return summary


def web_files(spine_dir: Path, weights_path: Path, out_dir: Path) -> dict[str, Any]:
    """Per-district cell centres for the browser's area tool: [lon, lat, index of GN]."""
    geographies = pd.read_parquet(spine_dir / "geographies.parquet")
    parent = {
        str(row["geography_id"]): (None if pd.isna(row["parent_id"]) else str(row["parent_id"]))
        for row in cast(list[dict[str, Any]], geographies.to_dict("records"))
    }
    weights = cast(list[Row], pd.read_parquet(weights_path).to_dict("records"))
    resolution = int(h3.get_resolution(str(weights[0]["h3"])))
    by_district: dict[str, dict[str, list[str]]] = {}
    for row in weights:
        gid = str(row["geography_id"])
        ds = parent.get(gid)
        district = parent.get(ds) if ds else None
        if district is None:
            continue
        by_district.setdefault(district, {}).setdefault(gid, []).append(str(row["h3"]))
    total = 0
    for district, gns in sorted(by_district.items()):
        ids = sorted(gns)
        cells_out: list[list[float]] = []
        for index, gid in enumerate(ids):
            for cell in sorted(gns[gid]):
                lat, lon = h3.cell_to_latlng(cell)
                cells_out.append([round(lon, 5), round(lat, 5), index])
        path = out_dir / "grid" / f"{district}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(
                {"resolution": resolution, "gn": ids, "cells": cells_out}, separators=(",", ":")
            )
            + "\n"
        )
        total += path.stat().st_size
    return {
        "available": True,
        "resolution": resolution,
        "average_cell_km2": h3.average_hexagon_area(resolution, "km^2"),
        "districts": len(by_district),
        "bytes": total,
        "weight_source": WEIGHT_SOURCE,
        "method": (
            "H3 cell centres, each tagged with the GN division that contains it. A GN count "
            "is shared equally among its cells; an area's estimate is the sum over the cells "
            "inside it. Modelled estimate; information floor: GN division."
        ),
        "source_sha256": _sha256(weights_path),
    }
