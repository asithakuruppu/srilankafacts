"""DCS Final Report (CPH2024_Final_Eng.pdf) tables against the release.

Page text comes from ``scripts/pdf_pages.swift`` (PDFKit, macOS) in ``pages_dir``:

    swift scripts/pdf_pages.swift <CPH2024_Final_Eng.pdf> data/build/audit/pdf-pages \
        72 104 115 124 205 208 211 212

Tables: 3.6 sector by district (p. 72), 6.1.3 age (p. 104), 6.1.11 ethnic group by district
(p. 115), 6.1.15 religion by district (p. 124), 11.6 materials (p. 205), 11.9 drinking water
(p. 208), 11.12 firewood and gas by district (p. 211), 11.13 lighting (p. 212).
"""

from __future__ import annotations

import re
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from slf.crosschecks.common import Result, district_ids, values
from slf.datasets import census_2024_materials as mat

PAGES = (72, 104, 115, 124, 205, 208, 211, 212)
GND, TOPICS = "census-2024-gnd-tables", "census-2024-topic-tables"
NUM = r"[\d,]+"


def _page(pages_dir: Path, n: int, title: str) -> str:
    text = (pages_dir / f"page-{n:03d}.txt").read_text(encoding="utf-8")
    if title not in text:
        raise ValueError(f"PDF page {n}: {title!r} not found")
    return text[text.index(title) :]


def _int(text: str) -> int:
    return 0 if text == "-" else int(text.replace(",", ""))


def _one_decimal(x: float) -> Decimal:
    return Decimal(repr(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


FR_1112_CHECK = "Final Report 11.12: firewood and gas share by district"


def _sum(ours: dict[tuple[str, str], float], geo: str, indicators: list[str]) -> float | None:
    """Sum of release values, or None when any is missing (reported as a difference)."""
    parts = [ours.get((geo, i)) for i in indicators]
    return None if any(p is None for p in parts) else float(sum(p for p in parts if p is not None))


def _compare(result: Result, key: str, label: str, pdf: object, got: object) -> None:
    result.compared += 1
    if got != pdf:
        result.differences[key] = f"{label}: Final Report {pdf}, release {got}"


ETHNIC = [
    ["population_total"],
    ["population_ethnicity_sinhalese"],
    ["population_ethnicity_sri_lanka_tamil"],
    ["population_ethnicity_indian_tamil"],
    ["population_ethnicity_sri_lanka_moor"],
    ["population_ethnicity_burgher"],
    ["population_ethnicity_malay"],
    # the report's "Other" combines these four A6 categories
    [
        "population_ethnicity_sri_lanka_chetty",
        "population_ethnicity_bharatha",
        "population_ethnicity_veddha",
        "population_ethnicity_other",
    ],
]
RELIGION = [
    ["population_total"],
    ["population_religion_buddhist"],
    ["population_religion_hindu"],
    ["population_religion_islam"],
    ["population_religion_roman_catholic"],
    ["population_religion_other_christian"],
    ["population_religion_other"],
]


def ethnicity_religion(release: Path, pages_dir: Path) -> list[Result]:
    ours = values(release, GND, TOPICS)
    places = district_ids(release)
    out = []
    for check, page, title, columns, width, pick in (
        (
            "Final Report 6.1.11: ethnic group by district",
            115,
            "Table 6.1.11",
            ETHNIC,
            16,
            slice(1, None, 2),
        ),
        (
            "Final Report 6.1.15: religion by district",
            124,
            "Table 6.1.15",
            RELIGION,
            7,
            slice(None),
        ),
    ):
        text = _page(pages_dir, page, title)
        pattern = re.compile(rf"^([A-Z][A-Za-z ]+?) ((?:{NUM} ){{{width - 1}}}{NUM})$", re.M)
        rows = {name: [_int(n) for n in nums.split()] for name, nums in pattern.findall(text)}
        if len(rows) != 26:
            raise ValueError(f"{title}: {len(rows)} lines, expected 26")
        result = Result(check)
        for name, numbers in rows.items():
            geo = places[mat.district_key(name)]
            for indicators, pdf in zip(columns, numbers[pick], strict=True):
                total = _sum(ours, geo, indicators)
                got = None if total is None else int(total)
                _compare(result, f"{geo} {'+'.join(indicators)}", f"{name}", pdf, got)
        out.append(result)
    return out


def sector(release: Path, pages_dir: Path) -> Result:
    text = _page(pages_dir, 72, "Table 3.6 : Population Distribution by District and Sector, 2024")
    tokens = text[: text.index("According to Table 3.6")].split()
    ours = values(release, TOPICS)
    places = district_ids(release)
    rows: dict[str, list[int]] = {}
    i = 0
    while i < len(tokens):
        for words in (2, 1):
            key = mat.district_key(" ".join(tokens[i : i + words]))
            if key in places and i + words < len(tokens) and re.fullmatch(NUM, tokens[i + words]):
                cells = tokens[i + words : i + words + 10]
                rows[places[key]] = [_int(c) for c in cells[0::2]]
                i += words + 10
                break
        else:
            i += 1
    if len(rows) != 26:
        raise ValueError(f"Table 3.6: {len(rows)} lines, expected 26")
    result = Result("Final Report 3.6: sector by district")
    for geo, (total, urban, estate_urban, rural, estate_rural) in rows.items():
        if total != urban + estate_urban + rural + estate_rural:
            raise ValueError(f"Table 3.6 {geo}: sectors do not add up to the total")
        # the release's "urban" is DCS's Urban*, urban plus estate urban
        for indicator, pdf in (
            ("population_sector_urban", urban + estate_urban),
            ("population_sector_rural", rural),
            ("population_sector_estate_rural", estate_rural),
        ):
            got = ours.get((geo, indicator))
            _compare(result, f"{geo} {indicator}", geo, pdf, None if got is None else int(got))
    return result


def age(release: Path, pages_dir: Path) -> Result:
    text = _page(pages_dir, 104, "Table 6.1.3 : Population by Age Groups and Sex, 2012 and 2024")
    ours = values(release, GND, TOPICS)
    num = r"([\d,]+)"
    row = re.compile(rf"^(\d\d[\u2013-]\d\d|95 and over|Sri Lanka) {' '.join([num] * 6)}$", re.M)
    result = Result("Final Report 6.1.3: national five-year age groups")
    for m in row.finditer(text):
        label = m.group(1)
        total, male, female = (_int(m.group(i)) for i in (5, 6, 7))
        if label == "Sri Lanka":
            pairs = [
                ("population_total", total),
                ("population_male", male),
                ("population_female", female),
            ]
        elif label == "95 and over":
            pairs = [("population_age_95_plus", total)]
        else:
            lo, hi = (int(x) for x in re.split(r"[\u2013-]", label))
            pairs = [(f"population_age_{lo}_{hi}", total)]
        for indicator, pdf in pairs:
            got = ours.get(("LK", indicator))
            _compare(result, f"LK {indicator}", label, pdf, None if got is None else int(got))
    if result.compared != 23:
        raise ValueError(f"Table 6.1.3: {result.compared} values, expected 23")
    return result


WATER = {
    "Protected well": ["households_water_protected_well"],
    "Semi protected well": ["households_water_semi_protected_well"],
    "Unprotected well": ["households_water_unprotected_well"],
    "Tube well": ["households_water_tube_well"],
    "Spring/Fountain": ["households_water_spring"],
    "Pipe borne water - National water supply & drainage board": ["households_water_pipe_nwsdb"],
    "Pipe borne water - Local Authority": ["households_water_pipe_local_authority"],
    "Pipe borne water - Community based organization": ["households_water_pipe_community"],
    "Pipe borne water - Private water supply project": ["households_water_pipe_private"],
    "Tank/ River/Streams": ["households_water_tank_river_stream"],
    "Rainwater": ["households_water_rain_water"],
    "Bottled water": ["households_water_bottled_water"],
    "Filter water (R.O. Plant)": ["households_water_filter_ro_plant"],
    "Bowser": ["households_water_bowser"],
    "Other": ["households_water_other"],
}
LIGHTING = {
    "Electricity - National grid/Rural hydro power project": [
        "households_lighting_electricity_grid"
    ],
    "Kerosene lamp": ["households_lighting_kerosene_lamp"],
    "Solar power (grid connected)": ["households_lighting_solar_grid_connected"],
    "Solar power (standalone)": ["households_lighting_solar_stand_alone"],
    # footnote: "Other" includes biogas, generator and other
    "Other*": [
        "households_lighting_biogas",
        "households_lighting_generator",
        "households_lighting_other",
    ],
}
# The report's material "Other" equals the release's Other plus "Not relevant".
MATERIALS = {
    ("Wall", "Bricks"): ["housing_wall_brick_share"],
    ("Wall", "Cement block"): ["housing_wall_cement_block_share"],
    ("Wall", "Granite/Cube stones"): ["housing_wall_granite_cube_stone_share"],
    ("Wall", "Cabook"): ["housing_wall_cabook_share"],
    ("Wall", "Pressed soil bricks"): ["housing_wall_pressed_soil_brick_share"],
    ("Wall", "Mud/Warichchi"): ["housing_wall_mud_share"],
    ("Wall", "Cadjan/Palmyra"): ["housing_wall_cadjan_palmyrah_share"],
    ("Wall", "Planks/Metal sheets/Asbestos"): ["housing_wall_plank_metal_sheet_asbestos_share"],
    ("Wall", "Zink Aluminium Sheets"): ["housing_wall_zinc_aluminium_sheet_share"],
    ("Wall", "Other"): ["housing_wall_other_share", "housing_wall_not_relevant_share"],
    ("Roof", "Tile"): ["housing_roof_tile_share"],
    ("Roof", "Asbestos"): ["housing_roof_asbestos_share"],
    ("Roof", "Concrete"): ["housing_roof_concrete_share"],
    ("Roof", "Zink Aluminium Sheets"): ["housing_roof_zinc_aluminium_sheet_share"],
    ("Roof", "Metal Sheet"): ["housing_roof_metal_sheet_share"],
    ("Roof", "Cadjan/Palmyra/Straw"): ["housing_roof_cadjan_palmyrah_straw_share"],
    ("Roof", "Other"): ["housing_roof_other_share", "housing_roof_not_relevant_share"],
    ("Floor", "Cement"): ["housing_floor_cement_share"],
    ("Floor", "Terrazzo/Tile/Granite/Wood (Finished)/Titanium"): [
        "housing_floor_terrazzo_tile_granite_finished_wood_share"
    ],
    ("Floor", "Concrete"): ["housing_floor_concrete_share"],
    ("Floor", "Mud"): ["housing_floor_mud_share"],
    ("Floor", "Wood"): ["housing_floor_wood_share"],
    ("Floor", "Sand"): ["housing_floor_sand_share"],
    ("Floor", "Other"): ["housing_floor_other_share", "housing_floor_not_relevant_share"],
}


def housing(release: Path, pages_dir: Path) -> list[Result]:
    ours = values(release, TOPICS)
    places = district_ids(release)
    out = []
    for check, page, title, mapping in (
        ("Final Report 11.9: drinking water, national counts", 208, "Table 11.9", WATER),
        ("Final Report 11.13: lighting, national counts", 212, "Table 11.13", LIGHTING),
    ):
        text = _page(pages_dir, page, title)
        result = Result(check)
        for name, indicators in mapping.items():
            m = re.search(rf"^{re.escape(name)} ({NUM}) ", text, re.M)
            if m is None:
                raise ValueError(f"{title}: line {name!r} not found")
            total = _sum(ours, "LK", indicators)
            got = None if total is None else int(total)
            _compare(result, f"LK {'+'.join(indicators)}", name, _int(m.group(1)), got)
        out.append(result)

    text = _page(pages_dir, 211, "Table 11.12")
    result = Result(FR_1112_CHECK)
    for m in re.finditer(r"^([A-Z][A-Za-z ]+?) [\d.]+ ([\d.]+) [\d.]+ ([\d.]+)$", text, re.M):
        geo = places.get(mat.district_key(m.group(1)))
        if geo is None:
            continue  # sector lines
        for indicator, pdf in (
            ("households_cooking_firewood_share", m.group(2)),
            ("households_cooking_gas_share", m.group(3)),
        ):
            value = ours.get((geo, indicator))
            got = None if value is None else _one_decimal(value)
            _compare(result, f"{geo} {indicator}", m.group(1), Decimal(pdf), got)
    if result.compared != 52:
        raise ValueError(f"Table 11.12: {result.compared} values, expected 52")
    out.append(result)

    text = _page(pages_dir, 205, "Table 11.6")
    result = Result("Final Report 11.6: wall, roof and floor materials, national %")
    section = ""
    for line in text.splitlines():
        if line in ("Wall", "Roof", "Floor"):
            section = line
            continue
        m = re.fullmatch(r"(.+) (\d+\.\d)", line)
        if not (section and m and (section, m.group(1)) in MATERIALS):
            continue
        indicators = MATERIALS[(section, m.group(1))]
        total = _sum(ours, "LK", indicators)
        got = None if total is None else _one_decimal(total)
        _compare(
            result,
            f"LK {'+'.join(indicators)}",
            f"{section} {m.group(1)}",
            Decimal(m.group(2)),
            got,
        )
        if section == "Floor" and m.group(1) == "Other":
            break
    if result.compared != len(MATERIALS):
        raise ValueError(f"Table 11.6: {result.compared} values, expected {len(MATERIALS)}")
    out.append(result)
    return out
