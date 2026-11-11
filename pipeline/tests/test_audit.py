"""Q01 audit helpers: the checks must be able to fail."""

from __future__ import annotations

import pandas as pd
import pytest

from slf import audit


def _raw() -> audit.Raw:
    # Two GN rows in DS 1103 (district 11, province 1), Excel rows 6 and 7.
    pop = pd.DataFrame(
        {
            0: [1, 1],
            1: ["Western", "Western"],
            2: [11, 11],
            3: ["Colombo", "Colombo"],
            4: [3, 3],
            6: [5, 10],
            7: ["A", "B"],
            9: [100, 50],
            10: [40, 20],
            11: [60, 30],
            13: [20, 10],
            14: [60, 30],
            15: [5, 5],
            16: [15, 5],
        },
        index=pd.Index([6, 7], name="excel_row"),
    )
    housing = pop[[0, 1, 2, 3, 4, 6, 7]].assign(**{"9": [25, 10]}).rename(columns={"9": 9})
    for f in (pop, housing):
        f["district"] = f[2]
        f["ds"] = f["district"] * 100 + f[4]
        f["gn"] = f["ds"] * 1000 + f[6]
        f["province"] = f[0]
    return audit.Raw(pop, housing, None, None, {})  # type: ignore[arg-type]


CODES = {"LK1103005": "1103005", "LK1103010": "1103010"}


def _row(geo: str, ind: str, loc: str) -> pd.Series:
    return pd.Series({"geography_id": geo, "indicator_id": ind, "source_locator": loc})


def test_excel_column_letters():
    assert [audit.excel_column(i) for i in (0, 9, 25, 26)] == ["A", "J", "Z", "AA"]


def test_cell_trace_reads_the_cell_and_checks_row_identity():
    loc = "GN_population.xlsx, sheet 'Population', row 7, column 9 ('Total')"
    t = audit.trace(_row("LK1103010", "population_total", loc), _raw(), {}, CODES)
    assert t.expected == 50 and t.row_identity_ok
    wrong = audit.trace(_row("LK1103005", "population_total", loc), _raw(), {}, CODES)
    assert wrong.row_identity_ok is False


def test_sum_and_derived_traces():
    loc = "… 2 GN rows summed to ds 1103; row range 6-7"
    raw = _raw()
    assert audit.trace(_row("LK1103", "population_total", loc), raw, {}, CODES).expected == 150
    assert audit.trace(_row("LK1103", "occupied_housing_units", loc), raw, {}, CODES).expected == 35
    ratio = audit.trace(_row("LK1103", "sex_ratio", loc), raw, {}, CODES).expected
    assert ratio == pytest.approx(100 * 60 / 90)
    dens = audit.trace(_row("LK1103", "population_density", loc), raw, {"LK1103": 3.0}, CODES)
    assert dens.expected == pytest.approx(50.0)


def test_compare_catches_tampering():
    assert audit.compare("population_total", 150.0, 150.0)
    assert not audit.compare("population_total", 151.0, 150.0)
    assert audit.compare("sex_ratio", 66.6667, 100 * 60 / 90)
    assert not audit.compare("sex_ratio", 66.6668, 100 * 60 / 90)
    assert audit.compare("sex_ratio", None, None)
    assert not audit.compare("sex_ratio", 0.0, None)


def test_pdf_table_parsing():
    text = "Sri Lanka 21,781,800 100.0\nWestern Province 6,117,341 28.1\n"
    text += "Colombo 562,550 78,052 654,051 113,837\nNote: rounded 1 place"
    assert audit.parse_pdf_table(text) == {
        "Sri Lanka": 21_781_800,
        "Western Province": 6_117_341,
        "Colombo": 654_051,
    }


def test_sample_is_reproducible_and_includes_forced_values():
    rows = []
    for geo in ["LK", "LK1", "LK11", "LK1103", "LK2206300", "LK2206125", "LK1103005"]:
        for ind in ["population_total", "occupied_housing_units", "sex_ratio"]:
            rows.append(
                {
                    "claim_id": f"{geo}:{ind}",
                    "geography_id": geo,
                    "indicator_id": ind,
                    "value_status": "normal",
                }
            )
    obs = pd.DataFrame(rows)
    a, b = audit.draw_sample(obs, 1), audit.draw_sample(obs, 1)
    assert a["claim_id"].tolist() == b["claim_id"].tolist()
    assert "LK2206300:population_total" in set(a["claim_id"])
    assert a["claim_id"].is_unique
