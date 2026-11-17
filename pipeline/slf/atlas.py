"""Web atlas bundle: map geometry with shared borders, neighbour graph, profile space, change.

Everything here is derived for display from a release and the spine build. Nothing is a new
fact: geometry is a simplified copy of the spine's COD-AB polygons, the neighbour graph is the
spine's adjacency tables, the profile block is the profile build, and the change block is the
history build. `manifest.json` records each input and method.

Geometry method: the GN divisions form a valid polygon coverage. They are simplified *as a
coverage* (shared edges stay identical on both sides), then dissolved up the hierarchy, so
provinces, districts, DS and GN divisions nest exactly and no gaps or overlaps appear between
neighbours. Borders are written once, as a line mesh ranked by the highest level they divide
(0 coast, 1 province, 2 district, 3 DS, 4 GN), so the map never draws a shared border twice.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from shapely.geometry.base import BaseGeometry

CRS_METRIC = 5235
CRS_PUBLISH = 4326
OVERVIEW_TOLERANCE_M = 150.0
DETAIL_TOLERANCE_M = 30.0
DECIMALS = 5
CLUSTER_CLASSES = ("high_high", "low_low", "high_low", "low_high")
LEVEL_NAMES = {0: "country", 1: "province", 2: "district", 3: "ds", 4: "gn"}


def _rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], frame.to_dict("records"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n")


def _publish(geoms: list[BaseGeometry] | np.ndarray) -> list[BaseGeometry]:
    """Reproject metric geometries to EPSG:4326 and round coordinates."""
    series = gpd.GeoSeries(list(geoms), crs=CRS_METRIC).to_crs(CRS_PUBLISH)
    return [
        shapely.transform(geom, lambda coords: np.round(coords, DECIMALS)) for geom in series.values
    ]


def _feature(geom: BaseGeometry, properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "Feature",
        "properties": properties,
        "geometry": json.loads(shapely.to_geojson(geom)),
    }


def _collection(features: list[dict[str, Any]]) -> dict[str, Any]:
    return {"type": "FeatureCollection", "features": features}


def _lines(geom: BaseGeometry) -> BaseGeometry:
    """Keep only the line parts of a geometry and merge them into long runs."""
    parts = [
        part
        for part in shapely.get_parts(geom)
        if part.geom_type in ("LineString", "MultiLineString") and not part.is_empty
    ]
    if not parts:
        return shapely.MultiLineString()
    return shapely.line_merge(shapely.union_all(parts))


def _borders(polygons: Sequence[BaseGeometry] | np.ndarray) -> BaseGeometry:
    """All borders of a set of polygons, each shared border once."""
    return shapely.union_all(shapely.boundary(np.asarray(polygons, dtype=object)))


def _dissolve(geoms: np.ndarray, keys: list[str]) -> dict[str, BaseGeometry]:
    frame = gpd.GeoDataFrame({"key": keys}, geometry=list(geoms), crs=CRS_METRIC)
    grouped = frame.dissolve(by="key")
    return {str(key): geom for key, geom in zip(grouped.index, grouped.geometry, strict=True)}


def _ranked_mesh(levels: Sequence[Sequence[BaseGeometry]]) -> list[BaseGeometry]:
    """Borders by rank: levels[0] is the country, then each finer level.

    Rank r holds the borders that divide units of level r but not of level r - 1.
    """
    ranked: list[BaseGeometry] = []
    coarser: BaseGeometry | None = None
    for polygons in levels:
        borders = _borders(polygons)
        ranked.append(_lines(borders if coarser is None else shapely.difference(borders, coarser)))
        coarser = borders
    return ranked


def _mesh_features(ranked: list[BaseGeometry], first_rank: int = 0) -> list[dict[str, Any]]:
    published = _publish(ranked)
    return [
        _feature(geom, {"rank": first_rank + offset})
        for offset, geom in enumerate(published)
        if not geom.is_empty
    ]


def build_geometry(spine_dir: Path, out_dir: Path) -> dict[str, Any]:
    geographies = pd.read_parquet(spine_dir / "geographies.parquet")
    versions = gpd.GeoDataFrame(gpd.read_parquet(spine_dir / "geography_versions.geoparquet"))
    parent = {
        str(row["geography_id"]): (None if pd.isna(row["parent_id"]) else str(row["parent_id"]))
        for row in _rows(geographies)
    }
    names = {
        str(row["geography_id"]): (None if pd.isna(row["name_en"]) else str(row["name_en"]))
        for row in _rows(geographies)
    }

    gn = versions[versions["level"] == 4].to_crs(CRS_METRIC)
    gn_ids = [str(value) for value in gn["geography_id"]]
    gn_full = np.asarray(gn.geometry.values, dtype=object)
    if not shapely.coverage_is_valid(gn_full):
        raise ValueError("GN polygons are not a valid coverage; refusing to simplify them.")
    ds_of = [str(parent[g]) for g in gn_ids]
    district_of_ds = {ds: str(parent[ds]) for ds in set(ds_of)}
    province_of_district = {d: str(parent[d]) for d in set(district_of_ds.values())}

    # Detail tier: simplify the GN coverage, then dissolve upwards.
    gn_fine = shapely.coverage_simplify(gn_full, DETAIL_TOLERANCE_M)
    ds_fine = _dissolve(gn_fine, ds_of)
    district_fine = _dissolve(
        np.asarray(list(ds_fine.values()), dtype=object),
        [district_of_ds[ds] for ds in ds_fine],
    )
    province_fine = _dissolve(
        np.asarray(list(district_fine.values()), dtype=object),
        [province_of_district[d] for d in district_fine],
    )
    country_fine = shapely.union_all(list(province_fine.values()))

    # Overview tier: dissolve full-resolution GNs to DS, simplify the DS coverage, dissolve up.
    ds_full = _dissolve(gn_full, ds_of)
    ds_ids = sorted(ds_full)
    ds_coarse_arr = shapely.coverage_simplify(
        np.asarray([ds_full[ds] for ds in ds_ids], dtype=object), OVERVIEW_TOLERANCE_M
    )
    ds_coarse = dict(zip(ds_ids, ds_coarse_arr, strict=True))
    district_coarse = _dissolve(ds_coarse_arr, [district_of_ds[ds] for ds in ds_ids])
    province_coarse = _dissolve(
        np.asarray(list(district_coarse.values()), dtype=object),
        [province_of_district[d] for d in district_coarse],
    )
    country_coarse = shapely.union_all(list(province_coarse.values()))

    # Overview files.
    ds_published = dict(zip(ds_ids, _publish([ds_coarse[ds] for ds in ds_ids]), strict=True))
    _dump(
        out_dir / "overview.geojson",
        _collection(
            [
                _feature(
                    geom,
                    {
                        "id": ds,
                        "ds": ds,
                        "district": district_of_ds[ds],
                        "province": province_of_district[district_of_ds[ds]],
                        "country": "LK",
                    },
                )
                for ds, geom in ds_published.items()
            ]
        ),
    )
    outline_items: list[tuple[str, int, BaseGeometry]] = [("LK", 0, country_coarse)]
    outline_items += [(key, 1, geom) for key, geom in sorted(province_coarse.items())]
    outline_items += [(key, 2, geom) for key, geom in sorted(district_coarse.items())]
    outline_published = _publish([item[2] for item in outline_items])
    _dump(
        out_dir / "outlines.geojson",
        _collection(
            [
                _feature(geom, {"id": key, "level": level})
                for (key, level, _), geom in zip(outline_items, outline_published, strict=True)
            ]
        ),
    )
    _dump(
        out_dir / "mesh.geojson",
        _collection(
            _mesh_features(
                _ranked_mesh(
                    [
                        [country_coarse],
                        list(province_coarse.values()),
                        list(district_coarse.values()),
                        list(ds_coarse.values()),
                    ]
                )
            )
        ),
    )

    # Detail files: national fine borders once, then one file per district.
    fine_ranked = _ranked_mesh(
        [[country_fine], list(province_fine.values()), list(district_fine.values())]
    )
    fine_outline_items: list[tuple[str, int, BaseGeometry]] = [("LK", 0, country_fine)]
    fine_outline_items += [(key, 1, geom) for key, geom in sorted(province_fine.items())]
    fine_outline_items += [(key, 2, geom) for key, geom in sorted(district_fine.items())]
    fine_outlines = _publish([item[2] for item in fine_outline_items])
    _dump(
        out_dir / "fine.json",
        {
            "mesh": _collection(_mesh_features(fine_ranked)),
            "outlines": _collection(
                [
                    _feature(geom, {"id": key, "level": level})
                    for (key, level, _), geom in zip(fine_outline_items, fine_outlines, strict=True)
                ]
            ),
        },
    )

    label = {
        str(row["geography_id"]): [
            round(float(row["label_lon"]), 5),
            round(float(row["label_lat"]), 5),
        ]
        for row in _rows(versions)
    }
    area = {
        str(row["geography_id"]): (
            None if pd.isna(row["area_km2"]) else round(float(row["area_km2"]), 3)
        )
        for row in _rows(versions)
    }
    gn_published = _publish(gn_fine)
    district_border_lines = _borders(list(district_fine.values()))
    detail_bytes = 0
    for district in sorted(district_fine):
        index = [i for i, ds in enumerate(ds_of) if district_of_ds[ds] == district]
        district_ds = sorted({ds_of[i] for i in index})
        ds_borders = _borders([ds_fine[ds] for ds in district_ds])
        gn_borders = _borders([gn_fine[i] for i in index])
        ranked = [
            _lines(shapely.difference(ds_borders, district_border_lines)),
            _lines(shapely.difference(gn_borders, ds_borders)),
        ]
        ds_outlines = _publish([ds_fine[ds] for ds in district_ds])
        payload = {
            "district": district,
            "gn": _collection(
                [
                    _feature(
                        gn_published[i],
                        {
                            "id": gn_ids[i],
                            "gn": gn_ids[i],
                            "ds": ds_of[i],
                            "district": district,
                            "province": province_of_district[district],
                            "country": "LK",
                        },
                    )
                    for i in index
                ]
            ),
            "outlines": _collection(
                [
                    _feature(geom, {"id": ds, "level": 3})
                    for ds, geom in zip(district_ds, ds_outlines, strict=True)
                ]
            ),
            "mesh": _collection(_mesh_features(ranked, first_rank=3)),
            "units": {
                gn_ids[i]: {
                    "n": names.get(gn_ids[i]),
                    "c": label.get(gn_ids[i]),
                    "a": area.get(gn_ids[i]),
                }
                for i in index
            },
        }
        target = out_dir / "detail" / f"{district}.json"
        _dump(target, payload)
        detail_bytes += target.stat().st_size

    # Units above GN: name, level, parent, label point, bounding box, area.
    units: dict[str, Any] = {}
    boxes: dict[str, BaseGeometry] = {"LK": country_coarse, **province_coarse, **district_coarse}
    boxes.update(ds_coarse)
    box_keys = sorted(boxes)
    for key, geom in zip(box_keys, _publish([boxes[k] for k in box_keys]), strict=True):
        level = int(geographies.loc[geographies["geography_id"] == key, "level"].iloc[0])
        units[key] = {
            "n": names.get(key),
            "l": level,
            "p": parent.get(key),
            "c": label.get(key),
            "b": [round(float(v), 4) for v in geom.bounds],
            "a": area.get(key),
        }
    without_geometry = sorted(
        str(row["geography_id"])
        for row in _rows(geographies)
        if int(row["level"]) < 4 and str(row["geography_id"]) not in units
    )
    for key in without_geometry:
        level = int(geographies.loc[geographies["geography_id"] == key, "level"].iloc[0])
        units[key] = {
            "n": names.get(key),
            "l": level,
            "p": parent.get(key),
            "c": None,
            "b": None,
            "a": None,
        }
    _dump(out_dir / "units.json", units)

    return {
        "method": (
            "GN polygons (COD-AB v03, from the spine) simplified as a coverage in EPSG:5235, "
            "then dissolved to DS, district, province and country; borders written once as a "
            "ranked line mesh. Display geometry only: areas and adjacency come from the spine."
        ),
        "overview_tolerance_m": OVERVIEW_TOLERANCE_M,
        "detail_tolerance_m": DETAIL_TOLERANCE_M,
        "coordinate_decimals": DECIMALS,
        "gn_polygons": len(gn_ids),
        "ds_polygons": len(ds_ids),
        "units_without_geometry": without_geometry,
        "detail_files": len(district_fine),
        "detail_bytes": detail_bytes,
        "source": "geography_versions.geoparquet",
        "source_sha256": _sha256(spine_dir / "geography_versions.geoparquet"),
    }


def build_adjacency(spine_dir: Path, out_dir: Path) -> dict[str, Any]:
    """Neighbour lists from the spine's adjacency tables (G01), unchanged, made symmetric."""
    geographies = pd.read_parquet(spine_dir / "geographies.parquet")
    parent = {
        str(row["geography_id"]): (None if pd.isna(row["parent_id"]) else str(row["parent_id"]))
        for row in _rows(geographies)
    }
    counts: dict[str, int] = {}
    upper: dict[str, dict[str, list[list[Any]]]] = {}
    files: dict[str, str] = {}
    for level in ("province", "district", "ds", "gn"):
        path = spine_dir / "spatial" / f"adjacency_{level}_cod-ab-v03.parquet"
        if not path.exists():
            continue
        files[level] = _sha256(path)
        table = pd.read_parquet(path)
        pairs: dict[str, dict[str, str]] = {}
        for row in _rows(table):
            a, b, kind = str(row["geography_id"]), str(row["neighbour_id"]), str(row["type"])
            pairs.setdefault(a, {})[b] = kind
            pairs.setdefault(b, {}).setdefault(a, kind)
        graph = {
            key: [[other, 0 if kind == "border" else 1] for other, kind in sorted(value.items())]
            for key, value in sorted(pairs.items())
        }
        counts[level] = sum(len(value) for value in graph.values()) // 2
        if level != "gn":
            upper[level] = graph
            continue
        by_district: dict[str, dict[str, list[list[Any]]]] = {}
        for key, value in graph.items():
            ds = parent.get(key)
            district = parent.get(ds) if ds else None
            if district:
                by_district.setdefault(district, {})[key] = value
        for district, value in by_district.items():
            _dump(out_dir / "adjacency-gn" / f"{district}.json", value)
    _dump(out_dir / "adjacency.json", upper)
    return {
        "method": (
            "Spine adjacency tables (rook contiguity on COD-AB v03 in EPSG:5235; units without a "
            "border neighbour get their 3 nearest units), made symmetric. Second item of each "
            "pair: 0 = shares a border, 1 = nearest unit, no shared border."
        ),
        "pairs": counts,
        "source_sha256": files,
    }


def build_clusters(release_dir: Path, out_dir: Path) -> dict[str, Any]:
    """Sparse local Moran classes (q <= 0.05 only) per indicator and level, from stats/."""
    stats = release_dir / "stats"
    by_indicator: dict[str, dict[str, dict[str, list[str]]]] = {}
    files = 0
    for path in sorted(stats.glob("local_*.parquet")):
        stem = path.stem.removeprefix("local_")
        indicator, _, level = stem.rpartition("_")
        if level not in ("gn", "ds", "district"):
            continue
        table = pd.read_parquet(path, columns=["geography_id", "class"])
        classes = {
            name: sorted(str(v) for v in table.loc[table["class"] == name, "geography_id"])
            for name in CLUSTER_CLASSES
        }
        by_indicator.setdefault(indicator, {})[level] = {k: v for k, v in classes.items() if v}
        files += 1
    for indicator, payload in by_indicator.items():
        _dump(out_dir / "clusters" / f"{indicator}.json", payload)
    return {
        "method": (
            "Local Moran's I classes from the release's stats/ tables (999 permutations, "
            "Benjamini-Hochberg q <= 0.05). Only significant units are listed. A class is a "
            "spatial-association label, not a causal finding."
        ),
        "indicators": len(by_indicator),
        "stats_files_read": files,
    }


def build_profile(profile_dir: Path, out_dir: Path) -> dict[str, Any]:
    """DS-level profile space for browser-side distances (D-031: no GN similar lists)."""
    vectors_dir = profile_dir / "vectors"
    axes_files = sorted(vectors_dir.glob("profile_v*_axes.parquet"))
    vector_files = [
        p for p in sorted(vectors_dir.glob("profile_v*.parquet")) if not p.stem.endswith("_axes")
    ]
    if not axes_files or not vector_files:
        return {"available": False, "reason": "no profile build found"}
    axes_file, vector_file = axes_files[-1], vector_files[-1]
    at_ds = [row for row in _rows(pd.read_parquet(vector_file)) if row["level"] == "ds"]
    ds = sorted(
        (row for row in at_ds if row["entity_type"] == "place"),
        key=lambda row: str(row["entity_id"]),
    )
    indicators = [row for row in at_ds if row["entity_type"] == "indicator"]
    by_axis: dict[int, list[dict[str, Any]]] = {}
    for row in _rows(pd.read_parquet(axes_file)):
        if row["level"] == "ds" and bool(row["retained"]):
            by_axis.setdefault(int(row["axis"]), []).append(row)
    axis_meta = []
    for axis, group in sorted(by_axis.items()):
        ordered = sorted(group, key=lambda row: -abs(float(row["loading"])))
        axis_meta.append(
            {
                "axis": axis,
                "variance_explained": round(float(group[0]["variance_explained"]), 5),
                "draft_label": str(group[0]["draft_label"]),
                "label_status": str(group[0]["label_status"]),
                "loadings": [
                    [str(row["indicator_id"]), round(float(row["loading"]), 4)]
                    for row in ordered[:6]
                ],
            }
        )
    unusual = {
        str(row["geography_id"]): row
        for row in _rows(pd.read_parquet(vectors_dir / "unusual_ds_2024.parquet"))
    }
    similar = json.loads((vectors_dir / "similar_ds_2024.json").read_text())
    contrasts = pd.read_parquet(vectors_dir / "contrasts_ds_2024.parquet")
    ids = [str(row["entity_id"]) for row in ds]
    payload = {
        "space_id": str(ds[0]["space_id"]),
        "space_version": str(ds[0]["space_version"]),
        "level": "ds",
        "period": str(ds[0]["period"]),
        "metric": "euclidean",
        "note": similar.get("notes"),
        "axes": axis_meta,
        "ids": ids,
        "vectors": [[round(float(x), 5) for x in row["vector"]] for row in ds],
        "norm": [round(float(row["norm"]), 5) for row in ds],
        "indicator_ids": [str(row["entity_id"]) for row in indicators],
        "indicator_vectors": [[round(float(x), 5) for x in row["vector"]] for row in indicators],
        "percentile": [
            (round(float(unusual[i]["percentile"]), 2) if i in unusual else None) for i in ids
        ],
        "top_indicators": [
            ([str(v) for v in unusual[i]["top_indicators"]] if i in unusual else []) for i in ids
        ],
        "similar": {
            "k": similar.get("k"),
            "indicators": similar.get("indicators"),
            "row_format": similar.get("row_format"),
            "places": similar.get("places"),
        },
        "contrasts": [
            [
                str(r["geography_id"]),
                str(r["neighbour_id"]),
                round(float(r["distance"]), 4),
                round(float(r["percentile_among_bordering_pairs"]), 2),
                bool(r["flagged"]),
            ]
            for r in _rows(contrasts)
        ],
    }
    _dump(out_dir / "profile.json", payload)
    return {
        "available": True,
        "space_id": payload["space_id"],
        "space_version": payload["space_version"],
        "places": len(ids),
        "axes": len(axis_meta),
        "source_sha256": {
            vector_file.name: _sha256(vector_file),
            axes_file.name: _sha256(axes_file),
        },
    }


def build_change(history_dir: Path, spine_dir: Path, out_dir: Path) -> dict[str, Any]:
    """DS population 2012 -> 2024 and the national census series, from the history build (G06)."""
    comparison = history_dir / "ds_comparison_2012_2024.csv"
    series = history_dir / "district_census_series.csv"
    if not comparison.exists():
        return {"available": False, "reason": "no history build found"}
    table = pd.read_csv(comparison, dtype={"geography_id": "string"})
    valid = set(pd.read_parquet(spine_dir / "geographies.parquet")["geography_id"].astype(str))
    rows = []
    dropped = []
    for row in _rows(table):
        gid = None if pd.isna(row["geography_id"]) else str(row["geography_id"])
        if gid is None or gid not in valid:
            dropped.append(str(row["ds_name"]))
            continue
        rows.append(
            {
                "id": gid,
                "pop_2012": None if pd.isna(row["pop_2012"]) else int(row["pop_2012"]),
                "pop_2024": None if pd.isna(row["pop_2024"]) else int(row["pop_2024"]),
                "growth_pct": None if pd.isna(row["growth_pct"]) else float(row["growth_pct"]),
                "annual_rate_pct": None
                if pd.isna(row["annual_rate_pct"])
                else float(row["annual_rate_pct"]),
                "change_type": str(row["change_type"]),
                "comparison": str(row["comparison"]),
                "method": str(row["method"]),
                "reason": None if pd.isna(row["reason"]) else str(row["reason"]),
            }
        )
    national = []
    if series.exists():
        frame = pd.read_csv(series)
        for row in (r for r in _rows(frame) if r["district"] == "Sri Lanka"):
            national.append(
                {
                    "year": int(row["year"]),
                    "population": None if pd.isna(row["population"]) else float(row["population"]),
                    "unit": str(row["unit"]),
                    "source": str(row["source"]),
                    "page": None if pd.isna(row["page"]) else str(row["page"]),
                    "comparison_to_2024": str(row["comparison_to_2024"]),
                }
            )
    sources_path = history_dir / "sources.json"
    sources = json.loads(sources_path.read_text()) if sources_path.exists() else {}
    _dump(
        out_dir / "change.json",
        {
            "status": "local_build_not_in_release",
            "note": (
                "Census history (G06). Built locally from DCS documents; not part of any "
                "release and not published. 'exact' means the same GN list in both censuses; "
                "'approximate' means GNs were re-aggregated or could not all be matched."
            ),
            "ds": rows,
            "national": national,
            "sources": [
                {
                    "id": key,
                    "url": value.get("url"),
                    "sha256": value.get("sha256"),
                    "retrieved_at": value.get("retrieved_at"),
                    "licence_note": value.get("licence_note"),
                }
                for key, value in sources.items()
            ],
        },
    )
    return {
        "available": True,
        "ds_rows": len(rows),
        "ds_rows_without_spine_id": dropped,
        "national_points": len(national),
        "district_series": "not exported: the series is keyed by district name only",
    }


def export(
    release_dir: Path,
    spine_dir: Path,
    out_dir: Path,
    profile_dir: Path | None = None,
    history_dir: Path | None = None,
) -> dict[str, Any]:
    latest = json.loads((release_dir / "api/v1/releases/latest.json").read_text())
    target = out_dir / str(latest["release"])
    target.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {
        "release": latest["release"],
        "kind": "web atlas bundle (derived, for display)",
        "geometry": build_geometry(spine_dir, target),
        "adjacency": build_adjacency(spine_dir, target),
        "clusters": build_clusters(release_dir, target),
        "profile": (
            build_profile(profile_dir, target)
            if profile_dir is not None
            else {"available": False, "reason": "no --profile-dir given"}
        ),
        "change": (
            build_change(history_dir, spine_dir, target)
            if history_dir is not None
            else {"available": False, "reason": "no --history-dir given"}
        ),
    }
    _dump(target / "manifest.json", manifest)
    return manifest
