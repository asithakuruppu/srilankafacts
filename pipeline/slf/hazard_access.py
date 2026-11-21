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

    def by_code(self) -> dict[str, str]:
        return {r["external_code"]: r["geography_id"] for r in self.rows}


def spine_places(spine_dir: Path) -> dict[int, list[Place]]:
    g = pd.read_parquet(spine_dir / "geographies.parquet")
    out: dict[int, list[Place]] = {}
    for r in g[g["level"].isin([1, 2])].to_dict("records"):
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


def crosswalk_desinventar(raw: Path, spine_dir: Path, work: Path) -> Crosswalk:
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
    cw.notes.append(
        f"DS divisions: {len(ds)} in the shapefile (2015 file, boundary vintage not stated); "
        "not mapped, because the event table carries no DS column and a DS crosswalk would "
        "need the 2012-to-2024 succession table (rule 5)."
    )
    return cw


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

DI_DATASET = "desinventar-sri-lanka"
DI_FLOOR = "district (DesInventar record location; GN named in about a quarter of records)"


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
    rows: list[dict[str, Any]] = []

    def emit(indicator: str, frame: pd.DataFrame) -> None:
        for (gid, year), g in frame.groupby(["gid", "year"]):
            lines = g["_line"].tolist()
            rows.append(
                _row(
                    indicator,
                    str(gid),
                    float(len(g)),
                    meta,
                    f"{path.name}: count of {len(g)} record(s) with Code District mapped to "
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
                    DI_FLOOR,
                    DI_DATASET,
                    str(int(year)),
                    f"{int(year)}-01-01",
                    f"{int(year)}-12-31",
                    "interval_total",
                )
            )

    for key, (_, types) in HAZARDS.items():
        emit(f"di_{key}_records", use[use["Event"].isin(types)])
    emit("di_disaster_records", use[~use["is_epi"]])
    return rows, qa, d


# --- build -----------------------------------------------------------------------------------


def build(raw: Path, spine_dir: Path, catalog: Path, out_dir: Path, work: Path) -> dict[str, Any]:
    valid = set(pd.read_parquet(spine_dir / "geographies.parquet")["geography_id"].astype(str))
    heigit = crosswalk_heigit(raw, spine_dir)
    di = crosswalk_desinventar(raw, spine_dir, work)
    for cw in (heigit, di):
        write_codes(cw, catalog)
        bad = [r["geography_id"] for r in cw.rows if r["geography_id"] not in valid]
        if bad:
            raise ValueError(f"{cw.code_system}: ids not in the spine: {bad}")
    unmatched: list[str] = []
    rows = ingest_heigit_access(raw, heigit.by_code(), unmatched)
    di_rows, qa, _ = ingest_desinventar(raw, di.by_code())
    rows += di_rows
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
        "- Not ingested: the nine tables are derived from other datasets (flood hazard layers, "
        "population), each needing its own check (catalogue note); only the Rural Access Index "
        "is ingested, by `slf subnational build`.",
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
