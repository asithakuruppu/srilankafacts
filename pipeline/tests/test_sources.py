"""Source comparisons (D-019) and the Final Report reference table."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from slf import final_report, sources
from slf.datasets import census_2024_gnd as census

REPO = Path(__file__).resolve().parents[2]
REPORT = REPO / "catalog" / "references" / "dcs-cph2024-final-report-tables.csv"


def test_reference_csv_matches_the_ingest_anchors():
    ref = pd.read_csv(REPORT, dtype={"geography_id": str})

    def values(indicator: str) -> dict[str, int]:
        rows = ref.loc[ref["indicator_id"] == indicator]
        return dict(zip(rows["geography_id"].tolist(), rows["value"].tolist(), strict=True))

    pop, housing = values("population_total"), values("occupied_housing_units")
    assert len(pop) == 35 and len(housing) == 26  # country + 9 provinces + 25 districts
    assert pop["LK"] == census.EXPECTED_NATIONAL["population_total"]
    assert housing["LK"] == census.EXPECTED_NATIONAL["occupied_housing_units"]
    for code, value in census.EXPECTED_DISTRICTS_POP.items():
        assert pop[f"LK{code}"] == value
    for code, value in census.EXPECTED_DISTRICTS_HOUSING.items():
        assert housing[f"LK{code}"] == value
    assert set(ref["verification"]) == {"machine_extracted"}


def test_final_report_table_parsing():
    text = "Sri Lanka 21,781,800 100.0\nWestern Province 6,117,341 28.1\n"
    text += "Colombo 562,550 78,052 654,051 113,837\nNote: rounded to 1 place"
    assert final_report.parse_table(text) == {
        "Sri Lanka": 21_781_800,
        "Western Province": 6_117_341,
        "Colombo": 654_051,
    }


def test_cod_ab_counts_roll_up_and_skip_provisional_units():
    geos = pd.DataFrame(
        {
            "geography_id": [
                "LK",
                "LK1",
                "LK11",
                "LK1103",
                "LK1103005",
                "LK1103010",
                "LK-ADM3-P0001",
            ],
            "level": [0, 1, 2, 3, 4, 4, 3],
            "parent_id": [None, "LK", "LK1", "LK11", "LK1103", "LK1103", "LK11"],
            "status": ["current"] * 6 + ["provisional"],
        }
    )
    counts = sources.cod_ab_counts(geos)
    assert counts[("LK1103", "gn_division_count")] == 2
    assert counts[("LK", "gn_division_count")] == 2
    assert counts[("LK11", "ds_division_count")] == 1  # provisional unit not counted


def test_summary_flags_differences_and_missing_claims():
    def claim(v: float | None) -> dict:
        return sources._claim(sources.COD_AB, v, "x", True)

    same = sources._summary("LK", "gn_division_count", [claim(10), claim(10)], "")
    diff = sources._summary("LK", "gn_division_count", [claim(10), claim(8)], "")
    gap = sources._summary("LK", "gn_division_count", [claim(10), claim(None)], "")
    assert same["agree"] and same["spread"] == 0
    assert not diff["agree"] and diff["spread"] == 2 and diff["relative_spread"] == 0.2
    assert not gap["agree"]


def test_ds_code_map_reads_aggregate_locators():
    obs = pd.DataFrame(
        {
            "geography_id": ["LK1103", "LK-ADM3-P0001", "LK1103005"],
            "indicator_id": ["population_total"] * 3,
            "source_locator": [
                "... 35 GN rows summed to ds 1103; row range 6-40",
                "... 29 GN rows summed to ds 5221; row range 8298-8326",
                "GN_population.xlsx, sheet 'Population', row 6, column 9 ('Total')",
            ],
        }
    )
    assert sources.ds_code_map(obs) == {"1103": "LK1103", "5221": "LK-ADM3-P0001"}
