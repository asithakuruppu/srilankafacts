"""Compare claims from different sources about the same place (D-019).

Stage 1 compares what the held, publishable sources say about:
- GN and DS division counts inside each place: COD-AB v03 (the boundary set the atlas uses)
  against the DCS 2024 census workbook (the divisions DCS enumerated);
- population and occupied housing units for the country, provinces and districts: the sum of
  the DCS GN workbook (the published value) against the DCS Final Report tables.

NSDI 2017 also lists GN divisions, but its reuse rights are `unclear` and the catalogue marks it
"cross-check only", so it is not compared here: everything this module writes ships in the
release (AGENTS rule 4).

A difference is reported as a difference. Sources can differ for legitimate reasons (different
reference dates, boundary changes, how a unit is split); the page states each source's date and
does not judge which is right (AGENTS rule 12).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import openpyxl
import pandas as pd

COD_AB = {
    "source_id": "cod-ab-v03",
    "label": "COD-AB v03 boundaries (Survey Department, via OCHA)",
    "reference_date": "2022-08-16",
}
DCS_WORKBOOK = {
    "source_id": "dcs-census2024-gn-workbook",
    "label": "DCS Census 2024 GN workbook",
    "reference_date": "2024-12-19",
}
DCS_REPORT = {
    "source_id": "dcs-census2024-final-report",
    "label": "DCS Census 2024 Final Report",
    "reference_date": "2024-12-19",
}
INDICATORS = {
    "gn_division_count": "GN divisions",
    "ds_division_count": "DS divisions",
    "population_total": "Population",
    "occupied_housing_units": "Occupied housing units",
}
SUM_RE = re.compile(r"(\d+) GN rows summed to (country|province|district|ds) (\w+)")


@dataclass
class Comparisons:
    table: pd.DataFrame  # one row per claim
    by_place: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def _level(geo: str) -> str | None:
    return {2: "country", 3: "province", 4: "district", 6: "ds"}.get(len(geo))


def cod_ab_counts(geographies: pd.DataFrame) -> dict[tuple[str, str], int]:
    """GN and DS counts inside each place, from the spine's COD-AB units (provisional excluded)."""
    g = geographies[geographies["status"] == "current"]
    parent = dict(zip(g["geography_id"], g["parent_id"], strict=False))

    def ancestors(geo: str) -> list[str]:
        out, cur = [], parent.get(geo)
        while isinstance(cur, str):
            out.append(cur)
            cur = parent.get(cur)
        return out

    counts: dict[tuple[str, str], int] = {}
    for level, indicator in ((4, "gn_division_count"), (3, "ds_division_count")):
        for geo in g.loc[g["level"] == level, "geography_id"]:
            for anc in ancestors(str(geo)):
                counts[(anc, indicator)] = counts.get((anc, indicator), 0) + 1
    return counts


def dcs_counts(pop_xlsx: Path, ds_map: dict[str, str]) -> dict[tuple[str, str], int]:
    """GN and DS counts by the DCS workbook's own codes; DS codes mapped through the release."""
    wb = openpyxl.load_workbook(pop_xlsx, read_only=True, data_only=True)
    rows = [
        (int(r[0]), int(r[2]), int(r[2]) * 100 + int(r[4]))  # type: ignore[arg-type]
        for r in wb["Population"].iter_rows(min_row=6, values_only=True)
        if r[0] is not None
    ]
    wb.close()
    frame = pd.DataFrame(rows, columns=["province", "district", "ds"])
    counts: dict[tuple[str, str], int] = {}
    counts[("LK", "gn_division_count")] = len(frame)
    counts[("LK", "ds_division_count")] = len(set(frame["ds"].tolist()))
    for col in ("province", "district"):
        for code, grp in frame.groupby(col):
            counts[(f"LK{code}", "gn_division_count")] = len(grp)
            counts[(f"LK{code}", "ds_division_count")] = len(set(grp["ds"].tolist()))
    for code, grp in frame.groupby("ds"):
        geo = ds_map.get(str(code))
        if geo is not None and _level(geo) == "ds":
            counts[(geo, "gn_division_count")] = len(grp)
    return counts


def ds_code_map(observations: pd.DataFrame) -> dict[str, str]:
    """DCS DS code -> release geography id, read from the aggregate source locators."""
    out: dict[str, str] = {}
    pop = observations[observations["indicator_id"] == "population_total"]
    for geo, loc in zip(pop["geography_id"], pop["source_locator"], strict=True):
        m = SUM_RE.search(str(loc))
        if m and m[2] == "ds":
            out[m[3]] = str(geo)
    return out


def _claim(source: dict[str, str], value: float | None, locator: str, preferred: bool) -> dict:
    return {**source, "value": value, "locator": locator, "preferred": preferred}


def _summary(
    geo: str, indicator: str, claims: list[dict[str, Any]], note: str, reason: str = ""
) -> dict:
    values = [c["value"] for c in claims if c["value"] is not None]
    spread = (max(values) - min(values)) if values else None
    missing = len(values) < len(claims)
    return {
        "geography_id": geo,
        "indicator_id": indicator,
        "label": INDICATORS[indicator],
        "claims": claims,
        "n_sources": len(claims),
        "spread": spread,
        "relative_spread": round(spread / max(values), 6) if values and max(values) else None,
        "agree": not missing and spread == 0,
        "preferred_reason": reason,
        "note": note,
    }


COUNT_NOTE = (
    "COD-AB is the boundary set this atlas maps; DCS lists the divisions it enumerated in the "
    "2024 census. Counts can differ because of the reference date or how units are split or "
    "matched; the crosswalk QA report lists the unit-level differences."
)
COUNT_REASON = "This atlas maps COD-AB v03 units, so its place pages count those."
VALUE_REASON = "The value this atlas publishes, traced to workbook rows."
VALUE_NOTE = (
    "The published value is the sum of the GN workbook rows. The Final Report prints the same "
    "total in a table; both are DCS publications of the same census."
)


def compare(
    observations: pd.DataFrame,
    geographies: pd.DataFrame,
    pop_xlsx: Path,
    report_csv: Path,
) -> Comparisons:
    cod = cod_ab_counts(geographies)
    dcs = dcs_counts(pop_xlsx, ds_code_map(observations))
    report = pd.read_csv(report_csv, dtype={"geography_id": str})
    published = observations.set_index(["geography_id", "indicator_id"])["value"].to_dict()

    summaries: list[dict[str, Any]] = []
    places = sorted({k[0] for k in cod} | {k[0] for k in dcs})
    for geo in places:
        level = _level(geo)
        if level is None:
            continue
        for indicator in ("gn_division_count", "ds_division_count"):
            if level == "ds" and indicator == "ds_division_count":
                continue
            a, b = cod.get((geo, indicator)), dcs.get((geo, indicator))
            if a is None and b is None:
                continue
            claims = [
                _claim(COD_AB, a, "child units in the COD-AB v03 admin layers", True),
                _claim(
                    DCS_WORKBOOK,
                    b,
                    "rows of GN_population.xlsx by DCS code"
                    if b is not None
                    else "no DCS division maps to this unit",
                    False,
                ),
            ]
            summaries.append(_summary(geo, indicator, claims, COUNT_NOTE, COUNT_REASON))
    for r in report.to_dict("records"):
        geo, indicator = str(r["geography_id"]), str(r["indicator_id"])
        value = published.get((geo, indicator))
        claims = [
            _claim(
                DCS_WORKBOOK,
                None if value is None else float(value),  # type: ignore[arg-type]
                "sum of GN_population.xlsx / GN_housing.xlsx rows (the published value)",
                True,
            ),
            _claim(
                DCS_REPORT,
                float(r["value"]),
                f"{r['table']}, PDF page {r['pdf_page']} (printed {r['printed_page']})",
                False,
            ),
        ]
        summaries.append(_summary(geo, indicator, claims, VALUE_NOTE, VALUE_REASON))

    rows = []
    by_place: dict[str, list[dict[str, Any]]] = {}
    for s in summaries:
        by_place.setdefault(s["geography_id"], []).append(s)
        for c in s["claims"]:
            rows.append(
                {
                    "geography_id": s["geography_id"],
                    "indicator_id": s["indicator_id"],
                    "source_id": c["source_id"],
                    "value": c["value"],
                    "reference_date": c["reference_date"],
                    "locator": c["locator"],
                    "preferred": c["preferred"],
                    "spread": s["spread"],
                    "relative_spread": s["relative_spread"],
                    "agree": s["agree"],
                }
            )
    return Comparisons(pd.DataFrame(rows), by_place)


def qa_markdown(c: Comparisons) -> str:
    t = c.table.drop_duplicates(["geography_id", "indicator_id"])
    lines = [
        "# Source comparisons (D-019)",
        "",
        "Generated by the release build. Claims from different publishable sources about the same "
        "place; a difference is reported, not resolved.",
        "",
        "| Indicator | Places compared | Agree | Differ |",
        "|---|---|---|---|",
    ]
    for ind, g in t.groupby("indicator_id", sort=True):
        agree = g["agree"].tolist().count(True)
        lines.append(f"| `{ind}` | {len(g)} | {agree} | {len(g) - agree} |")
    differ = c.table[~c.table["agree"]]
    lines += ["", "## Differences", ""]
    if differ.empty:
        lines.append("None.")
    else:
        wide = differ.pivot_table(
            index=["geography_id", "indicator_id"],
            columns="source_id",
            values="value",
            aggfunc="first",
        ).reset_index()
        cols = [c for c in wide.columns if c not in ("geography_id", "indicator_id")]
        lines += [
            "| Place | Indicator | " + " | ".join(cols) + " |",
            "|---|---|" + "---|" * len(cols),
        ]
        for r in wide.to_dict("records"):
            vals = ["n/a" if pd.isna(r[k]) else f"{int(r[k]):,}" for k in cols]
            lines.append(
                f"| `{r['geography_id']}` | `{r['indicator_id']}` | " + " | ".join(vals) + " |"
            )
    return "\n".join(lines) + "\n"
