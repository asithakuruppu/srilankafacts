"""Point resolver: coordinates -> the places that contain them (G07 step 8 `point_in_polygon`).

Exact answers use the spine's full-resolution COD-AB polygons. A point is placed in the GN
division whose polygon contains it (`covers`, so a point on a shared border goes to the
first GN in id order, deterministically); its DS, district, province and country follow the
spine hierarchy, and electoral districts follow `catalog/geographies/relations/` (ids only,
never names). A point in no GN (sea, or one of the source's 84 km² of holes) resolves to
nothing at GN level and says so.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import geopandas as gpd
import pandas as pd
import shapely
from shapely.strtree import STRtree


@dataclass
class Resolution:
    lon: float
    lat: float
    places: dict[str, str] = field(default_factory=dict)
    names: dict[str, str | None] = field(default_factory=dict)
    note: str | None = None


LEVEL_KEYS = {4: "gn", 3: "ds", 2: "district", 1: "province", 0: "country"}


class Resolver:
    def __init__(self, spine_dir: Path, relations_dir: Path | None = None) -> None:
        versions = gpd.GeoDataFrame(gpd.read_parquet(spine_dir / "geography_versions.geoparquet"))
        gn = versions[versions["level"] == 4]
        pairs = sorted(zip((str(v) for v in gn["geography_id"]), gn.geometry.values, strict=True))
        self._ids = [gid for gid, _ in pairs]
        self._geoms = [geom for _, geom in pairs]
        self._tree = STRtree(self._geoms)
        geographies = pd.read_parquet(spine_dir / "geographies.parquet")
        rows = cast(list[dict[str, Any]], geographies.to_dict("records"))
        self._parent = {
            str(r["geography_id"]): (None if pd.isna(r["parent_id"]) else str(r["parent_id"]))
            for r in rows
        }
        self._level = {str(r["geography_id"]): int(r["level"]) for r in rows}
        self._name = {
            str(r["geography_id"]): (None if pd.isna(r["name_en"]) else str(r["name_en"]))
            for r in rows
        }
        self._ed_of_district: dict[str, str] = {}
        if relations_dir is not None:
            for path in sorted(relations_dir.glob("electoral_*.csv")):
                table = pd.read_csv(path, dtype=str)
                for r in cast(list[dict[str, Any]], table.to_dict("records")):
                    if r["relation"] == "composed_of" and str(r["geography_id"]).startswith(
                        "LK-ED-"
                    ):
                        self._ed_of_district[str(r["related_id"])] = str(r["geography_id"])

    def resolve(self, lon: float, lat: float) -> Resolution:
        point = shapely.Point(lon, lat)
        result = Resolution(lon, lat)
        hits = sorted(int(i) for i in self._tree.query(point, predicate="intersects"))
        gn = next((self._ids[i] for i in hits if self._geoms[i].covers(point)), None)
        if gn is None:
            result.note = (
                "No GN division contains this point (sea, or a gap in the boundary source)."
            )
            return result
        current: str | None = gn
        while current is not None:
            key = LEVEL_KEYS.get(self._level.get(current, -1))
            if key:
                result.places[key] = current
                result.names[key] = self._name.get(current)
            current = self._parent.get(current)
        district = result.places.get("district")
        if district and district in self._ed_of_district:
            result.places["ed"] = self._ed_of_district[district]
        return result


def district_to_ed(relations_dir: Path) -> dict[str, str]:
    """District id -> electoral district id, for the browser resolver."""
    found: dict[str, str] = {}
    for path in sorted(relations_dir.glob("electoral_*.csv")):
        for r in cast(list[dict[str, Any]], pd.read_csv(path, dtype=str).to_dict("records")):
            if r["relation"] == "composed_of" and str(r["geography_id"]).startswith("LK-ED-"):
                found[str(r["related_id"])] = str(r["geography_id"])
    return dict(sorted(found.items()))


def as_json(result: Resolution) -> str:
    return json.dumps(
        {
            "lon": result.lon,
            "lat": result.lat,
            "places": result.places,
            "names": result.names,
            "note": result.note,
            "method": "point in full-resolution COD-AB GN polygon (spine), hierarchy by id",
        },
        indent=2,
        ensure_ascii=False,
    )
