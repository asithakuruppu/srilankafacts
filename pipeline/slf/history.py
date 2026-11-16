"""Stage 2 history (G06): DS boundary change 2012 -> 2024 and the district census series.

Inputs (all snapshots; nothing here downloads except `snapshot`):

- DCS "Population by GN division and sex 2012" (a DCS-authored PDF, created 2015, printed
  from `Population by GN and Sex 2012.xlsx`). The original DCS address was not found; the
  copy held is the one mirrored in nuuuwan/lk_census_2012 at a pinned commit. It gives the
  2012 district, DS and GN rows with DCS GN numbers. Used for 2012 DS membership and DS totals.
- DCS Statistical Abstract 2024, Table 2.7 (population by DS division, Census 2012), served by
  DCS. Independent check of every 2012 DS total.
- DCS Statistical Abstract 2024, Table 2.1 (population by district, census years 1871-2012,
  thousands). Transcribed to `catalog/references/dcs-abstract2024-table2.1-transcription.csv`
  and checked here against the PDF's own text layer.
- DCS Census 2024 Final Report (already snapshotted for census-2024-gnd-tables): Tables 2.1,
  2.3, 2.4 (administrative structure), 3.1 (national series) and 3.3 (district 1981-2024).
- DCS Census 2024 GN workbook (census-2024-gnd-tables), for 2024 DS membership and totals.

PDF page text comes from `scripts/pdf_pages.swift` (macOS PDFKit), as for the Q01 audit.

Matching never uses names alone across schemes: GNs are matched between the two DCS lists
inside the same district on DCS's own GN number, with the GN name as a second key. Every
change is classified from those GN flows, and every comparison carries `exact` or
`approximate` with its method (data-model §3.3, AGENTS rules 5 and 6).
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from slf.snapshot import SnapshotRef, snapshot_url
from slf.storage import Storage

NUUUWAN_COMMIT = "8d8af0571f5c2c3ff289e4a8323969d761556f00"
NUUUWAN_BASE = (
    f"https://raw.githubusercontent.com/nuuuwan/lk_census_2012/{NUUUWAN_COMMIT}"
    "/data/population-gender"
)
ABSTRACT_BASE = "https://www.statistics.gov.lk/abstract2024/CHAP2"

# (source, dataset, url, filename, licence note)
SNAPSHOTS: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "nuuuwan",
        "nuuuwan-lk-census-2012",
        f"{NUUUWAN_BASE}/source.pdf",
        "population-gender_source.pdf",
        "DCS-authored PDF mirrored in an MIT repository; figures' rights follow DCS (unclear)",
    ),
    (
        "nuuuwan",
        "nuuuwan-lk-census-2012",
        f"{NUUUWAN_BASE}/data.json",
        "population-gender_data.json",
        "MIT repository; cross-check only, never authority",
    ),
    (
        "dcs",
        "census-2012-tables",
        f"{ABSTRACT_BASE}/2.7.pdf",
        "abstract2024_table2.7.pdf",
        "DCS Statistical Abstract 2024; no reuse terms published (unclear)",
    ),
    (
        "dcs",
        "census-district-series",
        f"{ABSTRACT_BASE}/2.1.pdf",
        "abstract2024_table2.1.pdf",
        "DCS Statistical Abstract 2024; no reuse terms published (unclear)",
    ),
)

CENSUS_DATE_2012 = date(2012, 3, 20)  # Final Report 2024, Table 3.1
CENSUS_DATE_2024 = date(2024, 12, 19)
YEARS = (CENSUS_DATE_2024 - CENSUS_DATE_2012).days / 365.25

# DCS district codes (2024 workbook) by the names printed in the 2012 GN file.
DISTRICTS: dict[str, int] = {
    "Colombo": 11, "Gampaha": 12, "Kalutara": 13, "Kandy": 21, "Matale": 22,
    "Nuwara Eliya": 23, "Galle": 31, "Matara": 32, "Hambantota": 33, "Jaffna": 41,
    "Mannar": 42, "Vavuniya": 43, "Mullaitivu": 44, "Kilinochchi": 45, "Batticaloa": 51,
    "Ampara": 52, "Trincomalee": 53, "Kurunegala": 61, "Puttalam": 62, "Anuradhapura": 71,
    "Polonnaruwa": 72, "Badulla": 81, "Moneragala": 82, "Ratnapura": 91, "Kegalle": 92,
}  # fmt: skip

_NUM = r"\d{1,3}(?:,\d{3})*"
_GN_NO = re.compile(r"(?:[A-Z]{1,2}[/\-]?)?\d+[A-Za-z0-9/\-]*")
_PAGE = re.compile(r"page-(\d{3})\.txt$")


def latest_snapshot(storage: Storage, dataset_prefix: str, filename: str) -> SnapshotRef:
    keys = sorted(k for k in storage.list(dataset_prefix) if k.endswith("/" + filename))
    if not keys:
        raise FileNotFoundError(
            f"no snapshot {dataset_prefix}/…/{filename}; run `slf history snapshot`"
        )
    meta = json.loads(storage.get(keys[-1] + ".meta.json"))
    return SnapshotRef(**{**meta, "reused": True})


def snapshot(storage: Storage) -> list[SnapshotRef]:
    """Fetch the four history inputs (the Final Report and GN workbook are already held)."""
    return [
        snapshot_url(storage, source=s, dataset=d, url=u, filename=f, licence_note=n)
        for s, d, u, f, n in SNAPSHOTS
    ]


def norm(name: object) -> str:
    """Lower-case ASCII letters and digits only (hyphen variants, spaces and brackets dropped)."""
    text = unicodedata.normalize("NFKD", str(name)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", text.lower())


def norm_gn_number(value: object) -> str | None:
    """'J-37', 'J/37' and 'j 37' -> 'J37'; '06' -> '6'.

    DCS writes the same GN number with different separators in the two lists.
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    text = re.sub(r"[\s/\-]", "", str(value)).upper()
    text = re.sub(r"(?<!\d)0+(?=\d)", "", text)  # '06' -> '6'
    return text or None


def _pages(pages_dir: Path) -> list[tuple[int, list[str]]]:
    out = []
    for p in sorted(pages_dir.glob("page-*.txt")):
        m = _PAGE.search(p.name)
        if m:
            out.append((int(m[1]), p.read_text("utf-8").splitlines()))
    if not out:
        raise FileNotFoundError(f"no page-*.txt in {pages_dir}")
    return out


# --- 2012 GN file -----------------------------------------------------------------------------


@dataclass
class Rows2012:
    districts: pd.DataFrame
    ds: pd.DataFrame
    gn: pd.DataFrame
    national: dict[str, int]
    unparsed: list[str] = field(default_factory=list)


def parse_line(line: str) -> tuple[str, str | None, int | None, int | None, int | None] | None:
    """'Yati Hanguranketha 495B 799 367 432' -> (name, gn number, total, male, female).

    Lines with a name and GN number but no figures (GNs DCS lists without population) return
    totals of None. Header and page-number lines return None.
    """
    toks = line.strip().split()
    if len(toks) >= 4 and all(re.fullmatch(_NUM, t) for t in toks[-3:]):
        t, m, f = (int(x.replace(",", "")) for x in toks[-3:])
        if m + f == t:
            rest = toks[:-3]
            gn_no = None
            if (
                len(rest) > 2
                and re.fullmatch(r"[A-Za-z0-9]", rest[-1])
                and _GN_NO.fullmatch(rest[-2])
            ):
                # The number printed with a space before its suffix: '175 A', '126A 1'.
                gn_no, rest = rest[-2] + rest[-1], rest[:-2]
            elif len(rest) > 1 and _GN_NO.fullmatch(rest[-1]):
                gn_no, rest = rest[-1], rest[:-1]
            return " ".join(rest), gn_no, t, m, f
    if (
        len(toks) >= 2
        and _GN_NO.fullmatch(toks[-1])
        and re.match(r"[A-Za-z]", toks[0])
        and not any(re.fullmatch(r"[\d,]+", t) for t in toks[:-1])
    ):
        # A name and GN number with no other figures; a row whose figures fail the check
        # above is not mistaken for one (it returns None and breaks the DS arithmetic).
        return " ".join(toks[:-1]), toks[-1], None, None, None
    return None


def parse_gn_2012(pages_dir: Path) -> Rows2012:
    """Rebuild the district > DS > GN hierarchy from the 2012 GN file's page text.

    The file prints a district row, then for each DS a DS row followed by its GN rows, with no
    level column. The hierarchy is recovered from the arithmetic: a DS row's total equals the
    sum of the GN rows after it, and a district's total equals the sum of its DS rows. GN rows
    without figures belong to the DS whose rows they sit among (a DS row always precedes its
    GNs). Any break in the arithmetic raises.
    """
    seq: list[tuple[int, int, tuple[str, str | None, int | None, int | None, int | None]]] = []
    unparsed: list[str] = []
    for page, lines in _pages(pages_dir):
        for i, line in enumerate(lines, start=1):
            parsed = parse_line(line)
            if not seq and (parsed is None or parsed[0] != "Sri Lanka"):
                continue  # title and column headers before the first row
            if parsed is None:
                if line.strip() and not line.strip().isdigit():
                    unparsed.append(f"p{page} l{i}: {line.strip()}")
                continue
            seq.append((page, i, parsed))
    if not seq or seq[0][2][0] != "Sri Lanka":
        raise ValueError("2012 GN file: first row is not Sri Lanka")
    _, _, (_, _, nt, nm, nf) = seq[0]
    national = {"total": nt or 0, "male": nm or 0, "female": nf or 0}
    dist_rows, ds_rows, gn_rows = [], [], []
    k = 1
    while k < len(seq):
        page, line, (dname, _, dt, dm, df_) = seq[k]
        if dname not in DISTRICTS or dt is None:
            raise ValueError(f"p{page} l{line}: expected a district row, got {dname!r}")
        k += 1
        dist_rows.append(
            dict(
                district=dname,
                district_code=DISTRICTS[dname],
                total=dt,
                male=dm,
                female=df_,
                page=page,
                line=line,
            )
        )
        dsum = order = 0
        while dsum < dt:
            page, line, (sname, _, st, sm, sf) = seq[k]
            if st is None:
                raise ValueError(f"p{page} l{line}: expected a DS row, got {sname!r}")
            k += 1
            order += 1
            ds_id = f"{DISTRICTS[dname]:02d}-{order:02d}"
            ds_rows.append(
                dict(
                    ds_2012=ds_id,
                    district=dname,
                    district_code=DISTRICTS[dname],
                    order=order,
                    name=sname,
                    total=st,
                    male=sm,
                    female=sf,
                    page=page,
                    line=line,
                )
            )
            gsum = 0
            while k < len(seq) and (gsum < st or seq[k][2][2] is None):
                page, line, (gname, gno, gt, gm, gf) = seq[k]
                k += 1
                gn_rows.append(
                    dict(
                        ds_2012=ds_id,
                        ds_name=sname,
                        district_code=DISTRICTS[dname],
                        name=gname,
                        gn_number=gno,
                        total=gt,
                        male=gm,
                        female=gf,
                        page=page,
                        line=line,
                    )
                )
                gsum += gt or 0
            if gsum != st:
                raise ValueError(f"DS {sname} ({dname}): GN rows sum to {gsum}, DS row {st}")
            dsum += st
        if dsum != dt:
            raise ValueError(f"district {dname}: DS rows sum to {dsum}, district row {dt}")
    return Rows2012(
        districts=pd.DataFrame(dist_rows),
        ds=pd.DataFrame(ds_rows),
        gn=pd.DataFrame(gn_rows),
        national=national,
        unparsed=unparsed,
    )


def parse_abstract_ds_triples(pages_dir: Path) -> list[tuple[int, int, int, int]]:
    """(total, male, female, page) for every row of Abstract Table 2.7 (DS and district rows).

    The rows mix Sinhala, legacy-font Tamil and English, so names are not parsed; rows are
    compared to the 2012 GN file by their three figures. One printed figure uses a point as
    a thousands separator ('2.324,349'), so points are treated like commas.
    """
    out = []
    for page, lines in _pages(pages_dir):
        for line in lines:
            toks = line.strip().split()
            if len(toks) < 4 or not all(
                re.fullmatch(r"\d{1,3}(?:[.,]\d{3})*", t) for t in toks[-3:]
            ):
                continue
            t, m, f = (int(re.sub(r"[.,]", "", x)) for x in toks[-3:])
            if m + f == t:
                out.append((t, m, f, page))
    return out


# --- Final Report 2024 tables -----------------------------------------------------------------


def parse_table_3_3(text: str) -> pd.DataFrame:
    """Final Report Table 3.3: district population 1981, 2001, 2012, 2024 (and growth rates).

    2001 is '-' for the seven districts DCS could not fully enumerate.
    """
    rows = []
    names = ["Sri Lanka", *DISTRICTS]
    for line in text.splitlines():
        s = line.strip()
        name = next((n for n in names if s.startswith(n + " ")), None)
        if not name:
            continue
        toks = s[len(name) :].split()
        nums: list[int | None] = []
        for t in toks:
            if re.fullmatch(_NUM, t) and "," in t:
                nums.append(int(t.replace(",", "")))
            elif t == "-" and len(nums) == 1:
                nums.append(None)
            if len(nums) == 4:
                break
        if len(nums) == 4:
            rows.append(
                dict(
                    district=name,
                    p1981=nums[0],
                    p2001=nums[1],
                    p2012=nums[2],
                    p2024=nums[3],
                    rate_2012_2024=float(toks[-1]),
                )
            )
    return pd.DataFrame(rows)


def parse_table_3_1(text: str) -> pd.DataFrame:
    """Final Report Table 3.1: census dates and national population 1871-2024."""
    rows = []
    for m in re.finditer(r"^(\d{2}) ([A-Z][a-z]+) (\d{4})\d? ([\d,]+)", text, re.M):
        rows.append(
            dict(
                year=int(m[3]),
                census_date=f"{m[1]} {m[2]} {m[3]}",
                population=int(m[4].replace(",", "")),
            )
        )
    return pd.DataFrame(rows)


def parse_table_2_3(text: str) -> dict[str, int]:
    """Final Report Table 2.3 (2012): number of DS divisions by district (and 'Total')."""
    out: dict[str, int] = {}
    for line in text.splitlines():
        m = re.match(r"^(Total|[A-Z][a-z]+(?: Eliya)?) (\d+) ", line.strip())
        if m and (m[1] == "Total" or m[1] in DISTRICTS):
            out[m[1]] = int(m[2])
    return out


# --- GN matching ------------------------------------------------------------------------------


Rec = dict[str, Any]


def records(df: pd.DataFrame) -> list[Rec]:
    """Rows as plain dicts with string keys (NaN becomes None)."""
    out: list[Rec] = []
    for row in df.to_dict("records"):
        out.append({str(k): (None if isinstance(v, float) and math.isnan(v) else v)
                    for k, v in row.items()})  # fmt: skip
    return out


def match_gns(gn12: pd.DataFrame, gn24: pd.DataFrame) -> pd.DataFrame:
    """Match 2012 GN rows to 2024 GN rows inside each district, in four layers.

    1. DCS GN number and normalised name both equal (unique on both sides).
    2. GN number equal (unique on both sides among rows still unmatched).
    3. Normalised name equal (unique on both sides among rows still unmatched).
    4. Number, name and DS name equal (for a GN DCS lists under two DS divisions, Punanai
       East 211B, Final Report 2024 Table 2.4 note 2).
    Returns one row per 2012 GN with `gn_2024` (DCS 7-digit code) and `match_layer`, or
    nulls when unmatched. Rows are never matched across districts.
    """
    a = records(gn12)
    for r in a:
        r["gn_number_printed"] = r["gn_number"]
        r["key_number"] = norm_gn_number(r["gn_number"])
        r["key_name"] = norm(r["name"])
        r["key_ds"] = norm(r["ds_name"])
        r["gn_2024"] = r["ds_2024"] = r["name_2024"] = r["match_layer"] = None
    b = records(gn24)
    for r in b:
        r["key_number"] = norm_gn_number(r["gn_number"])
        r["key_name"] = norm(r["gn_name"])
        r["key_ds"] = norm(r["ds_name"])
    layers = (
        ("number_and_name", ("key_number", "key_name")),
        ("number", ("key_number",)),
        ("name", ("key_name",)),
        ("number_name_and_ds", ("key_number", "key_name", "key_ds")),
    )
    taken: set[str] = set()
    for layer, fields in layers:

        def key(r: Rec, fields: tuple[str, ...] = fields) -> tuple[Any, ...] | None:
            values = tuple(r[f] for f in fields)
            return None if any(v in (None, "") for v in values) else (r["district_code"], *values)

        left: dict[tuple[Any, ...], list[Rec]] = defaultdict(list)
        for r in a:
            if r["gn_2024"] is None and (k := key(r)) is not None:
                left[k].append(r)
        right: dict[tuple[Any, ...], list[Rec]] = defaultdict(list)
        for r in b:
            if r["dcs_gn"] not in taken and (k := key(r)) is not None:
                right[k].append(r)
        for k, rows in left.items():
            other = right.get(k, [])
            if len(rows) == 1 and len(other) == 1:
                rows[0].update(gn_2024=other[0]["dcs_gn"], ds_2024=other[0]["dcs_ds"],
                               name_2024=other[0]["gn_name"], match_layer=layer)  # fmt: skip
                taken.add(other[0]["dcs_gn"])
    for r in a:
        for f in ("key_number", "key_name", "key_ds"):
            del r[f]
    return pd.DataFrame(a)


# --- Classification ---------------------------------------------------------------------------

MINOR = 0.10  # a flow below 10% of both units' GNs is a transfer, not a split or merge
ONE_TO_ONE = ("unchanged", "renamed")


@dataclass
class Result:
    units_2012: pd.DataFrame
    units_2024: pd.DataFrame
    flows: pd.DataFrame
    relations: pd.DataFrame
    comparison: pd.DataFrame
    groups: pd.DataFrame
    gn_matches: pd.DataFrame
    unmatched_2024: pd.DataFrame
    checks: dict[str, object] = field(default_factory=dict)


def exp_rate(p0: float, p1: float, years: float) -> float:
    """Average annual growth rate (%), exponential, as DCS uses in Final Report Table 3.3."""
    return 100 * math.log(p1 / p0) / years


def classify(
    ds12: pd.DataFrame,
    gn_m: pd.DataFrame,
    gn24: pd.DataFrame,
    ds24_spine: dict[str, str],
) -> Result:
    """Classify each DS 2012 -> 2024 change from GN flows and build relations and comparisons."""
    units12 = records(ds12)
    gns12 = records(gn_m)
    gns24 = records(gn24)
    name12 = {u["ds_2012"]: str(u["name"]) for u in units12}
    total12 = {u["ds_2012"]: int(u["total"]) for u in units12}
    name24: dict[str, str] = {}
    district24: dict[str, int] = {}
    pop24: Counter[str] = Counter()
    n24: Counter[str] = Counter()
    for g in gns24:
        name24[g["dcs_ds"]] = str(g["ds_name"])
        district24[g["dcs_ds"]] = int(g["district_code"])
        pop24[g["dcs_ds"]] += int(g["population_total"])
        n24[g["dcs_ds"]] += 1
    n12: Counter[str] = Counter(g["ds_2012"] for g in gns12)
    un12: Counter[str] = Counter(g["ds_2012"] for g in gns12 if g["gn_2024"] is None)
    matched24 = {g["gn_2024"] for g in gns12 if g["gn_2024"] is not None}
    un24_rows = [g for g in gns24 if g["dcs_gn"] not in matched24]
    un24: Counter[str] = Counter(g["dcs_ds"] for g in un24_rows)

    flow_n: Counter[tuple[str, str]] = Counter()
    flow_p: Counter[tuple[str, str]] = Counter()
    for g in gns12:
        if g["gn_2024"] is not None:
            flow_n[(g["ds_2012"], g["ds_2024"])] += 1
            flow_p[(g["ds_2012"], g["ds_2024"])] += int(g["total"] or 0)
    flows: list[Rec] = []
    for (i, j), n in sorted(flow_n.items()):
        s12, s24 = n / n12[i], n / n24[j]
        flows.append(dict(ds_2012=i, name_2012=name12[i], ds_2024=j, name_2024=name24[j],
                          gn_count=n, pop_2012=flow_p[(i, j)], share_of_2012_gns=round(s12, 4),
                          share_of_2024_gns=round(s24, 4),
                          major=s12 >= MINOR or s24 >= MINOR))  # fmt: skip
    succ: dict[str, list[str]] = defaultdict(list)
    pred: dict[str, list[str]] = defaultdict(list)
    for f in flows:
        if f["major"]:
            succ[f["ds_2012"]].append(f["ds_2024"])
            pred[f["ds_2024"]].append(f["ds_2012"])

    # Unit-level change types.
    t12: dict[str, str] = {}
    for i in name12:
        s = succ.get(i, [])
        if len(s) == 1 and len(pred[s[0]]) == 1:
            t12[i] = "unchanged" if norm(name12[i]) == norm(name24[s[0]]) else "renamed"
        elif len(s) > 1:
            t12[i] = "split"
        elif len(s) == 1:
            t12[i] = "merged"
        else:
            t12[i] = "no_successor"
    t24: dict[str, str] = {}
    for j in name24:
        p = pred.get(j, [])
        if len(p) > 1:
            t24[j] = "merged"
        elif len(p) == 1:
            if t12[p[0]] in ONE_TO_ONE:
                t24[j] = t12[p[0]]
            elif norm(name12[p[0]]) == norm(name24[j]):
                t24[j] = "split_remainder"
            else:
                t24[j] = "new"
        else:
            t24[j] = "no_predecessor"
    # A minor flow (a GN transfer) marks both ends, and the units they otherwise map to, as
    # boundary-adjusted when they would otherwise be one-to-one.
    for f in flows:
        if f["major"]:
            continue
        for i in (f["ds_2012"], *pred.get(f["ds_2024"], [])):
            if t12.get(i) in ONE_TO_ONE:
                t12[i] = "boundary_adjusted"
        for j in (f["ds_2024"], *succ.get(f["ds_2012"], [])):
            if t24.get(j) in ONE_TO_ONE:
                t24[j] = "boundary_adjusted"
    for f in flows:
        a, b = t12[f["ds_2012"]], t24[f["ds_2024"]]
        if not f["major"]:
            f["change_type"] = "boundary_adjusted"
        elif a == "split":
            f["change_type"] = "split"
        elif b == "merged":
            f["change_type"] = "merged"
        elif "boundary_adjusted" in (a, b):
            f["change_type"] = "boundary_adjusted"
        else:
            f["change_type"] = a

    # Identity (data-model §3.3): split or merged 2012 units are retired and get a vintage id;
    # every other 2012 unit continues under its 2024 successor's spine id.
    gid12: dict[str, str | None] = {}
    for i in name12:
        if t12[i] in ("split", "merged", "no_successor"):
            gid12[i] = f"LK-ADM3-V2012-{i}"
        else:
            gid12[i] = ds24_spine.get(succ[i][0])
    for u in units12:
        i = u["ds_2012"]
        u.update(change_type=t12[i], geography_id=gid12[i], successors=";".join(succ.get(i, [])),
                 gn_count=n12[i], gn_unmatched=un12[i])  # fmt: skip
    units24: list[Rec] = [
        dict(dcs_ds=j, ds_name=name24[j], district_code=district24[j], gn_count=n24[j],
             pop_2024=pop24[j], change_type=t24[j], geography_id=ds24_spine.get(j),
             predecessors=";".join(pred.get(j, [])), gn_unmatched=un24[j])
        for j in sorted(name24)
    ]  # fmt: skip

    # Succession relations, only where identity changes (from a retired 2012 unit).
    pop12_from: Counter[str] = Counter()
    pop12_on24: Counter[str] = Counter()
    for f in flows:
        pop12_from[f["ds_2012"]] += f["pop_2012"]
        pop12_on24[f["ds_2024"]] += f["pop_2012"]
    rel: list[Rec] = []
    for f in flows:
        a, b = gid12[f["ds_2012"]], ds24_spine.get(f["ds_2024"])
        if not a or not b or not a.startswith("LK-ADM3-V2012-"):
            continue
        note = (f"{f['gn_count']} GNs; DCS 2012 DS '{f['name_2012']}' -> DCS 2024 DS "
                f"{f['ds_2024']} '{f['name_2024']}'; {f['change_type']}; weight = share of "
                "2012 population (GN rows of the DCS 2012 file)")  # fmt: skip
        w_s = f["pop_2012"] / pop12_from[f["ds_2012"]] if pop12_from[f["ds_2012"]] else None
        w_p = f["pop_2012"] / pop12_on24[f["ds_2024"]] if pop12_on24[f["ds_2024"]] else None
        for gid, rid, kind, w in ((a, b, "succeeded_by", w_s), (b, a, "preceded_by", w_p)):
            rel.append(dict(geography_id=gid, related_id=rid, relation=kind, vintage="2012-2024",
                            weight=None if w is None else round(w, 6), method="official_list",
                            source="census-2012-tables;census-2024-gnd-tables",
                            valid_from="2012-03-20" if kind == "succeeded_by" else "",
                            valid_to="", notes=note))  # fmt: skip

    # Comparison table, one row per 2024 DS.
    comp: list[Rec] = []
    for u in units24:
        j, preds = u["dcs_ds"], pred.get(u["dcs_ds"], [])
        one = u["change_type"] in ONE_TO_ONE and len(preds) == 1
        if one and u["gn_unmatched"] == 0 and un12[preds[0]] == 0:
            p, label, method = total12[preds[0]], "exact", "same_gn_list"
            reason = "every GN matched one-to-one between the DCS 2012 and 2024 lists"
        elif one:
            # Same unit, but some GNs could not be matched, so a transfer cannot be ruled
            # out. DCS's own DS total is used; the label stays approximate.
            p, label, method = total12[preds[0]], "approximate", "same_ds_total_gns_unverified"
            reason = f"{u['gn_unmatched'] + un12[preds[0]]} GNs unmatched (both sides)"
        else:
            p, label, method = pop12_on24[j], "approximate", "gn_reaggregation"
            reasons = [] if u["change_type"] in ONE_TO_ONE else [u["change_type"]]
            if u["gn_unmatched"]:
                reasons.append(f"{u['gn_unmatched']} 2024 GNs unmatched")
            if any(un12[x] for x in preds):
                reasons.append("2012 GNs unmatched in a predecessor")
            reason = "; ".join(reasons) or "GN-level rebuild"
        change = u["pop_2024"] - p
        comp.append(dict(dcs_ds=j, ds_name=u["ds_name"], district_code=u["district_code"],
                         geography_id=u["geography_id"], change_type=u["change_type"],
                         predecessors=u["predecessors"], pop_2012=p, pop_2024=u["pop_2024"],
                         change=change, growth_pct=round(100 * change / p, 2) if p else None,
                         annual_rate_pct=round(exp_rate(p, u["pop_2024"], YEARS), 2) if p else None,
                         comparison=label, method=method, reason=reason))  # fmt: skip

    # Comparison groups: connected components of the flow graph (major and minor flows).
    parent: dict[str, str] = {}

    def find(x: str) -> str:
        while parent.setdefault(x, x) != x:
            x = parent[x]
        return x

    for f in flows:
        parent[find("a" + f["ds_2012"])] = find("b" + f["ds_2024"])
    members: dict[str, list[str]] = defaultdict(list)
    for node in list(parent):
        members[find(node)].append(node)
    groups: list[Rec] = []
    for nodes in members.values():
        a = sorted(n[1:] for n in nodes if n[0] == "a")
        b = sorted(n[1:] for n in nodes if n[0] == "b")
        if len(a) == 1 and len(b) == 1:
            continue
        un = sum(un12[x] for x in a) + sum(un24[x] for x in b)
        p_a, p_b = sum(total12[x] for x in a), sum(pop24[x] for x in b)
        method = "closed_gn_group" + (f"; {un} GNs unmatched" if un else "")
        groups.append(dict(ds_2012=";".join(a), names_2012="; ".join(name12[x] for x in a),
                           ds_2024=";".join(b), names_2024="; ".join(name24[x] for x in b),
                           pop_2012=p_a, pop_2024=p_b, change=p_b - p_a,
                           annual_rate_pct=round(exp_rate(p_a, p_b, YEARS), 2),
                           comparison="exact" if un == 0 else "approximate",
                           method=method))  # fmt: skip
    return Result(
        units_2012=pd.DataFrame(units12),
        units_2024=pd.DataFrame(units24),
        flows=pd.DataFrame(flows),
        relations=pd.DataFrame(rel),
        comparison=pd.DataFrame(comp),
        groups=pd.DataFrame(groups),
        gn_matches=gn_m,
        unmatched_2024=pd.DataFrame(un24_rows),
    )


# --- District series --------------------------------------------------------------------------

# Creations recorded by DCS (Abstract 2024 Table 2.1 note; Final Report 2024 Table 2.1).
DISTRICT_CREATIONS = {
    "Gampaha": "carved out in September 1978 (Abstract 2024 Table 2.1 note)",
    "Mullaitivu": "carved out in September 1978 (Abstract 2024 Table 2.1 note)",
    "Kilinochchi": "carved out in February 1984 (Abstract 2024 Table 2.1 note)",
}


def district_series(transcription: pd.DataFrame, t33: pd.DataFrame) -> pd.DataFrame:
    """Long table of district populations by census year with a comparability label.

    `comparison_to_2024` is `exact` only for 2012 (the 25 districts have not changed since
    2001, Final Report 2024 §2.2.2, and GN counts per district are the same in Tables 2.3 and
    2.4 except Matale's 13 reservoir GNs). 2001 is `exact` too except where DCS estimated the
    figure. Every earlier year is `approximate`: district boundaries before 2001 are not shown to
    equal today's, and DCS records districts being created and abolished.
    """
    rows = []
    years = [c for c in transcription.columns if c != "district"]
    for r in transcription.to_dict("records"):
        d = r["district"]
        for y in years:
            v = r[y]
            yi = int(y)
            if v == "..":
                status, val = "not_available", None
            else:
                status, val = "normal", round(float(v) * 1000)
            estimated = yi == 2001 and d in {
                "Jaffna",
                "Mannar",
                "Vavuniya",
                "Mullaitivu",
                "Kilinochchi",
                "Batticaloa",
                "Trincomalee",
            }
            if d == "Sri Lanka" or yi >= 2012 or (yi == 2001 and not estimated):
                comp = "exact"
            else:
                comp = "approximate"
            if d == "Chilaw":
                comp = "not_comparable"
            rows.append(
                dict(
                    district=d,
                    year=yi,
                    population=val,
                    unit="persons (rounded from thousands)",
                    value_status="estimate" if estimated else status,
                    source="DCS Statistical Abstract 2024, Table 2.1",
                    page=1,
                    comparison_to_2024=comp,
                    note=DISTRICT_CREATIONS.get(d, ""),
                )
            )
    for r in t33.to_dict("records"):
        for y, v in (
            (1981, r["p1981"]),
            (2001, r["p2001"]),
            (2012, r["p2012"]),
            (2024, r["p2024"]),
        ):
            if v is None or (isinstance(v, float) and math.isnan(v)):
                continue
            comp = "exact" if y >= 2012 or (y == 2001) else "approximate"
            note = ""
            if y == 1981:
                note = (
                    (
                        "DCS: Jaffna and Kilinochchi 1981 are presented on current boundaries "
                        "(Table 3.3 note 2)"
                    )
                    if r["district"] in ("Jaffna", "Kilinochchi")
                    else ""
                )
            rows.append(
                dict(
                    district=r["district"],
                    year=y,
                    population=int(v),
                    unit="persons",
                    value_status="normal",
                    source="DCS Census 2024 Final Report, Table 3.3",
                    page=69,
                    comparison_to_2024=comp,
                    note=note,
                )
            )
    return pd.DataFrame(rows)


# --- Checks -----------------------------------------------------------------------------------


def check_transcription(transcription: pd.DataFrame, page_text: str) -> dict[str, object]:
    """Every transcribed value must occur in the PDF text layer; columns must add up."""
    pool = Counter(v.replace(",", "") for v in re.findall(r"\d[\d,]*\.\d|\b150\b", page_text))
    need: Counter[str] = Counter()
    for c in transcription.columns[1:]:
        need.update(v for v in transcription[c] if v != "..")
    missing = need - pool
    totals = {}
    nat = transcription[transcription["district"] == "Sri Lanka"].iloc[0]
    rest = transcription[transcription["district"] != "Sri Lanka"]
    for c in transcription.columns[1:]:
        s = sum(float(v) for v in rest[c] if v != "..")
        totals[c] = round(s - float(nat[c]), 1)
    return {
        "values": sum(need.values()),
        "missing_from_text_layer": dict(missing),
        "column_sum_minus_total": totals,
    }


# --- Orchestration ----------------------------------------------------------------------------

PDF_PAGES = {
    # name: (snapshot dataset prefix, file, pages needed)
    "gn2012": ("raw/nuuuwan/nuuuwan-lk-census-2012", "population-gender_source.pdf", "all"),
    "abstract27": ("raw/dcs/census-2012-tables", "abstract2024_table2.7.pdf", "all"),
    "abstract21": ("raw/dcs/census-district-series", "abstract2024_table2.1.pdf", "1"),
    "fr2024": ("raw/dcs/census-2024-gnd-tables", "CPH2024_Final_Eng.pdf", "60 63 64 67 69"),
}


@dataclass
class Run:
    rows12: Rows2012
    result: Result
    series: pd.DataFrame
    t33: pd.DataFrame
    t31: pd.DataFrame
    refs: dict[str, SnapshotRef]
    checks: dict[str, object]


def run(storage: Storage, pages_root: Path, catalog: Path) -> Run:
    from slf.datasets.census_2024_gnd import _crosswalk, _latest, parse_population

    refs = {k: latest_snapshot(storage, prefix, f) for k, (prefix, f, _) in PDF_PAGES.items()}
    refs["gn2024"] = _latest(storage, "GN_population.xlsx")
    rows12 = parse_gn_2012(pages_root / "gn2012")
    gn24 = parse_population(storage, refs["gn2024"])
    _, ds_map = _crosswalk(catalog)
    fr = pages_root / "fr2024"
    t33 = parse_table_3_3((fr / "page-069.txt").read_text("utf-8"))
    t31 = parse_table_3_1((fr / "page-067.txt").read_text("utf-8"))
    t23 = parse_table_2_3((fr / "page-063.txt").read_text("utf-8"))
    gn_m = match_gns(rows12.gn, gn24)
    result = classify(rows12.ds, gn_m, gn24, ds_map)

    transcription = pd.read_csv(
        catalog / "references" / "dcs-abstract2024-table2.1-transcription.csv", dtype=str
    )
    series = district_series(transcription, t33)

    # Checks (G06 "Verify").
    checks: dict[str, object] = {}
    t33r = records(t33)
    fr12 = {r["district"]: r["p2012"] for r in t33r}
    fr24 = {r["district"]: r["p2024"] for r in t33r}
    ds12r, gn12r, gnmr = records(rows12.ds), records(rows12.gn), records(gn_m)
    comp = records(result.comparison)
    checks["national_2012_gn_file"] = rows12.national["total"]
    checks["national_2012_table_3_3"] = fr12.get("Sri Lanka")
    checks["national_2012_ds_sum"] = sum(int(r["total"]) for r in ds12r)
    checks["districts_2012_differing_from_table_3_3"] = {
        r["district"]: (r["total"], fr12.get(r["district"]))
        for r in records(rows12.districts)
        if r["total"] != fr12.get(r["district"])
    }
    by_d24: Counter[str] = Counter()
    for g in records(gn24):
        by_d24[str(g["district_name"])] += int(g["population_total"])
    checks["national_2024_gn_workbook"] = sum(by_d24.values())
    checks["national_2024_table_3_3"] = fr24.get("Sri Lanka")
    checks["national_2024_ds_sum"] = sum(int(r["pop_2024"]) for r in comp)
    checks["districts_2024_differing_from_table_3_3"] = {
        d: (v, fr24.get(d)) for d, v in by_d24.items() if v != fr24.get(d)
    }
    checks["comparison_pop_2012_sum"] = sum(int(r["pop_2012"]) for r in comp)
    checks["ds_2012_count"] = len(ds12r)
    checks["ds_2012_count_table_2_3"] = t23.get("Total")
    per_d = Counter(str(r["district"]) for r in ds12r)
    checks["ds_2012_count_by_district_differing"] = {
        d: (n, t23.get(d)) for d, n in per_d.items() if n != t23.get(d)
    }
    checks["ds_2024_count"] = len(result.units_2024)
    pool = Counter((t, m, f) for t, m, f, _ in parse_abstract_ds_triples(pages_root / "abstract27"))
    missing = [
        f"{r['name']} ({r['district']}) {r['total']}"
        for r in ds12r
        if pool[(r["total"], r["male"], r["female"])] == 0
    ]
    checks["ds_2012_rows_in_abstract_2_7"] = len(ds12r) - len(missing)
    checks["ds_2012_rows_missing_from_abstract_2_7"] = missing
    checks["gn_2012_rows"] = len(gn12r)
    checks["gn_2012_rows_without_figures"] = sum(1 for g in gn12r if g["total"] is None)
    checks["gn_2012_matched_by_layer"] = dict(
        Counter(str(g["match_layer"] or "unmatched") for g in gnmr)
    )
    checks["gn_2024_rows"] = len(gn24)
    checks["gn_2024_unmatched"] = len(result.unmatched_2024)
    un12 = [g for g in gnmr if g["gn_2024"] is None]
    checks["gn_2012_unmatched_in_matale"] = sum(1 for g in un12 if g["district_code"] == 22)
    checks["gn_2012_unmatched_population"] = sum(int(g["total"] or 0) for g in un12)
    checks["unparsed_lines_2012"] = rows12.unparsed
    a21 = (pages_root / "abstract21" / "page-001.txt").read_text("utf-8").replace("W25.1", "25.1")
    checks["abstract_2_1_transcription"] = check_transcription(transcription, a21)
    # Does our exponential rate reproduce DCS's published 2012-2024 district rates?
    rate_diff = {}
    for r in t33r:
        ours = round(exp_rate(r["p2012"], r["p2024"], YEARS), 1)
        if abs(ours - r["rate_2012_2024"]) > 0.05:
            rate_diff[r["district"]] = (ours, r["rate_2012_2024"])
    checks["rate_formula_differs_from_table_3_3"] = rate_diff
    result.checks = checks
    return Run(rows12, result, series, t33, t31, refs, checks)


RESERVOIR_NOTE = (
    "Matale: 13 of 545 GNs removed for the Kalu Ganga and Moragahakanda reservoirs "
    "(Final Report 2024, Table 2.4 note 1)"
)


def unmatched_rows(res: Result) -> list[Rec]:
    """Unmatched GNs from both lists, with a documented reason where one exists."""
    out: list[Rec] = []
    for g in records(res.gn_matches):
        if g["gn_2024"] is not None:
            continue
        reason = ""
        if g["district_code"] == 22:
            reason = RESERVOIR_NOTE
        elif g["total"] is None:
            reason = "listed by DCS in 2012 without figures"
        out.append(dict(side="2012", district_code=g["district_code"], ds=g["ds_2012"],
                        name=g["name"], gn_number=g["gn_number_printed"], total=g["total"],
                        locator=f"page {g['page']} line {g['line']}",
                        explanation=reason))  # fmt: skip
    for g in records(res.unmatched_2024):
        out.append(dict(side="2024", district_code=g["district_code"], ds=g["dcs_ds"],
                        name=g["gn_name"], gn_number=g["gn_number"], total=g["population_total"],
                        locator=f"GN_population.xlsx row {g['line']} (DCS GN {g['dcs_gn']})",
                        explanation=""))  # fmt: skip
    return out


def write(r: Run, out_dir: Path, relations_csv: Path, qa_dir: Path) -> list[Path]:
    """Write build outputs, the catalogue relations and the reviewable QA tables."""
    out_dir.mkdir(parents=True, exist_ok=True)
    qa_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    res = r.result
    tables = {
        "ds_2012_units.csv": res.units_2012,
        "ds_2024_units.csv": res.units_2024,
        "ds_flows_2012_2024.csv": res.flows,
        "ds_comparison_2012_2024.csv": res.comparison,
        "ds_comparison_groups_2012_2024.csv": res.groups,
        "district_census_series.csv": r.series,
    }
    for name, df in tables.items():
        for d in (out_dir, qa_dir):
            p = d / name
            df.to_csv(p, index=False)
            written.append(p)
    gm = out_dir / "gn_matches_2012_2024.csv"
    res.gn_matches.to_csv(gm, index=False)
    un = qa_dir / "gn_unmatched_2012_2024.csv"
    pd.DataFrame(unmatched_rows(res)).to_csv(un, index=False)
    relations_csv.parent.mkdir(parents=True, exist_ok=True)
    res.relations.to_csv(relations_csv, index=False)
    checks = out_dir / "checks.json"
    checks.write_text(json.dumps(r.checks, indent=1, default=str) + "\n", encoding="utf-8")
    sources = out_dir / "sources.json"
    sources.write_text(
        json.dumps({k: v.__dict__ for k, v in r.refs.items()}, indent=1) + "\n", encoding="utf-8"
    )
    return [*written, gm, un, relations_csv, checks, sources]
