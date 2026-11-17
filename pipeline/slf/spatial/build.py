"""Landscape roll-ups: open raster layers summarised for every place in the spine.

Each layer is read from immutable snapshots under ``raw/``, summed over GN divisions on the
raster's own pixel grid (:mod:`slf.spatial.zonal`), and added up through the hierarchy. Only
additive components (areas, weighted sums) are stored per GN; every published share or mean is
recomputed from those components at each level, so a district value is exactly what its GN
divisions give.

Nothing here is a fact about people. Every value is a `modelled_estimate` carrying the pixel
size its information comes from.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio

from slf.spatial import zonal
from slf.spatial.layers import (
    GHSL_EPOCHS,
    HA,
    LOSS_YEARS,
    SMOD_GROUPS,
    SPECS,
    WORLDCOVER_CLASSES,
)

VINTAGE = "cod-ab-v03"


@dataclass(frozen=True)
class Held:
    path: Path
    sha256: str
    url: str
    retrieved_at: str


def held_files(roots: list[Path], source: str, dataset: str) -> list[Held]:
    """The newest snapshot of each file of a dataset, across the given data roots."""
    newest: dict[str, Held] = {}
    for root in roots:
        folder = root / "raw" / source / dataset
        for meta_path in sorted(folder.glob("*/*.meta.json")):
            meta = json.loads(meta_path.read_text())
            data = meta_path.with_name(meta_path.name.removesuffix(".meta.json"))
            held = Held(data, meta["sha256"], meta.get("url") or "", meta["retrieved_at"])
            if data.name not in newest or newest[data.name].retrieved_at < held.retrieved_at:
                newest[data.name] = held
    return [newest[name] for name in sorted(newest)]


def digest(files: list[Held]) -> str:
    """One sha256 standing for a set of snapshot files (the hash of their sorted hashes)."""
    joined = "\n".join(sorted(f.sha256 for f in files))
    return hashlib.sha256(joined.encode()).hexdigest()


@contextmanager
def open_raster(held: Held) -> Iterator[rasterio.DatasetReader]:
    if held.path.suffix == ".zip":
        tif = next(n for n in zipfile.ZipFile(held.path).namelist() if n.endswith(".tif"))
        with rasterio.open(f"zip://{held.path}!{tif}") as dataset:
            yield dataset
    else:
        with rasterio.open(held.path) as dataset:
            yield dataset


@dataclass
class Layer:
    """Additive components per GN for one dataset, with what they were read from."""

    dataset: str
    files: list[Held]
    floor: str
    locator: str
    blocks: int = 0
    sums: dict[str, np.ndarray] = field(default_factory=dict)
    minima: dict[str, np.ndarray] = field(default_factory=dict)
    maxima: dict[str, np.ndarray] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def _run(files: list[Held], zones: zonal.Zones, reducer: Any, **kw: Any) -> int:
    blocks = 0
    for held in files:
        with open_raster(held) as dataset:
            blocks += zonal.walk([dataset], zones, reducer, **kw)
    return blocks


def terrain(roots: list[Path], zones: zonal.Zones) -> Layer:
    files = held_files(roots, "copernicus", "copernicus-dem-glo30")
    reducer = zonal.Terrain(len(zones))
    layer = Layer(
        "copernicus-dem-glo30",
        files,
        "grid-30m",
        f"Copernicus DEM GLO-30, {len(files)} one-degree tiles, band 1 (metres above EGM2008); "
        "pixels whose centre is inside the place",
    )
    layer.blocks = _run(files, zones, reducer, halo=1)
    e, s = reducer.elevation, reducer.slope
    layer.sums = {
        "terrain_area": e.area[1:],
        "elevation_wsum": e.weighted[1:],
        "slope_wsum": s.weighted[1:],
        "slope_area": s.area[1:],
        "steep_area": s.above[0][1:],
    }
    layer.minima = {"elevation_min": e.minimum[1:]}
    layer.maxima = {"elevation_max": e.maximum[1:]}
    return layer


def land_cover(roots: list[Path], zones: zonal.Zones) -> Layer:
    files = held_files(roots, "esa", "esa-worldcover-2021")
    slugs = [slug for slug, _ in WORLDCOVER_CLASSES.values()]
    lut = np.full(256, len(slugs) + 1, dtype=np.int64)  # other classes
    lut[0] = len(slugs)  # no data
    for i, value in enumerate(WORLDCOVER_CLASSES):
        lut[value] = i
    reducer = zonal.ClassAreas(len(zones), lut, len(slugs) + 2)
    layer = Layer(
        "esa-worldcover-2021",
        files,
        "grid-10m",
        f"ESA WorldCover 2021 v200 map, {len(files)} three-degree tiles, band 1 (class value); "
        "pixels whose centre is inside the place",
    )
    layer.blocks = _run(files, zones, reducer)
    table = reducer.table()
    for i, slug in enumerate(slugs):
        layer.sums[f"wc_{slug}"] = table[:, i]
    layer.sums["wc_nodata"] = table[:, len(slugs)]
    layer.sums["wc_other"] = table[:, len(slugs) + 1]
    layer.sums["wc_mapped"] = table[:, : len(slugs)].sum(axis=1) + table[:, len(slugs) + 1]
    return layer


def forest(roots: list[Path], zones: zonal.Zones) -> Layer:
    files = held_files(roots, "umd-glad", "hansen-global-forest-change")
    reducer = zonal.ForestChange(len(zones), canopy_threshold=30, last_year=LOSS_YEARS[-1] - 2000)
    layer = Layer(
        "hansen-global-forest-change",
        files,
        "grid-30m",
        "Global Forest Change v1.12 (2000-2024), tiles 10N_070E and 10N_080E, layers "
        "treecover2000 (canopy >= 30%) and lossyear; pixels whose centre is inside the place",
    )
    tiles = sorted(
        {f.path.name.rsplit("_", 2)[-2] + "_" + f.path.name.rsplit("_", 1)[-1] for f in files}
    )
    for tile in tiles:
        pair = {
            ("treecover2000" if "treecover2000" in f.path.name else "lossyear"): f
            for f in files
            if f.path.name.endswith(tile)
        }
        with ExitStack() as stack:
            cover = stack.enter_context(open_raster(pair["treecover2000"]))
            loss = stack.enter_context(open_raster(pair["lossyear"]))
            layer.blocks += zonal.walk([cover, loss], zones, reducer)
    layer.sums = {
        "forest_land": reducer.land[1:],
        "tree_cover_2000": reducer.cover[1:],
        "loss_outside_cover": reducer.loss_outside_cover[1:],
    }
    table = reducer.loss_table()
    for k, year in enumerate(LOSS_YEARS):
        layer.sums[f"loss_{year}"] = table[:, k]
    return layer


def surface_water(roots: list[Path], zones: zonal.Zones) -> Layer:
    files = held_files(roots, "jrc", "jrc-global-surface-water")
    # classes: 0 never water, 1 water in 1-74% of observations, 2 water in >= 75%, 3 no data
    lut = np.full(256, 3, dtype=np.int64)
    lut[0] = 0
    lut[1:75] = 1
    lut[75:101] = 2
    reducer = zonal.ClassAreas(len(zones), lut, 4)
    layer = Layer(
        "jrc-global-surface-water",
        files,
        "grid-30m",
        "JRC Global Surface Water v1.4 occurrence 1984-2021, tiles 70E_10N and 80E_10N, band 1 "
        "(percent of valid observations with water); pixels whose centre is inside the place",
    )
    layer.blocks = _run(files, zones, reducer)
    table = reducer.table()
    layer.sums = {
        "gsw_measured": table[:, :3].sum(axis=1),
        "gsw_ever": table[:, 1] + table[:, 2],
        "gsw_permanent": table[:, 2],
        "gsw_nodata": table[:, 3],
    }
    return layer


def built_up(roots: list[Path], zones: zonal.Zones) -> Layer:
    files = held_files(roots, "ghsl", "ghsl-built-up")
    layer = Layer(
        "ghsl-built-up",
        files,
        "grid-100m",
        "GHS-BUILT-S R2023A, 100 m Mollweide tiles R8_C26, R8_C27, R9_C26, R9_C27, band 1 (m² of "
        "built-up surface per cell); each cell split into 25 sub-cells of 20 m and shared between "
        "places by sub-cell centre",
    )
    for epoch in GHSL_EPOCHS:
        chosen = [f for f in files if f"_E{epoch}_" in f.path.name]
        if len(chosen) != 4:
            layer.notes.append(f"epoch {epoch}: {len(chosen)} of 4 tiles held; epoch skipped")
            continue
        reducer = zonal.Moments(len(zones), valid=lambda a: a <= 10_000)
        layer.blocks += _run(chosen, zones, reducer, upsample=5)
        layer.sums[f"built_{epoch}"] = reducer.weighted[1:] / 10_000.0
        layer.sums[f"built_measured_{epoch}"] = reducer.area[1:]
    return layer


def settlement(roots: list[Path], zones: zonal.Zones) -> Layer:
    files = held_files(roots, "ghsl", "ghsl-settlement-model")
    groups = ["urban_centre", "urban_cluster", "rural", "water", "nodata"]
    lut = np.full(65536, 4, dtype=np.int64)
    for value, group in SMOD_GROUPS.items():
        lut[value] = groups.index(group)
    reducer = _Int16Classes(len(zones), lut, len(groups))
    layer = Layer(
        "ghsl-settlement-model",
        files,
        "grid-1km",
        "GHS-SMOD R2023A 2020 (V2-0), 1 km Mollweide tiles R8_C26, R8_C27, R9_C26, R9_C27, band 1 "
        "(Degree of Urbanisation level 2 class); each cell split into 2,500 sub-cells of 20 m",
    )
    layer.blocks = _run(files, zones, reducer, upsample=50, block=200)
    table = reducer.table()
    layer.sums = {
        "smod_measured": table[:, :4].sum(axis=1),
        "smod_urban_centre": table[:, 0],
        "smod_urban": table[:, 0] + table[:, 1],
        "smod_nodata": table[:, 4],
    }
    return layer


class _Int16Classes(zonal.ClassAreas):
    """ClassAreas for signed 16-bit class rasters (negative no-data becomes a high index)."""

    def __call__(self, labels: np.ndarray, arrays: list[np.ndarray], areas: np.ndarray) -> None:
        super().__call__(labels, [arrays[0].astype(np.uint16)], areas)


# --- hierarchy -------------------------------------------------------------------------------


@dataclass
class Hierarchy:
    ids: list[str]  # every place, GN first (in zone order)
    level: dict[str, int]
    members: dict[str, np.ndarray]  # place -> indices of its GN divisions

    @classmethod
    def from_spine(cls, zones: zonal.Zones, spine_dir: Path) -> Hierarchy:
        geos = pd.read_parquet(spine_dir / "geographies.parquet")
        relations = pd.read_parquet(spine_dir / "geography_relations.parquet")
        parent = dict(zip(geos.geography_id, geos.parent_id, strict=True))
        level = {str(k): int(v) for k, v in zip(geos.geography_id, geos.level, strict=True)}
        index = {gid: i for i, gid in enumerate(zones.ids)}
        members: dict[str, list[int]] = {}
        for gid, i in index.items():
            members[gid] = [i]
            up = parent.get(gid)
            while isinstance(up, str) and up:
                members.setdefault(up, []).append(i)
                up = parent.get(up)
        composed = relations[relations.relation == "composed_of"]
        for unit, rows in composed.groupby("geography_id"):
            members[str(unit)] = [index[r] for r in rows.related_id if r in index]
        ids = list(zones.ids) + sorted(
            (g for g in members if g not in index), key=lambda g: (-level.get(g, 0), g)
        )
        return cls(ids, level, {g: np.array(members[g], dtype=np.int64) for g in ids})

    def total(self, values: np.ndarray) -> np.ndarray:
        return np.array([values[self.members[g]].sum() for g in self.ids])

    def lowest(self, values: np.ndarray) -> np.ndarray:
        return np.array([values[self.members[g]].min() for g in self.ids])

    def highest(self, values: np.ndarray) -> np.ndarray:
        return np.array([values[self.members[g]].max() for g in self.ids])


# --- observations ----------------------------------------------------------------------------


def _ratio(num: np.ndarray, den: np.ndarray, scale: float = 1.0) -> np.ndarray:
    with np.errstate(invalid="ignore", divide="ignore"):
        out = scale * num / den
    out[~(den > 0)] = np.nan
    return out


@dataclass
class Emitter:
    hierarchy: Hierarchy
    frames: list[pd.DataFrame] = field(default_factory=list)

    def add(
        self,
        layer: Layer,
        indicator: str,
        values: np.ndarray,
        *,
        period: str,
        start: str,
        end: str,
        time_support: str,
        locator: str | None = None,
        collection_method: str = "satellite_observation",
        data_nature: str = "modelled_estimate",
        first: int | None = None,
        how: str = "zonal sum over GN divisions",
    ) -> None:
        spec = SPECS[indicator]
        ids = self.hierarchy.ids[:first]
        values = values[:first]
        rounded = np.round(values.astype(np.float64), spec.decimals + 2)
        missing = ~np.isfinite(rounded)
        frame = pd.DataFrame(
            {
                "claim_id": [f"{layer.dataset}:{g}:{indicator}:{period}" for g in ids],
                "indicator_id": indicator,
                "geography_id": ids,
                "geography_vintage": VINTAGE,
                "period": period,
                "time_start": start,
                "time_end": end,
                "time_support": time_support,
                "support_type": "area_mean" if spec.measure_type == "mean" else "area_total",
                "footprint_ref": ids,
                "information_footprint_ref": layer.floor,
                "universe": spec.universe,
                "collection_method": collection_method,
                "sensitivity": "public",
                "revision_status": "final",
                "preferred": True,
                "preferred_reason": f"Only claim for this indicator: {layer.dataset}.",
                "breakdown": None,
                "value": np.where(missing, np.nan, rounded),
                "value_status": np.where(missing, "not_available", "normal"),
                "unit": spec.unit,
                "data_nature": data_nature,
                "verification": "machine_extracted",
                "dataset_id": layer.dataset,
                "snapshot_sha256": digest(layer.files),
                "source_locator": (locator or layer.locator)
                + f"; {how} ({VINTAGE})"
                + ("" if first else ", summed to higher levels"),
            }
        )
        self.frames.append(frame)


def emit_all(layers: dict[str, Layer], h: Hierarchy) -> pd.DataFrame:
    out = Emitter(h)
    t = layers["terrain"]
    obs: dict[str, Any] = dict(
        period="2013", start="2010-12-12", end="2015-01-16", time_support="observed_around"
    )
    area = h.total(t.sums["terrain_area"])
    out.add(t, "terrain_measured_area", area / HA, **obs)
    out.add(t, "elevation_mean", _ratio(h.total(t.sums["elevation_wsum"]), area), **obs)
    out.add(t, "elevation_min", h.lowest(t.minima["elevation_min"]), **obs)
    out.add(t, "elevation_max", h.highest(t.maxima["elevation_max"]), **obs)
    slope_area = h.total(t.sums["slope_area"])
    out.add(t, "slope_mean", _ratio(h.total(t.sums["slope_wsum"]), slope_area), **obs)
    steep = h.total(t.sums["steep_area"])
    out.add(t, "steep_land_area", steep / HA, **obs)
    out.add(t, "steep_land_share", _ratio(steep, slope_area, 100), **obs)

    w = layers["land_cover"]
    obs: dict[str, Any] = dict(
        period="2021", start="2021-01-01", end="2021-12-31", time_support="observed_around"
    )
    mapped = h.total(w.sums["wc_mapped"])
    out.add(w, "land_cover_mapped_area", mapped / HA, **obs)
    for value, (slug, _) in WORLDCOVER_CLASSES.items():
        a = h.total(w.sums[f"wc_{slug}"])
        loc = f"{w.locator}; class value {value}"
        out.add(w, f"land_cover_{slug}_area", a / HA, locator=loc, **obs)
        out.add(w, f"land_cover_{slug}_share", _ratio(a, mapped, 100), locator=loc, **obs)

    f = layers["forest"]
    obs: dict[str, Any] = dict(
        period="2000", start="2000-01-01", end="2000-12-31", time_support="observed_around"
    )
    land = h.total(f.sums["forest_land"])
    cover = h.total(f.sums["tree_cover_2000"])
    out.add(f, "forest_measured_area", land / HA, **obs)
    out.add(f, "tree_cover_2000_area", cover / HA, **obs)
    out.add(f, "tree_cover_2000_share", _ratio(cover, land, 100), **obs)
    total_loss = np.zeros(len(h.ids))
    for year in LOSS_YEARS:
        loss = h.total(f.sums[f"loss_{year}"])
        total_loss += loss
        out.add(
            f,
            "tree_cover_loss_area",
            loss / HA,
            period=str(year),
            start=f"{year}-01-01",
            end=f"{year}-12-31",
            time_support="interval_total",
            locator=f"{f.locator}; lossyear value {year - 2000}",
        )
    span: dict[str, Any] = dict(
        period="2024", start="2001-01-01", end="2024-12-31", time_support="interval_total"
    )
    out.add(f, "tree_cover_loss_total_area", total_loss / HA, **span)
    out.add(f, "tree_cover_loss_total_share", _ratio(total_loss, cover, 100), **span)

    g = layers["surface_water"]
    obs: dict[str, Any] = dict(
        period="2021", start="1984-03-16", end="2021-12-31", time_support="interval_mean"
    )
    measured = h.total(g.sums["gsw_measured"])
    out.add(g, "surface_water_measured_area", measured / HA, **obs)
    for key in ("permanent", "ever"):
        a = h.total(g.sums[f"gsw_{key}"])
        out.add(g, f"surface_water_{key}_area", a / HA, **obs)
        out.add(g, f"surface_water_{key}_share", _ratio(a, measured, 100), **obs)

    b = layers["built_up"]
    for epoch in GHSL_EPOCHS:
        if f"built_{epoch}" not in b.sums:
            continue
        obs: dict[str, Any] = dict(
            period=str(epoch),
            start=f"{epoch}-01-01",
            end=f"{epoch}-12-31",
            time_support="observed_around",
        )
        loc = b.locator.replace("GHS-BUILT-S R2023A,", f"GHS-BUILT-S R2023A epoch {epoch},")
        measured = h.total(b.sums[f"built_measured_{epoch}"])
        built = h.total(b.sums[f"built_{epoch}"])
        out.add(b, "built_up_measured_area", measured / HA, locator=loc, **obs)
        out.add(b, "built_up_surface_area", built / HA, locator=loc, **obs)
        out.add(b, "built_up_surface_share", _ratio(built, measured, 100), locator=loc, **obs)

    s = layers["settlement"]
    obs: dict[str, Any] = dict(
        period="2020", start="2020-01-01", end="2020-12-31", time_support="observed_around"
    )
    measured = h.total(s.sums["smod_measured"])
    out.add(s, "settlement_measured_area", measured / HA, **obs)
    for key in ("urban_centre", "urban"):
        a = h.total(s.sums[f"smod_{key}"])
        out.add(s, f"settlement_{key}_area", a / HA, **obs)
        out.add(s, f"settlement_{key}_share", _ratio(a, measured, 100), **obs)

    frame = pd.concat(out.frames, ignore_index=True)
    frame["note_ids"] = [[] for _ in range(len(frame))]
    frame["release"] = None
    return frame


LAYER_BUILDERS = {
    "terrain": terrain,
    "land_cover": land_cover,
    "forest": forest,
    "surface_water": surface_water,
    "built_up": built_up,
    "settlement": settlement,
}


def load_zones(spine_dir: Path) -> zonal.Zones:
    versions = gpd.read_parquet(spine_dir / "geography_versions.geoparquet")
    gn: Any = versions[(versions.level == 4) & (versions.vintage == VINTAGE)]
    return zonal.Zones.from_frame(gpd.GeoDataFrame(gn.sort_values("geography_id")))


# --- driver and QA ---------------------------------------------------------------------------


def _cached(name: str, roots: list[Path], zones: zonal.Zones, cache_dir: Path) -> Layer:
    """Per-GN components are cached by the hash of the snapshots they were read from."""
    import pickle

    probe = LAYER_SOURCES[name]
    key = digest(held_files(roots, *probe))[:16]
    path = cache_dir / f"{name}-{key}.pkl"
    if path.exists():
        with path.open("rb") as handle:
            return pickle.load(handle)
    layer = LAYER_BUILDERS[name](roots, zones)
    cache_dir.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        pickle.dump(layer, handle)
    return layer


LAYER_SOURCES = {
    "terrain": ("copernicus", "copernicus-dem-glo30"),
    "land_cover": ("esa", "esa-worldcover-2021"),
    "forest": ("umd-glad", "hansen-global-forest-change"),
    "surface_water": ("jrc", "jrc-global-surface-water"),
    "built_up": ("ghsl", "ghsl-built-up"),
    "settlement": ("ghsl", "ghsl-settlement-model"),
}

MEASURED = {
    "terrain": "terrain_area",
    "land_cover": "wc_mapped",
    "forest": "forest_land",
    "surface_water": "gsw_measured",
    "built_up": "built_measured_2020",
    "settlement": "smod_measured",
}

WIDE = [
    ("elevation_mean", "2013"),
    ("elevation_max", "2013"),
    ("slope_mean", "2013"),
    ("steep_land_share", "2013"),
    ("land_cover_tree_share", "2021"),
    ("land_cover_cropland_share", "2021"),
    ("land_cover_grassland_share", "2021"),
    ("land_cover_built_up_share", "2021"),
    ("land_cover_water_share", "2021"),
    ("land_cover_mangrove_share", "2021"),
    ("tree_cover_2000_share", "2000"),
    ("tree_cover_loss_total_share", "2024"),
    ("surface_water_permanent_share", "2021"),
    ("surface_water_ever_share", "2021"),
    ("built_up_surface_share", "1975"),
    ("built_up_surface_share", "2000"),
    ("built_up_surface_share", "2020"),
    ("settlement_urban_share", "2020"),
    ("settlement_urban_centre_share", "2020"),
]


def check_frame(frame: pd.DataFrame) -> list[str]:
    """The generic observation rules (slf.dataset.check_observations), applied to all rows."""
    from slf.dataset import REQUIRED_OBSERVATION_FIELDS
    from slf.schemas import SUPPORT_TYPES, TIME_SUPPORTS

    errors: list[str] = []
    normal = frame.value_status == "normal"
    for column in REQUIRED_OBSERVATION_FIELDS:
        rows: Any = frame[column].isna() | (frame[column].astype(str) == "")
        if column == "value":
            rows &= normal
        if rows.any():
            errors.append(f"{int(rows.sum())} rows missing {column}")
    if frame.claim_id.duplicated().any():
        errors.append(f"{int(frame.claim_id.duplicated().sum())} duplicate claim ids")
    if not set(frame.support_type).issubset(SUPPORT_TYPES):
        errors.append("unknown support_type")
    if not set(frame.time_support).issubset(TIME_SUPPORTS):
        errors.append("unknown time_support")
    if (frame.time_start > frame.time_end).any():
        errors.append("time_start after time_end")
    shares = frame[(frame.unit == "percent") & normal]
    bad = shares[(shares.value < 0) | (shares.value > 100.0001)]
    if len(bad):
        errors.append(f"{len(bad)} shares outside 0-100")
    negative = frame[normal & (frame.unit == "hectares") & (frame.value < 0)]
    if len(negative):
        errors.append(f"{len(negative)} negative areas")
    return errors


def build(roots: list[Path], spine_dir: Path, out_dir: Path) -> dict[str, Any]:
    zones = load_zones(spine_dir)
    hierarchy = Hierarchy.from_spine(zones, spine_dir)
    layers = {name: _cached(name, roots, zones, out_dir / "cache") for name in LAYER_BUILDERS}
    from slf.spatial import points as point_layers

    versions = gpd.read_parquet(spine_dir / "geography_versions.geoparquet")
    current: Any = versions[(versions.level == 4) & (versions.vintage == VINTAGE)]
    gn: Any = current.sort_values("geography_id")
    labels = gpd.GeoSeries(gpd.points_from_xy(gn.label_lon, gn.label_lat), crs="EPSG:4326")
    out_dir.mkdir(parents=True, exist_ok=True)
    extra: dict[str, Any] = {}
    point_frame, point_sets = point_layers.build(roots, zones, hierarchy, labels, out_dir, extra)
    frame = pd.concat([emit_all(layers, hierarchy), point_frame], ignore_index=True)
    errors = check_frame(frame)
    out_dir.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(out_dir / "observations.parquet", index=False)

    components = pd.DataFrame({"geography_id": zones.ids})
    for layer in layers.values():
        for key, values in {**layer.sums, **layer.minima, **layer.maxima}.items():
            components[key] = values
    components.to_parquet(out_dir / "components_gn.parquet", index=False)

    geos = pd.read_parquet(spine_dir / "geographies.parquet")[
        ["geography_id", "level", "name_en", "parent_id"]
    ]
    wide: Any = geos.copy()
    for indicator, period in WIDE:
        rows: Any = frame[(frame.indicator_id == indicator) & (frame.period == period)]
        wide = wide.merge(
            rows[["geography_id", "value"]].rename(columns={"value": f"{indicator}_{period}"}),
            on="geography_id",
            how="left",
        )
    wide.sort_values(["level", "geography_id"]).to_csv(
        out_dir / "landscape_places.csv", index=False
    )

    sources = {
        layer.dataset: {
            "snapshot_sha256": digest(layer.files),
            "information_floor": layer.floor,
            "files": [
                {
                    "file": f.path.name,
                    "sha256": f.sha256,
                    "url": f.url,
                    "retrieved_at": f.retrieved_at,
                }
                for f in layer.files
            ],
        }
        for layer in layers.values()
    }
    (out_dir / "sources.json").write_text(json.dumps(sources, indent=1) + "\n")

    for points in point_sets.values():
        sources[points.dataset] = {
            "snapshot_sha256": digest(points.files),
            "information_floor": "point",
            "licence": points.licence,
            "files": [
                {
                    "file": f.path.name,
                    "sha256": f.sha256,
                    "url": f.url,
                    "retrieved_at": f.retrieved_at,
                }
                for f in points.files
            ],
        }
    (out_dir / "sources.json").write_text(json.dumps(sources, indent=1) + "\n")
    spine_area = gn.geometry.to_crs(5235).area.to_numpy()
    qa = render_qa(layers, zones, hierarchy, frame, spine_area, errors)
    qa += render_points_qa(point_sets, frame)
    if "rollup" in extra:
        qa += render_buildings_qa(extra["rollup"], zones, frame, spine_area)
    (out_dir / "qa.md").write_text(qa, encoding="utf-8")
    return {"rows": len(frame), "errors": errors, "indicators": frame.indicator_id.nunique()}


def render_buildings_qa(
    rolled: Any, zones: zonal.Zones, frame: pd.DataFrame, spine_area: np.ndarray
) -> str:
    built: Any = frame[
        (frame.indicator_id == "built_up_surface_area")
        & (frame.period == "2020")
        & (frame.geography_id == "LK")
    ]
    lines = [
        "",
        "## 8. Building footprints (Overture Maps, ODbL)",
        "",
        f"- Footprints read: {rolled.read:,}; inside a GN polygon: {int(rolled.count.sum()):,}; "
        f"outside every GN polygon: {rolled.unresolved:,}.",
        f"- Total footprint area: {rolled.area_m2.sum() / 1e6:,.1f} km² "
        f"({100 * rolled.area_m2.sum() / spine_area.sum():.2f}% of the country). For comparison, "
        f"GHS-BUILT-S 2020 gives {float(built.value.iloc[0]) / 100:,.1f} km² of built-up surface, "
        "from different imagery and a different method.",
        f"- Footprints with a recorded height: {int(rolled.with_height.sum()):,}.",
        f"- GN divisions with no footprint: {int((rolled.count == 0).sum())}.",
        "",
        "| First-listed source of the footprint | Footprints in the extract | Inside a GN polygon |",
        "|---|---:|---:|",
    ]
    for name, total in sorted(rolled.source_totals.items(), key=lambda kv: -kv[1]):
        inside = rolled.by_source.get(name, rolled.by_source["other"])
        lines.append(f"| {name} | {total:,} | {int(inside.sum()):,} |")
    return "\n".join(lines) + "\n"


def render_points_qa(point_sets: dict[str, Any], frame: pd.DataFrame) -> str:
    lines = [
        "",
        "## 7. Point layers resolved to GN divisions",
        "",
        "| Dataset | Licence | Records read | Records used | Inside a GN polygon | Outside every GN polygon |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for points in point_sets.values():
        used = len(points.frame)
        lines.append(
            f"| {points.dataset} | {points.licence} | {points.read:,} | {used:,} "
            f"| {used - points.unresolved:,} | {points.unresolved:,} |"
        )
    lines += [
        "",
        "Points outside every GN polygon (in the sea, on unmapped islets, or wrongly placed) are "
        "kept in `features/<dataset>.parquet` with an empty `gn_id`; they are in no place's count.",
        "",
    ]
    for points in point_sets.values():
        lines += [f"- {points.dataset}: {note}." for note in points.notes]
    national: Any = frame[
        (frame.geography_id == "LK")
        & frame.indicator_id.isin(
            [
                "schools_located",
                "schools_connected",
                "health_facilities_mapped",
                "places_listed",
                "wikidata_items",
            ]
        )
    ]
    lines += ["", "| National count (LK) | Value |", "|---|---:|"]
    lines += [f"| {r.indicator_id} | {r.value:,.0f} |" for r in national.itertuples()]
    for indicator in ("nearest_school_distance", "nearest_health_facility_distance"):
        rows = frame[frame.indicator_id == indicator].value
        if len(rows):
            q = rows.quantile([0.5, 0.9, 0.99, 1.0]).to_numpy()
            lines.append(
                f"| {indicator} (km): median, p90, p99, max over GN divisions "
                f"| {q[0]:.2f}, {q[1]:.2f}, {q[2]:.2f}, {q[3]:.2f} |"
            )
    return "\n".join(lines) + "\n"


def render_qa(
    layers: dict[str, Layer],
    zones: zonal.Zones,
    h: Hierarchy,
    frame: pd.DataFrame,
    spine_area: np.ndarray,
    errors: list[str],
) -> str:
    def national(indicator: str, period: str) -> float:
        row = frame[
            (frame.indicator_id == indicator)
            & (frame.period == period)
            & (frame.geography_id == "LK")
        ]
        return float(row.value.iloc[0])

    lines = [
        "# QA: landscape roll-ups",
        "",
        "Generated by `slf spatial build`. Every number below was computed in this run.",
        "",
        f"- Places: {len(h.ids)} ({len(zones)} GN divisions and {len(h.ids) - len(zones)} higher units)",
        f"- Observations: {len(frame):,} rows, {frame.indicator_id.nunique()} indicators",
        f"- Rows with no value (`not_available`): {int((frame.value_status != 'normal').sum()):,}",
        f"- Rule checks on all rows: {'passed' if not errors else 'FAILED: ' + '; '.join(errors)}",
        "",
        "## 1. Sources read",
        "",
        "| Dataset | Files | Information floor | Combined sha256 (first 16) | Raster blocks used |",
        "|---|---:|---|---|---:|",
    ]
    for layer in layers.values():
        lines.append(
            f"| {layer.dataset} | {len(layer.files)} | {layer.floor} | `{digest(layer.files)[:16]}` "
            f"| {layer.blocks} |"
        )
    lines += [
        "",
        "Per-file hashes, URLs and retrieval times are in `sources.json` beside this report.",
        "",
        "## 2. Coverage: measured area against the spine's own area",
        "",
        "The spine area is the GN polygon area in EPSG:5235. The measured area is the sum of the "
        "ground areas of the pixels (or sub-cells) whose centre falls inside the polygon. A ratio "
        "far from 1 means the place is small compared with the pixel.",
        "",
        "| Layer | Measured km² | Spine km² | Ratio | GN ratio p1 | p50 | p99 | GNs outside 0.9-1.1 | "
        "GNs with no pixel |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, layer in layers.items():
        measured = layer.sums[MEASURED[name]]
        ratio = measured / spine_area
        p1, p50, p99 = np.percentile(ratio, [1, 50, 99])
        lines.append(
            f"| {name} | {measured.sum() / 1e6:,.1f} | {spine_area.sum() / 1e6:,.1f} "
            f"| {measured.sum() / spine_area.sum():.4f} | {p1:.3f} | {p50:.3f} | {p99:.3f} "
            f"| {int(((ratio < 0.9) | (ratio > 1.1)).sum())} | {int((measured == 0).sum())} |"
        )
    wc = layers["land_cover"].sums
    f = layers["forest"].sums
    lines += [
        "",
        "## 3. National figures (LK), for cross-checking against published totals",
        "",
        "| Figure | Value |",
        "|---|---:|",
        f"| Mean elevation (m) | {national('elevation_mean', '2013'):.1f} |",
        f"| Highest pixel (m) | {national('elevation_max', '2013'):.1f} |",
        f"| Lowest pixel (m) | {national('elevation_min', '2013'):.1f} |",
        f"| Mean slope (degrees) | {national('slope_mean', '2013'):.2f} |",
        f"| Steep land share, slope over 15° (%) | {national('steep_land_share', '2013'):.2f} |",
    ]
    for slug, label in WORLDCOVER_CLASSES.values():
        lines.append(
            f"| WorldCover 2021: {label} (% of mapped area) "
            f"| {national(f'land_cover_{slug}_share', '2021'):.2f} |"
        )
    lines += [
        f"| WorldCover pixels with no data inside GN polygons (km²) | {wc['wc_nodata'].sum() / 1e6:.2f} |",
        f"| WorldCover pixels of other classes (km²) | {wc['wc_other'].sum() / 1e6:.2f} |",
        f"| Tree cover 2000, canopy ≥ 30% (ha) | {national('tree_cover_2000_area', '2000'):,.0f} |",
        f"| Tree cover 2000 (% of area) | {national('tree_cover_2000_share', '2000'):.2f} |",
        f"| Tree cover loss 2001-2024 inside that cover (ha) | {national('tree_cover_loss_total_area', '2024'):,.0f} |",
        f"| Loss as % of 2000 tree cover | {national('tree_cover_loss_total_share', '2024'):.2f} |",
        f"| Loss pixels outside the ≥ 30% cover, not counted (ha) | {f['loss_outside_cover'].sum() / HA:,.0f} |",
        f"| Surface water in ≥ 75% of observations (% of area) | {national('surface_water_permanent_share', '2021'):.2f} |",
        f"| Surface water ever detected (% of area) | {national('surface_water_ever_share', '2021'):.2f} |",
        f"| Urban centre or cluster, GHS-SMOD 2020 (% of area) | {national('settlement_urban_share', '2020'):.2f} |",
        f"| Urban centre, GHS-SMOD 2020 (% of area) | {national('settlement_urban_centre_share', '2020'):.2f} |",
        "",
        "### Tree cover loss by year (ha, LK)",
        "",
        "| Year | Loss (ha) |",
        "|---|---:|",
    ]
    loss: Any = frame[(frame.indicator_id == "tree_cover_loss_area") & (frame.geography_id == "LK")]
    for row in loss.sort_values("period").itertuples():
        lines.append(f"| {row.period} | {row.value:,.0f} |")
    lines += [
        "",
        "### Built-up surface by epoch (GHS-BUILT-S, LK)",
        "",
        "| Epoch | Built-up surface (ha) | Share of area (%) |",
        "|---|---:|---:|",
    ]
    for epoch in GHSL_EPOCHS:
        if f"built_{epoch}" in layers["built_up"].sums:
            lines.append(
                f"| {epoch} | {national('built_up_surface_area', str(epoch)):,.0f} "
                f"| {national('built_up_surface_share', str(epoch)):.3f} |"
            )
    lines += ["", "## 4. Internal consistency", ""]
    slugs = [slug for slug, _ in WORLDCOVER_CLASSES.values()]
    class_sum = sum(wc[f"wc_{s}"] for s in slugs) + wc["wc_other"]
    lines.append(
        f"- WorldCover class areas sum to the mapped area for every GN: max difference "
        f"{np.abs(class_sum - wc['wc_mapped']).max():.6f} m²."
    )
    up = h.total(layers["terrain"].sums["terrain_area"])
    lines.append(
        f"- Hierarchy: the country's terrain area equals the sum over GN divisions: "
        f"{up[h.ids.index('LK')] / 1e6:,.3f} km² against {layers['terrain'].sums['terrain_area'].sum() / 1e6:,.3f} km²."
    )
    by_level: dict[int, int] = {}
    for g in h.ids:
        by_level[h.level.get(g, -1)] = by_level.get(h.level.get(g, -1), 0) + 1
    lines.append(f"- Places by level: {dict(sorted(by_level.items()))}.")
    notes = [n for layer in layers.values() for n in layer.notes]
    lines += ["", "## 5. Notes from the run", ""] + ([f"- {n}" for n in notes] or ["- None."])
    missing: Any = frame[frame.value_status != "normal"]
    lines += ["", "## 6. Values not available", ""]
    if len(missing):
        counts = missing.groupby("indicator_id").size().sort_values(ascending=False)
        lines += ["| Indicator | Rows without a value |", "|---|---:|"]
        lines += [f"| {k} | {v} |" for k, v in counts.items()]
        lines.append("")
        lines.append(
            "A share has no value when its denominator is zero (for example the share of "
            "year-2000 tree cover lost, in a place with no tree cover in 2000)."
        )
    else:
        lines.append("- None.")
    return "\n".join(lines) + "\n"
