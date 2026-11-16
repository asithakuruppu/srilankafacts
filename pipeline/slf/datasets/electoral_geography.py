"""Electoral geography (G05, SCHEME electoral): electoral districts (ED) and polling divisions (PD).

Units and codes come from the Election Commission's register of electors by polling division,
2016-2025 (one page per ED: PD letter, PD name, electors per year, ED total). Our ids follow D-004:
``LK-ED-NN`` (Commission ED number) and ``LK-PD-NNX`` (ED number + Commission PD letter).

Composition (data-model §3.4):

- **ED**: each ED is one administrative district, except Jaffna ED (Jaffna + Kilinochchi) and
  Vanni ED (Mannar + Vavuniya + Mullaitivu). The grouping is in
  ``catalog/geographies/relations/electoral_ec-2024.csv`` (``composed_of`` district, weight 1); GN
  membership follows from the admin hierarchy. ED geometry is the union of COD-AB districts.
- **PD**: no official GN list per PD and no PD boundaries with known rights exist publicly
  (``docs/research/rights/election-results.md``). nuuuwan's ``gig-data`` assigns a ``pd_id`` to each
  GN but has no licence and no stated origin. It is read **only inside the local build** to run
  G05's checks and compute test denominators; nothing derived from it is committed or released.
  Its GN ids join to the spine through the G02 crosswalk (``codes/nuuuwan.csv``), never by name.

Checks (G05 "Verify"): unit counts against the register and the result files; weight sums per GN;
coverage (GNs without a unit, units without GNs); IoU of each unit's geometry against the union of
its GNs (EPSG:5235); Census 2024 denominators against registered electors.
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import geopandas as gpd
import pandas as pd
from shapely.geometry import shape
from shapely.ops import unary_union

from slf.snapshot import SnapshotRef, snapshot_url
from slf.storage import Storage

VINTAGE = "ec-2024"
AREA_CRS = "EPSG:5235"
REGISTER_YEARS = tuple(range(2016, 2026))
GIG_SOURCE = "nuuuwan"
GIG_DATASET = "nuuuwan-gig-data"
GIG_COMMIT = "ada93f259a5c950f8a7b1246fcf792f011f9e112"  # master on 2026-11-15
GIG_RAW = f"https://raw.githubusercontent.com/nuuuwan/gig-data/{GIG_COMMIT}"
GIG_LICENCE_NOTE = "no licence (GitHub metadata 2026-11-15); internal QA only, never published"

_NUM = r"\d{1,3}(?:,\d{3})+|\d+"
_ED_HEAD = re.compile(r"Electoral District\s*:\s*-?\s*(\d{1,2})\s*-\s*([A-Za-z][A-Za-z .\-]*)")
_PD_LINE = re.compile(rf"^([A-Z]{{1,2}})\s+(.+?)\s+((?:{_NUM})(?:\s+(?:{_NUM})){{9}})\s*$")
_TOTAL_LINE = re.compile(rf"^((?:{_NUM})(?:\s+(?:{_NUM})){{9}})\s*$")


def ed_id(number: int) -> str:
    return f"LK-ED-{number:02d}"


def pd_id(ed_number: int, letter: str) -> str:
    return f"LK-PD-{ed_number:02d}{letter}"


@dataclass(frozen=True)
class PdEntry:
    ed_number: int
    ed_name: str
    letter: str
    name: str
    electors: Mapping[int, int]
    page: int
    line: int

    @property
    def geography_id(self) -> str:
        return pd_id(self.ed_number, self.letter)


@dataclass
class Register:
    pds: list[PdEntry] = field(default_factory=list)
    ed_names: dict[int, str] = field(default_factory=dict)
    ed_totals: dict[int, dict[int, int]] = field(default_factory=dict)
    ed_pages: dict[int, int] = field(default_factory=dict)
    problems: list[str] = field(default_factory=list)


def _ints(text: str) -> list[int]:
    return [int(t.replace(",", "")) for t in text.split()]


def parse_register(pages: Mapping[int, str]) -> Register:
    """Parse the register of electors by PD (2016-2025), one ED per page.

    Every page must name one ED, list its PDs with ten yearly figures, and end with an ED total
    whose ten figures equal the column sums of its PDs; any deviation is a problem, never ignored.
    """
    reg = Register()
    for page_no in sorted(pages):
        text = pages[page_no]
        head = _ED_HEAD.search(text)
        if not head:
            reg.problems.append(f"page {page_no}: no 'Electoral District' heading")
            continue
        number, name = int(head.group(1)), head.group(2).strip()
        if number in reg.ed_names:
            reg.problems.append(f"page {page_no}: ED {number} already seen on another page")
        reg.ed_names[number] = name
        reg.ed_pages[number] = page_no
        rows: list[PdEntry] = []
        totals: list[list[int]] = []
        for line_no, raw in enumerate(text.splitlines(), start=1):
            line = re.sub(r"\s+", " ", raw).strip()
            if m := _PD_LINE.match(line):
                values = _ints(m.group(3))
                rows.append(
                    PdEntry(
                        ed_number=number,
                        ed_name=name,
                        letter=m.group(1),
                        name=m.group(2).strip(),
                        electors=dict(zip(REGISTER_YEARS, values, strict=True)),
                        page=page_no,
                        line=line_no,
                    )
                )
            elif m := _TOTAL_LINE.match(line):
                totals.append(_ints(m.group(1)))
        if not rows:
            reg.problems.append(f"page {page_no}: ED {number} has no polling division rows")
        letters = [r.letter for r in rows]
        if len(set(letters)) != len(letters):
            reg.problems.append(f"page {page_no}: duplicate PD letters {letters}")
        sums = [sum(r.electors[y] for r in rows) for y in REGISTER_YEARS]
        match = [t for t in totals if t == sums]
        if match:
            reg.ed_totals[number] = dict(zip(REGISTER_YEARS, match[0], strict=True))
        else:
            reg.problems.append(
                f"page {page_no}: ED {number} PD sums {sums} match no total line {totals}"
            )
        reg.pds.extend(rows)
    return reg


# --- codes and relations (committed to catalog/) ---------------------------------------------


def code_rows(reg: Register, register_ref: SnapshotRef) -> list[dict[str, object]]:
    """GEO_CODE rows: Commission codes (ED number, ED-letter) and nuuuwan's EC-ids, per unit."""
    note = f"register of electors 2016-2025, sha256 {register_ref.sha256[:12]}"
    rows: list[dict[str, object]] = []
    for number in sorted(reg.ed_names):
        page = reg.ed_pages[number]
        for system, code in (("election-commission", str(number)), ("nuuuwan", f"EC-{number:02d}")):
            rows.append(
                {
                    "geography_id": ed_id(number),
                    "vintage": VINTAGE,
                    "code_system": system,
                    "external_code": code,
                    "external_name": reg.ed_names[number],
                    "match_method": "exact_code",
                    "confidence": 1.0,
                    "notes": f"{note}, page {page}"
                    if system == "election-commission"
                    else "nuuuwan EC-id = Commission ED number",
                }
            )
    for p in sorted(reg.pds, key=lambda p: (p.ed_number, p.letter)):
        for system, code in (
            ("election-commission", f"{p.ed_number}-{p.letter}"),
            ("nuuuwan", f"EC-{p.ed_number:02d}{p.letter}"),
        ):
            rows.append(
                {
                    "geography_id": p.geography_id,
                    "vintage": VINTAGE,
                    "code_system": system,
                    "external_code": code,
                    "external_name": p.name,
                    "match_method": "exact_code",
                    "confidence": 1.0,
                    "notes": f"{note}, page {p.page} line {p.line}"
                    if system == "election-commission"
                    else "nuuuwan EC-id = Commission ED number + PD letter",
                }
            )
    return rows


def parent_rows(reg: Register) -> list[dict[str, object]]:
    """GEO_RELATION rows: each ED is the parent of the PDs the register lists under it."""
    return [
        {
            "geography_id": ed_id(p.ed_number),
            "related_id": p.geography_id,
            "relation": "parent",
            "vintage": VINTAGE,
            "weight": None,
            "method": "official_list",
            "source": "election-results",
            "valid_from": None,
            "valid_to": None,
            "notes": f"register of electors 2016-2025 page {p.page}",
        }
        for p in sorted(reg.pds, key=lambda p: (p.ed_number, p.letter))
    ]


# --- nuuuwan gig-data (internal QA input) ----------------------------------------------------


def gig_files(pd_ids: Iterable[str], ed_ids: Iterable[str]) -> list[str]:
    return [
        "ents/gnd.tsv",
        "ents/pd.tsv",
        "ents/ed.tsv",
        *(f"geo/pd/{i}.json" for i in pd_ids),
        *(f"geo/ed/{i}.json" for i in ed_ids),
    ]


def snapshot_gig(storage: Storage, files: Iterable[str]) -> dict[str, SnapshotRef]:
    """Snapshot nuuuwan gig-data files at a pinned commit (reused when already stored)."""
    existing: dict[str, SnapshotRef] = {}
    for key in storage.list(f"raw/{GIG_SOURCE}/{GIG_DATASET}"):
        if key.endswith(".meta.json"):
            meta = json.loads(storage.get(key))
            existing[meta["url"]] = SnapshotRef(**{**meta, "reused": True})
    out: dict[str, SnapshotRef] = {}
    for path in files:
        url = f"{GIG_RAW}/{path}"
        out[path] = existing.get(url) or snapshot_url(
            storage,
            source=GIG_SOURCE,
            dataset=GIG_DATASET,
            url=url,
            filename=path.replace("/", "__"),
            licence_note=GIG_LICENCE_NOTE,
        )
    return out


def read_tsv(storage: Storage, ref: SnapshotRef) -> pd.DataFrame:
    import io

    return pd.read_csv(io.BytesIO(storage.get(ref.key)), sep="\t", dtype=str)


def read_geojson(storage: Storage, ref: SnapshotRef):
    """nuuuwan's geo/*.json: a list of polygons of [lng, lat] rings, or GeoJSON."""
    data = json.loads(storage.get(ref.key))
    if isinstance(data, dict) and "type" in data:
        if data["type"] == "FeatureCollection":
            return unary_union([shape(f["geometry"]) for f in data["features"]])
        if data["type"] == "Feature":
            return shape(data["geometry"])
        return shape(data)
    # nuuuwan format: a list of rings (each a list of [lng, lat], one polygon per ring), or a
    # list of polygons (each a list of rings)
    depth, x = 0, data
    while isinstance(x, list) and x:
        depth, x = depth + 1, x[0]
    coords = [[ring] for ring in data] if depth == 3 else data
    return shape({"type": "MultiPolygon", "coordinates": coords}).buffer(0)


# --- checks ----------------------------------------------------------------------------------


@dataclass
class Composition:
    """unit id -> {gn id: weight}, with the method and source of the weights."""

    members: dict[str, dict[str, float]]
    method: str
    source: str
    notes: list[str] = field(default_factory=list)


def weight_sums(comp: Composition, all_gns: Iterable[str]) -> Counter[float]:
    """Distribution of each GN's total weight across the scheme's units (G05 step 4)."""
    total: dict[str, float] = defaultdict(float)
    for gns in comp.members.values():
        for gn, w in gns.items():
            total[gn] += w
    return Counter(round(total.get(gn, 0.0), 6) for gn in all_gns)


def iou_table(
    unit_geoms: Mapping[str, object], gn_geoms: gpd.GeoSeries, comp: Composition
) -> pd.DataFrame:
    """IoU of each unit's geometry against the union of its member GNs, in EPSG:5235."""
    rows = []
    for unit, members in sorted(comp.members.items()):
        geom = unit_geoms.get(unit)
        ids = [g for g in members if g in gn_geoms.index]
        if geom is None or not ids:
            rows.append({"unit": unit, "iou": None, "unit_km2": None, "gn_union_km2": None})
            continue
        union = unary_union(list(gn_geoms.loc[ids].values))
        a = gpd.GeoSeries([cast(Any, geom)], crs="EPSG:4326").to_crs(AREA_CRS).iloc[0]
        b = gpd.GeoSeries([union], crs=gn_geoms.crs).to_crs(AREA_CRS).iloc[0]
        inter = a.intersection(b).area
        uni = a.union(b).area
        rows.append(
            {
                "unit": unit,
                "iou": round(inter / uni, 4) if uni else None,
                "unit_km2": round(a.area / 1e6, 2),
                "gn_union_km2": round(b.area / 1e6, 2),
            }
        )
    return pd.DataFrame(rows)


def denominators(
    comp: Composition, gn_values: pd.DataFrame, indicators: Iterable[str]
) -> pd.DataFrame:
    """Sum of (weight x GN value) per unit and indicator; counts only (rates are recomputed later)."""
    wanted = list(indicators)
    values = gn_values[gn_values["indicator_id"].isin(wanted)].pivot_table(
        index="geography_id", columns="indicator_id", values="value", aggfunc="first"
    )
    rows = []
    for unit, members in sorted(comp.members.items()):
        ids = [g for g in members if g in values.index]
        row: dict[str, object] = {
            "geography_id": unit,
            "gn_members": len(members),
            "gn_with_census": len(ids),
        }
        for ind in wanted:
            if ind in values.columns:
                row[ind] = float(
                    sum(
                        members[g] * float(values.at[g, ind])
                        for g in ids
                        if pd.notna(values.at[g, ind])
                    )
                )
        rows.append(row)
    return pd.DataFrame(rows)


# --- ED grouping (catalog/geographies/relations/electoral_ec-2024.csv) -----------------------

ED_DISTRICTS: dict[int, tuple[tuple[str, str], ...]] = {
    1: (("LK11", "Colombo"),), 2: (("LK12", "Gampaha"),), 3: (("LK13", "Kalutara"),),
    4: (("LK21", "Kandy"),), 5: (("LK22", "Matale"),), 6: (("LK23", "Nuwara Eliya"),),
    7: (("LK31", "Galle"),), 8: (("LK32", "Matara"),), 9: (("LK33", "Hambantota"),),
    10: (("LK41", "Jaffna"), ("LK45", "Kilinochchi")),
    11: (("LK42", "Mannar"), ("LK43", "Vavuniya"), ("LK44", "Mullaitivu")),
    12: (("LK51", "Batticaloa"),), 13: (("LK52", "Ampara"),), 14: (("LK53", "Trincomalee"),),
    15: (("LK61", "Kurunegala"),), 16: (("LK62", "Puttalam"),), 17: (("LK71", "Anuradhapura"),),
    18: (("LK72", "Polonnaruwa"),), 19: (("LK81", "Badulla"),), 20: (("LK82", "Monaragala"),),
    21: (("LK91", "Ratnapura"),), 22: (("LK92", "Kegalle"),),
}  # fmt: skip
ED_NOTE = {
    10: "Jaffna ED = Jaffna + Kilinochchi districts (Wikipedia 'Electoral districts of Sri Lanka', "
    "secondary); the register lists PD K Kilinochchi under ED 10",
    11: "Vanni ED = Mannar + Vavuniya + Mullaitivu districts (Wikipedia, secondary); the register "
    "lists PDs Mannar, Vavuniya and Mullaitivu under ED 11",
}
ED_NOTE_DEFAULT = (
    "ED conterminous with its administrative district (Wikipedia, secondary); checked against "
    "nuuuwan's GN-to-ED assignment in QA"
)


def ed_rows() -> list[dict[str, object]]:
    return [
        {
            "geography_id": ed_id(n),
            "related_id": d,
            "relation": "composed_of",
            "vintage": VINTAGE,
            "weight": 1.0,
            "method": "manual",
            "source": "election-results",
            "valid_from": None,
            "valid_to": None,
            "notes": ED_NOTE.get(n, ED_NOTE_DEFAULT),
        }
        for n, districts in sorted(ED_DISTRICTS.items())
        for d, _name in districts
    ]


def write_catalog(reg: Register, register_ref: SnapshotRef, catalog: Path) -> list[Path]:
    """Write the electoral codes and relations CSVs (generated; do not edit by hand)."""
    codes = catalog / "geographies" / "codes" / "electoral-ec-2024.csv"
    rels = catalog / "geographies" / "relations" / "electoral_ec-2024.csv"
    pd.DataFrame(code_rows(reg, register_ref)).to_csv(codes, index=False)
    pd.DataFrame([*ed_rows(), *parent_rows(reg)]).to_csv(rels, index=False)
    return [codes, rels]


# --- build (G05 checks; local only for anything derived from gig-data) -----------------------


@dataclass
class ElectoralBuild:
    outputs: list[Path] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    qa: str = ""


def _gn_districts(spine_dir: Path) -> dict[str, str]:
    """GN p-code -> district p-code, through the spine's parent edges (never by parsing codes)."""
    rel = pd.read_parquet(spine_dir / "geography_relations.parquet")
    rel = rel[rel["relation"] == "parent"]
    parent = dict(zip(rel["related_id"], rel["geography_id"], strict=False))
    geos = pd.read_parquet(spine_dir / "geographies.parquet")
    level = dict(zip(geos["geography_id"], geos["level"], strict=False))
    out: dict[str, str] = {}
    for gid, lv in level.items():
        if lv != 4:
            continue
        cur: str | None = gid
        while cur is not None and level.get(cur) != 2:
            cur = parent.get(cur)
        if cur is not None:
            out[gid] = cur
    return out


def _census_gn(census_dirs: Iterable[Path], gn_ids: set[str]) -> pd.DataFrame:
    frames = []
    for d in census_dirs:
        f = pd.read_parquet(
            d / "observations.parquet",
            columns=["indicator_id", "geography_id", "value", "breakdown"],
        )
        f = f[f["geography_id"].isin(sorted(gn_ids)) & f["breakdown"].isna()]
        frames.append(f[["indicator_id", "geography_id", "value"]])
    return pd.concat(frames, ignore_index=True).drop_duplicates(["indicator_id", "geography_id"])


DENOMINATORS = (
    "population_total",
    "population_age_0_4",
    "population_age_5_9",
    "population_age_10_14",
    "population_age_15_19",
    "households_total",
    "occupied_housing_units",
)


def _with_adults(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    young = (
        frame["population_age_0_4"] + frame["population_age_5_9"] + frame["population_age_10_14"]
    )
    frame["population_age_15_plus"] = frame["population_total"] - young
    frame["population_age_20_plus"] = (
        frame["population_age_15_plus"] - frame["population_age_15_19"]
    )
    return frame


def build(
    storage: Storage,
    reg: Register,
    spine_dir: Path,
    census_dirs: list[Path],
    catalog: Path,
    results: Mapping[str, float],
    out_dir: Path,
) -> ElectoralBuild:
    res = ElectoralBuild()
    out_dir.mkdir(parents=True, exist_ok=True)
    gn_district = _gn_districts(spine_dir)
    all_gns = set(gn_district)
    district_ed = {d: n for n, ds in ED_DISTRICTS.items() for d, _ in ds}
    geos = pd.read_parquet(spine_dir / "geographies.parquet")
    names = dict(zip(geos["geography_id"], geos["name_en"], strict=False))
    for n, ds in ED_DISTRICTS.items():
        for d, name in ds:
            if names.get(d) != name:
                res.errors.append(
                    f"ED {n}: district {d} is '{names.get(d)}' in the spine, expected '{name}'"
                )

    ed_comp = Composition(defaultdict(dict), "manual (district grouping)", "election-results")
    for gn, d in gn_district.items():
        if d in district_ed:
            ed_comp.members[ed_id(district_ed[d])][gn] = 1.0

    # gig-data (internal)
    pd_ids = [f"EC-{p.ed_number:02d}{p.letter}" for p in reg.pds]
    ed_ids_ec = [f"EC-{n:02d}" for n in sorted(reg.ed_names)]
    refs = snapshot_gig(storage, gig_files(pd_ids, ed_ids_ec))
    gig_gnd = read_tsv(storage, refs["ents/gnd.tsv"])
    gig_pd = read_tsv(storage, refs["ents/pd.tsv"])
    gig_ed = read_tsv(storage, refs["ents/ed.tsv"])
    cw = pd.read_csv(catalog / "geographies" / "codes" / "nuuuwan.csv", dtype=str)
    nu_to_spine = dict(zip(cw["external_code"], cw["geography_id"], strict=False))
    gig_gnd["spine_id"] = [nu_to_spine.get(str(i)) for i in gig_gnd["id"]]
    unmatched_gig = gig_gnd[gig_gnd["spine_id"].isna()]

    pd_comp = Composition(
        defaultdict(dict), "attribute (nuuuwan gig-data pd_id)", "nuuuwan-gig-data"
    )
    sub = gig_gnd[gig_gnd["spine_id"].notna()]
    matched: list[dict[str, str]] = [
        {"spine_id": str(sid), "pd_id": str(p), "ed_id": str(e), "name": str(n)}
        for sid, p, e, n in zip(
            sub["spine_id"], sub["pd_id"], sub["ed_id"], sub["name"], strict=True
        )
    ]
    for r in matched:
        unit = "LK-PD-" + r["pd_id"][3:]
        pd_comp.members[unit][r["spine_id"]] = pd_comp.members[unit].get(r["spine_id"], 0.0) + 1.0

    # ED agreement with nuuuwan's per-GN ed_id
    ours_ed = {gn: ed_id(district_ed[d]) for gn, d in gn_district.items() if d in district_ed}
    ed_disagree = []
    for r in matched:
        theirs = "LK-ED-" + r["ed_id"][3:]
        if ours_ed.get(r["spine_id"]) != theirs:
            ed_disagree.append((r["spine_id"], ours_ed.get(r["spine_id"]), theirs, r["name"]))
    pd_cross = [
        (unit, sorted({ours_ed.get(g) or "" for g in m}))
        for unit, m in pd_comp.members.items()
        if {ours_ed.get(g) for g in m} != {"LK-ED-" + unit[6:8]}
    ]

    # IoU (EPSG:5235)
    versions = gpd.read_parquet(spine_dir / "geography_versions.geoparquet")
    gn_geoms = versions[versions["level"] == 4].set_index("geography_id")["geometry"]
    gn_geoms = gpd.GeoSeries(gn_geoms, crs=versions.crs)
    nu_ed_geom = {
        ed_id(int(i[3:])): read_geojson(storage, refs[f"geo/ed/{i}.json"]) for i in ed_ids_ec
    }
    nu_pd_geom = {"LK-PD-" + i[3:]: read_geojson(storage, refs[f"geo/pd/{i}.json"]) for i in pd_ids}
    ed_iou = iou_table(nu_ed_geom, gn_geoms, ed_comp)
    pd_iou = iou_table(nu_pd_geom, gn_geoms, pd_comp)

    # denominators
    census = _census_gn(census_dirs, all_gns)
    ed_den = _with_adults(denominators(ed_comp, census, DENOMINATORS))
    pd_den = _with_adults(denominators(pd_comp, census, DENOMINATORS))
    for frame in (ed_den, pd_den):
        frame["electors_registered"] = [results.get(str(g)) for g in frame["geography_id"]]
        frame["electors_per_100_adults_20_plus"] = (
            100 * frame["electors_registered"] / frame["population_age_20_plus"]
        ).round(2)
        frame["electors_per_100_adults_15_plus"] = (
            100 * frame["electors_registered"] / frame["population_age_15_plus"]
        ).round(2)

    # ED population from GN sums vs the census build's own district totals (which include GNs the
    # crosswalk could not match to the spine): the gap is the unmatched GNs' population.
    district_pop: dict[str, float] = {}
    for d in census_dirs:
        f = pd.read_parquet(
            d / "observations.parquet",
            columns=["indicator_id", "geography_id", "value", "breakdown"],
        )
        f = f[(f["indicator_id"] == "population_total") & f["breakdown"].isna()]
        district_pop.update(dict(zip(f["geography_id"], f["value"], strict=False)))
    ed_den["population_total_district_tables"] = ed_den["geography_id"].map(
        lambda u: sum(district_pop.get(dd, 0.0) for dd, _ in ED_DISTRICTS[int(u[6:])])
    )
    ed_den["population_gap_unmatched_gns"] = (
        ed_den["population_total_district_tables"] - ed_den["population_total"]
    )

    ed_ws = weight_sums(ed_comp, all_gns)
    pd_ws = weight_sums(pd_comp, all_gns)
    outputs = {
        "ed_denominators.csv": ed_den,
        "ed_iou.csv": ed_iou,
        "pd_denominators_internal.csv": pd_den,
        "pd_iou_internal.csv": pd_iou,
        "ed_nuuuwan_disagreements.csv": pd.DataFrame(
            ed_disagree, columns=["gn", "ours", "nuuuwan", "nuuuwan_name"]
        ),
        "gig_gn_unmatched.csv": unmatched_gig[["id", "name", "pd_id"]],
    }
    for name, frame in outputs.items():
        path = out_dir / name
        frame.to_csv(path, index=False)
        res.outputs.append(path)

    res.qa = _qa(
        reg, gig_pd, gig_ed, ed_comp, pd_comp, ed_ws, pd_ws, ed_iou, pd_iou, ed_den, pd_den,
        ed_disagree, pd_cross, unmatched_gig, all_gns, gig_gnd,
    )  # fmt: skip
    qa = out_dir / "qa.md"
    qa.write_text(res.qa, encoding="utf-8")
    res.outputs.append(qa)
    return res


def _dist(series: pd.Series) -> str:
    s = series.dropna()
    if s.empty:
        return "n/a"
    q = s.quantile([0, 0.05, 0.25, 0.5, 0.75, 1]).round(4).tolist()
    return f"min {q[0]}, p5 {q[1]}, p25 {q[2]}, median {q[3]}, p75 {q[4]}, max {q[5]} (n={len(s)})"


def _qa(reg, gig_pd, gig_ed, ed_comp, pd_comp, ed_ws, pd_ws, ed_iou, pd_iou, ed_den, pd_den,
        ed_disagree, pd_cross, unmatched_gig, all_gns, gig_gnd) -> str:  # fmt: skip
    def top(frame: pd.DataFrame, col: str, n: int = 10) -> list[str]:
        f = frame.dropna(subset=[col]).copy()
        f["dev"] = (f[col] - f[col].median()).abs()
        f = f.sort_values("dev", ascending=False).head(n)
        rows = [
            "| unit | electors | pop 20+ | pop 15+ | electors per 100 aged 20+ |",
            "|---|---|---|---|---|",
        ]
        for r in f.to_dict("records"):
            rows.append(
                f"| {r['geography_id']} | {int(r['electors_registered'])} | "
                f"{int(r['population_age_20_plus'])} | {int(r['population_age_15_plus'])} | {r[col]} |"
            )
        return rows

    lines = [
        "# QA: electoral geography (G05, scheme `electoral`, vintage ec-2024)",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "|---|---|",
        f"| EDs in the Commission's register | {len(reg.ed_names)} |",
        f"| PDs in the Commission's register | {len(reg.pds)} |",
        f"| EDs composed from spine districts | {len(ed_comp.members)} |",
        f"| nuuuwan gig-data PDs / EDs | {len(gig_pd)} / {len(gig_ed)} |",
        f"| nuuuwan gig-data GN rows / matched to the spine via codes/nuuuwan.csv | {len(gig_gnd)} / {len(gig_gnd) - len(unmatched_gig)} |",
        f"| PDs with at least one matched GN (internal) | {sum(bool(m) for m in pd_comp.members.values())} |",
        f"| Spine GNs (COD-AB v03) | {len(all_gns)} |",
        "",
        "## Weight sums per GN (each GN's total weight across the scheme's units)",
        "",
        f"- ED: {dict(sorted(ed_ws.items()))}",
        f"- PD (internal, gig-data): {dict(sorted(pd_ws.items()))}",
        "",
        "## ED check against nuuuwan's per-GN `ed_id`",
        "",
        f"{len(ed_disagree)} matched GNs are in a different ED in nuuuwan's list than our district grouping gives.",
        "",
        f"PDs whose matched GNs fall in more than one ED, or in another ED than the PD's own: {len(pd_cross)}"
        + (f" ({', '.join(u for u, _ in pd_cross[:10])})" if pd_cross else ""),
        "",
        "## ED population: GN sums vs census district totals",
        "",
        f"Sum over EDs of GN-summed population: {int(ed_den['population_total'].sum()):,}; of district totals: "
        f"{int(ed_den['population_total_district_tables'].sum()):,}; gap (GNs not matched to the spine): "
        f"{int(ed_den['population_gap_unmatched_gns'].sum()):,}. EDs with a gap: "
        + ", ".join(
            f"{r.geography_id} {int(r.population_gap_unmatched_gns):,}"
            for r in ed_den.itertuples()
            if r.population_gap_unmatched_gns
        )
        + ".",
        "",
        "## IoU: unit geometry vs union of its member GNs (EPSG:5235)",
        "",
        f"- ED (nuuuwan ED shape vs union of COD-AB GNs of the district grouping): {_dist(ed_iou['iou'])}",
        f"- PD (internal; nuuuwan PD shape vs union of COD-AB GNs that nuuuwan assigns to it): {_dist(pd_iou['iou'])}",
        f"- PDs with IoU < 0.9: {int((pd_iou['iou'] < 0.9).sum())}; < 0.8: {int((pd_iou['iou'] < 0.8).sum())}",
        "",
        "## Denominators against registered electors (2024 presidential result sheets)",
        "",
        "Registered electors are people aged 18+ on the 2024 register; Census 2024 (19 Dec 2024) gives five-year age bands, so 18+ is bracketed by 15+ and 20+. "
        "ED electors include postal voters.",
        "",
        f"- ED electors per 100 aged 20+: {_dist(ed_den['electors_per_100_adults_20_plus'])}",
        f"- ED electors per 100 aged 15+: {_dist(ed_den['electors_per_100_adults_15_plus'])}",
        f"- PD electors per 100 aged 20+ (internal): {_dist(pd_den['electors_per_100_adults_20_plus'])}",
        "",
        "### Top 10 EDs furthest from the median (electors per 100 aged 20+)",
        "",
        *top(ed_den, "electors_per_100_adults_20_plus"),
        "",
        "### Top 10 PDs furthest from the median (internal composition)",
        "",
        *top(pd_den, "electors_per_100_adults_20_plus"),
        "",
    ]
    return "\n".join(lines) + "\n"
