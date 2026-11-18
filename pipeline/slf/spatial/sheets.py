"""The Ceylon one-inch map series index (Survey Department of Ceylon, 1958-1976) by place.

The held index has 72 sheet footprints with their Stanford addresses (PURL and IIIF manifest)
and an `available` flag for the sheets Stanford has scanned. This is not map content: it says
which historical sheets cover a place, so that a scan can be found from the place. A sheet
covers a place when it overlaps at least ``MIN_SHARE`` of the place's area (areas in EPSG:5235),
which keeps sheets that only touch a boundary out of the lists. A higher level lists every sheet
that covers at least one of its GN divisions (the union of their lists); its overlap area and
share are the sums over its GN divisions.

Files written beside the other landscape outputs: ``features/ceylon-one-inch-sheets.parquet``
(the sheets) and ``place_map_sheets.parquet`` (place, sheet, overlap, share of the place).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
from shapely import STRtree

from slf.spatial.build import Emitter, Hierarchy, Layer, held_files
from slf.spatial.zonal import Zones

MIN_SHARE = 0.01
CRS_METRIC = 5235


def build(
    roots: list[Path], zones: Zones, hierarchy: Hierarchy, out_dir: Path
) -> tuple[pd.DataFrame, Layer | None, dict[str, Any]]:
    held = [
        f
        for f in held_files(roots, "stanford", "ceylon-one-inch-index")
        if f.path.name == "index_map.geojson"
    ]
    if not held:
        return pd.DataFrame(), None, {"held": False}
    sheets = gpd.read_file(held[0].path)
    if sheets.crs is None or sheets.crs.to_epsg() != 4326:
        raise ValueError("the sheet index must be in EPSG:4326")
    sheets = sheets.sort_values("Sheet_Num").reset_index(drop=True)
    sheets["scanned"] = sheets["available"].astype(str).str.lower().eq("true")
    sheet_geoms = sheets.geometry.to_crs(CRS_METRIC).to_numpy()
    gn_geoms = zones.frame.geometry.to_crs(CRS_METRIC).to_numpy()
    gn_area = np.array([g.area for g in gn_geoms])
    tree = STRtree(sheet_geoms)
    left, right = tree.query(gn_geoms, predicate="intersects")
    overlap = shapely.area(shapely.intersection(gn_geoms[left], sheet_geoms[right]))
    pairs = pd.DataFrame({"gn": left, "sheet": right, "overlap_m2": overlap})
    pairs["gn_covered"] = pairs.overlap_m2 / gn_area[pairs.gn.to_numpy()] >= MIN_SHARE

    # every place with the GN divisions it is made of (a GN is a member of each ancestor)
    member = pd.DataFrame(
        [(place, int(gn)) for place, gns in hierarchy.members.items() for gn in gns],
        columns=["geography_id", "gn"],
    )
    area = member.assign(area=gn_area[member.gn.to_numpy()]).groupby("geography_id").area.sum()
    table: Any = (
        member.merge(pairs, on="gn")
        .groupby(["geography_id", "sheet"], as_index=False)
        .agg(overlap_m2=("overlap_m2", "sum"), covers=("gn_covered", "any"))
    )
    table["place_area_m2"] = area.reindex(table.geography_id).to_numpy()
    table["share_of_place"] = table.overlap_m2 / table.place_area_m2
    table["sheet_num"] = sheets.Sheet_Num.to_numpy()[table.sheet.to_numpy()]
    table["scanned"] = sheets.scanned.to_numpy()[table.sheet.to_numpy()]
    table["overlap_km2"] = (table.overlap_m2 / 1e6).round(4)
    table["share_of_place"] = table.share_of_place.round(5)

    features = out_dir / "features"
    features.mkdir(parents=True, exist_ok=True)
    keep = ["Sheet_Num", "label", "call_num", "recId", "websiteUrl", "iiifUrl", "available"]
    sheets[[*keep, "scanned", "geometry"]].assign(
        licence="Public domain (stated by Stanford record yk696bp5456)"
    ).to_parquet(features / "ceylon-one-inch-sheets.parquet", index=False)
    table[table.covers][
        ["geography_id", "sheet_num", "overlap_km2", "share_of_place", "scanned"]
    ].to_parquet(out_dir / "place_map_sheets.parquet", index=False)

    layer = Layer(
        "ceylon-one-inch-index",
        held,
        "map-sheet",
        "Stanford index_map.geojson (72 sheet footprints of the Survey Department of Ceylon "
        f"one-inch series, 1958-1976); a sheet covers a place if it overlaps at least "
        f"{MIN_SHARE:.0%} of the place's area (EPSG:{CRS_METRIC})",
    )
    emitter = Emitter(hierarchy)
    covering: Any = table[table.covers]
    every = np.array(hierarchy.ids)
    for indicator, subset in (
        ("map_sheets_one_inch", covering),
        ("map_sheets_one_inch_scanned", covering[covering.scanned]),
    ):
        counts = subset.groupby("geography_id").size().reindex(every).fillna(0).to_numpy()
        emitter.add(
            layer,
            indicator,
            counts.astype(float),
            period="1976",
            start="1958-01-01",
            end="1976-12-31",
            time_support="observed_around",
            collection_method="admin_register",
            data_nature="administrative_count",
            how="count of overlapping sheets (union over GN divisions)",
        )
    frame = pd.concat(emitter.frames, ignore_index=True)
    own = covering[covering.geography_id.isin(zones.ids)].groupby("geography_id").size()
    summary = {
        "held": True,
        "sheets": len(sheets),
        "scanned": int(sheets.scanned.sum()),
        "places": len(hierarchy.ids),
        "gn_without_sheet": len(zones.ids) - len(own),
        "max_sheets_per_gn": int(cast(int, own.max())),
    }
    return frame, layer, summary
