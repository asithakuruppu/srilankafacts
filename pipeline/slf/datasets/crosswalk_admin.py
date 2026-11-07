"""Admin code crosswalk (prompt G02): DCS Census 2024, NSDI, Lanka Data Layer and nuuuwan
codes matched to the spine's p-codes (COD-AB v03).

Match order: exact_code (only where the code transformation is shown to hold, and names agree)
→ name_and_parent (documented normalisation, unique within the parent) → manual review queue.
Nothing is dropped: every unit in every system is matched, queued, or listed as having no
counterpart.

Privacy: the NSDI GN layer also holds GN officers' names and phone numbers. Those fields are
never requested (AGENTS rule 11).
"""

# pandas type stubs can't follow these DataFrame operations; behaviour is covered by tests.
# pyright: reportArgumentType=false, reportCallIssue=false, reportAttributeAccessIssue=false
# pyright: reportOperatorIssue=false, reportReturnType=false, reportGeneralTypeIssues=false

from __future__ import annotations

import io
import json
import random
import re
import tarfile
import time
import unicodedata
import urllib.parse
import urllib.request
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

import openpyxl
import pandas as pd

from slf.snapshot import USER_AGENT, SnapshotRef, snapshot_bytes
from slf.storage import Storage

VINTAGE = "cod-ab-v03"
NSDI_BASE = "https://gisapps.nsdi.gov.lk/server/rest/services/Srilanka/Boundaries/MapServer"
NSDI_FIELDS = {
    # layer id: fields requested (never gnd_officer_name / gnd_officer_phone)
    1: [
        "objectid", "gnd_name", "gnd_code", "gnd_number", "gnd_name_gazetted",
        "ds_division_name", "ds_division_code", "district_name", "district_code",
        "province_name", "province_code", "dispute", "province_census_code",
        "district_census_code", "ds_division_census_code", "gnd_census_code", "gnd_no_census",
        "gnd_name_census", "admin_code", "year_created", "data_source",
    ],
    2: [
        "objectid", "ds_division_name", "ds_division_code", "district_name", "district_code",
        "province_name", "province_code", "adjusted_area", "description",
    ],
}  # fmt: skip
PAGE = 1000  # NSDI maxRecordCount
PAUSE_S = 1.5

FUZZY_ACCEPT = 0.80  # code agrees and names this similar → exact_code accepted
FUZZY_REVIEW = 0.60  # below this, a same-code candidate is not even suggested


# --- Snapshots of each system's unit list ----------------------------------------------------


def _get_json(url: str) -> dict[str, object]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def snapshot_nsdi_attributes(storage: Storage) -> SnapshotRef:
    """Page through NSDI GN and DS attributes (no geometry) and snapshot them as one JSON."""
    out: dict[str, object] = {"service": NSDI_BASE, "layers": {}, "queries": []}
    for layer, fields in NSDI_FIELDS.items():
        rows: list[dict[str, object]] = []
        offset = 0
        while True:
            q = {
                "where": "1=1",
                "outFields": ",".join(fields),
                "returnGeometry": "false",
                "orderByFields": "objectid",
                "resultOffset": offset,
                "resultRecordCount": PAGE,
                "f": "json",
            }
            url = f"{NSDI_BASE}/{layer}/query?{urllib.parse.urlencode(q)}"
            data = _get_json(url)
            feats = data.get("features", [])
            assert isinstance(feats, list)
            rows += [f["attributes"] for f in feats]
            out["queries"].append(url)  # type: ignore[union-attr]
            time.sleep(PAUSE_S)
            if not data.get("exceededTransferLimit") and len(feats) < PAGE:
                break
            offset += PAGE
        out["layers"][str(layer)] = rows  # type: ignore[index]
    content = json.dumps(out, ensure_ascii=False, indent=1).encode("utf-8")
    return snapshot_bytes(
        storage,
        source="nsdi",
        dataset="nsdi-admin-boundaries",
        filename="nsdi_gn_ds_attributes.json",
        content=content,
        url=f"{NSDI_BASE}/{{1,2}}/query (paged; see 'queries')",
        licence_note="no licence text on the service (copyrightText empty); cross-check only",
    )


def latest(storage: Storage, prefix: str, filename: str) -> SnapshotRef:
    keys = sorted(k for k in storage.list(prefix) if k.endswith("/" + filename))
    if not keys:
        raise FileNotFoundError(f"no snapshot {prefix}*/{filename}; run the snapshot step")
    meta = json.loads(storage.get(keys[-1] + ".meta.json"))
    return SnapshotRef(**{**meta, "reused": True})


# --- Parse each system into a common unit table ----------------------------------------------
# Columns: system, level (3 = DS, 4 = GN), code, name, parent_code, parent_name, candidate_pcode


def parse_dcs(storage: Storage, ref: SnapshotRef) -> pd.DataFrame:
    wb = openpyxl.load_workbook(io.BytesIO(storage.get(ref.key)), read_only=True)
    ws = wb.worksheets[0]
    header = [
        str(c or "").replace("\n", " ").strip()
        for c in next(ws.iter_rows(min_row=4, max_row=4, values_only=True))
    ]
    expected = ["Province Code", "Province Name", "District Code", "District Name",
                "DS_Division Code", "DS_Division Name", "GN_Division Code", "GN_Division Name",
                "GN_Division Number"]  # fmt: skip
    if header[:9] != expected:
        raise ValueError(f"unexpected DCS header {header[:9]}")
    recs = []
    for r in ws.iter_rows(min_row=6, values_only=True):
        if r[6] is None:
            continue
        dist, ds, gn = int(r[2]), int(r[4]), int(r[6])
        recs.append(
            {
                "dist": dist, "dist_name": str(r[3]).strip(), "ds": ds,
                "ds_name": str(r[5]).strip(), "gn": gn, "gn_name": str(r[7]).strip(),
                "gn_number": (str(r[8]).strip() or None) if r[8] is not None else None,
                "population": r[9],
            }
        )  # fmt: skip
    df = pd.DataFrame(recs)
    ds_code = df["dist"].astype(str) + df["ds"].map("{:02d}".format)
    gn = pd.DataFrame(
        {
            "system": "dcs_census2024",
            "level": 4,
            "code": ds_code + df["gn"].map("{:03d}".format),
            "name": df["gn_name"],
            "parent_code": ds_code,
            "parent_name": df["ds_name"],
            "extra": df["gn_number"],
        }
    )
    ds = (
        pd.DataFrame(
            {
                "code": ds_code,
                "name": df["ds_name"],
                "parent_code": df["dist"].astype(str),
                "parent_name": df["dist_name"],
            }
        )
        .drop_duplicates()
        .assign(system="dcs_census2024", level=3, extra=None)
    )
    out = pd.concat([ds, gn], ignore_index=True)
    out["candidate_pcode"] = "LK" + out["code"]
    return out


def parse_nsdi(storage: Storage, ref: SnapshotRef) -> pd.DataFrame:
    data = json.loads(storage.get(ref.key))
    gn = pd.DataFrame(data["layers"]["1"])
    ds = pd.DataFrame(data["layers"]["2"])

    def s(v: object) -> str | None:
        if v is None or (isinstance(v, float) and pd.isna(v)):
            return None
        t = str(v).strip()
        return t or None

    gn_rows = pd.DataFrame(
        {
            "system": "nsdi",
            "level": 4,
            # gnd_code is empty for every row; admin_code holds district+DS+GN (7 digits)
            "code": gn["admin_code"].map(s),
            "name": gn["gnd_name"].map(s),
            "parent_code": gn["admin_code"].map(lambda c: (s(c) or "")[:4] or None),
            "parent_name": gn["ds_division_name"].map(s),
            "extra": gn["dispute"].map(s),
        }
    )
    ds_rows = pd.DataFrame(
        {
            "system": "nsdi",
            "level": 3,
            "code": ds["ds_division_code"].map(s),
            "name": ds["ds_division_name"].map(s),
            "parent_code": ds["district_code"].map(s),
            "parent_name": ds["district_name"].map(s),
            "extra": None,
        }
    )
    out = pd.concat([ds_rows, gn_rows], ignore_index=True)
    out["candidate_pcode"] = out["code"].map(lambda c: f"LK{c}" if c and c.isdigit() else None)
    return out


def parse_ldl(storage: Storage, ref: SnapshotRef) -> pd.DataFrame:
    with tarfile.open(fileobj=io.BytesIO(storage.get(ref.key))) as tf:
        member = tf.extractfile("package/dist/index.mjs")
        assert member is not None
        js = member.read().decode("utf-8")
    m = re.search(r"units: (\[\[.*?\]\])\s*\}", js, flags=re.S)
    if not m:
        raise ValueError("could not find the units array in the LDL package")
    units = json.loads(m.group(1))
    df = pd.DataFrame(
        units,
        columns=[
            "code",
            "level",
            "name",
            "name_si",
            "name_ta",
            "parent_code",
            "area_km2",
            "lat",
            "lon",
        ],
    )
    df = df[df["level"].isin([3, 4])]
    names = dict(zip(df["code"], df["name"], strict=False))
    return pd.DataFrame(
        {
            "system": "ldl",
            "level": df["level"].astype(int),
            "code": df["code"],
            "name": df["name"],
            "parent_code": df["parent_code"],
            "parent_name": df["parent_code"].map(names),
            "extra": None,
            "candidate_pcode": df["code"],
        }
    )


def parse_nuuuwan(storage: Storage, ref: SnapshotRef) -> pd.DataFrame:
    rows = json.loads(storage.get(ref.key))
    ids = [r["region_id"] for r in rows]
    if not all(re.fullmatch(r"LK-\d{7}", i) for i in ids):
        raise ValueError("unexpected nuuuwan id format")
    return pd.DataFrame(
        {
            "system": "nuuuwan",
            "level": 4,
            "code": ids,
            "name": [r.get("region_name_from_source") for r in rows],
            "parent_code": [i[3:7] for i in ids],
            "parent_name": None,
            "extra": None,
            "candidate_pcode": ["LK" + i[3:] for i in ids],
        }
    )


# --- Name normalisation (documented in the crosswalk report) ---------------------------------

SUFFIXES = (" korale", " pattu", " ds division", " division", " town and gravets", " sub")


def _has(v: object) -> bool:
    return isinstance(v, str) and bool(v.strip())


def norm_basic(name: object) -> str:
    if not _has(name):
        return ""
    assert isinstance(name, str)
    t = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    t = t.replace("&", " and ")
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def norm_core(name: object) -> str:
    """Basic, minus bracketed alternative names, generic suffixes and 'four' → '4'."""
    raw = re.sub(r"\([^)]*\)", " ", name) if isinstance(name, str) else name
    t = " " + norm_basic(raw) + " "
    t = t.replace(" four ", " 4 ")
    for suf in ("korale", "koralaya", "ds division", "division"):
        t = t.replace(f" {suf} ", " ")
    return re.sub(r"\s+", " ", t).strip()


def tokens_contained(a: object, b: object) -> bool:
    """True if every word of the shorter core name appears in the longer one."""
    x, y = set(norm_core(a).split()), set(norm_core(b).split())
    return bool(x and y) and (x <= y or y <= x)


def norm_loose(name: object) -> str:
    """Spelling-tolerant key: basic + common romanisation variants, no spaces."""
    t = norm_basic(name)
    for a, b in (
        ("oo", "u"),
        ("ee", "i"),
        ("aa", "a"),
        ("th", "t"),
        ("dh", "d"),
        ("w", "v"),
        ("y", "i"),
    ):
        t = t.replace(a, b)
    t = re.sub(r"(.)\1+", r"\1", t)  # collapse doubled letters
    return t.replace(" ", "")


def similarity(a: object, b: object) -> float:
    x, y = norm_loose(a), norm_loose(b)
    xc, yc = norm_loose(norm_core(a)), norm_loose(norm_core(b))
    if xc and xc == yc:
        return 1.0 if x == y else 0.97
    if not x or not y:
        return 0.0
    if x == y:
        return 1.0
    return SequenceMatcher(None, x, y).ratio()


# --- Matching --------------------------------------------------------------------------------


@dataclass
class MatchResult:
    matches: pd.DataFrame  # one row per system unit with a geography_id
    review: pd.DataFrame  # manual review queue
    no_counterpart: pd.DataFrame  # spine units with no unit in the system


def match_system(
    units: pd.DataFrame, spine: pd.DataFrame, *, code_equivalence: bool
) -> MatchResult:
    """Match one system's DS (3) and GN (4) units to spine p-codes."""
    sp = spine[spine["level"].isin([3, 4])].set_index("geography_id")
    by_parent: dict[tuple[int, str], list[str]] = {}
    for gid, row in sp.iterrows():
        if row["parent_id"]:
            by_parent.setdefault((int(row["level"]), row["parent_id"]), []).append(str(gid))

    matched: list[dict[str, object]] = []
    review: list[dict[str, object]] = []
    # DS first, so GN parents can be resolved through the DS crosswalk
    ds_map: dict[str, str] = {}
    for lv in (3, 4):
        for u in units[units["level"] == lv].itertuples(index=False):
            cand = u.candidate_pcode
            base = {"system": u.system, "level": lv, "code": u.code, "name_in_system": u.name}
            # 1. exact code (only where the transformation is proven for this system)
            if code_equivalence and cand in sp.index and int(sp.loc[cand, "level"]) == lv:
                sim = similarity(u.name, sp.loc[cand, "name_en"])
                has_name = _has(sp.loc[cand, "name_en"]) and _has(u.name)
                contained = tokens_contained(u.name, sp.loc[cand, "name_en"])
                if sim >= FUZZY_ACCEPT or contained or not has_name:
                    conf = 1.0 if sim == 1.0 else 0.95 if sim >= FUZZY_ACCEPT else 0.85
                    note = (
                        "a name is missing on one side; matched on code only" if not has_name
                        else None if sim >= FUZZY_ACCEPT
                        else f"code agrees; one name contains the other ('{sp.loc[cand, 'name_en']}')"
                    )  # fmt: skip
                    if not has_name:
                        conf = 0.8
                    matched.append(
                        {
                            **base,
                            "geography_id": cand,
                            "match_method": "exact_code",
                            "confidence": conf if note is None else 0.8,
                            "note": note,
                        }
                    )
                    if lv == 3:
                        ds_map[str(u.code)] = cand
                    continue
            # 1b. GN number agrees under a DS whose code was remapped by the DS crosswalk
            if code_equivalence and lv == 4 and str(u.parent_code) in ds_map and u.code:
                cand2 = ds_map[str(u.parent_code)] + str(u.code)[-3:]
                if cand2 != cand and cand2 in sp.index:
                    sim2 = similarity(u.name, sp.loc[cand2, "name_en"])
                    if sim2 >= FUZZY_ACCEPT or tokens_contained(u.name, sp.loc[cand2, "name_en"]):
                        matched.append({**base, "geography_id": cand2, "match_method": "exact_code", "confidence": 0.9,
                                        "note": f"GN number agrees under remapped DS {ds_map[str(u.parent_code)]} (name similarity {sim2:.2f})"})  # fmt: skip
                        continue
            # 2. name within parent (parent through the DS crosswalk, else the candidate parent)
            if lv == 3:
                parent = f"LK{u.parent_code}" if u.parent_code else None
            else:
                parent = ds_map.get(str(u.parent_code)) or (
                    f"LK{u.parent_code}"
                    if u.parent_code and str(u.parent_code).isdigit()
                    else u.parent_code
                )
            siblings = by_parent.get((lv, parent), []) if parent else []
            exact = [
                g
                for g in siblings
                if norm_loose(sp.loc[g, "name_en"]) == norm_loose(u.name) and norm_loose(u.name)
            ]
            if len(exact) == 1:
                matched.append(
                    {
                        **base,
                        "geography_id": exact[0],
                        "match_method": "name_and_parent",
                        "confidence": 0.9,
                        "note": f"parent {parent}; code {cand} "
                        + ("differs" if cand != exact[0] else "agrees"),
                    }
                )
                if lv == 3:
                    ds_map[str(u.code)] = exact[0]
                continue
            # 3. manual review with candidates
            scored = sorted(
                ((similarity(u.name, sp.loc[g, "name_en"]), g) for g in siblings), reverse=True
            )[:3]
            if cand in sp.index and cand not in [g for _, g in scored]:
                s = similarity(u.name, sp.loc[cand, "name_en"])
                if s >= FUZZY_REVIEW:
                    scored.append((s, cand))
            reason = (
                "several same-name units in parent" if len(exact) > 1
                else "no unit with this code or name in the parent" if not scored
                else "code exists but names differ" if cand in sp.index
                else "no same-name unit in parent"
            )  # fmt: skip
            review.append({**base, "parent_in_system": u.parent_name or u.parent_code, "parent_geography_id": parent, "reason": reason,
                           "candidates": "; ".join(f"{g} {sp.loc[g, 'name_en']} ({s:.2f})" for s, g in scored) or None})  # fmt: skip

    m = pd.DataFrame(
        matched,
        columns=[
            "system",
            "level",
            "code",
            "name_in_system",
            "geography_id",
            "match_method",
            "confidence",
            "note",
        ],
    )
    # One spine unit claimed by several system units: keep the strongest claim, queue the rest.
    m = m.sort_values(["geography_id", "confidence"], ascending=[True, False])
    clash = m.duplicated("geography_id", keep="first")
    winners = m[~clash].set_index("geography_id")
    for row in m[clash].itertuples(index=False):
        w = winners.loc[row.geography_id]
        review.append({"system": row.system, "level": row.level, "code": row.code, "name_in_system": row.name_in_system,
                       "parent_in_system": None, "parent_geography_id": None,
                       "reason": f"spine unit already matched to {w['code']} '{w['name_in_system']}'; possibly a unit COD-AB does not have, or a duplicate",
                       "candidates": f"{row.geography_id} ({row.match_method}, {row.confidence})"})  # fmt: skip
    m = m[~clash].sort_values(["level", "code"]).reset_index(drop=True)
    r = pd.DataFrame(
        review,
        columns=[
            "system",
            "level",
            "code",
            "name_in_system",
            "parent_in_system",
            "parent_geography_id",
            "reason",
            "candidates",
        ],
    )
    used = set(m["geography_id"])
    nc = sp[~sp.index.isin(used)].reset_index()[["geography_id", "level", "name_en", "parent_id"]]
    return MatchResult(matches=m, review=r, no_counterpart=nc)


def inherit_matches(
    units: pd.DataFrame,
    base_units: pd.DataFrame,
    base: MatchResult,
    spine: pd.DataFrame,
    *,
    to_base: dict[str, str],
) -> MatchResult:
    """Reuse another system's crosswalk when ids are a proven 1:1 relabelling (e.g. nuuuwan → DCS)."""
    mapped = units["code"].map(to_base)
    base_codes = set(base_units.loc[base_units["level"].isin(units["level"].unique()), "code"])
    if mapped.isna().any() or set(mapped) != base_codes:
        raise ValueError("ids are not a 1:1 relabelling of the base system; match independently")
    names = dict(zip(units["code"], units["name"], strict=False))
    back = {v: k for k, v in to_base.items()}

    def relabel(frame: pd.DataFrame) -> pd.DataFrame:
        df = pd.DataFrame(frame[frame["level"].isin(units["level"].unique())]).copy()
        df["system"] = units["system"].iloc[0]
        df["code"] = df["code"].map(back)
        df["name_in_system"] = df["code"].map(names)
        return df

    m = relabel(base.matches)
    m["note"] = (
        m["note"]
        .fillna("")
        .str.cat(["via DCS code (ids identical)"] * len(m), sep="; ")
        .str.strip("; ")
    )
    r = relabel(base.review)
    sp = spine[spine["level"].isin(units["level"].unique())]
    nc = sp[~sp["geography_id"].isin(set(m["geography_id"]))][
        ["geography_id", "level", "name_en", "parent_id"]
    ]
    return MatchResult(matches=m, review=r, no_counterpart=nc.reset_index(drop=True))


def test_code_equivalence(
    units: pd.DataFrame, spine: pd.DataFrame, n: int = 50, seed: int = 7
) -> tuple[int, int, list[tuple[str, str, str]]]:
    """Sample n GN units: does the transformed code exist with a similar name?"""
    sp = spine.set_index("geography_id")
    gn = units[units["level"] == 4].reset_index(drop=True)
    idx = random.Random(seed).sample(range(len(gn)), min(n, len(gn)))
    ok, sample = 0, []
    for i in idx:
        u = gn.iloc[i]
        cand = u["candidate_pcode"]
        spine_name = sp.loc[cand, "name_en"] if cand in sp.index else None
        if spine_name is not None and similarity(u["name"], spine_name) >= FUZZY_ACCEPT:
            ok += 1
        sample.append((str(u["code"]), str(u["name"]), f"{cand} {spine_name}"))
    return ok, len(idx), sample


def codes_csv(m: pd.DataFrame) -> pd.DataFrame:
    """Rows for catalog/geographies/codes/{system}.csv (GeoCodeRow schema)."""
    return pd.DataFrame(
        {
            "geography_id": m["geography_id"],
            "vintage": VINTAGE,
            "code_system": m["system"].str.replace("_", "-"),
            "external_code": m["code"].astype(str),
            "external_name": m["name_in_system"],
            "match_method": m["match_method"],
            "confidence": m["confidence"],
            "notes": m["note"],
        }
    )


def write_outputs(results: dict[str, MatchResult], catalog_root: Path) -> list[Path]:
    codes_dir = catalog_root / "geographies" / "codes"
    codes_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for system, res in results.items():
        p = codes_dir / f"{system.replace('_', '-')}.csv"
        codes_csv(res.matches).sort_values(["geography_id", "external_code"]).to_csv(p, index=False)
        paths.append(p)
    review = pd.concat([r.review for r in results.values()], ignore_index=True)
    p = catalog_root / "geographies" / "manual-review.csv"
    review.to_csv(p, index=False)
    paths.append(p)
    return paths


# --- Build, report ---------------------------------------------------------------------------

SNAPSHOTS = {
    "dcs_census2024": ("raw/dcs/census-2024-gnd-tables/", "GN_population.xlsx", parse_dcs),
    "nsdi": ("raw/nsdi/nsdi-admin-boundaries/", "nsdi_gn_ds_attributes.json", parse_nsdi),
    "ldl": ("raw/lanka-data-layer/ldl-admin-npm/", "admin-0.1.0.tgz", parse_ldl),
    "nuuuwan": ("raw/nuuuwan/nuuuwan-lk-census-2024/", "Person-Sex_gnd_data.json", parse_nuuuwan),
}
LEVEL = {3: "DS", 4: "GN"}


@dataclass
class CrosswalkBuild:
    units: dict[str, pd.DataFrame]
    results: dict[str, MatchResult]
    refs: dict[str, SnapshotRef]
    equivalence: dict[str, tuple[int, int, list[tuple[str, str, str]]]]


def apply_manual(
    res: MatchResult, system: str, manual: pd.DataFrame, spine: pd.DataFrame
) -> MatchResult:
    """Apply person-made decisions (catalog/geographies/manual-matches.csv); they win over automatic ones."""
    rows = manual[manual["system"] == system]
    if rows.empty:
        return res
    names = dict(zip(spine["geography_id"], spine["name_en"], strict=False))
    m, r = res.matches.copy(), res.review.copy()
    for d in rows.itertuples(index=False):
        level = int(d.level)
        prev = m[(m["code"] == d.code) & (m["level"] == level)]
        prev_r = r[(r["code"] == d.code) & (r["level"] == level)]
        name = (
            prev["name_in_system"].iloc[0]
            if len(prev)
            else (prev_r["name_in_system"].iloc[0] if len(prev_r) else None)
        )
        m = m[~((m["code"] == d.code) & (m["level"] == level))]
        r = r[~((r["code"] == d.code) & (r["level"] == level))]
        base = {"system": system, "level": level, "code": d.code, "name_in_system": name}
        if d.decision == "match":
            m = pd.concat([m, pd.DataFrame([{**base, "geography_id": d.geography_id, "match_method": "manual", "confidence": 0.9,
                                              "note": f"manual ({d.decided_by}, {d.date}): {d.evidence}"}])], ignore_index=True)  # fmt: skip
        elif d.decision == "review":
            was = (
                f"; automatic match was {prev['geography_id'].iloc[0]} {names.get(prev['geography_id'].iloc[0])}"
                if len(prev)
                else ""
            )
            r = pd.concat([r, pd.DataFrame([{**base, "parent_in_system": None, "parent_geography_id": None,
                                              "reason": f"manual review ({d.decided_by}, {d.date}): {d.evidence}{was}", "candidates": None}])], ignore_index=True)  # fmt: skip
    used = set(m["geography_id"])
    nc = res.no_counterpart
    # spine units freed by a manual decision become "no counterpart"
    freed = spine[spine["level"].isin(res.matches["level"].unique()) & ~spine["geography_id"].isin(used)
                  & spine["geography_id"].isin(res.matches["geography_id"])][["geography_id", "level", "name_en", "parent_id"]]  # fmt: skip
    nc = pd.concat([nc, freed], ignore_index=True).drop_duplicates("geography_id")
    return MatchResult(
        matches=m.sort_values(["level", "code"]).reset_index(drop=True),
        review=r.reset_index(drop=True),
        no_counterpart=nc,
    )


def build(
    storage: Storage, spine: pd.DataFrame, manual: pd.DataFrame | None = None
) -> CrosswalkBuild:
    full_spine = spine
    if "status" in spine.columns:
        # provisional units are matched only by a person
        spine = pd.DataFrame(spine[spine["status"] == "current"])
    refs = {k: latest(storage, pre, fn) for k, (pre, fn, _) in SNAPSHOTS.items()}
    units = {k: SNAPSHOTS[k][2](storage, refs[k]) for k in SNAPSHOTS}
    equiv = {k: test_code_equivalence(u, spine) for k, u in units.items()}
    results: dict[str, MatchResult] = {}
    for k in ("dcs_census2024", "nsdi", "ldl"):
        ok, n, _ = equiv[k]
        results[k] = match_system(units[k], spine, code_equivalence=ok >= 0.9 * n)
        if manual is not None:
            results[k] = apply_manual(results[k], k, manual, full_spine)
    nu = units["nuuuwan"]
    results["nuuuwan"] = inherit_matches(
        nu,
        units["dcs_census2024"],
        results["dcs_census2024"],
        spine,
        to_base={c: c[3:] for c in nu["code"]},
    )
    return CrosswalkBuild(units=units, results=results, refs=refs, equivalence=equiv)


def _table(df: pd.DataFrame) -> str:
    if df.empty:
        return "None."
    cols = list(df.columns)
    lines = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for row in df.itertuples(index=False):
        lines.append(
            "| " + " | ".join("" if pd.isna(v) else str(v).replace("|", "/") for v in row) + " |"
        )
    return "\n".join(lines)


def render_report(b: CrosswalkBuild, spine: pd.DataFrame) -> str:
    names = dict(zip(spine["geography_id"], spine["name_en"], strict=False))
    rates = []
    for k, res in b.results.items():
        for lv in (3, 4):
            n = int((b.units[k]["level"] == lv).sum())
            if not n:
                continue
            m = res.matches[res.matches["level"] == lv]
            rates.append({
                "System": k, "Level": LEVEL[lv], "Units in system": f"{n:,}",
                "exact_code": int((m["match_method"] == "exact_code").sum()),
                "name_and_parent": int((m["match_method"] == "name_and_parent").sum()),
                "manual": int((m["match_method"] == "manual").sum()),
                "Matched %": f"{100 * len(m) / n:.2f}",
                "Review queue": int((res.review["level"] == lv).sum()),
                "Spine units with no counterpart": int((res.no_counterpart["level"] == lv).sum()),
            })  # fmt: skip
    dcs = b.results["dcs_census2024"]
    nsdi = b.results["nsdi"]
    ds_remap = dcs.matches[
        (dcs.matches["level"] == 3) & (dcs.matches["match_method"] == "name_and_parent")
    ]
    ds_remap = ds_remap.assign(spine_name=ds_remap["geography_id"].map(names))[
        ["code", "name_in_system", "geography_id", "spine_name"]
    ]
    nsdi_nc = nsdi.no_counterpart[nsdi.no_counterpart["level"] == 3][["geography_id", "name_en"]]
    nsdi_ds_review = nsdi.review[nsdi.review["level"] == 3][
        ["code", "name_in_system", "parent_in_system", "reason"]
    ]
    allm = pd.concat([r.matches for r in b.results.values()], ignore_index=True)
    sample = allm[allm["level"] == 4].sample(20, random_state=11)
    sample = sample.assign(spine_name=sample["geography_id"].map(names))[
        [
            "system",
            "code",
            "name_in_system",
            "geography_id",
            "spine_name",
            "match_method",
            "confidence",
        ]
    ]
    review_total = sum(len(r.review) for r in b.results.values())
    nsdi_units = b.units["nsdi"]
    disputes = nsdi_units[(nsdi_units["level"] == 4) & nsdi_units["extra"].notna()][
        "extra"
    ].value_counts()

    eq_rows = [
        {
            "System": k,
            "Sample": n,
            "Code transform holds": ok,
            "Example": f"{s[0][0]} {s[0][1]} → {s[0][2]}",
        }
        for k, (ok, n, s) in b.equivalence.items()
    ]
    src_rows = [
        {
            "System": k,
            "Snapshot": f"`{r.key}`",
            "sha256": r.sha256[:16] + "…",
            "Retrieved": r.retrieved_at,
        }
        for k, r in b.refs.items()
    ]

    return "\n".join([
        "# Crosswalk report: admin codes → spine p-codes (COD-AB v03)",
        "",
        "Generated by `slf crosswalk build` (`pipeline/slf/datasets/crosswalk_admin.py`, prompt G02). "
        "Outputs: `catalog/geographies/codes/{system}.csv` and `catalog/geographies/manual-review.csv`.",
        "",
        "## 1. Inputs",
        "",
        _table(pd.DataFrame(src_rows)),
        "",
        "- **DCS Census 2024** (authoritative for census joins): the GN-level population workbook "
        "(\"Grama Niladhari Division Level Population by Sex and Age Group (Provisional)\"). Rights unclear; used internally for matching only.",
        "- **NSDI**: attributes of the GN (layer 1) and DS (layer 2) layers, paged at 1,000 records with pauses. "
        "GN officers' names and phone numbers in that layer were **not** requested. `gnd_code` is empty for every GN, so `admin_code` is used.",
        "- **Lanka Data Layer**: the `@lanka-data-layer/admin` 0.1.0 npm package (MIT). Cross-check only.",
        "- **nuuuwan** `lk_census_2024` (`Person-Sex/gnd_data.json`, MIT). Cross-check only.",
        "",
        "## 2. Is the code transformation real? (tested before use)",
        "",
        "Rule tested: system code `DDSSGGG` (district, DS, GN) → p-code `LKDDSSGGG`. Sample of 50 random GN units per system; "
        f"\"holds\" means the p-code exists and the names agree (similarity ≥ {FUZZY_ACCEPT}).",
        "",
        _table(pd.DataFrame(eq_rows)),
        "",
        "The transformation holds broadly, so codes are used, but **only unit by unit**: a code match is accepted only if the names also agree. "
        "This matters because DS codes have drifted (section 4).",
        "",
        "## 3. Match rates",
        "",
        _table(pd.DataFrame(rates)),
        "",
        f"**Review queue: {review_total} items** (all systems) in `catalog/geographies/manual-review.csv`, each with a reason and up to three candidates. "
        "Nothing is dropped: every unit is matched, queued, or (for spine units) listed as having no counterpart.",
        "",
        "Method and confidence: `exact_code` 1.0 (names identical), 0.95 (names similar), 0.9 (GN number agrees under a remapped DS), "
        "0.85 (code agrees and one name contains the other, e.g. \"Laggala-Pallegama\" / \"Laggala\"), 0.8 (code only; a name is missing). "
        "`name_and_parent` 0.9 (same normalised name, unique in the parent). Fuzzy name matches are **never** accepted without a code agreeing.",
        "",
        "Name normalisation: Unicode → ASCII, lower case, `&` → `and`, punctuation removed; bracketed alternative names removed; "
        "`four` → `4`; suffixes `korale`, `koralaya`, `division` dropped; romanisation variants folded (`oo`→`u`, `ee`→`i`, `aa`→`a`, `th`→`t`, `dh`→`d`, `w`→`v`, `y`→`i`, doubled letters).",
        "",
        "## 4. DS divisions: 340 (DCS) vs 339 (COD-AB) vs 332 (NSDI) vs 331 (commonly cited)",
        "",
        "**DCS 340 vs COD-AB 339: Kalmunai.** COD-AB has one Kalmunai unit (`LK5221`, 58 GNs). DCS splits that area into two DS divisions: "
        "**Kalmunai North Sub** (DCS 5221) and **Kalmunai** (DCS 5224), 29 GNs each. The 29 *named* COD-AB GNs in `LK5221` are exactly the 29 DCS 5221 GNs (codes and names agree); "
        "the other 29 COD-AB GNs have no names, so they cannot yet be matched one to one with DCS 5224's GNs. By the lead's decision (D-022), Kalmunai North Sub is the provisional unit "
        "`LK-ADM3-P0001`, composed of its 29 GNs (`catalog/geographies/provisional.csv`). DCS 5224 is **not** equivalent to `LK5221` and stays in the review queue with this explanation "
        "(`catalog/geographies/manual-matches.csv`); `LK5221` is therefore listed as having no DCS counterpart.",
        "",
        "**DS codes differ between DCS and COD-AB for 13 units** (matched by name within the district):",
        "",
        _table(ds_remap),
        "",
        "So a DCS DS code cannot be turned into a p-code by rule in these districts (Nuwara Eliya, Galle, Batticaloa, Ampara, Badulla). Example: DCS 2309 is Walapane, COD-AB `LK2309` is Nildandahinna.",
        "",
        f"**NSDI 332.** NSDI has two \"Water Area\" pseudo-units (code 9999), three duplicated codes, and older units such as an undivided \"Kothmale\". "
        f"{len(nsdi_nc)} COD-AB DS units have no NSDI counterpart:",
        "",
        _table(nsdi_nc),
        "",
        "NSDI DS units in the review queue:",
        "",
        _table(nsdi_ds_review),
        "",
        "This pattern (newer DS divisions missing, an undivided Kothmale) suggests the NSDI DS layer predates recent DS creations. That is an inference; dates are not given by the service.",
        "",
        "**331 (commonly cited).** Not resolved: no official list with 331 units was found in this task. COD-AB (339) and DCS 2024 (339 + Kalmunai North Sub) agree with each other. "
        "The Survey Department letter (`docs/outreach/`) asks for the official list.",
        "",
        "## 5. GN divisions",
        "",
        "- DCS 14,008 vs COD-AB 14,043: matched units, the DCS review queue and the COD-AB GNs with no DCS counterpart are all listed in the CSVs. "
        "COD-AB GNs without a DCS counterpart cluster in Kalmunai (`LK5221`) and Eravur (`LK5115`), consistent with the Kalmunai North Sub and Eravur differences.",
        "- Same-name GN groups within a DS (for example two \"High Forest\" in `LK2324`) are never matched by name; they need a code or a person.",
        "- Several review items are one place with two names (for example DCS \"Kompagngnaweediya\" vs COD-AB `LK1103130` \"Slave Island\"). They need a person, ideally with a Sinhala/Tamil speaker.",
        "",
        "NSDI boundary dispute flags on GN polygons (from the `dispute` field; used in G03):",
        "",
        _table(disputes.rename_axis("dispute flag").reset_index(name="GN units")),
        "",
        "## 6. Twenty random GN matches to eyeball",
        "",
        _table(sample),
        "",
    ])  # fmt: skip
