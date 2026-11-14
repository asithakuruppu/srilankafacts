"""Cross-check: Final Report Table 6.1.3 (population by five-year age group, 2024) vs the release.

The release's national five-year age counts (census-2024-topic-tables, step b; 60-64 from
census-2024-gnd-tables) are sums of GN rows. The Final Report (CPH2024_Final_Eng.pdf, Table
6.1.3, PDF page 104) prints the 2024 national totals by age group and sex. Run from pipeline/:

    swift scripts/pdf_pages.swift <CPH2024_Final_Eng.pdf> data/build/audit/pdf-pages 104
    uv run python ../docs/qa/data/census-2024-final-report-age.py <release dir>
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

PAGE = Path("data/build/audit/pdf-pages/page-104.txt")


def main(release: Path) -> None:
    text = PAGE.read_text(encoding="utf-8")
    text = text[text.index("Table 6.1.3 : Population by Age Groups and Sex, 2012 and 2024") :]
    values: dict[str, float] = {}
    for name in ("census-2024-gnd-tables", "census-2024-topic-tables"):
        obs = pd.read_parquet(
            release / "observations" / f"{name}.parquet",
            columns=["geography_id", "indicator_id", "value"],
        )
        lk = obs[obs["geography_id"] == "LK"]
        values |= dict(zip(lk["indicator_id"], lk["value"], strict=True))

    num = r"([\d,]+)"
    row = re.compile(rf"^(\d\d[\u2013-]\d\d|95 and over|Sri Lanka) {' '.join([num] * 6)}$", re.M)
    compared = differences = 0
    for m in row.finditer(text):
        label = m.group(1)
        total, male, female = (int(m.group(i).replace(",", "")) for i in (5, 6, 7))
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
            ours = values.get(indicator)
            compared += 1
            if ours is None or int(ours) != pdf:
                differences += 1
                print(f"DIFF {label} {indicator}: PDF {pdf:,}, release {ours}")
    assert compared == 23, compared
    print(f"Table 6.1.3 age (Sri Lanka, 2024): {compared} values compared, {differences} differ")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
