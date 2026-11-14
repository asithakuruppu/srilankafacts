"""Census 2024 topic tables, step (d): population by ethnic group and by religion (D-032, D-033).

Source: DCS Census of Population and Housing 2024, Population A-series tables. A6 (ethnic group)
and A7 (religion) give, for Sri Lanka, each district and each DS division, the population by
category. A2 and A3 give the same at district level only and are used as a check.

D-033: these two topics are published for DS divisions, districts, provinces and the country only,
from DCS's own DS and district tables, never from sums of GN values (the GN files fold groups of
fewer than 10 people into "Other"). They carry ``sensitivity: sensitive_group`` and
``distribution: places_only``: place files and downloads, but no per-level indicator files, no
indicator pages, rankings, maps or neighbour comparisons.

The A-series tables carry no DS codes. DS lines join to DCS DS codes through a reviewed match
file, never by name at build time, and every match must pass a numeric check: the DS total equals
the sum of GN population for that DCS DS code in the GN population workbook.

This module parses and checks. ``census_2024_topics`` turns the parsed tables into observations.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from slf.datasets.census_2024_gnd import _int_cell
from slf.datasets.census_2024_materials import MatLine, district_key, english

BASE_URL = "https://www.statistics.gov.lk/Population/StaticalInformation/CPH2024"
MATCH_FILE = ("geographies", "name-matches", "dcs-census2024-population-a-series-ds.csv")


@dataclass(frozen=True)
class Layout:
    """Where things are in one kind of A-series sheet (0-based columns, 1-based lines)."""

    title_line: int
    title_column: int
    label_line: int
    label_column: int

    @property
    def total_column(self) -> int:
        return self.label_column + 1

    @property
    def first_category_column(self) -> int:
        return self.label_column + 2


DS_LAYOUT = Layout(title_line=4, title_column=1, label_line=7, label_column=1)  # A6, A7
DISTRICT_LAYOUT = Layout(title_line=3, title_column=0, label_line=6, label_column=0)  # A2, A3


@dataclass(frozen=True)
class IdCategory:
    slug: str
    name: str
    source_label: str  # English heading as printed (typos kept)


@dataclass(frozen=True)
class IdTopic:
    key: str  # ethnicity | religion
    ds_table: str  # A6 | A7
    district_table: str  # A2 | A3
    ds_title: str  # English title of the DS table, after "<table> : "
    district_title: str
    categories: tuple[IdCategory, ...]

    @property
    def ds_file(self) -> str:
        return f"PopulationA_{self.ds_table}.xlsx"

    @property
    def district_file(self) -> str:
        return f"PopulationA_{self.district_table}.xlsx"

    @property
    def ds_url(self) -> str:
        return f"{BASE_URL}/PopulationA/{self.ds_table}"

    @property
    def district_url(self) -> str:
        return f"{BASE_URL}/PopulationA/{self.district_table}"

    def count_id(self, category: IdCategory) -> str:
        return f"population_{self.key}_{category.slug}"

    def share_id(self, category: IdCategory) -> str:
        return f"{self.count_id(category)}_share"

    @property
    def count_ids(self) -> tuple[str, ...]:
        return tuple(self.count_id(c) for c in self.categories)

    @property
    def share_ids(self) -> tuple[str, ...]:
        return tuple(self.share_id(c) for c in self.categories)


_C = IdCategory
ID_TOPICS: tuple[IdTopic, ...] = (
    IdTopic(
        key="ethnicity",
        ds_table="A6",
        district_table="A2",
        ds_title=(
            "Population by ethnicity and district according to Divisional Secretary's "
            "Division, 2024"
        ),
        district_title="Population by ethnic group according to districts, 2024",
        categories=(
            _C("sinhalese", "Sinhalese", "Sinhalees"),
            _C("sri_lanka_tamil", "Sri Lanka Tamil", "Sri lanka Tamil"),
            _C(
                "indian_tamil",
                "Indian Tamil / Malaiyaga Thamilar",
                "Indian Tamil/ Malaiyaga Thamilar",
            ),
            _C("sri_lanka_moor", "Sri Lanka Moor / Muslim", "Sri Lanka Moor/Muslim"),
            _C("burgher", "Burgher", "Burgher"),
            _C("malay", "Malay", "Malay"),
            _C("sri_lanka_chetty", "Sri Lanka Chetty", "Sri Lanka Chetty"),
            _C("bharatha", "Bharatha", "Bharatha"),
            _C("veddha", "Veddha", "Veddhas"),
            _C("other", "Other", "Other"),
        ),
    ),
    IdTopic(
        key="religion",
        ds_table="A7",
        district_table="A3",
        ds_title=(
            "Population by religion and district according to Divisional Secretary's Division, 2024"
        ),
        district_title="Population by religion according to districts, 2024",
        categories=(
            _C("buddhist", "Buddhist", "Buddhist"),
            _C("hindu", "Hindu", "Hindu"),
            _C("islam", "Islam", "Islam"),
            _C("roman_catholic", "Roman Catholic", "Roman Catholic"),
            _C("other_christian", "Other Christian", "Other Christian"),
            _C("other", "Other", "Other"),
        ),
    ),
)
ID_COUNT_INDICATORS: tuple[str, ...] = tuple(i for t in ID_TOPICS for i in t.count_ids)
ID_SHARE_INDICATORS: tuple[str, ...] = tuple(i for t in ID_TOPICS for i in t.share_ids)
ID_INDICATORS: tuple[str, ...] = ID_COUNT_INDICATORS + ID_SHARE_INDICATORS


def _text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def check_header(
    topic: IdTopic, rows: list[tuple[object, ...]], table: str, title: str, layout: Layout
) -> None:
    """Fail unless the title and every category heading are where this module expects them."""
    got = _text(rows[layout.title_line - 1][layout.title_column])
    if got != f"{table} : {title}":
        raise ValueError(f"{table}: unexpected title {got!r}")
    labels = rows[layout.label_line - 1]
    for j, category in enumerate(topic.categories):
        column = layout.first_category_column + j
        heading = english(labels[column]) if column < len(labels) else ""
        if heading != category.source_label:
            raise ValueError(
                f"{table} column {column + 1}: heading {heading!r}, "
                f"expected {category.source_label!r}"
            )
    extra = labels[layout.first_category_column + len(topic.categories) :]
    if any(c is not None and str(c).strip() for c in extra):
        raise ValueError(f"{table}: unexpected heading after the last category: {extra!r}")


def _counts(
    topic: IdTopic, row: tuple[object, ...], line: int, table: str, layout: Layout
) -> tuple[int, ...]:
    first = layout.first_category_column
    width = len(topic.categories)
    cells = row[first : first + width]
    counts = tuple(
        _int_cell(v, line=line, field=f"{table} column {first + j + 1}")
        for j, v in enumerate(cells)
    )
    if len(counts) != width:
        raise ValueError(f"{table} row {line}: {len(counts)} categories, expected {width}")
    rest = row[first + width :]
    if any(c is not None and str(c).strip() for c in rest):
        raise ValueError(f"{table} row {line}: values after the last category: {rest!r}")
    return counts


def parse_ds_table(topic: IdTopic, rows: list[tuple[object, ...]]) -> list[MatLine]:
    """Every count line of A6 or A7, each checked to sum to its total.

    Lines are, in order: Sri Lanka, then for each district a "<name> District" line followed by
    its DS lines. Blank lines are skipped; a line with values but no label is an error.
    """
    table, layout = topic.ds_table, DS_LAYOUT
    check_header(topic, rows, table, topic.ds_title, layout)
    out: list[MatLine] = []
    district = ""
    for line, r in enumerate(rows[layout.label_line :], start=layout.label_line + 1):
        cell = r[layout.label_column] if len(r) > layout.label_column else None
        if cell is None or not str(cell).strip():
            if any(c is not None and str(c).strip() for c in r):
                raise ValueError(f"{table} row {line}: values without a label: {r!r}")
            continue
        if any(c is not None and str(c).strip() for c in r[: layout.label_column]):
            raise ValueError(f"{table} row {line}: unexpected cell before the label")
        label = english(cell)
        if label.endswith("Sri Lanka"):
            kind, label = "country", "Sri Lanka"
        elif label.endswith(" District"):
            kind, district = "district", district_key(label.removesuffix(" District"))
        else:
            kind = "ds"
            if not district:
                raise ValueError(f"{table} row {line}: DS line before any district line")
        total = _int_cell(r[layout.total_column], line=line, field=f"{table} total")
        counts = _counts(topic, r, line, table, layout)
        if sum(counts) != total:
            raise ValueError(
                f"{table} row {line} ({label}): categories sum to {sum(counts)}, total {total}"
            )
        out.append(MatLine(line, kind, label, district if kind != "country" else "", total, counts))
    if [m.kind for m in out].count("country") != 1:
        raise ValueError(f"{table}: expected exactly one Sri Lanka line")
    return out


def parse_district_table(topic: IdTopic, rows: list[tuple[object, ...]]) -> dict[str, MatLine]:
    """District (and 'sri lanka') -> count line from A2 or A3.

    Count lines carry a label in column A; the percentage line under each has none.
    """
    table, layout = topic.district_table, DISTRICT_LAYOUT
    check_header(topic, rows, table, topic.district_title, layout)
    out: dict[str, MatLine] = {}
    for line, r in enumerate(rows[layout.label_line :], start=layout.label_line + 1):
        if not r or r[0] is None:
            continue
        label = _text(r[0])
        key = district_key(label)
        total = _int_cell(r[layout.total_column], line=line, field=f"{table} total")
        counts = _counts(topic, r, line, table, layout)
        if sum(counts) != total:
            raise ValueError(f"{table} row {line}: categories sum to {sum(counts)}, total {total}")
        kind = "country" if key.endswith("sri lanka") else "district"
        key = "sri lanka" if kind == "country" else key
        if key in out:
            raise ValueError(f"{table}: {key} appears twice")
        out[key] = MatLine(line, kind, label, "" if kind == "country" else key, total, counts)
    return out


def check_tables(
    tables: Mapping[str, list[MatLine]],
    district_tables: Mapping[str, dict[str, MatLine]],
) -> list[str]:
    """Checks across the four tables. Returns error messages; empty means all passed.

    1. A6 and A7 list the same lines with the same labels and totals.
    2. In each DS table, DS lines sum to their district line and district lines to Sri Lanka.
    3. Each district table (A2, A3) equals the district and Sri Lanka lines of its DS table.
    """
    errors: list[str] = []
    topics = {t.key: t for t in ID_TOPICS}
    first_key = next(iter(tables))
    first = [(m.kind, m.label, m.total) for m in tables[first_key]]
    for key, lines in tables.items():
        topic = topics[key]
        table = topic.ds_table
        if [(m.kind, m.label, m.total) for m in lines] != first:
            errors.append(f"{table}: lines or totals differ from {topics[first_key].ds_table}")
        width = len(topic.categories)
        ds_sum: dict[str, list[int]] = {}
        district_sum = [0] * (width + 1)
        country: MatLine | None = None
        for m in lines:
            values = [m.total, *m.counts]
            if m.kind == "ds":
                acc = ds_sum.setdefault(m.district, [0] * (width + 1))
                ds_sum[m.district] = [a + v for a, v in zip(acc, values, strict=True)]
            elif m.kind == "district":
                district_sum = [a + v for a, v in zip(district_sum, values, strict=True)]
            else:
                country = m
        for m in lines:
            if m.kind == "district" and ds_sum.get(m.district) != [m.total, *m.counts]:
                errors.append(f"{table} row {m.line}: DS lines do not sum to {m.label}")
        if country is None or district_sum != [country.total, *country.counts]:
            errors.append(f"{table}: district lines do not sum to the Sri Lanka line")

        published = district_tables.get(key, {})
        ours = {
            ("sri lanka" if m.kind == "country" else m.district): m for m in lines if m.kind != "ds"
        }
        dtable = topic.district_table
        if set(published) != set(ours):
            errors.append(
                f"{dtable}: districts differ from {table}; only in {dtable}: "
                f"{sorted(set(published) - set(ours))}, only in {table}: "
                f"{sorted(set(ours) - set(published))}"
            )
        for k, m in sorted(ours.items()):
            p = published.get(k)
            if p is not None and (p.total, p.counts) != (m.total, m.counts):
                errors.append(f"{dtable} row {p.line} ({k}) differs from {table} row {m.line}")
    return errors
