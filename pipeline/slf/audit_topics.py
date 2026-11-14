"""Q01 machine re-trace for the Census 2024 topic tables (``census-2024-topic-tables``, D-032).

Like ``slf.audit``, this is deliberately independent of the ingest code
(``slf.datasets.census_2024_topics`` and friends). For each sampled value it parses the
``source_locator``, opens the raw snapshot by its sha256, and:

- for a cell locator, reads that cell (Excel row and column letter);
- for a derived share, reads the numerator and denominator cells and divides;
- for a GN sum ("N GN rows summed to ds 1103"), selects the raw GN rows by the DCS codes in the
  workbook's own code columns, checks there are N of them, and sums the indicator's column;
- for an A-series province sum ("district rows 11, 27 summed to province 1"), sums those rows.

Which column an aggregate value comes from is not in its locator, so it is taken from the same
indicator's cell locators in the release; those cells are themselves re-traced.

It also checks the place file the website reads: indicators with ``distribution:
downloads_only`` must be absent from it, all others present with the same value. And it checks
that ethnicity and religion (D-033) appear at no GN.

A machine re-trace is not human verification (AGENTS rule 7).
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd

from slf.audit import _nan_to_none, count_true, find_snapshot, level_of

DATASET = "census-2024-topic-tables"
SEED = 20261112
QUOTA = 1  # values per indicator at each level
SHARE_TOL = 5.1e-5  # shares are published to 4 decimals

CELL_RE = re.compile(
    r"^(?P<file>[^,]+\.xlsx), sheet '(?P<sheet>[^']+)', row (?P<row>\d+), "
    r"column (?P<col>[A-Z]+)(?: \('.*'\)| ÷ column (?P<den>[A-Z]+); derived share)$"
)
GN_SUM_RE = re.compile(
    r"^(?P<file>[^,]+\.xlsx), sheet '(?P<sheet>[^']+)', (?P<n>\d+) GN rows summed to "
    r"(?P<level>ds|district|province|country) (?P<code>\w+); row range \d+-\d+"
    r"(?P<share>; derived share)?$"
)
ROWS_SUM_RE = re.compile(
    r"^(?P<file>[^,]+\.xlsx), sheet '(?P<sheet>[^']+)', district rows (?P<rows>[\d, ]+) "
    r"summed to province \d+(?P<share>; derived share)?$"
)
SENSITIVE = ("population_ethnicity_", "population_religion_")


def col_index(letter: str) -> int:
    """Excel letter -> 0-based index ('A' -> 0, 'J' -> 9)."""
    n = 0
    for ch in letter:
        n = n * 26 + ord(ch) - 64
    return n - 1


def _num(value: object) -> float:
    if isinstance(value, bool) or value is None:
        raise ValueError(f"not a number: {value!r}")
    if isinstance(value, int | float):
        return float(value)
    text = str(value).strip()
    if not re.fullmatch(r"-?\d+(\.\d+)?", text):
        raise ValueError(f"not a number: {value!r}")
    return float(text)


def _code(value: object) -> int | None:
    text = str(value).strip() if value is not None else ""
    return int(text) if text.isdigit() else None


@dataclass
class Workbooks:
    """Raw sheets, read once, keyed by (sha256, sheet). Rows are 1-based Excel rows."""

    raw_dir: Path
    paths: dict[str, Path] = field(default_factory=dict)
    sheets: dict[tuple[str, str], list[tuple[object, ...]]] = field(default_factory=dict)

    def rows(self, sha: str, sheet: str) -> list[tuple[object, ...]]:
        key = (sha, sheet)
        if key not in self.sheets:
            if sha not in self.paths:
                self.paths[sha] = find_snapshot(self.raw_dir, sha)
            wb = openpyxl.load_workbook(self.paths[sha], read_only=True, data_only=True)
            self.sheets[key] = [tuple(r) for r in wb[sheet].iter_rows(values_only=True)]
            wb.close()
        return self.sheets[key]

    def cell(self, sha: str, sheet: str, row: int, col: str) -> float:
        line = self.rows(sha, sheet)[row - 1]
        index = col_index(col)
        return _num(line[index] if index < len(line) else None)


def gn_rows(rows: list[tuple[object, ...]]) -> pd.DataFrame:
    """GN rows of a GN workbook, with DCS codes read from the workbook's own code columns.

    The households file has province, district, DS and GN code columns (A, C, E, G); the GN
    population topic files have district, DS and GN codes (A, C, E). A GN row is one whose GN
    code cell holds a number.
    """
    header = next(
        (i, r)
        for i, r in enumerate(rows)
        if r and str(r[0] or "").strip().startswith(("Prov", "Dist"))
    )
    has_province = str(header[1][0]).strip().startswith("Province")
    district_col, ds_col, gn_col = (2, 4, 6) if has_province else (0, 2, 4)
    out = []
    for i, r in enumerate(rows[header[0] + 1 :], start=header[0] + 2):
        if len(r) <= gn_col:
            continue
        district, ds, gn = _code(r[district_col]), _code(r[ds_col]), _code(r[gn_col])
        if district is None or ds is None or gn is None:
            continue
        out.append(
            {
                "excel_row": i,
                "province": _code(r[0]) if has_province else None,
                "district": district,
                "ds": district * 100 + ds,
            }
        )
    return pd.DataFrame(out)


@dataclass
class Columns:
    """Where an indicator's values come from in its workbook, learned from cell locators."""

    numerator: dict[tuple[str, str], str] = field(default_factory=dict)  # (file, ind) -> letter
    denominator: dict[tuple[str, str], str] = field(default_factory=dict)

    @classmethod
    def learn(cls, obs: pd.DataFrame) -> Columns:
        out = cls()
        cells = pd.DataFrame(obs[obs["source_locator"].str.match(CELL_RE)])
        firsts = cells.drop_duplicates(subset=["indicator_id", "file"])
        for loc, ind, file in zip(
            firsts["source_locator"], firsts["indicator_id"], firsts["file"], strict=True
        ):
            if m := CELL_RE.match(str(loc)):
                out.numerator[(str(file), str(ind))] = m["col"]
                if m["den"]:
                    out.denominator[(str(file), str(ind))] = m["den"]
        return out


def trace(
    row: pd.Series, books: Workbooks, columns: Columns, province_of: dict[int, int]
) -> tuple[float | None, str]:
    """Value recomputed from the raw snapshot, and how."""
    loc, ind, sha = (
        str(row["source_locator"]),
        str(row["indicator_id"]),
        str(row["snapshot_sha256"]),
    )
    if m := CELL_RE.match(loc):
        num = books.cell(sha, m["sheet"], int(m["row"]), m["col"])
        if not m["den"]:
            return num, f"cell {m['file']} {m['col']}{m['row']}"
        den = books.cell(sha, m["sheet"], int(m["row"]), m["den"])
        value = 100.0 * num / den if den else None
        return value, f"cells {m['col']}{m['row']} ÷ {m['den']}{m['row']} x 100"
    if m := GN_SUM_RE.match(loc):
        rows = books.rows(sha, m["sheet"])
        gn = gn_rows(rows)
        level, code = m["level"], m["code"]
        if level == "country":
            pick = gn
        elif level == "province":
            if bool(gn["province"].notna().all()):
                prov = gn["province"]
            else:
                prov = pd.Series([province_of.get(int(d)) for d in gn["district"]], index=gn.index)
            pick = gn[prov == int(code)]
        else:
            pick = gn[gn[level] == int(code)]
        if len(pick) != int(m["n"]):
            return None, f"{len(pick)} raw GN rows for {level} {code}, locator says {m['n']}"
        key = (m["file"], ind)
        num_col = columns.numerator.get(key)
        if num_col is None:
            return None, f"no cell locator for {ind} in {m['file']}"
        num = sum(books.cell(sha, m["sheet"], int(r), num_col) for r in pick["excel_row"])
        how = f"sum of {len(pick)} raw GN rows ({level} {code}), column {num_col}"
        if not m["share"]:
            return num, how
        den_col = columns.denominator[key]
        den = sum(books.cell(sha, m["sheet"], int(r), den_col) for r in pick["excel_row"])
        return (100.0 * num / den if den else None), f"{how} ÷ column {den_col}"
    if m := ROWS_SUM_RE.match(loc):
        lines = [int(x) for x in m["rows"].split(",")]
        key = (m["file"], ind)
        num_col = columns.numerator.get(key)
        if num_col is None:
            return None, f"no cell locator for {ind} in {m['file']}"
        num = sum(books.cell(sha, m["sheet"], r, num_col) for r in lines)
        how = f"sum of district rows {m['rows']}, column {num_col}"
        if not m["share"]:
            return num, how
        den_col = columns.denominator[key]
        den = sum(books.cell(sha, m["sheet"], r, den_col) for r in lines)
        return (100.0 * num / den if den else None), f"{how} ÷ column {den_col}"
    return None, f"locator not understood: {loc}"


def draw_sample(obs: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    """QUOTA values per indicator at each level where the indicator has values; every
    ``not_available`` value."""
    rng = np.random.default_rng(seed)
    parts = [obs[obs["value_status"] != "normal"].assign(stratum="every not_available value")]
    normal = obs[obs["value_status"] == "normal"]
    for _, group in normal.groupby(["indicator_id", "level"], sort=True):
        pick = rng.choice(len(group), size=min(QUOTA, len(group)), replace=False)
        parts.append(group.iloc[np.sort(pick)].assign(stratum=f"random {QUOTA} per indicator"))
    return pd.concat(parts).drop_duplicates("claim_id").reset_index(drop=True)


@dataclass
class TopicsResult:
    release: str
    published: int
    sample: pd.DataFrame
    snapshots: dict[str, str]  # file -> sha256
    sensitive_gn: int
    names: dict[str, str] = field(default_factory=dict)  # geography id -> English name
    warnings: list[str] = field(default_factory=list)


def run(release_dir: Path, raw_dir: Path, seed: int = SEED) -> TopicsResult | None:
    path = release_dir / "observations" / f"{DATASET}.parquet"
    if not path.exists():
        return None
    obs = pd.read_parquet(path)
    obs = obs.assign(
        level=obs["geography_id"].map(level_of),
        file=obs["source_locator"].str.extract(r"^([^,]+\.xlsx)", expand=False),
    )
    release = str(obs["release"].iloc[0])
    columns = Columns.learn(obs)
    books = Workbooks(raw_dir)

    hh_sha = str(obs.loc[obs["file"] == "HH_GND_excel.xlsx", "snapshot_sha256"].tolist()[0])
    hh_rows = gn_rows(books.rows(hh_sha, "Households"))
    province_of = dict(zip(hh_rows["district"], hh_rows["province"], strict=False))

    index = json.loads((release_dir / "api" / "v1" / "indicators.json").read_text("utf-8"))
    distribution = {i["id"]: i.get("distribution", "api") for i in index["indicators"]}
    places: dict[str, dict[str, float | None]] = {}

    sample = draw_sample(obs, seed)
    out = []
    for _, row in sample.iterrows():
        expected, how = trace(row, books, columns, province_of)
        published = _nan_to_none(row["value"])
        ind = str(row["indicator_id"])
        if published is None or expected is None:
            source_ok = published is None and expected is None and "understood" not in how
        elif "derived share" in str(row["source_locator"]):
            source_ok = abs(published - round(expected, 4)) <= SHARE_TOL
        else:
            source_ok = published == expected
        geo = str(row["geography_id"])
        if geo not in places:
            place = release_dir / "api" / "v1" / "places" / f"{geo}.json"
            values = json.loads(place.read_text("utf-8"))["values"] if place.exists() else []
            places[geo] = {v["indicator_id"]: v["value"] for v in values}
        in_api = ind in places[geo]
        if distribution.get(ind) == "downloads_only":
            api_ok = not in_api
        else:
            api_ok = in_api and places[geo][ind] == published
        out.append(
            {
                "claim_id": row["claim_id"],
                "level": row["level"],
                "geography_id": geo,
                "indicator_id": ind,
                "distribution": distribution.get(ind, "missing from indicators.json"),
                "stratum": row["stratum"],
                "published": published,
                "traced": expected,
                "trace_method": how,
                "in_place_file": in_api,
                "source_match": source_ok,
                "api_match": api_ok,
                "source_locator": row["source_locator"],
            }
        )
    result = pd.DataFrame(out)
    snapshots = {
        str(f): str(s)
        for f, s in obs.drop_duplicates("file")[["file", "snapshot_sha256"]].itertuples(index=False)
    }
    sensitive_gn = int(
        (obs["indicator_id"].str.startswith(SENSITIVE) & (obs["level"] == "gn")).sum()
    )
    warnings = []
    bad = result[~(result["source_match"] & result["api_match"])]
    if len(bad):
        warnings.append(f"{len(bad)} sampled topic-table values failed the re-trace or API check")
    if sensitive_gn:
        warnings.append(f"{sensitive_gn} ethnicity or religion values at GN level (D-033)")
    admin = release_dir / "api" / "v1" / "geographies" / "admin.json"
    names: dict[str, str] = {}
    if admin.exists():
        for g in json.loads(admin.read_text("utf-8"))["geographies"]:
            names[str(g["geography_id"])] = str(g["name_en"])
    return TopicsResult(release, len(obs), result, snapshots, sensitive_gn, names, warnings)


STEP_FILES = (  # one confirmation value per D-032 step: (step, file prefix, level)
    ("a", "HH_GND_excel", "gn"),
    ("b", "GN_Level_Population_by_", "gn"),
    ("c", "HousingA_", "ds"),
    ("d", "PopulationA_", "ds"),
)


def lead_rows(res: TopicsResult, first_check: int, seed: int = SEED) -> pd.DataFrame:
    """One count per D-032 step for the lead to read in the raw workbook (Q01 sheet rows).

    Only sampled count cells that passed the re-trace are offered, so the lead checks the
    published value, not a value already known to be wrong.
    """
    rng = np.random.default_rng(seed + 2)
    s = res.sample
    ok = s["trace_method"].str.startswith("cell ") & s["source_match"] & s["api_match"]
    cells = pd.DataFrame(s[ok & (s["published"].fillna(0) > 0)])
    rows: list[dict[str, object]] = []
    for step, prefix, level in STEP_FILES:
        pool = pd.DataFrame(
            cells[cells["source_locator"].str.startswith(prefix) & (cells["level"] == level)]
        )
        if pool.empty:
            continue
        r = pool.iloc[int(rng.integers(len(pool)))]
        m = CELL_RE.match(str(r["source_locator"]))
        assert m
        rows.append(
            {
                "check": first_check + len(rows),
                "geography_id": r["geography_id"],
                "place": res.names.get(str(r["geography_id"]), ""),
                "indicator_id": r["indicator_id"],
                "published_value": r["published"],
                "where_to_look": f"{m['file']}, sheet '{m['sheet']}', cell {m['col']}{m['row']}",
                "how": f"D-032 step ({step}); locator: {r['source_locator']}",
                "lead_reads": "",
                "matches": "",
            }
        )
    return pd.DataFrame(rows)


def _fmt(v: object) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "n/a"
    f = float(v)  # type: ignore[arg-type]
    return f"{int(f):,}" if f.is_integer() else f"{f:,.4f}"


def render(res: TopicsResult) -> str:
    s = res.sample
    errors = s[~(s["source_match"] & s["api_match"])]
    ok = len(errors) == 0 and res.sensitive_gn == 0
    lines = [
        "",
        "## Topic tables (`census-2024-topic-tables`, D-032)",
        "",
        f"- **Machine re-trace: {'PASS' if ok else 'FAIL'}** ({len(errors)} of {len(s)} sampled "
        f"values failed). Generated by `slf.audit_topics`, independent of the ingest code.",
        f"- Sample: {QUOTA} value per indicator at each level where it has values, plus every "
        f"`not_available` value; **{len(s):,}** of {res.published:,} published values, "
        f"{s['indicator_id'].nunique()} indicators. Seed {SEED}.",
        "- Cells are read at the locator's Excel row and column; shares are recomputed from the "
        "two cells; GN sums select raw rows by the DCS codes in the workbook's own code columns "
        "and check the row count; A-series province sums add the named district rows. Counts "
        f"must match exactly, shares within {SHARE_TOL}.",
        "- Place-file check: `downloads_only` indicators must be absent from "
        "`api/v1/places/{id}.json`; all others present with the published value.",
        f"- Ethnicity or religion values at GN level (D-033): **{res.sensitive_gn}** in the whole "
        "release.",
        "- The lead confirmation sheet gains one count per D-032 step (cells in the raw "
        "workbooks), after the GN dataset's 20 values.",
        "",
        "| Level | Sampled | Re-trace errors | Place-file errors |",
        "|---|---|---|---|",
    ]
    order = ["country", "province", "district", "ds", "gn", "provisional"]
    for level in order:
        part = s[s["level"] == level]
        if len(part):
            lines.append(
                f"| {level} | {len(part)} | {count_true(~part['source_match'])} | "
                f"{count_true(~part['api_match'])} |"
            )
    lines += ["", "| Source file | Sampled |", "|---|---|"]
    files = s["source_locator"].str.extract(r"^([^,]+\.xlsx)", expand=False)
    for name, n in files.value_counts().sort_index().items():
        lines.append(f"| `{name}` (sha256 `{res.snapshots.get(str(name), '?')[:12]}`) | {n} |")
    lines += ["", "### Topic-table errors", ""]
    if len(errors):
        lines += [
            "| Claim | Published | Traced | In place file | Method |",
            "|---|---|---|---|---|",
        ]
        for _, r in errors.iterrows():
            lines.append(
                f"| `{r['claim_id']}` | {_fmt(r['published'])} | {_fmt(r['traced'])} | "
                f"{r['in_place_file']} | {r['trace_method']} |"
            )
    else:
        lines.append("None.")
    lines += [
        "",
        f"Per-value results: `accuracy-audit-{res.release}-topics-sample.csv` ({len(s)} rows).",
    ]
    return "\n".join(lines) + "\n"
