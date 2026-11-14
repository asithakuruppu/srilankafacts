from pathlib import Path

import pytest

from slf.datasets import census_2024_materials as mat
from slf.datasets import census_2024_topics as topics

ROOF = next(t for t in mat.MAT_TOPICS if t.key == "roof")
WIDTH = mat.FIRST_CATEGORY_COLUMN + len(ROOF.categories)


def _table(table: str, data: list[list[object]]) -> list[tuple[object, ...]]:
    """An A-series-shaped sheet: title on line 3, headings on line 6, data from line 7."""
    blank: list[object] = [None] * WIDTH
    title = [f"{table} : Number of housing units {ROOF.title_words} at district level, 2024"]
    labels: list[object] = [None, None]
    labels += [f"සිංහල\nதமிழ்\n{c.source_label}" for c in ROOF.categories]
    rows = [blank, blank, title + blank[1:], blank, blank, labels, *data]
    return [tuple(r) for r in rows]


def _line(label: str, counts: list[int], total: int | None = None) -> list[object]:
    return [label, sum(counts) if total is None else total, *counts]


def _counts(first: int, second: int = 0) -> list[int]:
    return [first, second] + [0] * (len(ROOF.categories) - 2)


def _ds_table() -> list[tuple[object, ...]]:
    return _table(
        "A11",
        [
            _line("ශ්‍රී ලංකාව\nஇலங்கை\nSri Lanka", _counts(30, 3)),
            _line("කොළඹ\nகொழும்பு\nColombo District ", _counts(30, 3)),
            _line("A\nB\nColombo", _counts(10, 1)),
            [None] * WIDTH,
            _line("A\nB\nKolonnawa", _counts(20, 2)),
        ],
    )


def test_parse_ds_table_reads_line_kinds_and_english_labels():
    lines = mat.parse_ds_table(ROOF, _ds_table())
    assert [(m.kind, m.label, m.district) for m in lines] == [
        ("country", "Sri Lanka", ""),
        ("district", "Colombo District", "colombo"),
        ("ds", "Colombo", "colombo"),
        ("ds", "Kolonnawa", "colombo"),
    ]
    assert lines[3].line == 11 and lines[3].total == 22


def test_parse_ds_table_fails_when_categories_do_not_sum():
    rows = _ds_table()
    rows[8] = tuple(_line("A\nB\nColombo", _counts(10, 1), total=12))
    with pytest.raises(ValueError, match="categories sum to 11, total 12"):
        mat.parse_ds_table(ROOF, rows)


def test_header_check_rejects_a_moved_column():
    rows = _ds_table()
    labels = list(rows[5])
    labels[2], labels[3] = labels[3], labels[2]
    rows[5] = tuple(labels)
    with pytest.raises(ValueError, match="column 3"):
        mat.parse_ds_table(ROOF, rows)


def test_check_tables_flags_ds_lines_that_do_not_sum_to_their_district():
    rows = _ds_table()
    rows[8] = tuple(_line("A\nB\nColombo", _counts(9, 2)))
    lines = mat.parse_ds_table(ROOF, rows)
    district = mat.parse_district_table(
        ROOF,
        _table(
            "A3",
            [
                _line("ශ්‍රී ලංකාව இலங்கை  Sri Lanka", _counts(30, 3)),
                _line("කොළඹ  கொழும்பு  Colombo", _counts(30, 3)),
            ],
        ),
    )
    errors = mat.check_tables({"roof": lines}, {"roof": district})
    assert any("DS lines do not sum to Colombo District" in e for e in errors)


def test_check_tables_flags_a_district_table_that_differs():
    lines = mat.parse_ds_table(ROOF, _ds_table())
    district = mat.parse_district_table(
        ROOF,
        _table(
            "A3",
            [
                _line("ශ්‍රී ලංකාව இலங்கை  Sri Lanka", _counts(30, 3)),
                _line("කොළඹ  கொழும்பு  Colombo", _counts(29, 4)),
            ],
        ),
    )
    errors = mat.check_tables({"roof": lines}, {"roof": district})
    assert errors == ["A3 row 8 (colombo) differs from A11 row 8"]


def test_match_requires_the_file_and_the_numeric_check():
    lines = mat.parse_ds_table(ROOF, _ds_table())
    matches = {("11", "Colombo"): "1103", ("11", "Kolonnawa"): "1106"}
    codes, errors = mat.match_ds_lines(lines, matches, {"colombo": 11}, {"1103": 11, "1106": 22})
    assert errors == []
    assert codes == {("colombo", "Colombo"): "1103", ("colombo", "Kolonnawa"): "1106"}

    # a swapped match fails the totals check
    swapped = {("11", "Colombo"): "1106", ("11", "Kolonnawa"): "1103"}
    _, errors = mat.match_ds_lines(lines, swapped, {"colombo": 11}, {"1103": 11, "1106": 22})
    assert len(errors) == 2 and all("GN sum of occupied housing units" in e for e in errors)

    # a DS line missing from the file is an error, never a guess by name
    _, errors = mat.match_ds_lines(
        lines, {("11", "Colombo"): "1103"}, {"colombo": 11}, {"1103": 11, "1106": 22}
    )
    assert any("'Kolonnawa' (district 11) not in the match file" in e for e in errors)
    assert any("no table line: ['1106']" in e for e in errors)


def test_indicators_are_new_and_paired():
    assert len(mat.MAT_COUNT_INDICATORS) == 37
    assert len(mat.MAT_SHARE_INDICATORS) == 37
    existing = set(topics.ALL_INDICATORS) | set(topics.POP_INDICATORS)
    assert not set(mat.MAT_INDICATORS) & existing
    assert "occupied_housing_units" not in mat.MAT_INDICATORS  # published by census-2024-gnd-tables


def test_materials_rows_use_housing_units_and_ds_floor():
    row = topics._row(
        indicator="housing_roof_tile",
        geography_id="LK1103",
        value=5.0,
        source_locator="test",
        snapshot_sha256="abc",
        information_floor="ds-2024",
    )
    assert row["universe"] == "housing_units_occupied"
    assert row["unit"] == "housing_units"
    assert row["information_footprint_ref"] == "ds-2024"
    assert "by DS (Housing A-series tables)" in str(row["preferred_reason"])


def test_match_file_covers_340_ds_once():
    path = Path(__file__).resolve().parents[2].joinpath("catalog", *mat.MATCH_FILE)
    matches = mat.load_matches(str(path))
    assert len(matches) == 340
    assert len(set(matches.values())) == 340
    assert all(code.startswith(district) for (district, _), code in matches.items())
