"""downloads_only indicators stay out of place and per-level API files (LA-004); places_only
indicators are in place files but not in per-level files (D-033)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from slf.catalog import Catalog
from slf.release import _write_api
from slf.schemas import Indicator


def _indicator(indicator_id: str, distribution: str) -> Indicator:
    return Indicator(
        id=indicator_id,
        name=indicator_id,
        measure_type="count",
        unit="households",
        aggregation="sum",
        distribution=distribution,  # type: ignore[arg-type]
        definition="test",
    )


def _observation(indicator_id: str, value: float) -> dict[str, object]:
    return {
        "indicator_id": indicator_id,
        "geography_id": "LK",
        "value": value,
        "value_status": "normal",
        "unit": "households",
        "period": "2024",
        "time_start": "2024-12-19",
        "time_end": "2024-12-19",
        "claim_id": f"c:{indicator_id}",
        "dataset_id": "ds",
        "snapshot_sha256": "abc",
        "source_locator": "test",
        "verification": "machine_extracted",
        "support_type": "area_total",
        "information_footprint_ref": "gn-2024",
    }


def test_distribution_controls_place_and_level_files(tmp_path: Path):
    catalog = Catalog(
        indicators={
            "households_total": _indicator("households_total", "api"),
            "households_water_bowser": _indicator("households_water_bowser", "downloads_only"),
            "population_religion_hindu": _indicator("population_religion_hindu", "places_only"),
        }
    )
    observations = pd.DataFrame(
        [
            _observation("households_total", 10.0),
            _observation("households_water_bowser", 2.0),
            _observation("population_religion_hindu", 3.0),
        ]
    )
    geographies = pd.DataFrame(
        [
            {
                "geography_id": "LK",
                "name_en": "Sri Lanka",
                "name_si": None,
                "name_ta": None,
                "level": 0,
                "parent_id": None,
                "status": "current",
            }
        ]
    )
    written = _write_api(
        tmp_path,
        version="v0",
        preview=True,
        observations=observations,
        geographies=geographies,
        catalog=catalog,
        datasets=[],
        citation="test",
    )
    place = json.loads((tmp_path / "api/v1/places/LK.json").read_text())
    assert [v["indicator_id"] for v in place["values"]] == [
        "households_total",
        "population_religion_hindu",
    ]
    assert not any(w.startswith("api/v1/indicators/population_religion_hindu/") for w in written)
    assert not any(w.startswith("api/v1/indicators/households_water_bowser/") for w in written)
    assert any(w.startswith("api/v1/indicators/households_total/") for w in written)
    index = json.loads((tmp_path / "api/v1/indicators.json").read_text())
    entry = {i["id"]: i for i in index["indicators"]}["households_water_bowser"]
    assert entry["distribution"] == "downloads_only"
    assert entry["topic"] == []
    assert entry["value_count"] == 1
