"""Q01 accuracy audit: sample published values and trace each one back to its source.

The audit is deliberately independent of the census ingest code (`slf.datasets.census_2024_gnd`):
it re-reads the raw DCS workbooks from their snapshot files, recomputes sums and derived values
with its own formulas, and compares them with the release parquet, the release API JSON (which
the website reads), and, where page text is supplied, the DCS Final Report tables.

A machine re-trace is not human verification: values stay `machine_extracted` until the lead
confirms the sheet this module writes (AGENTS rule 7).
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd

SEED = 20261112
DATASET = "census-2024-gnd-tables"

# Values sampled per indicator at each level. Country and the provisional unit are taken whole.
QUOTAS = {"province": 2, "district": 2, "ds": 2, "gn": 5}
# Values that an override or manual match changed: always audited (Kandalama/Kiralessa swap).
FORCED = [
    ("LK2206300", "population_total"),
    ("LK2206125", "population_total"),
    ("LK2206300", "occupied_housing_units"),
    ("LK2206125", "occupied_housing_units"),
]
LEVELS = {2: "country", 3: "province", 4: "district", 6: "ds", 9: "gn", 13: "provisional"}

POP_COLUMNS = {  # 0-based tuple index in GN_population.xlsx sheet 'Population'
    "population_total": 9,
    "population_male": 10,
    "population_female": 11,
    "population_age_0_14": 13,
    "population_age_15_59": 14,
    "population_age_60_64": 15,
    "population_age_65_plus": 16,
}
HOUSING_COLUMN = 9  # 0-based, GN_housing.xlsx sheet 'Housing Units'
COUNTS = [*POP_COLUMNS, "occupied_housing_units"]
FIRST_DATA_ROW = 6

# Tolerances: counts must match exactly; derived values are published to 4 decimals.
DERIVED_TOL = 5.1e-5
DENSITY_REL_TOL = 1e-4  # area is recomputed here from the published geometry

PDF_TABLES = {
    "population_total": ("Table 3.2", 68),
    "occupied_housing_units": ("Table 11.2", 202),
}

CELL_RE = re.compile(
    r"^(?P<file>\S+\.xlsx), sheet '(?P<sheet>[^']+)', row (?P<row>\d+), column (?P<col>\d+)"
)
DERIVED_RE = re.compile(
    r"GN_population\.xlsx row (?P<prow>\d+) and GN_housing\.xlsx row (?P<hrow>\d+)"
)
SUM_RE = re.compile(r"summed to (?P<level>country|province|district|ds) (?P<code>\w+)")


def excel_column(index0: int) -> str:
    """0-based column index -> Excel letter (9 -> 'J')."""
    n, out = index0 + 1, ""
    while n:
        n, r = divmod(n - 1, 26)
        out = chr(65 + r) + out
    return out


def count_true(mask: object) -> int:
    return int(np.count_nonzero(np.asarray(mask, dtype=bool)))


def level_of(geography_id: str) -> str:
    return LEVELS[len(geography_id)]


# --- raw sources -----------------------------------------------------------------------------


@dataclass
class Raw:
    """The two DCS workbooks, as read from their snapshot files."""

    pop: pd.DataFrame  # indexed by Excel row number
    housing: pd.DataFrame
    pop_path: Path
    housing_path: Path
    sha: dict[str, str]  # file name -> sha256


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_snapshot(raw_dir: Path, sha: str) -> Path:
    for path in sorted(raw_dir.rglob("*.xlsx")):
        if sha256(path) == sha:
            return path
    raise FileNotFoundError(f"no raw snapshot with sha256 {sha} under {raw_dir}")


def _sheet(path: Path, sheet: str) -> pd.DataFrame:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = []
    for i, row in enumerate(wb[sheet].iter_rows(min_row=FIRST_DATA_ROW, values_only=True)):
        if row[0] is None:
            continue
        rows.append((FIRST_DATA_ROW + i, *row))
    wb.close()
    width = max(len(r) for r in rows)
    frame = pd.DataFrame(rows, columns=["excel_row", *range(width - 1)]).set_index("excel_row")
    frame["district"] = frame[2].astype(int)
    frame["ds"] = frame["district"] * 100 + frame[4].astype(int)
    frame["gn"] = frame["ds"] * 1000 + frame[6].astype(int)
    frame["province"] = frame[0].astype(int)
    return frame


def load_raw(raw_dir: Path, pop_sha: str, housing_sha: str) -> Raw:
    pop_path = find_snapshot(raw_dir, pop_sha)
    housing_path = find_snapshot(raw_dir, housing_sha)
    pop = _sheet(pop_path, "Population")
    housing = _sheet(housing_path, "Housing Units")
    return Raw(
        pop,
        housing,
        pop_path,
        housing_path,
        {pop_path.name: pop_sha, housing_path.name: housing_sha},
    )


def _counts_for(raw: Raw, prow_mask: pd.Series, hrow_mask: pd.Series) -> dict[str, float]:
    out = {k: float(raw.pop.loc[prow_mask, c].astype(float).sum()) for k, c in POP_COLUMNS.items()}
    out["occupied_housing_units"] = float(
        raw.housing.loc[hrow_mask, HOUSING_COLUMN].astype(float).sum()
    )
    return out


def derived(indicator: str, c: dict[str, float], area_km2: float | None) -> float | None:
    """Independent restatement of the indicator definitions in docs/methods/census-2024.md."""
    total, male, female = c["population_total"], c["population_male"], c["population_female"]
    old = c["population_age_60_64"] + c["population_age_65_plus"]
    formulas: dict[str, tuple[float, float]] = {
        "sex_ratio": (100 * male, female),
        "population_age_0_14_share": (100 * c["population_age_0_14"], total),
        "population_age_60_plus_share": (100 * old, total),
        "persons_per_occupied_housing_unit": (total, c["occupied_housing_units"]),
        "population_density": (total, area_km2 or 0.0),
    }
    if indicator in c:
        return c[indicator]
    if indicator == "population_age_60_plus":
        return old
    num, den = formulas[indicator]
    return num / den if den else None


# --- tracing ---------------------------------------------------------------------------------


@dataclass
class Trace:
    expected: float | None
    method: str
    row_identity_ok: bool | None = None
    note: str = ""


def trace(row: pd.Series, raw: Raw, areas: dict[str, float], dcs_codes: dict[str, str]) -> Trace:
    loc, ind, geo = str(row["source_locator"]), str(row["indicator_id"]), str(row["geography_id"])
    if m := CELL_RE.match(loc):
        frame = raw.pop if m["file"] == "GN_population.xlsx" else raw.housing
        r, col = int(m["row"]), int(m["col"])
        value = float(frame.loc[r, col])
        identity = str(int(frame.loc[r, "gn"])) == dcs_codes.get(geo)
        return Trace(value, f"cell {m['file']} {excel_column(col)}{r}", identity)
    if m := DERIVED_RE.search(loc):
        prow, hrow = int(m["prow"]), int(m["hrow"])
        c = _counts_for(
            raw,
            pd.Series(raw.pop.index == prow, index=raw.pop.index),
            pd.Series(raw.housing.index == hrow, index=raw.housing.index),
        )
        identity = str(int(raw.pop.loc[prow, "gn"])) == dcs_codes.get(geo) and int(
            raw.pop.loc[prow, "gn"]
        ) == int(raw.housing.loc[hrow, "gn"])
        return Trace(
            derived(ind, c, areas.get(geo)), f"recomputed from rows {prow}/{hrow}", identity
        )
    if m := SUM_RE.search(loc):
        lvl, code = m["level"], m["code"]
        if lvl == "country":
            pm, hm = np.ones(len(raw.pop), bool), np.ones(len(raw.housing), bool)
        else:
            pm, hm = raw.pop[lvl] == int(code), raw.housing[lvl] == int(code)
        c = _counts_for(
            raw, pd.Series(pm, index=raw.pop.index), pd.Series(hm, index=raw.housing.index)
        )
        n = int(np.asarray(pm).sum())
        return Trace(derived(ind, c, areas.get(geo)), f"sum of {n} raw GN rows ({lvl} {code})")
    return Trace(None, "unparsed locator", note=f"locator not understood: {loc}")


def compare(indicator: str, published: float | None, expected: float | None) -> bool:
    if published is None or expected is None:
        return published is None and expected is None
    if indicator in COUNTS or indicator == "population_age_60_plus":
        return published == expected
    if indicator == "population_density":
        return math.isclose(published, expected, rel_tol=DENSITY_REL_TOL)
    return abs(published - expected) <= DERIVED_TOL


def _nan_to_none(v: object) -> float | None:
    if v is None:
        return None
    f = float(v)  # type: ignore[arg-type]
    return None if math.isnan(f) else f


# --- sampling --------------------------------------------------------------------------------


def draw_sample(obs: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    obs = obs.assign(level=obs["geography_id"].map(level_of))
    parts = [
        obs[obs["level"].isin(["country", "provisional"])].assign(stratum="all at level"),
        obs[obs["value_status"] != "normal"].assign(stratum="every not_available value"),
    ]
    forced = obs.set_index(["geography_id", "indicator_id"]).index.isin(FORCED)
    parts.append(obs[forced].assign(stratum="changed by manual match (forced)"))
    for level, k in QUOTAS.items():
        for _, group in obs[(obs["level"] == level) & (obs["value_status"] == "normal")].groupby(
            "indicator_id", sort=True
        ):
            pick = rng.choice(len(group), size=min(k, len(group)), replace=False)
            parts.append(group.iloc[np.sort(pick)].assign(stratum=f"random {k} per indicator"))
    sample = pd.concat(parts).drop_duplicates("claim_id", keep="first")
    order = {name: i for i, name in enumerate(LEVELS.values())}
    return sample.sort_values(
        ["level", "geography_id", "indicator_id"],
        key=lambda s: s.map(order) if s.name == "level" else s,
    ).reset_index(drop=True)


# --- PDF table check -------------------------------------------------------------------------


def parse_pdf_table(text: str) -> dict[str, int]:
    """Lines like 'Western Province 6,117,341 28.1' or 'Colombo 562,550 78,052 654,051 113,837'."""
    out: dict[str, int] = {}
    for line in text.splitlines():
        m = re.match(r"^([A-Z][A-Za-z ]+?)\s+((?:[\d,]+\s*)+(?:\d+\.\d)?)$", line.strip())
        if not m:
            continue
        nums = [int(n.replace(",", "")) for n in re.findall(r"\d[\d,]*(?!\.\d)", m[2]) if "," in n]
        if nums:
            out[m[1].strip()] = nums[0] if len(nums) < 4 else nums[2]  # Table 11.2: 2024 occupied
    return out


def pdf_names(raw: Raw) -> dict[str, str]:
    """DCS names (from the workbook itself) -> release geography ids for "
    "country/province/district."""
    names = {"Sri Lanka": "LK"}
    for code, name in raw.pop[[0, 1]].drop_duplicates().itertuples(index=False):
        names[f"{str(name).strip()} Province"] = f"LK{int(code)}"
    for code, name in raw.pop[[2, 3]].drop_duplicates().itertuples(index=False):
        names[str(name).strip()] = f"LK{int(code)}"
    return names


def pdf_check(obs: pd.DataFrame, pages_dir: Path, raw: Raw) -> pd.DataFrame | None:
    names = pdf_names(raw)
    rows = []
    for indicator, (table, page) in PDF_TABLES.items():
        path = pages_dir / f"page-{page:03d}.txt"
        if not path.exists():
            return None
        for name, value in parse_pdf_table(path.read_text(encoding="utf-8")).items():
            geo = names.get(name)
            if geo is None:
                continue
            hit = obs[(obs["geography_id"] == geo) & (obs["indicator_id"] == indicator)]
            published = float(hit["value"].tolist()[0]) if len(hit) else None
            rows.append(
                {
                    "geography_id": geo,
                    "pdf_name": name,
                    "indicator_id": indicator,
                    "pdf_table": table,
                    "pdf_page": page,
                    "pdf_value": value,
                    "published": published,
                    "match": published == value,
                }
            )
    return pd.DataFrame(rows)


# --- run -------------------------------------------------------------------------------------


@dataclass
class AuditResult:
    release: str
    seed: int
    population: pd.DataFrame
    sample: pd.DataFrame
    pdf: pd.DataFrame | None
    raw: Raw
    headline_values: int
    warnings: list[str] = field(default_factory=list)


def api_value(
    release_dir: Path, geo: str, indicator: str, cache: dict[str, dict]
) -> float | str | None:
    if geo not in cache:
        path = release_dir / "api" / "v1" / "places" / f"{geo}.json"
        cache[geo] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    for v in cache[geo].get("values", []):
        if v["indicator_id"] == indicator:
            return _nan_to_none(v["value"])
    return "missing"


def run(
    release_dir: Path, raw_dir: Path, catalog: Path, pages_dir: Path, seed: int = SEED
) -> AuditResult:
    import geopandas as gpd

    obs = pd.read_parquet(release_dir / "observations" / f"{DATASET}.parquet")
    release = str(obs["release"].iloc[0])
    cell = obs["source_locator"].str.match(CELL_RE)
    pop_sha = obs.loc[
        cell & obs["source_locator"].str.startswith("GN_population"), "snapshot_sha256"
    ].iloc[0]
    housing_sha = obs.loc[
        cell & obs["source_locator"].str.startswith("GN_housing"), "snapshot_sha256"
    ].iloc[0]
    raw = load_raw(raw_dir, str(pop_sha), str(housing_sha))

    versions = gpd.read_parquet(release_dir / "geography_versions.geoparquet")
    areas = dict(
        zip(versions["geography_id"], versions.to_crs(5235).geometry.area / 1e6, strict=True)
    )
    codes = pd.read_csv(catalog / "geographies" / "codes" / "dcs-census2024.csv", dtype=str)
    dcs_codes = dict(zip(codes["geography_id"], codes["external_code"], strict=False))

    sample = draw_sample(obs, seed)
    cache: dict[str, dict] = {}
    out = []
    for _, row in sample.iterrows():
        t = trace(row, raw, areas, dcs_codes)
        published = _nan_to_none(row["value"])
        api = api_value(release_dir, str(row["geography_id"]), str(row["indicator_id"]), cache)
        source_ok = compare(str(row["indicator_id"]), published, t.expected)
        api_ok = api != "missing" and api == published
        out.append(
            {
                **{
                    k: row[k]
                    for k in ["claim_id", "level", "geography_id", "indicator_id", "stratum"]
                },
                "published": published,
                "traced": t.expected,
                "trace_method": t.method,
                "row_identity_ok": t.row_identity_ok,
                "api_value": None if api == "missing" else api,
                "source_match": source_ok and t.row_identity_ok is not False,
                "api_match": api_ok,
                "source_locator": row["source_locator"],
                "note": t.note,
            }
        )
    result = pd.DataFrame(out)
    headline = int(obs["geography_id"].str.len().isin([2, 3, 4]).sum())
    warnings = []
    pdf = pdf_check(obs, pages_dir, raw)
    if pdf is None:
        warnings.append(f"PDF page text not found in {pages_dir}; Final Report comparison not run")
    elif count_true(~pdf["match"]):
        warnings.append(f"{count_true(~pdf['match'])} Final Report values differ from the release")
    bad = result[~(result["source_match"] & result["api_match"])]
    if len(bad):
        warnings.append(f"{len(bad)} sampled values failed the re-trace or API check")
    return AuditResult(release, seed, obs, result, pdf, raw, headline, warnings)


# --- lead sheet ------------------------------------------------------------------------------


def lead_sheet(res: AuditResult, seed: int = SEED) -> pd.DataFrame:
    """20 highest-stakes values for the lead to confirm personally against the source."""
    rows: list[dict[str, object]] = []
    obs = res.population.set_index(["geography_id", "indicator_id"])
    names = {v: k for k, v in pdf_names(res.raw).items()}

    def add(geo: str, ind: str, where: str, how: str) -> None:
        rows.append(
            {
                "check": len(rows) + 1,
                "geography_id": geo,
                "place": names.get(geo, geo),
                "indicator_id": ind,
                "published_value": float(obs.loc[(geo, ind), "value"]),  # type: ignore[arg-type]
                "where_to_look": where,
                "how": how,
                "lead_reads": "",
                "matches": "",
            }
        )

    p68, p202 = (
        "CPH2024_Final_Eng.pdf, PDF page 68 (printed 51), Table 3.2",
        ("CPH2024_Final_Eng.pdf, PDF page 202 (printed 185), Table 11.2, column '2024 Occupied'"),
    )
    add("LK", "population_total", p68, "row 'Sri Lanka'")
    add("LK", "occupied_housing_units", p202, "row 'Sri Lanka'")
    for geo in ["LK1", "LK5", "LK4"]:
        add(geo, "population_total", p68, f"row '{names[geo]}'")
    for geo in ["LK11", "LK12", "LK52", "LK42", "LK51", "LK92"]:
        add(geo, "population_total", p68, f"row '{names[geo]}'")
    for geo in ["LK11", "LK52", "LK42"]:
        add(geo, "occupied_housing_units", p202, f"row '{names[geo]}'")
    # GN cells: the corrected Kandalama/Kiralessa pair, then random sampled GN cell values.
    gn = res.sample.loc[
        (res.sample["level"] == "gn") & res.sample["trace_method"].str.startswith("cell")
    ]
    forced = gn.loc[
        gn["stratum"].str.contains("forced") & (gn["indicator_id"] == "population_total")
    ]
    rest = gn.loc[~gn.index.isin(forced.index)]
    rng = np.random.default_rng(seed + 1)
    picks = pd.concat(
        [forced, rest.iloc[np.sort(rng.choice(len(rest), 6 - len(forced), replace=False))]]
    )
    gn_names = res.raw.pop.set_index("gn")[7].to_dict()
    for _, r in picks.iterrows():
        m = CELL_RE.match(str(r["source_locator"]))
        assert m
        frame = res.raw.pop if m["file"] == "GN_population.xlsx" else res.raw.housing
        dcs = int(frame.loc[int(m["row"]), "gn"])
        cell = f"{excel_column(int(m['col']))}{m['row']}"
        gn_name = str(gn_names.get(dcs, "")).strip()
        rows.append(
            {
                "check": len(rows) + 1,
                "geography_id": r["geography_id"],
                "place": str(gn_names.get(dcs, "")).strip(),
                "indicator_id": r["indicator_id"],
                "published_value": r["published"],
                "where_to_look": f"{m['file']}, sheet '{m['sheet']}', cell {cell}",
                "how": f"row {m['row']} should be GN code {dcs} ({gn_name})",
                "lead_reads": "",
                "matches": "",
            }
        )
    return pd.DataFrame(rows)


# --- report ----------------------------------------------------------------------------------


def _fmt(v: object) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "n/a"
    f = float(v)  # type: ignore[arg-type]
    return f"{int(f):,}" if f.is_integer() else f"{f:,.4f}"


def render(res: AuditResult, sheet: pd.DataFrame) -> str:
    s = res.sample
    errors = s.loc[~(s["source_match"] & s["api_match"])]
    headline = s.loc[s["level"].isin(["country", "province", "district"])]
    head_err = errors.loc[errors["level"].isin(["country", "province", "district"])]
    other = s.loc[~s.index.isin(headline.index)]
    other_err = errors.loc[~errors.index.isin(head_err.index)]
    target = max(100, math.ceil(0.02 * res.headline_values))
    lines = [
        f"# Q01 accuracy audit: {res.release}",
        "",
        "Generated by `uv run slf audit q01`; do not edit by hand. Prepared by an agent for the "
        "lead.",
        "",
        "Verification tags: ✅ verified by running or reading the cited source · 🟡 claimed by a "
        "source, not independently checked · ❌ not found or failed · ❓ assumption.",
        "",
        "## Verdict",
        "",
    ]
    machine_pass = len(head_err) == 0 and len(other_err) <= 0.005 * len(other)
    pdf_ok = res.pdf is not None and bool(res.pdf["match"].all())
    lines += [
        f"- **Machine re-trace: {'PASS' if machine_pass else 'FAIL'}** "
        f"({len(errors)} of {len(s)} sampled values failed). "
        f"Final Report tables: {'PASS' if pdf_ok else 'FAIL or not run'}.",
        "- **Release verdict: PENDING.** Q01 is a human gate. The verdict becomes PASS only after "
        "the "
        "lead confirms the 20 values in the confirmation sheet against the source files. Until "
        "then "
        "every value stays `verification: machine_extracted`.",
        "",
        "## Method",
        "",
        f"- Release: `{res.release}`. Seed: **{res.seed}**.",
        f"- Sample size target: max(100, 2% of {res.headline_values:,} headline values) = "
        f"{target}. "
        f"Drawn: **{len(s)}** of {len(res.population):,} published values.",
        "- Strata: every country and provisional-unit value; every `not_available` value; values a "
        "manual match changed (Kandalama/Kiralessa); then a fixed number per indicator at each "
        "level "
        f"({', '.join(f'{k} {v}' for k, v in QUOTAS.items())}).",
        "- For each value: parse the `source_locator`, open the raw snapshot by its sha256, read "
        "the "
        "cell (or sum the raw rows by the DCS code the locator names), recompute derived values "
        "with "
        "formulas written independently of the ingest code, and compare. Counts must match "
        "exactly; "
        f"derived values within {DERIVED_TOL}; density within relative {DENSITY_REL_TOL} (area is "
        "recomputed here in EPSG:5235 from the release geometry).",
        "- For GN rows the audit also checks **row identity**: the raw row's DCS code must be the "
        "code "
        "the crosswalk (`catalog/geographies/codes/dcs-census2024.csv`) gives for that GN.",
        "- The API check reads `api/v1/places/{id}.json`, the file the website renders "
        "(`web/src/lib/release.ts`).",
        "",
        "Raw snapshots used ✅:",
        "",
        "| File | sha256 |",
        "|---|---|",
    ]
    for name, sha in res.raw.sha.items():
        lines.append(f"| `{name}` | `{sha}` |")
    lines += ["", "## Sample composition", "", "| Level | Stratum | Values |", "|---|---|---|"]
    comp = s.groupby(["level", "stratum"], sort=False).size()
    for (level, stratum), n in comp.items():  # type: ignore[misc]
        lines.append(f"| {level} | {stratum} | {n} |")
    lines += ["", "| Indicator | Values |", "|---|---|"]
    for ind, n in s["indicator_id"].value_counts().sort_index().items():
        lines.append(f"| `{ind}` | {n} |")
    lines += [
        "",
        "## Results ✅",
        "",
        "| Group | Sampled | Re-trace errors | API errors | Error rate | Threshold |",
        "|---|---|---|---|---|---|",
    ]
    for label, part, thr in [
        ("Headline (country, province, district)", headline, "0 errors"),
        ("Other (DS, GN, provisional)", other, "≤ 0.5%"),
    ]:
        se = count_true(~part["source_match"])
        ae = count_true(~part["api_match"])
        bad = count_true(~(part["source_match"] & part["api_match"]))
        lines.append(
            f"| {label} | {len(part)} | {se} | {ae} | {bad / max(len(part), 1):.1%} | {thr} |"
        )
    ident = s["row_identity_ok"].dropna()
    lines += [
        "",
        f"GN row identity: {count_true(ident)} / {len(ident)} rows are the GN the crosswalk says.",
    ]
    lines += ["", "### Errors", ""]
    if len(errors):
        lines += ["| Claim | Published | Traced | API | Method |", "|---|---|---|---|---|"]
        for _, r in errors.iterrows():
            lines.append(
                f"| `{r['claim_id']}` | {_fmt(r['published'])} | {_fmt(r['traced'])} | "
                f"{_fmt(r['api_value'])} | {r['trace_method']} |"
            )
    else:
        lines.append("None.")
    lines += ["", "## Final Report comparison (independent published totals)", ""]
    if res.pdf is None:
        lines.append("❌ Not run: PDF page text missing (run `swift scripts/pdf_pages.swift`).")
    else:
        p = res.pdf
        lines.append(
            f"{count_true(p['match'])} / {len(p)} country, province and district values match the "
            f"DCS "
            "Final Report ✅ (page text extracted with PDFKit from the snapshot "
            "`CPH2024_Final_Eng.pdf`)."
        )
        lines += ["", "| Table | Indicator | Rows compared | Matches |", "|---|---|---|---|"]
        for (table, ind), g in p.groupby(["pdf_table", "indicator_id"]):  # type: ignore[misc]
            lines.append(
                f"| {table} (PDF p.{int(g['pdf_page'].iloc[0])}) | `{ind}` | {len(g)} | "
                f"{count_true(g['match'])} |"
            )
        miss = p[~p["match"]]
        for _, r in miss.iterrows():
            lines.append(
                f"- ❌ {r['pdf_name']} `{r['indicator_id']}`: PDF {r['pdf_value']:,}, "
                f"release {_fmt(r['published'])}"
            )
    lines += [
        "",
        "## Findings that are not value errors",
        "",
        "1. **`source_locator` column numbers are 0-based.** `column 9 ('Total')` is Excel column "
        "**J**, "
        "not I. The header name in brackets is correct, but a person reading 'column 9' in Excel "
        "lands on the GN number column. Recommendation: a separate fix PR writes the Excel letter "
        "(`cell J352`) into locators. The confirmation sheet already uses Excel letters.",
        "2. **Derived-value locators name both workbooks even for indicators that use one** "
        "(for example sex ratio uses only the population workbook). Harmless, but imprecise.",
        "3. **Aggregate locators give a row range, not the rows.** For DS 1103 the range 6-40 "
        "happens "
        "to be contiguous; the audit sums by DCS code instead, which is what the range means.",
        "",
        "## Not covered",
        "",
        "- **Website rendering** (number formatting on the page) is not checked here: the audit "
        "checks "
        "the JSON the website reads. A display check needs the built site.",
        "- **Area** for density is recomputed from the same COD-AB geometry the pipeline uses, so "
        "it "
        "checks the arithmetic, not the boundary.",
        "- **Age and sex at national level** are checked against the workbook only; the Final "
        "Report "
        "pages for those tables were not parsed.",
        "- This audit re-traces values; it cannot detect an error that DCS itself published.",
        "",
        "## Lead confirmation sheet",
        "",
        f"`q01-lead-sheet-{res.release}.csv` lists {len(sheet)} values: national, province and "
        f"district "
        "totals against Final Report Tables 3.2 and 11.2 (page images in `screenshots/q01/`), and "
        "GN "
        "cells against the DCS workbooks, including the corrected Kandalama/Kiralessa pair. Fill "
        "in "
        "`lead_reads` and `matches` (yes/no).",
        "",
        "| # | Place | Indicator | Published | Where to look |",
        "|---|---|---|---|---|",
    ]
    for _, r in sheet.iterrows():
        lines.append(
            f"| {r['check']} | {r['place']} (`{r['geography_id']}`) | `{r['indicator_id']}` | "
            f"{_fmt(r['published_value'])} | {r['where_to_look']}; {r['how']} |"
        )
    lines += [
        "",
        "## Full per-value results",
        "",
        f"`accuracy-audit-{res.release}-sample.csv` ({len(s)} rows).",
    ]
    return "\n".join(lines) + "\n"
