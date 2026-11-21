# ruff: noqa: E501
"""Statistical tables from held official sources: HIES poverty, LFS labour force, paddy (Stage 3).

Three datasets, each a published table read from a snapshot already held under ``raw/``:

- ``hies-poverty``: DCS "Poverty Indicators 2019", Table 04 (headcount index, number of poor and
  contribution to total poverty by sector, province and district; two poverty lines).
- ``labour-force-survey``: DCS Labour Force Survey Annual Report 2024, Tables 12, 12A and 12B
  (labour force status of the population aged 15+ by district; both sexes, male, female).
- ``paddy-statistics``: DCS paddy statistics by district, Maha 2010/11 and Yala 2012, read from the
  data.gov.lk CSV copies (the CSV's season is checked against the DCS PDF title page).

Rules applied (AGENTS.md): every row names its snapshot sha256 and a locator (page/table/row or
CSV row/column); geography joins only through the reviewed match file
``catalog/geographies/name-matches/dcs-statistical-tables-districts.csv`` (never by name at build
time) and every target must exist in the geography spine; source units that are not spine places
(Mahaweli 'H', Uda Walawe paddy management areas) are listed as unmatched, not dropped; values are
``machine_extracted``. Rights for all three sources are unclear and none carries a ``publication``
decision, so the release builder refuses them; this module only writes a private build folder.

PDF text comes from ``swift scripts/pdf_pages.swift <pdf> <out_dir> <pages...>`` (macOS), which
writes ``page-NNN.txt`` from the PDF's own text layer.
"""

from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from slf.dataset import Row, check_observations

MATCH_FILE = ("geographies", "name-matches", "dcs-statistical-tables-districts.csv")
SPINE_VINTAGE = "cod-ab-v03"
NUM = r"-?[\d,]+(?:\.\d+)?"


def _num(text: str) -> float:
    return float(text.replace(",", ""))


# --- Geography matching ---------------------------------------------------------------------


@dataclass(frozen=True)
class GeoMatch:
    geography_id: str
    method: str


def load_matches(catalog_root: Path, dataset_id: str) -> dict[str, GeoMatch]:
    """Source label -> spine id for one dataset, from the reviewed match file."""
    path = catalog_root.joinpath(*MATCH_FILE)
    out: dict[str, GeoMatch] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if dataset_id in r["datasets"].split(";"):
                if r["source_label"] in out:
                    raise ValueError(f"{path.name}: {r['source_label']!r} listed twice")
                out[r["source_label"]] = GeoMatch(r["geography_id"], r["match_method"])
    return out


def load_spine_ids(spine_dir: Path) -> dict[str, str]:
    """Geography id -> English name for country, province and district levels of the spine."""
    import pyarrow.parquet as pq

    table = pq.read_table(
        spine_dir / "geographies.parquet", columns=["geography_id", "level", "name_en"]
    )
    return {r["geography_id"]: r["name_en"] for r in table.to_pylist() if r["level"] <= 2}


# --- Snapshot lookup ------------------------------------------------------------------------


@dataclass(frozen=True)
class Snap:
    path: Path
    sha256: str
    url: str | None
    retrieved_at: str

    @property
    def key(self) -> str:
        return self.path.name


def find_snapshot(raw_root: Path, source: str, dataset: str, filename: str) -> Snap:
    """Latest snapshot of ``filename``; the sha256 is re-computed, not trusted from the meta file."""
    base = raw_root / source / dataset
    hits = sorted(base.glob(f"*/{filename}"))
    if not hits:
        raise FileNotFoundError(f"no snapshot of {filename} under {base}")
    path = hits[-1]
    meta_path = path.with_name(path.name + ".meta.json")
    meta: dict[str, Any] = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if meta.get("sha256") and meta["sha256"] != digest:
        raise ValueError(f"{path}: sha256 differs from its .meta.json (file changed?)")
    return Snap(path, digest, meta.get("url"), meta.get("retrieved_at", path.parent.name))


# --- Unmatched / QA bookkeeping --------------------------------------------------------------


@dataclass
class Result:
    dataset_id: str
    rows: list[Row] = field(default_factory=list)
    unmatched: list[str] = field(default_factory=list)  # source units with no spine place
    notes: list[str] = field(default_factory=list)  # QA facts, shown in the report
    checks: list[tuple[str, bool, str]] = field(default_factory=list)  # name, passed, detail
    not_ingested: list[str] = field(default_factory=list)  # held-but-skipped inputs and why


def _row(
    *,
    dataset_id: str,
    indicator: str,
    geography_id: str,
    period: str,
    time_start: dt.date,
    time_end: dt.date,
    time_support: str,
    value: float | None,
    unit: str,
    universe: str,
    collection_method: str,
    data_nature: str,
    snap: Snap,
    locator: str,
    breakdown: dict[str, str] | None = None,
    note: str,
    revision_status: str = "final",
) -> Row:
    tag = (
        ""
        if breakdown is None
        else ":" + ",".join(f"{k}={v}" for k, v in sorted(breakdown.items()))
    )
    return {
        "claim_id": f"{dataset_id}:{geography_id}:{indicator}:{period}{tag}",
        "indicator_id": indicator,
        "geography_id": geography_id,
        "geography_vintage": SPINE_VINTAGE,
        "period": period,
        "time_start": time_start.isoformat(),
        "time_end": time_end.isoformat(),
        "time_support": time_support,
        "support_type": "area_total",
        "footprint_ref": geography_id,
        "information_footprint_ref": geography_id,
        "universe": universe,
        "collection_method": collection_method,
        "sensitivity": "public",
        "revision_status": revision_status,
        "preferred": True,
        "preferred_reason": f"Only claim for this table in {dataset_id}.",
        "breakdown": breakdown,
        "value": value,
        "value_status": "normal" if value is not None else "not_available",
        "unit": unit,
        "data_nature": data_nature,
        "verification": "machine_extracted",
        "dataset_id": dataset_id,
        "snapshot_sha256": snap.sha256,
        "source_locator": locator,
        "note_ids": [],
        "release": None,
        "extraction_note": note,
    }


# --- HIES poverty 2019, Table 04 ------------------------------------------------------------

HIES_ID = "hies-poverty"
HIES_FILE = "PovertyIndicators-2019.pdf"
HIES_PAGE = 4
HIES_INDICATORS: tuple[tuple[str, str, str], ...] = (
    # (indicator, unit, column group); columns in the table: OldPL (head, number, share), UPL (...)
    ("poverty_headcount_old_pl", "percent", "old:0"),
    ("poor_population_old_pl", "persons", "old:1"),
    ("poverty_contribution_old_pl", "percent", "old:2"),
    ("poverty_headcount_updated_pl", "percent", "upl:0"),
    ("poor_population_updated_pl", "persons", "upl:1"),
    ("poverty_contribution_updated_pl", "percent", "upl:2"),
)
_HIES_ROW = re.compile(rf"^(?P<label>[A-Za-z' .]+?)\s+((?:{NUM})(?:\s+(?:{NUM})){{5}})\s*$")
SECTORS = {"Urban": "urban", "Rural": "rural", "Estate": "estate"}


def parse_hies_table04(text: str) -> list[tuple[str, str, int, list[float]]]:
    """(section, label, line_no, six numbers) for each data row of Table 04.

    Sections: country, sector, province, district. Raises if the table title is missing.
    """
    lines = text.splitlines()
    if not any(ln.startswith("Table 04: Poverty headcount index") for ln in lines):
        raise ValueError("Table 04 title not found on the page")
    out: list[tuple[str, str, int, list[float]]] = []
    section = "country"
    for n, raw in enumerate(lines, start=1):
        line = raw.strip()
        if line in ("Sector", "Province", "District"):
            section = line.lower()
            continue
        m = _HIES_ROW.match(line)
        if not m:
            continue
        numbers = [_num(x) for x in re.findall(NUM, line[len(m.group("label")) :])]
        out.append((section, m.group("label").strip(), n, numbers))
    return out


def build_hies(
    raw_root: Path, catalog_root: Path, spine: dict[str, str], pages_dir: Path
) -> Result:
    res = Result(HIES_ID)
    snap = find_snapshot(raw_root, "dcs", HIES_ID, HIES_FILE)
    text = (pages_dir / HIES_FILE / f"page-{HIES_PAGE:03d}.txt").read_text()
    matches = load_matches(catalog_root, HIES_ID)
    parsed = parse_hies_table04(text)
    period, start, end = "2019", dt.date(2019, 1, 1), dt.date(2019, 12, 31)
    for section, label, line_no, nums in parsed:
        if section == "sector":
            geo, breakdown = "LK", {"sector": SECTORS[label]}
        else:
            m = matches.get(label)
            if m is None or m.geography_id not in spine:
                res.unmatched.append(f"{section}: {label!r} (page {HIES_PAGE} line {line_no})")
                continue
            geo, breakdown = m.geography_id, None
        for indicator, unit, group in HIES_INDICATORS:
            line_name, idx = group.split(":")
            col = int(idx) + (0 if line_name == "old" else 3)
            res.rows.append(
                _row(
                    dataset_id=HIES_ID,
                    indicator=indicator,
                    geography_id=geo,
                    period=period,
                    time_start=start,
                    time_end=end,
                    time_support="interval_mean",
                    value=nums[col],
                    unit=unit,
                    universe="persons",
                    collection_method="sample_survey",
                    data_nature="survey_estimate",
                    snap=snap,
                    locator=(
                        f"{HIES_FILE} p.{HIES_PAGE} Table 04, row '{label}', column {col + 1} "
                        f"(text line {line_no})"
                    ),
                    breakdown=breakdown,
                    note="Number printed as given; poor-population counts are rounded to 100.",
                )
            )
    _hies_checks(res, parsed)
    return res


def _hies_checks(res: Result, parsed: list[tuple[str, str, int, list[float]]]) -> None:
    by = {
        s: [(label, nums) for sec, label, _, nums in parsed if sec == s]
        for s in ("country", "sector", "province", "district")
    }
    res.notes.append(
        "rows read: "
        + ", ".join(f"{len(v)} {k}" for k, v in by.items())
        + " (expected 1 country, 3 sector, 9 province, 25 district)"
    )
    expected = {"country": 1, "sector": 3, "province": 9, "district": 25}
    res.checks.append(
        (
            "row counts",
            all(len(by[k]) == v for k, v in expected.items()),
            str({k: len(v) for k, v in by.items()}),
        )
    )
    total = by["country"][0][1]
    for section in ("sector", "province", "district"):
        for name, col in (("old PL", 1), ("updated PL", 4)):
            s = sum(n[col] for _, n in by[section])
            # published counts are rounded to the nearest 100: allow 50 per row
            tol = 50 * len(by[section]) + 100
            res.checks.append(
                (
                    f"{section} poor population sums to Sri Lanka ({name})",
                    abs(s - total[col]) <= tol,
                    f"sum {s:,.0f} vs published {total[col]:,.0f} (tolerance {tol})",
                )
            )


# --- LFS 2024, Tables 12 / 12A / 12B --------------------------------------------------------

LFS_ID = "labour-force-survey"
LFS_FILE = "LFS2024.pdf"
LFS_TABLES: tuple[tuple[int, str, str], ...] = (
    (92, "Table 12 - Labour force status", "both"),
    (93, "Table 12A - Labour force status", "male"),
    (94, "Table 12B - labour force status", "female"),
)
LFS_COLUMNS: tuple[tuple[str, str, str, str], ...] = (
    # (indicator, unit, measure label, universe) in the printed column order after the label
    ("lfs_population_15_plus", "persons", "household population 15+", "persons_15_plus"),
    ("lfs_labour_force", "persons", "total labour force", "persons_15_plus"),
    (
        "lfs_labour_force_participation_rate",
        "percent",
        "labour force participation rate",
        "persons_15_plus",
    ),
    ("lfs_employed", "persons", "employed number", "persons_15_plus"),
    (None, "percent", "employed rate (share of labour force)", ""),  # type: ignore[arg-type]
    ("lfs_unemployed", "persons", "unemployed number", "persons_15_plus"),
    ("lfs_unemployment_rate", "percent", "unemployment rate", "labour_force"),
    ("lfs_not_in_labour_force", "persons", "not in labour force", "persons_15_plus"),
)
_LFS_ROW = re.compile(rf"^(?P<label>[A-Za-z .]+?)\s+((?:{NUM})(?:\s+(?:{NUM})){{7}})\s*$")


res_repairs: list[str] = []  # labels of rows reassembled from a scrambled text layer


def parse_lfs_table(text: str, title_start: str) -> list[tuple[str, int, list[float]]]:
    lines = text.splitlines()
    if not any(ln.startswith(title_start) for ln in lines):
        raise ValueError(f"title {title_start!r} not found on the page")
    out = []
    # The text layer of one printed row can come out scrambled: the last row of a page (Kegalle,
    # Table 12A) is split as "<unemployed> <rate> <label> <5 numbers> <footnote>" with the
    # not-in-labour-force count on the next line. It is reassembled here in printed order; the
    # row checks (employed + unemployed = labour force, LF + not in LF = population) then pass or fail.
    scrambled = re.compile(
        rf"^({NUM}) ({NUM}) (?P<label>[A-Za-z .]+?) ((?:{NUM} ){{4}}{NUM}) These figures"
    )
    for i, raw in enumerate(lines):
        m = scrambled.match(raw.strip())
        if m and i + 1 < len(lines) and re.fullmatch(NUM, lines[i + 1].strip()):
            lines[i] = (
                f"{m.group('label')} {m.group(4)} {m.group(1)} {m.group(2)} {lines[i + 1].strip()}"
            )
            lines[i + 1] = ""
            res_repairs.append(m.group("label"))
    for n, raw in enumerate(lines, start=1):
        m = _LFS_ROW.match(raw.strip())
        if m:
            nums = [_num(x) for x in re.findall(NUM, raw.strip()[len(m.group("label")) :])]
            out.append((m.group("label").strip(), n, nums))
    return out


def build_lfs(raw_root: Path, catalog_root: Path, spine: dict[str, str], pages_dir: Path) -> Result:
    res = Result(LFS_ID)
    snap = find_snapshot(raw_root, "dcs", LFS_ID, LFS_FILE)
    matches = load_matches(catalog_root, LFS_ID)
    period, start, end = "2024", dt.date(2024, 1, 1), dt.date(2024, 12, 31)
    tables: dict[str, dict[str, list[float]]] = {}
    for page, title, sex in LFS_TABLES:
        text = (pages_dir / LFS_FILE / f"page-{page:03d}.txt").read_text()
        parsed = parse_lfs_table(text, title)
        tables[sex] = {}
        for label, line_no, nums in parsed:
            m = matches.get(label)
            if m is None or m.geography_id not in spine:
                res.unmatched.append(f"{sex}: {label!r} (p.{page} line {line_no})")
                continue
            tables[sex][m.geography_id] = nums
            for j, (indicator, unit, measure, universe) in enumerate(LFS_COLUMNS):
                if indicator is None:
                    continue  # employed rate: derivable (100 - unemployment rate); not stored
                res.rows.append(
                    _row(
                        dataset_id=LFS_ID,
                        indicator=indicator,
                        geography_id=m.geography_id,
                        period=period,
                        time_start=start,
                        time_end=end,
                        time_support="interval_mean",
                        value=nums[j],
                        unit=unit,
                        universe=universe,
                        collection_method="sample_survey",
                        data_nature="survey_estimate",
                        snap=snap,
                        locator=(
                            f"{LFS_FILE} p.{page} {title[: title.index(' - ')]}, row "
                            f"'{label}', column {j + 2} ({measure}; text line {line_no})"
                        ),
                        breakdown={"sex": sex},
                        note="Sample-survey estimate; DCS notes high CV for some district values.",
                    )
                )
    if res_repairs:
        res.notes.append(
            "text-layer rows reassembled in printed order (checked by the row sums): "
            + ", ".join(sorted(set(res_repairs)))
        )
    _lfs_checks(res, tables)
    return res


def _lfs_checks(res: Result, tables: dict[str, dict[str, list[float]]]) -> None:
    for sex, t in tables.items():
        res.checks.append(
            (f"{sex}: 26 rows (Sri Lanka + 25 districts)", len(t) == 26, f"{len(t)} rows")
        )
        bad = []
        for geo, n in t.items():
            pop, lf, _, emp, _, unemp, _, nilf = n
            if abs(emp + unemp - lf) > 1:
                bad.append(
                    f"{geo}: employed+unemployed {emp + unemp:,.0f} != labour force {lf:,.0f}"
                )
            if abs(lf + nilf - pop) > 1:
                bad.append(
                    f"{geo}: labour force + not in LF {lf + nilf:,.0f} != population {pop:,.0f}"
                )
        res.checks.append(
            (
                f"{sex}: employed+unemployed = labour force; LF + not in LF = population (+/-1: printed counts are rounded)",
                not bad,
                "; ".join(bad) or f"all {len(t)} rows",
            )
        )
        districts = [g for g in t if g != "LK"]
        for i, name in ((0, "population"), (1, "labour force"), (5, "unemployed")):
            s = sum(t[g][i] for g in districts)
            res.checks.append(
                (
                    f"{sex}: districts sum to Sri Lanka ({name}; +/-25 rounding)",
                    abs(s - t["LK"][i]) <= len(districts),
                    f"sum {s:,.0f} vs {t['LK'][i]:,.0f}",
                )
            )
    if {"both", "male", "female"} <= set(tables):
        bad = [
            f"{g}[{i}]"
            for g in tables["both"]
            for i in (0, 1, 3, 5, 7)
            if g in tables["male"]
            and g in tables["female"]
            and abs(tables["male"][g][i] + tables["female"][g][i] - tables["both"][g][i]) > 2
        ]
        res.checks.append(
            (
                "male + female = both sexes (counts, every row, +/-2 rounding)",
                not bad,
                ", ".join(bad) or "all rows",
            )
        )


# --- Paddy ----------------------------------------------------------------------------------

PADDY_ID = "paddy-statistics"
PADDY_SOURCE = "data-gov-lk"
PADDY_RAW_DATASET = "data-gov-lk-other-topics"
PADDY_FILES: tuple[dict[str, Any], ...] = (
    {
        "file": "paddy_production_statistics_maha_2011_0.csv",
        "period": "2010/11-maha",
        # The file name says "maha_2011"; the DCS PDF title page says "2010/11 MAHA SEASON".
        "evidence": "paddy_production_statistics_maha_2011.pdf title: '2010/11 MAHA SEASON', final estimate, issued 30 Oct 2011",
        "start": dt.date(2010, 9, 1),
        "end": dt.date(2011, 3, 31),
        "total_sown": 1_804_204.0,  # Sri Lanka, gross extent sown, all schemes (acres), PDF
    },
    {
        "file": "paddy_production_statistics_yala_2012_0.csv",
        "period": "2012-yala",
        "evidence": "paddy_production_statistics_yala_2012.pdf title: '2012 YALA SEASON', final estimate, issued 24 Jan 2013",
        "start": dt.date(2012, 4, 1),
        "end": dt.date(2012, 8, 31),
        "total_sown": 900_795.0,
    },
)
PADDY_NOT_INGESTED: tuple[tuple[str, str], ...] = (
    (
        "department_of_census_and_statistics_paddy_statistics_0.csv",
        "metric units (hectares), no season or year in the file or its name; the DCS title page is not held",
    ),
    (
        "paddy statistics_extent_sown_harvested_(gross & nett)_average_yield_and_production_by_district_maha_season_0.csv",
        "metric units (hectares), no season or year in the file or its name; the DCS title page is not held",
    ),
    (
        "paddy_production_statistics_maha_2010.xls / yala_2010.xls",
        "xls only (no csv); reading .xls needs a new dependency (xlrd), not added",
    ),
)
# (indicator, unit, csv column index after the district label)
PADDY_COLUMNS: tuple[tuple[str, str, int], ...] = (
    ("paddy_gross_extent_sown", "acres", 4),
    ("paddy_gross_extent_harvested", "acres", 8),
    ("paddy_average_yield", "bushels_per_nett_acre", 12),
    ("paddy_nett_extent_harvested", "acres", 13),
    ("paddy_production", "thousand_bushels", 14),
)


def _paddy_label(label: str) -> str:
    return label.replace("*", "").strip()


def build_paddy(raw_root: Path, catalog_root: Path, spine: dict[str, str]) -> Result:
    res = Result(PADDY_ID)
    matches = load_matches(catalog_root, PADDY_ID)
    for spec in PADDY_FILES:
        snap = find_snapshot(raw_root, PADDY_SOURCE, PADDY_RAW_DATASET, spec["file"])
        with snap.path.open(newline="", encoding="utf-8-sig") as f:
            table = list(csv.reader(f))
        header = ",".join(table[0]).upper()
        if "ACRES" not in header or "BUSHELS" not in header or "TOTAL PRODUCTION" not in header:
            raise ValueError(f"{spec['file']}: header is not the acres/bushels layout")
        body = [r for r in table[1:] if r and r[0].strip()]
        res.notes.append(
            f"{spec['period']}: {len(body)} rows in {spec['file']}; season evidence: {spec['evidence']}"
        )
        sums = 0.0
        blank = []
        for i, r in enumerate(body, start=2):
            label = _paddy_label(r[0])
            sown = r[4].strip()
            sums += _num(sown) if sown else 0.0
            m = matches.get(label)
            if m is None or m.geography_id not in spine:
                res.unmatched.append(
                    f"{spec['period']}: {label!r} (csv row {i}) is a paddy management area, not a spine place"
                    if label in ("UDAWALAWE", "UDA WALAWE", "MAHAWELI", "MAHAWELI 'H'")
                    else f"{spec['period']}: {label!r} (csv row {i})"
                )
                continue
            for indicator, unit, col in PADDY_COLUMNS:
                raw = r[col].strip() if col < len(r) else ""
                value = _num(raw) if raw else None
                if value is None:
                    blank.append(f"{label} {indicator}")
                res.rows.append(
                    _row(
                        dataset_id=PADDY_ID,
                        indicator=indicator,
                        geography_id=m.geography_id,
                        period=spec["period"],
                        time_start=spec["start"],
                        time_end=spec["end"],
                        time_support="interval_total"
                        if indicator not in ("paddy_average_yield",)
                        else "interval_mean",
                        value=value,
                        unit=unit,
                        universe="paddy_fields",
                        collection_method="admin_register",
                        data_nature="official_estimate",
                        snap=snap,
                        locator=f"{spec['file']} row {i} ('{r[0].strip()}'), column {col + 1}",
                        note=(
                            "Final estimate. Season dates are the conventional Maha (Sep-Mar) and "
                            "Yala (Apr-Aug) windows, not stated in the table (assumption)."
                        ),
                    )
                )
        res.checks.append(
            (
                f"{spec['period']}: gross extent sown sums to the PDF's Sri Lanka total",
                abs(sums - spec["total_sown"]) < 1,
                f"CSV sum {sums:,.1f} vs PDF Sri Lanka {spec['total_sown']:,.0f} acres (read from the PDF page image)",
            )
        )
        if blank:
            res.notes.append(
                f"{spec['period']}: blank cells in the CSV, stored as not_available: {', '.join(blank)}"
            )
    res.not_ingested = [f"{name}: {why}" for name, why in PADDY_NOT_INGESTED]
    return res


# --- Output ---------------------------------------------------------------------------------


def qa_markdown(res: Result, title: str, spine_note: str) -> str:
    qa = check_observations(res.dataset_id, [dict(r) for r in res.rows])
    for r in res.rows:
        if r["value_status"] == "normal" and r["value"] is not None and r["value"] < 0:
            qa.errors.append(f"{r['claim_id']}: negative value")
    n_geo = len({r["geography_id"] for r in res.rows})
    periods = sorted({r["period"] for r in res.rows})
    lines = [
        f"# QA report: {title} (`{res.dataset_id}`)",
        "",
        f"- Observations: {len(res.rows)} across {n_geo} geographies; periods: {', '.join(periods)}",
        f"- Generic observation checks: {len(qa.errors)} errors, {len(qa.warnings)} warnings",
        f"- Null values (stored `not_available`): {sum(1 for r in res.rows if r['value'] is None)}",
        f"- Verification: all rows `machine_extracted`. Geography: {spine_note}",
        f"- Unmatched source units (not in output): {len(res.unmatched)}",
        "",
        "## Checks",
        "",
        *[f"- {'✅' if ok else '❌'} {name}: {detail}" for name, ok, detail in res.checks],
    ]
    if qa.errors:
        lines += ["", "## Errors", "", *[f"- {e}" for e in qa.errors[:50]]]
    if res.notes:
        lines += ["", "## Notes", "", *[f"- {n}" for n in res.notes]]
    lines += ["", "## Unmatched source units", ""]
    lines += [f"- {u}" for u in res.unmatched] or ["- none"]
    if res.not_ingested:
        lines += ["", "## Held but not ingested", "", *[f"- {n}" for n in res.not_ingested]]
    return "\n".join(lines) + "\n"


def write_outputs(
    results: Iterable[tuple[Result, str]], out_dir: Path, spine_note: str
) -> list[Path]:
    import pyarrow as pa
    import pyarrow.parquet as pq

    written = []
    for res, title in results:
        d = out_dir / res.dataset_id
        d.mkdir(parents=True, exist_ok=True)
        rows = [
            {**r, "breakdown": json.dumps(r["breakdown"]) if r["breakdown"] else None}
            for r in res.rows
        ]
        pq.write_table(pa.Table.from_pylist(rows), d / "observations.parquet")
        with (d / "observations.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        (d / "qa.md").write_text(qa_markdown(res, title, spine_note), encoding="utf-8")
        written.append(d)
    return written


def build_all(
    *, raw_root: Path, catalog_root: Path, spine_dir: Path, pages_dir: Path, out_dir: Path
) -> list[tuple[Result, str]]:
    spine = load_spine_ids(spine_dir)
    results = [
        (build_hies(raw_root, catalog_root, spine, pages_dir), "HIES poverty indicators 2019"),
        (
            build_lfs(raw_root, catalog_root, spine, pages_dir),
            "Labour Force Survey 2024, district tables",
        ),
        (build_paddy(raw_root, catalog_root, spine), "Paddy statistics by district and season"),
    ]
    write_outputs(
        results,
        out_dir,
        "joined by the reviewed match file to spine ids (country, province, district)",
    )
    return results
