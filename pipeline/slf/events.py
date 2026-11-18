"""Events layer and place timelines ("Living Sri Lanka", D-020) from held event datasets.

- Floods, 26 Nov to 2 Dec 2025 (Cyclone Ditwah): UNOSAT's multi-sensor flood extent, with
  permanent water removed by UNOSAT, intersected with every GN division in EPSG:5235.
  Flooded area and its share of the place's area, summed up the hierarchy. Satellite
  mapping misses flooding under cloud or tree cover; the figure is a lower bound.
- Active fires, VIIRS S-NPP (FIRMS archive, standard quality): detections of type 0
  (presumed vegetation fire) with nominal or high confidence, counted by DS division and
  district for each complete calendar year 2013 to 2025. A detection is a 375 m pixel with a
  hot spot, not a count of fires.
- Storm tracks (IBTrACS v04r01): each storm whose 3-hourly track line passes within 50 km of
  a district's boundary, with the strongest WMO wind reported on that stretch.

Points join places by point-in-polygon on the spine's full GN polygons; nothing joins by
name. Event rows use the same ledger columns as other builds.
"""

from __future__ import annotations

import io
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import shapely

CRS_METRIC = 5235
FIRE_YEARS = range(2013, 2026)
MODIS_FIRE_YEARS = range(2001, 2026)  # the MODIS archive starts 2000-12-01
MODIS_MIN_CONFIDENCE = 30  # FIRMS classes: low 0-29, nominal 30-79, high 80-100
STORM_BUFFER_M = 50_000


@dataclass(frozen=True)
class Spec:
    id: str
    name: str
    dataset: str
    unit: str
    decimals: int
    measure_type: str
    definition: str
    data_nature: str
    floor: str
    higher_is: str = "neutral"
    group: str = "Events"


SPECS: list[Spec] = [
    Spec(
        "flood_area_2025_ditwah",
        "Area flooded, Cyclone Ditwah (26 Nov to 2 Dec 2025)",
        "unosat-ditwah-flood-2025",
        "hectares",
        1,
        "count",
        "Area inside UNOSAT's satellite-mapped flood extent for 26 November to 2 December 2025, "
        "excluding permanent water. A lower bound: cloud and tree cover hide some flooding.",
        "modelled_estimate",
        "satellite flood extent (10 m to 30 m)",
    ),
    Spec(
        "flood_share_2025_ditwah",
        "Share of area flooded, Cyclone Ditwah (2025)",
        "unosat-ditwah-flood-2025",
        "percent",
        2,
        "share",
        "Mapped flooded area as a share of the place's area (EPSG:5235).",
        "modelled_estimate",
        "satellite flood extent (10 m to 30 m)",
    ),
    Spec(
        "fire_detections",
        "Active fire detections (VIIRS), per year",
        "nasa-firms-active-fire-lk",
        "detections",
        0,
        "count",
        "VIIRS S-NPP 375 m pixels flagged as presumed vegetation fire with nominal or high "
        "confidence (NASA FIRMS archive). A detection is a hot pixel, not a fire count.",
        "modelled_estimate",
        "grid-375m",
    ),
    Spec(
        "fire_detections_modis",
        "Active fire detections (MODIS), per year",
        "nasa-firms-active-fire-lk",
        "detections",
        0,
        "count",
        "MODIS Terra and Aqua 1 km pixels (Collection 6.1) flagged as presumed vegetation fire "
        "with confidence 30 or more (NASA FIRMS archive), per calendar year. A detection is a hot "
        "pixel, not a fire count; the 1 km pixel and the different sensor mean counts are not "
        "comparable with the VIIRS indicator.",
        "modelled_estimate",
        "grid-1km",
    ),
]
SPEC_BY_ID = {spec.id: spec for spec in SPECS}


def _latest(raw: Path, source: str, dataset: str, pattern: str) -> tuple[Path, dict[str, Any]]:
    files = sorted((raw / source / dataset).glob(f"*/{pattern}"))
    if not files:
        raise FileNotFoundError(f"{source}/{dataset}/*/{pattern}")
    path = files[-1]
    return path, json.loads(path.with_name(path.name + ".meta.json").read_text())


def _hierarchy(spine_dir: Path) -> tuple[gpd.GeoDataFrame, dict[str, str | None], dict[str, int]]:
    geographies = pd.read_parquet(spine_dir / "geographies.parquet")
    records = cast(list[dict[str, Any]], geographies.to_dict("records"))
    parent = {
        str(r["geography_id"]): (None if pd.isna(r["parent_id"]) else str(r["parent_id"]))
        for r in records
    }
    level = {str(r["geography_id"]): int(r["level"]) for r in records}
    versions = gpd.GeoDataFrame(gpd.read_parquet(spine_dir / "geography_versions.geoparquet"))
    return versions, parent, level


def _ancestors(gid: str, parent: dict[str, str | None]) -> list[str]:
    chain = [gid]
    current = parent.get(gid)
    while current:
        chain.append(current)
        current = parent.get(current)
    return chain


def _row(
    spec: Spec,
    gid: str,
    period: str,
    value: float,
    meta: dict[str, Any],
    locator: str,
    start: str,
    end: str,
) -> dict[str, Any]:
    return {
        "claim_id": f"{spec.dataset}:{gid}:{spec.id}:{period}",
        "indicator_id": spec.id,
        "geography_id": gid,
        "period": period,
        "time_start": start,
        "time_end": end,
        "value": value,
        "value_status": "normal",
        "unit": spec.unit,
        "information_footprint_ref": spec.floor,
        "data_nature": spec.data_nature,
        "verification": "machine_extracted",
        "dataset_id": spec.dataset,
        "snapshot_sha256": meta["sha256"],
        "source_url": meta.get("url"),
        "source_locator": locator,
        "breakdown": None,
    }


def floods(
    raw: Path, versions: gpd.GeoDataFrame, parent: dict[str, str | None]
) -> list[dict[str, Any]]:
    path, meta = _latest(raw, "unosat", "unosat-ditwah-flood-2025", "FL20251128LKA_gdb.zip")
    layer = "Multisensors_20251126_20251202_FloodExtent_SriLanka"
    gdb = f"/vsizip/{path}/FL20251128LKA.gdb"
    flood = pyogrio.read_dataframe(gdb, layer=layer)
    flood = gpd.GeoDataFrame(flood, geometry="geometry").set_crs(4326, allow_override=True)
    # Flood parts, indexed; each GN is intersected only with the parts its box touches.
    parts = shapely.get_parts(
        shapely.force_2d(np.asarray(flood.to_crs(CRS_METRIC).geometry.values))
    )
    parts = shapely.make_valid(parts[~shapely.is_empty(parts)])
    gn = gpd.GeoDataFrame(versions[versions["level"] == 4]).to_crs(CRS_METRIC)
    ids = [str(v) for v in gn["geography_id"]]
    geoms = np.asarray(gn.geometry.values, dtype=object)
    tree = shapely.STRtree(parts)
    gn_index, part_index = tree.query(geoms, predicate="intersects")
    pieces = shapely.area(shapely.intersection(geoms[gn_index], parts[part_index]))
    flooded = np.bincount(gn_index, weights=pieces, minlength=len(ids))
    areas = shapely.area(geoms)
    totals: dict[str, list[float]] = {}
    for gid, wet, area in zip(ids, flooded, areas, strict=True):
        for place in _ancestors(gid, parent):
            item = totals.setdefault(place, [0.0, 0.0])
            item[0] += float(wet)
            item[1] += float(area)
    rows = []
    locator = f"{path.name}, layer {layer}, intersected with GN polygons in EPSG:5235 and summed"
    for gid, (wet, area) in sorted(totals.items()):
        rows.append(
            _row(
                SPEC_BY_ID["flood_area_2025_ditwah"],
                gid,
                "2025",
                round(wet / 1e4, 2),
                meta,
                locator,
                "2025-11-26",
                "2025-12-02",
            )
        )
        rows.append(
            _row(
                SPEC_BY_ID["flood_share_2025_ditwah"],
                gid,
                "2025",
                round(100 * wet / area, 3) if area else 0.0,
                meta,
                locator,
                "2025-11-26",
                "2025-12-02",
            )
        )
    return rows


def fires(
    raw: Path,
    versions: gpd.GeoDataFrame,
    parent: dict[str, str | None],
    level: dict[str, int],
    sensor: str = "viirs",
) -> list[dict[str, Any]]:
    modis = sensor == "modis"
    indicator = "fire_detections_modis" if modis else "fire_detections"
    years = MODIS_FIRE_YEARS if modis else FIRE_YEARS
    path, meta = _latest(
        raw,
        "nasa-firms",
        "nasa-firms-active-fire-lk",
        "DL_FIRE_M-C61_*.zip" if modis else "DL_FIRE_SV-C2_*.zip",
    )
    with zipfile.ZipFile(path) as archive:
        name = next(n for n in archive.namelist() if n.startswith("fire_archive_"))
        table = pd.read_csv(io.BytesIO(archive.read(name)))
    if modis:
        confidence = cast(pd.Series, pd.to_numeric(table["confidence"], errors="coerce"))
        table = pd.DataFrame(table[(table["type"] == 0) & (confidence >= MODIS_MIN_CONFIDENCE)])
        rule = f"type 0, confidence >= {MODIS_MIN_CONFIDENCE}, points in place"
    else:
        table = pd.DataFrame(table[(table["type"] == 0) & table["confidence"].isin(["n", "h"])])
        rule = "type 0, confidence n or h, points in place"
    table["year"] = table["acq_date"].astype(str).str[:4].astype(int)
    table = pd.DataFrame(table[table["year"].isin(list(years))])
    points = gpd.GeoDataFrame(
        {"year": table["year"].to_numpy()},
        geometry=gpd.points_from_xy(table["longitude"], table["latitude"]),
        crs=4326,
    )
    gn = gpd.GeoDataFrame(versions[versions["level"] == 4][["geography_id", "geometry"]])
    joined = gpd.sjoin(points, gn, how="inner", predicate="within")
    counts: dict[tuple[str, int], int] = {}
    for gid, year in zip(joined["geography_id"].astype(str), joined["year"], strict=True):
        for place in _ancestors(gid, parent):
            if level.get(place, 9) <= 3:
                counts[(place, int(year))] = counts.get((place, int(year)), 0) + 1
    places = {p for p, _ in counts} | {
        p for p, lv in level.items() if lv <= 3 and p in set(parent) | {"LK"}
    }
    rows = []
    for place in sorted(places):
        for year in years:
            rows.append(
                _row(
                    SPEC_BY_ID[indicator],
                    place,
                    str(year),
                    float(counts.get((place, year), 0)),
                    meta,
                    f"{name} in {path.name}: {rule}",
                    f"{year}-01-01",
                    f"{year}-12-31",
                )
            )
    return rows


def storms(
    raw: Path, versions: gpd.GeoDataFrame
) -> tuple[dict[str, list[list[Any]]], dict[str, Any]]:
    path, meta = _latest(raw, "noaa-ncei", "ibtracs-storm-tracks", "ibtracs_all_list_*.csv")
    table = pd.read_csv(path, skiprows=[1], low_memory=False)
    table["wind"] = pd.to_numeric(table["WMO_WIND"], errors="coerce")
    table["LAT"] = pd.to_numeric(table["LAT"], errors="coerce")
    table["LON"] = pd.to_numeric(table["LON"], errors="coerce")
    table = pd.DataFrame(table.dropna(subset=["LAT", "LON"]))
    districts = gpd.GeoDataFrame(versions[versions["level"] == 2]).to_crs(CRS_METRIC)
    zones = {
        str(gid): shapely.buffer(geom, STORM_BUFFER_M)
        for gid, geom in zip(districts["geography_id"], districts.geometry, strict=True)
    }
    passes: dict[str, list[list[Any]]] = {}
    for sid, track in table.sort_values("ISO_TIME").groupby("SID"):
        pts = gpd.GeoSeries(gpd.points_from_xy(track["LON"], track["LAT"]), crs=4326).to_crs(
            CRS_METRIC
        )
        coords = [(p.x, p.y) for p in pts]
        line = shapely.LineString(coords) if len(coords) > 1 else shapely.Point(coords[0])
        winds = track["wind"].to_numpy()
        times = track["ISO_TIME"].astype(str).to_numpy()
        for gid, zone in zones.items():
            if not line.intersects(zone):
                continue
            near = [i for i, p in enumerate(pts) if zone.distance(p) <= STORM_BUFFER_M]
            near_winds = [w for w in (winds[i] for i in near) if not np.isnan(w)]
            first = times[near[0]] if near else times[0]
            passes.setdefault(gid, []).append(
                [str(sid), first[:10], None if not near_winds else int(max(near_winds))]
            )
    for gid in passes:
        passes[gid].sort(key=lambda item: item[1])
    return passes, {
        "dataset_id": "ibtracs-storm-tracks",
        "snapshot_sha256": meta["sha256"],
        "file": path.name,
        "method": f"track line within {STORM_BUFFER_M // 1000} km of the district boundary; "
        "wind is the highest WMO_WIND (knots) at track points inside that zone, if reported",
    }


def build(raw_root: Path, spine_dir: Path, out_dir: Path) -> dict[str, Any]:
    versions, parent, level = _hierarchy(spine_dir)
    rows: list[dict[str, Any]] = []
    failed: list[str] = []
    for name, step in (
        ("floods", lambda: floods(raw_root, versions, parent)),
        ("fires", lambda: fires(raw_root, versions, parent, level)),
        ("fires_modis", lambda: fires(raw_root, versions, parent, level, "modis")),
    ):
        try:
            rows += step()
        except FileNotFoundError as missing:
            failed.append(f"{name}: not held ({missing})")
    out_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(out_dir / "observations.parquet", index=False)
    storm_summary: dict[str, Any] = {}
    try:
        passes, storm_summary = storms(raw_root, versions)
        (out_dir / "storms.json").write_text(
            json.dumps(
                {
                    **storm_summary,
                    "row_format": ["storm id", "first date near", "max wind kt"],
                    "districts": passes,
                },
                separators=(",", ":"),
            )
            + "\n"
        )
        storm_summary["districts_with_passes"] = len(passes)
        storm_summary["passes"] = sum(len(v) for v in passes.values())
    except FileNotFoundError as missing:
        failed.append(f"storms: not held ({missing})")
    frame = pd.DataFrame(rows)
    summary = {
        "rows": len(rows),
        "indicators": sorted(set(frame["indicator_id"])) if rows else [],
        "storms": storm_summary,
        "not_held": failed,
    }
    if rows:
        national = pd.DataFrame(frame[frame["geography_id"] == "LK"])
        summary["national"] = {
            f"{r['indicator_id']}:{r['period']}": r["value"]
            for r in cast(list[dict[str, Any]], national.to_dict("records"))
        }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary
