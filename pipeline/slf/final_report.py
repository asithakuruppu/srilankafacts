"""DCS Census 2024 Final Report tables 3.2 and 11.2 as a reviewable reference CSV.

The Final Report is a PDF in the census snapshot (`CPH2024_Final_Eng.pdf`). Page text is
extracted on macOS with `scripts/pdf_pages.swift` (PDFKit); this module parses that text and
writes `catalog/references/dcs-cph2024-final-report-tables.csv`, one row per place and
indicator, with the page, table and snapshot sha256. Values stay `machine_extracted`.

Place names in the PDF are matched to codes using the names in the DCS GN workbook itself, so no
name is matched against another source (AGENTS rule 5).
"""

from __future__ import annotations

import re
from pathlib import Path

import openpyxl
import pandas as pd

PDF_FILE = "CPH2024_Final_Eng.pdf"
TABLES = {
    # indicator: (table, 1-based PDF page, printed page)
    "population_total": ("Table 3.2", 68, 51),
    "occupied_housing_units": ("Table 11.2", 202, 185),
}
COLUMNS = [
    "geography_id",
    "pdf_name",
    "indicator_id",
    "value",
    "table",
    "pdf_page",
    "printed_page",
    "snapshot_file",
    "snapshot_sha256",
    "verification",
]


def parse_table(text: str) -> dict[str, int]:
    """Rows like 'Western Province 6,117,341 28.1' or 'Colombo 562,550 78,052 654,051 113,837'.

    Table 11.2 has four numbers per row (2012 occupied, 2012 vacant, 2024 occupied, 2024
    vacant); the third is the 2024 occupied count.
    """
    out: dict[str, int] = {}
    for line in text.splitlines():
        m = re.match(r"^([A-Z][A-Za-z ]+?)\s+((?:[\d,]+\s*)+(?:\d+\.\d)?)$", line.strip())
        if not m:
            continue
        nums = [int(n.replace(",", "")) for n in re.findall(r"\d[\d,]*(?!\.\d)", m[2]) if "," in n]
        if nums:
            out[m[1].strip()] = nums[0] if len(nums) < 4 else nums[2]
    return out


def workbook_names(pop_xlsx: Path) -> dict[str, str]:
    """DCS province/district names from the GN workbook -> COD-AB ids (LK1, LK11, ...)."""
    names = {"Sri Lanka": "LK"}
    wb = openpyxl.load_workbook(pop_xlsx, read_only=True, data_only=True)
    for row in wb["Population"].iter_rows(min_row=6, values_only=True):
        if row[0] is None:
            continue
        names[f"{str(row[1]).strip()} Province"] = f"LK{int(row[0])}"  # type: ignore[arg-type]
        names[str(row[3]).strip()] = f"LK{int(row[2])}"  # type: ignore[arg-type]
    wb.close()
    return names


def extract(pages_dir: Path, pop_xlsx: Path, pdf_sha256: str) -> tuple[pd.DataFrame, list[str]]:
    names = workbook_names(pop_xlsx)
    rows, problems = [], []
    for indicator, (table, page, printed) in TABLES.items():
        path = pages_dir / f"page-{page:03d}.txt"
        if not path.exists():
            problems.append(f"missing {path}; run scripts/pdf_pages.swift for page {page}")
            continue
        parsed = parse_table(path.read_text(encoding="utf-8"))
        for name, value in parsed.items():
            geo = names.get(name)
            if geo is None:
                problems.append(f"{table}: no workbook name matches {name!r}")
                continue
            rows.append(
                {
                    "geography_id": geo,
                    "pdf_name": name,
                    "indicator_id": indicator,
                    "value": value,
                    "table": table,
                    "pdf_page": page,
                    "printed_page": printed,
                    "snapshot_file": PDF_FILE,
                    "snapshot_sha256": pdf_sha256,
                    "verification": "machine_extracted",
                }
            )
    frame = pd.DataFrame(rows, columns=COLUMNS).sort_values(["indicator_id", "geography_id"])
    return frame.reset_index(drop=True), problems
