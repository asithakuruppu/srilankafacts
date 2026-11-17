"""Zonal statistics: what each raster says about each GN division.

A raster is walked in blocks. For every block that touches a zone, the zone polygons are burnt
into a label grid on the raster's own pixel grid (in the raster's own CRS, so the source pixels
are never resampled), and a reducer adds each pixel's ground area to its zone. Areas are in
square metres: exact ellipsoidal areas for geographic rasters, the constant cell area for
equal-area rasters.

Coarse rasters can be split into ``upsample`` by ``upsample`` sub-cells before labelling, so a
100 m cell that straddles two small GN divisions is shared between them by area instead of being
given whole to one. The information is still that of the source cell (the information floor).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

import geopandas as gpd
import numpy as np
import rasterio
from pyproj import Geod, Transformer
from rasterio import features
from rasterio.crs import CRS
from rasterio.windows import Window
from rasterio.windows import bounds as window_bounds
from rasterio.windows import transform as window_transform
from shapely import STRtree, box

# WGS 84
_A = 6378137.0
_E2 = 0.00669437999014
_E = float(np.sqrt(_E2))


def _authalic(phi: np.ndarray) -> np.ndarray:
    s = np.sin(phi)
    return s / (1 - _E2 * s * s) + np.log((1 + _E * s) / (1 - _E * s)) / (2 * _E)


def geographic_row_areas(lat_top: float, pixel_height: float, pixel_width: float, rows: int):
    """Ground area (m²) of one pixel in each row of a north-up geographic raster window."""
    edges = np.radians(lat_top - pixel_height * np.arange(rows + 1))
    b2 = _A * _A * (1 - _E2)
    band = b2 / 2 * np.radians(pixel_width) * (_authalic(edges[:-1]) - _authalic(edges[1:]))
    return np.abs(band)


_GEOD = Geod(ellps="WGS84")
_TO_GEOGRAPHIC: dict[str, Transformer] = {}


def ground_scale(crs: CRS, bounds: tuple[float, float, float, float]) -> float:
    """True ground area of a projected block divided by its nominal (map) area.

    "Equal-area" projections such as the World Mollweide used by GHSL are computed on a sphere,
    so a nominal 100 m cell is not exactly one hectare on the WGS 84 ellipsoid (about 0.7% less
    at Sri Lanka's latitude). The block's outline is densified, taken to longitude and latitude,
    and its geodesic area compared with its map area.
    """
    key = crs.to_wkt()
    if key not in _TO_GEOGRAPHIC:
        _TO_GEOGRAPHIC[key] = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
    left, bottom, right, top = bounds
    t = np.linspace(0, 1, 33)[:-1]
    xs = np.concatenate(
        [
            left + (right - left) * t,
            np.full(32, right),
            right - (right - left) * t,
            np.full(32, left),
        ]
    )
    ys = np.concatenate(
        [
            np.full(32, bottom),
            bottom + (top - bottom) * t,
            np.full(32, top),
            top - (top - bottom) * t,
        ]
    )
    lon, lat = _TO_GEOGRAPHIC[key].transform(xs, ys)
    area, _ = _GEOD.polygon_area_perimeter(lon, lat)
    return abs(area) / ((right - left) * (top - bottom))


@dataclass
class Zones:
    """Zone polygons (EPSG:4326) with stable integer labels 1..n; 0 means no zone."""

    ids: list[str]
    frame: gpd.GeoDataFrame
    _cache: dict[str, tuple[np.ndarray, STRtree]] = field(default_factory=dict)

    @classmethod
    def from_frame(cls, frame: gpd.GeoDataFrame, id_column: str = "geography_id") -> Zones:
        if len(frame) >= 65535:
            raise ValueError("zone labels are 16-bit; at most 65,534 zones")
        if frame.crs is None or frame.crs.to_epsg() != 4326:
            raise ValueError("zones must be in EPSG:4326")
        clean = gpd.GeoDataFrame(frame.reset_index(drop=True))
        return cls(ids=[str(v) for v in clean[id_column]], frame=clean)

    def __len__(self) -> int:
        return len(self.ids)

    def in_crs(self, crs: CRS) -> tuple[np.ndarray, STRtree]:
        key = crs.to_wkt()
        if key not in self._cache:
            geoms = self.frame.geometry.to_crs(crs).to_numpy()
            self._cache[key] = (geoms, STRtree(geoms))
        return self._cache[key]


# reducer(labels, arrays, areas): labels is (h, w) uint16; arrays one (h, w) array per input
# raster; areas is (h, 1) or (1, 1) float64 ground area of one (sub-)pixel in m².
Reducer = Callable[[np.ndarray, list[np.ndarray], np.ndarray], None]


def walk(
    datasets: Sequence[rasterio.DatasetReader],
    zones: Zones,
    reducer: Reducer,
    *,
    block: int = 2048,
    upsample: int = 1,
    halo: int = 0,
) -> int:
    """Feed every block of the rasters that touches a zone to ``reducer``.

    All ``datasets`` must share one grid. With ``halo`` > 0 the arrays carry that many extra
    pixels on each side where the raster has them (for neighbourhood operations); the reducer
    gets ``arrays`` with the halo and must crop to ``labels``' shape itself using
    :func:`crop_halo`. Returns the number of blocks used.
    """
    first = datasets[0]
    for other in datasets[1:]:
        if other.transform != first.transform or other.shape != first.shape:
            raise ValueError("rasters walked together must share one grid")
    if first.transform.b != 0 or first.transform.d != 0 or first.transform.e >= 0:
        raise ValueError("only north-up rasters are supported")
    geoms, tree = zones.in_crs(first.crs)
    geographic = first.crs.is_geographic
    used = 0
    for row in range(0, first.height, block):
        for col in range(0, first.width, block):
            h = min(block, first.height - row)
            w = min(block, first.width - col)
            win = Window(col, row, w, h)  # type: ignore[call-arg]
            hits = tree.query(box(*window_bounds(win, first.transform)))
            if len(hits) == 0:
                continue
            transform = window_transform(win, first.transform)
            if upsample > 1:
                transform = transform @ transform.scale(1 / upsample, 1 / upsample)
            labels = features.rasterize(
                ((geoms[i], int(i) + 1) for i in sorted(hits)),
                out_shape=(h * upsample, w * upsample),
                transform=transform,
                fill=0,
                dtype="uint16",
            )
            if labels is None or not labels.any():
                continue
            r0, c0 = max(0, row - halo), max(0, col - halo)
            r1, c1 = min(first.height, row + h + halo), min(first.width, col + w + halo)
            read = Window(c0, r0, c1 - c0, r1 - r0)  # type: ignore[call-arg]
            arrays = [d.read(1, window=read) for d in datasets]
            if upsample > 1:
                arrays = [np.repeat(np.repeat(a, upsample, 0), upsample, 1) for a in arrays]
            if geographic:
                areas = geographic_row_areas(
                    transform.f, -transform.e, transform.a, h * upsample
                ).reshape(-1, 1)
            else:
                nominal = abs(transform.a * transform.e)
                areas = np.array(
                    [[nominal * ground_scale(first.crs, window_bounds(win, first.transform))]]
                )
            reducer.offsets = (row - r0, col - c0)  # type: ignore[attr-defined]
            reducer.pixel = (transform, geographic)  # type: ignore[attr-defined]
            reducer(labels, arrays, areas)
            used += 1
    return used


def crop_halo(array: np.ndarray, offsets: tuple[int, int], shape: tuple[int, int]) -> np.ndarray:
    return array[offsets[0] : offsets[0] + shape[0], offsets[1] : offsets[1] + shape[1]]


class ClassAreas:
    """Area per zone of each class of a categorical raster (classes may be merged by ``lut``)."""

    def __init__(self, n_zones: int, lut: np.ndarray, n_classes: int) -> None:
        self.lut = lut  # raw pixel value -> class index 0..n_classes-1
        self.n_classes = n_classes
        self.area = np.zeros((n_zones + 1) * n_classes, dtype=np.float64)

    def __call__(self, labels: np.ndarray, arrays: list[np.ndarray], areas: np.ndarray) -> None:
        mask = labels > 0
        cls = self.lut[arrays[0][mask]]
        idx = labels[mask].astype(np.int64) * self.n_classes + cls
        weights = np.broadcast_to(areas, labels.shape)[mask]
        self.area += np.bincount(idx, weights=weights, minlength=self.area.size)

    def table(self) -> np.ndarray:
        """(n_zones, n_classes) areas in m²; row i is zone label i + 1."""
        return self.area.reshape(-1, self.n_classes)[1:]


class Moments:
    """Area-weighted sum, area, minimum and maximum of a continuous raster per zone.

    ``valid`` says which raw values count; ``transform`` turns raw values into the measured
    quantity (for example a scale factor). Extra area sums can be collected for thresholds.
    """

    def __init__(
        self,
        n_zones: int,
        *,
        valid: Callable[[np.ndarray], np.ndarray],
        thresholds: Sequence[float] = (),
    ) -> None:
        n = n_zones + 1
        self.valid = valid
        self.thresholds = tuple(thresholds)
        self.weighted = np.zeros(n)
        self.area = np.zeros(n)
        self.invalid_area = np.zeros(n)
        self.minimum = np.full(n, np.inf)
        self.maximum = np.full(n, -np.inf)
        self.above = np.zeros((len(self.thresholds), n))

    def add(self, labels: np.ndarray, values: np.ndarray, areas: np.ndarray) -> None:
        n = self.area.size
        in_zone = labels > 0
        good = in_zone & self.valid(values)
        weights_all = np.broadcast_to(areas, labels.shape)
        self.invalid_area += np.bincount(
            labels[in_zone & ~good], weights=weights_all[in_zone & ~good], minlength=n
        )
        lab = labels[good].astype(np.int64)
        val = values[good].astype(np.float64)
        wts = weights_all[good]
        self.area += np.bincount(lab, weights=wts, minlength=n)
        self.weighted += np.bincount(lab, weights=wts * val, minlength=n)
        np.minimum.at(self.minimum, lab, val)
        np.maximum.at(self.maximum, lab, val)
        for k, t in enumerate(self.thresholds):
            over = val > t
            self.above[k] += np.bincount(lab[over], weights=wts[over], minlength=n)

    def __call__(self, labels: np.ndarray, arrays: list[np.ndarray], areas: np.ndarray) -> None:
        self.add(labels, arrays[0], areas)

    def mean(self) -> np.ndarray:
        with np.errstate(invalid="ignore", divide="ignore"):
            return (self.weighted / self.area)[1:]


class Terrain:
    """Elevation moments and slope (degrees) from a geographic elevation raster."""

    def __init__(self, n_zones: int, steep_degrees: float = 15.0) -> None:
        self.elevation = Moments(n_zones, valid=np.isfinite)
        self.slope = Moments(n_zones, valid=np.isfinite, thresholds=(steep_degrees,))
        self.offsets = (0, 0)
        self.pixel: tuple[rasterio.Affine, bool] | None = None

    def __call__(self, labels: np.ndarray, arrays: list[np.ndarray], areas: np.ndarray) -> None:
        assert self.pixel is not None
        transform, geographic = self.pixel
        if not geographic:
            raise ValueError("Terrain expects a geographic raster")
        dem = arrays[0].astype(np.float64)
        rows = dem.shape[0]
        # metres per pixel: north-south from the ellipsoid row areas, east-west per row
        lat_top = transform.f + self.offsets[0] * -transform.e
        lats = np.radians(lat_top + transform.e * (np.arange(rows) + 0.5))
        dy = np.radians(-transform.e) * _A * (1 - _E2) / (1 - _E2 * np.sin(lats) ** 2) ** 1.5
        dx = np.radians(transform.a) * _A * np.cos(lats) / np.sqrt(1 - _E2 * np.sin(lats) ** 2)
        gy, gx = np.gradient(dem)
        slope = np.degrees(np.arctan(np.hypot(gx / dx[:, None], gy / dy[:, None])))
        shape = (labels.shape[0], labels.shape[1])
        self.elevation.add(labels, crop_halo(dem, self.offsets, shape), areas)
        self.slope.add(labels, crop_halo(slope, self.offsets, shape), areas)


class ForestChange:
    """Hansen Global Forest Change: tree cover in 2000 and loss by year inside that cover.

    ``arrays`` is [treecover2000 (0-100 %), lossyear (0 = none, n = 2000 + n)].
    """

    def __init__(self, n_zones: int, canopy_threshold: int = 30, last_year: int = 24) -> None:
        self.n = n_zones + 1
        self.threshold = canopy_threshold
        self.years = last_year
        self.land = np.zeros(self.n)
        self.cover = np.zeros(self.n)
        self.loss = np.zeros(self.n * (self.years + 1))
        self.loss_outside_cover = np.zeros(self.n)

    def __call__(self, labels: np.ndarray, arrays: list[np.ndarray], areas: np.ndarray) -> None:
        cover, lossyear = arrays
        mask = labels > 0
        lab = labels[mask].astype(np.int64)
        wts = np.broadcast_to(areas, labels.shape)[mask]
        forest = cover[mask] >= self.threshold
        year = np.minimum(lossyear[mask], self.years).astype(np.int64)
        self.land += np.bincount(lab, weights=wts, minlength=self.n)
        self.cover += np.bincount(lab[forest], weights=wts[forest], minlength=self.n)
        lost = forest & (year > 0)
        self.loss += np.bincount(
            lab[lost] * (self.years + 1) + year[lost], weights=wts[lost], minlength=self.loss.size
        )
        stray = ~forest & (year > 0)
        self.loss_outside_cover += np.bincount(lab[stray], weights=wts[stray], minlength=self.n)

    def loss_table(self) -> np.ndarray:
        """(n_zones, years) loss area in m²; column k is year 2001 + k."""
        return self.loss.reshape(self.n, self.years + 1)[1:, 1:]
