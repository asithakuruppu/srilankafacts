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
