"""Cross-check: Final Report Tables 6.1.11 and 6.1.15 against the release (D-033 values).

The DCS Final Report (CPH2024_Final_Eng.pdf, sha256 in the census-2024-gnd-tables dossier) prints
the 2024 population by ethnic group and by religion for Sri Lanka and each district. The release
takes these values from DCS's Population tables A6/A7 (census-2024-topic-tables). This compares
the two. Run from pipeline/, after extracting the page text with PDFKit:

    swift scripts/pdf_pages.swift <CPH2024_Final_Eng.pdf> data/build/audit/pdf-pages 115 124
    uv run python ../docs/qa/data/census-2024-final-report-ethnicity-religion.py <release dir>

Table 6.1.11 (PDF page 115) gives 2012 and 2024 side by side; only 2024 is compared. Its "Other"
column combines A6's Sri Lanka Chetty, Bharatha, Veddha and Other.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

from slf.datasets import census_2024_materials as mat

PAGES = Path("data/build/audit/pdf-pages")
ETHNIC = [  # Table 6.1.11 column order (2024 values), each a list of release indicators to add
    ["population_total"],
    ["population_ethnicity_sinhalese"],
    ["population_ethnicity_sri_lanka_tamil"],
    ["population_ethnicity_indian_tamil"],
    ["population_ethnicity_sri_lanka_moor"],
    ["population_ethnicity_burgher"],
    ["population_ethnicity_malay"],
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
NUM = r"[\d,]+"


def rows(page: int, title: str, numbers: int) -> dict[str, list[int]]:
    text = (PAGES / f"page-{page:03d}.txt").read_text(encoding="utf-8")
    assert title in text, (page, title)
    pattern = re.compile(rf"^([A-Z][A-Za-z ]+?) ((?:{NUM} ){{{numbers - 1}}}{NUM})$", re.M)
    out = {}
    for name, nums in pattern.findall(text):
        out[name] = [int(n.replace(",", "")) for n in nums.split()]
    return out


def main(release: Path) -> None:
    topics = pd.read_parquet(
        release / "observations" / "census-2024-topic-tables.parquet",
        columns=["geography_id", "indicator_id", "value"],
    )
    gnd = pd.read_parquet(
        release / "observations" / "census-2024-gnd-tables.parquet",
        columns=["geography_id", "indicator_id", "value"],
    )
    values = pd.concat([topics, gnd]).set_index(["geography_id", "indicator_id"])["value"].to_dict()
    names = pd.read_parquet(
        release / "geographies.parquet", columns=["geography_id", "name_en", "level"]
    )
    places = {"sri lanka": "LK"} | {
        mat.district_key(n): g for g, n, lv in names.itertuples(index=False) if lv == 2
    }
    for label, page, title, columns, width, pick in (
        ("Table 6.1.11 ethnic group", 115, "Table 6.1.11", ETHNIC, 16, slice(1, None, 2)),
        ("Table 6.1.15 religion", 124, "Table 6.1.15", RELIGION, 7, slice(None)),
    ):
        table = rows(page, title, width)
        assert len(table) == 26, (label, len(table), sorted(table))
        compared = differences = 0
        for name, numbers in table.items():
            geo = places[mat.district_key(name)]
            for indicators, pdf in zip(columns, numbers[pick], strict=True):
                ours = sum(values[(geo, i)] for i in indicators)
                compared += 1
                if int(ours) != pdf:
                    differences += 1
                    print(
                        f"DIFF {label} {name} ({geo}) {'+'.join(indicators)}: "
                        f"PDF {pdf:,}, release {int(ours):,}"
                    )
        print(f"{label}: {len(table)} lines, {compared} values compared, {differences} differ")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
