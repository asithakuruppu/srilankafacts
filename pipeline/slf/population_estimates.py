"""National annual population estimates 1891-1946 (Harvard Dataverse, Chandra & Sarathchandra).

The held table has one row per year for the whole island and two columns: an estimate for all
districts and one for non-plantation districts. It is national only (no districts), and the
values follow one constant growth rate (apart from a repeated 1918), so they are a smooth
reconstruction, not yearly counts.
Each value is copied with its row number; nothing is modelled here. The all-districts series is
checked against the census totals in DCS Statistical Abstract 2024 Table 2.1 (held in
``catalog/references``) for the years both have.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pandas as pd

DATASET = "population-trajectory-1891-1946"
SOURCE = "harvard-dataverse"
FILENAME = "Population.Trajectory.SriLanka.Ceylon.1891_1946.copy.v1.tab"
COLUMNS = {
    "population_estimated_all_districts": "EstimatedPopulationAllDistrictsIncluding1946Data",
    "population_estimated_nonplantation": (
        "EstimatedPopulationNonplantationDistrictsIncluding1946Data"
    ),
}
FLOOR = "country (annual national estimate on a smooth curve; not a yearly count)"


def _latest(raw_root: Path) -> tuple[Path, dict[str, Any]]:
    files = sorted((raw_root / SOURCE / DATASET).glob(f"*/{FILENAME}"))
    if not files:
        raise FileNotFoundError(f"{SOURCE}/{DATASET}/*/{FILENAME}")
    path = files[-1]
    return path, json.loads(path.with_name(path.name + ".meta.json").read_text())


def build(raw_root: Path, catalog: Path, out_dir: Path) -> dict[str, Any]:
    path, meta = _latest(raw_root)
    table = pd.read_csv(path, sep="\t", dtype={"Year": str})
    rows: list[dict[str, Any]] = []
    repeated = set(table.Year[table.Year.duplicated(keep=False)])
    for index, record in enumerate(table.to_dict("records")):
        year = str(record["Year"])
        repeat = (
            f"; the year {year} appears twice in the source with different values and the file "
            "does not say which is which (kept in file order)"
            if year in repeated
            else ""
        )
        for indicator, column in COLUMNS.items():
            rows.append(
                {
                    "claim_id": f"{DATASET}:LK:{indicator}:{year}"
                    + (f":row{index + 2}" if year in repeated else ""),
                    "indicator_id": indicator,
                    "geography_id": "LK",
                    "period": year,
                    "time_start": f"{year}-01-01",
                    "time_end": f"{year}-12-31",
                    "value": round(float(record[column]), 0),
                    "value_status": "normal",
                    "unit": "persons",
                    "information_footprint_ref": FLOOR,
                    "data_nature": "reconstruction",
                    "verification": "machine_extracted",
                    "dataset_id": DATASET,
                    "snapshot_sha256": meta["sha256"],
                    "source_url": meta.get("url"),
                    "source_locator": (
                        f"{path.name}, data row {index + 2}, column '{column}'{repeat}"
                    ),
                    "breakdown": None,
                }
            )
    frame = pd.DataFrame(rows)

    series = table[COLUMNS["population_estimated_all_districts"]]
    growth = series.pct_change().dropna()
    jumps = growth[growth.round(6) != growth.round(6).mode().iloc[0]]
    estimates = table.drop_duplicates("Year", keep=False).set_index(
        table.drop_duplicates("Year", keep=False).Year.astype(int)
    )[COLUMNS["population_estimated_all_districts"]]
    census = pd.read_csv(
        catalog / "references/dcs-abstract2024-table2.1-transcription.csv", dtype=str
    )
    island = census[census.district == "Sri Lanka"].iloc[0]
    checks: list[dict[str, float]] = []
    for year in estimates.index:
        text = island.get(str(year))
        if text is None or text == "..":
            continue
        dcs = float(text) * 1000
        estimate = float(cast(float, estimates[year]))
        checks.append(
            {
                "year": int(year),
                "estimate_all_districts": estimate,
                "dcs_table_2_1_persons": dcs,
                "difference_percent": round(100 * (estimate / dcs - 1), 2),
            }
        )
    out_dir.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(out_dir / "observations.parquet", index=False)
    check_frame = pd.DataFrame(checks)
    check_frame.to_csv(out_dir / "crosscheck_dcs_table_2_1.csv", index=False)
    lines = [
        "# QA: national population estimates 1891-1946",
        "",
        f"Rows: {len(frame)} ({frame.indicator_id.nunique()} indicators, "
        f"{frame.period.nunique()} years, country only). "
        f"Source file sha256 `{meta['sha256'][:16]}`.",
        "",
        "## Is it interpolated? (computed)",
        "",
        f"{len(growth) - len(jumps)} of the {len(growth)} year-to-year steps in the all-districts "
        f"series have the same growth rate ({growth.round(6).mode().iloc[0]:.4%} a year), "
        "so the series "
        "follows one smooth curve, not yearly counts. The one other step is a fall of about 6% "
        f"between the two rows for {', '.join(sorted(repeated)) or 'no year'}: the year appears "
        "twice with different values, which the file does not explain (the influenza pandemic "
        "year ❓). Both rows are kept with distinct claim ids and that year is left out of the "
        "cross-check.",
        "",
        "## Cross-check against DCS Statistical Abstract 2024 Table 2.1 (census totals)",
        "",
        "| Year | Estimate (all districts) | DCS census total | Difference |",
        "|---|---:|---:|---:|",
    ]
    for r in checks:
        lines.append(
            f"| {r['year']} | {r['estimate_all_districts']:,.0f} "
            f"| {r['dcs_table_2_1_persons']:,.0f} | {r['difference_percent']:+.2f}% |"
        )
    lines += [
        "",
        "The census totals are DCS's own transcribed figures; the estimate series is the "
        "source's reconstruction and is not expected to equal them.",
        "",
    ]
    (out_dir / "qa.md").write_text("\n".join(lines))
    return {
        "rows": len(frame),
        "years": f"{estimates.index.min()}-{estimates.index.max()}",
        "crosscheck_years": [c["year"] for c in checks],
        "max_abs_difference_percent": float(check_frame.difference_percent.abs().max())
        if len(check_frame)
        else None,
    }
