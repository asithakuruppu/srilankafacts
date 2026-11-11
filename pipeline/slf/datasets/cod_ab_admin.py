# pandas/geopandas type stubs can't follow DataFrame/GeoSeries operations precisely; these
# checks are relaxed for this data module only. Behaviour is covered by tests instead.
# pyright: reportArgumentType=false, reportCallIssue=false, reportAttributeAccessIssue=false
# pyright: reportOperatorIssue=false, reportReturnType=false, reportGeneralTypeIssues=false
"""Geography spine v0: admin levels 0-4 from OCHA COD-AB (prompt G01).

Steps: snapshot → inspect → build geographies, versions and parent edges → validate →
contiguity graph → `geo` space coordinates → write outputs and a QA report.

Rules this module follows (AGENTS.md, G01):
- Parents come from the source's attribute codes, never from spatial inference. Where the
  spatial parent (the unit containing the child's label point) disagrees, it is reported only.
- Canonical geometry is never simplified. Areas and distances are computed in EPSG:5235.
- Lanka Data Layer and nuuuwan are compared by counts only; their geometry is not used.
"""

from __future__ import annotations

import io
import json
import zipfile
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import shapely

from slf.snapshot import SnapshotRef, snapshot_url
from slf.storage import Storage

DATASET_ID = "cod-ab-lka"
SOURCE_ID = "ocha-hdx"
VINTAGE = "cod-ab-v03"  # HDX: "COD-AB dataset version 03"; layers carry version "v03"
METADATA_URL = "https://data.humdata.org/api/3/action/package_show?id=cod-ab-lka"
GDB_URL = (
    "https://data.humdata.org/dataset/0bedcaf3-88cd-4591-b9d5-5d3220e26abf/resource/"
    "3bc0e89f-92c9-42f7-86f6-062949cbf8f1/download/lka_admin_boundaries.gdb.zip"
)
GDB_FILENAME = "lka_admin_boundaries.gdb.zip"
LICENCE_NOTE = "CC BY-IGO 3.0 (HDX license_id cc-by-igo)"

AREA_CRS = "EPSG:5235"  # SLD99 / Sri Lanka Grid 1999 (AGENTS.md)
LEVEL_NAMES = {0: "country", 1: "province", 2: "district", 3: "ds", 4: "gn"}
# name fields: COD-AB declares lang=en, lang1=si, lang2=ta on every layer (checked in inspect()).
NAME_FIELDS = {"name_en": "", "name_si": "1", "name_ta": "2"}

SNAP_TOLERANCE_M = 1.0  # boundaries closer than this count as touching
MIN_SHARED_BORDER_M = 10.0  # shorter contacts (corner touches) are not border neighbours
DISTANCE_BAND_K = 3  # isolated units get their 3 nearest units as distance-band neighbours
OUTSIDE_PARENT_THRESHOLD = 0.01  # report children with more than 1 % of area outside parent

# Counts to compare against (docs/lanka-data-layer-audit.md and the landscape doc).
REFERENCE_COUNTS: dict[str, dict[int, str]] = {
    "Lanka Data Layer (audit)": {0: "1", 1: "9", 2: "25", 3: "339", 4: "14,043"},
    "NSDI geoportal (audit)": {1: "9", 2: "25", 3: "332 features (329 codes)", 4: "14,051"},
    "Commonly cited": {3: "331", 4: "14,022"},
}


# --- Snapshot --------------------------------------------------------------------------------


def latest_snapshot(storage: Storage, filename: str) -> SnapshotRef | None:
    keys = sorted(
        k for k in storage.list(f"raw/{SOURCE_ID}/{DATASET_ID}/") if k.endswith("/" + filename)
    )
    if not keys:
        return None
    meta = json.loads(storage.get(keys[-1] + ".meta.json"))
    return SnapshotRef(**{**meta, "reused": True})


def snapshot(storage: Storage, *, refresh: bool = False) -> tuple[SnapshotRef, SnapshotRef]:
    """Snapshot HDX metadata and the geodatabase (reusing existing snapshots unless refresh)."""
    meta = None if refresh else latest_snapshot(storage, "hdx_package_show.json")
    if meta is None:
        meta = snapshot_url(
            storage,
            source=SOURCE_ID,
            dataset=DATASET_ID,
            url=METADATA_URL,
            filename="hdx_package_show.json",
            licence_note="HDX metadata record",
        )
    gdb = None if refresh else latest_snapshot(storage, GDB_FILENAME)
    if gdb is None:
        gdb = snapshot_url(
            storage,
            source=SOURCE_ID,
            dataset=DATASET_ID,
            url=GDB_URL,
            filename=GDB_FILENAME,
            licence_note=LICENCE_NOTE,
            timeout=900,
        )
    return meta, gdb


def gdb_path(storage_root: Path, ref: SnapshotRef) -> str:
    """GDAL path to the geodatabase inside the (unextracted, immutable) zip."""
    zpath = storage_root / ref.key
    with zipfile.ZipFile(zpath) as zf:
        gdb = sorted({n.split("/")[0] for n in zf.namelist() if n.split("/")[0].endswith(".gdb")})
    if len(gdb) != 1:
        raise ValueError(f"expected one .gdb folder in {zpath}, found {gdb}")
    return f"/vsizip/{zpath}/{gdb[0]}"


# --- Inspect ---------------------------------------------------------------------------------


@dataclass
class Inspection:
    layers: list[dict[str, object]] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        rows = ["| Layer | Geometry | Features | CRS | Fields |", "|---|---|---|---|---|"]
        for lyr in self.layers:
            rows.append(
                f"| `{lyr['name']}` | {lyr['geometry']} | {lyr['features']:,} | {lyr['crs']} | "
                f"{len(lyr['fields'])}: {', '.join(f'`{f}`' for f in lyr['fields'])} |"  # type: ignore[arg-type]
            )
        return "\n".join(rows)


def inspect(path: str) -> Inspection:
    out = Inspection()
    for name, gtype in pyogrio.list_layers(path):
        info = pyogrio.read_info(path, layer=name)
        out.layers.append(
            {
                "name": str(name),
                "geometry": str(gtype),
                "features": int(info["features"]),
                "crs": info["crs"],
                "fields": list(info["fields"]),
            }
        )
    for lv in LEVEL_NAMES:
        layer = f"lka_admin{lv}"
        if layer not in {lyr["name"] for lyr in out.layers}:
            out.problems.append(f"layer {layer} missing")
            continue
        df = pyogrio.read_dataframe(
            path, layer=layer, read_geometry=False, columns=["lang", "lang1", "lang2"]
        )
        langs = df.drop_duplicates().values.tolist()
        if langs != [["en", "si", "ta"]]:
            out.problems.append(f"{layer}: unexpected language fields {langs}")
    return out


# --- Build -----------------------------------------------------------------------------------


def _clean(value: object) -> str | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    text = str(value).strip()
    return text or None


def read_levels(path: str) -> gpd.GeoDataFrame:
    """All five levels in one frame: geography_id, level, names, parent_id, attributes, geometry."""
    frames = []
    for lv in LEVEL_NAMES:
        g = pyogrio.read_dataframe(path, layer=f"lka_admin{lv}")
        crs = g.crs.to_string() if g.crs is not None else None
        if crs != "EPSG:4326":
            raise ValueError(f"lka_admin{lv}: CRS {crs}, expected EPSG:4326 (confirm before use)")
        df = gpd.GeoDataFrame(
            {
                "geography_id": g[f"adm{lv}_pcode"].map(_clean),
                "level": lv,
                **{k: g[f"adm{lv}_name{suffix}"].map(_clean) for k, suffix in NAME_FIELDS.items()},
                "parent_id": g[f"adm{lv - 1}_pcode"].map(_clean) if lv > 0 else None,
                "source_version": g["version"].map(_clean),
                "valid_on": pd.to_datetime(g["valid_on"]).dt.date,
                "source_area_sqkm": g["area_sqkm"],
            },
            geometry=g.geometry,
            crs="EPSG:4326",
        )
        frames.append(df)
    return gpd.GeoDataFrame(pd.concat(frames, ignore_index=True), crs="EPSG:4326")


def build_geographies(units: gpd.GeoDataFrame) -> pd.DataFrame:
    g = pd.DataFrame(units.drop(columns="geometry"))
    return pd.DataFrame(
        {
            "geography_id": g["geography_id"],
            "scheme": "admin",
            "level": g["level"].astype("int8"),
            "level_name": g["level"].map(LEVEL_NAMES),
            "name_en": g["name_en"],
            "name_si": g["name_si"],
            "name_ta": g["name_ta"],
            "alt_names": [[] for _ in range(len(g))],
            "parent_id": g["parent_id"],
            "status": "current",
            "valid_from": g["valid_on"],
            "valid_to": None,
        }
    )


NAME_OVERRIDE_FIELDS = ("name_en", "name_si", "name_ta")
SPINE_DATASET_ID = "cod-ab-lka"


def apply_name_overrides(
    geos: pd.DataFrame, overrides: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Apply person-made name corrections from overrides/ (AGENTS rule 3, D-028).

    A row applies only if its target exists and the current value equals `old_value` (empty
    means "no name"). Anything else is an error, so a stale override never silently wins.
    Returns the corrected table, the applied rows (for the QA report) and errors.
    """
    geos = geos.copy()
    errors: list[str] = []
    applied: list[dict[str, object]] = []
    rows = overrides[overrides["dataset_id"] == SPINE_DATASET_ID] if len(overrides) else overrides
    index = {gid: i for i, gid in zip(geos.index, geos["geography_id"], strict=True)}
    for o in rows.itertuples(index=False):
        if o.field not in NAME_OVERRIDE_FIELDS:
            errors.append(f"override {o.override_id}: field '{o.field}' is not a name field")
            continue
        if o.target not in index:
            errors.append(f"override {o.override_id}: target {o.target} is not in the spine")
            continue
        i = index[o.target]
        current = geos.at[i, o.field]
        current = None if current is None or pd.isna(current) or current == "" else str(current)
        old = (
            None
            if o.old_value is None or pd.isna(o.old_value) or o.old_value == ""
            else str(o.old_value)
        )
        if current != old:
            errors.append(
                f"override {o.override_id}: {o.target}.{o.field} is {current!r}, expected {old!r}"
            )
            continue
        geos.at[i, o.field] = o.new_value
        applied.append(
            {"override_id": o.override_id, "geography_id": o.target, "field": o.field,
             "new_value": o.new_value, "evidence": o.evidence}
        )  # fmt: skip
    return geos, pd.DataFrame(applied), errors


def load_overrides(overrides_root: Path) -> pd.DataFrame:
    path = overrides_root / f"{SPINE_DATASET_ID}.csv"
    if not path.is_file():
        return pd.DataFrame(columns=["override_id", "dataset_id", "target", "field", "old_value",
                                     "new_value", "evidence"])  # fmt: skip
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def build_versions(units: gpd.GeoDataFrame, gdb_ref: SnapshotRef) -> gpd.GeoDataFrame:
    metric = units.geometry.to_crs(AREA_CRS)
    label = shapely.point_on_surface(units.geometry.values)  # guaranteed inside the polygon
    return gpd.GeoDataFrame(
        {
            "geography_id": units["geography_id"],
            "level": units["level"].astype("int8"),
            "vintage": VINTAGE,
            "valid_from": units["valid_on"],
            "area_km2": metric.area.values / 1e6,
            "source_area_sqkm": units["source_area_sqkm"],
            "label_lon": shapely.get_x(label),
            "label_lat": shapely.get_y(label),
            "source_dataset": DATASET_ID,
            "snapshot_sha256": gdb_ref.sha256,
            "status": "current",
        },
        geometry=units.geometry.values,
        crs="EPSG:4326",
    )


def build_relations(geos: pd.DataFrame) -> pd.DataFrame:
    """Parent edges as a GEO_RELATION edge table (D-021): parent → child."""
    child = geos[geos["parent_id"].notna()]
    return pd.DataFrame(
        {
            "geography_id": child["parent_id"].values,
            "related_id": child["geography_id"].values,
            "relation": "parent",
            "vintage": VINTAGE,
            "weight": None,
            "method": "attribute",
            "source": DATASET_ID,
            "valid_from": child["valid_from"].values,
            "valid_to": None,
            "notes": None,
        }
    )


# --- Validate --------------------------------------------------------------------------------


def check_hierarchy(geos: pd.DataFrame) -> list[str]:
    """Hard rules (fail the build): unique ids, parents exist, parent level is one up."""
    errors: list[str] = []
    dup = geos["geography_id"][geos["geography_id"].duplicated()].tolist()
    if dup:
        errors.append(f"duplicate geography_id: {dup[:10]}")
    missing = geos["geography_id"].isna().sum()
    if missing:
        errors.append(f"{missing} units without a p-code")
    level_of = dict(zip(geos["geography_id"], geos["level"], strict=False))
    for gid, lv, raw_parent in geos[["geography_id", "level", "parent_id"]].itertuples(index=False):
        parent = None if pd.isna(raw_parent) else raw_parent
        if lv == 0:
            if parent is not None:
                errors.append(f"{gid}: country has a parent")
            continue
        if parent is None:
            errors.append(f"{gid}: no parent")
        elif parent not in level_of:
            errors.append(f"{gid}: parent {parent} does not exist")
        elif level_of[parent] != lv - 1:
            errors.append(f"{gid}: parent {parent} is level {level_of[parent]}, expected {lv - 1}")
    return errors


def outside_parent(versions: gpd.GeoDataFrame, geos: pd.DataFrame) -> pd.DataFrame:
    """Share of each child's area that lies outside its attribute parent (EPSG:5235)."""
    metric = versions.to_crs(AREA_CRS).set_index("geography_id")
    child = geos[geos["parent_id"].notna()][["geography_id", "parent_id", "level"]]
    cg = metric.geometry.reindex(child["geography_id"]).values
    pg = metric.geometry.reindex(child["parent_id"]).values
    child_area = shapely.area(cg)
    outside = shapely.area(shapely.difference(cg, pg))
    return pd.DataFrame(
        {
            "geography_id": child["geography_id"].values,
            "parent_id": child["parent_id"].values,
            "level": child["level"].values,
            "outside_km2": outside / 1e6,
            "share_outside": np.where(child_area > 0, outside / child_area, np.nan),
        }
    ).sort_values("share_outside", ascending=False)


def spatial_parent_disagreements(versions: gpd.GeoDataFrame, geos: pd.DataFrame) -> pd.DataFrame:
    """Units whose label point falls in a different parent than the attribute parent."""
    rows = []
    pts = gpd.GeoDataFrame(
        versions[["geography_id", "level"]],
        geometry=gpd.points_from_xy(versions["label_lon"], versions["label_lat"]),
        crs="EPSG:4326",
    )
    attr_parent = dict(zip(geos["geography_id"], geos["parent_id"], strict=False))
    for lv in range(1, 5):
        child_pts = pts[pts["level"] == lv]
        parents = versions[versions["level"] == lv - 1][["geography_id", "geometry"]]
        joined = gpd.sjoin(child_pts, parents, how="left", predicate="within")
        for cid, spatial in zip(
            joined["geography_id_left"], joined["geography_id_right"], strict=False
        ):
            sp = None if pd.isna(spatial) else spatial
            if sp != attr_parent.get(cid):
                rows.append(
                    {
                        "geography_id": cid,
                        "attribute_parent": attr_parent.get(cid),
                        "spatial_parent": sp,
                    }
                )
    return pd.DataFrame(rows, columns=["geography_id", "attribute_parent", "spatial_parent"])


def area_rollups(versions: gpd.GeoDataFrame) -> pd.DataFrame:
    country = float(versions.loc[versions["level"] == 0, "area_km2"].sum())
    out = versions.groupby("level")["area_km2"].agg(["count", "sum"]).reset_index()
    out["diff_vs_country_km2"] = out["sum"] - country
    out["diff_pct"] = 100 * out["diff_vs_country_km2"] / country
    return out


def name_coverage(geos: pd.DataFrame) -> pd.DataFrame:
    cols = list(NAME_FIELDS)
    cov = geos.groupby("level")[cols].agg(lambda s: s.notna().mean() * 100).round(1)
    cov.insert(0, "units", geos.groupby("level").size())
    return cov.reset_index()


def duplicate_names(geos: pd.DataFrame) -> pd.DataFrame:
    g = geos[geos["name_en"].notna() & geos["parent_id"].notna()]
    dup = g[g.duplicated(["parent_id", "name_en"], keep=False)]
    return dup.sort_values(["parent_id", "name_en"])[
        ["level", "parent_id", "name_en", "geography_id"]
    ]


# --- Contiguity graph and geo space ----------------------------------------------------------


def adjacency(versions: gpd.GeoDataFrame, level: int) -> pd.DataFrame:
    """Rook contiguity for one level (shared border ≥ MIN_SHARED_BORDER_M), in EPSG:5235.

    Units with no border neighbours get their DISTANCE_BAND_K nearest units as
    `distance_band` neighbours, so spatial statistics never see an isolated unit.
    """
    lv = versions[versions["level"] == level].to_crs(AREA_CRS).reset_index(drop=True)
    ids = lv["geography_id"].to_numpy()
    geoms = lv.geometry.values
    cols = ["geography_id", "neighbour_id", "shared_border_m", "distance_m", "type"]
    if len(lv) < 2:
        return pd.DataFrame(columns=cols)
    buf = shapely.buffer(geoms, SNAP_TOLERANCE_M)
    tree = shapely.STRtree(geoms)
    left, right = tree.query(buf, predicate="intersects")
    keep = left < right
    left, right = left[keep], right[keep]
    shared = shapely.length(shapely.intersection(shapely.boundary(geoms[left]), buf[right]))
    border = shared >= MIN_SHARED_BORDER_M
    a, b, s = left[border], right[border], shared[border]
    edges = pd.DataFrame(
        {
            "geography_id": np.concatenate([ids[a], ids[b]]),
            "neighbour_id": np.concatenate([ids[b], ids[a]]),
            "shared_border_m": np.concatenate([s, s]),
            "distance_m": 0.0,
            "type": "border",
        }
    )
    connected = set(edges["geography_id"])
    extra = []
    for i, gid in enumerate(ids):
        if gid in connected:
            continue
        dist = shapely.distance(geoms[i], geoms)
        dist[i] = np.inf
        for j in np.argsort(dist)[:DISTANCE_BAND_K]:
            extra.append(
                {
                    "geography_id": gid,
                    "neighbour_id": ids[j],
                    "shared_border_m": None,
                    "distance_m": float(dist[j]),
                    "type": "distance_band",
                }
            )
    if extra:
        edges = pd.concat([edges, pd.DataFrame(extra)], ignore_index=True)
    return edges[cols].sort_values(["geography_id", "neighbour_id"]).reset_index(drop=True)


def geo_vectors(versions: gpd.GeoDataFrame) -> pd.DataFrame:
    """`geo` space: 3D unit vector of each unit's label point (vector-space-model.md §4)."""
    lon = np.radians(versions["label_lon"].to_numpy())
    lat = np.radians(versions["label_lat"].to_numpy())
    xyz = np.column_stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)])
    return pd.DataFrame(
        {
            "entity_type": "place",
            "entity_id": versions["geography_id"].to_numpy(),
            "period": None,
            "space_id": "geo",
            "space_version": "0.1",
            "vintage": VINTAGE,
            "vector": list(xyz.astype("float32")),
            "norm": np.linalg.norm(xyz, axis=1).astype("float32"),
        }
    )


# --- Report and outputs ----------------------------------------------------------------------


def _md_table(df: pd.DataFrame, floatfmt: str = ".3f") -> str:
    def fmt(v: object) -> str:
        if isinstance(v, float):
            return "" if np.isnan(v) else format(v, floatfmt)
        if v is None:
            return ""
        return str(v)

    head = "| " + " | ".join(map(str, df.columns)) + " |"
    sep = "|" + "---|" * len(df.columns)
    body = ["| " + " | ".join(fmt(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([head, sep, *body])


def add_provisional(
    geos: pd.DataFrame,
    versions: gpd.GeoDataFrame,
    catalog_root: Path,
    gdb_ref: SnapshotRef,
) -> tuple[pd.DataFrame, gpd.GeoDataFrame, pd.DataFrame, list[str]]:
    """Add provisional units (D-022) from the catalogue; geometry = union of composed_of units.

    Returns updated geographies and versions, the provisional relation edges, and errors.
    """
    prov_path = catalog_root / "geographies" / "provisional.csv"
    rel_path = catalog_root / "geographies" / "relations" / "provisional.csv"
    if not prov_path.exists():
        return geos, versions, pd.DataFrame(columns=build_relations(geos.head(0)).columns), []
    prov = pd.read_csv(prov_path, dtype=str, keep_default_na=False).replace("", None)
    rel = pd.read_csv(rel_path, dtype=str, keep_default_na=False).replace("", None)
    rel["weight"] = pd.to_numeric(rel["weight"])
    errors: list[str] = []
    level_of = dict(zip(geos["geography_id"], geos["level"], strict=False))
    geom_of = versions.set_index("geography_id").geometry
    new_geos, new_versions = [], []
    for p in prov.itertuples(index=False):
        level = int(p.level)
        members = rel[(rel["geography_id"] == p.geography_id) & (rel["relation"] == "composed_of")][
            "related_id"
        ]
        missing = [m for m in members if m not in level_of]
        wrong = [m for m in members if m in level_of and level_of[m] != level + 1]
        if missing or wrong or members.empty:
            errors.append(
                f"{p.geography_id}: composed_of members missing {missing[:5]} or at the wrong level {wrong[:5]}"
            )
            continue
        geom = shapely.union_all(geom_of.reindex(members).values)
        label = shapely.point_on_surface(geom)
        valid_from = pd.to_datetime(p.valid_from).date() if p.valid_from else None
        new_geos.append({
            "geography_id": p.geography_id, "scheme": "admin", "level": level,
            "level_name": LEVEL_NAMES[level], "name_en": p.name_en, "name_si": p.name_si,
            "name_ta": p.name_ta, "alt_names": [], "parent_id": p.parent_id,
            "status": p.status, "valid_from": valid_from, "valid_to": None,
        })  # fmt: skip
        new_versions.append({
            "geography_id": p.geography_id, "level": level, "vintage": VINTAGE,
            "valid_from": valid_from,
            "area_km2": float(gpd.GeoSeries([geom], crs="EPSG:4326").to_crs(AREA_CRS).area.iloc[0]) / 1e6,
            "source_area_sqkm": np.nan, "label_lon": shapely.get_x(label), "label_lat": shapely.get_y(label),
            "source_dataset": f"{p.source} (geometry: union of {len(members)} COD-AB units)",
            "snapshot_sha256": gdb_ref.sha256, "status": p.status, "geometry": geom,
        })  # fmt: skip
    if new_geos:
        g2 = pd.DataFrame(new_geos)
        g2["level"] = g2["level"].astype("int8")
        geos = pd.concat([geos, g2], ignore_index=True)
        v2 = gpd.GeoDataFrame(new_versions, geometry="geometry", crs="EPSG:4326")
        v2["level"] = v2["level"].astype("int8")
        versions = gpd.GeoDataFrame(pd.concat([versions, v2], ignore_index=True), crs="EPSG:4326")
    return geos, versions, rel, errors


@dataclass
class SpineResult:
    errors: list[str]
    report_md: str
    outputs: list[Path]


def build_spine(
    storage: Storage,
    storage_root: Path,
    out_dir: Path,
    *,
    refresh: bool = False,
    catalog_root: Path | None = None,
) -> SpineResult:
    meta_ref, gdb_ref = snapshot(storage, refresh=refresh)
    hdx = json.loads(storage.get(meta_ref.key))["result"]
    path = gdb_path(storage_root, gdb_ref)
    insp = inspect(path)
    units = read_levels(path)
    geos = build_geographies(units)
    override_errors: list[str] = []
    name_overrides = pd.DataFrame()
    if catalog_root is not None:
        geos, name_overrides, override_errors = apply_name_overrides(
            geos, load_overrides(catalog_root.parent / "overrides")
        )
    versions = build_versions(units, gdb_ref)
    relations = build_relations(geos)
    prov_errors: list[str] = []
    if catalog_root is not None:
        geos, versions, prov_rel, prov_errors = add_provisional(
            geos, versions, catalog_root, gdb_ref
        )
        relations = pd.concat([relations, prov_rel], ignore_index=True)
    current = versions[versions["status"] == "current"]

    errors = list(insp.problems) + check_hierarchy(geos) + prov_errors + override_errors
    ampara = geos.loc[geos["geography_id"] == "LK52", "parent_id"].tolist()
    if ampara != ["LK5"]:
        errors.append(f"regression: Ampara LK52 parent is {ampara}, expected ['LK5']")
    invalid = versions[~versions.geometry.is_valid]["geography_id"].tolist()

    outside = outside_parent(versions, geos)
    offenders = outside[outside["share_outside"] > OUTSIDE_PARENT_THRESHOLD]
    disagree = spatial_parent_disagreements(versions, geos)
    rollups = area_rollups(current)  # provisional units overlap COD-AB units; not counted
    names = name_coverage(geos)
    dups = duplicate_names(geos)

    adj = {lv: adjacency(current, lv) for lv in range(1, 5)}
    isolated = {
        lv: sorted(set(df.loc[df["type"] == "distance_band", "geography_id"]))
        for lv, df in adj.items()
    }
    vectors = geo_vectors(versions)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "spatial").mkdir(exist_ok=True)
    (out_dir / "vectors").mkdir(exist_ok=True)
    (out_dir / "qa").mkdir(exist_ok=True)
    outputs: list[Path] = []

    def out(rel: str) -> Path:
        p = out_dir / rel
        outputs.append(p)
        return p

    geos.to_parquet(out("geographies.parquet"), index=False)
    relations.to_parquet(out("geography_relations.parquet"), index=False)
    versions.to_parquet(out("geography_versions.geoparquet"), index=False)
    for lv, df in adj.items():
        df.to_parquet(out(f"spatial/adjacency_{LEVEL_NAMES[lv]}_{VINTAGE}.parquet"), index=False)
    vectors.to_parquet(out(f"vectors/geo_{VINTAGE}.parquet"), index=False)
    gpkg = out(f"geography_spine_{VINTAGE}.gpkg")
    if gpkg.exists():
        gpkg.unlink()  # build output (not raw); rebuilt from scratch each run
    joined = versions.merge(
        geos.drop(columns=["level", "valid_from", "alt_names"]), on="geography_id"
    )
    for lv, name in LEVEL_NAMES.items():
        layer = joined[joined["level"] == lv].copy()
        layer["valid_from"] = layer["valid_from"].astype(str)
        layer.to_file(gpkg, layer=f"admin{lv}_{name}", driver="GPKG")
    labels = gpd.GeoDataFrame(
        joined[["geography_id", "level", "name_en", "name_si", "name_ta"]],
        geometry=gpd.points_from_xy(joined["label_lon"], joined["label_lat"]),
        crs="EPSG:4326",
    )
    labels.to_file(gpkg, layer="label_points", driver="GPKG")
    if len(offenders):
        top = offenders.head(200).merge(versions[["geography_id"]], on="geography_id")
        geom = versions.set_index("geography_id").geometry.reindex(top["geography_id"]).values
        gpd.GeoDataFrame(top, geometry=geom, crs="EPSG:4326").to_file(
            gpkg, layer="qa_outside_parent", driver="GPKG"
        )

    report = render_report(
        hdx=hdx,
        meta_ref=meta_ref,
        gdb_ref=gdb_ref,
        insp=insp,
        geos=geos,
        errors=errors,
        invalid=invalid,
        outside=outside,
        offenders=offenders,
        disagree=disagree,
        rollups=rollups,
        names=names,
        dups=dups,
        adj=adj,
        isolated=isolated,
    )
    report += _overrides_section(name_overrides)
    out("qa/geography-spine-v0.md").write_text(report, encoding="utf-8")
    return SpineResult(errors=errors, report_md=report, outputs=outputs)


def _overrides_section(applied: pd.DataFrame) -> str:
    lines = ["", "## Name overrides applied", ""]
    if applied.empty:
        return "\n".join([*lines, "None.", ""])
    lines += [
        f"{len(applied)} person-made name corrections from `overrides/{SPINE_DATASET_ID}.csv` "
        "(AGENTS rule 3, D-028). COD-AB v03 had no name for these units.",
        "",
        "| override | unit | field | new value |",
        "|---|---|---|---|",
    ]
    for r in applied.itertuples(index=False):
        lines.append(f"| {r.override_id} | {r.geography_id} | {r.field} | {r.new_value} |")
    return "\n".join([*lines, ""])


def render_report(
    *,
    hdx: dict[str, object],
    meta_ref: SnapshotRef,
    gdb_ref: SnapshotRef,
    insp: Inspection,
    geos: pd.DataFrame,
    errors: Sequence[str],
    invalid: Sequence[str],
    outside: pd.DataFrame,
    offenders: pd.DataFrame,
    disagree: pd.DataFrame,
    rollups: pd.DataFrame,
    names: pd.DataFrame,
    dups: pd.DataFrame,
    adj: dict[int, pd.DataFrame],
    isolated: dict[int, list[str]],
) -> str:
    counts = geos[geos["status"] == "current"].groupby("level").size().to_dict()
    prov_counts = geos[geos["status"] == "provisional"].groupby("level").size().to_dict()
    cmp_rows = []
    for lv, lname in LEVEL_NAMES.items():
        extra = f" (+{prov_counts[lv]} provisional)" if lv in prov_counts else ""
        row = {"Level": f"{lv} {lname}", "COD-AB v03 (this build)": f"{counts.get(lv, 0):,}{extra}"}
        for ref, vals in REFERENCE_COUNTS.items():
            row[ref] = vals.get(lv, "")
        cmp_rows.append(row)
    adj_rows = []
    for lv, df in adj.items():
        border = df[df["type"] == "border"]
        n = int(((geos["level"] == lv) & (geos["status"] == "current")).sum())
        adj_rows.append(
            {
                "Level": f"{lv} {LEVEL_NAMES[lv]}",
                "Units": n,
                "Border edges (undirected)": len(border) // 2,
                "Mean neighbours": f"{len(border) / n:.2f}" if n else "0",
                "Units with no border neighbour": len(isolated[lv]),
            }
        )
    lang_names = {"name_en": "English", "name_si": "Sinhala", "name_ta": "Tamil"}
    name_of = dict(zip(geos["geography_id"], geos["name_en"], strict=False))
    missing = geos.groupby("level")[list(NAME_FIELDS)].agg(lambda s: int(s.isna().sum()))
    dup_summary = dups.groupby("level").size().rename("units in duplicate-name sets").reset_index()

    lines = [
        "# QA report: geography spine v0 (COD-AB admin levels 0-4)",
        "",
        "Generated by `slf spine build` (`pipeline/slf/datasets/cod_ab_admin.py`, prompt G01).",
        "",
        f"**Result:** {'PASS' if not errors else 'FAIL'}: {len(errors)} blocking errors.",
        "",
        "## 1. Source and snapshot",
        "",
        f"- Dataset: {hdx.get('title')} (HDX `cod-ab-lka`), licence {hdx.get('license_title')}.",
        f"- Source stated by HDX: {hdx.get('dataset_source')}. Vintage name used: `{VINTAGE}`.",
        f"- HDX dataset date: {hdx.get('dataset_date')}; "
        f"resource last modified {hdx.get('last_modified')}.",
        f"- Geodatabase snapshot: `{gdb_ref.key}`, sha256 `{gdb_ref.sha256}`, "
        f"{gdb_ref.size_bytes:,} bytes, retrieved {gdb_ref.retrieved_at}.",
        f"- Metadata snapshot: `{meta_ref.key}`, sha256 `{meta_ref.sha256}`.",
        "- HDX caveats (quoted from the metadata snapshot):",
        "",
        *[f"  > {ln}" for ln in str(hdx.get("caveats") or "").splitlines() if ln.strip()],
        "",
        "## 2. Inspection (before any transformation)",
        "",
        insp.to_markdown(),
        "",
        "Name fields: every admin layer declares `lang=en`, `lang1=si`, `lang2=ta`, so "
        "`admN_name` → English, `admN_name1` → Sinhala, `admN_name2` → Tamil. "
        + ("Confirmed on all five layers." if not insp.problems else f"Problems: {insp.problems}"),
        "",
        "## 3. Blocking checks",
        "",
        "- Unique ids, every parent exists, parent is exactly one level up: "
        + ("pass" if not [e for e in errors if "parent" in e or "duplicate" in e] else "FAIL"),
        "- Ampara `LK52` → Eastern Province `LK5` (regression for the Lanka Data Layer bug): "
        + ("pass" if not [e for e in errors if "Ampara" in e] else "FAIL"),
        "",
        *([f"- ERROR: {e}" for e in errors[:50]] or ["No blocking errors."]),
        "",
        "## 4. Unit counts compared (not resolved here; that is G02)",
        "",
        _md_table(pd.DataFrame(cmp_rows)),
        "",
        "## 5. Geometry",
        "",
        f"- Invalid geometries (OGC validity): {len(invalid)}"
        + (f": {', '.join(invalid[:20])}" if invalid else ""),
        "- Canonical geometry is kept unsimplified. Areas computed in EPSG:5235.",
        "",
        "Area roll-up per level against the country polygon:",
        "",
        _md_table(rollups.rename(columns={"sum": "area_km2"}), ".2f"),
        "",
        f"### Units outside their attribute parent (> {OUTSIDE_PARENT_THRESHOLD:.0%} of area)",
        "",
        f"{len(offenders)} of {len(outside)} units exceed the threshold. Top 10:",
        "",
        _md_table(offenders.head(10), ".4f") if len(offenders) else "None.",
        "",
        "Distribution of the share outside parent, all units: "
        + ", ".join(
            f"{q:.0%} ≤ {outside['share_outside'].quantile(q):.5f}" for q in (0.5, 0.9, 0.99)
        )
        + f", max {outside['share_outside'].max():.4f}.",
        "",
        "### Attribute parent vs spatial parent (label point)",
        "",
        f"{len(disagree)} units have a label point outside their attribute parent. "
        "Parents are **not** changed; any fix needs the lead's decision "
        "or an override with evidence.",
        "",
        _md_table(disagree.head(20)) if len(disagree) else "None.",
        "",
        "## 6. Names",
        "",
        "Coverage (% of units with a name) per level and language:",
        "",
        _md_table(names.rename(columns=lang_names), ".1f"),
        "",
        "Missing names (count of units) per level:",
        "",
        _md_table(missing.rename(columns=lang_names).reset_index()),
        "",
        "Missing Tamil names stay null: names are never machine-transliterated into the "
        "published field (data-model.md §3.6).",
        "",
        "Duplicate English names within the same parent (ids remain the keys):",
        "",
        _md_table(dup_summary) if len(dup_summary) else "None.",
        "",
        "Examples:",
        "",
        _md_table(dups.head(10)) if len(dups) else "None.",
        "",
        "## 7. Contiguity graph",
        "",
        f"Rook contiguity in EPSG:5235: boundaries within {SNAP_TOLERANCE_M:g} m "
        "count as touching; "
        f"a shared border of at least {MIN_SHARED_BORDER_M:g} m makes two units neighbours "
        f"(shorter contacts are corner touches). Units with no border neighbour get their "
        f"{DISTANCE_BAND_K} nearest units as `distance_band` neighbours.",
        "",
        _md_table(pd.DataFrame(adj_rows)),
        "",
        *[
            f"- Level {lv} without border neighbours (islands or separated units): "
            + ", ".join(f"{gid} {name_of.get(gid) or '(no English name)'}" for gid in v[:30])
            + (f" … (+{len(v) - 30})" if len(v) > 30 else "")
            for lv, v in isolated.items()
            if v
        ],
        "",
        "## 8. Provisional units (D-022)",
        "",
        "Units missing from COD-AB, added from `catalog/geographies/provisional.csv`. Geometry is the union of "
        "their `composed_of` units. They overlap COD-AB units, so they are excluded from area roll-ups and the "
        "contiguity graph.",
        "",
        _md_table(
            geos.loc[
                geos["status"] == "provisional", ["geography_id", "level", "name_en", "parent_id"]
            ]
        )
        if (geos["status"] == "provisional").any()
        else "None.",
        "",
        "## 9. Outputs",
        "",
        "`geographies.parquet`, `geography_relations.parquet` (parent edges, D-021), "
        "`geography_versions.geoparquet`, `spatial/adjacency_{level}_" + VINTAGE + ".parquet`, "
        "`vectors/geo_" + VINTAGE + ".parquet`, and `geography_spine_" + VINTAGE + ".gpkg` "
        "(layers per level, label points and `qa_outside_parent` for QGIS).",
        "",
    ]
    return "\n".join(lines)


def relations_csv(relations: pd.DataFrame) -> str:
    buf = io.StringIO()
    relations.to_csv(buf, index=False)
    return buf.getvalue()
