"""Building footprints rolled up to GN divisions (Overture Maps buildings, ODbL).

Each footprint goes to the GN division its representative point falls in. Only physical
attributes are read: geometry, the source dataset, and whether a height is recorded. Nothing
about people is attached to a building (AGENTS rule 11); only per-place counts and areas leave
this module, and they stay ODbL.
"""

from __future__ import annotations

import pickle
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq
import shapely
from pyproj import Transformer

from slf.spatial.build import Held, digest, held_files
from slf.spatial.zonal import Zones

SMALL_M2 = 20.0  # footprints under this are mostly sheds and outbuildings (a chosen cut)
LARGE_M2 = 250.0  # footprints at or above this are large buildings (a chosen cut)
SOURCES = ("OpenStreetMap", "Microsoft ML Buildings", "Google Open Buildings")


@dataclass
class BuildingRollup:
    files: list[Held]
    read: int = 0
    unresolved: int = 0
    count: np.ndarray = field(default_factory=lambda: np.zeros(0))
    area_m2: np.ndarray = field(default_factory=lambda: np.zeros(0))
    with_height: np.ndarray = field(default_factory=lambda: np.zeros(0))
    perimeter_m: np.ndarray = field(default_factory=lambda: np.zeros(0))
    compact_sum: np.ndarray = field(default_factory=lambda: np.zeros(0))
    shaped: np.ndarray = field(default_factory=lambda: np.zeros(0))
    small: np.ndarray = field(default_factory=lambda: np.zeros(0))
    large: np.ndarray = field(default_factory=lambda: np.zeros(0))
    by_source: dict[str, np.ndarray] = field(default_factory=dict)
    source_totals: dict[str, int] = field(default_factory=dict)


def rollup(roots: list[Path], zones: Zones, cache_dir: Path) -> BuildingRollup | None:
    files = [
        f
        for f in held_files(roots, "overture", "overture-buildings")
        if f.path.suffix == ".parquet"
    ]
    if not files:
        return None
    files = files[-1:]
    cached = cache_dir / f"buildings-v2-{digest(files)[:16]}.pkl"
    if cached.exists():
        with cached.open("rb") as handle:
            return pickle.load(handle)
    n = len(zones)
    out = BuildingRollup(
        files,
        count=np.zeros(n),
        area_m2=np.zeros(n),
        with_height=np.zeros(n),
        perimeter_m=np.zeros(n),
        compact_sum=np.zeros(n),
        shaped=np.zeros(n),
        small=np.zeros(n),
        large=np.zeros(n),
    )
    out.by_source = {name: np.zeros(n) for name in (*SOURCES, "other")}
    _geoms, tree = zones.in_crs(zones.frame.crs)
    to_metres = Transformer.from_crs("EPSG:4326", "EPSG:5235", always_xy=True)
    parquet = pq.ParquetFile(files[0].path)
    for batch in parquet.iter_batches(
        batch_size=250_000, columns=["geometry", "sources", "height"]
    ):
        geometry = shapely.from_wkb(batch.column("geometry").to_numpy(zero_copy_only=False))
        points = shapely.point_on_surface(geometry)
        pairs = tree.query(points, predicate="intersects")
        index = np.full(len(points), -1, dtype=np.int64)
        order = np.lexsort((pairs[1], pairs[0]))
        first = np.unique(pairs[0][order], return_index=True)
        index[first[0]] = pairs[1][order][first[1]]
        inside = index >= 0
        out.read += len(points)
        out.unresolved += int((~inside).sum())
        project: Any = to_metres.transform  # (x, y) arrays in, (x, y) arrays out
        projected = shapely.transform(geometry[inside], project, interleaved=False)
        area = shapely.area(projected)
        where = index[inside]
        out.count += np.bincount(where, minlength=n)
        out.area_m2 += np.bincount(where, weights=area, minlength=n)
        # Shape in metres on the national grid: perimeter, and the Polsby-Popper compactness
        # 4 pi A / P^2 (1 for a circle, about 0.79 for a square, near 0 for a sliver).
        perimeter = shapely.length(projected)
        ok = (area > 0) & (perimeter > 0)
        compact = np.zeros(len(area))
        compact[ok] = np.minimum(4 * np.pi * area[ok] / perimeter[ok] ** 2, 1.0)
        out.perimeter_m += np.bincount(where[ok], weights=perimeter[ok], minlength=n)
        out.compact_sum += np.bincount(where[ok], weights=compact[ok], minlength=n)
        out.shaped += np.bincount(where[ok], minlength=n)
        out.small += np.bincount(where[area < SMALL_M2], minlength=n)
        out.large += np.bincount(where[area >= LARGE_M2], minlength=n)
        height = batch.column("height").to_numpy(zero_copy_only=False)
        has_height = ~np.isnan(np.asarray(height, dtype=np.float64))[inside]
        out.with_height += np.bincount(where[has_height], minlength=n)
        sources = batch.column("sources").to_pylist()
        primary = np.array([s[0]["dataset"] if s else "other" for s in sources], dtype=object)
        for name in np.unique(primary):
            out.source_totals[str(name)] = out.source_totals.get(str(name), 0) + int(
                (primary == name).sum()
            )
        primary = primary[inside]
        known = np.isin(primary, SOURCES)
        for name in SOURCES:
            out.by_source[name] += np.bincount(where[primary == name], minlength=n)
        out.by_source["other"] += np.bincount(where[~known], minlength=n)
    cache_dir.mkdir(parents=True, exist_ok=True)
    with cached.open("wb") as handle:
        pickle.dump(out, handle)
    return out
