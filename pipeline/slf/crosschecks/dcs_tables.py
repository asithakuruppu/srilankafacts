"""DCS's own DS and district tables against the release's GN sums.

- A5 (Population A-series): population by sex and four age bands, every DS and district.
- A13-A16 (Housing A-series): households by cooking fuel, drinking water, lighting and toilets.

Both are checks only; none of their values are published. DS lines join through the reviewed
match files and the G02 crosswalk, never by name.
"""

from __future__ import annotations

import glob
from pathlib import Path

import openpyxl

from slf.crosschecks.common import ROOT, Result, district_ids, values
from slf.datasets import census_2024_materials as mat
from slf.datasets.census_2024_gnd import _crosswalk, _int_cell

TOPIC_RAW = ("dcs", "census-2024-topic-tables")
A5_CHECK = "DCS table A5: sex and age, Sri Lanka, districts and DS"
A5_COLUMNS = {
    2: "population_total",
    3: "population_male",
    4: "population_female",
    5: "population_age_0_14",
    6: "population_age_15_59",
    7: "population_age_60_64",
    8: "population_age_65_plus",
}
# English headings as printed; "15 - 59" uses U+2010 HYPHEN in DCS's file.
A5_HEADINGS = {
    3: "Male",
    4: "Female",
    5: "Less than 15 years",
    6: "15 \u2010 59 Years",
    7: "60-64 Years",
    8: "65 years and over",
}
AMENITY_TABLES = {
    "A13": "households_cooking_",
    "A14": "households_water_",
    "A15": "households_lighting_",
    "A16": "households_toilet_",
}


def _rows(raw_dir: Path, name: str, notes: list[str]) -> list[tuple[object, ...]]:
    """Rows of the newest snapshot of a check-only file (these files are not in the release, so
    there is no recorded sha256 to look up). The file used is added to ``notes``."""
    paths = sorted(glob.glob(str(raw_dir.joinpath(*TOPIC_RAW) / "*" / name)))
    if not paths:
        raise FileNotFoundError(f"no snapshot of {name} under {raw_dir.joinpath(*TOPIC_RAW)}")
    notes.append(f"{name}: snapshot {Path(paths[-1]).parent.name}")
    wb = openpyxl.load_workbook(paths[-1], read_only=True, data_only=True)
    rows: list[tuple[object, ...]] = []
    for r in wb.worksheets[0].iter_rows(values_only=True):
        rows.append(tuple(r))
    wb.close()
    return rows


def _place(
    label: str,
    district: str,
    places: dict[str, str],
    matches: dict[tuple[str, str], str],
    ds_map: dict[str, str],
) -> tuple[str, str | None, str]:
    """(kind, spine id or None, district code) for one A-series line label."""
    if label.endswith("Sri Lanka"):
        return "country", "LK", district
    if label.endswith(" District"):
        geo = places[mat.district_key(label.removesuffix(" District"))]
        return "district", geo, geo[2:]
    dcs = matches.get((district, label))
    if dcs is None:
        raise ValueError(f"'{label}' (district {district}) is not in the match file")
    return "ds", ds_map.get(dcs), district


def a5(release: Path, raw_dir: Path) -> Result:
    result = Result(A5_CHECK)
    rows = _rows(raw_dir, "PopulationA_A5.xlsx", result.notes)
    title = " ".join(str(rows[2][1]).split())
    if not title.startswith("A5 : Population by sex, age"):
        raise ValueError(f"A5: unexpected title {title!r}")
    for col, heading in A5_HEADINGS.items():
        if mat.english(rows[5][col]) != heading:
            raise ValueError(f"A5 column {col + 1}: heading {rows[5][col]!r}")
    matches = mat.load_matches(
        str(ROOT / "catalog/geographies/name-matches/dcs-census2024-population-a-series-ds.csv")
    )
    _, ds_map = _crosswalk(ROOT / "catalog")
    ours = values(release, "census-2024-gnd-tables")
    places = district_ids(release)
    district = ""
    for line, r in enumerate(rows, start=1):
        if line < 7 or r[1] is None:
            continue
        label = mat.english(r[1])
        _kind, geo, district = _place(label, district, places, matches, ds_map)
        if geo is None:
            result.notes.append(f"row {line}: {label} has no spine unit (D-022); skipped")
            continue
        for col, indicator in A5_COLUMNS.items():
            dcs_value = _int_cell(r[col], line=line, field=indicator)
            got = ours.get((geo, indicator))
            result.compared += 1
            if got is None or int(got) != dcs_value:
                result.differences[f"{geo} {indicator}"] = (
                    f"A5 row {line} {label}: A5 {dcs_value}, release {got}"
                )
    return result


def a13_a16(release: Path, raw_dir: Path) -> list[Result]:
    matches = mat.load_matches(
        str(ROOT / "catalog/geographies/name-matches/dcs-census2024-a-series-ds.csv")
    )
    _, ds_map = _crosswalk(ROOT / "catalog")
    ours = {
        k: v
        for k, v in values(release, "census-2024-topic-tables").items()
        if k[1].startswith("households_") and not k[1].endswith("_share")
    }
    places = district_ids(release)
    results = []
    for table, prefix in AMENITY_TABLES.items():
        result = Result(f"DCS table {table}: households by {prefix[11:-1]}, districts and DS")
        rows = _rows(raw_dir, f"HousingA_{table}.xlsx", result.notes)
        start = next(
            i for i, r in enumerate(rows) if r and r[0] and mat.english(r[0]).endswith("Sri Lanka")
        )
        data = [(i, r) for i, r in enumerate(rows, start=1) if i > start and r and r[0] is not None]
        first_line, first = data[0]
        width = max(j for j, c in enumerate(first) if c is not None) + 1
        candidates = {i: v for (g, i), v in ours.items() if g == "LK" and i.startswith(prefix)}
        # Map each column to the release indicator with the same national value (one-to-one).
        columns: dict[int, str] = {1: "households_total"}
        for col in range(2, width):
            national = _int_cell(first[col], line=first_line, field=f"{table} col {col}")
            hits = [i for i, v in candidates.items() if int(v) == national]
            if len(hits) != 1:
                raise ValueError(
                    f"{table} column {col + 1}: {len(hits)} indicators match {national}"
                )
            columns[col] = hits[0]
        if len(set(columns.values())) != len(columns):
            raise ValueError(f"{table}: two columns map to one indicator")
        district = ""
        for line, r in data:
            label = mat.english(r[0])
            _kind, geo, district = _place(label, district, places, matches, ds_map)
            if geo is None:
                result.notes.append(f"row {line}: {label} has no spine unit (D-022); skipped")
                continue
            for col, indicator in columns.items():
                dcs_value = _int_cell(r[col], line=line, field=f"{table} col {col}")
                got = ours.get((geo, indicator))
                result.compared += 1
                if got is None or int(got) != dcs_value:
                    result.differences[f"{geo} {indicator}"] = (
                        f"{table} row {line} {label}: {table} {dcs_value}, release {got}"
                    )
        results.append(result)
    return results
