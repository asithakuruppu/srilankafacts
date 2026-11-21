"""Stage 3 sub-national indicators from held open tables keyed by OCHA p-code.

Each table already carries the spine's own p-codes (LK1 to LK9, LK11 to LK92), so rows join
by id. A code not in the spine is reported, never forced (rules 5 and 6). Values are copied
or summed from the source with the arithmetic stated in each row's `source_locator`; nothing
is modelled here beyond what the source already models.

- OPHI MPI (SLDHS 2016): province and national survey estimates, copied.
- WFP/CHIRPS rainfall: the latest complete calendar year's total (sum of 36 dekads) and the
  source's long-term average for the same dekads; anomaly = total / average - 1. The country
  figure is the mean depth over districts weighted by the source's pixel counts.
- WFP/MODIS NDVI: the latest complete year's mean of the 36 dekadal values, and the same
  mean of the source's long-term averages.
- HeiGIT Rural Access Index: share of rural population within 2 km of a paved road,
  by district, copied.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import pandas as pd


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
    group: str = "Beyond the census"


SPECS: list[Spec] = [
    Spec(
        "mpi",
        "Multidimensional Poverty Index",
        "ophi-mpi",
        "index",
        4,
        "index",
        "OPHI's Multidimensional Poverty Index from the 2016 Sri Lanka Demographic and Health "
        "Survey: share of people who are poor times the average intensity of their deprivation.",
        "survey_estimate",
        "province (survey sample)",
        "lower_is_better",
        "Poverty (DHS 2016)",
    ),
    Spec(
        "mpi_headcount",
        "People in multidimensional poverty",
        "ophi-mpi",
        "percent",
        2,
        "share",
        "Share of people deprived in at least one third of the weighted MPI indicators "
        "(SLDHS 2016, OPHI).",
        "survey_estimate",
        "province (survey sample)",
        "lower_is_better",
        "Poverty (DHS 2016)",
    ),
    Spec(
        "mpi_intensity",
        "Intensity of deprivation among the poor",
        "ophi-mpi",
        "percent",
        2,
        "share",
        "Average share of weighted indicators in which poor people are deprived "
        "(SLDHS 2016, OPHI).",
        "survey_estimate",
        "province (survey sample)",
        "lower_is_better",
        "Poverty (DHS 2016)",
    ),
    Spec(
        "mpi_vulnerable",
        "People vulnerable to poverty",
        "ophi-mpi",
        "percent",
        2,
        "share",
        "Share of people deprived in 20% to 33% of the weighted indicators (SLDHS 2016, OPHI).",
        "survey_estimate",
        "province (survey sample)",
        "lower_is_better",
        "Poverty (DHS 2016)",
    ),
    Spec(
        "mpi_severe",
        "People in severe poverty",
        "ophi-mpi",
        "percent",
        2,
        "share",
        "Share of people deprived in at least half of the weighted indicators (SLDHS 2016, OPHI).",
        "survey_estimate",
        "province (survey sample)",
        "lower_is_better",
        "Poverty (DHS 2016)",
    ),
    Spec(
        "rainfall_annual",
        "Rainfall in the latest full year",
        "wfp-chirps-rainfall-subnational",
        "millimetres",
        0,
        "mean",
        "Total rainfall over the calendar year, CHIRPS estimates "
        "(satellite and gauges) averaged over the place by WFP.",
        "modelled_estimate",
        "grid-5km",
        group="Climate and vegetation",
    ),
    Spec(
        "rainfall_annual_normal",
        "Long-term average yearly rainfall",
        "wfp-chirps-rainfall-subnational",
        "millimetres",
        0,
        "mean",
        "Sum of WFP's long-term average rainfall for each ten-day period of the year (CHIRPS).",
        "modelled_estimate",
        "grid-5km",
        group="Climate and vegetation",
    ),
    Spec(
        "rainfall_annual_anomaly",
        "Rainfall against the long-term average",
        "wfp-chirps-rainfall-subnational",
        "percent",
        1,
        "ratio",
        "Latest full year's rainfall as a percentage above (+) or below (-) the long-term average.",
        "modelled_estimate",
        "grid-5km",
        group="Climate and vegetation",
    ),
    Spec(
        "ndvi_annual_mean",
        "Vegetation greenness (NDVI), latest full year",
        "wfp-ndvi-subnational",
        "index",
        3,
        "mean",
        "Mean MODIS Normalised Difference "
        "Vegetation Index over the year (WFP, 36 ten-day values); 0 bare, near 1 dense green.",
        "modelled_estimate",
        "grid-250m",
        group="Climate and vegetation",
    ),
    Spec(
        "ndvi_annual_normal",
        "Long-term average vegetation greenness (NDVI)",
        "wfp-ndvi-subnational",
        "index",
        3,
        "mean",
        "Mean of WFP's long-term average NDVI for each ten-day period of the year (MODIS).",
        "modelled_estimate",
        "grid-250m",
        group="Climate and vegetation",
    ),
    Spec(
        "ndvi_annual_anomaly",
        "Vegetation greenness against the long-term average",
        "wfp-ndvi-subnational",
        "percent",
        1,
        "ratio",
        "Latest full year's mean NDVI as a "
        "percentage above or below the mean of WFP's long-term averages.",
        "modelled_estimate",
        "grid-250m",
        group="Climate and vegetation",
    ),
    Spec(
        "rural_access_index",
        "Rural Access Index",
        "heigit-risk-indicators",
        "percent",
        1,
        "share",
        "Share of the rural population living within 2 km of a paved road "
        "(HeiGIT, from Mapillary and Planet road-surface classification and a modelled "
        "population grid).",
        "modelled_estimate",
        "grid-100m",
        "higher_is_better",
        "Access",
    ),
]
SPEC_BY_ID = {spec.id: spec for spec in SPECS}


def _latest(
    raw_root: Path, source: str, dataset: str, filename: str
) -> tuple[Path, dict[str, Any]]:
    files = sorted((raw_root / source / dataset).glob(f"*/{filename}"))
    if not files:
        raise FileNotFoundError(f"{source}/{dataset}/*/{filename}")
    path = files[-1]
    meta = json.loads(path.with_name(path.name + ".meta.json").read_text())
    return path, meta


def _row(
    spec: Spec,
    gid: str,
    period: str,
    value: float,
    meta: dict[str, Any],
    locator: str,
    start: str,
    end: str,
) -> dict[str, Any]:
    return {
        "claim_id": f"{spec.dataset}:{gid}:{spec.id}:{period}",
        "indicator_id": spec.id,
        "geography_id": gid,
        "period": period,
        "time_start": start,
        "time_end": end,
        "value": value,
        "value_status": "normal",
        "unit": spec.unit,
        "information_footprint_ref": spec.floor,
        "data_nature": spec.data_nature,
        "verification": "machine_extracted",
        "dataset_id": spec.dataset,
        "snapshot_sha256": meta["sha256"],
        "source_url": meta.get("url"),
        "source_locator": locator,
        "breakdown": None,
    }


def _ophi(raw: Path, valid: set[str], unmatched: list[str]) -> list[dict[str, Any]]:
    path, meta = _latest(raw, "ophi", "ophi-mpi", "lka_mpi.csv")
    table = pd.read_csv(path, dtype=str)
    columns = {
        "mpi": "MPI",
        "mpi_headcount": "Headcount Ratio",
        "mpi_intensity": "Intensity of Deprivation",
        "mpi_vulnerable": "Vulnerable to Poverty",
        "mpi_severe": "In Severe Poverty",
    }
    rows = []
    for index, record in enumerate(cast(list[dict[str, Any]], table.to_dict("records"))):
        code = record.get("Admin 1 PCode")
        gid = "LK" if not isinstance(code, str) or not code.strip() else code.strip()
        if gid not in valid:
            unmatched.append(f"ophi-mpi: {gid}")
            continue
        for indicator, column in columns.items():
            rows.append(
                _row(
                    SPEC_BY_ID[indicator],
                    gid,
                    "2016",
                    float(record[column]),
                    meta,
                    f"{path.name}, row {index + 2}, column '{column}'",
                    "2016-01-01",
                    "2016-12-31",
                )
            )
    return rows


def _dekadal(
    path: Path,
    meta: dict[str, Any],
    value: str,
    average: str,
    how: str,
    valid: set[str],
    unmatched: list[str],
    ids: tuple[str, str, str],
) -> list[dict[str, Any]]:
    records = cast(list[dict[str, Any]], pd.read_csv(path, dtype={"PCODE": str}).to_dict("records"))
    by_year: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for record in records:
        year_of = str(record["date"])[:4]
        by_year.setdefault(year_of, {}).setdefault(str(record["PCODE"]), []).append(record)
    districts = {str(r["PCODE"]) for r in records if int(r["adm_level"]) == 2}
    complete = sorted(
        y for y, places in by_year.items() if all(len(places.get(d, [])) == 36 for d in districts)
    )
    if not complete:
        return []
    year = complete[-1]
    rows: list[dict[str, Any]] = []
    pixels: dict[str, float] = {}
    totals: dict[str, tuple[float, float]] = {}
    for gid, group in sorted(by_year[year].items()):
        if gid not in valid:
            unmatched.append(f"{meta['key']}: {gid}")
            continue
        observed_values = [r[value] for r in group]
        normal_values = [r[average] for r in group]
        if len(group) != 36 or any(pd.isna(v) for v in observed_values + normal_values):
            unmatched.append(f"{meta['key']}: {gid} incomplete in {year}")
            continue
        observed = float(sum(float(v) for v in observed_values))
        normal = float(sum(float(v) for v in normal_values))
        if how != "sum":
            observed, normal = observed / 36, normal / 36
        totals[gid] = (observed, normal)
        if int(group[0]["adm_level"]) == 2:
            pixels[gid] = float(group[0]["n_pixels"])
    if pixels:
        weight = sum(pixels.values())
        totals["LK"] = (
            sum(totals[g][0] * pixels[g] for g in pixels) / weight,
            sum(totals[g][1] * pixels[g] for g in pixels) / weight,
        )
    verb = "sum" if how == "sum" else "mean"
    for gid, (observed, normal) in sorted(totals.items()):
        where = (
            "pixel-weighted mean of the 25 district values"
            if gid == "LK"
            else f"PCODE {gid}, {year}-01-01 to {year}-12-21"
        )
        start, end = f"{year}-01-01", f"{year}-12-31"
        rows.append(
            _row(
                SPEC_BY_ID[ids[0]],
                gid,
                year,
                round(observed, 4),
                meta,
                f"{path.name}: {verb} of '{value}' over 36 dekads; {where}",
                start,
                end,
            )
        )
        rows.append(
            _row(
                SPEC_BY_ID[ids[1]],
                gid,
                year,
                round(normal, 4),
                meta,
                f"{path.name}: {verb} of '{average}' over 36 dekads; {where}",
                start,
                end,
            )
        )
        if ids[2]:
            rows.append(
                _row(
                    SPEC_BY_ID[ids[2]],
                    gid,
                    year,
                    round((observed / normal - 1) * 100, 2),
                    meta,
                    f"{path.name}: ({verb} '{value}' / {verb} '{average}' - 1) * 100; {where}",
                    start,
                    end,
                )
            )
    return rows


def _heigit(raw: Path, valid: set[str], unmatched: list[str]) -> list[dict[str, Any]]:
    path, meta = _latest(raw, "heigit", "heigit-risk-indicators", "LKA_ADM2_rai.csv")
    table = pd.read_csv(path, dtype={"ADM2_PCODE": str})
    rows = []
    for index, record in enumerate(cast(list[dict[str, Any]], table.to_dict("records"))):
        gid = str(record["ADM2_PCODE"])
        if gid not in valid:
            unmatched.append(f"heigit RAI: {gid}")
            continue
        rows.append(
            _row(
                SPEC_BY_ID["rural_access_index"],
                gid,
                "2026",
                float(record["RAI_total_pop"]),
                meta,
                f"{path.name}, row {index + 2}, column 'RAI_total_pop'",
                "2026-01-01",
                "2026-12-31",
            )
        )
    return rows


def build(raw_root: Path, spine_dir: Path, out_dir: Path) -> dict[str, Any]:
    valid = set(pd.read_parquet(spine_dir / "geographies.parquet")["geography_id"].astype(str))
    unmatched: list[str] = []
    failed: list[str] = []
    rows: list[dict[str, Any]] = []
    steps = {
        "ophi-mpi": lambda: _ophi(raw_root, valid, unmatched),
        "wfp-chirps-rainfall-subnational": lambda: _dekadal(
            *_latest(
                raw_root, "wfp", "wfp-chirps-rainfall-subnational", "lka-rainfall-subnat-full.csv"
            ),
            "rfh",
            "rfh_avg",
            "sum",
            valid,
            unmatched,
            ("rainfall_annual", "rainfall_annual_normal", "rainfall_annual_anomaly"),
        ),
        "wfp-ndvi-subnational": lambda: _ndvi(raw_root, valid, unmatched),
        "heigit-risk-indicators": lambda: _heigit(raw_root, valid, unmatched),
    }
    for name, step in steps.items():
        try:
            rows += step()
        except FileNotFoundError as missing:
            failed.append(f"{name}: not held ({missing})")
    out_dir.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    frame.to_parquet(out_dir / "observations.parquet", index=False)
    summary = {
        "rows": len(rows),
        "indicators": sorted({r["indicator_id"] for r in rows}),
        "unmatched_or_incomplete": unmatched,
        "not_held": failed,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    lines = [
        "# QA: Stage 3 sub-national indicators (p-coded open tables)",
        "",
        f"Rows: {len(rows)}. Indicators: {len(summary['indicators'])}.",
        "",
        "| Indicator | Places | Period | Min | Max |",
        "|---|---:|---|---:|---:|",
    ]
    for indicator, group in frame.groupby("indicator_id") if rows else []:
        lines.append(
            f"| {indicator} | {len(group)} | {', '.join(sorted(set(group['period'])))} | "
            f"{group['value'].min():.4g} | {group['value'].max():.4g} |"
        )
    lines += ["", "Unmatched or incomplete:", *[f"- {u}" for u in unmatched or ["none"]]]
    lines += ["", "Not held:", *[f"- {u}" for u in failed or ["none"]], ""]
    (out_dir / "qa.md").write_text("\n".join(lines))
    return summary


def _ndvi(raw: Path, valid: set[str], unmatched: list[str]) -> list[dict[str, Any]]:
    path, meta = _latest(raw, "wfp", "wfp-ndvi-subnational", "lka-ndvi-subnat-full.csv")
    return _dekadal(
        path,
        meta,
        "vim",
        "vim_avg",
        "mean",
        valid,
        unmatched,
        ("ndvi_annual_mean", "ndvi_annual_normal", "ndvi_annual_anomaly"),
    )
