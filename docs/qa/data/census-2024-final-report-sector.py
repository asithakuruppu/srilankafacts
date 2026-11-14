"""Cross-check: Final Report Table 3.6 (population by district and sector) against the release.

The release's sector counts (census-2024-topic-tables, step b) are sums of GN rows from DCS's GN
sector file, whose "Urban*" column combines DCS's urban and estate urban sectors. The Final Report
(CPH2024_Final_Eng.pdf, Table 3.6, PDF page 72) prints all four sectors for Sri Lanka and each
district. Run from pipeline/:

    swift scripts/pdf_pages.swift <CPH2024_Final_Eng.pdf> data/build/audit/pdf-pages 72
    uv run python ../docs/qa/data/census-2024-final-report-sector.py <release dir>

Rows wrap irregularly in the extracted text, so each row is read as the 10 tokens after its
district name: total, %, urban, %, estate urban, %, rural, %, estate rural, %. "-" is zero.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

from slf.datasets import census_2024_materials as mat

PAGE = Path("data/build/audit/pdf-pages/page-072.txt")


def main(release: Path) -> None:
    text = PAGE.read_text(encoding="utf-8")
    start = text.index("Table 3.6 : Population Distribution by District and Sector, 2024")
    end = text.index("According to Table 3.6")
    tokens = text[start:end].split()
    names = pd.read_parquet(
        release / "geographies.parquet", columns=["geography_id", "name_en", "level"]
    )
    districts = {n: g for g, n, lv in names.itertuples(index=False) if lv == 2}
    obs = pd.read_parquet(
        release / "observations" / "census-2024-topic-tables.parquet",
        columns=["geography_id", "indicator_id", "value"],
    )
    values = obs.set_index(["geography_id", "indicator_id"])["value"].to_dict()

    rows: dict[str, list[int]] = {}
    i = 0
    places = {"Sri Lanka": "LK"} | {n: g for n, g in districts.items()}
    # the PDF spells some names differently; match through the normalised district key
    keyed = {mat.district_key(n): (n, g) for n, g in places.items()}
    while i < len(tokens):
        for words in (2, 1):
            name = " ".join(tokens[i : i + words])
            if mat.district_key(name) in keyed and re.fullmatch(r"[\d,]+", tokens[i + words]):
                cells = tokens[i + words : i + words + 10]
                rows[keyed[mat.district_key(name)][1]] = [
                    0 if c == "-" else int(c.replace(",", "")) for c in cells[0::2]
                ]
                i += words + 10
                break
        else:
            i += 1
    assert len(rows) == 26, sorted(rows)
    compared = differences = 0
    for geo, (total, urban, estate_urban, rural, estate_rural) in rows.items():
        assert total == urban + estate_urban + rural + estate_rural, geo
        for indicator, pdf in (
            ("population_sector_urban", urban + estate_urban),
            ("population_sector_rural", rural),
            ("population_sector_estate_rural", estate_rural),
        ):
            ours = values.get((geo, indicator))
            compared += 1
            if ours is None or int(ours) != pdf:
                differences += 1
                print(f"DIFF {geo} {indicator}: PDF {pdf:,}, release {ours}")
    print(f"Table 3.6 sector: {len(rows)} lines, {compared} values compared, {differences} differ")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
