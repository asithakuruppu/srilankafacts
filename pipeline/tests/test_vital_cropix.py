# ruff: noqa: E501
"""DCS vital statistics parsers and CROPIX code translation on small inline samples (no raw data)."""

from __future__ import annotations

from slf import cropix
from slf import stat_tables as st

COUNTS = [
    ("Table 2 : Number of Births, Deaths and Marriages registered by District, 2019-2025",),
    ("Districts", 2021, None, None, "2022*", None, None),
    (None, "Births*", "Deaths", "Marriages*", "Births", "Deaths", "Marriages"),
    (" Sri lanka", 30, 20, 10, 31, 21, 11),
    ("Colombo", 30, 20, 10, 31, 21, 11),
    ("*  Provisional", None, None, None, None, None, None),
]

RATES = [
    ("Table 1 : Crude Birth Rates & Crude Death Rates",),
    (None, None, None, None, None, None, None, "per 1,000 persons"),
    ("Province/ District", "2024*", None, None, None, None, None),
    (None, "Crude Birth Rate", None, None, "Crude Death Rate", None, None),
    (None, "Total", "Male", "Female", "Total", "Male", "Female"),
    ("Sri Lanka", 10.1, 10.6, 9.6, 7.8, 8.8, 6.8),
    (" North-West", 10, 10.6, 9.4, 8.2, 9.7, 6.8),
    ("Note: Province & District level figures are based on the usual residence ",),
]

MIDYEAR = """Total Male Female Total Male Female
Sri Lanka 21,756 10,500 11,256 21,778 10,511 11,267
Nuwara-eliya 726 347 379 727 347 380
* Provisional
2025*
"""


def test_counts_years_measures_and_provisional_marks() -> None:
    rows = st.parse_vital_counts(COUNTS)
    assert len(rows) == 12
    by = {(label, year, measure): (prov, value) for label, _, year, measure, prov, value in rows}
    assert by[("Sri lanka", 2021, "Births")] == (True, 30.0)  # '*' on the measure
    assert by[("Sri lanka", 2021, "Deaths")] == (False, 20.0)
    assert by[("Colombo", 2022, "Marriages")] == (True, 11.0)  # '*' on the year


def test_rates_carry_year_measure_and_sex() -> None:
    rows = st.parse_vital_rates(RATES)
    assert len(rows) == 12
    first = rows[0]
    assert first[0] == "Sri Lanka" and first[2] == 2024 and first[3] == "Crude Birth Rate"
    assert first[4] == "Total" and first[5] is True and first[6] == 10.1
    assert {r[0] for r in rows} == {"Sri Lanka", "North-West"}
    assert ("North-West", 2024, "Crude Death Rate", "Female") in {
        (r[0], r[2], r[3], r[4]) for r in rows
    }


def test_midyear_rows_need_three_numbers_per_year() -> None:
    rows = st.parse_midyear_page(MIDYEAR, 2)
    assert [(label, nums[0], nums[3]) for label, _, nums in rows] == [
        ("Sri Lanka", 21756.0, 21778.0),
        ("Nuwara-eliya", 726.0, 727.0),
    ]
    assert st.parse_midyear_page(MIDYEAR, 3) == []


def test_cropix_code_translation() -> None:
    assert cropix.dcs_code("1-1-03-115") == "1103115"
    assert cropix.dcs_code("5-2-24-010") == "5224010"
    assert cropix.dcs_code("3-3-03-080-P") is None
    assert cropix.dcs_code("1-1-3-115") is None


def test_cropix_name_agreement() -> None:
    assert cropix.name_agreement("Rathmalana West", "Ratmalana West") == "close"
    assert cropix.name_agreement("Kal /Pallewela", "Kal/Pallewela") == "same"
    assert cropix.name_agreement("Slave Island", "Kompagngnaweediya") == "different"
