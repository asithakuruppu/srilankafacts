"""Cross-check: Final Report housing chapter (Tables 11.6, 11.9, 11.12, 11.13) against the release.

Compares the DCS Final Report (CPH2024_Final_Eng.pdf) with census-2024-topic-tables:

- 11.9 households by main source of drinking water, Sri Lanka, counts (PDF page 208);
- 11.13 households by main source of lighting, Sri Lanka, counts (page 212); its "Other"
  combines biogas, generator and other;
- 11.12 share of households using firewood / gas for cooking, Sri Lanka and 25 districts, one
  decimal (page 211). These differ by 0.1 in some places; no grouping of categories or choice of
  denominator reproduces all of them, while DCS's own district table A13 matches the release
  exactly, so they are reported, not treated as release errors;
- 11.6 housing units by wall, roof and floor material, Sri Lanka, percent, one decimal (page 205).

Percentages are compared after rounding the release share half-up to one decimal. Run from
pipeline/:

    swift scripts/pdf_pages.swift <CPH2024_Final_Eng.pdf> data/build/audit/pdf-pages 205 208 211 212
    uv run python ../docs/qa/data/census-2024-final-report-housing.py <release dir>
"""

from __future__ import annotations

import re
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pandas as pd

from slf.datasets import census_2024_materials as mat

PAGES = Path("data/build/audit/pdf-pages")
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
    "Other*": [
        "households_lighting_biogas",
        "households_lighting_generator",
        "households_lighting_other",
    ],
}
# (section, PDF label) -> release share indicator(s). The Final Report's "Other" matches the
# release's Other plus "Not relevant" (it has no "Not relevant" line).
MATERIALS = {
    ("Wall", "Bricks"): "housing_wall_brick_share",
    ("Wall", "Cement block"): "housing_wall_cement_block_share",
    ("Wall", "Granite/Cube stones"): "housing_wall_granite_cube_stone_share",
    ("Wall", "Cabook"): "housing_wall_cabook_share",
    ("Wall", "Pressed soil bricks"): "housing_wall_pressed_soil_brick_share",
    ("Wall", "Mud/Warichchi"): "housing_wall_mud_share",
    ("Wall", "Cadjan/Palmyra"): "housing_wall_cadjan_palmyrah_share",
    ("Wall", "Planks/Metal sheets/Asbestos"): "housing_wall_plank_metal_sheet_asbestos_share",
    ("Wall", "Zink Aluminium Sheets"): "housing_wall_zinc_aluminium_sheet_share",
    ("Wall", "Other"): "housing_wall_other_share+housing_wall_not_relevant_share",
    ("Roof", "Tile"): "housing_roof_tile_share",
    ("Roof", "Asbestos"): "housing_roof_asbestos_share",
    ("Roof", "Concrete"): "housing_roof_concrete_share",
    ("Roof", "Zink Aluminium Sheets"): "housing_roof_zinc_aluminium_sheet_share",
    ("Roof", "Metal Sheet"): "housing_roof_metal_sheet_share",
    ("Roof", "Cadjan/Palmyra/Straw"): "housing_roof_cadjan_palmyrah_straw_share",
    ("Roof", "Other"): "housing_roof_other_share+housing_roof_not_relevant_share",
    ("Floor", "Cement"): "housing_floor_cement_share",
    (
        "Floor",
        "Terrazzo/Tile/Granite/Wood (Finished)/Titanium",
    ): "housing_floor_terrazzo_tile_granite_finished_wood_share",
    ("Floor", "Concrete"): "housing_floor_concrete_share",
    ("Floor", "Mud"): "housing_floor_mud_share",
    ("Floor", "Wood"): "housing_floor_wood_share",
    ("Floor", "Sand"): "housing_floor_sand_share",
    ("Floor", "Other"): "housing_floor_other_share+housing_floor_not_relevant_share",
}


def page(n: int, title: str) -> str:
    text = (PAGES / f"page-{n:03d}.txt").read_text(encoding="utf-8")
    start = text.index(title)
    return text[start:]


def one_decimal(x: float) -> Decimal:
    return Decimal(repr(x)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def main(release: Path) -> None:
    obs = pd.read_parquet(
        release / "observations" / "census-2024-topic-tables.parquet",
        columns=["geography_id", "indicator_id", "value"],
    )
    values = obs.set_index(["geography_id", "indicator_id"])["value"].to_dict()
    names = pd.read_parquet(
        release / "geographies.parquet", columns=["geography_id", "name_en", "level"]
    )
    districts = {mat.district_key(n): g for g, n, lv in names.itertuples(index=False) if lv == 2}
    results: list[tuple[str, int, int]] = []

    def counts(label: str, text: str, mapping: dict[str, list[str]]) -> None:
        compared = differences = 0
        for name, indicators in mapping.items():
            m = re.search(rf"^{re.escape(name)} ([\d,]+) ", text, re.M)
            assert m, (label, name)
            pdf = int(m.group(1).replace(",", ""))
            ours = int(sum(values[("LK", i)] for i in indicators))
            compared += 1
            if ours != pdf:
                differences += 1
                print(f"DIFF {label} {name}: PDF {pdf:,}, release {ours:,}")
        results.append((label, compared, differences))

    counts("11.9 drinking water (LK, counts)", page(208, "Table 11.9"), WATER)
    counts("11.13 lighting (LK, counts)", page(212, "Table 11.13"), LIGHTING)

    text = page(211, "Table 11.12")
    compared = differences = 0
    for m in re.finditer(r"^([A-Z][A-Za-z ]+?) [\d.]+ ([\d.]+) [\d.]+ ([\d.]+)$", text, re.M):
        key = mat.district_key(m.group(1))
        geo = "LK" if key == "sri lanka" else districts.get(key)
        if geo is None:
            continue  # sector lines (Urban*, Rural, Estate- Rural**)
        for indicator, pdf in (
            ("households_cooking_firewood_share", m.group(2)),
            ("households_cooking_gas_share", m.group(3)),
        ):
            compared += 1
            ours = one_decimal(values[(geo, indicator)])
            if ours != Decimal(pdf):
                differences += 1
                print(f"DIFF 11.12 {m.group(1)} {indicator}: PDF {pdf}, release {ours}")
    assert compared == 52, compared
    results.append(("11.12 firewood and gas (LK + 25 districts, %)", compared, differences))

    text = page(205, "Table 11.6")
    section = ""
    compared = differences = 0
    for line in text.splitlines():
        if line in ("Wall", "Roof", "Floor"):
            section = line
            continue
        m = re.fullmatch(r"(.+) (\d+\.\d)", line)
        if not (section and m and (section, m.group(1)) in MATERIALS):
            continue
        indicator = MATERIALS[(section, m.group(1))]
        compared += 1
        ours = one_decimal(sum(values[("LK", i)] for i in indicator.split("+")))
        if ours != Decimal(m.group(2)):
            differences += 1
            print(f"DIFF 11.6 {section} {m.group(1)}: PDF {m.group(2)}, release {ours}")
        if section == "Floor" and m.group(1) == "Other":
            break
    assert compared == len(MATERIALS), compared
    results.append(("11.6 wall, roof, floor materials (LK, %)", compared, differences))

    for label, n, d in results:
        print(f"{label}: {n} values compared, {d} differ")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
