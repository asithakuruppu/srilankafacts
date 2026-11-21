"""Feature-level `form-feature` and `context-feature` spaces v0.1: one vector per mapped building.

PRIVATE PREVIEW BUILD. The lead asked on 2026-11-21 for the per-feature spaces to be built for the
private preview, with publication waiting for permissions (LA-007, D-058). Everything is written to
the gitignored build folder and nothing is added to a release, the atlas or the live preview.

Rule 11 still holds inside the preview: a feature row carries only physical attributes (geometry
derived numbers, a modelled cell height, distances, an elevation and a biomass value read at its
point) and the GN it falls in. No census or other statistic about people is attached to a
building, and no owner, occupant, name or address is read. Rights: the footprints are ODbL
(Overture) and the road layer is ODbL (OpenStreetMap), so the output is share-alike material.

The method is the place-level one (:func:`slf.profile.fit`): standardise, winsorise at ±5, weight
blocks equally, PCA. It is fitted on a seeded random sample and every feature is projected with the
stored parameters, so a distance between two features decomposes exactly into named inputs.
"""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import rasterio
import shapely
from pyproj import Transformer
from scipy.spatial import KDTree as cKDTree

from slf import profile
from slf.spatial.build import held_files
from slf.spatial.zonal import Zones

SPACE_VERSION = "0.1"
FIT_SAMPLE = 400_000
SEED = 20261121
RETAIN_VARIANCE = 0.85
MAX_AXES = 6
ROAD_SPACING_M = 30.0
EXPLAIN_TOP = 3

FORM_BLOCKS = {
    "size": ["log_area", "height"],
    "shape": ["compactness", "rectangularity", "log_elongation"],
}
CONTEXT_BLOCKS = {
    "neighbourhood": ["log_near_100m", "log_near_500m", "log_nn_distance"],
    "access": ["log_road", "log_school", "log_health", "log_coast"],
    "land": ["sqrt_biomass", "log_elevation"],
}
INPUTS: dict[str, str] = {
    "log_area": "log10(footprint area in m2, EPSG:5235)",
    "height": "log10(1 + GHS-BUILT-H cell height in m); 0 where the cell has no modelled height",
    "compactness": "4 pi area / perimeter^2 (EPSG:5235)",
    "rectangularity": "footprint area / area of its minimum rotated rectangle",
    "log_elongation": "log10(long side / short side of the minimum rotated rectangle)",
    "log_near_100m": "log10(1 + other footprints within 100 m of the inside point)",
    "log_near_500m": "log10(1 + other footprints within 500 m of the inside point)",
    "log_nn_distance": "log10(1 + metres to the nearest other footprint)",
    "log_road": "log10(1 + metres to the nearest OSM road or path, vertices every 30 m)",
    "log_school": "log10(1 + metres to the nearest Giga school location)",
    "log_health": "log10(1 + metres to the nearest healthsites.io facility)",
    "log_coast": "log10(1 + metres to the outline of the GN divisions: sea coast, plus lagoon and "
    "island edges)",
    "sqrt_biomass": "square root of CTrees 2025 biomass at the point, Mg/ha",
    "log_elevation": "log10(1 + metres above EGM2008 at the point, negative set to 0)",
}


@dataclass
class Sampler:
    """Reads a raster band into memory once and answers point lookups (lon, lat in 4326)."""

    array: np.ndarray
    transform: Any
    crs: Any
    nodata: float | None

    @classmethod
    def many(cls, paths: list[Any]) -> list[Sampler]:
        out = []
        for opener in paths:
            with opener() as dataset:
                out.append(cls(dataset.read(1), dataset.transform, dataset.crs, dataset.nodata))
        return out

    def lookup(self, lon: np.ndarray, lat: np.ndarray, into: np.ndarray, filled: np.ndarray):
        if self.crs.to_epsg() == 4326:
            x, y = lon, lat
        else:
            x, y = Transformer.from_crs("EPSG:4326", self.crs, always_xy=True).transform(lon, lat)
        col = np.floor((x - self.transform.c) / self.transform.a).astype(np.int64)
        row = np.floor((y - self.transform.f) / self.transform.e).astype(np.int64)
        h, w = self.array.shape
        inside = (row >= 0) & (row < h) & (col >= 0) & (col < w) & ~filled
        values = np.full(len(lon), np.nan)
        values[inside] = self.array[row[inside], col[inside]]
        if self.nodata is not None:
            values[values == self.nodata] = np.nan
        take = inside & np.isfinite(values)
        into[take] = values[take]
        filled |= take


def _opener(path: Path):
    def open_() -> rasterio.DatasetReader:
        if path.suffix == ".zip":
            tif = next(n for n in zipfile.ZipFile(path).namelist() if n.endswith(".tif"))
            return rasterio.open(f"zip://{path}!{tif}")
        return rasterio.open(path)

    return open_


def read_buildings(
    roots: list[Path], zones: Zones, limit_batches: int | None = None
) -> dict[str, Any]:
    """Per-footprint geometry numbers in EPSG:5235 and the GN each footprint falls in."""
    files = [
        f
        for f in held_files(roots, "overture", "overture-buildings")
        if f.path.suffix == ".parquet"
    ][-1:]
    if not files:
        raise FileNotFoundError("overture-buildings not held")
    to_m = Transformer.from_crs("EPSG:4326", "EPSG:5235", always_xy=True)
    project: Any = to_m.transform
    _, tree = zones.in_crs(zones.frame.crs)
    cols: dict[str, list[np.ndarray]] = {
        k: [] for k in ("lon", "lat", "x", "y", "area", "compact", "rect", "elong", "gn")
    }
    ids: list[pa.Array] = []
    for number, batch in enumerate(
        pq.ParquetFile(files[0].path).iter_batches(batch_size=250_000, columns=["id", "geometry"])
    ):
        if limit_batches is not None and number >= limit_batches:
            break
        geometry = shapely.from_wkb(batch.column("geometry").to_numpy(zero_copy_only=False))
        points = shapely.point_on_surface(geometry)
        pairs = tree.query(points, predicate="intersects")
        gn = np.full(len(points), -1, dtype=np.int32)
        order = np.lexsort((pairs[1], pairs[0]))
        first = np.unique(pairs[0][order], return_index=True)
        gn[first[0]] = pairs[1][order][first[1]]
        projected = shapely.transform(geometry, project, interleaved=False)
        area = shapely.area(projected)
        perimeter = shapely.length(projected)
        rect = shapely.oriented_envelope(projected)
        rect_area = shapely.area(rect)
        corners = shapely.get_coordinates(rect).reshape(-1, 5, 2)[:, :4]
        side_a = np.hypot(*(corners[:, 1] - corners[:, 0]).T)
        side_b = np.hypot(*(corners[:, 2] - corners[:, 1]).T)
        long_side, short_side = np.maximum(side_a, side_b), np.minimum(side_a, side_b)
        good = (area > 0) & (perimeter > 0) & (rect_area > 0) & (short_side > 0)
        with np.errstate(invalid="ignore", divide="ignore"):
            compact = np.where(good, np.minimum(4 * np.pi * area / perimeter**2, 1.0), np.nan)
            rectangularity = np.where(good, np.minimum(area / rect_area, 1.0), np.nan)
            elongation = np.where(good, long_side / short_side, np.nan)
        xy = shapely.get_coordinates(points)
        px, py = to_m.transform(xy[:, 0], xy[:, 1])
        for key, value in (
            ("lon", xy[:, 0]),
            ("lat", xy[:, 1]),
            ("x", px),
            ("y", py),
            ("area", area),
            ("compact", compact),
            ("rect", rectangularity),
            ("elong", elongation),
            ("gn", gn),
        ):
            cols[key].append(np.asarray(value))
        ids.append(batch.column("id"))
    out: dict[str, Any] = {k: np.concatenate(v) for k, v in cols.items()}
    out["id"] = pa.chunked_array(ids)
    out["file"] = files[0]
    return out


def _densified(lines: Any, spacing: float) -> np.ndarray:
    dense = shapely.segmentize(lines, spacing)
    return shapely.get_coordinates(dense)


def _distance(tree: cKDTree, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return tree.query(np.column_stack([x, y]), k=1, workers=-1)[0]


def context_layers(roots: list[Path], b: dict[str, Any], zones: Zones, features_dir: Path):
    """Distances and point values for every footprint."""
    n = len(b["x"])
    xy = np.column_stack([b["x"], b["y"]])
    own = cKDTree(xy)
    near100 = own.query_ball_point(xy, 100.0, return_length=True, workers=-1) - 1
    near500 = own.query_ball_point(xy, 500.0, return_length=True, workers=-1) - 1
    nn = own.query(xy, k=2, workers=-1)[0][:, 1]
    to_m = Transformer.from_crs("EPSG:4326", "EPSG:5235", always_xy=True)
    project: Any = to_m.transform

    import geopandas as gpd
    import pyogrio

    osm = held_files(roots, "osm", "osm-sri-lanka")
    roads = pyogrio.read_dataframe(
        osm[0].path,
        sql="SELECT highway FROM lines WHERE highway IS NOT NULL",
        sql_dialect="OGRSQL",
    )
    road_geoms = shapely.transform(roads.geometry.to_numpy(), project, interleaved=False)
    road_xy = _densified(road_geoms, ROAD_SPACING_M)
    d_road = _distance(cKDTree(road_xy), b["x"], b["y"])

    def point_distance(name: str) -> np.ndarray:
        table = gpd.read_parquet(features_dir / name)
        pts = table.geometry.to_crs(5235)
        return _distance(cKDTree(shapely.get_coordinates(pts.to_numpy())), b["x"], b["y"])

    d_school = point_distance("giga-school-locations.parquet")
    d_health = point_distance("healthsites-lk.parquet")
    outline = shapely.union_all(zones.frame.geometry.to_crs(5235).to_numpy()).boundary
    coast_xy = _densified(np.array([outline]), ROAD_SPACING_M)
    d_coast = _distance(cKDTree(coast_xy), b["x"], b["y"])

    lon, lat = b["lon"], b["lat"]
    height = np.full(n, np.nan)
    filled = np.zeros(n, dtype=bool)
    for held in held_files(roots, "ghsl", "ghsl-building-height"):
        for s in Sampler.many([_opener(held.path)]):
            s.lookup(lon, lat, height, filled)
    biomass = np.full(n, np.nan)
    filled = np.zeros(n, dtype=bool)
    for held in held_files(roots, "ctrees", "ctrees-aboveground-biomass"):
        if held.path.suffix == ".tif":
            for s in Sampler.many([_opener(held.path)]):
                s.lookup(lon, lat, biomass, filled)
    biomass = biomass / 10.0
    elevation = np.full(n, np.nan)
    filled = np.zeros(n, dtype=bool)
    for held in held_files(roots, "copernicus", "copernicus-dem-glo30"):
        if held.path.suffix == ".tif":
            for s in Sampler.many([_opener(held.path)]):
                s.lookup(lon, lat, elevation, filled)
    return {
        "near_100m": near100,
        "near_500m": near500,
        "nn_distance": nn,
        "road_m": d_road,
        "school_m": d_school,
        "health_m": d_health,
        "coast_m": d_coast,
        "height_m": height,
        "biomass_mgha": biomass,
        "elevation_m": elevation,
    }


def inputs(b: dict[str, Any], c: dict[str, np.ndarray]) -> pd.DataFrame:
    with np.errstate(invalid="ignore", divide="ignore"):
        height = np.where(c["height_m"] > 0, c["height_m"], 0.0)
        height = np.where(np.isnan(c["height_m"]), np.nan, height)
        return pd.DataFrame(
            {
                "log_area": np.log10(np.where(b["area"] > 0, b["area"], np.nan)),
                "height": np.log10(1 + height),
                "compactness": b["compact"],
                "rectangularity": b["rect"],
                "log_elongation": np.log10(b["elong"]),
                "log_near_100m": np.log10(1 + c["near_100m"]),
                "log_near_500m": np.log10(1 + c["near_500m"]),
                "log_nn_distance": np.log10(1 + c["nn_distance"]),
                "log_road": np.log10(1 + c["road_m"]),
                "log_school": np.log10(1 + c["school_m"]),
                "log_health": np.log10(1 + c["health_m"]),
                "log_coast": np.log10(1 + c["coast_m"]),
                "sqrt_biomass": np.sqrt(
                    np.where(c["biomass_mgha"] >= 0, c["biomass_mgha"], np.nan)
                ),
                "log_elevation": np.log10(1 + np.clip(c["elevation_m"], 0, None)),
            }
        )


def fit_and_project(x: pd.DataFrame, blocks: dict[str, list[str]]):
    """Fit on a seeded sample of complete rows; project every complete row exactly."""
    columns = [c for block in blocks.values() for c in block]
    arr = x[columns].to_numpy(dtype=float)
    complete = np.isfinite(arr).all(axis=1)
    rng = np.random.default_rng(SEED)
    pool = np.flatnonzero(complete)
    sample = rng.choice(pool, size=min(FIT_SAMPLE, len(pool)), replace=False)
    f = profile.fit(pd.DataFrame(arr[sample], columns=columns), blocks)
    cumulative = np.cumsum(f.eigenvalues / f.eigenvalues.sum())
    f.retained = list(range(min(int(np.searchsorted(cumulative, RETAIN_VARIANCE) + 1), MAX_AXES)))
    assert f.mean is not None and f.sd is not None and f.weights is not None
    assert f.centre is not None
    z = np.clip((arr[complete] - f.mean) / f.sd, -profile.WINSOR_SD, profile.WINSOR_SD)
    z = z * f.weights - f.centre
    scores = np.full((len(arr), len(f.retained)), np.nan, dtype=np.float32)
    scores[complete] = (z @ f.basis).astype(np.float32)
    return f, scores, complete, columns


def _stat(values: np.ndarray, q: float) -> float:
    return float(np.nanpercentile(values, q))


def explain(f: profile.Fit, za: np.ndarray, zb: np.ndarray) -> list[list[Any]]:
    """Top input contributions to the squared distance between two projected rows."""
    dz = za - zb
    ds = dz @ f.basis
    indicator = dz * (f.basis @ ds)
    order = np.argsort(-indicator)[:EXPLAIN_TOP]
    return [[f.columns[i], round(float(indicator[i]), 4)] for i in order]


def checks(f: profile.Fit, x: pd.DataFrame, scores: np.ndarray, gn: np.ndarray, xy: np.ndarray):
    """Exact decomposition, and how local the nearest neighbours are, on a seeded sample."""
    rng = np.random.default_rng(SEED)
    ok = np.flatnonzero(np.isfinite(scores).all(axis=1))
    columns = f.columns
    arr = x[columns].to_numpy(dtype=float)
    assert f.mean is not None and f.sd is not None and f.weights is not None
    assert f.centre is not None
    mean, sd = np.asarray(f.mean), np.asarray(f.sd)
    weights, centre = np.asarray(f.weights), np.asarray(f.centre)

    def zrow(i: np.ndarray) -> np.ndarray:
        z = np.clip((arr[i] - mean) / sd, -profile.WINSOR_SD, profile.WINSOR_SD)
        return z * weights - centre

    pick = rng.choice(ok, size=min(2000, len(ok)), replace=False)
    tree = cKDTree(scores[ok])
    found: Any = tree.query(scores[pick], k=6, workers=-1)
    neighbours = ok[np.asarray(found[1])[:, 1:]]
    err = 0.0
    for a, nbrs in zip(pick[:300], neighbours[:300], strict=True):
        b = nbrs[0]
        za, zb = zrow(np.array([a]))[0], zrow(np.array([b]))[0]
        sq_axes = float((((za - zb) @ f.basis) ** 2).sum())
        sq_direct = float(((scores[a].astype(float) - scores[b].astype(float)) ** 2).sum())
        dz = za - zb
        sq_inputs = float((dz * (f.basis @ (dz @ f.basis))).sum())
        err = max(err, abs(sq_axes - sq_inputs), abs(sq_axes - sq_direct))
    near_m = np.hypot(*(xy[pick, None, :] - xy[neighbours]).transpose(2, 0, 1)).mean()
    rand = rng.choice(ok, size=(len(pick), 5))
    rand_m = np.hypot(*(xy[pick, None, :] - xy[rand]).transpose(2, 0, 1)).mean()
    same_gn = float((gn[neighbours] == gn[pick, None]).mean())
    return {
        "sample": len(pick),
        "max_abs_decomposition_error": err,
        "mean_distance_to_5_nearest_in_space_m": round(float(near_m), 1),
        "mean_distance_to_5_random_m": round(float(rand_m), 1),
        "neighbours_in_same_gn": round(same_gn, 4),
        "float32_rounding_note": "vectors are stored as float32; the error is against those",
    }


def build(
    roots: list[Path],
    zones: Zones,
    features_dir: Path,
    out_dir: Path,
    limit_batches: int | None = None,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    b = read_buildings(roots, zones, limit_batches)
    c = context_layers(roots, b, zones, features_dir)
    x = inputs(b, c)
    summary: dict[str, Any] = {
        "space_version": SPACE_VERSION,
        "features": len(x),
        "outside_every_gn": int((b["gn"] < 0).sum()),
        "inputs": INPUTS,
        "spaces": {},
        "privacy": "physical attributes only; no people statistic, name, owner or address",
    }
    table: dict[str, Any] = {
        "feature_id": b["id"],
        "gn_id": pa.array([zones.ids[g] if g >= 0 else None for g in b["gn"]], type=pa.string()),
        "lon": pa.array(b["lon"], type=pa.float64()),
        "lat": pa.array(b["lat"], type=pa.float64()),
    }
    axis_rows: list[dict[str, Any]] = []
    for space_id, blocks in (("form-feature", FORM_BLOCKS), ("context-feature", CONTEXT_BLOCKS)):
        f, scores, complete, columns = fit_and_project(x, blocks)
        norms = np.sqrt(np.nansum(scores.astype(np.float64) ** 2, axis=1))
        norms[~complete] = np.nan
        table[f"{space_id}_vector"] = pa.array(
            [r if ok else None for r, ok in zip(scores.tolist(), complete, strict=True)],
            type=pa.list_(pa.float32()),
        )
        table[f"{space_id}_norm"] = pa.array(norms.astype(np.float32))
        share = f.eigenvalues / f.eigenvalues.sum()
        for j in range(len(f.eigenvalues)):
            for i, column in enumerate(columns):
                axis_rows.append(
                    {
                        "space_id": space_id,
                        "space_version": SPACE_VERSION,
                        "axis": j + 1,
                        "retained": j in f.retained,
                        "variance_explained": float(share[j]),
                        "input": column,
                        "loading": float(f.loadings[i, j]),
                        "label_status": "machine_generated_draft",
                    }
                )
        summary["spaces"][space_id] = {
            "space_version": SPACE_VERSION,
            "features_in_space": int(complete.sum()),
            "excluded_undefined_input": int((~complete).sum()),
            "fit_sample": min(FIT_SAMPLE, int(complete.sum())),
            "axes_retained": len(f.retained),
            "variance_explained_retained": round(float(share[f.retained].sum()), 4),
            "clipped_in_fit_sample": {k: v for k, v in f.clipped.items() if v},
            "inputs_missing": {
                c_: int(np.isnan(x[c_].to_numpy(dtype=float)).sum()) for c_ in columns
            },
            "checks": checks(f, x, scores, b["gn"], np.column_stack([b["x"], b["y"]])),
            "input_summary": {
                c_: {
                    "p1": round(_stat(x[c_].to_numpy(dtype=float), 1), 3),
                    "median": round(_stat(x[c_].to_numpy(dtype=float), 50), 3),
                    "p99": round(_stat(x[c_].to_numpy(dtype=float), 99), 3),
                }
                for c_ in columns
            },
            "axes": [
                {
                    "axis": j + 1,
                    "variance_explained": round(float(share[j]), 4),
                    "loadings": {
                        c_: round(float(v), 3)
                        for c_, v in zip(columns, f.loadings[:, j], strict=True)
                    },
                }
                for j in f.retained
            ],
        }
    for name, values in (
        ("area_m2", b["area"]),
        ("height_cell_m", c["height_m"]),
        ("near_100m", c["near_100m"]),
        ("road_m", c["road_m"]),
        ("school_m", c["school_m"]),
        ("health_m", c["health_m"]),
        ("coast_m", c["coast_m"]),
        ("biomass_mgha", c["biomass_mgha"]),
        ("elevation_m", c["elevation_m"]),
    ):
        table[name] = pa.array(np.asarray(values, dtype=np.float32))
    pq.write_table(
        pa.table(table), out_dir / f"features_v{SPACE_VERSION}.parquet", compression="zstd"
    )
    pd.DataFrame(axis_rows).to_parquet(out_dir / f"axes_v{SPACE_VERSION}.parquet", index=False)
    summary["source_file_sha256"] = b["file"].sha256
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    (out_dir / "qa.md").write_text(render_qa(summary), encoding="utf-8")
    return summary


def render_qa(s: dict[str, Any]) -> str:
    lines = [
        "# QA: feature-level `form-feature` and `context-feature` spaces v0.1 (private preview)",
        "",
        "Generated by `slf spatial featurespace`. Every number was computed in this run. "
        "One row per "
        "mapped building footprint, physical attributes only (no people statistic, name, owner or "
        "address). Share-alike (ODbL) material: not published.",
        "",
        f"- Footprints: {s['features']:,}; outside every GN polygon: {s['outside_every_gn']:,} "
        "(kept, with an empty `gn_id`).",
        "",
        "| Input | Definition |",
        "|---|---|",
        *[f"| {k} | {v} |" for k, v in s["inputs"].items()],
    ]
    for space_id, info in s["spaces"].items():
        c = info["checks"]
        lines += [
            "",
            f"## `{space_id}` v{info['space_version']}",
            "",
            f"- Features in the space: {info['features_in_space']:,}; excluded for an undefined "
            f"input: {info['excluded_undefined_input']:,} (fitted on a seeded sample of "
            f"{info['fit_sample']:,}).",
            f"- Axes retained: {info['axes_retained']} "
            f"({info['variance_explained_retained']:.1%} of variance).",
            f"- Exact decomposition: largest absolute error over 300 pairs "
            f"{c['max_abs_decomposition_error']:.2e}.",
            f"- Locality, {c['sample']:,} random features: the 5 nearest in this space are on "
            f"average {c['mean_distance_to_5_nearest_in_space_m']:,} m away on the ground, against "
            f"{c['mean_distance_to_5_random_m']:,} m for random features; "
            f"{c['neighbours_in_same_gn']:.1%} are in the same GN.",
            "",
            "| Input | undefined | p1 | median | p99 |",
            "|---|---:|---:|---:|---:|",
            *[
                f"| {k} | {info['inputs_missing'][k]:,} | {v['p1']} | {v['median']} | {v['p99']} |"
                for k, v in info["input_summary"].items()
            ],
            "",
            "| Axis | Variance | Strongest loadings |",
            "|---|---:|---|",
        ]
        for ax in info["axes"]:
            top = sorted(ax["loadings"].items(), key=lambda kv: -abs(kv[1]))[:3]
            lines.append(
                f"| {ax['axis']} | {ax['variance_explained']:.1%} | "
                + ", ".join(f"{k} {v:+.2f}" for k, v in top)
                + " |"
            )
    return "\n".join(lines) + "\n"
