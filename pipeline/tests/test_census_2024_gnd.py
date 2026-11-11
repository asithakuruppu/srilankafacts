from pathlib import Path

import pytest

from slf.datasets import census_2024_gnd as mod


def test_derived_values_come_from_published_counts():
    counts: dict[str, float] = {
        "population_total": 1000.0,
        "population_male": 480.0,
        "population_female": 520.0,
        "population_age_0_14": 200.0,
        "population_age_15_59": 650.0,
        "population_age_60_64": 60.0,
        "population_age_65_plus": 90.0,
        "occupied_housing_units": 250.0,
    }
    derived = mod._derived(counts, area_km2=2.0)
    assert derived["population_age_60_plus"] == 150.0
    assert derived["sex_ratio"] == pytest.approx(92.3077)
    assert derived["population_age_0_14_share"] == pytest.approx(20.0)
    assert derived["population_age_60_plus_share"] == pytest.approx(15.0)
    assert derived["persons_per_occupied_housing_unit"] == pytest.approx(4.0)
    assert derived["population_density"] == pytest.approx(500.0)


def test_derived_values_are_null_when_denominator_is_zero_or_missing():
    counts: dict[str, float] = dict.fromkeys(mod.COUNT_INDICATORS, 0.0)
    derived = mod._derived(counts, area_km2=None)
    assert derived["population_age_60_plus"] == 0.0
    assert derived["sex_ratio"] is None
    assert derived["population_age_0_14_share"] is None
    assert derived["population_age_60_plus_share"] is None
    assert derived["persons_per_occupied_housing_unit"] is None
    assert derived["population_density"] is None


def test_row_records_provenance_and_verification_level():
    row = mod._row(
        indicator="population_total",
        geography_id="LK11",
        value=1.0,
        source_locator="GN_population.xlsx row 6",
        snapshot_sha256="abc",
    )
    assert row["dataset_id"] == "census-2024-gnd-tables"
    assert row["verification"] == "machine_extracted"
    assert row["revision_status"] == "provisional"
    assert row["support_type"] == "area_total"
    assert row["time_support"] == "snapshot"
    assert row["snapshot_sha256"] == "abc"


def _rows(geography_id: str, indicator_values: dict[str, float]) -> list[dict]:
    rows = []
    for indicator in mod.ALL_INDICATORS:
        value = indicator_values.get(indicator, 0.0)
        rows.append(
            mod._row(
                indicator=indicator,
                geography_id=geography_id,
                value=value,
                source_locator="test",
                snapshot_sha256="abc",
            )
        )
    return rows


def test_validate_accepts_district_total_keyed_by_code(monkeypatch):
    monkeypatch.setattr(mod, "EXPECTED_NATIONAL", {})
    monkeypatch.setattr(mod, "EXPECTED_DISTRICTS_POP", {11: 1000})
    monkeypatch.setattr(mod, "EXPECTED_DISTRICTS_HOUSING", {11: 250})
    rows = _rows(
        "LK11",
        {
            "population_total": 1000.0,
            "occupied_housing_units": 250.0,
        },
    )
    report = mod.Census2024Gnd().validate(rows)
    assert report.ok, report.errors


def test_validate_flags_district_total_mismatch(monkeypatch):
    monkeypatch.setattr(mod, "EXPECTED_NATIONAL", {})
    monkeypatch.setattr(mod, "EXPECTED_DISTRICTS_POP", {11: 999})
    monkeypatch.setattr(mod, "EXPECTED_DISTRICTS_HOUSING", {})
    rows = _rows(
        "LK11",
        {
            "population_total": 1000.0,
            "occupied_housing_units": 250.0,
        },
    )
    report = mod.Census2024Gnd().validate(rows)
    assert any("district LK11: population 1000.0, expected 999" in e for e in report.errors)


def test_crosswalk_uses_provisional_kalmunai_and_leaves_5224_unmapped():
    catalog = Path(__file__).resolve().parents[2] / "catalog"
    gn, ds = mod._crosswalk(catalog)
    assert ds["5221"] == "LK-ADM3-P0001"
    assert "5224" not in ds
    assert gn["1103005"] == "LK1103005"
