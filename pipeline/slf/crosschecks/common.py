"""Shared pieces for the independent cross-checks (Q01, every release)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from slf.datasets import census_2024_materials as mat

ROOT = Path(__file__).resolve().parents[3]


@dataclass
class Result:
    """One comparison: how many values were compared and which differ.

    ``differences`` maps a stable key ("<geography id> <indicator>") to a readable message.
    """

    check: str
    compared: int = 0
    differences: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


def values(release: Path, *datasets: str) -> dict[tuple[str, str], float]:
    frames = [
        pd.read_parquet(
            release / "observations" / f"{d}.parquet",
            columns=["geography_id", "indicator_id", "value"],
        )
        for d in datasets
    ]
    frame = pd.concat(frames)
    return frame.set_index(["geography_id", "indicator_id"])["value"].to_dict()


def district_ids(release: Path) -> dict[str, str]:
    """Normalised district name (``mat.district_key``) -> spine id, plus 'sri lanka' -> LK."""
    names = pd.read_parquet(
        release / "geographies.parquet", columns=["geography_id", "name_en", "level"]
    )
    out = {mat.district_key(n): g for g, n, lv in names.itertuples(index=False) if lv == 2}
    return {"sri lanka": "LK"} | out
