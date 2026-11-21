"""Code crosswalks and indicators for HeiGIT accessibility and DesInventar disaster records.

Neither source uses the spine's p-codes for these tables, so each gets a reviewed crosswalk
(rule 5) before any value is joined:

- HeiGIT accessibility tables carry ISO 3166-2 codes (``LK-1``, ``LK-52``) and names
  ("Ampara District"). The ISO number equals the p-code suffix for most districts but not
  for the four northern ones (ISO: Kilinochchi 42, Mannar 43, Vavuniya 44, Mullaitivu 45;
  p-codes LK45, LK42, LK43, LK44), so the code is never used on its own. A unit matches when
  its name equals one spine name at the right level and, for districts, the parent province
  (taken from the source's own province rows) agrees. The ISO/p-code agreement is recorded.
- DesInventar records carry DesInventar's own ``lkaPPP`` (province) and ``lkaPPPDDD``
  (district) codes. The boundary files shipped with the data give each code's name and its
  parent, so names are matched within the matched parent. DS division codes exist in the
  shapefile but the event table has no DS column, so that level is not mapped here.

Unmatched or ambiguous units are never forced: they go to the QA report (rule 6).
"""

# pandas type stubs can't follow these DataFrame operations; behaviour is covered by tests.
# pyright: reportArgumentType=false, reportCallIssue=false, reportAttributeAccessIssue=false
# pyright: reportOperatorIssue=false, reportReturnType=false, reportGeneralTypeIssues=false

from __future__ import annotations

import csv
import json
import re
import unicodedata
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

VINTAGE = "cod-ab-v03"
DATE_RE = re.compile(r"^(\d{1,2})/(\d{1,2})/(\d{4})$")

CODE_COLUMNS = [
    "geography_id",
    "vintage",
    "code_system",
    "external_code",
    "external_name",
    "match_method",
    "confidence",
    "notes",
]


def norm(name: str) -> str:
    """Lower-case ASCII letters only, with generic words dropped ("Ampara District")."""
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    text = re.sub(r"\b(district|province|ds|division)\b", " ", text)
    return re.sub(r"[^a-z]", "", text)


@dataclass
class Place:
    geography_id: str
    name: str
    parent_id: str


@dataclass
class Crosswalk:
    code_system: str
    rows: list[dict[str, Any]] = field(default_factory=list)
    unmatched: list[str] = field(default_factory=list)
    ambiguous: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    #: units with a candidate that is not safe to accept (rule 5): never mapped, always listed
    review: list[str] = field(default_factory=list)

    def by_code(self) -> dict[str, str]:
        return {r["external_code"]: r["geography_id"] for r in self.rows}


def spine_places(spine_dir: Path) -> dict[int, list[Place]]:
    g = pd.read_parquet(spine_dir / "geographies.parquet")
    out: dict[int, list[Place]] = {}
    for r in g[g["level"].isin([1, 2, 3])].to_dict("records"):
        out.setdefault(int(r["level"]), []).append(
            Place(str(r["geography_id"]), str(r["name_en"]), str(r["parent_id"]))
        )
    return out


def _match(
    name: str, candidates: list[Place], parent: str | None
) -> tuple[Place | None, str | None]:
    """Unique normalised-name match among candidates (within ``parent`` when given)."""
    pool = [p for p in candidates if parent is None or p.parent_id == parent]
    hits = [p for p in pool if norm(p.name) == norm(name)]
    if len(hits) == 1:
        return hits[0], None
    if not hits:
        return None, "no spine unit with this name" + (f" under {parent}" if parent else "")
    return None, "more than one spine unit: " + ", ".join(h.geography_id for h in hits)


def _add(
    cw: Crosswalk,
    place: Place,
    code: str,
    name: str,
    method: str,
    confidence: float,
    note: str,
) -> None:
    cw.rows.append(
        {
            "geography_id": place.geography_id,
            "vintage": VINTAGE,
            "code_system": cw.code_system,
            "external_code": code,
            "external_name": name,
            "match_method": method,
            "confidence": confidence,
            "notes": note,
        }
    )


# --- raw access ------------------------------------------------------------------------------


def latest(raw: Path, source: str, dataset: str, filename: str) -> tuple[Path, dict[str, Any]]:
    files = sorted((raw / source / dataset).glob(f"*/{filename}"))
    if not files:
        raise FileNotFoundError(f"{source}/{dataset}/*/{filename}")
    meta = json.loads(files[-1].with_name(files[-1].name + ".meta.json").read_text())
    return files[-1], meta


# --- HeiGIT ----------------------------------------------------------------------------------


def heigit_units(raw: Path) -> pd.DataFrame:
    path, _ = latest(raw, "heigit", "heigit-accessibility", "LKA_hospitals_access_long.csv")
    d = pd.read_csv(path, dtype=str)
    return d[["name", "iso", "id", "admin_level"]].drop_duplicates().reset_index(drop=True)


def crosswalk_heigit(raw: Path, spine_dir: Path) -> Crosswalk:
    cw = Crosswalk("heigit-iso")
    places = spine_places(spine_dir)
    units = heigit_units(raw)
    province_of: dict[str, str] = {}
    for u in units[units["admin_level"] == "ADM1"].to_dict("records"):
        place, why = _match(u["name"], places[1], "LK")
        if place is None:
            cw.unmatched.append(f"{u['iso']} {u['name']}: {why}")
            continue
        suffix = u["iso"].removeprefix("LK-")
        agree = suffix == place.geography_id.removeprefix("LK")
        _add(
            cw,
            place,
            u["iso"],
            u["name"],
            "name_and_parent",
            1.0,
            f"name matches a unique province; ISO number {'agrees' if agree else 'DISAGREES'}"
            " with the p-code suffix",
        )
        province_of[u["iso"]] = place.geography_id
    # HeiGIT states no parent on district rows; the ISO district number's first digit is
    # the ISO province, which is the source's own hierarchy (ISO 3166-2:LK).
    for u in units[units["admin_level"] == "ADM2"].to_dict("records"):
        parent_iso = "LK-" + u["iso"].removeprefix("LK-")[:1]
        parent = province_of.get(parent_iso)
        if parent is None:
            cw.unmatched.append(f"{u['iso']} {u['name']}: its ISO province {parent_iso} unmatched")
            continue
        place, why = _match(u["name"], places[2], parent)
        if place is None:
            cw.unmatched.append(f"{u['iso']} {u['name']}: {why}")
            continue
        suffix = u["iso"].removeprefix("LK-")
        agree = suffix == place.geography_id.removeprefix("LK")
        note = "name unique within the province whose ISO number is the district's first digit"
        note += (
            "; ISO number agrees with the p-code suffix"
            if agree
            else f"; ISO number DISAGREES with the p-code suffix (ISO {suffix}, spine "
            f"{place.geography_id.removeprefix('LK')}): the ISO code must not be used as a p-code"
        )
        _add(cw, place, u["iso"], u["name"], "name_and_parent", 1.0, note)
    cw.rows.append(
        {
            "geography_id": "LK",
            "vintage": VINTAGE,
            "code_system": cw.code_system,
            "external_code": "LKA",
            "external_name": "Sri Lanka",
            "match_method": "exact_code",
            "confidence": 1.0,
            "notes": "ISO 3166-1 alpha-3 for the country",
        }
    )
    return cw


# --- DesInventar -----------------------------------------------------------------------------


def desinventar_units(raw: Path, work: Path) -> dict[str, pd.DataFrame]:
    """Province, district and DS tables from the shapefile attribute tables (no geometry used)."""
    import pyogrio

    zpath, _ = latest(raw, "undrr-desinventar", "desinventar-sri-lanka", "srilanka.zip")
    work.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zpath) as z:
        z.extractall(work)
    out = {}
    for key, stem in (("province", "provi"), ("district", "ditric"), ("ds", "dsdivi")):
        out[key] = pyogrio.read_dataframe(work / f"{stem}.shp", read_geometry=False)
    return out


# Spelling variants confirmed by hand. Each is recorded as a `manual` match, never promoted to a
# name join: the variant must be the only unmatched district under an already matched parent.
REVIEWED_ALIASES: dict[tuple[str, str], tuple[str, str]] = {
    ("lka008002", "Moneragala"): (
        "LK82",
        "variant spelling of Monaragala; the only DesInventar district under Uva (lka008) not "
        "matched by name, and Monaragala is the only spine district under LK8 left unmatched "
        "(Badulla matched by name); lead review pending",
    ),
}


def crosswalk_desinventar(
    raw: Path, spine_dir: Path, work: Path, catalog: Path | None = None
) -> Crosswalk:
    cw = Crosswalk("desinventar")
    places = spine_places(spine_dir)
    units = desinventar_units(raw, work)
    province_of: dict[str, str] = {}
    for u in units["province"].to_dict("records"):
        place, why = _match(u["PROVINCE_N"], places[1], "LK")
        if place is None:
            cw.unmatched.append(f"{u['pro_code']} {u['PROVINCE_N']}: {why}")
            continue
        _add(
            cw,
            place,
            u["pro_code"],
            u["PROVINCE_N"],
            "name_and_parent",
            1.0,
            "name equals one spine province (parent LK); name from the province shapefile",
        )
        province_of[u["pro_code"]] = place.geography_id
    for u in units["district"].to_dict("records"):
        parent = province_of.get(u["pro_code"])
        if parent is None:
            cw.unmatched.append(
                f"{u['dis_code']} {u['DISTRICT_N']}: province {u['pro_code']} unmatched"
            )
            continue
        place, why = _match(u["DISTRICT_N"], places[2], parent)
        alias = REVIEWED_ALIASES.get((u["dis_code"], u["DISTRICT_N"]))
        if place is None and alias is not None:
            taken = {r["geography_id"] for r in cw.rows}
            candidate = next((p for p in places[2] if p.geography_id == alias[0]), None)
            if (
                candidate is not None
                and candidate.parent_id == parent
                and candidate.geography_id not in taken
            ):
                _add(cw, candidate, u["dis_code"], u["DISTRICT_N"], "manual", 0.95, alias[1])
                continue
        if place is None:
            cw.unmatched.append(f"{u['dis_code']} {u['DISTRICT_N']}: {why}")
            continue
        _add(
            cw,
            place,
            u["dis_code"],
            u["DISTRICT_N"],
            "name_and_parent",
            1.0,
            f"name equals one spine district under {parent}; the shapefile's province "
            f"{u['pro_code']} ({u['PROVINCE_N']}) matches that parent",
        )
    ds = units["ds"]
    if catalog is None:
        cw.notes.append(
            f"DS divisions: {len(ds)} in the shapefile; not mapped (no catalogue folder given)."
        )
        return cw
    _map_ds(cw, places[3], ds, {r["external_code"]: r["geography_id"] for r in cw.rows}, catalog)
    return cw


DS_ACCEPT = 0.80  # code agrees and names are this similar (as in the DCS crosswalk)


def _names(name: str) -> list[str]:
    """Normalised candidate names: the whole label, the part before "(" and the bracketed part."""
    out = [norm(name)]
    m = re.match(r"^(.*?)\((.*)\)\s*$", name)
    if m:
        out += [norm(m.group(1)), norm(m.group(2))]
    return [n for n in dict.fromkeys(out) if n]


def _sim(a: str, b: str) -> float:
    from difflib import SequenceMatcher

    return max(
        (SequenceMatcher(None, x, y).ratio() for x in _names(a) for y in _names(b)), default=0.0
    )


def _map_ds(
    cw: Crosswalk,
    spine_ds: list[Place],
    ds: pd.DataFrame,
    district_of: dict[str, str],
    catalog: Path,
) -> None:
    """DesInventar DS divisions (2015 shapefile) to spine DS divisions.

    1. The shapefile's DCS-style DS code equals a DCS code already mapped in
       ``codes/dcs-census2024.csv`` and the names are alike (>= 0.80), and the spine unit sits
       in the district matched from the DesInventar district: ``exact_code``.
    2. Otherwise a name (whole, before or inside the brackets) equal to exactly one spine DS of
       the matched district: ``name_and_parent``.
    3. A match that lands on a unit created by a 2012 to 2024 split is refused: the old unit's
       events cannot be assigned to one part. Anything else goes to the review list.
    """
    dcs = pd.read_csv(catalog / "geographies" / "codes" / "dcs-census2024.csv", dtype=str)
    dcs = dcs[dcs["external_code"].str.len() == 4]
    by_dcs = {r["external_code"]: r["geography_id"] for r in dcs.to_dict("records")}
    succ = pd.read_csv(
        catalog / "geographies" / "relations" / "succession_ds_2012-2024.csv", dtype=str
    )
    split_into = set(succ[succ["relation"] == "succeeded_by"]["related_id"])
    place_of = {p.geography_id: p for p in spine_ds}
    taken: dict[str, str] = {}
    for u in ds.to_dict("records"):
        label = f"{u['ds_code']} {u['DSD_N'].strip()} ({u['DISTRICT_N']})"
        parent = district_of.get(u["dis_code"])
        if parent is None:
            cw.unmatched.append(f"{label}: its district {u['dis_code']} is unmatched")
            continue
        code = "" if pd.isna(u["DSDCODE4"]) else str(int(float(u["DSDCODE4"])))
        target: Place | None = None
        method, conf, note = "", 0.0, ""
        gid = by_dcs.get(code)
        if gid in place_of and place_of[gid].parent_id == parent:
            sim = _sim(u["DSD_N"], place_of[gid].name)
            if sim >= DS_ACCEPT:
                target, method = place_of[gid], "exact_code"
                conf = 1.0 if sim >= 0.999 else 0.9
                note = f"DS code {code} equals DCS code of {gid}; name similarity {sim:.2f}"
            else:
                cw.review.append(
                    f"{label}: DCS code {code} is {gid} '{place_of[gid].name}' but the names "
                    f"differ (similarity {sim:.2f}); renamed or reassigned code, not mapped"
                )
                continue
        else:
            hits = [
                p
                for p in spine_ds
                if p.parent_id == parent and norm(p.name) in set(_names(u["DSD_N"]))
            ]
            if len(hits) == 1:
                target, method, conf = hits[0], "name_and_parent", 0.9
                note = f"name equals the only spine DS with that name under {parent}"
            else:
                why = "no DS code match and " + (
                    "no same-name DS in the district" if not hits else "several same-name DS"
                )
                cw.unmatched.append(f"{label}: {why}")
                continue
        if target.geography_id in split_into:
            cw.review.append(
                f"{label}: lands on {target.geography_id} '{target.name}', created by a 2012 to "
                "2024 split; the old unit's events cannot be assigned to one part, not mapped"
            )
            continue
        if target.geography_id in taken:
            cw.review.append(
                f"{label}: {target.geography_id} is already the match of "
                f"{taken[target.geography_id]}; two DesInventar DS for one spine DS, not mapped"
            )
            continue
        taken[target.geography_id] = u["ds_code"]
        _add(cw, target, u["ds_code"], u["DSD_N"].strip(), method, conf, note)
    cw.notes.append(
        f"DS divisions: {len(ds)} in DesInventar's 2015 shapefile; "
        f"{sum(1 for r in cw.rows if len(r['geography_id']) == 6)} matched, "
        f"{len(cw.review)} to review, "
        f"{sum(1 for u in cw.unmatched if u.startswith('lka'))} unmatched (listed below)."
    )


def write_codes(cw: Crosswalk, catalog: Path) -> Path:
    path = catalog / "geographies" / "codes" / f"{cw.code_system}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CODE_COLUMNS, lineterminator="\n")
        w.writeheader()
        for r in sorted(cw.rows, key=lambda r: r["external_code"]):
            w.writerow(r)
    return path


# --- HeiGIT indicators -----------------------------------------------------------------------


@dataclass(frozen=True)
class Spec:
    id: str
    name: str
    dataset: str
    unit: str
    decimals: int
    measure_type: str
    definition: str
    data_nature: str
    floor: str
    higher_is: str = "neutral"
    group: str = "Access"


ACCESS_BANDS = {
    # id suffix: (label, range_type, range)
    "hospital_30min": ("hospital", "TIME", 1800),
    "hospital_60min": ("hospital", "TIME", 3600),
    "hospital_120min": ("hospital", "TIME", 7200),
    "primary_care_30min": ("primary_healthcare", "TIME", 1800),
    "primary_care_60min": ("primary_healthcare", "TIME", 3600),
    "school_5km": ("education", "DISTANCE", 5000),
    "school_10km": ("education", "DISTANCE", 10000),
}
_WORD = {
    "hospital": "a hospital",
    "primary_healthcare": "primary healthcare",
    "education": "a school",
}
_DATASET = "heigit-accessibility"
_FLOOR = "grid-100m (WorldPop population, OpenStreetMap roads and facilities)"

SPECS: list[Spec] = []
for _key, (_cat, _kind, _rng) in ACCESS_BANDS.items():
    _how = f"{_rng // 60} minutes' travel" if _kind == "TIME" else f"{_rng // 1000} km"
    SPECS.append(
        Spec(
            f"access_{_key}",
            f"Population within {_how} of {_WORD[_cat]}",
            _DATASET,
            "percent",
            1,
            "share",
            f"Share of the district's total population living within {_how} of {_WORD[_cat]}, "
            "as modelled by HeiGIT from OpenStreetMap roads and facilities and a modelled "
            "population grid. Cumulative: includes people nearer than the stated limit.",
            "modelled_estimate",
            _FLOOR,
            "higher_is_better",
        )
    )


def ingest_heigit_access(
    raw: Path, xwalk: dict[str, str], unmatched: list[str]
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    files = {
        "hospitals": "LKA_hospitals_access_long.csv",
        "primary_healthcare": "LKA_primary_healthcare_access_long.csv",
        "education": "LKA_education_access_long.csv",
    }
    wanted = {(cat, kind, rng): key for key, (cat, kind, rng) in ACCESS_BANDS.items()}
    for category, filename in files.items():
        path, meta = latest(raw, "heigit", "heigit-accessibility", filename)
        table = pd.read_csv(path, dtype={"iso": str})
        for index, rec in enumerate(table.to_dict("records")):
            if rec["population_type"] != "total":
                continue
            cat = "hospital" if category == "hospitals" else category
            key = wanted.get((cat, rec["range_type"], int(rec["range"])))
            if key is None:
                continue
            gid = xwalk.get(rec["iso"])
            if gid is None:
                unmatched.append(f"heigit access: {rec['iso']} {rec['name']}")
                continue
            rows.append(
                _row(
                    f"access_{key}",
                    gid,
                    float(rec["population_share"]),
                    meta,
                    f"{path.name}, row {index + 2}, column 'population_share' "
                    f"(population_type=total, {rec['range_type']}={rec['range']})",
                    "percent",
                    "area_mean",
                    "modelled_estimate",
                    _FLOOR,
                    _DATASET,
                    "2026",
                    "2026-01-01",
                    "2026-12-31",
                    "interval_mean",
                )
            )
    return rows


# --- DesInventar indicators ------------------------------------------------------------------

HAZARDS: dict[str, tuple[str, set[str]]] = {
    "flood": ("Floods", {"FLOOD", "URBAN FLOOD", "FLASH FLOOD", "CYCLONE & FLOOD"}),
    "landslide": (
        "Landslides and slips",
        {"LANDSLIDE", "EARTH SLIP", "CUTTING FAILURE", "ROCK FALL"},
    ),
    "drought": ("Droughts", {"DROUGHT"}),
    "wind": ("Strong winds, gales and cyclones", {"STRONG WIND", "GALE", "CYCLONE", "TORNADO"}),
}
# Everything that is not an epidemic or an animal attack counts towards the disaster total.
NON_DISASTER = {"EPIDEMIC", "ANIMAL ATTACK", "SNAKE BITE", "PLAGUE"}

# CC BY-SA datasets: a public bundle needs a licence statement that carries share-alike.
SHARE_ALIKE_DATASETS = {"heigit-accessibility", "heigit-risk-indicators"}

DI_DATASET = "desinventar-sri-lanka"
DI_FLOOR = "district (DesInventar record location; GN named in about a quarter of records)"
DI_DS_FLOOR = "DS division (DesInventar 2015 DS file; matched by code and name, no split)"


def _di_spec(id_: str, name: str, definition: str) -> Spec:
    return Spec(
        id_,
        name,
        DI_DATASET,
        "records",
        0,
        "count",
        definition,
        "administrative_record",
        DI_FLOOR,
        group="Disaster records (DesInventar)",
    )


_COMMON = (
    " One record is one reported event at one place and date in the DMC/DesInventar database, "
    "not one distinct disaster; reporting effort varies by year, so a missing year is not a "
    "zero."
)
SPECS += [
    _di_spec(
        f"di_{key}_records",
        f"{label}: DesInventar records per year",
        f"Records of {label.lower()} in the DesInventar database for Sri Lanka, "
        "by district and year of the event date." + _COMMON,
    )
    for key, (label, _) in HAZARDS.items()
]
SPECS.append(
    _di_spec(
        "di_disaster_records",
        "All disaster types: DesInventar records per year",
        "All DesInventar records except epidemics, plague, animal attacks and snake bites, "
        "by district and year of the event date." + _COMMON,
    )
)
SPEC_BY_ID = {s.id: s for s in SPECS}


def _row(
    indicator: str,
    gid: str,
    value: float,
    meta: dict[str, Any],
    locator: str,
    unit: str,
    support_type: str,
    data_nature: str,
    floor: str,
    dataset: str,
    period: str,
    start: str,
    end: str,
    time_support: str,
) -> dict[str, Any]:
    return {
        "claim_id": f"{dataset}:{gid}:{indicator}:{period}",
        "indicator_id": indicator,
        "geography_id": gid,
        "period": period,
        "time_start": start,
        "time_end": end,
        "value": value,
        "value_status": "normal",
        "unit": unit,
        "information_footprint_ref": floor,
        "data_nature": data_nature,
        "verification": "machine_extracted",
        "dataset_id": dataset,
        "snapshot_sha256": meta["sha256"],
        "source_url": meta.get("url"),
        "source_locator": locator,
        "breakdown": None,
        "support_type": support_type,
        "time_support": time_support,
        "boundary_vintage": VINTAGE,
    }


def read_events(raw: Path) -> tuple[pd.DataFrame, Path, dict[str, Any]]:
    path, meta = latest(raw, "undrr-desinventar", "desinventar-sri-lanka", "di_report-srilanka.xls")
    d = pd.read_csv(path, sep="\t", dtype=str, keep_default_na=False, encoding="utf-8")
    d = d.loc[:, ~d.columns.str.startswith("Unnamed")]
    d["Event"] = d["Event"].str.strip().str.upper()
    d["_line"] = range(2, len(d) + 2)
    return d, path, meta


def event_year(date: str) -> int | None:
    m = DATE_RE.match(date.strip())
    if m is None:
        return None
    day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None
    return year


@dataclass
class EventQA:
    total: int = 0
    epidemic_etc: int = 0
    no_district: int = 0
    unmatched_code: dict[str, int] = field(default_factory=dict)
    bad_date: int = 0
    bad_date_examples: list[str] = field(default_factory=list)
    used: int = 0
    by_event: dict[str, int] = field(default_factory=dict)
    year_range: tuple[int, int] | None = None
    province_mismatch: int = 0
    ds_with_code: int = 0
    ds_mapped: int = 0
    ds_unmapped_code: dict[str, int] = field(default_factory=dict)
    ds_conflict: int = 0


def ingest_desinventar(
    raw: Path, xwalk: dict[str, str]
) -> tuple[list[dict[str, Any]], EventQA, pd.DataFrame]:
    d, path, meta = read_events(raw)
    qa = EventQA(total=len(d))
    d["year"] = d["Date (YMD)"].map(event_year)
    d["gid"] = d["Code District"].map(xwalk)
    d["is_epi"] = d["Event"].isin(NON_DISASTER)
    qa.epidemic_etc = int(d["is_epi"].sum())
    qa.no_district = int((d["Code District"] == "").sum())
    unknown = d[(d["Code District"] != "") & d["gid"].isna()]
    qa.unmatched_code = unknown["Code District"].value_counts().to_dict()
    # Hierarchy check: the record's province column must be the district code's own province.
    qa.province_mismatch = int(
        ((d["Code District"] != "") & (d["Code District"].str[:6] != d["Code Region"])).sum()
    )
    # A record whose own province column contradicts its district code is not counted.
    conflict = (d["Code District"] != "") & (d["Code District"].str[:6] != d["Code Region"])
    ok = d[d["gid"].notna() & ~conflict]
    bad = ok[ok["year"].isna()]
    qa.bad_date = len(bad)
    qa.bad_date_examples = sorted(set(bad["Date (YMD)"]))[:12]
    use = ok[ok["year"].notna()].copy()
    use["year"] = use["year"].astype(int)
    qa.used = len(use)
    qa.by_event = use["Event"].value_counts().to_dict()
    if len(use):
        qa.year_range = (int(use["year"].min()), int(use["year"].max()))
    # DS division ("Code Commune"): used only when it sits under the record's own district.
    has_ds = use["Code Commune"] != ""
    qa.ds_with_code = int(has_ds.sum())
    ds_conflict = has_ds & (use["Code Commune"].str[:9] != use["Code District"])
    qa.ds_conflict = int(ds_conflict.sum())
    use["gid_ds"] = use["Code Commune"].map(xwalk).where(has_ds & ~ds_conflict)
    qa.ds_mapped = int(use["gid_ds"].notna().sum())
    lost = use[has_ds & ~ds_conflict & use["gid_ds"].isna()]
    qa.ds_unmapped_code = lost["Code Commune"].value_counts().to_dict()
    rows: list[dict[str, Any]] = []

    def emit(indicator: str, frame: pd.DataFrame, column: str = "gid") -> None:
        ds = column == "gid_ds"
        code_name = "Code Commune (DS division)" if ds else "Code District"
        for (gid, year), g in frame[frame[column].notna()].groupby([column, "year"]):
            lines = g["_line"].tolist()
            rows.append(
                _row(
                    indicator,
                    str(gid),
                    float(len(g)),
                    meta,
                    f"{path.name}: count of {len(g)} record(s) with {code_name} mapped to "
                    f"{gid} and event year {year} (file lines {lines[0]} to {lines[-1]}"
                    f"{', not contiguous' if len(lines) != lines[-1] - lines[0] + 1 else ''}); "
                    "event types "
                    + (
                        "; ".join(sorted(set(g["Event"])))
                        if len(set(g["Event"])) <= 6
                        else f"{len(set(g['Event']))} types"
                    ),
                    "records",
                    "area_total",
                    "administrative_record",
                    DI_DS_FLOOR if ds else DI_FLOOR,
                    DI_DATASET,
                    str(int(year)),
                    f"{int(year)}-01-01",
                    f"{int(year)}-12-31",
                    "interval_total",
                )
            )

    for key, (_, types) in HAZARDS.items():
        emit(f"di_{key}_records", use[use["Event"].isin(types)])
        emit(f"di_{key}_records", use[use["Event"].isin(types)], "gid_ds")
    emit("di_disaster_records", use[~use["is_epi"]])
    emit("di_disaster_records", use[~use["is_epi"]], "gid_ds")
    return rows, qa, d


# --- HeiGIT risk-indicator tables ---------------------------------------------------------------
# Provenance as stated in HeiGIT's HDX description (read 2026-11-21 🟡, not independently
# verified): demographics WorldPop, rural share GHSL, facilities OpenStreetMap, flood hazard JRC
# (30 cm depth, return periods 10, 50, 100 and 500 years), evacuation times least-cost paths
# on a motorised friction surface. Every group below is checked in `hazard_checks.py`.

RISK_DATASET = "heigit-risk-indicators"
RISK_FLOOR = "grid-100m (HeiGIT GAIA pipeline: WorldPop, GHSL, OSM, JRC hazard maps)"
RETURN_PERIODS = (10, 50, 100, 500)


def _risk_spec(id_: str, name: str, unit: str, decimals: int, measure: str, text: str, group: str):
    return Spec(
        id_,
        name,
        RISK_DATASET,
        unit,
        decimals,
        measure,
        text,
        "modelled_estimate",
        RISK_FLOOR,
        group=group,
    )


_POP = (
    "Population, modelled on a grid by WorldPop and summed to the district by HeiGIT. "
    "Not the census: against Census 2024 the district totals differ by -21% to +42% "
    "(checks report); use the census for population. "
)
RISK_SPECS: list[Spec] = [
    _risk_spec(
        f"heigit_{key}",
        f"{label} (WorldPop, via HeiGIT)",
        "persons",
        0,
        "count",
        _POP + f"{label}. A modelled count, not the census figure.",
        "Population (modelled)",
    )
    for key, label in [
        ("pop_total", "Total population"),
        ("pop_female", "Female population"),
        ("pop_under5", "Children under 5"),
        ("pop_under15", "Population under 15"),
        ("pop_65plus", "Population aged 65 and over"),
    ]
]
RISK_SPECS += [
    _risk_spec(
        "heigit_rural_share",
        "Share of population in rural areas (GHSL, via HeiGIT)",
        "percent",
        1,
        "share",
        "Share of the district's population living outside urban extents in the Global Human "
        "Settlement Layer.",
        "Population (modelled)",
    )
]
RISK_SPECS += [
    _risk_spec(
        f"osm_{key}_count",
        f"Mapped {label} in OpenStreetMap",
        "facilities",
        0,
        "count",
        f"Number of {label} mapped in OpenStreetMap inside the district at HeiGIT's extraction "
        "date (2026). A count of mapped features: unmapped facilities are missing, and the "
        "definition of the category is OSM's.",
        "Facilities (OpenStreetMap)",
    )
    for key, label in [
        ("hospitals", "hospitals"),
        ("primary_care", "primary health care facilities"),
    ]
]
for _rp in RETURN_PERIODS:
    RISK_SPECS += [
        _risk_spec(
            f"evac_minutes_mean_rp{_rp}",
            f"Evacuation time from 1-in-{_rp}-year flooded areas, mean",
            "minutes",
            1,
            "mean",
            "Mean least-cost travel time on a motorised friction surface from flooded cells "
            f"(depth over 30 cm, {_rp}-year return period, JRC) to the nearest safe zone.",
            "Flood evacuation (HeiGIT, JRC)",
        ),
        _risk_spec(
            f"evac_minutes_median_rp{_rp}",
            f"Evacuation time from 1-in-{_rp}-year flooded areas, median",
            "minutes",
            1,
            "median",
            "Median of the same travel times.",
            "Flood evacuation (HeiGIT, JRC)",
        ),
        _risk_spec(
            f"flood_rp{_rp}_crops_km2",
            f"Cropland flooded over 30 cm, 1-in-{_rp}-year event",
            "km2",
            1,
            "count",
            f"Cropland area under more than 30 cm of water in the {_rp}-year return-period "
            "flood hazard map (JRC), by district.",
            "Flood exposure (HeiGIT, JRC)",
        ),
        _risk_spec(
            f"flood_rp{_rp}_crops_share",
            f"Share of cropland flooded over 30 cm, 1-in-{_rp}-year event",
            "percent",
            1,
            "share",
            "Flooded cropland as a share of the district's cropland.",
            "Flood exposure (HeiGIT, JRC)",
        ),
        *[
            _risk_spec(
                f"flood_rp{_rp}_{key}",
                f"{label} exposed to over 30 cm of flooding, 1-in-{_rp}-year event",
                unit,
                0,
                "count",
                f"{label} located where the {_rp}-year flood hazard map (JRC) shows more than "
                "30 cm of water. Population is WorldPop modelled; facilities are OpenStreetMap "
                "features.",
                "Flood exposure (HeiGIT, JRC)",
            )
            for key, label, unit in [
                ("pop_female", "Women and girls", "persons"),
                ("pop_under5", "Children under 5", "persons"),
                ("pop_65plus", "People aged 65 and over", "persons"),
                ("hospitals", "Hospitals", "facilities"),
                ("primary_care", "Primary health care facilities", "facilities"),
            ]
        ],
    ]
SPECS += RISK_SPECS

# (indicator id, file, column, period footprint)
_RISK_COLUMNS: list[tuple[str, str, str]] = [
    ("heigit_pop_total", "LKA_ADM2_demographics.csv", "total_pop"),
    ("heigit_pop_female", "LKA_ADM2_demographics.csv", "female_pop"),
    ("heigit_pop_under5", "LKA_ADM2_demographics.csv", "children_u5"),
    ("heigit_pop_under15", "LKA_ADM2_demographics.csv", "pop_u15"),
    ("heigit_pop_65plus", "LKA_ADM2_demographics.csv", "elderly"),
    ("heigit_rural_share", "LKA_ADM2_rural_population.csv", "rural_pop_perc"),
    ("osm_hospitals_count", "LKA_ADM2_facilities.csv", "hospitals_count"),
    ("osm_primary_care_count", "LKA_ADM2_facilities.csv", "primary_healthcare_count"),
]
for _rp in RETURN_PERIODS:
    _RISK_COLUMNS += [
        (
            f"evac_minutes_mean_rp{_rp}",
            "LKA_ADM2_evacuability.csv",
            f"RP{_rp}_evac_time_minutes_mean",
        ),
        (
            f"evac_minutes_median_rp{_rp}",
            "LKA_ADM2_evacuability.csv",
            f"RP{_rp}_evac_time_minutes_median",
        ),
        (f"flood_rp{_rp}_crops_km2", "LKA_ADM2_flood_exposure.csv", f"RP{_rp}_crops_30cm_km2"),
        (
            f"flood_rp{_rp}_crops_share",
            "LKA_ADM2_flood_exposure.csv",
            f"RP{_rp}_crops_30cm_croppct",
        ),
        (f"flood_rp{_rp}_pop_female", "LKA_ADM2_flood_exposure.csv", f"RP{_rp}_female_pop_30cm"),
        (f"flood_rp{_rp}_pop_under5", "LKA_ADM2_flood_exposure.csv", f"RP{_rp}_children_u5_30cm"),
        (f"flood_rp{_rp}_pop_65plus", "LKA_ADM2_flood_exposure.csv", f"RP{_rp}_elderly_30cm"),
        (
            f"flood_rp{_rp}_hospitals",
            "LKA_ADM2_flood_exposure.csv",
            f"RP{_rp}_hospitals_30cm_count",
        ),
        (
            f"flood_rp{_rp}_primary_care",
            "LKA_ADM2_flood_exposure.csv",
            f"RP{_rp}_primary_healthcare_30cm_count",
        ),
    ]
SPEC_BY_ID = {sp.id: sp for sp in SPECS}


def ingest_risk(raw: Path, valid: set[str], unmatched: list[str]) -> list[dict[str, Any]]:
    """District values copied cell by cell from the p-coded tables (no arithmetic)."""
    rows: list[dict[str, Any]] = []
    tables: dict[str, tuple[Path, dict[str, Any], pd.DataFrame]] = {}
    for indicator, filename, column in _RISK_COLUMNS:
        if filename not in tables:
            path, meta = latest(raw, "heigit", RISK_DATASET, filename)
            tables[filename] = (path, meta, pd.read_csv(path, dtype={"ADM2_PCODE": str}))
        path, meta, table = tables[filename]
        spec = SPEC_BY_ID[indicator]
        for index, rec in enumerate(table.to_dict("records")):
            gid = str(rec["ADM2_PCODE"])
            value = rec[column]
            if gid not in valid:
                unmatched.append(f"{filename}: {gid}")
                continue
            if pd.isna(value):
                unmatched.append(f"{filename}: {gid} empty '{column}'")
                continue
            rows.append(
                _row(
                    indicator,
                    gid,
                    float(value),
                    meta,
                    f"{path.name}, row {index + 2}, column '{column}'",
                    spec.unit,
                    "area_mean"
                    if spec.measure_type in {"share", "mean", "median"}
                    else "area_total",
                    "modelled_estimate",
                    RISK_FLOOR,
                    RISK_DATASET,
                    "2026",
                    "2026-01-01",
                    "2026-12-31",
                    "interval_mean",
                )
            )
    return rows


# --- build -----------------------------------------------------------------------------------


def build(raw: Path, spine_dir: Path, catalog: Path, out_dir: Path, work: Path) -> dict[str, Any]:
    valid = set(pd.read_parquet(spine_dir / "geographies.parquet")["geography_id"].astype(str))
    heigit = crosswalk_heigit(raw, spine_dir)
    di = crosswalk_desinventar(raw, spine_dir, work, catalog)
    for cw in (heigit, di):
        write_codes(cw, catalog)
        bad = [r["geography_id"] for r in cw.rows if r["geography_id"] not in valid]
        if bad:
            raise ValueError(f"{cw.code_system}: ids not in the spine: {bad}")
    unmatched: list[str] = []
    rows = ingest_heigit_access(raw, heigit.by_code(), unmatched)
    di_rows, qa, _ = ingest_desinventar(raw, di.by_code())
    rows += di_rows
    rows += ingest_risk(raw, valid, unmatched)
    # HeiGIT risk tables are p-coded already: verify, do not translate.
    risk_unmatched = risk_pcode_check(raw, valid)
    out_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    frame.to_parquet(out_dir / "observations.parquet", index=False)
    summary = {
        "rows": len(rows),
        "indicators": sorted({r["indicator_id"] for r in rows}),
        "heigit_units_matched": len(heigit.rows),
        "heigit_unmatched": heigit.unmatched,
        "desinventar_units_matched": len(di.rows),
        "desinventar_unmatched": di.unmatched,
        "heigit_risk_pcode_unmatched": risk_unmatched,
        "access_unmatched_rows": unmatched,
        "desinventar_events": {
            "total": qa.total,
            "non_disaster_types": qa.epidemic_etc,
            "no_district": qa.no_district,
            "unmatched_district_code": qa.unmatched_code,
            "unparseable_date": qa.bad_date,
            "used": qa.used,
            "year_range": qa.year_range,
        },
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    (out_dir / "qa.md").write_text(render_qa(heigit, di, qa, frame, risk_unmatched, unmatched))
    return summary


RISK_FILES = [
    "LKA_ADM2_access.csv",
    "LKA_ADM2_coping.csv",
    "LKA_ADM2_demographics.csv",
    "LKA_ADM2_evacuability.csv",
    "LKA_ADM2_facilities.csv",
    "LKA_ADM2_flood_exposure.csv",
    "LKA_ADM2_rai.csv",
    "LKA_ADM2_rural_population.csv",
    "LKA_ADM2_vulnerability.csv",
]


def risk_pcode_check(raw: Path, valid: set[str]) -> list[str]:
    """The risk tables use ADM2 p-codes directly: confirm every code is a spine district."""
    bad: list[str] = []
    for name in RISK_FILES:
        try:
            path, _ = latest(raw, "heigit", "heigit-risk-indicators", name)
        except FileNotFoundError:
            bad.append(f"{name}: not held")
            continue
        codes = pd.read_csv(path, dtype=str)["ADM2_PCODE"]
        bad += [f"{name}: {c}" for c in codes if c not in valid or len(c) != 4]
        if len(set(codes)) != 25:
            bad.append(f"{name}: {len(set(codes))} distinct districts, expected 25")
    return bad


def render_qa(
    heigit: Crosswalk,
    di: Crosswalk,
    qa: EventQA,
    frame: pd.DataFrame,
    risk_unmatched: list[str],
    access_unmatched: list[str],
) -> str:
    def block(cw: Crosswalk, label: str) -> list[str]:
        prov = [r for r in cw.rows if len(r["geography_id"]) == 3]
        dist = [r for r in cw.rows if len(r["geography_id"]) == 4]
        out = [
            f"## {label}",
            "",
            f"- Provinces matched: {len(prov)}; districts matched: {len(dist)}.",
            f"- Unmatched or ambiguous: {len(cw.unmatched)}",
            *[f"  - {u}" for u in cw.unmatched],
            *[f"- {n}" for n in cw.notes],
            *(
                [f"- To review, not mapped: {len(cw.review)}", *[f"  - {u}" for u in cw.review]]
                if cw.review
                else []
            ),
        ]
        disagree = [r for r in cw.rows if "DISAGREES" in str(r["notes"])]
        if disagree:
            out += [
                "- ISO number differs from the p-code suffix for: "
                + ", ".join(
                    f"{r['external_code']} {r['external_name']} → {r['geography_id']}"
                    for r in disagree
                ),
            ]
        return [*out, ""]

    lines = [
        "# QA: crosswalks and indicators for HeiGIT and DesInventar",
        "",
        *block(heigit, "HeiGIT accessibility (ISO 3166-2 codes → spine)"),
        *block(di, "DesInventar (own province and district codes → spine)"),
        "## HeiGIT risk-indicator tables (p-coded)",
        "",
        f"- p-code check on {len(RISK_FILES)} tables: "
        + ("all codes are spine districts" if not risk_unmatched else "problems below"),
        *[f"  - {u}" for u in risk_unmatched],
        "- Ingested: demographics (5), rural share, OSM hospitals and primary care counts, "
        "evacuation times (8) and flood exposure (28); the checks report covers each group. "
        "Not ingested: educational-facility counts (OSM holds about 40% of Giga's school list "
        "in the median district), the `access` counts (two HeiGIT products disagree by up to "
        "20 points), `coping` and `vulnerability` (identical joins of other tables) and the "
        "per-group RAI columns (only RAI_total_pop, by `slf subnational build`).",
        "",
        "## HeiGIT accessibility indicators",
        "",
        f"- Unmatched rows: {len(access_unmatched)}",
        *[f"  - {u}" for u in access_unmatched],
        "",
        "## DesInventar event records",
        "",
        f"- Records in the file: {qa.total}.",
        f"- Not counted as disasters (epidemic, plague, animal attack, snake bite): "
        f"{qa.epidemic_etc}.",
        f"- Records with no district code: {qa.no_district}.",
        f"- Records whose district code is not in the crosswalk: "
        f"{sum(qa.unmatched_code.values())} {qa.unmatched_code or ''}",
        f"- Records whose province column disagrees with the district code's province "
        f"(excluded, both are epidemic records): {qa.province_mismatch}.",
        f"- Records matched to a district but with an unparseable date (not counted by year): "
        f"{qa.bad_date}; examples {qa.bad_date_examples}",
        f"- DS division level: {qa.ds_with_code} matched records carry a DS code; "
        f"{qa.ds_mapped} reach a spine DS; {qa.ds_conflict} contradict their district (excluded); "
        f"{sum(qa.ds_unmapped_code.values())} carry a DS code not mapped "
        f"({len(qa.ds_unmapped_code)} codes, counted at district level only): "
        f"{dict(sorted(qa.ds_unmapped_code.items(), key=lambda kv: -kv[1])[:15])}",
        f"- Records matched to a district with a valid year: {qa.used}; years {qa.year_range}.",
        "",
        "| Event type (as written) | Records matched |",
        "|---|---:|",
        *[f"| {k} | {v} |" for k, v in sorted(qa.by_event.items(), key=lambda kv: -kv[1])],
        "",
        "## Observation rows",
        "",
        "| Indicator | Rows | Places | Periods |",
        "|---|---:|---:|---|",
    ]
    for ind, g in frame.groupby("indicator_id") if len(frame) else []:
        periods = sorted(set(g["period"]))
        lines.append(
            f"| {ind} | {len(g)} | {g['geography_id'].nunique()} | "
            f"{periods[0]} to {periods[-1]} ({len(periods)}) |"
        )
    lines.append("")
    return "\n".join(lines)
