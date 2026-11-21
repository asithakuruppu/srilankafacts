"""Point layers resolved to places: schools, health facilities, listed places, landmarks.

Each point gets the GN division it falls in (point in polygon, in EPSG:4326 as published) and
through it the DS division, district and province. Points outside every GN polygon are counted
and listed in the QA report, never dropped silently. Only counts per place and straight-line
distances are published; the resolved feature tables stay in the build folder with their own
licences.
"""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from shapely import STRtree

from slf.spatial import buildings as building_layers
from slf.spatial.build import Emitter, Held, Hierarchy, Layer, _ratio, held_files
from slf.spatial.layers import HEALTH_AMENITIES, OVERTURE_CATEGORIES, OVERTURE_MIN_CONFIDENCE
from slf.spatial.zonal import Zones


@dataclass
class PointSet:
    dataset: str
    licence: str
    files: list[Held]
    frame: gpd.GeoDataFrame  # columns: name, category, extra..., geometry (EPSG:4326)
    unresolved: int = 0
    read: int = 0
    notes: list[str] = field(default_factory=list)


def _points(frame: pd.DataFrame, lon: str, lat: str) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(
        frame, geometry=gpd.points_from_xy(frame[lon], frame[lat]), crs="EPSG:4326"
    )


def schools(roots: list[Path]) -> PointSet:
    files = [
        f for f in held_files(roots, "giga", "giga-school-locations") if "schema" not in f.path.name
    ]
    raw = pd.read_csv(files[0].path)
    frame = _points(
        pd.DataFrame(
            {
                "name": raw.school_name,
                "category": raw.education_level,
                "connected": raw.connectivity.eq("Yes"),
                "lon": raw.longitude,
                "lat": raw.latitude,
            }
        ),
        "lon",
        "lat",
    )
    return PointSet("giga-school-locations", "CC BY 4.0", files, frame, read=len(raw))


def health(roots: list[Path]) -> PointSet:
    files = held_files(roots, "healthsites", "healthsites-lk")
    raw = gpd.read_file(files[0].path)
    keep: Any = raw[raw.amenity.isin(HEALTH_AMENITIES)].copy()
    keep["geometry"] = keep.geometry.representative_point()
    frame = gpd.GeoDataFrame(
        {
            "name": keep.name.replace("", None),
            "category": keep.amenity,
            "osm_id": keep.osm_id,
            "osm_type": keep.osm_type,
        },
        geometry=keep.geometry,
        crs="EPSG:4326",
    )
    out = PointSet("healthsites-lk", "ODbL 1.0", files, frame, read=len(raw))
    out.notes.append(
        f"{len(raw) - len(keep)} of {len(raw)} healthsites records are pharmacies, dentists or "
        "untyped and are not counted as health facilities"
    )
    return out


def overture_places(roots: list[Path]) -> PointSet:
    files = held_files(roots, "overture", "overture-places")
    files = [f for f in files if f.path.suffix == ".parquet"][-1:]
    raw = pd.read_parquet(files[0].path)
    top = [
        t["hierarchy"][0]
        if t is not None and t["hierarchy"] is not None and len(t["hierarchy"])
        else None
        for t in raw.taxonomy
    ]
    geometry = shapely.from_wkb(raw.geometry.to_numpy())
    frame = gpd.GeoDataFrame(
        {
            "name": [n["primary"] if n is not None else None for n in raw.names],
            "category": top,
            "basic_category": raw.basic_category,
            "confidence": raw.confidence,
            "overture_id": raw.id,
        },
        geometry=geometry,
        crs="EPSG:4326",
    )
    confident: Any = frame[frame.confidence >= OVERTURE_MIN_CONFIDENCE].copy()
    out = PointSet(
        "overture-places",
        "CDLA-Permissive-2.0",
        files,
        confident,
        read=len(raw),
    )
    out.notes.append(
        f"{len(raw) - len(confident)} of {len(raw)} Overture places have confidence below "
        f"{OVERTURE_MIN_CONFIDENCE} and are not counted"
    )
    return out


def wikidata(roots: list[Path]) -> PointSet:
    files = held_files(roots, "wikidata", "wikidata-places-lk")
    rows = json.loads(files[0].path.read_text())["results"]["bindings"]
    records = []
    for row in rows:
        lon, lat = row["coord"]["value"].removeprefix("Point(").removesuffix(")").split()
        records.append(
            {
                "wikidata_id": row["item"]["value"].rsplit("/", 1)[-1],
                "name": row.get("en", {}).get("value"),
                "name_si": row.get("si", {}).get("value"),
                "name_ta": row.get("ta", {}).get("value"),
                "category": row.get("classes", {}).get("value") or None,
                "heritage": row.get("heritage", {}).get("value"),
                "inception": row.get("inception", {}).get("value"),
                "lon": float(lon),
                "lat": float(lat),
            }
        )
    table = pd.DataFrame(records)
    # an item with several labels or inception dates comes back as several rows
    unique = table.drop_duplicates("wikidata_id")
    out = PointSet(
        "wikidata-places-lk", "CC0 1.0", files, _points(unique, "lon", "lat"), read=len(unique)
    )
    out.notes.append(f"{len(table) - len(unique)} duplicate result rows merged by Wikidata id")
    return out


def geonames(roots: list[Path]) -> PointSet:
    files = held_files(roots, "geonames", "geonames-lk")
    with zipfile.ZipFile(files[0].path) as archive, archive.open("LK.txt") as handle:
        raw = pd.read_csv(handle, sep="\t", header=None, low_memory=False, keep_default_na=False)
    frame = _points(
        pd.DataFrame(
            {
                "geonames_id": raw[0],
                "name": raw[1],
                "alternate_names": raw[3],
                "category": raw[6] + "." + raw[7],
                "lon": raw[5].astype(float),
                "lat": raw[4].astype(float),
            }
        ),
        "lon",
        "lat",
    )
    return PointSet("geonames-lk", "CC BY 4.0", files, frame, read=len(raw))


READERS = {
    "schools": schools,
    "health": health,
    "overture_places": overture_places,
    "wikidata": wikidata,
    "geonames": geonames,
}


def resolve(points: PointSet, zones: Zones) -> np.ndarray:
    """Index of the GN division each point falls in, or -1."""
    _geoms, tree = zones.in_crs(zones.frame.crs)
    pairs = tree.query(points.frame.geometry.to_numpy(), predicate="intersects")
    index = np.full(len(points.frame), -1, dtype=np.int64)
    # a point exactly on a shared border matches two polygons; the first by zone order is kept
    order = np.lexsort((pairs[1], pairs[0]))
    first = np.unique(pairs[0][order], return_index=True)
    index[first[0]] = pairs[1][order][first[1]]
    points.unresolved = int((index < 0).sum())
    return index


def counts(index: np.ndarray, n: int, mask: np.ndarray | None = None) -> np.ndarray:
    chosen = index[(index >= 0) & (mask if mask is not None else True)]
    return np.bincount(chosen, minlength=n).astype(np.float64)


def nearest_km(zones: Zones, label_points: gpd.GeoSeries, points: gpd.GeoSeries) -> np.ndarray:
    target = points.to_crs(5235).to_numpy()
    origin = label_points.to_crs(5235).to_numpy()
    tree = STRtree(target)
    nearest = tree.nearest(origin)
    return shapely.distance(origin, target[nearest]) / 1000.0


def build(
    roots: list[Path],
    zones: Zones,
    hierarchy: Hierarchy,
    label_points: gpd.GeoSeries,
    out_dir: Path,
    buildings_out: dict[str, Any],
    land_m2: np.ndarray | None = None,
) -> tuple[pd.DataFrame, dict[str, PointSet]]:
    geos = hierarchy
    emitter = Emitter(geos)
    sets: dict[str, PointSet] = {}
    indexes: dict[str, np.ndarray] = {}
    n = len(zones)
    features_dir = out_dir / "features"
    features_dir.mkdir(parents=True, exist_ok=True)
    for key, reader in READERS.items():
        try:
            points = reader(roots)
        except (IndexError, FileNotFoundError):
            continue
        index = resolve(points, zones)
        sets[key], indexes[key] = points, index
        table = points.frame.copy()
        table["gn_id"] = [zones.ids[i] if i >= 0 else None for i in index]
        table["ds_id"] = table.gn_id.str[:6]
        table["district_id"] = table.gn_id.str[:4]
        table["licence"] = points.licence
        table.to_parquet(features_dir / f"{points.dataset}.parquet", index=False)

    def layer(points: PointSet, what: str) -> Layer:
        return Layer(points.dataset, points.files, "point", what)

    if "schools" in sets:
        p, i = sets["schools"], indexes["schools"]
        lay = layer(p, "Giga school list, columns longitude and latitude; point in GN polygon")
        obs: dict[str, Any] = dict(
            period="2024", start="2024-01-01", end="2024-12-31", time_support="observed_around"
        )
        kw: dict[str, Any] = dict(
            collection_method="admin_register",
            data_nature="administrative_count",
            how="points counted per GN division",
        )
        located = geos.total(counts(i, n))
        connected = geos.total(counts(i, n, p.frame.connected.to_numpy()))
        emitter.add(lay, "schools_located", located, **obs, **kw)
        emitter.add(lay, "schools_connected", connected, **obs, **kw)
        emitter.add(lay, "schools_connected_share", _ratio(connected, located, 100), **obs, **kw)
        emitter.add(
            lay,
            "nearest_school_distance",
            nearest_km(zones, label_points, p.frame.geometry),
            first=n,
            **obs,
            collection_method="admin_register",
            data_nature="modelled_estimate",
            how="straight-line distance from the GN label point",
        )
    if "health" in sets:
        p, i = sets["health"], indexes["health"]
        lay = layer(
            p,
            "healthsites.io GeoJSON (OpenStreetMap), amenity in hospital, clinic, doctors; point in GN polygon",
        )
        obs: dict[str, Any] = dict(
            period="2026",
            start="2026-01-01",
            end=p.files[0].retrieved_at[:4]
            + "-"
            + p.files[0].retrieved_at[4:6]
            + "-"
            + p.files[0].retrieved_at[6:8],
            time_support="snapshot",
        )
        kw: dict[str, Any] = dict(collection_method="crowd_mapped", data_nature="modelled_estimate")
        emitter.add(
            lay,
            "health_facilities_mapped",
            geos.total(counts(i, n)),
            how="points counted per GN division",
            **obs,
            **kw,
        )
        emitter.add(
            lay,
            "nearest_health_facility_distance",
            nearest_km(zones, label_points, p.frame.geometry),
            first=n,
            how="straight-line distance from the GN label point",
            **obs,
            **kw,
        )
    if "overture_places" in sets:
        p, i = sets["overture_places"], indexes["overture_places"]
        lay = layer(
            p, f"Overture Maps places, confidence >= {OVERTURE_MIN_CONFIDENCE}; point in GN polygon"
        )
        obs: dict[str, Any] = dict(
            period="2026", start="2026-01-01", end="2026-10-21", time_support="snapshot"
        )
        kw: dict[str, Any] = dict(
            collection_method="crowd_mapped",
            data_nature="modelled_estimate",
            how="points counted per GN division",
        )
        emitter.add(lay, "places_listed", geos.total(counts(i, n)), **obs, **kw)
        category = p.frame.category.to_numpy()
        for slug in OVERTURE_CATEGORIES:
            emitter.add(
                lay,
                f"places_listed_{slug}",
                geos.total(counts(i, n, category == slug)),
                locator=f"{lay.locator}; taxonomy.hierarchy[0] = {slug}",
                **obs,
                **kw,
            )
    if "wikidata" in sets:
        p, i = sets["wikidata"], indexes["wikidata"]
        lay = layer(
            p,
            "Wikidata SPARQL result (items with P17 = Sri Lanka and P625 coordinates); point in GN polygon",
        )
        day = p.files[0].retrieved_at
        obs: dict[str, Any] = dict(
            period="2026",
            start="2026-01-01",
            end=f"{day[:4]}-{day[4:6]}-{day[6:8]}",
            time_support="snapshot",
        )
        emitter.add(
            lay,
            "wikidata_items",
            geos.total(counts(i, n)),
            collection_method="crowd_mapped",
            data_nature="modelled_estimate",
            how="points counted per GN division",
            **obs,
        )
    rolled = building_layers.rollup(roots, zones, out_dir / "cache")
    if rolled is not None:
        lay = Layer(
            "overture-buildings",
            rolled.files,
            "feature",
            "Overture Maps buildings extract, release 2026-10-21.0; footprint assigned to the GN "
            "division containing its inside point",
        )
        obs = dict(period="2026", start="2026-01-01", end="2026-10-21", time_support="snapshot")
        kw = dict(
            collection_method="crowd_mapped",
            data_nature="modelled_estimate",
            how="footprints counted per GN division",
        )
        number = geos.total(rolled.count)
        area = geos.total(rolled.area_m2)
        emitter.add(lay, "buildings_mapped", number, **obs, **kw)
        emitter.add(lay, "building_footprint_area", area / 10_000.0, **obs, **kw)
        emitter.add(lay, "building_footprint_mean", _ratio(area, number), **obs, **kw)
        small = geos.total(rolled.small)
        large = geos.total(rolled.large)
        emitter.add(lay, "buildings_small", small, **obs, **kw)
        emitter.add(lay, "buildings_large", large, **obs, **kw)
        emitter.add(lay, "buildings_small_share", _ratio(small, number, 100), **obs, **kw)
        emitter.add(lay, "buildings_large_share", _ratio(large, number, 100), **obs, **kw)
        emitter.add(
            lay,
            "building_compactness_mean",
            _ratio(geos.total(rolled.compact_sum), geos.total(rolled.shaped)),
            **obs,
            **{**kw, "how": "mean over footprints per GN division"},
        )
        if land_m2 is not None:
            land = geos.total(land_m2)
            where = {**kw, "how": "footprints per land area of the GN division"}
            emitter.add(lay, "buildings_per_km2", _ratio(number, land, 1e6), **obs, **where)
            emitter.add(lay, "building_coverage_share", _ratio(area, land, 100), **obs, **where)
        buildings_out["rollup"] = rolled
    frame = pd.concat(emitter.frames, ignore_index=True) if emitter.frames else pd.DataFrame()
    if len(frame):
        frame["note_ids"] = [[] for _ in range(len(frame))]
        frame["release"] = None
    return frame, sets
