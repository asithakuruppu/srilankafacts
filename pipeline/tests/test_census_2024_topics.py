import pytest

from slf.datasets import census_2024_topics as mod


def _sheet(data_rows: list[list[object]]) -> list[tuple[object, ...]]:
    """A minimal HH_GND-shaped sheet: 6 header lines, then data from line 7."""
    width = mod.LAST_COLUMN + 1
    titles: list[object] = [None] * width
    titles[mod.HOUSEHOLDS_COLUMN] = "Number of Households"
    for group, title in mod.GROUP_TITLES.items():
        titles[min(c.column for c in mod.CATEGORIES if c.group == group)] = title
    labels: list[object] = [None] * width
    for c in mod.CATEGORIES:
        labels[c.column] = c.source_label
    blank = tuple([None] * width)
    return [blank, blank, blank, tuple(titles), blank, tuple(labels), *map(tuple, data_rows)]


def _gn_row(households: int, *, firewood: int | None = None) -> list[object]:
    row: list[object] = [1, "Western", 11, "Colombo", 3, "Colombo", 5, "A GN", " ", households]
    row += [0] * (mod.LAST_COLUMN + 1 - len(row))
    # put every household in the first category of each group
    for group in mod.GROUPS:
        first = min(c.column for c in mod.CATEGORIES if c.group == group)
        row[first] = households
    if firewood is not None:
        row[25] = firewood
    return row


def test_every_group_is_complete_and_columns_are_unique():
    columns = [c.column for c in mod.CATEGORIES]
    assert len(columns) == len(set(columns)) == 37
    assert columns == list(range(10, 47))
    assert len(set(mod.ALL_INDICATORS)) == 75
    assert "households_cooking_firewood" in mod.COUNT_INDICATORS


def test_parse_reads_codes_and_counts():
    frame = mod.parse_households(_sheet([_gn_row(120)]))
    record = frame.iloc[0]
    assert record["dcs_gn"] == "1103005"
    assert record["dcs_ds"] == "1103"
    assert record["households_total"] == 120
    assert record["households_water_protected_well"] == 120
    assert record["households_cooking_firewood"] == 120
    assert int(record["line"]) == 7


def test_parse_fails_when_a_group_does_not_sum_to_households():
    with pytest.raises(ValueError, match="cooking categories sum to 125"):
        mod.parse_households(_sheet([_gn_row(120, firewood=125)]))


def test_parse_fails_on_a_moved_column():
    sheet = _sheet([_gn_row(10)])
    labels = list(sheet[5])
    labels[25], labels[26] = labels[26], labels[25]
    sheet[5] = tuple(labels)
    with pytest.raises(ValueError, match="column 25"):
        mod.parse_households(sheet)


def test_share_is_null_when_there_are_no_households():
    assert mod._share(0.0, 0.0) is None
    assert mod._share(25.0, 200.0) == pytest.approx(12.5)


def test_row_records_provenance_and_verification_level():
    row = mod._row(
        indicator="households_cooking_firewood_share",
        geography_id="LK11",
        value=None,
        source_locator="test",
        snapshot_sha256="abc",
    )
    assert row["dataset_id"] == "census-2024-topic-tables"
    assert row["verification"] == "machine_extracted"
    assert row["unit"] == "percent"
    assert row["value_status"] == "not_available"
    assert row["universe"] == "households"


def test_district_table_parser_skips_percentage_rows_and_reads_names():
    rows: list[tuple[object, ...]] = [
        ("A6 : title", None),
        ("District", "Households"),
        ("ශ්‍රී ලංකාව இலங்கை Sri Lanka", 10, 6, 0, 4, 0, 0, 0, 0, 0),
        (None, 100, 60.0, 0, 40.0, 0, 0, 0, 0, 0),
        ("මොණරාගල  மொணராகலை  Monaragala ", 10, 6, 0, 4, 0, 0, 0, 0, 0),
    ]
    table = mod.parse_district_table(rows, "cooking")
    assert table == {
        "sri lanka": [10, 6, 0, 4, 0, 0, 0, 0, 0],
        "moneragala": [10, 6, 0, 4, 0, 0, 0, 0, 0],
    }


def test_compare_flags_a_category_mismatch_and_unmatched_rows():
    cooking = [c.count_id for c in mod.CATEGORIES if c.group == "cooking"]
    values = {("LK", "households_total"): 10.0, ("LK11", "households_total"): 10.0}
    values |= {("LK", i): 0.0 for i in cooking} | {("LK11", i): 0.0 for i in cooking}
    values[("LK", "households_cooking_firewood")] = 10.0
    values[("LK11", "households_cooking_firewood")] = 9.0
    values[("LK11", "households_cooking_gas")] = 1.0
    table = {
        "sri lanka": [10, 10, 0, 0, 0, 0, 0, 0, 0],
        "colombo": [10, 10, 0, 0, 0, 0, 0, 0, 0],
        "nowhere": [1, 1, 0, 0, 0, 0, 0, 0, 0],
    }
    errors = mod.compare_with_district_tables(values, {"cooking": table}, {11: "Colombo"})
    assert any("extra ['nowhere']" in e for e in errors)
    assert any("LK11 households_cooking_firewood: GN sum 9.0" in e for e in errors)
    assert any("LK11 households_cooking_gas: GN sum 1.0" in e for e in errors)
    assert not any(e.startswith("LK ") for e in errors)
