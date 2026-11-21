"""Bridge methods between spatial fabrics (spatial-first-analytics.md §4.3).

Every function returns rows that stamp `derived_by` (the method id) and `data_nature`. Moving a
value to a finer or partial support is always a `modelled_estimate`; summing whole GNs keeps the
input's nature and is flagged `exact`. Nothing is dropped silently: a unit with a missing member
is returned with `value: None` and the missing GN listed.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import shapely
from shapely.geometry.base import BaseGeometry
from shapely.strtree import STRtree

from slf import grid

Row = dict[str, Any]
Members = Mapping[str, Mapping[str, float]]  # unit -> {gn: share of that GN inside the unit}

AGGREGATE_SUM = "aggregate_sum"
AGGREGATE_RECOMPUTE = "aggregate_recompute"
APPORTION_WEIGHTED = "apportion_weighted"
POINT_IN_POLYGON = "point_in_polygon"
ZONAL_STATS = "zonal_stats"


def _combine(
    values: Mapping[str, float], gns: Mapping[str, float]
) -> tuple[float | None, list[str]]:
    missing = sorted(gid for gid in gns if gid not in values)
    if missing:
        return None, missing
    return sum(values[gid] * share for gid, share in gns.items()), []


def aggregate_sum(
    values: Mapping[str, float],
    members: Members,
    input_nature: str = "census_count",
) -> list[Row]:
    """GN values to composed units. Exact when every member GN lies wholly inside the unit."""
    rows: list[Row] = []
    for unit, gns in sorted(members.items()):
        total, missing = _combine(values, gns)
        whole = all(share == 1.0 for share in gns.values())
        rows.append(
            {
                "geography_id": unit,
                "value": total,
                "missing_gn": missing,
                "exact": whole and not missing,
                "derived_by": AGGREGATE_SUM,
                "data_nature": input_nature if whole else "modelled_estimate",
            }
        )
    return rows


def aggregate_recompute(
    numerators: Mapping[str, float],
    denominators: Mapping[str, float],
    members: Members,
    scale: float = 1.0,
    input_nature: str = "census_count",
) -> list[Row]:
    """Rates are never averaged: sum numerator and denominator, then divide."""
    rows: list[Row] = []
    for unit, gns in sorted(members.items()):
        num, miss_n = _combine(numerators, gns)
        den, miss_d = _combine(denominators, gns)
        missing = sorted(set(miss_n) | set(miss_d))
        value = None if num is None or den is None or den == 0 else scale * num / den
        whole = all(share == 1.0 for share in gns.values())
        rows.append(
            {
                "geography_id": unit,
                "value": value,
                "numerator": num,
                "denominator": den,
                "missing_gn": missing,
                "exact": whole and not missing and value is not None,
                "derived_by": AGGREGATE_RECOMPUTE,
                "data_nature": input_nature if whole else "modelled_estimate",
            }
        )
    return rows


def apportion_weighted(
    values: Mapping[str, float], weights: Sequence[Row], weight_source: str
) -> list[Row]:
    """GN values to cells, in proportion to named weights. Always a modelled estimate."""
    return [
        {
            **row,
            "weight_source": weight_source,
            "derived_by": APPORTION_WEIGHTED,
            "data_nature": "modelled_estimate",
        }
        for row in grid.to_cells(dict(values), list(weights))
    ]


def point_in_polygon(
    points: Sequence[tuple[str, float, float]],
    polygons: Mapping[str, BaseGeometry],
    vintage: str,
    border_tolerance: float = 1e-5,
) -> list[Row]:
    """Assign each (id, lon, lat) to the polygon containing it; record the boundary vintage.

    A point within `border_tolerance` degrees of a polygon edge is flagged `on_border`; a point
    inside none is returned with `geography_id: None` rather than dropped.
    """
    ids = sorted(polygons)
    tree = STRtree([polygons[i] for i in ids])
    rows: list[Row] = []
    for pid, lon, lat in points:
        point = shapely.Point(lon, lat)
        hit = None
        on_border = False
        for index in tree.query(point.buffer(border_tolerance)):
            geom = polygons[ids[int(index)]]
            if hit is None and geom.covers(point):
                hit = ids[int(index)]
            if geom.boundary.distance(point) <= border_tolerance:
                on_border = True
        rows.append(
            {
                "point_id": pid,
                "geography_id": hit,
                "boundary_vintage": vintage,
                "on_border": on_border,
                "derived_by": POINT_IN_POLYGON,
                "data_nature": "administrative_count",
            }
        )
    return rows


def zonal_stats(
    cell_values: Mapping[str, float],
    cell_zone: Mapping[str, str],
    statistic: str,
    source_licence: str,
) -> list[Row]:
    """Cell (raster or hex) values to zones: `sum` or `mean`; the source's licence is recorded."""
    if statistic not in {"sum", "mean"}:
        raise ValueError(f"unsupported statistic {statistic!r}")
    total: dict[str, float] = {}
    count: dict[str, int] = {}
    for cell, value in cell_values.items():
        zone = cell_zone.get(cell)
        if zone is None:
            continue
        total[zone] = total.get(zone, 0.0) + value
        count[zone] = count.get(zone, 0) + 1
    return [
        {
            "geography_id": zone,
            "value": total[zone] if statistic == "sum" else total[zone] / count[zone],
            "cells": count[zone],
            "statistic": statistic,
            "source_licence": source_licence,
            "derived_by": ZONAL_STATS,
            "data_nature": "modelled_estimate",
        }
        for zone in sorted(total)
    ]
