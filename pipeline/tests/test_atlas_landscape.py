"""Feature categories: events, organisations and admin units are not shown as places."""

from __future__ import annotations

from slf.atlas_landscape import _category


def test_events_and_admin_units_are_left_out() -> None:
    assert _category("heritage", "suicide car bombing") is None
    assert _category("heritage", "holiday|festival") is None
    assert _category("heritage", "fourth-level administrative division") is None
    assert _category("place", "A.ADM4") is None


def test_places_get_readable_categories() -> None:
    assert _category("heritage", "museum") == "museum"
    assert _category("place", "S.HTL") == "hotel"
    assert _category("place", "T.XYZ") == "terrain feature"
    assert _category("school", "Primary") == "Primary"


def test_public_bundle_leaves_out_share_alike_access_indicators(tmp_path) -> None:  # type: ignore[no-untyped-def]
    import pandas as pd

    from slf import atlas_landscape
    from slf.hazard_access import SPECS

    spine = tmp_path / "spine"
    spine.mkdir()
    pd.DataFrame(
        [("LK", 0, "Sri Lanka", None), ("LK41", 2, "Jaffna", "LK4")],
        columns=["geography_id", "level", "name_en", "parent_id"],
    ).to_parquet(spine / "geographies.parquet")
    hazard = tmp_path / "hazard"
    hazard.mkdir()
    base = {
        "geography_id": "LK41",
        "period": "2026",
        "time_start": "2026-01-01",
        "time_end": "2026-12-31",
        "value": 90.0,
        "value_status": "normal",
        "unit": "percent",
        "information_footprint_ref": "x",
        "data_nature": "modelled_estimate",
        "verification": "machine_extracted",
        "snapshot_sha256": "ab" * 32,
        "source_url": "u",
        "source_locator": "l",
        "breakdown": None,
    }
    rows = [
        {
            **base,
            "claim_id": "a",
            "indicator_id": "access_hospital_30min",
            "dataset_id": "heigit-accessibility",
        },
        {
            **base,
            "claim_id": "b",
            "indicator_id": "di_flood_records",
            "dataset_id": "desinventar-sri-lanka",
            "unit": "records",
        },
    ]
    pd.DataFrame(rows).to_parquet(hazard / "observations.parquet")
    local = atlas_landscape.build_extra(None, spine, None, tmp_path / "o1", None, hazard, False)
    public = atlas_landscape.build_extra(None, spine, None, tmp_path / "o2", None, hazard, True)
    assert local["indicators"] == 2 and public["indicators"] == 1
    assert any(s.dataset == "heigit-accessibility" for s in SPECS)
