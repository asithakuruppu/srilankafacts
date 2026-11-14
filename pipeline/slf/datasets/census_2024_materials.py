"""Census 2024 topic tables, step (c): housing unit structure and materials by DS (D-032).

Source: DCS Census of Population and Housing 2024, Housing A-series tables. A9-A12 give, for Sri
Lanka, each district and each DS division, the number of (occupied) housing units by structure
and by main wall, roof and floor material. A1-A4 give the same at district level only and are
used as a check. No GN breakdown is published.

The A-series tables carry no DS codes, only trilingual names. DS rows join to DCS DS codes through
a reviewed match file (``catalog/geographies/name-matches/dcs-census2024-a-series-ds.csv``),
never by name at build time, and every match must pass a numeric check: the DS total equals the
sum of GN occupied housing units for that DCS DS code in the GN housing workbook.

This module parses and checks. ``census_2024_topics`` turns the parsed tables into observations.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

import pandas as pd

from slf.datasets.census_2024_gnd import _int_cell

BASE_URL = "https://www.statistics.gov.lk/Population/StaticalInformation/CPH2024"
MATCH_FILE = ("geographies", "name-matches", "dcs-census2024-a-series-ds.csv")
TOTAL_COLUMN = 1  # 0-based; "Number of housing units"
FIRST_CATEGORY_COLUMN = 2
LABEL_LINE = 6  # 1-based line holding the category headings
TITLE_LINE = 3  # 1-based line holding the English title


@dataclass(frozen=True)
class MatCategory:
    slug: str
    name: str
    source_label: str  # English heading as printed in the DS table (typos kept)


@dataclass(frozen=True)
class MatTopic:
    key: str  # structure | wall | roof | floor
    ds_table: str  # A9..A12
    district_table: str  # A1..A4
    title_words: str  # must appear in both tables' English titles
    categories: tuple[MatCategory, ...]

    @property
    def ds_file(self) -> str:
        return f"HousingA_{self.ds_table}.xlsx"

    @property
    def district_file(self) -> str:
        return f"HousingA_{self.district_table}.xlsx"

    @property
    def ds_url(self) -> str:
        return f"{BASE_URL}/HousingA/{self.ds_table}"

    @property
    def district_url(self) -> str:
        return f"{BASE_URL}/HousingA/{self.district_table}"

    def count_id(self, category: MatCategory) -> str:
        return f"housing_{self.key}_{category.slug}"

    def share_id(self, category: MatCategory) -> str:
        return f"{self.count_id(category)}_share"

    @property
    def count_ids(self) -> tuple[str, ...]:
        return tuple(self.count_id(c) for c in self.categories)

    @property
    def share_ids(self) -> tuple[str, ...]:
        return tuple(self.share_id(c) for c in self.categories)

    def column(self, category: MatCategory) -> int:
        return FIRST_CATEGORY_COLUMN + self.categories.index(category)


_C = MatCategory
MAT_TOPICS: tuple[MatTopic, ...] = (
    MatTopic(
        key="structure",
        ds_table="A9",
        district_table="A1",
        title_words="by housing unit structure",
        categories=(
            _C("single_1_floor", "Single house, 1 floor", "Single house - Single storeyed"),
            _C("single_2_floors", "Single house, 2 floors", "Single house - two storeyed"),
            _C(
                "single_3_plus_floors",
                "Single house, more than 2 floors",
                "Single house - more than two storeyed",
            ),
            _C("attached_1_floor", "Attached house, 1 floor", "Attached House - 1st Floor"),
            _C("attached_2_floors", "Attached house, 2 floors", "Attached House - 2nd Floor"),
            _C(
                "attached_3_4_floors",
                "Attached house, 3 or 4 floors",
                "Attached House - 3rd or 4th Floors",
            ),
            _C(
                "attached_5_10_floors",
                "Attached house, 5 to 10 floors",
                "Attached House - 5th to 10th Floors",
            ),
            _C(
                "attached_11_19_floors",
                "Attached house, 11 to 19 floors",
                "Attached House - 11th to 19th Floors",
            ),
            _C(
                "attached_20_plus_floors",
                "Attached house, 20 or more floors",
                "Attached House - From 20th Floors or more",
            ),
            _C("other", "Other", "Other"),
        ),
    ),
    MatTopic(
        key="wall",
        ds_table="A10",
        district_table="A2",
        title_words="by main material used for walls construction",
        categories=(
            _C("brick", "Brick", "Brick"),
            _C("cement_block", "Cement block", "Cement block"),
            _C("granite_cube_stone", "Granite or cube stones", "Granite/Cube stones"),
            _C("cabook", "Cabook", "Cabook"),
            _C("pressed_soil_brick", "Pressed soil bricks", "Pressed soil bricks"),
            _C("mud", "Mud or warichchi", "Mud/Warichchi"),
            _C("cadjan_palmyrah", "Cadjan or palmyrah", "Kadjan/ Palmyrah"),
            _C(
                "plank_metal_sheet_asbestos",
                "Plank, metal sheet or asbestos",
                "Plank/ Metal Sheet/Asbestos",
            ),
            _C("zinc_aluminium_sheet", "Zinc aluminium sheets", "Zink Aluminium Sheets"),
            _C("other", "Other", "Other"),
            _C("not_relevant", "Not relevant", "Not Relavent"),
        ),
    ),
    MatTopic(
        key="roof",
        ds_table="A11",
        district_table="A3",
        title_words="by main material used for roof construction",
        categories=(
            _C("tile", "Tile", "Tile"),
            _C("asbestos", "Asbestos", "Asbestos"),
            _C("concrete", "Concrete", "Concrete"),
            _C("zinc_aluminium_sheet", "Zinc aluminium sheet", "Zink Aluminium Sheet"),
            _C("metal_sheet", "Metal sheet", "Metal Sheet"),
            _C("cadjan_palmyrah_straw", "Cadjan, palmyrah or straw", "cadjan/ Palmyrah/Straw"),
            _C("other", "Other", "Other"),
            _C("not_relevant", "Not relevant", "Not Relavent"),
        ),
    ),
    MatTopic(
        key="floor",
        ds_table="A12",
        district_table="A4",
        title_words="by main material used for floor construction",
        categories=(
            _C("cement", "Cement", "Cement"),
            _C(
                "terrazzo_tile_granite_finished_wood",
                "Terrazzo, tile, granite, finished wood or titanium",
                "Terrazzo/Tile/Granite/Wood(finished)/Titanium",
            ),
            _C("concrete", "Concrete", "Concrete"),
            _C("mud", "Mud", "Mud"),
            _C("wood", "Wood", "Wood"),
            _C("sand", "Sand", "Sand"),
            _C("other", "Other", "Other"),
            _C("not_relevant", "Not relevant", "Not Relavent"),
        ),
    ),
)
MAT_COUNT_INDICATORS: tuple[str, ...] = tuple(i for t in MAT_TOPICS for i in t.count_ids)
MAT_SHARE_INDICATORS: tuple[str, ...] = tuple(i for t in MAT_TOPICS for i in t.share_ids)
MAT_INDICATORS: tuple[str, ...] = MAT_COUNT_INDICATORS + MAT_SHARE_INDICATORS


@dataclass(frozen=True)
class MatLine:
    """One count line of an A-series table. ``kind`` is country, district or ds."""

    line: int  # 1-based
    kind: str
    label: str  # English part of the label
    district: str  # normalised district name for district and DS lines; "" for the country
    total: int
    counts: tuple[int, ...]


def english(value: object) -> str:
    """The English part of a trilingual cell: its last non-empty line, spaces normalised."""
    parts = [p for p in str(value).split("\n") if p.strip()]
    return re.sub(r"\s+", " ", parts[-1]).strip() if parts else ""


def district_key(text: str) -> str:
    """A district name, normalised (DCS spells some differently in different tables)."""
    words = re.findall(r"[A-Za-z]+", text)
    name = " ".join(words).lower()
    aliases = {"rathnapura": "ratnapura", "nuwaraeliya": "nuwara eliya", "monaragala": "moneragala"}
    return aliases.get(name, name)


def check_header(topic: MatTopic, rows: list[tuple[object, ...]], table: str) -> None:
    """Fail unless the title and every category heading are where this module expects them."""
    title = re.sub(r"\s+", " ", str(rows[TITLE_LINE - 1][0] or "")).strip()
    if not title.startswith(f"{table} : Number of housing units") or (
        topic.title_words not in title
    ):
        raise ValueError(f"{table}: unexpected title {title!r}")
    labels = rows[LABEL_LINE - 1]
    for category in topic.categories:
        column = topic.column(category)
        got = english(labels[column]) if column < len(labels) else ""
        if got.lower() != category.source_label.lower():
            raise ValueError(
                f"{table} column {column + 1}: heading {got!r}, expected {category.source_label!r}"
            )
    extra = labels[FIRST_CATEGORY_COLUMN + len(topic.categories) :]
    if any(c is not None and str(c).strip() for c in extra):
        raise ValueError(f"{table}: unexpected heading after the last category: {extra!r}")


def _counts(topic: MatTopic, row: tuple[object, ...], line: int, table: str) -> tuple[int, ...]:
    width = len(topic.categories)
    cells = row[FIRST_CATEGORY_COLUMN : FIRST_CATEGORY_COLUMN + width]
    counts = tuple(
        _int_cell(v, line=line, field=f"{table} column {FIRST_CATEGORY_COLUMN + j + 1}")
        for j, v in enumerate(cells)
    )
    if len(counts) != width:
        raise ValueError(f"{table} row {line}: {len(counts)} categories, expected {width}")
    return counts


def parse_ds_table(topic: MatTopic, rows: list[tuple[object, ...]]) -> list[MatLine]:
    """Every count line of an A9-A12 table, each checked to sum to its total.

    Lines are, in order: Sri Lanka, then for each district a "<name> District" line followed by
    its DS lines. Blank lines are skipped.
    """
    table = topic.ds_table
    check_header(topic, rows, table)
    out: list[MatLine] = []
    district = ""
    for line, r in enumerate(rows[LABEL_LINE:], start=LABEL_LINE + 1):
        if not r or r[0] is None:
            if any(c is not None for c in r):
                raise ValueError(f"{table} row {line}: values without a label: {r!r}")
            continue
        label = english(r[0])
        if label == "Sri Lanka":
            kind = "country"
        elif label.endswith(" District"):
            kind, district = "district", district_key(label.removesuffix(" District"))
        else:
            kind = "ds"
            if not district:
                raise ValueError(f"{table} row {line}: DS line before any district line")
        total = _int_cell(r[TOTAL_COLUMN], line=line, field=f"{table} total")
        counts = _counts(topic, r, line, table)
        if sum(counts) != total:
            raise ValueError(
                f"{table} row {line} ({label}): categories sum to {sum(counts)}, total {total}"
            )
        out.append(MatLine(line, kind, label, district if kind != "country" else "", total, counts))
    if [m.kind for m in out].count("country") != 1:
        raise ValueError(f"{table}: expected exactly one Sri Lanka line")
    return out


def parse_district_table(topic: MatTopic, rows: list[tuple[object, ...]]) -> dict[str, MatLine]:
    """District (and 'sri lanka') -> count line from an A1-A4 table.

    Count lines carry a label in column A; the percentage line under each has none.
    """
    table = topic.district_table
    check_header(topic, rows, table)
    out: dict[str, MatLine] = {}
    for line, r in enumerate(rows[LABEL_LINE:], start=LABEL_LINE + 1):
        if not r or r[0] is None:
            continue
        label = english(r[0]) if "\n" in str(r[0]).strip() else re.sub(r"\s+", " ", str(r[0]))
        key = district_key(label)
        total = _int_cell(r[TOTAL_COLUMN], line=line, field=f"{table} total")
        counts = _counts(topic, r, line, table)
        if sum(counts) != total:
            raise ValueError(f"{table} row {line}: categories sum to {sum(counts)}, total {total}")
        if key in out:
            raise ValueError(f"{table}: {key} appears twice")
        kind = "country" if key.endswith("sri lanka") else "district"
        out["sri lanka" if kind == "country" else key] = MatLine(
            line, kind, label, "" if kind == "country" else key, total, counts
        )
    return out


def load_matches(path: str) -> dict[tuple[str, str], str]:
    """(district code, English DS label) -> DCS DS code, from the reviewed match file."""
    frame = pd.read_csv(path, dtype=str)
    out: dict[tuple[str, str], str] = {}
    for rec in frame.to_dict("records"):
        key = (str(rec["district_code"]), str(rec["label_en"]))
        if key in out:
            raise ValueError(f"match file: {key} listed twice")
        out[key] = str(rec["dcs_ds"])
    if len(set(out.values())) != len(out):
        raise ValueError("match file: a DCS DS code is listed twice")
    return out


def check_tables(
    tables: Mapping[str, list[MatLine]],
    district_tables: Mapping[str, dict[str, MatLine]],
) -> list[str]:
    """Checks across the eight tables. Returns error messages; empty means all passed.

    1. A9-A12 list the same lines with the same labels and totals.
    2. In each DS table, DS lines sum to their district line and district lines to Sri Lanka.
    3. Each district table (A1-A4) equals the district and Sri Lanka lines of its DS table.
    """
    errors: list[str] = []
    topics = {t.key: t for t in MAT_TOPICS}
    first_key = next(iter(tables))
    first = [(m.kind, m.label, m.total) for m in tables[first_key]]
    for key, lines in tables.items():
        table = topics[key].ds_table
        if [(m.kind, m.label, m.total) for m in lines] != first:
            errors.append(f"{table}: lines or totals differ from {topics[first_key].ds_table}")
        width = len(topics[key].categories)
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
        dtable = topics[key].district_table
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


def match_ds_lines(
    lines: list[MatLine],
    matches: Mapping[tuple[str, str], str],
    district_codes: Mapping[str, int],
    gn_housing_by_ds: Mapping[str, int],
    what: str = "occupied housing units",
) -> tuple[dict[tuple[str, str], str], list[str]]:
    """(district, DS label) -> DCS DS code for every DS line, with the numeric check.

    Keyed by district and label, not line number: A9-A12 list the same lines in the same order
    (``check_tables``) but have different blank rows.

    ``district_codes`` maps normalised district names to DCS district codes.
    ``gn_housing_by_ds`` is the sum of GN occupied housing units per DCS DS code (or of
    ``what``, when another table reuses this check).
    """
    errors: list[str] = []
    out: dict[tuple[str, str], str] = {}
    for m in lines:
        if m.kind != "ds":
            continue
        code = district_codes.get(m.district)
        if code is None:
            errors.append(f"row {m.line}: district {m.district!r} has no DCS code")
            continue
        ds = matches.get((f"{code:02d}", m.label))
        if ds is None:
            errors.append(f"row {m.line}: {m.label!r} (district {code:02d}) not in the match file")
            continue
        if not ds.startswith(f"{code:02d}"):
            errors.append(f"row {m.line}: {m.label!r} matched to {ds}, outside district {code:02d}")
        expected = gn_housing_by_ds.get(ds)
        if expected != m.total:
            errors.append(
                f"row {m.line}: {m.label!r} -> DCS DS {ds}: table total {m.total}, GN sum of "
                f"{what} {expected}"
            )
        if (m.district, m.label) in out:
            errors.append(f"row {m.line}: {m.label!r} appears twice in its district")
        out[(m.district, m.label)] = ds
    unused = set(matches.values()) - set(out.values())
    if unused:
        errors.append(f"match file rows not used: {sorted(unused)}")
    missing = set(gn_housing_by_ds) - set(out.values())
    if missing:
        errors.append(f"DCS DS codes with GN {what} but no table line: {sorted(missing)}")
    return out, errors
