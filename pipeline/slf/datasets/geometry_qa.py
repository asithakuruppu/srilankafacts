"""Geometry QA for the spine (prompt G03).

Checks canonical (unsimplified) COD-AB geometry: validity, emptiness, parts and holes; overlaps
and gaps between siblings, and coverage of each parent (EPSG:5235); then compares districts and
DS divisions with NSDI shapes (intersection over union). Findings are reported, never fixed:
geometry is only repaired in a flagged copy, and only if invalid.
"""

# pandas/geopandas stubs can't follow these operations; behaviour is covered by tests.
# pyright: reportArgumentType=false, reportCallIssue=false, reportAttributeAccessIssue=false
# pyright: reportOperatorIssue=false, reportReturnType=false, reportGeneralTypeIssues=false
# ruff: noqa: E501

from __future__ import annotations

import http.client
import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

from slf.snapshot import USER_AGENT, SnapshotRef, snapshot_bytes
from slf.storage import Storage

AREA_CRS = "EPSG:5235"
NSDI_BASE = "https://gisapps.nsdi.gov.lk/server/rest/services/Srilanka/Boundaries/MapServer"
NSDI_GEOM_LAYERS = {
    3: ("district", "objectid,district_name,district_code,province_code,adjusted_area", 1),
    2: ("ds", "objectid,ds_division_name,ds_division_code,district_code,adjusted_area", 10),
}
PAUSE_S = 2.0
OVERLAP_KM2 = 0.01
GAP_KM2 = 0.01
SLIVER_THINNESS = 0.1  # 4πA/P²: 1 for a circle, near 0 for a thin strip
LEVEL_NAMES = {0: "country", 1: "province", 2: "district", 3: "ds", 4: "gn"}


# --- NSDI geometry snapshot ------------------------------------------------------------------


def _fetch_json_once_retry(url: str) -> dict[str, object]:
    """Fetch JSON; on a truncated response, wait and try exactly once more."""
    for attempt in (1, 2):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.loads(r.read())
        except (http.client.IncompleteRead, TimeoutError, ConnectionError):
            if attempt == 2:
                raise
            time.sleep(10)
    raise AssertionError("unreachable")


def snapshot_nsdi_geometry(storage: Storage) -> SnapshotRef:
    """District and DS polygons from NSDI as GeoJSON (EPSG:4326), small pages with pauses."""
    out: dict[str, object] = {"service": NSDI_BASE, "layers": {}, "queries": []}
    for layer, (name, fields, page) in NSDI_GEOM_LAYERS.items():
        feats: list[object] = []
        offset = 0
        while True:
            q = {
                "where": "1=1", "outFields": fields, "returnGeometry": "true", "outSR": 4326,
                "orderByFields": "objectid", "resultOffset": offset, "resultRecordCount": page,
                "f": "geojson",
            }  # fmt: skip
            url = f"{NSDI_BASE}/{layer}/query?{urllib.parse.urlencode(q)}"
            data = _fetch_json_once_retry(url)
            batch = data.get("features", [])
            feats += batch
            out["queries"].append(url)  # type: ignore[union-attr]
            time.sleep(PAUSE_S)
            if len(batch) < page:
                break
            offset += page
        out["layers"][name] = {"type": "FeatureCollection", "features": feats}  # type: ignore[index]
    return snapshot_bytes(
        storage,
        source="nsdi",
        dataset="nsdi-admin-boundaries",
        filename="nsdi_district_ds_geometry.json",
        content=json.dumps(out).encode("utf-8"),
        url=f"{NSDI_BASE}/{{3,2}}/query (paged GeoJSON; see 'queries')",
        licence_note="no licence text on the service; internal comparison only",
    )


def load_nsdi_geometry(storage: Storage, ref: SnapshotRef) -> dict[str, gpd.GeoDataFrame]:
    data = json.loads(storage.get(ref.key))
    return {
        name: gpd.GeoDataFrame.from_features(fc["features"], crs="EPSG:4326")
        for name, fc in data["layers"].items()
    }


# --- Checks on canonical geometry ------------------------------------------------------------


def structure(versions: gpd.GeoDataFrame) -> pd.DataFrame:
    """Per level: invalid (with reasons), empty, multipart units, total parts and holes."""
    g = versions.geometry.values
    parts = shapely.get_num_geometries(g)
    polys = [shapely.get_parts(x) for x in g]
    holes = np.array([int(sum(shapely.get_num_interior_rings(p))) for p in polys])
    df = pd.DataFrame({
        "level": versions["level"].to_numpy(),
        "valid": shapely.is_valid(g),
        "empty": shapely.is_empty(g),
        "parts": parts,
        "holes": holes,
    })  # fmt: skip
    out = df.groupby("level").agg(
        units=("valid", "size"),
        invalid=("valid", lambda s: int((~s).sum())),
        empty=("empty", "sum"),
        multipart_units=("parts", lambda s: int((s > 1).sum())),
        max_parts=("parts", "max"),
        units_with_holes=("holes", lambda s: int((s > 0).sum())),
        total_holes=("holes", "sum"),
    )
    return out.reset_index()


def invalid_reasons(versions: gpd.GeoDataFrame) -> pd.DataFrame:
    bad = versions[~versions.geometry.is_valid]
    return pd.DataFrame(
        {
            "geography_id": bad["geography_id"],
            "reason": shapely.is_valid_reason(bad.geometry.values),
        }
    )


def sibling_overlaps(
    versions: gpd.GeoDataFrame, geos: pd.DataFrame, level: int
) -> gpd.GeoDataFrame:
    """Overlaps between units of one level (siblings or not) above OVERLAP_KM2, in EPSG:5235."""
    lv = versions[versions["level"] == level].to_crs(AREA_CRS).reset_index(drop=True)
    ids = lv["geography_id"].to_numpy()
    g = lv.geometry.values
    left, right = shapely.STRtree(g).query(g, predicate="intersects")
    keep = left < right
    left, right = left[keep], right[keep]
    inter = shapely.intersection(g[left], g[right])
    area = shapely.area(inter) / 1e6
    big = area > OVERLAP_KM2
    parent = dict(zip(geos["geography_id"], geos["parent_id"], strict=False))
    a, b = ids[left[big]], ids[right[big]]
    out = gpd.GeoDataFrame(
        {
            "level": level,
            "geography_id": a,
            "other_id": b,
            "same_parent": [parent.get(x) == parent.get(y) for x, y in zip(a, b, strict=True)],
            "overlap_km2": area[big],
        },
        geometry=inter[big],
        crs=AREA_CRS,
    )
    return out.sort_values("overlap_km2", ascending=False).to_crs("EPSG:4326")


def parent_gaps(versions: gpd.GeoDataFrame, geos: pd.DataFrame, level: int) -> gpd.GeoDataFrame:
    """Parts of each parent (level-1) not covered by its children (level), above GAP_KM2."""
    metric = versions.to_crs(AREA_CRS)
    children = metric[metric["level"] == level].merge(
        geos[["geography_id", "parent_id"]], on="geography_id"
    )
    parents = metric[metric["level"] == level - 1].set_index("geography_id")
    rows = []
    for pid, grp in children.groupby("parent_id"):
        if pid not in parents.index:
            continue
        gap = shapely.difference(
            parents.loc[pid, "geometry"], shapely.union_all(grp.geometry.values)
        )
        for part in shapely.get_parts(gap):
            a = shapely.area(part) / 1e6
            if a > GAP_KM2:
                per = shapely.length(part)
                rows.append({"level": level, "parent_id": pid, "gap_km2": a,
                             "thinness": 4 * np.pi * shapely.area(part) / per**2 if per else 0.0, "geometry": part})  # fmt: skip
    if not rows:
        return gpd.GeoDataFrame(
            columns=["level", "parent_id", "gap_km2", "thinness", "sliver", "geometry"],
            geometry="geometry",
            crs="EPSG:4326",
        )
    out = gpd.GeoDataFrame(rows, geometry="geometry", crs=AREA_CRS)
    out["sliver"] = out["thinness"] < SLIVER_THINNESS
    return out.sort_values("gap_km2", ascending=False).to_crs("EPSG:4326")


def coverage(versions: gpd.GeoDataFrame) -> pd.DataFrame:
    metric = versions.to_crs(AREA_CRS)
    country = float(shapely.area(metric.loc[metric["level"] == 0, "geometry"].iloc[0])) / 1e6
    rows = []
    for lv in range(1, 5):
        u = shapely.union_all(metric.loc[metric["level"] == lv, "geometry"].values)
        covered = shapely.area(u) / 1e6
        rows.append({"level": lv, "level_name": LEVEL_NAMES[lv], "union_km2": covered, "country_km2": country,
                     "missing_km2": country - covered, "missing_pct": 100 * (country - covered) / country})  # fmt: skip
    return pd.DataFrame(rows)


def compare_with_nsdi(
    versions: gpd.GeoDataFrame, nsdi: gpd.GeoDataFrame, code_to_gid: dict[str, str], level: int
) -> pd.DataFrame:
    """Intersection over union per unit, matched through the crosswalk codes."""
    ours = versions[versions["level"] == level].to_crs(AREA_CRS).set_index("geography_id")
    theirs = nsdi.to_crs(AREA_CRS)
    code_col = "district_code" if level == 2 else "ds_division_code"
    name_col = "district_name" if level == 2 else "ds_division_name"
    theirs = theirs.assign(
        code=theirs[code_col].astype(str),
        geography_id=theirs[code_col].astype(str).map(code_to_gid),
    )
    # NSDI can hold several features per unit (duplicated codes): dissolve by geography_id
    matched = theirs.dropna(subset=["geography_id"])
    diss = matched.dissolve(
        by="geography_id", aggfunc={"code": "first", name_col: "first", "adjusted_area": "sum"}
    )
    rows = []
    for gid, row in diss.iterrows():
        if gid not in ours.index:
            continue
        a, b = ours.loc[gid, "geometry"], row.geometry
        inter = shapely.area(shapely.intersection(a, b))
        union = shapely.area(shapely.union(a, b))
        # where does the NSDI polygon actually lie? (largest share on one spine unit)
        hits = ours.geometry.values[
            shapely.STRtree(ours.geometry.values).query(b, predicate="intersects")
        ]
        hit_ids = ours.index.to_numpy()[
            shapely.STRtree(ours.geometry.values).query(b, predicate="intersects")
        ]
        shares = shapely.area(shapely.intersection(hits, b)) / max(shapely.area(b), 1e-9)
        best = int(np.argmax(shares)) if len(shares) else -1
        rows.append({
            "geography_id": gid, "nsdi_code": row["code"], "nsdi_name": row[name_col],
            "iou": inter / union if union else np.nan,
            "area_km2": shapely.area(a) / 1e6, "nsdi_area_km2": shapely.area(b) / 1e6,
            "nsdi_adjusted_area": row["adjusted_area"],
            "nsdi_polygon_mostly_on": hit_ids[best] if best >= 0 else None,
            "share_on_it": float(shares[best]) if best >= 0 else np.nan,
        })  # fmt: skip
    out = pd.DataFrame(rows)
    unmatched = theirs[theirs["geography_id"].isna()][["code", name_col]].rename(
        columns={name_col: "nsdi_name"}
    )
    out.attrs["unmatched"] = unmatched
    return out.sort_values("iou")


def make_valid_copy(versions: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    bad = versions[~versions.geometry.is_valid].copy()
    bad["geometry"] = shapely.make_valid(bad.geometry.values)
    bad["repaired"] = True
    return bad


# --- Build and report ------------------------------------------------------------------------


@dataclass
class GeometryQA:
    structure: pd.DataFrame
    invalid: pd.DataFrame
    overlaps: dict[int, gpd.GeoDataFrame]
    gaps: dict[int, gpd.GeoDataFrame]
    coverage: pd.DataFrame
    iou: dict[int, pd.DataFrame]
    disputes: pd.DataFrame
    nsdi_ref: SnapshotRef | None


def run(versions: gpd.GeoDataFrame, geos: pd.DataFrame, nsdi: dict[str, gpd.GeoDataFrame] | None,
        nsdi_codes: pd.DataFrame | None, nsdi_ref: SnapshotRef | None, disputes: pd.DataFrame) -> GeometryQA:  # fmt: skip
    iou: dict[int, pd.DataFrame] = {}
    if nsdi is not None and nsdi_codes is not None:
        ds_map = dict(
            zip(nsdi_codes["external_code"].astype(str), nsdi_codes["geography_id"], strict=False)
        )
        iou[2] = compare_with_nsdi(
            versions,
            nsdi["district"],
            {str(c): f"LK{c}" for c in nsdi["district"]["district_code"]},
            2,
        )
        iou[3] = compare_with_nsdi(versions, nsdi["ds"], ds_map, 3)
    return GeometryQA(
        structure=structure(versions),
        invalid=invalid_reasons(versions),
        overlaps={lv: sibling_overlaps(versions, geos, lv) for lv in range(1, 5)},
        gaps={lv: parent_gaps(versions, geos, lv) for lv in range(1, 5)},
        coverage=coverage(versions),
        iou=iou,
        disputes=disputes,
        nsdi_ref=nsdi_ref,
    )


def _t(df: pd.DataFrame, fmt: str = ".4f") -> str:
    if df is None or df.empty:
        return "None."
    df = pd.DataFrame(df.drop(columns="geometry", errors="ignore"))

    def f(v: object) -> str:
        if isinstance(v, (float, np.floating)):
            return "" if np.isnan(v) else format(float(v), fmt)
        return "" if v is None else str(v)

    lines = ["| " + " | ".join(map(str, df.columns)) + " |", "|" + "---|" * len(df.columns)]
    lines += ["| " + " | ".join(f(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join(lines)


def checklist(qa: GeometryQA, names: dict[str, str]) -> list[str]:
    items: list[str] = []

    def nm(g: str) -> str:
        return f"{g} {names.get(g) or '(no name)'}"

    items.append(
        "**Ampara district (`LK52`)**: confirm it sits in Eastern Province (`LK5`) and its outline looks right. Why: the Lanka Data Layer hierarchy error (audit §7)."
    )
    if 2 in qa.iou and not qa.iou[2].empty:
        w = qa.iou[2].iloc[0]
        items.append(
            f"**District with the lowest NSDI agreement: {nm(w['geography_id'])}** (IoU {w['iou']:.3f}). Toggle `nsdi_district` over `admin2_district`. Why: largest shape difference between the two official-looking sources."
        )
    if 3 in qa.iou and not qa.iou[3].empty:
        for _, w in qa.iou[3].head(3).iterrows():
            where = w["nsdi_polygon_mostly_on"]
            if where != w["geography_id"] and w["share_on_it"] > 0.9:
                items.append(
                    f"**NSDI polygon labelled '{w['nsdi_name']}' lies on {nm(where)}**, not on {nm(w['geography_id'])}. Toggle `nsdi_ds` over `admin3_ds`. Why: confirms a labelling error in NSDI (similar names), so NSDI codes must not be trusted for these units."
                )
            else:
                items.append(
                    f"**DS {nm(w['geography_id'])} vs NSDI '{w['nsdi_name']}'** (IoU {w['iou']:.3f}). Why: one of the biggest DS shape differences; check whether NSDI shows an older, unsplit unit."
                )
    for lv in (4, 3):
        if not qa.overlaps[lv].empty:
            o = qa.overlaps[lv].iloc[0]
            items.append(
                f"**Largest {LEVEL_NAMES[lv].upper()} overlap: {nm(o['geography_id'])} and {nm(o['other_id'])}** ({o['overlap_km2']:.3f} km², layer `overlaps_{LEVEL_NAMES[lv]}`). Why: overlapping units double-count anything apportioned by area."
            )
            break
    for lv in (4, 3):
        if not qa.gaps[lv].empty:
            gp = qa.gaps[lv].iloc[0]
            items.append(
                f"**Largest gap inside {nm(gp['parent_id'])}** ({gp['gap_km2']:.2f} km², layer `gaps_{LEVEL_NAMES[lv]}`). Why: is it water (lagoon, reservoir) or land with no unit?"
            )
            break
    if not qa.disputes.empty:
        d = qa.disputes.iloc[0]
        items.append(
            f"**A GN flagged by NSDI as disputed: {nm(d['geography_id'])}** ('{d['dispute']}', layer `nsdi_disputed_gn`). Why: NSDI records {len(qa.disputes)} GN boundary disputes; COD-AB carries no such flag."
        )
    items.append(
        "**Coastline near Jaffna lagoon and Mannar**: compare `admin0_country` with the basemap. Why: country coverage gaps are reported per level in §3."
    )
    items.append(
        "**Islands (Delft `LK4142` and the GN islands in the spine QA report)**: check they are complete. Why: units with no land neighbour get distance-band neighbours."
    )
    return items[:10]


def render(qa: GeometryQA, names: dict[str, str], img: dict[str, str]) -> str:
    ov = pd.DataFrame([{"level": LEVEL_NAMES[lv], "overlaps > 0.01 km²": len(df), "of which siblings": int(df["same_parent"].sum()) if len(df) else 0,
                        "total km²": float(df["overlap_km2"].sum()) if len(df) else 0.0, "largest km²": float(df["overlap_km2"].max()) if len(df) else 0.0}
                       for lv, df in qa.overlaps.items()])  # fmt: skip
    gp = pd.DataFrame([{"level (children)": LEVEL_NAMES[lv], "gaps > 0.01 km²": len(df), "slivers": int(df["sliver"].sum()) if len(df) else 0,
                        "total km²": float(df["gap_km2"].sum()) if len(df) else 0.0, "largest km²": float(df["gap_km2"].max()) if len(df) else 0.0}
                       for lv, df in qa.gaps.items()])  # fmt: skip
    lines = [
        "# Geometry QA: COD-AB v03 (canonical, unsimplified)",
        "",
        "Generated by `slf geometry-qa build` (`pipeline/slf/datasets/geometry_qa.py`, prompt G03). Areas in EPSG:5235. Findings only; no geometry was edited.",
        "",
        "## 1. Structure",
        "",
        _t(qa.structure, ".0f"),
        "",
        f"Invalid geometries: {len(qa.invalid)}. "
        + (
            "No `make_valid` copy needed; tiles and analysis should use the canonical geometry as is."
            if qa.invalid.empty
            else "A flagged `make_valid` copy is in the GeoPackage (`repaired: true`); the original is kept."
        ),
        "",
        _t(qa.invalid) if not qa.invalid.empty else "",
        "## 2. Overlaps between units of the same level",
        "",
        _t(ov, ".3f"),
        "",
        "Top 10 GN overlaps:",
        "",
        _t(qa.overlaps[4].head(10)[["geography_id", "other_id", "same_parent", "overlap_km2"]])
        if len(qa.overlaps[4])
        else "None.",
        "",
        "## 3. Gaps and coverage",
        "",
        "Area of each parent not covered by its children:",
        "",
        _t(gp, ".3f"),
        "",
        "Top 10 gaps inside a DS division (GN level):",
        "",
        _t(
            qa.gaps[4]
            .head(10)[["parent_id", "gap_km2", "thinness", "sliver"]]
            .assign(parent=lambda d: d["parent_id"].map(names))
        )
        if len(qa.gaps[4])
        else "None.",
        "",
        "Coverage of the country polygon by each level:",
        "",
        _t(qa.coverage, ".2f"),
        "",
    ]
    if img.get("gaps"):
        lines += [f"![Gaps in GN coverage]({img['gaps']})", ""]
    lines += ["## 4. Comparison with NSDI shapes", ""]
    if not qa.iou:
        lines += ["Skipped: NSDI geometry not available.", ""]
    else:
        assert qa.nsdi_ref is not None
        lines += [f"NSDI snapshot `{qa.nsdi_ref.key}` (sha256 `{qa.nsdi_ref.sha256[:16]}…`), matched through `catalog/geographies/codes/nsdi.csv`. "
                  "IoU = intersection over union (1 = identical). NSDI `adjusted_area` is shown as published; its definition and unit are unknown.", ""]  # fmt: skip
        for lv, df in qa.iou.items():
            q = df["iou"].quantile([0.1, 0.5]).to_list() if len(df) else [np.nan, np.nan]
            lines += [f"### {'Districts' if lv == 2 else 'DS divisions'}: {len(df)} compared; median IoU {q[1]:.4f}, 10th percentile {q[0]:.4f}; {int((df['iou'] < 0.9).sum())} below 0.9", "",
                      "Lowest 10:", "", _t(df.head(10), ".3f"), ""]  # fmt: skip
            mix = df[
                (df["iou"] < 0.5)
                & (df["nsdi_polygon_mostly_on"] != df["geography_id"])
                & (df["share_on_it"] > 0.9)
            ]
            if len(mix):
                lines += [f"**Likely labelling errors in NSDI ({len(mix)}):** the polygon carrying this unit's code and name lies (over 90 %) on a *different* spine unit, usually one with a similar name:", "",
                          _t(mix.assign(lies_on=mix["nsdi_polygon_mostly_on"].map(names))[["geography_id", "nsdi_name", "nsdi_polygon_mostly_on", "lies_on", "share_on_it"]], ".3f"), ""]  # fmt: skip
            older = df[(df["iou"] < 0.9) & (df["nsdi_polygon_mostly_on"] == df["geography_id"])]
            if len(older):
                lines += [f"Units where NSDI's polygon is mostly on the same unit but much larger or smaller ({len(older)}), consistent with NSDI holding older, unsplit units:", "",
                          _t(older[["geography_id", "nsdi_name", "iou", "area_km2", "nsdi_area_km2"]], ".3f"), ""]  # fmt: skip
            un = df.attrs.get("unmatched")
            if un is not None and len(un):
                lines += [f"NSDI features with no spine counterpart ({len(un)}):", "", _t(un), ""]
        if img.get("iou"):
            lines += [f"![DS agreement with NSDI]({img['iou']})", ""]
    lines += [
        "## 5. NSDI boundary-dispute flags on GN divisions",
        "",
        f"{len(qa.disputes)} GN divisions carry a dispute flag in NSDI attributes (matched to spine ids through the crosswalk). COD-AB has no equivalent field.",
        "",
        _t(qa.disputes.groupby("dispute").size().rename("GN units").reset_index())
        if len(qa.disputes)
        else "None.",
        "",
        "## 6. Review checklist for the lead (about one hour in QGIS)",
        "",
        "Open `pipeline/data/build/geometry-qa/geometry_qa_cod-ab-v03.gpkg` and `pipeline/data/build/geography-spine/geography_spine_cod-ab-v03.gpkg` in QGIS, add an OpenStreetMap basemap, then:",
        "",
        *[f"{i}. [ ] {item}" for i, item in enumerate(checklist(qa, names), start=1)],
        "",
        "No `.qgz` project file is included: QGIS is not installed on the build machine, so a generated project could not be checked to open. The GeoPackage layers above are named to be self-explanatory.",
        "",
    ]
    return "\n".join(lines)


def write_gpkg(
    qa: GeometryQA, versions: gpd.GeoDataFrame, nsdi: dict[str, gpd.GeoDataFrame] | None, path: Path
) -> None:
    if path.exists():
        path.unlink()  # build output, rebuilt each run
    for lv, df in qa.overlaps.items():
        if len(df):
            df.to_file(path, layer=f"overlaps_{LEVEL_NAMES[lv]}", driver="GPKG")
    for lv, df in qa.gaps.items():
        if len(df):
            df.to_file(path, layer=f"gaps_{LEVEL_NAMES[lv]}", driver="GPKG")
    if nsdi is not None:
        nsdi["district"].to_file(path, layer="nsdi_district", driver="GPKG")
        nsdi["ds"].to_file(path, layer="nsdi_ds", driver="GPKG")
    for lv, df in qa.iou.items():
        g = versions.set_index("geography_id").geometry.reindex(df["geography_id"]).values
        gpd.GeoDataFrame(df.reset_index(drop=True), geometry=g, crs="EPSG:4326").to_file(
            path, layer=f"nsdi_iou_{LEVEL_NAMES[lv]}", driver="GPKG"
        )
    if len(qa.disputes):
        g = versions.set_index("geography_id").geometry.reindex(qa.disputes["geography_id"]).values
        gpd.GeoDataFrame(qa.disputes.reset_index(drop=True), geometry=g, crs="EPSG:4326").to_file(
            path, layer="nsdi_disputed_gn", driver="GPKG"
        )
    if not qa.invalid.empty:
        make_valid_copy(versions).to_file(path, layer="repaired_make_valid", driver="GPKG")


def thumbnails(qa: GeometryQA, versions: gpd.GeoDataFrame, out_dir: Path) -> dict[str, str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir.mkdir(parents=True, exist_ok=True)
    made: dict[str, str] = {}
    country = versions[versions["level"] == 0]
    if len(qa.gaps[4]):
        fig, ax = plt.subplots(figsize=(5, 7), dpi=110)
        country.plot(ax=ax, color="#eeeeee", edgecolor="#999999", linewidth=0.4)
        qa.gaps[4].plot(ax=ax, color="#d62728", edgecolor="#d62728", linewidth=0.8)
        ax.set_title("Gaps inside DS divisions not covered by GNs (> 0.01 km²)", fontsize=8)
        ax.set_axis_off()
        fig.savefig(out_dir / "gn-gaps.png", bbox_inches="tight")
        plt.close(fig)
        made["gaps"] = "img/gn-gaps.png"
    if 3 in qa.iou and len(qa.iou[3]):
        ds = versions[versions["level"] == 3].merge(
            qa.iou[3][["geography_id", "iou"]], on="geography_id", how="left"
        )
        fig, ax = plt.subplots(figsize=(5, 7), dpi=110)
        ds.plot(ax=ax, column="iou", cmap="viridis", vmin=0.5, vmax=1.0, legend=True, edgecolor="white", linewidth=0.2,
                missing_kwds={"color": "#dddddd", "label": "no NSDI match"})  # fmt: skip
        ax.set_title("DS divisions: agreement with NSDI shape (IoU)", fontsize=8)
        ax.set_axis_off()
        fig.savefig(out_dir / "ds-iou.png", bbox_inches="tight")
        plt.close(fig)
        made["iou"] = "img/ds-iou.png"
    return made
