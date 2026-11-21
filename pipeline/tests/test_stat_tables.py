# ruff: noqa: E501
"""Statistical tables: parsers and checks on small inline samples (no network, no raw data)."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from slf import stat_tables as st

HIES = """Poverty indicators-2019 4
Table 04: Poverty headcount index, number of poor population and contribution to total poverty by sector
Sri Lanka 3.2 689,800 100.0 14.3 3,042,300 100.0
Sector
Urban 1.1 41,800 6.1 6.0 217,500 7.1
Province
Western 1.1 65,900 9.6 5.7 342,200 11.2
District
Colombo 0.3 8,100 1.2 2.3 54,800 1.8
Vavunia 5.5 10,100 1.5 13.9 25,300 0.8
"""

LFS = """Table 12 - Labour force status (Current) of the household population
Total 100 60 60.0 57 95.0 3 5.0 40
Colombo 50 30 60.0 28 93.3 2 6.7 20
7,125 3.3 Kegalle 327,145 214,302 65.5 207,177 96.7 These figures are to be treated with caution
112,843
"""


def test_hies_sections_and_values() -> None:
    rows = st.parse_hies_table04(HIES)
    assert [(s, label) for s, label, _, _ in rows] == [
        ("country", "Sri Lanka"),
        ("sector", "Urban"),
        ("province", "Western"),
        ("district", "Colombo"),
        ("district", "Vavunia"),
    ]
    assert rows[0][3] == [3.2, 689800.0, 100.0, 14.3, 3042300.0, 100.0]


def test_hies_requires_title() -> None:
    with pytest.raises(ValueError):
        st.parse_hies_table04("Sri Lanka 3.2 689,800 100.0 14.3 3,042,300 100.0")


def test_lfs_rows_and_scrambled_row_repair() -> None:
    st.res_repairs.clear()
    rows = st.parse_lfs_table(LFS, "Table 12 - Labour force status")
    by = {label: nums for label, _, nums in rows}
    assert by["Colombo"][0] == 50
    kegalle = by["Kegalle"]
    # printed order: population, labour force, rate, employed, rate, unemployed, rate, not in LF
    assert kegalle == [327145, 214302, 65.5, 207177, 96.7, 7125, 3.3, 112843]
    assert kegalle[3] + kegalle[5] == kegalle[1] and kegalle[1] + kegalle[7] == kegalle[0]
    assert st.res_repairs == ["Kegalle"]


def test_lfs_requires_title() -> None:
    with pytest.raises(ValueError):
        st.parse_lfs_table("Colombo 50 30 60.0 28 93.3 2 6.7 20", "Table 12 - Labour force status")


def _match_file(root: Path, lines: list[str]) -> None:
    d = root / "geographies" / "name-matches"
    d.mkdir(parents=True)
    with (d / "dcs-statistical-tables-districts.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["source_label", "geography_id", "match_method", "datasets", "evidence"])
        for line in lines:
            w.writerow(line.split("|"))


def test_matches_are_per_dataset_and_never_by_name_alone(tmp_path: Path) -> None:
    _match_file(
        tmp_path,
        [
            "Vavunia|LK43|spelling_variant|hies-poverty;labour-force-survey|x",
            "VAVUNIYA|LK43|exact_name|paddy-statistics|x",
        ],
    )
    assert st.load_matches(tmp_path, "hies-poverty").keys() == {"Vavunia"}
    assert st.load_matches(tmp_path, "paddy-statistics").keys() == {"VAVUNIYA"}
    assert st.load_matches(tmp_path, "school-census") == {}


def test_duplicate_match_label_is_an_error(tmp_path: Path) -> None:
    _match_file(tmp_path, ["A|LK1|exact_name|hies-poverty|x", "A|LK2|exact_name|hies-poverty|x"])
    with pytest.raises(ValueError):
        st.load_matches(tmp_path, "hies-poverty")


def test_paddy_footnote_mark_is_stripped() -> None:
    assert st._paddy_label("JAFFNA *") == "JAFFNA"


def test_real_match_file_targets_exist_in_catalogue_names() -> None:
    path = (
        Path(__file__).parents[2]
        / "catalog"
        / "geographies"
        / "name-matches"
        / "dcs-statistical-tables-districts.csv"
    )
    rows = list(csv.DictReader(path.open(newline="")))
    ids = {r["geography_id"] for r in rows}
    assert len(ids - {"LK"}) == 34  # 9 provinces + 25 districts
    labels = [(r["source_label"], d) for r in rows for d in r["datasets"].split(";")]
    assert len(labels) == len(set(labels)), "a label is listed twice for one dataset"


DENGUE = """Table 1: Reported dengue cases in week 27 and week
26 of 2026
Colombo 329 230 1178* 1676 7713 14995
Vavuniya Nil Ni 4 10 28 94
Kalmunai* 7 21 43 71 314 783
Total* 1209 1059 5998* 7916 30060 61057
"""


def test_dengue_parser_handles_nil_footnote_marks_and_misprint() -> None:
    week, rows = st.parse_dengue_table1(DENGUE)
    assert week == 27
    assert rows["Colombo"] == [329, 230, 1178, 1676, 7713, 14995]
    assert rows["Vavuniya"] == [0, None, 4, 10, 28, 94]  # "Ni" is unreadable, not guessed
    assert set(rows) == {"Colombo", "Vavuniya", "Kalmunai", "Total"}


def test_dengue_parser_requires_title() -> None:
    with pytest.raises(ValueError):
        st.parse_dengue_table1("Colombo 1 2 3 4 5 6")


def test_registry_has_the_stat_datasets() -> None:
    from slf.datasets import REGISTRY

    assert {
        "hies-poverty",
        "labour-force-survey",
        "paddy-statistics",
        "dengue-weekly-district",
    } <= set(REGISTRY)
