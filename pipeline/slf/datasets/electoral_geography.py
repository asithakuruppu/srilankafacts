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
    # nuuuwan format: list of polygons, each a list of rings, each a list of [lng, lat]
    return shape({"type": "MultiPolygon", "coordinates": data})


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
        a = gpd.GeoSeries([geom], crs="EPSG:4326").to_crs(AREA_CRS).iloc[0]
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
    """Σ(weight × GN value) per unit and indicator; counts only (rates are recomputed later)."""
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
                    sum(members[g] * float(values.at[g, ind]) for g in ids if pd.notna(values.at[g, ind]))
                )
        rows.append(row)
    return pd.DataFrame(rows)
