from pathlib import Path

import pytest

from slf.catalog import CatalogReport, load_catalog
from slf.datasets import census_2024_ethnicity_religion as er
from slf.datasets import census_2024_materials as mat
from slf.datasets import census_2024_topics as topics

RELIGION = next(t for t in er.ID_TOPICS if t.key == "religion")
CATALOG = Path(__file__).resolve().parents[2] / "catalog"


def _sheet(layout: er.Layout, title: str, data: list[list[object]]) -> list[tuple[object, ...]]:
    """An A-series-shaped sheet with the title and headings where ``layout`` says."""
    width = layout.first_category_column + len(RELIGION.categories) + 1
    rows: list[list[object]] = [[None] * width for _ in range(layout.label_line)]
    rows[layout.title_line - 1][layout.title_column] = title
    for j, c in enumerate(RELIGION.categories):
        rows[layout.label_line - 1][layout.first_category_column + j] = (
            f"සිංහල\nதமிழ்\n{c.source_label}"
        )
    for d in data:
        row: list[object] = [None] * width
        row[layout.label_column : layout.label_column + len(d)] = d
        rows.append(row)
    return [tuple(r) for r in rows]


def _line(label: str | None, counts: list[int], total: int | None = None) -> list[object]:
    # DCS writes numbers as text in these files
    return [label, str(sum(counts) if total is None else total), *(str(c) for c in counts)]


def _counts(first: int, second: int = 0) -> list[int]:
    return [first, second] + [0] * (len(RELIGION.categories) - 2)


def _ds_rows() -> list[tuple[object, ...]]:
    return _sheet(
        er.DS_LAYOUT,
        f"A7 : {RELIGION.ds_title}",
        [
            _line("ශ්‍රී ලංකාව இலங்கை Sri Lanka", _counts(30, 3)),
            _line("කොළඹ දිස්ත්‍රික්කය \nகொழும்பு  மாவட்டம்\nColombo District", _counts(30, 3)),
            _line("A\nB\nColombo", _counts(10, 1)),
            _line("A\nB\nKolonnawa", _counts(20, 2)),
        ],
    )


def _district_rows(colombo: list[int]) -> list[tuple[object, ...]]:
    return _sheet(
        er.DISTRICT_LAYOUT,
        f"A3 : {RELIGION.district_title}",
        [
            _line("ශ්‍රී ලංකා இலங்கை Sri Lanka", _counts(30, 3)),
            [None, "100", "90.9", "9.1"],  # percentage line, no label
            _line("කොළඹ கொழும்பு Colombo", colombo),
        ],
    )


def test_parse_ds_table_reads_lines_from_column_b():
    lines = er.parse_ds_table(RELIGION, _ds_rows())
    assert [(m.kind, m.label, m.district, m.total) for m in lines] == [
        ("country", "Sri Lanka", "", 33),
        ("district", "Colombo District", "colombo", 33),
        ("ds", "Colombo", "colombo", 11),
        ("ds", "Kolonnawa", "colombo", 22),
    ]


def test_parse_ds_table_fails_when_categories_do_not_sum():
    rows = list(_ds_rows())
    row = list(rows[-1])
    row[er.DS_LAYOUT.total_column] = "23"
    rows[-1] = tuple(row)
    with pytest.raises(ValueError, match="categories sum to 22, total 23"):
        er.parse_ds_table(RELIGION, rows)


def test_parse_ds_table_rejects_values_without_a_label():
    rows = [*_ds_rows(), tuple([None, None, "5", "5"] + [None] * 4)]
    with pytest.raises(ValueError, match="values without a label"):
        er.parse_ds_table(RELIGION, rows)


def test_header_check_rejects_a_moved_column_and_a_wrong_title():
    rows = list(_ds_rows())
    labels = list(rows[er.DS_LAYOUT.label_line - 1])
    labels[3], labels[4] = labels[4], labels[3]
    rows[er.DS_LAYOUT.label_line - 1] = tuple(labels)
    with pytest.raises(ValueError, match="column 4"):
        er.parse_ds_table(RELIGION, rows)
    rows = list(_ds_rows())
    title = list(rows[er.DS_LAYOUT.title_line - 1])
    title[1] = "A6 : something else"
    rows[er.DS_LAYOUT.title_line - 1] = tuple(title)
    with pytest.raises(ValueError, match="unexpected title"):
        er.parse_ds_table(RELIGION, rows)


def test_check_tables_compares_ds_sums_and_district_table():
    lines = er.parse_ds_table(RELIGION, _ds_rows())
    good = er.parse_district_table(RELIGION, _district_rows(_counts(30, 3)))
    assert er.check_tables({"religion": lines}, {"religion": good}) == []
    bad = er.parse_district_table(RELIGION, _district_rows(_counts(29, 4)))
    errors = er.check_tables({"religion": lines}, {"religion": bad})
    assert errors == ["A3 row 9 (colombo) differs from A7 row 9"]


def test_match_uses_population_totals():
    lines = er.parse_ds_table(RELIGION, _ds_rows())
    matches = {("11", "Colombo"): "1103", ("11", "Kolonnawa"): "1106"}
    codes, errors = mat.match_ds_lines(
        lines, matches, {"colombo": 11}, {"1103": 11, "1106": 22}, what="population"
    )
    assert errors == [] and codes[("colombo", "Kolonnawa")] == "1106"
    swapped = {("11", "Colombo"): "1106", ("11", "Kolonnawa"): "1103"}
    _, errors = mat.match_ds_lines(
        lines, swapped, {"colombo": 11}, {"1103": 11, "1106": 22}, what="population"
    )
    assert len(errors) == 2 and all("GN sum of population" in e for e in errors)


def test_rows_are_sensitive_and_ds_floor():
    row = topics._row(
        indicator="population_religion_hindu_share",
        geography_id="LK1103",
        value=5.0,
        source_locator="test",
        snapshot_sha256="abc",
        information_floor="ds-2024",
    )
    assert row["sensitivity"] == "sensitive_group"
    assert row["universe"] == "persons" and row["unit"] == "percent"
    assert row["information_footprint_ref"] == "ds-2024"
    other = topics._row(
        indicator="housing_roof_tile_share",
        geography_id="LK1103",
        value=5.0,
        source_locator="test",
        snapshot_sha256="abc",
        information_floor="ds-2024",
    )
    assert other["sensitivity"] == "public"


def test_catalog_marks_every_indicator_places_only_and_sensitive():
    catalog = load_catalog(CATALOG, None, CatalogReport())
    assert len(er.ID_COUNT_INDICATORS) == 16 and len(er.ID_SHARE_INDICATORS) == 16
    for indicator_id in er.ID_INDICATORS:
        indicator = catalog.indicators[indicator_id]
        assert indicator.distribution == "places_only", indicator_id
        assert indicator.sensitivity == "sensitive_group", indicator_id
    existing = set(topics.ALL_INDICATORS) | set(topics.POP_INDICATORS) | set(mat.MAT_INDICATORS)
    assert not set(er.ID_INDICATORS) & existing


def test_population_match_file_covers_340_ds_once():
    matches = mat.load_matches(str(CATALOG.joinpath(*er.MATCH_FILE)))
    assert len(matches) == 340
    assert all(code.startswith(district) for (district, _), code in matches.items())
