"""Cross-check: DCS Housing tables A13-A16 (household amenities by DS) against the release.

The release's DS, district and national household amenity counts (census-2024-topic-tables,
step a) are sums of GN rows from HH_GND_excel. A13 (cooking), A14 (drinking water), A15
(lighting) and A16 (toilets) are DCS's own DS and district tables. Step (a) was checked against
the district tables A5-A8 only; this adds the DS level. Run from pipeline/:

    uv run python ../docs/qa/data/census-2024-a13-a16-crosscheck.py <release dir>

Columns: each table column is mapped to the release count indicator whose national (Sri Lanka)
value equals the column's Sri Lanka value; the mapping must be one-to-one, and is then tested on
every other line. DS lines join through the reviewed Housing A-series match file and the G02
crosswalk; nothing is matched by name here.
"""

from __future__ import annotations

import glob
import sys
from pathlib import Path

import openpyxl
import pandas as pd

from slf.datasets import census_2024_materials as mat
from slf.datasets.census_2024_gnd import _crosswalk, _int_cell

TABLES = {
    "A13": "households_cooking_",
    "A14": "households_water_",
    "A15": "households_lighting_",
    "A16": "households_toilet_",
}


def main(release: Path) -> None:
    root = Path(__file__).resolve().parents[3]
    matches = mat.load_matches(
        str(root / "catalog/geographies/name-matches/dcs-census2024-a-series-ds.csv")
    )
    _, ds_map = _crosswalk(root / "catalog")
    obs = pd.read_parquet(
        release / "observations" / "census-2024-topic-tables.parquet",
        columns=["geography_id", "indicator_id", "value"],
    )
    obs = obs[
        obs["indicator_id"].str.startswith("households_")
        & ~obs["indicator_id"].str.endswith("_share")
    ]
    values = obs.set_index(["geography_id", "indicator_id"])["value"].to_dict()
    names = pd.read_parquet(
        release / "geographies.parquet", columns=["geography_id", "name_en", "level"]
    )
    district_ids = {mat.district_key(n): g for g, n, lv in names.itertuples(index=False) if lv == 2}
    for table, prefix in TABLES.items():
        path = glob.glob(f"data/raw/dcs/census-2024-topic-tables/*/HousingA_{table}.xlsx")
        assert len(path) == 1, path
        rows = list(
            openpyxl.load_workbook(path[0], read_only=True, data_only=True)
            .worksheets[0]
            .iter_rows(values_only=True)
        )
        start = next(
            i for i, r in enumerate(rows) if r and r[0] and mat.english(r[0]).endswith("Sri Lanka")
        )
        data = [(i, r) for i, r in enumerate(rows, start=1) if i > start and r and r[0] is not None]
        first_line, first = data[0]
        assert mat.english(first[0]).endswith("Sri Lanka"), first[0]
        width = max(j for j, c in enumerate(first) if c is not None) + 1
        candidates = {i: v for (g, i), v in values.items() if g == "LK" and i.startswith(prefix)}
        columns: dict[int, str] = {1: "households_total"}
        for col in range(2, width):
            national = _int_cell(first[col], line=first_line, field=f"{table} col {col}")
            hits = [i for i, v in candidates.items() if int(v) == national]
            assert len(hits) == 1, (table, col, national, hits)
            columns[col] = hits[0]
        assert len(set(columns.values())) == len(columns), table
        unmapped = sorted(set(candidates) - set(columns.values()))
        compared = differences = 0
        lines = {"country": 0, "district": 0, "ds": 0}
        district_code = ""
        for line, r in data:
            label = mat.english(r[0])
            if label.endswith("Sri Lanka"):
                kind, geo = "country", "LK"
            elif label.endswith(" District"):
                kind = "district"
                geo = district_ids[mat.district_key(label.removesuffix(" District"))]
                district_code = geo[2:]
            else:
                kind = "ds"
                dcs = matches.get((district_code, label))
                if dcs is None:
                    print(
                        f"{table} row {line}: '{label}' (district {district_code}) "
                        "not in the match file"
                    )
                    continue
                geo = ds_map.get(dcs)
                if geo is None:
                    print(f"{table} row {line}: {label} (DCS {dcs}) has no spine unit; skipped")
                    continue
            lines[kind] += 1
            for col, indicator in columns.items():
                dcs_value = _int_cell(r[col], line=line, field=f"{table} col {col}")
                ours = values.get((geo, indicator))
                compared += 1
                if ours is None or int(ours) != dcs_value:
                    differences += 1
                    print(
                        f"DIFF {table} row {line} {label} -> {geo} {indicator}: "
                        f"{table} {dcs_value}, release {ours}"
                    )
        print(
            f"{table}: {len(columns) - 1} categories mapped, unmapped {unmapped}; lines {lines}; "
            f"{compared} values compared, {differences} differ"
        )


if __name__ == "__main__":
    main(Path(sys.argv[1]))
