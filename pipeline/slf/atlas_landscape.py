"""Landscape lens files for the atlas bundle, from the landscape build (`slf spatial build`).

Nothing is recomputed. Each displayed indicator's values are copied, per level, from the
build's ledger rows for one period (the latest), with the row's information floor, data
nature, dataset and the dataset's rights from the catalogue. Component rows used only to
recompute shares (`*_measured_area`, class areas) are not displayed.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, cast

import pandas as pd

GROUPS: list[tuple[str, list[str]]] = [
    (
        "Terrain",
        ["elevation_mean", "elevation_min", "elevation_max", "slope_mean", "steep_land_share"],
    ),
    (
        "Land cover (2021)",
        [
            "land_cover_tree_share",
            "land_cover_cropland_share",
            "land_cover_grassland_share",
            "land_cover_shrubland_share",
            "land_cover_built_up_share",
            "land_cover_bare_share",
            "land_cover_water_share",
            "land_cover_wetland_share",
            "land_cover_mangrove_share",
        ],
    ),
    ("Trees", ["tree_cover_2000_share", "tree_cover_loss_total_share"]),
    ("Water", ["surface_water_permanent_share", "surface_water_ever_share"]),
    (
        "Built-up and settlement",
        [
            "built_up_surface_share",
            "settlement_urban_share",
            "settlement_urban_centre_share",
            "buildings_mapped",
            "building_footprint_mean",
        ],
    ),
    (
        "Facilities and mapped places",
        [
            "schools_located",
            "schools_connected_share",
            "nearest_school_distance",
            "health_facilities_mapped",
            "nearest_health_facility_distance",
            "places_listed",
            "wikidata_items",
        ],
    ),
]

LEVEL_KEYS = {0: "country", 1: "province", 2: "district", 3: "ds", 4: "gn"}
MEASURE_OF_UNIT = {"percent": "share"}


def _rows(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return cast(list[dict[str, Any]], frame.to_dict("records"))


def _dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n")


def _rights(catalog_dir: Path | None) -> dict[str, dict[str, Any]]:
    rights_of: dict[str, dict[str, Any]] = {}
    if catalog_dir is None:
        return rights_of
    from slf.catalog import CatalogReport, load_catalog
    from slf.release import _dataset_rights

    catalog = load_catalog(catalog_dir, catalog_dir.parent / "overrides", CatalogReport())
    for dataset_id in catalog.datasets:
        try:
            rights_of[dataset_id] = _dataset_rights(catalog, dataset_id)
        except Exception:  # a catalogue entry without rights stays unknown, never guessed
            continue
    return rights_of


def _export(
    source: Path,
    groups: list[tuple[str, list[str]]],
    meta_of: dict[str, dict[str, Any]],
    spine_dir: Path,
    catalog_dir: Path | None,
    folder: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Copy the latest period of each listed indicator, per level, with its provenance."""
    rights_of = _rights(catalog_dir)
    level_of = {
        str(r["geography_id"]): LEVEL_KEYS.get(int(r["level"]))
        for r in _rows(pd.read_parquet(spine_dir / "geographies.parquet"))
    }
    wanted = [i for _, ids in groups for i in ids]
    observations = pd.read_parquet(source)
    observations = pd.DataFrame(observations[observations["indicator_id"].isin(wanted)])
    index: list[dict[str, Any]] = []
    skipped: list[str] = []
    for group, ids in groups:
        for indicator in ids:
            rows = pd.DataFrame(observations[observations["indicator_id"] == indicator])
            rows = pd.DataFrame(rows[rows["breakdown"].isna()])
            meta = meta_of.get(indicator)
            if rows.empty or meta is None:
                skipped.append(indicator)
                continue
            period = sorted(str(p) for p in rows["period"].unique())[-1]
            rows = pd.DataFrame(rows[rows["period"].astype(str) == period])
            values: dict[str, dict[str, float]] = {}
            for r in _rows(rows):
                level = level_of.get(str(r["geography_id"]))
                if level is None or pd.isna(r["value"]):
                    continue
                values.setdefault(level, {})[str(r["geography_id"])] = round(float(r["value"]), 4)
            first = _rows(rows.head(1))[0]
            dataset = str(first["dataset_id"])
            rights = rights_of.get(dataset, {})
            index.append(
                {
                    "id": indicator,
                    **meta,
                    "short": meta["name"],
                    "levels": [
                        lv for lv in ("country", "province", "district", "ds", "gn") if lv in values
                    ],
                    "group": group,
                    "period": period,
                    "time_start": None
                    if pd.isna(first["time_start"])
                    else str(first["time_start"]),
                    "time_end": None if pd.isna(first["time_end"]) else str(first["time_end"]),
                    "floor": str(first["information_footprint_ref"]),
                    "data_nature": str(first["data_nature"]),
                    "verification": str(first["verification"]),
                    "dataset_id": dataset,
                    "snapshot_sha256": str(first["snapshot_sha256"]),
                    "source_locator": str(first["source_locator"]),
                    "licence": rights.get("licence"),
                    "attribution": rights.get("attribution"),
                    "commercial_reuse": rights.get("commercial_reuse", "unknown"),
                    "source_name": rights.get("source_name"),
                }
            )
            _dump(folder / "values" / f"{indicator}.json", values)
    _dump(folder / "index.json", {"indicators": index})
    return index, skipped


def build(
    landscape_dir: Path, spine_dir: Path, catalog_dir: Path | None, out_dir: Path
) -> dict[str, Any]:
    source = landscape_dir / "observations.parquet"
    if not source.exists():
        return {"available": False, "reason": "no landscape build found"}
    from slf.spatial.layers import SPECS

    meta_of = {
        spec.id: {
            "name": spec.name,
            "unit": spec.unit,
            "decimals": spec.decimals,
            "measureType": spec.measure_type,
            "higherIs": spec.higher_is,
            "definition": spec.definition,
        }
        for spec in SPECS.values()
    }
    index, skipped = _export(source, GROUPS, meta_of, spine_dir, catalog_dir, out_dir / "landscape")
    similar = landscape_dir / "vectors" / "similar_ds.json"
    if similar.exists():
        shutil.copyfile(similar, out_dir / "landscape" / "similar_ds.json")
    return {
        "available": True,
        "indicators": len(index),
        "skipped": skipped,
        "similar_ds": similar.exists(),
        "method": (
            "Copied from the landscape build's ledger rows (latest period per indicator); "
            "values are modelled estimates on their own information floor (D-044)."
        ),
    }


def build_extra(
    subnational_dir: Path | None,
    spine_dir: Path,
    catalog_dir: Path | None,
    out_dir: Path,
    events_dir: Path | None = None,
    hazard_dir: Path | None = None,
    public: bool = False,
    stat_tables_dir: Path | None = None,
) -> dict[str, Any]:
    """Stage 3 indicators (`slf subnational build`, `slf events`), shown in the Geography lens."""
    from slf.events import SPECS as EVENT_SPECS
    from slf.hazard_access import SHARE_ALIKE_DATASETS
    from slf.hazard_access import SPECS as HAZARD_SPECS
    from slf.subnational import SPECS as SUBNATIONAL_SPECS

    parts = []
    specs: list[Any] = []
    for folder, spec_list in (
        (subnational_dir, SUBNATIONAL_SPECS),
        (events_dir, EVENT_SPECS),
        (hazard_dir, HAZARD_SPECS),
    ):
        if folder is not None and (folder / "observations.parquet").exists():
            frame = pd.read_parquet(folder / "observations.parquet")
            if folder is hazard_dir and public:
                # HeiGIT is CC BY-SA: a public bundle needs a licence statement that carries
                # the share-alike terms, so its indicators stay out until a release does.
                frame = pd.DataFrame(frame[~frame["dataset_id"].isin(list(SHARE_ALIKE_DATASETS))])
                spec_list = [s for s in spec_list if s.dataset not in SHARE_ALIKE_DATASETS]
            if len(frame):
                parts.append(frame)
                specs += spec_list
    stat = _stat_table_part(stat_tables_dir, catalog_dir, public)
    if stat is not None:
        parts.append(stat[0])
        specs += stat[1]
    if not parts:
        return {"available": False, "reason": "no subnational or events build found"}
    source = out_dir / "extra" / "_observations.parquet"
    source.parent.mkdir(parents=True, exist_ok=True)
    pd.concat(parts, ignore_index=True).to_parquet(source, index=False)
    EXTRA = specs

    groups: dict[str, list[str]] = {}
    for spec in EXTRA:
        groups.setdefault(spec.group, []).append(spec.id)
    meta_of = {
        spec.id: {
            "name": spec.name,
            "unit": spec.unit,
            "decimals": spec.decimals,
            "measureType": spec.measure_type,
            "higherIs": spec.higher_is,
            "definition": spec.definition,
        }
        for spec in EXTRA
    }
    index, skipped = _export(
        source, list(groups.items()), meta_of, spine_dir, catalog_dir, out_dir / "extra"
    )
    source.unlink()
    timelines = _timelines(events_dir, out_dir) if events_dir is not None else {}
    return {"available": True, "indicators": len(index), "skipped": skipped, "timelines": timelines}


STAT_TABLE_GROUPS = {
    "poverty": "Poverty",
    "labour": "Labour",
    "agriculture": "Agriculture",
    "health": "Health",
    "population": "Population",
}


def _stat_table_part(
    stat_tables_dir: Path | None, catalog_dir: Path | None, public: bool
) -> tuple[pd.DataFrame, list[Any]] | None:
    """Rows and specs of the statistical-table datasets (`slf stat-tables build`).

    The rights of these tables are unclear (D-030/D-032 cover only the census), so a public
    bundle leaves them out. Only whole-population rows are shown on the map: the survey
    breakdowns (poverty by sector, labour by sex) stay in the observation downloads, except
    both-sexes labour rows, which are the headline figures.
    """
    from types import SimpleNamespace

    if stat_tables_dir is None or catalog_dir is None or public:
        return None
    from slf.catalog import CatalogReport, load_catalog

    catalog = load_catalog(catalog_dir, catalog_dir.parent / "overrides", CatalogReport())
    frames: list[pd.DataFrame] = []
    for path in sorted(stat_tables_dir.glob("*/observations.parquet")):
        frame = pd.read_parquet(path)
        both = frame["breakdown"].map(
            lambda b: isinstance(b, str) and json.loads(b) == {"sex": "both"}
        )
        frame = pd.DataFrame(frame[frame["breakdown"].isna() | both])
        frame["breakdown"] = None
        frames.append(frame)
    if not frames:
        return None
    frame = pd.concat(frames, ignore_index=True)
    specs = []
    for ind_id in sorted(frame["indicator_id"].unique()):
        ind = catalog.indicators.get(str(ind_id))
        if ind is None:
            continue
        topic = next((t for t in ind.topic if t in STAT_TABLE_GROUPS), "health")
        specs.append(
            SimpleNamespace(
                id=ind.id,
                name=ind.name,
                unit=ind.unit,
                decimals=ind.decimals,
                measure_type=ind.measure_type,
                higher_is=ind.higher_is,
                definition=ind.definition,
                group=STAT_TABLE_GROUPS[topic],
            )
        )
    return frame, specs


def _timelines(events_dir: Path, out_dir: Path) -> dict[str, Any]:
    """Yearly fire detections per DS and district, and storm passes per district."""
    done: dict[str, Any] = {}
    observations = events_dir / "observations.parquet"
    if observations.exists():
        frame = pd.read_parquet(observations)
        fires = pd.DataFrame(frame[frame["indicator_id"] == "fire_detections"])
        if len(fires):
            years = sorted({int(p) for p in fires["period"]})
            series: dict[str, list[int]] = {}
            for gid, group in fires.groupby("geography_id"):
                by_year = {int(r["period"]): int(r["value"]) for r in _rows(pd.DataFrame(group))}
                series[str(gid)] = [by_year.get(y, 0) for y in years]
            first = _rows(fires.head(1))[0]
            _dump(
                out_dir / "events" / "fires.json",
                {
                    "years": years,
                    "series": series,
                    "dataset_id": first["dataset_id"],
                    "snapshot_sha256": first["snapshot_sha256"],
                    "source_locator": first["source_locator"],
                },
            )
            done["fires"] = {"places": len(series), "years": [years[0], years[-1]]}
    storms = events_dir / "storms.json"
    if storms.exists():
        (out_dir / "events").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(storms, out_dir / "events" / "storms.json")
        done["storms"] = True
    return done


# Point features shown at high zoom and listed per GN ("what's here"). Public facilities and
# named places only; Overture's business listings stay counts (no names), and no attribute
# beyond name and category is copied (no addresses, phones, operators or people).
FEATURE_SOURCES: list[tuple[str, str, str]] = [
    ("school", "giga-school-locations", "Schools (Giga school locations, UNICEF/ITU)"),
    ("health", "healthsites-lk", "Health facilities (healthsites.io, from OpenStreetMap)"),
    ("heritage", "wikidata-places-lk", "Wikidata places"),
    ("place", "geonames-lk", "GeoNames place names"),
]


# Wikidata items in these classes are events, organisations or administrative units (the
# spine already holds those), not physical places, and are not shown.
WIKIDATA_EXCLUDE = {
    "massacre",
    "attack",
    "bombing",
    "suicide car bombing",
    "suicide bombing",
    "battle",
    "festival",
    "holiday",
    "event",
    "election",
    "organization",
    "nonprofit organization",
    "government agency",
    "Diocese of the Catholic Church",
    "terrorist attack",
    "shooting",
    "riot",
    "war",
    "armed conflict",
    "aviation accident",
    "disaster",
    "fourth-level administrative division",
    "Grama Niladhari division",
    "Divisional Secretariat of Sri Lanka",
    "district of Sri Lanka",
    "province of Sri Lanka",
    "electoral unit",
    "administrative territorial entity",
    "human-geographic territorial entity",
}

# GeoNames feature codes in words (https://www.geonames.org/export/codes.html); others fall
# back to their feature class. Administrative units (A.*) are left out: the spine holds them.
GEONAMES_CODES = {
    "P.PPL": "populated place",
    "P.PPLX": "section of populated place",
    "H.RSV": "reservoir",
    "L.LCTY": "locality",
    "S.EST": "estate",
    "S.ESTX": "estate",
    "S.ESTR": "rubber estate",
    "S.ESTO": "oil palm estate",
    "S.ESTT": "tea estate",
    "H.STM": "stream",
    "S.TRIG": "triangulation station",
    "V.FRST": "forest",
    "T.HLL": "hill",
    "S.HTL": "hotel",
    "T.MT": "mountain",
    "V.SCRB": "scrubland",
    "H.MRSH": "marsh",
    "H.WTRH": "waterhole",
    "V.GROVE": "grove",
    "T.RK": "rock",
    "T.ISL": "island",
    "V.CULT": "cultivated area",
    "T.PT": "point",
    "L.RESF": "forest reserve",
    "V.GRSLD": "grassland",
    "H.LGN": "lagoon",
    "S.TMPL": "temple",
    "R.RDJCT": "road junction",
    "T.RKS": "rocks",
    "L.RES": "reserve",
    "S.GDN": "garden",
    "S.RUIN": "ruin",
    "S.SHRN": "shrine",
    "S.SCH": "school",
    "H.RF": "reef",
    "S.RSTN": "railway station",
    "H.PND": "pond",
    "S.FCL": "facility",
    "S.MUS": "museum",
    "S.HSTS": "historical site",
    "S.HSP": "hospital",
    "S.CH": "church",
    "S.MSQE": "mosque",
    "S.AIRP": "airport",
    "H.BAY": "bay",
    "H.FLLS": "waterfall",
    "T.BCH": "beach",
    "S.LTHSE": "lighthouse",
    "S.BDG": "bridge",
    "S.DAM": "dam",
    "S.FT": "fort",
    "L.PRK": "park",
    "H.LK": "lake",
}
GEONAMES_CLASSES = {
    "H": "water feature",
    "L": "area",
    "P": "populated place",
    "R": "road or railway",
    "S": "building or site",
    "T": "terrain feature",
    "U": "undersea feature",
    "V": "vegetation",
}


def _category(kind: str, raw: str) -> str | None:
    """Readable category, or None when the item is not a physical place to show."""
    raw = "" if raw in ("nan", "None") else raw
    if kind == "place":
        if raw.startswith("A."):
            return None
        return GEONAMES_CODES.get(raw) or GEONAMES_CLASSES.get(raw[:1], "place")
    if kind == "heritage":
        classes = [c for c in raw.split("|") if c]
        if any(c in WIKIDATA_EXCLUDE for c in classes):
            return None
        return ", ".join(classes[:3])
    return raw


def build_features(landscape_dir: Path, out_dir: Path) -> dict[str, Any]:
    import shapely

    folder = landscape_dir / "features"
    if not folder.exists():
        return {"available": False, "reason": "no feature tables in the landscape build"}
    by_district: dict[str, list[list[Any]]] = {}
    counts: dict[str, int] = {}
    licences: dict[str, str] = {}
    unplaced: dict[str, int] = {}
    unnamed: dict[str, int] = {}
    excluded: dict[str, int] = {}
    for kind, dataset, _label in FEATURE_SOURCES:
        path = folder / f"{dataset}.parquet"
        if not path.exists():
            continue
        frame = pd.read_parquet(path)
        counts[kind] = 0
        unplaced[kind] = 0
        unnamed[kind] = 0
        excluded[kind] = 0
        for r in _rows(frame):
            district = str(r.get("district_id"))
            gn = str(r.get("gn_id"))
            if district in ("nan", "None") or gn in ("nan", "None"):
                unplaced[kind] += 1
                continue
            if "lon" in r and str(r["lon"]) not in ("nan", "None"):
                lon, lat = float(r["lon"]), float(r["lat"])
            else:
                point = shapely.from_wkb(r["geometry"])
                lon, lat = float(point.x), float(point.y)
            name = str(r.get("name") or "").strip()
            if not name or name == "nan":
                unnamed[kind] += 1
                continue
            category = _category(kind, str(r.get("category") or ""))
            if category is None:
                excluded[kind] += 1
                continue
            if kind == "heritage" and str(r.get("heritage") or "nan") not in ("nan", "None", ""):
                category = f"{category}, {r['heritage']}" if category else str(r["heritage"])
            by_district.setdefault(district, []).append(
                [round(lon, 5), round(lat, 5), kind, name[:120], category[:80], gn]
            )
            counts[kind] += 1
            licences[kind] = str(r.get("licence") or "")
    total = 0
    for district, points in sorted(by_district.items()):
        points.sort(key=lambda p: (p[5], p[2], p[3]))
        target = out_dir / "features" / f"{district}.json"
        _dump(
            target,
            {
                "district": district,
                "row_format": ["lon", "lat", "kind", "name", "category", "gn"],
                "points": points,
            },
        )
        total += target.stat().st_size
    sources = [
        {"kind": kind, "dataset_id": dataset, "label": label, "licence": licences.get(kind)}
        for kind, dataset, label in FEATURE_SOURCES
        if kind in counts
    ]
    _dump(out_dir / "features" / "index.json", {"sources": sources, "counts": counts})
    return {
        "available": True,
        "counts": counts,
        "outside_any_gn": unplaced,
        "without_name_not_shown": unnamed,
        "not_a_physical_place_not_shown": excluded,
        "districts": len(by_district),
        "bytes": total,
        "note": "Local preview only: individual features are not part of any release (D-044).",
    }
