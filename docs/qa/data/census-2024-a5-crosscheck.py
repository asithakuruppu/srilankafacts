"""Cross-check: DCS Population table A5 (sex and age by DS and district) against the release.

The release's DS, district and national sex and age values (census-2024-gnd-tables) are sums of
GN rows. A5 is DCS's own DS and district table. This script compares every A5 line with the
release, value by value. Run from pipeline/:

    uv run python ../docs/qa/data/census-2024-a5-crosscheck.py <release dir>

DS lines join through the reviewed match file (labels identical to A6/A7) and the G02 crosswalk;
nothing is matched by name here.
"""

from __future__ import annotations

import glob
import sys
from pathlib import Path

import openpyxl
import pandas as pd

from slf.datasets import census_2024_materials as mat
from slf.datasets.census_2024_gnd import _crosswalk, _int_cell

COLUMNS = {  # 0-based column in A5 -> indicator in census-2024-gnd-tables
    2: "population_total",
    3: "population_male",
    4: "population_female",
    5: "population_age_0_14",
    6: "population_age_15_59",
    7: "population_age_60_64",
    8: "population_age_65_plus",
}
# English headings as printed; "15 - 59" uses U+2010 HYPHEN in DCS's file.
HEADINGS = {
    3: "Male",
    4: "Female",
    5: "Less than 15 years",
    6: "15 \u2010 59 Years",
    7: "60-64 Years",
    8: "65 years and over",
}


def main(release: Path) -> None:
    root = Path(__file__).resolve().parents[3]
    path = glob.glob("data/raw/dcs/census-2024-topic-tables/*/PopulationA_A5.xlsx")
    assert len(path) == 1, path
    rows = list(
        openpyxl.load_workbook(path[0], read_only=True, data_only=True)
        .worksheets[0]
        .iter_rows(values_only=True)
    )
    title = " ".join(str(rows[2][1]).split())
    assert title.startswith("A5 : Population by sex, age"), title
    for col, heading in HEADINGS.items():
        assert mat.english(rows[5][col]) == heading, (col, rows[5][col])

    matches = mat.load_matches(
        str(root / "catalog/geographies/name-matches/dcs-census2024-population-a-series-ds.csv")
    )
    _, ds_map = _crosswalk(root / "catalog")
    obs = pd.read_parquet(
        release / "observations" / "census-2024-gnd-tables.parquet",
        columns=["geography_id", "indicator_id", "value"],
    )
    values = obs.set_index(["geography_id", "indicator_id"])["value"].to_dict()
    names = pd.read_parquet(
        release / "geographies.parquet", columns=["geography_id", "name_en", "level"]
    )
    district_ids = {mat.district_key(n): g for g, n, lv in names.itertuples(index=False) if lv == 2}

    compared = differences = skipped = 0
    district_code = ""
    lines = {"country": 0, "district": 0, "ds": 0}
    for line, r in enumerate(rows, start=1):
        if line < 7 or r[1] is None:
            continue
        label = mat.english(r[1])
        if label.endswith("Sri Lanka"):
            kind, geo = "country", "LK"
        elif label.endswith(" District"):
            kind = "district"
            geo = district_ids[mat.district_key(label.removesuffix(" District"))]
            district_code = geo[2:]
        else:
            kind = "ds"
            dcs = matches[(district_code, label)]
            geo = ds_map.get(dcs)
            if geo is None:
                skipped += 1
                print(f"row {line}: {label} (DCS {dcs}) has no spine unit; skipped")
                continue
        lines[kind] += 1
        for col, indicator in COLUMNS.items():
            a5 = _int_cell(r[col], line=line, field=indicator)
            ours = values.get((geo, indicator))
            compared += 1
            if ours is None or int(ours) != a5:
                differences += 1
                print(f"DIFF row {line} {label} -> {geo} {indicator}: A5 {a5}, release {ours}")
    print(f"lines {lines}, skipped {skipped}; {compared} values compared, {differences} differ")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
